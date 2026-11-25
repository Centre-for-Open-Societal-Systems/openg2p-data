# Domain lists

Code lists that vary by **domain as well as by country**. Crops are agricultural
*and* Kamuntu; a social registry install has no use for them.

Keeping them here rather than in `../codelists/` means one artifact per country
without every install loading every domain's lists — a Farmer Registry reads
`agriculture/`, NSR ignores it. Master Data loads a domain only when its chart
names it (`geoSeed.domains: [agriculture]`); registries then read the lists live
from Master Data.

The file format is identical to `../codelists/`, and `validate_pack.py` checks
both. An `attribute_id` must be unique across `codelists/` and every domain:
Master Data holds them in one table. Roles (`../../roles.json`) apply here too if
platform logic ever needs to reason about a domain value's meaning; none do today.

## agriculture/

| Lists | Used by |
|---|---|
| `CROP_COMMODITY`, `CROP_END_USE`, `CROP_SEASON`, `CURRENT_LAND_USE`, `FARMER_CLUSTER_ROLE`, `FARMING_TYPE`, `LAND_OWNERSHIP_TYPE`, `LAND_SIZE_UNIT`, `LIVESTOCK_BREED`, `LIVESTOCK_SYSTEM`, `LIVESTOCK_TYPE`, `MEANS_OF_ACQUISITION`, `SOURCE_OF_INCOME`, `WATER_SOURCE` | Farmer Registry |

Seasons follow Kamuntu's CSA Agricultural Sample Survey: Meher (main rains),
Belg (short rains) and irrigated dry-season production. Each list's codes carry a
short list prefix (`SEASON_MEHER`) so a code names its list on its own.

## disability/

| Lists | Used by |
|---|---|
| `AGE_ONSET_BAND`, `ANIMAL_ASSISTANCE_TYPE`, `ASSESSMENT_AUTHORITY`, `ASSESSMENT_METHOD`, `ASSISTIVE_TECHNOLOGY_TYPE`, `CAREGIVER_RELATIONSHIP`, `COMMUNICATION_NEED`, `DATA_SOURCE`, `DISABILITY_STATUS_LEVEL`, `HOUSING_SUPPORT_TYPE`, `HOUSING_TYPE`, `HUMAN_ASSISTANCE_TYPE`, `IMPAIRMENT_CAUSE`, `IMPAIRMENT_LEVEL`, `IMPAIRMENT_TYPE`, `INCOME_LEVEL`, `LEGAL_CAPACITY_STATUS`, `MEDICAL_CARE_TYPE`, `PROGRAM_ENROLMENT_STATUS`, `PROVISION_SOURCE`, `REGISTRATION_CHANNEL`, `RELATIONSHIP_TYPE`, `SUPPORT_FREQUENCY`, `SUPPORT_NEEDS_LEVEL`, `SUPPORT_STATUS`, `TRANSPORT_REQUIREMENT` | Disability Registry |
| `DISABILITY_STATUS`, `EMPLOYMENT_STATUS`, `IDENTITY_EVIDENCE_TYPE`, `PREFERRED_CONTACT_METHOD`, `PROGRAM_NAME`, `VERIFICATION_STATUS` | Disability Registry. Core lists in `ETH`; this pack has none, so they are here |

The Disability Registry uses 35 lists. This folder holds the ones this pack does
not already define; the registry reads the rest from `../codelists/` (`GENDER`,
`MARITAL_STATUS`, `EDUCATION_LEVEL`). Load it by naming the domain:
`geoSeed.domains: [agriculture, disability]`.

Value codes are the registry's own (the enums in OpenG2P/disability-registry,
`register_domain/models/enums.py`), which it maps to the SPDCI Disability Registry
code directories (CD.DR.01 to CD.DR.15) at the DCI interface. A display may be
changed freely; the codes are the ones the registry accepts. `PROGRAM_NAME`,
`ASSESSMENT_AUTHORITY` and `DATA_SOURCE` are generic examples of programmes,
institutions and sources, meant to be replaced by the country's own.

`DISABILITY_STATUS` here is assessment-based (assessed disabled, pending
assessment, expired, ...), not a yes/no survey answer. `ASSESSED_DISABLED` carries
the `disability_yes` role, which the contract requires of any pack that has the
list.
