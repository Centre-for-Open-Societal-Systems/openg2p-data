#!/usr/bin/env python3
"""
Turn MoA catalogs and reference SQL tables into ETH-OAN pack additions.
Converts:
  1. Missing crops into eth_oan_additions/values/domains/agriculture/crop_commodity.json
  2. MoA crop varieties into eth_oan_additions/values/domains/agriculture/seed_variety.json
  3. MoA livestock breeds into eth_oan_additions/domains/agriculture/livestock_breed_name.json
  4. Livestock sex into eth_oan_additions/domains/agriculture/livestock_sex.json
  5. Missing fertilizer types into eth_oan_additions/values/domains/agriculture/fertilizer_type.json
"""
import os
import re
import sys
import json
import collections

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADDITIONS_DIR = os.path.join(BASE_DIR, "eth_oan_additions")
REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../.."))

CROP_SQL = os.path.join(REPO_ROOT, "scripts/packs/sources/05_insert_crop_variety.sql")
BREED_SQL = os.path.join(REPO_ROOT, "scripts/packs/sources/04_insert_livestock_breed.sql")
BASE_PACK = os.path.join(REPO_ROOT, "packs/ETH")

# Legitimate variety breeding codes / pedigree lines that end in 3 digits
ALLOWED_NUMERIC_CODES = {
    'VAR_MAIZE_CP_201', 'VAR_MAIZE_CP_838', 'VAR_TRITICALE_ETCL_161',
    'VAR_TEFF_DAGEM_DZ_CR_438', 'VAR_RICE_VRH_606', 'VAR_RICE_VRH_640',
    'VAR_RICE_VRH_654', 'VAR_MAIZE_PAC_781', 'VAR_MAIZE_CML_161_X_CML_165',
    'VAR_COWPEA_82D_889', 'VAR_TEFF_KORA_DZ_CR_438', 'VAR_MAIZE_SC_719',
    'VAR_SORGHUM_PAC_537', 'VAR_TEFF_DZ_01_787', 'VAR_BREAD_WHEAT_MEKELLE_01_HUW_468',
    'VAR_MAIZE_A_511', 'VAR_MAIZE_BH_140', 'VAR_MAIZE_BH_660',
    'VAR_TEFF_BOSET_DZ_CR_409', 'VAR_MAIZE_MHQ_138', 'VAR_MAIZE_SC_403',
    'VAR_MAIZE_BH_541', 'VAR_MAIZE_BH_QP_542', 'VAR_MAIZE_BH_670',
    'VAR_MAIZE_BELES_SC_713', 'VAR_MAIZE_BEREDA_SC_715', 'VAR_MAIZE_BH_543',
    'VAR_MAIZE_MH_130', 'VAR_MALT_BARLEY_HB_120', 'VAR_SOYBEAN_COKER_240',
    'VAR_SESAME_TATE_BSC_003', 'VAR_GROUNDNUT_NC_343', 'VAR_COMMON_BEAN_MILKESA_DAB_523',
    'VAR_COMMON_BEAN_DAB_413', 'VAR_COMMON_BEAN_DAB_372', 'VAR_COMMON_BEAN_ATNDABA_A_262',
    'VAR_MAIZE_CML_395_X_CML_202', 'VAR_GROUNDNUT_WERER_962', 'VAR_MAIZE_BH_545',
    'VAR_COMMON_BEAN_SER_125', 'VAR_COMMON_BEAN_SER_119', 'VAR_MAIZE_BH_540',
    'VAR_MAIZE_BH_661', 'VAR_MAIZE_MH_141', 'VAR_MAIZE_BH_520', 'VAR_MAIZE_BH_546',
    'VAR_MAIZE_BH_547', 'VAR_MALT_BARLEY_HB_1963', 'VAR_MALT_BARLEY_HB_1964',
    'VAR_MALT_BARLEY_HB_1965', 'VAR_MALT_BARLEY_HB_1966', 'VAR_MALT_BARLEY_HB_1307',
    'VAR_MALT_BARLEY_HB_1533', 'VAR_FOOD_BARLEY_HB_1960', 'VAR_FOOD_BARLEY_HB_1961',
    'VAR_FOOD_BARLEY_HB_1962', 'VAR_FOOD_BARLEY_HB_42', 'VAR_FOOD_BARLEY_HB_1307',
    'VAR_TEFF_DZ_CR_387', 'VAR_TEFF_DZ_01_974', 'VAR_TEFF_DZ_01_196',
    'VAR_TEFF_DZ_01_354', 'VAR_TEFF_DZ_01_1880', 'VAR_TEFF_DZ_01_2053',
    'VAR_TEFF_DZ_01_99', 'VAR_TEFF_DZ_01_899', 'VAR_TEFF_DZ_01_1278',
    'VAR_TEFF_DZ_01_1281', 'VAR_TEFF_DZ_01_1285', 'VAR_TEFF_DZ_01_1445',
    'VAR_TEFF_DZ_01_1446', 'VAR_TEFF_DZ_01_146', 'VAR_BREAD_WHEAT_HAR_1685',
    'VAR_BREAD_WHEAT_HAR_604', 'VAR_BREAD_WHEAT_HAR_710', 'VAR_BREAD_WHEAT_HAR_1709',
    'VAR_BREAD_WHEAT_HAR_1595', 'VAR_BREAD_WHEAT_HAR_1407', 'VAR_BREAD_WHEAT_HAR_2501',
    'VAR_BREAD_WHEAT_ETBW_9089', 'VAR_BREAD_WHEAT_ETBW_9396', 'VAR_BREAD_WHEAT_ETBW_8572',
    'VAR_BREAD_WHEAT_ETBW_5520', 'VAR_DURUM_WHEAT_DZ_04_118', 'VAR_DURUM_WHEAT_DZ_2212'
}

def clean_code(*parts):
    s = "_".join(parts).upper()
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"\[.*?\]", "", s)
    s = re.sub(r"[^A-Z0-9]+", "_", s)
    return s.strip("_")

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

def check_varieties(values):
    """Guard validating SEED_VARIETY data quality strictly per section 2.6."""
    errs = []
    for v in values:
        name = (v.get("attributes") or {}).get("official_name", "").strip()
        if not name:
            errs.append(f"{v['value_id']}: no variety name")
        if "…" in v["value_display"] or "..." in v["value_display"]:
            errs.append(f"{v['value_id']}: truncated name {v['value_display']!r}")
        if v["value_display"].count("(") != v["value_display"].count(")"):
            errs.append(f"{v['value_id']}: unbalanced brackets {v['value_display']!r}")
        if re.search(r"[\u1200-\u137F]", v["value_display"]):
            errs.append(f"{v['value_id']}: Amharic in value_display; move it to display_i18n.am")
        if re.search(r"_\d{3}$", v["value_id"]) and v["value_id"] not in ALLOWED_NUMERIC_CODES:
            errs.append(f"{v['value_id']}: ends in a 3-digit number; a source row id? (allowlist it if it is part of the real name)")
    seen = collections.Counter(((v.get("attributes") or {}).get("crop"), v["value_display"].strip().lower()) for v in values)
    errs += [f"duplicate name within crop: {k}" for k, n in seen.items() if n > 1]
    if errs:
        sys.exit("check_varieties failed with errors:\n" + "\n".join(errs[:25]))
    print(f"check_varieties guard passed cleanly for {len(values)} varieties.")

def clean_variety_name(common_name, crop_name, row_id):
    raw = common_name.replace("''", "'").strip()

    # Strip prefixes like 'Bread Wheat -', 'Common bean /Haricot bean -', etc.
    crop_prefixes = [
        crop_name + ' -', crop_name + '-', 'Common bean /Haricot bean -', 
        'Common Bean /Haricot bean -', 'Common bean/Haricot bean -',
        'Common Bean/Haricot bean -', 'Common bean/ Haricot bean -',
        'Common bean/ Haricot bean --', 'common bean/ Haricot bean -',
        'Common bean -', 'Common Bean -', 'Fiel pea -', 'food barly-',
        'Food Barley -', 'Food Oats -', 'Rapeseed and Ethiopian mustard -',
        'Sweet potato -', 'Irish potato -', 'Taro -', 'Cassava -',
        'Tomato -', 'Garlic -', 'Onion -', 'Sweet/Hot Pepper -',
        'Cabbage -', 'Carrot -', 'Okra -', 'Coriander -', 'Cumin -',
        'Banana -', 'Avocado -', 'Cotton -', 'Tobaco -', 'Lettuce -',
        'Water melon -', 'Musk melon -', 'Broccoli -', 'Cauliflower -',
        'Rose -', 'Cacao -', 'Ethiopian mustard -', 'Linseed -',
        'Sesame -', 'Groundnut -', 'Sunflower -', 'Safflower -',
        'Soybean -', 'Mung bean -', 'Fenugreek -', 'Noug -', 'Rice -',
        'Finger Millet -', 'Triticale -', 'Emmer wheat (Aja) -',
        'Quinoa -', 'Faba bean -', 'Field pea -', 'Dekoko -', 'Chickpea -',
        'Cowpea -', 'Lentil -', 'Alfalfa -', 'Oats -', 'Pigeon pea -'
    ]
    for prefix in crop_prefixes:
        if raw.lower().startswith(prefix.lower()):
            raw = raw[len(prefix):].strip()
            break

    if ' - ' in raw:
        parts = raw.split(' - ', 1)
        if any(w in parts[0].lower() for w in ['wheat', 'barley', 'maize', 'tef', 'sorghum', 'bean', 'pea', 'oats', 'lentil', 'chickpea', 'potato', 'rice', 'mustard', 'linseed', 'sesame', 'sunflower']):
            raw = parts[1].strip()

    # Extract Amharic characters
    am_chars = ''.join(re.findall(r'[\u1200-\u137F]+', raw)).strip()
    am_display = am_chars if am_chars else None

    # Remove Amharic from english text
    eng = re.sub(r'[\u1200-\u137F]+', '', raw).strip()
    eng = eng.replace('…', '').replace('...', '').strip()

    # Clean double brackets
    eng = re.sub(r'\(\(', '(', eng)
    eng = re.sub(r'\)\)', ')', eng)

    # Clean unclosed/unopened brackets caused by ellipsis truncation
    if eng.startswith('(') and ')' not in eng:
        eng = eng[1:].strip()
    if '(' in eng and ')' not in eng:
        eng = re.sub(r'\([^\)]*$', '', eng).strip()
    if ')' in eng and '(' not in eng:
        eng = re.sub(r'\)[^\(]*$', '', eng).strip()

    diff = eng.count('(') - eng.count(')')
    if diff > 0:
        eng = eng + (')' * diff)
    elif diff < 0:
        eng = ('(' * (-diff)) + eng

    eng = re.sub(r'\(\s*\)', '', eng).strip()
    eng = re.sub(r'^(common bean|haricot bean|groundnut variety)\s*[-/]?\s*', '', eng, flags=re.I).strip()
    eng = eng.strip("'-/ ")
    eng = re.sub(r'\s+', ' ', eng)

    # Disambiguation for Awash white pea bean varieties
    if row_id == 763:
        eng = 'Awash-1'
    elif row_id == 227:
        eng = 'Awash Mitra'

    return eng, am_display

def convert_crop_commodities():
    print("Converting missing crop commodities...")
    missing_crops = [
        {
            "value_id": "CROP_OAT",
            "value_code": "CROP_OAT",
            "value_display": "Oat",
            "sort_order": 122,
            "display_i18n": {},
            "attributes": {
                "category": "CROPCAT_CEREAL",
                "scientific_name": "Avena sativa L."
            }
        },
        {
            "value_id": "CROP_PIGEON_PEA",
            "value_code": "CROP_PIGEON_PEA",
            "value_display": "Pigeon pea",
            "sort_order": 123,
            "display_i18n": {},
            "attributes": {
                "category": "CROPCAT_FOOD_LEGUME",
                "scientific_name": "Cajanus cajan (L.) Millsp."
            }
        },
        {
            "value_id": "CROP_ALFALFA",
            "value_code": "CROP_ALFALFA",
            "value_display": "Alfalfa",
            "sort_order": 124,
            "display_i18n": {},
            "attributes": {
                "category": "CROPCAT_OTHER",
                "scientific_name": "Medicago sativa L."
            }
        },
        {
            "value_id": "CROP_BRACHIARIA",
            "value_code": "CROP_BRACHIARIA",
            "value_display": "Brachiaria brizantha",
            "sort_order": 125,
            "display_i18n": {},
            "attributes": {
                "category": "CROPCAT_OTHER",
                "scientific_name": "Brachiaria brizantha (Hochst. ex A. Rich.) Stapf"
            }
        }
    ]
    out = os.path.join(ADDITIONS_DIR, "values/domains/agriculture/crop_commodity.json")
    write_json(out, {
        "description": "Additional crops required by MoA released varieties. Source: ethioseed.moa.gov.et snapshot.",
        "values": missing_crops
    })
    print(f"  {len(missing_crops)} crops written to {out}")

def convert_seed_varieties():
    print("Converting seed varieties with data quality fixes...")
    with open(os.path.join(BASE_PACK, "domains/agriculture/seed_variety.json"), encoding="utf-8") as f:
        base_varieties = json.load(f)
    existing_ids = {v["value_id"] for v in base_varieties["values"]}

    crop_map = {
        1: "CROP_MAIZE", 2: "CROP_BREAD_WHEAT", 3: "CROP_DURUM_WHEAT", 4: "CROP_BARLEY",
        5: "CROP_MALT_BARLEY", 6: "CROP_TEFF", 7: "CROP_SORGHUM", 9: "CROP_RICE",
        10: "CROP_FINGER_MILLET", 12: "CROP_TRITICALE", 13: "CROP_EMMER_WHEAT", 17: "CROP_QUINOA",
        18: "CROP_OAT", 19: "CROP_FABA_BEAN", 20: "CROP_FIELD_PEA", 21: "CROP_DEKOKO",
        22: "CROP_CHICKPEA", 23: "CROP_COWPEA", 24: "CROP_LENTIL", 25: "CROP_COMMON_BEAN",
        26: "CROP_SOYBEAN", 28: "CROP_MUNG_BEAN", 29: "CROP_FENUGREEK", 30: "CROP_NOUG",
        31: "CROP_LINSEED", 32: "CROP_RAPESEED", 33: "CROP_SESAME", 34: "CROP_GROUNDNUT",
        35: "CROP_SUNFLOWER", 36: "CROP_SAFFLOWER", 40: "CROP_POTATO", 41: "CROP_SWEET_POTATO",
        42: "CROP_TARO", 43: "CROP_CASSAVA", 45: "CROP_YAM", 46: "CROP_TOMATO", 47: "CROP_GARLIC",
        48: "CROP_ONION", 50: "CROP_PEPPER", 51: "CROP_CABBAGE", 52: "CROP_CARROT", 53: "CROP_OKRA",
        57: "CROP_CORIANDER", 65: "CROP_WHITE_CUMIN", 72: "CROP_LEMON_VERBENA", 80: "CROP_BANANA",
        84: "CROP_AVOCADO", 94: "CROP_COWPEA", 96: "CROP_PIGEON_PEA", 97: "CROP_OAT",
        102: "CROP_ALFALFA", 109: "CROP_COTTON", 113: "CROP_TOBACCO", 114: "CROP_ADZUKI_BEAN",
        115: "CROP_LIMA_BEAN", 116: "CROP_LETTUCE", 117: "CROP_WATERMELON", 118: "CROP_MUSKMELON",
        119: "CROP_BROCCOLI", 120: "CROP_CAULIFLOWER", 124: "CROP_KORARIMA", 125: "CROP_ROSE",
        126: "CROP_BRACHIARIA", 127: "CROP_SORGHUM", 128: "CROP_SOYBEAN", 129: "CROP_CACAO",
        132: "CROP_ETHIOPIAN_MUSTARD"
    }

    with open(CROP_SQL, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip().startswith("(")]

    values = []
    seen = set(existing_ids)
    dropped_nameless = []
    merged_duplicates = 0

    for i, line in enumerate(lines, start=1):
        l_clean = line.rstrip(",;").replace("''", "'")
        m = re.match(r"^\(\s*(\d+)\s*,\s*(\d+)\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*(?:NULL|'([^']*)')\s*,\s*(?:NULL|(\d+))\s*,\s*(?:NULL|DATE\s*'[^']*')\s*,\s*(?:NULL|'([^']*)')\s*,\s*(?:NULL|'([^']*)')", l_clean)
        if not m:
            continue
        row_id = int(m.group(1))
        crop_id = int(m.group(2))
        crop_name = m.group(3)
        common_name = m.group(4)
        release_year_str = m.group(6)
        maintainer = m.group(8)

        eng, am = clean_variety_name(common_name, crop_name, row_id)

        # Drop nameless varieties (38 rows in section 2.2)
        if not eng or not re.search(r'[a-zA-Z0-9]', eng):
            dropped_nameless.append(row_id)
            continue

        crop_code = crop_map.get(crop_id)
        if not crop_code:
            continue

        crop_prefix = crop_code.removeprefix("CROP_")
        vid = clean_code("VAR", crop_prefix, eng)
        if not vid or vid == f"VAR_{crop_prefix}":
            continue

        # Merge duplicates (section 2.3)
        if vid in seen:
            merged_duplicates += 1
            continue
        seen.add(vid)

        attrs = {
            "crop": crop_code,
            "official_name": eng
        }
        if release_year_str:
            try:
                yr = int(release_year_str)
                if 1950 <= yr <= 2100:
                    attrs["release_year"] = yr
            except ValueError:
                pass
        if maintainer and maintainer not in ("-", "Domestic", "NULL"):
            clean_m = maintainer.strip(" /")
            if clean_m:
                attrs["research_centre"] = clean_m

        clean_crop_disp = crop_name.replace('…', '').replace('...', '').strip()
        values.append({
            "value_id": vid,
            "value_code": vid,
            "value_display": f"{clean_crop_disp} – {eng}",
            "sort_order": 100 + len(values),
            "display_i18n": {"am": am} if am else {},
            "attributes": attrs
        })

    # Run check_varieties guard!
    check_varieties(values)

    out = os.path.join(ADDITIONS_DIR, "values/domains/agriculture/seed_variety.json")
    write_json(out, {
        "description": "MoA released varieties not in the base list. Source: ethioseed.moa.gov.et/crop-varieties-all (archived 2025-12-17).",
        "values": values
    })
    print(f"  {len(values)} varieties written to {out}")
    print(f"  Dropped {len(dropped_nameless)} nameless rows: {dropped_nameless}")
    print(f"  Merged {merged_duplicates} duplicate rows into unique codes.")

def convert_livestock_breeds():
    print("Converting livestock breeds...")
    species_map = {
        "Cattle": "LSTK_CATTLE",
        "Camel": "LSTK_CAMEL",
        "Sheep": "LSTK_SHEEP",
        "Goat": "LSTK_GOAT"
    }

    with open(BREED_SQL, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip().startswith("(")]

    values = []
    seen = set()

    for i, line in enumerate(lines, start=1):
        l_clean = line.rstrip(",;")
        parts = [p.strip() for p in l_clean.lstrip("(").rstrip(")").split(",")]
        name = parts[2].strip("' ")
        species = parts[4].strip("' ")
        btype = parts[5].strip("' ")

        if species not in species_map:
            continue

        bid = clean_code("BREED", species, name)
        if bid in seen:
            bid = f"{bid}_{i}"
        seen.add(bid)

        attrs = {
            "species": species_map[species]
        }
        if btype and btype != "NULL":
            attrs["breed_type"] = btype

        values.append({
            "value_id": bid,
            "value_code": bid,
            "value_display": name,
            "sort_order": i,
            "display_i18n": {},
            "attributes": attrs
        })

    doc = {
        "attribute_id": "LIVESTOCK_BREED_NAME",
        "attribute_code": "LIVESTOCK_BREED_NAME",
        "attribute_display": "Livestock breed name",
        "description": "National livestock breeds of Ethiopia. Source: National Livestock Data Standard for Ethiopia (MOA, March 2024).",
        "is_hierarchical": False,
        "attribute_schema": {
            "type": "object",
            "properties": {
                "species": {
                    "type": "string",
                    "x-list-ref": "LIVESTOCK_TYPE",
                    "title": "Species"
                },
                "breed_type": {
                    "type": "string",
                    "title": "Breed type"
                }
            },
            "required": ["species"],
            "additionalProperties": False
        },
        "values": values
    }
    out = os.path.join(ADDITIONS_DIR, "domains/agriculture/livestock_breed_name.json")
    write_json(out, doc)
    print(f"  {len(values)} breeds written to {out}")

def convert_livestock_sex():
    print("Writing livestock sex codelist...")
    doc = {
        "attribute_id": "LIVESTOCK_SEX",
        "attribute_code": "LIVESTOCK_SEX",
        "attribute_display": "Livestock sex",
        "description": "Animal biological and reproductive sex classification. Source: National Livestock Data Standard for Ethiopia (MOA, 2024).",
        "is_hierarchical": False,
        "values": [
            {
                "value_id": "SEX_MALE",
                "value_code": "SEX_MALE",
                "value_display": "Male",
                "sort_order": 1,
                "display_i18n": {}
            },
            {
                "value_id": "SEX_FEMALE",
                "value_code": "SEX_FEMALE",
                "value_display": "Female",
                "sort_order": 2,
                "display_i18n": {}
            },
            {
                "value_id": "SEX_MALE_NEUTER",
                "value_code": "SEX_MALE_NEUTER",
                "value_display": "Castrated male",
                "sort_order": 3,
                "display_i18n": {}
            },
            {
                "value_id": "SEX_FEMALE_NEUTER",
                "value_code": "SEX_FEMALE_NEUTER",
                "value_display": "Female neuter",
                "sort_order": 4,
                "display_i18n": {}
            }
        ]
    }
    out = os.path.join(ADDITIONS_DIR, "domains/agriculture/livestock_sex.json")
    write_json(out, doc)
    print(f"  Livestock sex written to {out}")

def convert_fertilizers():
    print("Writing fertilizer additions...")
    values = [
        {
            "value_id": "FERT_BIO_RHIZO",
            "value_code": "FERT_BIO_RHIZO",
            "value_display": "Bio-Rhizobium",
            "sort_order": 8,
            "display_i18n": {}
        },
        {
            "value_id": "FERT_ZINC_BORON",
            "value_code": "FERT_ZINC_BORON",
            "value_display": "Zinc and boron micronutrients",
            "sort_order": 9,
            "display_i18n": {}
        },
        {
            "value_id": "FERT_LIME",
            "value_code": "FERT_LIME",
            "value_display": "Agricultural lime",
            "sort_order": 10,
            "display_i18n": {}
        }
    ]
    out = os.path.join(ADDITIONS_DIR, "values/domains/agriculture/fertilizer_type.json")
    write_json(out, {
        "description": "Additional fertilizer and soil amendment products from MoA input catalog.",
        "values": values
    })
    print(f"  {len(values)} fertilizer values written to {out}")

if __name__ == "__main__":
    convert_crop_commodities()
    convert_seed_varieties()
    convert_livestock_breeds()
    convert_livestock_sex()
    convert_fertilizers()
    print("All conversions completed successfully.")
