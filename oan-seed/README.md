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

`grievance/data` carries the categories and sub-types of the OAN Grievance Routing Matrix D2, so every
environment starts with the same taxonomy.

| File | Holds |
|---|---|
| `Grievance_Service_Category.json` | 19 categories, `C01` to `C19`, plus the catch-all `Other` (`SYS`), which is the default category |
| `Grievance_Type.json` | 75 sub-types keyed on their code (`C01-01` to `C19-02`), plus the catch-all `Other` type (`SYS`) |
| `Grievance_Department.json` | The departments the sub-types name, added to the ones already seeded. Other keeps `Unrouted`, the triage desk |

Each sub-type carries `type_code`, `service_category`, `department`, `sla_l1_days`, `sla_l2_days`,
`external_referral` and `resolution_path`. `name` equals `type_code`, which is what the loader matches on.

- **SLA days** are the matrix's illustrative values, "to be decided by the respective owners". They are
  defaults an administrator can edit on the type. `0` at L1 means the type skips Kebele. `15 (follow-up)`
  for roads and electricity is stored as `15`.
- **Resolution path** is 1 Kebele Agriculture Office, 2 Kebele Committee, 3 Community Elders First,
  4 Direct to Woreda or ATI, 5 Confidential. The matrix has no path column, so the path is derived per
  sub-type from the routing deck: elders-first rows are 3, sensitive rows 5, rows that skip Kebele 4,
  committee rows 2 (plus repayment disputes and cooperative governance), and the rest 1. Counts: 39, 11, 6, 11, 8.
  C05, C06, C10, C14 and C16 therefore sit on more than one path, one path per sub-type.
- `NGV` (Not a grievance) and `OOS` (Out of scope) rows of the matrix are not categories here.
- Ticket codes use the service alphabet, which has no I, L, O or U.

### Run

Nothing runs by hand on a normal deploy: the seed image loads `oan-seed/grievance` after `bench migrate`.
To load into a site yourself, from the bench's `sites/` directory:

```bash
../env/bin/python ../apps/oan_grievance_service/ci/seed/load.py <site> <path to oan-seed/grievance>
```

The loader only creates records whose `name` is missing. A second run creates nothing, and an edit an
administrator made to a seeded category, type or department is kept. Loading needs the Grievance Type
fields from oan_grievance_service STG-512, so migrate the site first.

The loader never removes anything. A site that already holds the old demo categories and types keeps
them next to the new ones, and its `Other` type, created before this change under a `GTYPE-` name, is
not replaced by the `SYS` one. Start from a fresh site to get exactly the taxonomy above.

