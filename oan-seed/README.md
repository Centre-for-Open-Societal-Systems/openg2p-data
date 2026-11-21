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
| `Grievance_Department.json` | The 15 departments the matrix names, with `Unrouted` (the triage desk) and two unrelated demo departments. The four demo departments the matrix replaces are gone |
| `Grievance_SLA_Rule.json` | The SLA of each category (STG-514): its base rule, named `<category code>-BASE`, and the seasonal rules of the matrix's Seasonal Calendar, named `<category code>-R<n>` |
| `Grievance_SLA_Configuration.json` | One row per category, named `GR-SLA-<category code>`, with its escalation settings and the turnaround of each sub-type per level |
| `Grievance_Officer_Position.json` | Canonical posts across the 4-level ladder (Kebele DA, Woreda SMS/Expert, Zonal Head, Regional Bureau Head) |
| `Grievance_RBAC_Assignment.json` | Staffed desks for all 19 categories (C01 to C19) plus Unrouted, linking seats from `Grievance Officer Position` |

Each sub-type carries `type_code`, `service_category`, `external_referral` and `entry_role_level`. `name`
equals `type_code`, which is what the loader matches on.

- **Department.** The matrix names a department for every sub-type, but a type does not store it: routing
  reads the desks (`Grievance RBAC Assignment`), so the owner of a case is whatever desk is set up for the
  category, type and department. The departments are seeded so a desk can be made for them.
- **Turnaround days** are the matrix's illustrative values, "to be decided by the respective owners". They
  are rows of the category's SLA configuration (`level_turnarounds`): L1 is `nodal_officer` (Kebele) and L2
  is `senior_nodal_officer` (Woreda), each with the sub-type it is for. A level a sub-type skips has no
  row. `15 (follow-up)` for roads and electricity is stored as `15`. The catch-all has an L2 row of `7`,
  the triage window. 132 rows in all. The SLA engine does not read this table yet: it runs on the SLA
  days of the category's SLA rules.
- **SLA days** are the longest L1 plus L2 of the category's sub-types, on the category's base SLA rule
  (`Grievance_SLA_Rule.json`), which is what the engine reads; the configuration has no `sla_days` since
  STG-514. The catch-all `Other` gets its base rule (7 days) from the app on install, so the seed has none
  for it. Configurations and rules are named after the category code, not the `GR-SLA-####` and
  `GR-SLR-#####` series, so the series counters cannot run into them. The rules load before the
  configurations: an SLA configuration needs its category's base rule.
- **Entry role level** (`entry_role_level`) is a link to a `Grievance Role Level`: the lowest level whose
  officers handle the type. The routing deck gives each sub-type one of five resolution paths, and the matrix
  has no path column, so it was derived per sub-type from the deck: elders-first rows are path 3, sensitive
  rows 5, rows that skip Kebele 4, committee rows 2 (plus repayment disputes and cooperative governance), and
  the rest 1 (39, 11, 6, 11 and 8 sub-types). Only path 4 says something about a level, so the seed stores
  `senior_nodal_officer` for those 11 sub-types and `nodal_officer` for the other 64. The catch-all has none.
  The other four path labels (Kebele agriculture office, Kebele committee, community elders first,
  confidential) are not stored in the app. **The level is descriptive**: nothing in routing reads it. A type
  that skips Kebele is enforced by its desk having no officer at the Kebele level, so the desk hands the
  case to the next level.
- **External referral** is copied from the matrix row by row. C05 sub-types all refer to the Court and C10
  sub-types all refer to the Lender in the matrix, which may not be what each of them needs. The matrix
  owners should confirm.
- **Desks.** Desks are seeded for all 19 categories and Unrouted, mapping the 4-level public-sector organizational hierarchy (Kebele DA → Woreda SMS/Expert → Zonal Head → Regional Bureau Head) using canonical `Grievance Officer Position` records. All categories have staffed desks and appear in Submit Grievance.
- **Positions and assignments.** A `Grievance Officer Position` is a role (Crop DA, Crop SMS) with its
  role level and the position it reports to. Who holds it, and where, is a `Grievance Position Assignment`,
  so one position serves many people. Each desk officer row links its assignment. An assignment may give
  only an `email`: that person's first sign-in fills its `user`.
- **The catch-all** category `Other` and type `SYS` are made by the app on install, under those names, so
  the seed rows for them are skipped as already present.
- `NGV` (Not a grievance) and `OOS` (Out of scope) rows of the matrix are not categories here.
- Ticket codes use the service alphabet, which has no I, L, O or U.

### Sensitive and urgent handling (STG-514)

Each sub-type also carries `is_sensitive`, read from the matrix's Sensitive Flag column. SLA days, urgency
and priority are not fields of the type: they are the category's SLA rules (`Grievance SLA Rule`, one record
each, linked by `service_category`), the one source of a case's SLA in the service. Every rule carries
`sla_days`, `is_urgent` and `priority`. These Ethiopian values live only in this seed, not in the app.
Deploy the oan_grievance_service build with STG-514 first and migrate: before it, the site has no
`is_sensitive` on `Grievance Type` and no `Grievance SLA Rule`, and the loader fails.

- **Sensitive** is exactly the 8 sub-types the matrix marks Yes: C13-01 to C13-04, C15-01 to C15-03 and
  C16-01. C16-02 (wrong personal data) is No. No C04 sub-type is flagged: "C04 if coercion" is free text in
  the Confidential path, not a flag, so a coercion case is filed as C13-03 until the owners decide.
- **Base rules.** One per category (`C01-BASE` to `C19-BASE`): no type, area or window, the category's SLA
  days, Standard and Normal. The matrix flags every C17 sub-type Urgent all year, so `C17-BASE` is urgent
  with priority Urgent.
- **Seasonal rules.** The matrix flags every sub-type of C01, C02 and C07 Urgent in its season, so each has
  one windowed rule for the whole category. C09 is not Urgent: its rule raises priority to High. A window is
  a recurring month and day, the same every year; whole months run from the first to the last day of the
  month.

  | Rule | Category | Label | Window | SLA days | Urgent | Priority |
  |---|---|---|---|---|---|---|
  | `C01-R1` | C01 | Meher input season | 15 May to 31 August | 17 | yes | Urgent |
  | `C02-R1` | C02 | Irrigation season (dry season) | 1 October to 30 April | 17 | yes | Urgent |
  | `C07-R1` | C07 | Dry / irrigation season | 1 October to 30 April | 17 | yes | Urgent |
  | `C09-R1` | C09 | Harvest marketing peak | 1 October to 31 December | 17 | no | High |
  | `C17-BASE` | C17 | Pest and disease outbreak (all year) | all year (base rule) | 3 | yes | Urgent |

- **SLA days in season.** The matrix gives no in-season turnaround, so each seasonal rule carries its
  category's days. The owners set them on the site (for example 3 days in season), in the one list of
  `GET /api/v1/sla-rules`, through `PATCH /api/v1/sla-rules/{rule_id}`.
- **Belg woredas and woreda overrides** are not seeded: no official list exists. C01's February to April
  window for a Belg woreda, and a woreda's own C02 or C07 window, are rules with that woreda's
  `administrative_area`, added on the site.
- C15-03 (pesticide safety) stays on the Gender and Safety desk. Moving it to Crop Protection is only a
  proposal in the matrix, so the seed does not.

### Run

Nothing runs by hand on a normal deploy: the seed image loads `oan-seed/grievance` after `bench migrate`.
To load into a site yourself, from the bench's `sites/` directory:

```bash
../env/bin/python ../apps/oan_grievance_service/ci/seed/load.py <site> <path to oan-seed/grievance>
```

Deploy the oan_grievance_service build with STG-512 first and migrate: the `Grievance Type` and
`Grievance SLA Configuration` need the fields this seed fills.

A second run creates nothing, and an edit an administrator made to a seeded record is kept. A row counts
as present by its name.

### Existing sites

The loader never removes or changes anything, so this seed does not convert a site that already has the
old demo data: that site keeps its old categories, types and desks next to the new ones. Dev and test sites
with the old taxonomy should be recreated and seeded again, for example with the Helm chart's
`jobs.createSite.forceCreate` or its drop-site job.

A site seeded before STG-514 already holds the types and SLA configurations. On migrate, the app's
`move_sla_days_to_base_rules` patch gives each category with an active configuration its base rule, with
the days the configuration had, named `<category code>-BASE` like this seed's, so the loader finds the base
rules and skips them. The loader then adds the seasonal rules (`C01-R1` and so on), which are missing. It
skips the types, so on such a site the Sensitive flags and C17's urgency are set through the API
(`PATCH /api/v1/grievance-types/{id}`, `PATCH /api/v1/sla-rules/C17-BASE`): the app no longer carries
this data.
