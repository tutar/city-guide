-- Initialize City Guide Smart Assistant Database
-- This script runs when PostgreSQL container starts

-- Create additional database for testing if needed
CREATE DATABASE cityguide_test;

-- Grant privileges to the application user
GRANT ALL PRIVILEGES ON DATABASE cityguide TO cityguide_user;
GRANT ALL PRIVILEGES ON DATABASE cityguide_test TO cityguide_user;

-- Create extensions that might be needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set default search path
ALTER DATABASE cityguide SET search_path TO public;
ALTER DATABASE cityguide_test SET search_path TO public;
