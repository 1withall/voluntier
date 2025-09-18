-- Initialize database for Voluntier
-- This script is run when the PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create additional user if needed
-- The main user is created via environment variables

-- Create indexes for better performance
-- (These will be created by Alembic migrations, but included here as reference)

-- Users table indexes
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_verification_status ON users(verification_status);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role ON users(role);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_is_active ON users(is_active);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_skills_gin ON users USING gin(skills);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_interests_gin ON users USING gin(interests);

-- Events table indexes  
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_organizer_id ON events(organizer_id);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_organization_id ON events(organization_id);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_status ON events(status);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_start_date ON events(start_date);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_location_gist ON events USING gist(point(longitude, latitude));
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_categories_gin ON events USING gin(categories);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_required_skills_gin ON events USING gin(required_skills);

-- Event registrations indexes
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_registrations_user_id ON event_registrations(user_id);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_registrations_event_id ON event_registrations(event_id);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_registrations_status ON event_registrations(status);

-- Organizations indexes
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_organizations_user_id ON organizations(user_id);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_organizations_verification_status ON organizations(verification_status);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_organizations_categories_gin ON organizations USING gin(categories);

-- Messages indexes
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_recipient_id ON messages(recipient_id);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_event_id ON messages(event_id);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_message_type ON messages(message_type);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_is_read ON messages(is_read);

-- Audit logs indexes
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_resource_id ON audit_logs(resource_id);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- System metrics indexes
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_metrics_metric_name ON system_metrics(metric_name);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_metrics_dimensions_gin ON system_metrics USING gin(dimensions);

-- Full-text search indexes
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_fts ON events USING gin(to_tsvector('english', title || ' ' || description));
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_organizations_fts ON organizations USING gin(to_tsvector('english', legal_name || ' ' || display_name || ' ' || coalesce(description, '')));

COMMIT;