# Farmer sample ownership

ETH-OAN is the shared source of geography, reference lists and demographic demo
facts. Load the pack into MDS with samples enabled, then let Farmer consume MDS
through its MD_PG connection and native intake/approval workflow. Committing a
pack or deploying Farmer with LOAD_SAMPLE_DATA=false does not create farmers.

The sample contract contains 21 individuals in six households. The Farmer loader
creates six farmers (the adult household heads), six households and 21 household
members. Approved operational records remain in Farmer; MDS is not their system
of record. These fixtures have no farm, crop or livestock facts, so consumers must
not invent them. Adding such facts requires an explicit MDS contract first.

Each ETH-OAN individual has a stable individual_id, household_id, unique 12-digit
national_id, valid birth_date, published geo_pcode and reference codes. full_name
contains given_name, fathers_name and a grandfather name. The builder generates
this synthetic name once in the shared pack; consumers preserve it. The existing
MDS sample schema already stores full_name, so no extra MDS column is required.
Reload the updated samples before enabling the companion Farmer loader: it rejects
older two-part names instead of inventing a third part independently.

Staff sample CSVs are provisioning inputs for IAM/Keycloak tooling. They are not
Farmer records or credentials managed by MDS. Provision roles and AWE assignees
separately, supply passwords through Secrets, and never put passwords in this pack.
The legacy generate_farmer_data.py utility now writes ignored generated/farmer
files for offline analysis only; it must not populate a registry or supply an image.

Merge and publish this data change before the companion Farmer image change.
Validate with python scripts/packs/validate_pack.py packs/ETH-OAN and
python -m unittest discover -s tests. After rollout, verify approved/processed
intakes and registry counts in a disposable environment before promotion.
