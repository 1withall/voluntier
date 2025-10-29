# Changelog

All notable changes to the Voluntier project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 2025-01-23 16:45 UTC - Added
- Implemented database models with PostGIS support:
  - User model with verification fields (document/community/in-person), reputation scoring, PostGIS Point location
  - Opportunity model with PostGIS location, GiST indexes for geospatial queries
  - Match model with scoring algorithm (location 40%, skills 30%, availability 20%, reputation 10%)
  - Review model with time-decay, weighted reputation calculation, dispute/appeal process
- Set up Alembic for database migrations with async support
- Configured async SQLAlchemy engine with asyncpg driver
- Added comprehensive docstrings and examples for all models
- Installed GeoAlchemy2 for PostGIS geometry types

### 2025-01-23 16:15 UTC - Added
- Created async database connection setup in app/database.py
- Implemented FastAPI application with lifespan management in main.py
- Added configuration management with pydantic-settings in app/config.py
- Created .env.example template with database and security settings
- Enabled PostGIS extension initialization on startup
- Added health check endpoints (/ and /health)

### 2025-01-23 15:50 UTC - Added
- Initial project structure created
- Installed core dependencies: FastAPI, SQLAlchemy, asyncpg, Alembic, pydantic-settings, passlib, python-jose
- Installed dev dependencies: pytest, pytest-asyncio, black, ruff, mypy
- Created directory structure: app/{models,schemas,api/v1,services,core}/, tests/
- Added comprehensive PRD with Phase 1-3 roadmap
- Created .github/copilot-instructions.md with development guidelines

## Notes

- All timestamps are in UTC
- Commits follow Conventional Commits format
- Breaking changes are marked with BREAKING CHANGE in commit messages
