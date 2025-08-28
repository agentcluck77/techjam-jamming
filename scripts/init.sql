-- Database initialization script - Phase 1D
-- Basic setup for PostgreSQL container

-- Ensure database exists (should be created by environment variable)
-- CREATE DATABASE IF NOT EXISTS geolegal;

-- Basic extensions we might need
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE geolegal TO "user";