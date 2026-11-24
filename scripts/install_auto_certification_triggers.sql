-- ==============================================================================
-- Certification Auto-Default Trigger & Migration for OpenG2P Master Data Service
-- ==============================================================================
-- Purpose:
--   1. Adds 'certification_status' (CERTIFIED, UNCERTIFIED, PROVISIONAL)
--      exclusively to official CROP and SEED VARIETY catalogues:
--      - Server Staging/Prod: CROP_COMMODITY, CROP_CATEGORY, CROP_VARIETY,
--        SEED_VARIETY, and other CROP_% domain catalogues.
--      - Local Development: CROP_CATALOG, CROP_CATEGORY_CATALOG,
--        CROP_VARIETY_CATALOG.
--   2. General catalogues (Geography, Demography, Bank, SEED_SOURCE, etc.) 
--      do NOT receive any certification fields.
--   3. Safely backfills all existing crop entries to default 'CERTIFIED'
--      (safely handles JSON null / non-object attributes).
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
-- 2. Update JSON Schema in g2p_attributes for official CROP catalogues
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
WHERE attribute_code IN (
    'CROP_COMMODITY', 'CROP_CATEGORY', 'CROP_VARIETY', 'SEED_VARIETY',
    'CROP_CATALOG', 'CROP_CATEGORY_CATALOG', 'CROP_VARIETY_CATALOG'
) OR attribute_code LIKE 'CROP_%';

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
    WHERE attribute_code IN (
        'CROP_COMMODITY', 'CROP_CATEGORY', 'CROP_VARIETY', 'SEED_VARIETY',
        'CROP_CATALOG', 'CROP_CATEGORY_CATALOG', 'CROP_VARIETY_CATALOG'
    ) OR attribute_code LIKE 'CROP_%'
);

ALTER TABLE g2p_list_versions ENABLE TRIGGER trg_g2p_list_versions_guard;

-- ------------------------------------------------------------------------------
-- 4. Backfill existing line items in g2p_list_version_values
-- ------------------------------------------------------------------------------
ALTER TABLE g2p_list_version_values DISABLE TRIGGER trg_g2p_list_version_values_guard;

-- Auto-fill CERTIFIED for all existing items that do not yet have certification_status.
-- Handles rows where attributes is SQL NULL or stored as a JSON null scalar.
UPDATE g2p_list_version_values
SET attributes = jsonb_set(
    CASE 
        WHEN attributes IS NOT NULL AND jsonb_typeof(attributes) = 'object' THEN attributes 
        ELSE '{}'::jsonb 
    END,
    '{certification_status}',
    '"CERTIFIED"'::jsonb
)
WHERE list_id IN (
    SELECT attribute_id FROM g2p_attributes 
    WHERE attribute_code IN (
        'CROP_COMMODITY', 'CROP_CATEGORY', 'CROP_VARIETY', 'SEED_VARIETY',
        'CROP_CATALOG', 'CROP_CATEGORY_CATALOG', 'CROP_VARIETY_CATALOG'
    ) OR attribute_code LIKE 'CROP_%'
)
AND (
    attributes IS NULL 
    OR jsonb_typeof(attributes) != 'object' 
    OR attributes->>'certification_status' IS NULL 
    OR attributes->>'certification_status' = ''
);

ALTER TABLE g2p_list_version_values ENABLE TRIGGER trg_g2p_list_version_values_guard;

-- ------------------------------------------------------------------------------
-- 5. Trigger Function: Automatically default certification_status to 'CERTIFIED'
--    ONLY for official CROP catalogues or catalogues defining certification_status
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION g2p_catalogue_auto_certification_value()
RETURNS trigger AS $$
DECLARE
    has_cert_schema boolean := false;
BEGIN
    -- Check if this is an official crop catalog
    IF NEW.list_id IN ('CROP_COMMODITY', 'CROP_CATEGORY', 'CROP_VARIETY', 'SEED_VARIETY', 'CROP_CATALOG', 'CROP_CATEGORY_CATALOG', 'CROP_VARIETY_CATALOG')
       OR NEW.list_id LIKE 'CROP_%' THEN
        has_cert_schema := true;
    ELSE
        SELECT (attribute_schema->'properties'->'certification_status' IS NOT NULL)
        INTO has_cert_schema
        FROM g2p_list_versions
        WHERE list_id = NEW.list_id AND version_no = NEW.version_no;
    END IF;

    -- Automatically default certification_status to 'CERTIFIED' if not specified
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
