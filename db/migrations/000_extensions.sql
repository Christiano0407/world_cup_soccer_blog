-- =============================================================
-- FIFA World Cup Platform — Migration 000: Extensions & Schemas
-- =============================================================
-- Run order: FIRST — before any table creation
-- Author   : Platform DBA
-- Env      : PostgreSQL 16+
-- =============================================================

-- Enable UUID generation (used for users table)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- Enable better text search (blog / player names)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- Enable statistical functions
CREATE EXTENSION IF NOT EXISTS tablefunc;

-- Schemas isolation: raw data vs clean data vs analytics
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS warehouse;
CREATE SCHEMA IF NOT EXISTS audit;

-- Default search path
ALTER DATABASE "data-world-cup" SET search_path TO public, warehouse, audit;  

COMMENT ON SCHEMA raw       IS 'Staging area — CSV data before validation';
COMMENT ON SCHEMA public    IS 'Production data — validated and normalized';
COMMENT ON SCHEMA warehouse IS 'Analytical layer — pre-aggregated for dashboards';
COMMENT ON SCHEMA audit     IS 'Audit logs — row-level change history';