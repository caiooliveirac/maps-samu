-- ============================================
-- MAPS-SAMU: Database Initialization
-- Runs once on first container start
-- ============================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- fuzzy text search for addresses
CREATE EXTENSION IF NOT EXISTS unaccent;   -- normalize accented chars (Brazilian Portuguese)

-- Confirm extensions
DO $$
BEGIN
    RAISE NOTICE 'PostGIS version: %', PostGIS_Version();
    RAISE NOTICE 'Extensions loaded successfully';
END $$;
