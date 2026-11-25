# Domain lists

Code lists that vary by **domain as well as by country**. Crops are agricultural
*and* Ethiopian; a social registry install has no use for them.

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
| `CROP_COMMODITY` (with `CROP_CATEGORY`), `CROP_SEASON`, `SOIL_FERTILITY`, `WATER_SOURCE`, and the crop-season lists: `CROPPING_SYSTEM`, `LAND_PREPARATION_METHOD`, `IRRIGATION_SOURCE`, `IRRIGATION_METHOD`, `SEED_TYPE`, `SEED_SOURCE`, `SEED_VARIETY`, `SOWING_METHOD`, `FERTILIZER_TYPE`, `FARM_MACHINERY`, `CROP_GROWTH_STAGE`, `CROP_CONDITION`, `INFESTATION_TYPE`, `INFESTATION_AGENT`, `INFESTATION_SEVERITY`, `PEST_CONTROL_ACTION`, `CROP_DAMAGE_CAUSE`, `AGRO_ECOLOGICAL_ZONE` | Crop Sown Registry |

Seasons follow Ethiopia's CSA Agricultural Sample Survey: Meher (main rains),
Belg (short rains) and irrigated dry-season production. Each list's codes carry a
short list prefix (`SEASON_MEHER`, `SEV_HIGH`) so a code names its list on its own.

Crops follow the Ministry of Agriculture's crop variety list: `CROP_COMMODITY` has
one entry per MoA crop, plus `CROP_MALT_BARLEY` and `CROP_OTHER`. A list may carry
typed attributes: an `attribute_schema` (JSON Schema) and `attributes` per value,
where `x-list-ref` names another list (a crop's `category` is a `CROP_CATEGORY`
code; a variety's `crop` is a `CROP_COMMODITY` code). `validate_pack.py` checks
them. On an existing install, approve the `CROP_COMMODITY` draft before
`SEED_VARIETY`'s, whose varieties refer to the new crops.

## disability/

| Lists | Used by |
|---|---|
| `AGE_ONSET_BAND`, `ANIMAL_ASSISTANCE_TYPE`, `ASSESSMENT_AUTHORITY`, `ASSESSMENT_METHOD`, `ASSISTIVE_TECHNOLOGY_TYPE`, `CAREGIVER_RELATIONSHIP`, `COMMUNICATION_NEED`, `DATA_SOURCE`, `DISABILITY_STATUS_LEVEL`, `HOUSING_SUPPORT_TYPE`, `HOUSING_TYPE`, `HUMAN_ASSISTANCE_TYPE`, `IMPAIRMENT_CAUSE`, `IMPAIRMENT_LEVEL`, `IMPAIRMENT_TYPE`, `INCOME_LEVEL`, `LEGAL_CAPACITY_STATUS`, `MEDICAL_CARE_TYPE`, `PROGRAM_ENROLMENT_STATUS`, `PROVISION_SOURCE`, `REGISTRATION_CHANNEL`, `RELATIONSHIP_TYPE`, `SUPPORT_FREQUENCY`, `SUPPORT_NEEDS_LEVEL`, `SUPPORT_STATUS`, `TRANSPORT_REQUIREMENT` | Disability Registry |

The Disability Registry uses 35 lists. This folder holds the ones this pack does
not already define; the registry reads the rest from `../codelists/` (`GENDER`,
`MARITAL_STATUS`, `EDUCATION_LEVEL`, `EMPLOYMENT_STATUS`, `IDENTITY_EVIDENCE_TYPE`,
`PREFERRED_CONTACT_METHOD`, `VERIFICATION_STATUS`, `PROGRAM_NAME`,
`DISABILITY_STATUS`). Load it by naming the domain:
`geoSeed.domains: [agriculture, disability]`.

Value codes are the registry's own (the enums in OpenG2P/disability-registry,
`register_domain/models/enums.py`), which it maps to the SPDCI Disability Registry
code directories (CD.DR.01 to CD.DR.15) at the DCI interface. A display may be
changed freely; the codes are the ones the registry accepts.
`ASSESSMENT_AUTHORITY` and `DATA_SOURCE` are generic examples of institutions and
sources, meant to be replaced by the country's own.

`DISABILITY_STATUS` is not here: this pack's core list
(`../codelists/disability_status.json`, Yes / No / Unknown, holder of the
`disability_yes` role) already owns that id, and one id cannot hold both lists.
The registry's own statuses (assessed disabled, pending assessment, expired, ...)
are therefore not offered on an install of this pack until that is settled.
