#!/usr/bin/env python3
"""
Master Data Service (MDS) Complete Data Seeding Entrypoint
Seeds all 5 Ethiopian Reference Catalogs and Keycloak Org Hierarchy:
1. Base Catalogs (Crops, Seeds, Livestock)
2. Administrative Geography (l0 Country -> l1 Regions -> l2 Zones -> l3 Woredas)
3. Agricultural Inputs & Fertilizer Catalog (5th Catalog)
4. Keycloak Organization Hierarchy & Users (Optional if KEYCLOAK_URL is provided)
"""

import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def run_step(script_name, description):
    script_path = os.path.join(SCRIPT_DIR, script_name)
    print(f"\n==================================================")
    print(f"[*] Running MDS Seeding Step: {description}")
    print(f"    Script: {script_name}")
    print(f"==================================================")
    result = subprocess.run([sys.executable, script_path], cwd=SCRIPT_DIR)
    if result.returncode != 0:
        print(f"[!] Error: Step '{script_name}' failed with return code {result.returncode}")
        sys.exit(result.returncode)
    print(f"[✓] Step '{script_name}' completed successfully.")

def main():
    print("Starting OpenG2P Master Data Service (MDS) Seeding Pipeline...")
    
    # 1. Base Core Catalogs (Crops, Seeds, Livestock)
    run_step("import_all_catalogs.py", "Core Reference Catalogs (Crops, Seeds, Livestock)")
    
    # 2. Administrative Geography
    run_step("add_geography_to_catalogs.py", "Administrative Geography Hierarchy (l0..l3)")
    
    # 3. Agricultural Inputs Catalog
    run_step("import_input_catalog.py", "Certified Fertilizers & Inputs Catalog")
    
    # 4. Keycloak Setup (only if configured)
    if os.environ.get("KEYCLOAK_URL") or os.environ.get("KEYCLOAK_ADMIN_PASSWORD"):
        run_step("setup_keycloak_orgs_and_users.py", "Keycloak Organization & User Access Hierarchy")
    else:
        print("\n[*] KEYCLOAK_URL not set; skipping Keycloak user/group seeding.")

    print("\n==================================================")
    print("[✓] ALL MASTER DATA SERVICE SEEDING COMPLETED!")
    print("==================================================\n")

if __name__ == "__main__":
    main()
