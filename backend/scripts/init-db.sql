-- =============================================================================
-- PostgreSQL Initialization Script
-- =============================================================================
-- This script runs when PostgreSQL container starts for the first time.
-- It creates necessary extensions and sets up the database.
-- =============================================================================

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";    -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";      -- Trigram similarity (for search)

-- Create schema (optional, for organization)
-- CREATE SCHEMA IF NOT EXISTS champion;

-- Set timezone
SET timezone = 'Europe/Paris';

-- Create indexes for common queries (will be created by SQLAlchemy, but just in case)
-- These are placeholder comments - actual tables are created by SQLAlchemy

-- Performance tuning for the session
SET work_mem = '256MB';
SET maintenance_work_mem = '512MB';

-- Log slow queries (for debugging)
-- ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1 second

-- Vacuum settings for production
-- ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1;
-- ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05;

-- Connection limits
-- ALTER SYSTEM SET max_connections = 200;

-- Grant permissions (if using separate users)
-- GRANT ALL PRIVILEGES ON DATABASE champion_clone TO champion;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO champion;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO champion;

-- Done
SELECT 'Database initialized successfully' AS status;
