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
| `Grievance_SLA_Configuration.json` | One row per category, named `GR-SLA-<category code>`, with the turnaround of each sub-type per level, and the seasonal and urgent rules of the matrix's Seasonal Calendar (STG-514) |
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
  the triage window. 132 rows in all. The SLA engine does not read this table yet: it runs on `sla_days`.
- **SLA configuration** `sla_days` is the longest L1 plus L2 of the category's sub-types (`Other`: 7), and
  is what the engine reads. The rows are named after the category code, not the `GR-SLA-####` series, so
  the series counter cannot run into them.
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
- **The catch-all** category `Other` and type `SYS` are made by the app on install, under those names, so
  the seed rows for them are skipped as already present.
- `NGV` (Not a grievance) and `OOS` (Out of scope) rows of the matrix are not categories here.
- Ticket codes use the service alphabet, which has no I, L, O or U.

### Sensitive and urgent handling (STG-514)

Each sub-type also carries `is_sensitive`, read from the matrix's Sensitive Flag column. Urgency is not a
field of the type: the matrix's Urgent Flag, Urgent Season and Seasonal Calendar are seasonal rules
(`sla_rules`) on the category's SLA configuration. Deploy the oan_grievance_service build with STG-514
first and migrate: before it, the site has no `is_sensitive` on `Grievance Type` and no `Grievance SLA
Rule`, and the loader fails.

- **Sensitive** is exactly the 8 sub-types the matrix marks Yes: C13-01 to C13-04, C15-01 to C15-03 and
  C16-01. C16-02 (wrong personal data) is No. No C04 sub-type is flagged: "C04 if coercion" is free text in
  the Confidential path, not a flag, so a coercion case is filed as C13-03 until the owners decide.
- **Urgent** is every sub-type of C01, C02, C07 and C17, so each of those categories has one rule for the
  whole category. C09 is not Urgent: its rule raises priority to High.
- **Rules.** A window is a recurring month and day, the same every year; whole months run from the first
  to the last day of the month.

  | Configuration | Rule | Window | Urgent | Priority |
  |---|---|---|---|---|
  | `GR-SLA-C01` | Meher input season | 15 May to 31 August | yes | Urgent |
  | `GR-SLA-C02` | Irrigation season (dry season) | 1 October to 30 April | yes | Urgent |
  | `GR-SLA-C07` | Dry / irrigation season | 1 October to 30 April | yes | Urgent |
  | `GR-SLA-C09` | Harvest marketing peak | 1 October to 31 December | no | High |
  | `GR-SLA-C17` | Pest and disease outbreak (all year) | all year | yes | Urgent |

- **SLA days.** The matrix gives no in-season turnaround, so no rule sets `sla_days` and the category's
  SLA days apply. The owners set a rule's `sla_days` (for example 3 days in season) on the site.
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

A site seeded before STG-514 already holds the types and SLA configurations, so the loader would skip
them. The app's `apply_sensitive_urgent_matrix` patch sets the Sensitive flags and adds these rules on
migrate, only where they are still empty: a configuration that already has rules is left alone.
