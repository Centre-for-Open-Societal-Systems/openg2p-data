# Master Data Service (MDS) Seeding Scripts

This directory contains the authoritative data-seeding scripts for the OpenG2P Master Data Service (MDS) in Ethiopia Agri-Stack.

## Contents

* `seed_all_mds.py`: Master orchestrator running all seeding steps sequentially.
* `import_all_catalogs.py`: Populates the base reference catalogs:
  * **Crops**: 150 crops, 902 certified varieties (`CROP_VARIETY`), 7 categories, ecological zones.
  * **Seeds**: 130 seeds (`SEED_CATALOG`), certified seed varieties, demand trends.
  * **Livestock**: Species, 94 breeds (`LIVESTOCK_BREED_CATALOG`), census population records.
* `add_geography_to_catalogs.py`: Populates the Ethiopian Administrative Geography hierarchy (1 Country, 15 Regions, 107 Zones, 1,148 Woredas = 1,271 total units).
* `import_input_catalog.py`: Populates the 5th catalog for certified fertilizers, soil blends (`NPSB`, `Urea`, `DAP`, `Compost`), and amendment types.
* `setup_keycloak_orgs_and_users.py`: Provisions Keycloak organization groups (MoA, LDI, CSA) and user access hierarchy (Maker/Checker).
* `data/`: SQL schema files and data inserts with idempotent `CREATE TABLE IF NOT EXISTS` guards.

## Execution & Environment Variables

The scripts support both OpenG2P standard environment variables and standard PostgreSQL parameters:

| Variable | Description | Default |
|---|---|---|
| `MASTER_DATA_API_DB_HOSTNAME` / `PGHOST` | MDS PostgreSQL Host | `mds-standalone-postgres` |
| `MASTER_DATA_API_DB_PORT` / `PGPORT` | MDS PostgreSQL Port | `5432` |
| `MASTER_DATA_API_DB_DBNAME` / `PGDATABASE` | Database Name | `master_data` |
| `MASTER_DATA_API_DB_USERNAME` / `PGUSER` | Database User | `postgres` |
| `MASTER_DATA_API_DB_PASSWORD` / `PGPASSWORD` | Database Password | `password` |
| `KEYCLOAK_URL` | Keycloak Host (optional) | *None* |

### Run Seeding:
```bash
python3 scripts/mds/seed_all_mds.py
```
