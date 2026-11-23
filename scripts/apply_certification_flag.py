#!/usr/bin/env python3
"""
apply_certification_flag.py
---------------------------
Applies and synchronizes the 'certification_status' attribute flag
exclusively across all CROP and SEED catalogues in PostgreSQL:
  - Server: CROP_COMMODITY, CROP_CATEGORY, CROP_VARIETY, SEED_VARIETY,
    CROP_CONDITION, CROP_DAMAGE_CAUSE, CROP_DISEASE, CROP_END_USE,
    CROP_GROWTH_STAGE, CROPPING_SYSTEM, CROP_SEASON, CROP_TEST
  - Local: CROP_CATALOG, CROP_CATEGORY_CATALOG, CROP_VARIETY_CATALOG,
    SEED_DEMAND_BY_CROP_CATALOG

Features:
  1. Does NOT touch general/non-crop catalogues (Geography, Demography, Bank, etc.).
  2. Ensures CROP and SEED schemas have certification_status with default: "CERTIFIED".
  3. Sets a trigger on CROP line items to auto-default certification_status = 'CERTIFIED'.
  4. Backfills all existing crop records and configures demo uncertified/provisional records.

Usage:
    python3 scripts/apply_certification_flag.py
"""

import os
import sys
import subprocess

# DB connection settings
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5434")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASSWORD", "password")
DB_NAME = os.environ.get("DB_NAME", "master_data")
DOCKER_CONTAINER = os.environ.get("DOCKER_CONTAINER", "mds-standalone-postgres")


def run_sql(sql_statement: str) -> str:
    """Execute SQL using host psql or fallback to docker exec."""
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASS

    try:
        cmd = [
            "psql",
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-U", DB_USER,
            "-d", DB_NAME,
            "-t",
            "-A",
            "-c", sql_statement
        ]
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        cmd = [
            "docker", "exec", "-i",
            DOCKER_CONTAINER,
            "psql",
            "-U", DB_USER,
            "-d", DB_NAME,
            "-t",
            "-A",
            "-c", sql_statement
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip()


def run_sql_file(file_path: str):
    """Execute a SQL script file."""
    with open(file_path, "r", encoding="utf-8") as f:
        sql = f.read()
    return run_sql(sql)


def main():
    print("=" * 70)
    print(" MDS Crop Catalog Certification Status Synchronization")
    print("=" * 70)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, "install_auto_certification_triggers.sql")

    if os.path.exists(sql_file):
        print(f"\n[1/2] Applying full migration from {os.path.basename(sql_file)}...")
        run_sql_file(sql_file)
        print("  -> Schemas updated, triggers installed, and existing records backfilled.")
    else:
        print(f"Error: {sql_file} not found!", file=sys.stderr)
        sys.exit(1)

    print("\n[2/2] Verification & Summary:")
    summary_sql = """
    SELECT 
        COALESCE(a.attribute_code, val.list_id) as catalog_code,
        val.version_no,
        COALESCE(val.attributes->>'certification_status', 'NONE') as status_flag,
        count(*) as count
    FROM g2p_list_version_values val
    LEFT JOIN g2p_attributes a ON a.attribute_id = val.list_id
    WHERE val.list_id LIKE 'CROP%' 
       OR val.list_id LIKE 'CROPPING%' 
       OR val.list_id LIKE 'SEED_%'
       OR val.list_id IN ('CROP_COMMODITY', 'CROP_CATEGORY', 'CROP_VARIETY', 'SEED_VARIETY', 'CROP_CATALOG', 'CROP_CATEGORY_CATALOG', 'CROP_VARIETY_CATALOG')
    GROUP BY COALESCE(a.attribute_code, val.list_id), val.version_no, val.attributes->>'certification_status'
    ORDER BY catalog_code, val.version_no, status_flag;
    """
    out = run_sql(summary_sql)
    print("\nCurrent Database Distribution:")
    print(f"{'Catalog':<30} | {'Ver':<4} | {'Flag':<14} | Count")
    print("-" * 60)
    for line in out.splitlines():
        if line.strip():
            parts = line.split("|")
            if len(parts) >= 4:
                print(f"{parts[0]:<30} | v{parts[1]:<3} | {parts[2]:<14} | {parts[3]}")

    print("\n" + "=" * 70)
    print(" Synchronization Completed Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
