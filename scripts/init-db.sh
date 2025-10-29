#!/bin/bash
# Database initialization script for PostgreSQL with PostGIS
# This script is run automatically when the container is first created

set -e

# Enable PostGIS extension
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable PostGIS extension
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS postgis_topology;
    
    -- Create Temporal database for workflow orchestration
    CREATE DATABASE temporal;
    CREATE USER temporal WITH PASSWORD 'temporal_password';
    GRANT ALL PRIVILEGES ON DATABASE temporal TO temporal;
EOSQL

# Grant Temporal user permissions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "temporal" <<-EOSQL
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO temporal;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO temporal;
    GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO temporal;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO temporal;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO temporal;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO temporal;
EOSQL

echo "✓ PostGIS extension enabled"
echo "✓ Temporal database created"
echo "✓ Database initialization complete"
