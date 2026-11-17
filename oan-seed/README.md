# OAN seed data

Demo data for the OAN Frappe services, curated from the shared development sites.
The seed images copy one service's directory and load it after `bench migrate`, on every
deployment. Loading only creates records that are missing.

| Directory | Service | Holds |
|---|---|---|
| [`a2c/`](a2c) | OAN A2C | Banks, loan products, status stages, terms, users and their bank permissions |
| [`grievance/`](grievance) | OAN Grievance Service | Administrative areas, departments, categories, types, routing, SLAs, providers, users |

Each directory has a `manifest.json` (load order and Single DocTypes), `data/<DocType>.json`
with one record per line, and, where a service has attachments, `files/{public,private}`.

Not included, on purpose: passwords, API keys and environment hostnames. The loader sets the
password of the users it creates from a Kubernetes Secret. Fill these in per environment:
`OAN IAM Service`, `A2C OpenG2P Settings` and the connection on the `A2C Banks` source.

## Grievance taxonomy (STG-512)

`grievance/data` carries the categories and sub-types of the OAN Grievance Routing Matrix D2, so a new
environment starts with the same taxonomy. **It is a seed for a fresh site.** See "Existing sites" below.

| File | Holds |
|---|---|
| `Grievance_Service_Category.json` | 19 categories, `C01` to `C19`, plus the catch-all `Other` (`SYS`), which is the default category |
| `Grievance_Type.json` | 75 sub-types keyed on their code (`C01-01` to `C19-02`), plus the catch-all `Other` type (`SYS`) |
| `Grievance_Department.json` | The 15 departments the sub-types name, with `Unrouted` (the triage desk) and two unrelated demo departments. The four demo departments the matrix replaces are gone |
| `Grievance_SLA_Configuration.json` | One row per category, named `GR-SLA-<category code>` |
| `Grievance_RBAC_Assignment.json` | The demo desks, moved to the new categories and departments |

Each sub-type carries `type_code`, `service_category`, `department`, `sla_l1_days`, `sla_l2_days`,
`external_referral` and `resolution_path`. `name` equals `type_code`, which is what the loader matches on.

- **SLA days** on a type are the matrix's illustrative values, "to be decided by the respective owners".
  They are defaults an administrator can edit. `0` means no SLA at that level: `0` at L1 is a type that
  skips Kebele. `15 (follow-up)` for roads and electricity is stored as `15`. The catch-all type is
  `0` and `7`, the triage window.
- **SLA configuration** rows are the ones the SLA engine reads. `sla_days` is the longest L1 plus L2 of the
  category's sub-types (`Other`: 7). The rows are named after the category code, not the `GR-SLA-####`
  series, so the series counter cannot run into them.
- **Resolution path** is 1 Kebele Agriculture Office, 2 Kebele Committee, 3 Community Elders First,
  4 Direct to Woreda or ATI, 5 Confidential. The matrix has no path column, so the path is derived per
  sub-type from the routing deck: elders-first rows are 3, sensitive rows 5, rows that skip Kebele 4,
  committee rows 2 (plus repayment disputes and cooperative governance), and the rest 1. Counts: 39, 11, 6, 11, 8.
  C05, C07, C10, C11, C14 and C16 therefore sit on more than one path, one path per sub-type.
  The catch-all has none.
- **External referral** is copied from the matrix row by row. C05 sub-types all refer to the Court and C10
  sub-types all refer to the Lender in the matrix, which may not be what each of them needs. The matrix
  owners should confirm.
- **Desks.** Only the demo desks exist, so only C01, C09, C10 and `Other` have a staffed desk and appear in
  Submit Grievance. Their department follows the type: C09 `Marketing`, C10 `Credit and Payments`.
- `NGV` (Not a grievance) and `OOS` (Out of scope) rows of the matrix are not categories here.
- Ticket codes use the service alphabet, which has no I, L, O or U.

### Run

Nothing runs by hand on a normal deploy: the seed image loads `oan-seed/grievance` after `bench migrate`.
To load into a site yourself, from the bench's `sites/` directory:

```bash
../env/bin/python ../apps/oan_grievance_service/ci/seed/load.py <site> <path to oan-seed/grievance>
```

Deploy the oan_grievance_service build that adds the Grievance Type fields (STG-512) first and migrate.
The loader checks every data file against the site before it loads anything, and stops with a message
naming the missing fields, so a seed that is ahead of the app leaves nothing half loaded.

A second run creates nothing, and an edit an administrator made to a seeded record is kept. A row counts
as present by its name, and a category, type or SLA row also by its code, category and name, or category.
Rows that link to a skipped row are pointed at the record already on the site.

### Existing sites

The loader never removes or changes anything, so this seed does not convert a site that already has the
old demo data. Such a site keeps its old categories, types and desks next to the new ones, its old desks
keep pointing at the old categories, and the new categories get no desk. Only the catch-all is brought up
to date, by the oan_grievance_service patch `seed_catch_all_sys_codes`. For the taxonomy above, start from a
fresh site.
