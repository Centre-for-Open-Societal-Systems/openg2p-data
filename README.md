# openg2p-data

Sample and reference data for the OpenG2P platform, plus the generators that
produce it. Registry and Master Data db-seed images clone this repo at build
time, so what is committed here is what a seeded install contains.

## Layout

| Directory | What it holds |
|---|---|
| [`packs/`](packs) | **Country packs** — administrative hierarchy, P-codes and boundary geometry, one directory per country. The only supported way geography reaches the platform. Start with its [README](packs/README.md). |
| [`scripts/packs/`](scripts/packs) | Pack tooling: build a real pack from OCHA COD-AB, redraw the fictitious one, and validate either. |
| [`demography/`](demography) | Shared synthetic people: `individuals.csv`, `households.csv`, ~500 portrait images. Registry-agnostic — person `i0001` is the same individual in every registry, so cross-registry scenarios line up. |
| [`household-info/`](household-info) | The same population as consolidated wide CSVs (housing, assets, livelihoods, scores). |
| [`users/`](users) | Sample portal users. |
| [`oan-seed/`](oan-seed) | Demo data for the OAN A2C and Grievance Frappe services, one directory per service. |
| [`geo/`](geo) | **Legacy.** The pre-pack flat `geo.csv`. Superseded — see its [README](geo/README.md). |
| [`scripts/`](scripts) | Generators for everything above. |

## Which country does an install get?

Kamuntu — a **fictitious** country ([`packs/XKM`](packs/XKM)) — by default.

That default is deliberate. A demo install attaches invented poverty, enrolment
and payment figures to whatever geography it holds, and doing that to a real
country's name and outline is not something to do by accident. Real country packs
are first-class and one Helm value away (`geoSeed.countryPack` in the
`openg2p-master-data` chart), and they carry the licence obligations their
`manifest.json` records.

## CI and the Master Data seed image

Every pull request runs [`pr-checks`](.github/workflows/pr-checks.yml): lint,
data files, pack validation and list quality. Jenkins ([`Jenkinsfile`](Jenkinsfile))
runs the same gates on every branch and, on `develop` and tags, builds
`master-data-db-seed` from `OpenG2P/master-data-service` with that commit of this
repo baked in, proves the image's packs match the validated ones and pushes it to
ECR as `eoan/openg2p-data/master-data-db-seed:<version>-<branch>.<build>`, the
OAN naming standard the registry pipelines use (`eoan/<repository>/<image>`;
[oan-helm `naming-standard.md`](https://github.com/Centre-for-Open-Societal-Systems/oan-helm/blob/main/docs/release/naming-standard.md),
section 6). `<version>` is in [`init.yaml`](init.yaml), `<branch>` is the Jenkins
branch name as a slug (a pull request build is `pr-<n>`, and only `develop` and
tags publish, whatever any parameter says: a pull request or other branch build is
validated and built but never pushed, and `scripts/ci/publish_gate.sh` refuses it
before any ECR call), and `<build>` is the Jenkins build number, for example
`1.0.0-develop.57`. [`scripts/ci/image_names.py`](scripts/ci/image_names.py)
generates it. The tag holds no commit: the openg2p-data commit and the
master-data-service commit (`MDS_REF`) are OCI labels on the image
(`org.opencontainers.image.revision`, `org.openg2p.master-data-service.revision`
and `.source` / `.ref`) and are recorded with the digest in the build's
`dist/image.json`. A published tag is never overwritten.

CI stops there: it deploys and reseeds nothing, whatever its parameters. Seeding
Master Data, a registry or the services is a separate, approved deployment that
names the image by `repo:tag@digest` from `dist/image.json`
(`master-data.geoSeed.image.repository` and `.tag` in the commons-services
chart). The digest decides what runs; the tag says where it came from. `scripts/ci/check_jenkinsfile.py` fails
any change that puts a deploy back into the Jenkinsfile.

**The pin follows the build, through a pull request.** After a `develop` build publishes the image, the last stage
(`Propose seed pin in oan-helm`, `scripts/ci/propose_seed_pin.sh`) rewrites those two lines in oan-helm's
`charts/openg2p-commons-services/values.yaml` on the branch `bot/seed-image` and opens, or updates, one pull request
into `main`, together with the release record `releases/1.0.0-dev.<next>.yaml` that oan-helm's contract test compares the
chart's seed image with. A person reviews and merges it; merging releases a chart and New Dev follows it. Staging keeps its own pin
(`environments/staging/values/commons-services.yaml`) and is bumped by hand after New Dev is verified. The stage uses
the Jenkins credential `oan-helm-fork-token`, bound in that stage only. It never merges, never pushes to `main` and
never touches a cluster; the guard and `scripts/ci/tests/test_pin_guard.py` fail a change that does. A failure there
marks the build unstable and leaves the published image alone. An older build never moves the pin back.

**Setup this naming needs outside the repository**

- **A new ECR repository, `eoan/openg2p-data/master-data-db-seed`**, in
  `ap-south-1`, created before the first develop build by someone with ECR
  admin rights. The registry pipelines create theirs; this one does not, so the
  push stage fails if the repository is missing. Create it as the standard
  asks: immutable tags, scan on push, AES256, tagged `owner=openg2p-data` and
  `naming=eoan-standard`. The old `openg2p/commons/master-data-db-seed`
  repository and its tags stay as they are.
- **IAM:** `aws-ecr-creds` needs push (`ecr:BatchCheckLayerAvailability`,
  `InitiateLayerUpload`, `UploadLayerPart`, `CompleteLayerUpload`,
  `PutImage`), `ecr:DescribeImages`, `ecr:DescribeRepositories` and
  `ecr:BatchGetImage` / `GetDownloadUrlForLayer` on the new repository. A policy
  scoped to single repository ARNs does not cover it; use
  `eoan/openg2p-data/*`. Pull access for New Dev and staging likewise needs
  `eoan/openg2p-data/*`
  ([`ecr-pull-access.md`](https://github.com/Centre-for-Open-Societal-Systems/oan-helm/blob/main/docs/ecr-pull-access.md)).
- **Consumers opt in.** Nothing that pins
  `openg2p/commons/master-data-db-seed:<data sha 12>-mds-<mds sha 8>` moves by
  itself: a consumer switches to the new repository by changing
  `master-data.geoSeed.image.repository` and `.tag` to the `dist/image.json`
  values, in its own approved change.

## Generators

Nothing here is generated at install time — the outputs are committed, so seed
data is reviewable in a diff and reproducible. Regenerate deliberately:

```bash
cd scripts/packs
python3 generate_synthetic_pack.py --preset kamuntu --out ../../packs/XKM --version 2026-07-30
python3 validate_pack.py ../../packs/ETH ../../packs/XKM     # always
```

The pack tools are pure Python — no shapely, no GEOS. Everything else needs
`pip install -r scripts/requirements.txt`.

## What does not belong here

Data and generators here must be usable by more than one registry or service. A
generator that writes one registry's own tables belongs with that registry, beside
the schema it targets.

NSR's bulk sample generator, its `distributions.json` and the query that rebuilds
them used to live here and now sit in
`national-social-registry/docker/db-seed/`. They write NSR's extension tables and
draw every enum-backed value from NSR's enums, and keeping them a repo apart from
those enums had a concrete cost: a commit reworking the programme enums could not
show the generator going stale, so it and `reporting_views.sql` drifted into
agreeing with each other on eleven values the schema never defined. NSR's
`test/test_enum_values.py` guards that now — a test only writable once the two
live together.

`generate_nsr_data.py` and `generate_farmer_data.py` do stay: they read the shared
demography above and write committed fixture files, so they move with
`demography/`'s columns rather than with a registry's schema.
