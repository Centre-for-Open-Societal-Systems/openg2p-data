#!/usr/bin/env python3
"""Empty Master Data's geography so the next pack load is a first load.

DEVELOPMENT ONLY. Runs as an init container of the dev reseed Job (Jenkinsfile
FRESH_GEO_DEV, scripts/ci/seed_job_from_release.py --fresh-geo), right before
load_geo_pack.py, against the same database.

Why it exists: Master Data is a versioned catalogue and a published geography
version is immutable. Dev's version 1 was migrated from the pre-catalogue tables
(level ids `level-region`..., unit ids `woreda-ET010101`...), not loaded from a
pack, and the loader cannot version a pack over it: the pack's `l1`/`region`
level collides with `level-region`/`region` on the unique level mnemonic, and a
diff would retire every unit live records point at. On a development environment
the clean route is the one registries already use for their own databases
(farmer-registry `fresh-install`): remove the data and run the standard first
install again. Here that is: delete every geography version with its levels,
units, change rows and current-version pointer, and the legacy geo tables the
registries read; then the loader's first-load path publishes the pack as the
next version number with its boundaries.

What stays: code lists and their versions (the loader versions those itself),
catalogue releases (their geography pointer is cleared), the change log (the
reset is logged in it, so version numbers never restart), AWE events, and the
pack licence keys.

Registries keep whatever geography ids their records hold. Rows written against
the old ids must be re-keyed with packs/<pack>/migration/id_map.csv or
re-seeded; that is each registry's own delivery, not this script's.

Refuses to run unless FRESH_GEO_CONFIRM is exactly "fresh-geo-dev", and prints
what it removes.
"""

import json
import os
import sys

import psycopg2

CONFIRM = "fresh-geo-dev"

TABLES = (
    # child tables first (foreign keys to g2p_geo_versions)
    "g2p_geo_changes",
    "g2p_geo_version_units",
    "g2p_geo_version_levels",
    "g2p_geo_versions",
    # legacy tables the registries and the API's /geo routes read
    "g2p_geo_level_values",
    "g2p_geo_levels",
)
# The catalogue enforces its immutability with row triggers
# (g2p_catalogue_guard_geo_children, g2p_catalogue_guard_published_parent):
# nothing under a PUBLISHED version may change. That rule is the point of the
# catalogue, and this script is the one deliberate exception to it, so the
# guards are switched off for the deleting transaction only, on exactly these
# tables, and switched back on before it commits. ALTER TABLE needs the table
# owner, which the loader's database user (the API's) is.
GUARDED = (
    "g2p_geo_changes",
    "g2p_geo_version_units",
    "g2p_geo_version_levels",
    "g2p_geo_versions",
    "g2p_catalogue_releases",
)


def main() -> int:
    if os.environ.get("FRESH_GEO_CONFIRM") != CONFIRM:
        print(f"[reset-geo] refusing: FRESH_GEO_CONFIRM is not '{CONFIRM}'", file=sys.stderr)
        return 2
    actor = os.environ.get("PACK_ACTOR", "seed")
    conn = psycopg2.connect(
        dbname=os.environ.get("MDS_DB", "master_data"),
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", ""),
    )
    try:
        with conn, conn.cursor() as cur:
            # Same lock the loader takes, so a concurrent load cannot interleave.
            cur.execute("SELECT pg_advisory_xact_lock(hashtext('g2p_geo_draft'))")
            cur.execute("SELECT version_no, status, country, change_note FROM g2p_geo_versions ORDER BY version_no")
            versions = cur.fetchall()
            cur.execute("SELECT count(*) FROM g2p_geo_level_values")
            legacy_units = cur.fetchone()[0]
            if not versions and legacy_units == 0:
                print("[reset-geo] no geography in Master Data; nothing to remove")
                return 0
            for no, status, country, note in versions:
                print(f"[reset-geo] removing geography version {no} ({status}, country={country or '-'}): {note}")
            print(f"[reset-geo] removing {legacy_units} legacy geo units")
            counts = {}
            for table in GUARDED:
                cur.execute(f"ALTER TABLE {table} DISABLE TRIGGER USER")
            for table in TABLES:
                cur.execute(f"DELETE FROM {table}")
                counts[table] = cur.rowcount
            cur.execute("UPDATE g2p_catalogue_releases SET geo_version_no = NULL WHERE geo_version_no IS NOT NULL")
            counts["releases_unpinned"] = cur.rowcount
            for table in GUARDED:
                cur.execute(f"ALTER TABLE {table} ENABLE TRIGGER USER")
            cur.execute("DELETE FROM g2p_catalogue_state WHERE key = 'geo.current_version_no'")
            cur.execute("SELECT g2p_catalogue_bump_legacy_generation()")
            cur.execute(
                "SELECT g2p_catalogue_log(%s, %s, %s, %s, %s, %s::jsonb)",
                (
                    "geo.version.reset", "geo", "geography",
                    max((v[0] for v in versions), default=0), actor,
                    json.dumps({
                        "versions": [v[0] for v in versions],
                        "legacy_units": legacy_units,
                        "reason": "dev fresh geography: the pack is loaded as a first load",
                    }),
                ),
            )
        print("[reset-geo] removed: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
        print("[reset-geo] done; the loader now treats the pack as a first load")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
