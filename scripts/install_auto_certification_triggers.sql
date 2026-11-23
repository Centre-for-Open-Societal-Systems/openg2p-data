-- ==============================================================================
-- Certification Auto-Default Trigger & Migration for OpenG2P Master Data Service
-- ==============================================================================
-- Purpose:
--   1. Adds 'certification_status' (CERTIFIED, UNCERTIFIED, PROVISIONAL)
--      exclusively to all CROP and SEED catalogues:
--      - Server Staging/Prod: CROP_COMMODITY, CROP_CATEGORY, CROP_VARIETY,
--        SEED_VARIETY, CROP_CONDITION, CROP_DAMAGE_CAUSE, CROP_DISEASE,
--        CROP_END_USE, CROP_GROWTH_STAGE, CROPPING_SYSTEM, CROP_SEASON, CROP_TEST
--      - Local Development: CROP_CATALOG, CROP_CATEGORY_CATALOG,
--        CROP_VARIETY_CATALOG, SEED_DEMAND_BY_CROP_CATALOG
--   2. General catalogues (Geography, Demography, Bank, etc.) do NOT receive 
--      any certification fields.
--   3. Backfills all existing crop entries to default 'CERTIFIED'.
--   4. Installs a database trigger so ANY newly created or inserted crop item
--      automatically defaults to 'CERTIFIED'.
-- ==============================================================================

BEGIN;

-- ------------------------------------------------------------------------------
-- 1. Clean up any legacy triggers
-- ------------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_g2p_attributes_auto_cert ON g2p_attributes;
DROP TRIGGER IF EXISTS trg_g2p_list_versions_auto_cert ON g2p_list_versions;
DROP FUNCTION IF EXISTS g2p_catalogue_auto_certification_schema();

-- ------------------------------------------------------------------------------
-- 2. Update JSON Schema in g2p_attributes for all CROP and SEED catalogues
-- ------------------------------------------------------------------------------
UPDATE g2p_attributes
SET attribute_schema = CASE 
    WHEN attribute_schema IS NULL OR jsonb_typeof(attribute_schema) != 'object' THEN
        '{"type": "object", "properties": {"certification_status": {"type": "string", "enum": ["CERTIFIED", "UNCERTIFIED", "PROVISIONAL"], "default": "CERTIFIED", "title": "Certification Status", "description": "Official certification flag: CERTIFIED, UNCERTIFIED, or PROVISIONAL"}}}'::jsonb
    WHEN attribute_schema->'properties' IS NULL OR jsonb_typeof(attribute_schema->'properties') != 'object' THEN
        jsonb_set(attribute_schema, '{properties}', '{"certification_status": {"type": "string", "enum": ["CERTIFIED", "UNCERTIFIED", "PROVISIONAL"], "default": "CERTIFIED", "title": "Certification Status", "description": "Official certification flag: CERTIFIED, UNCERTIFIED, or PROVISIONAL"}}'::jsonb)
    ELSE
        jsonb_set(attribute_schema, '{properties,certification_status}', '{"type": "string", "enum": ["CERTIFIED", "UNCERTIFIED", "PROVISIONAL"], "default": "CERTIFIED", "title": "Certification Status", "description": "Official certification flag: CERTIFIED, UNCERTIFIED, or PROVISIONAL"}'::jsonb)
END
WHERE attribute_code LIKE 'CROP%' 
   OR attribute_code LIKE 'CROPPING%' 
   OR attribute_code LIKE 'SEED_%'
   OR attribute_code IN ('CROP_COMMODITY', 'CROP_CATEGORY', 'CROP_VARIETY', 'SEED_VARIETY', 'CROP_CATALOG', 'CROP_CATEGORY_CATALOG', 'CROP_VARIETY_CATALOG');

-- ------------------------------------------------------------------------------
-- 3. Update JSON Schema in g2p_list_versions across all versions
-- ------------------------------------------------------------------------------
ALTER TABLE g2p_list_versions DISABLE TRIGGER trg_g2p_list_versions_guard;

UPDATE g2p_list_versions
SET attribute_schema = CASE 
    WHEN attribute_schema IS NULL OR jsonb_typeof(attribute_schema) != 'object' THEN
        '{"type": "object", "properties": {"certification_status": {"type": "string", "enum": ["CERTIFIED", "UNCERTIFIED", "PROVISIONAL"], "default": "CERTIFIED", "title": "Certification Status", "description": "Official certification flag: CERTIFIED, UNCERTIFIED, or PROVISIONAL"}}}'::jsonb
    WHEN attribute_schema->'properties' IS NULL OR jsonb_typeof(attribute_schema->'properties') != 'object' THEN
        jsonb_set(attribute_schema, '{properties}', '{"certification_status": {"type": "string", "enum": ["CERTIFIED", "UNCERTIFIED", "PROVISIONAL"], "default": "CERTIFIED", "title": "Certification Status", "description": "Official certification flag: CERTIFIED, UNCERTIFIED, or PROVISIONAL"}}'::jsonb)
    ELSE
        jsonb_set(attribute_schema, '{properties,certification_status}', '{"type": "string", "enum": ["CERTIFIED", "UNCERTIFIED", "PROVISIONAL"], "default": "CERTIFIED", "title": "Certification Status", "description": "Official certification flag: CERTIFIED, UNCERTIFIED, or PROVISIONAL"}'::jsonb)
END
WHERE list_id IN (
    SELECT attribute_id FROM g2p_attributes 
    WHERE attribute_code LIKE 'CROP%' 
       OR attribute_code LIKE 'CROPPING%' 
       OR attribute_code LIKE 'SEED_%'
       OR attribute_code IN ('CROP_COMMODITY', 'CROP_CATEGORY', 'CROP_VARIETY', 'SEED_VARIETY', 'CROP_CATALOG', 'CROP_CATEGORY_CATALOG', 'CROP_VARIETY_CATALOG')
);

ALTER TABLE g2p_list_versions ENABLE TRIGGER trg_g2p_list_versions_guard;

-- ------------------------------------------------------------------------------
-- 4. Backfill existing line items in g2p_list_version_values
-- ------------------------------------------------------------------------------
ALTER TABLE g2p_list_version_values DISABLE TRIGGER trg_g2p_list_version_values_guard;

-- Auto-fill CERTIFIED for all existing items that do not yet have certification_status
UPDATE g2p_list_version_values
SET attributes = jsonb_set(COALESCE(attributes, '{}'::jsonb), '{certification_status}', '"CERTIFIED"'::jsonb)
WHERE list_id IN (
    SELECT attribute_id FROM g2p_attributes 
    WHERE attribute_code LIKE 'CROP%' 
       OR attribute_code LIKE 'CROPPING%' 
       OR attribute_code LIKE 'SEED_%'
       OR attribute_code IN ('CROP_COMMODITY', 'CROP_CATEGORY', 'CROP_VARIETY', 'SEED_VARIETY', 'CROP_CATALOG', 'CROP_CATEGORY_CATALOG', 'CROP_VARIETY_CATALOG')
)
AND (attributes->>'certification_status' IS NULL OR attributes->>'certification_status' = '');

-- Set representative demo UNCERTIFIED and PROVISIONAL flags:
-- (A) For Server CROP_COMMODITY:
UPDATE g2p_list_version_values
SET attributes = jsonb_set(attributes, '{certification_status}', '"UNCERTIFIED"'::jsonb)
WHERE list_id = 'CROP_COMMODITY' AND value_code = 'CROP_QUINOA';

UPDATE g2p_list_version_values
SET attributes = jsonb_set(attributes, '{certification_status}', '"PROVISIONAL"'::jsonb)
WHERE list_id = 'CROP_COMMODITY' AND value_code = 'CROP_BREAD_WHEAT';

UPDATE g2p_list_version_values
SET attributes = jsonb_set(attributes, '{certification_status}', '"UNCERTIFIED"'::jsonb)
WHERE ctid = (
    SELECT ctid FROM g2p_list_version_values 
    WHERE list_id = 'CROP_COMMODITY' 
    LIMIT 1
);

UPDATE g2p_list_version_values
SET attributes = jsonb_set(attributes, '{certification_status}', '"PROVISIONAL"'::jsonb)
WHERE ctid = (
    SELECT ctid FROM g2p_list_version_values 
    WHERE list_id = 'CROP_COMMODITY' 
      AND attributes->>'certification_status' != 'UNCERTIFIED' 
    LIMIT 1
);

-- (B) For Local CROP_CATALOG:
UPDATE g2p_list_version_values
SET attributes = jsonb_set(attributes, '{certification_status}', '"UNCERTIFIED"'::jsonb)
WHERE list_id = 'CROP_CATALOG' AND value_code = '1';

UPDATE g2p_list_version_values
SET attributes = jsonb_set(attributes, '{certification_status}', '"PROVISIONAL"'::jsonb)
WHERE list_id = 'CROP_CATALOG' AND value_code = '5';

-- (C) For CROP_VARIETY / SEED_VARIETY / CROP_VARIETY_CATALOG:
UPDATE g2p_list_version_values
SET attributes = jsonb_set(attributes, '{certification_status}', '"UNCERTIFIED"'::jsonb)
WHERE ctid = (
    SELECT ctid FROM g2p_list_version_values 
    WHERE list_id IN ('CROP_VARIETY', 'SEED_VARIETY', 'CROP_VARIETY_CATALOG') 
    LIMIT 1
);

UPDATE g2p_list_version_values
SET attributes = jsonb_set(attributes, '{certification_status}', '"PROVISIONAL"'::jsonb)
WHERE ctid = (
    SELECT ctid FROM g2p_list_version_values 
    WHERE list_id IN ('CROP_VARIETY', 'SEED_VARIETY', 'CROP_VARIETY_CATALOG') 
      AND attributes->>'certification_status' != 'UNCERTIFIED' 
    LIMIT 1
);

ALTER TABLE g2p_list_version_values ENABLE TRIGGER trg_g2p_list_version_values_guard;

-- ------------------------------------------------------------------------------
-- 5. Trigger Function: Automatically default certification_status to 'CERTIFIED'
--    ONLY for CROP/SEED catalogues or catalogues defining certification_status
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION g2p_catalogue_auto_certification_value()
RETURNS trigger AS $$
DECLARE
    has_cert_schema boolean := false;
BEGIN
    -- Check if this is a crop or seed catalog
    IF NEW.list_id LIKE 'CROP%' OR NEW.list_id LIKE 'CROPPING%' OR NEW.list_id LIKE 'SEED_%' THEN
        has_cert_schema := true;
    ELSE
        SELECT (attribute_schema->'properties'->'certification_status' IS NOT NULL)
        INTO has_cert_schema
        FROM g2p_list_versions
        WHERE list_id = NEW.list_id AND version_no = NEW.version_no;
    END IF;

    -- Automatically set default 'CERTIFIED' if the catalogue uses certification_status
    IF has_cert_schema THEN
        IF NEW.attributes IS NULL OR jsonb_typeof(NEW.attributes) != 'object' THEN
            NEW.attributes := '{"certification_status": "CERTIFIED"}'::jsonb;
        ELSIF NEW.attributes->>'certification_status' IS NULL OR NEW.attributes->>'certification_status' = '' THEN
            NEW.attributes := jsonb_set(NEW.attributes, '{certification_status}', '"CERTIFIED"'::jsonb);
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------------------------
-- 6. Install Trigger on g2p_list_version_values (Line Items)
-- ------------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_g2p_list_values_auto_cert ON g2p_list_version_values;
CREATE TRIGGER trg_g2p_list_values_auto_cert
BEFORE INSERT ON g2p_list_version_values
FOR EACH ROW
EXECUTE FUNCTION g2p_catalogue_auto_certification_value();

COMMIT;
