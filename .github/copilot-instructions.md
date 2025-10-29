# Voluntier: AI Development Guidelines

## Project Context

Voluntier is a **cross-platform community volunteer connection application** in **Phase 1: Foundation** (Q4 2025). The tech stack:
- **Backend**: FastAPI (Python 3.13+) with async/await
- **Database**: PostgreSQL 17+ with PostGIS for geospatial queries
- **Mobile**: React Native (planned)
- **Caching**: Redis for sessions and real-time features

See `/PRD.md` for complete architecture and`/README.md` for setup.

## Critical: UV Package Manager

**ALL dependency and Python execution must use `uv`:**

```bash
# Add dependencies (NEVER manually edit pyproject.toml)
uv add fastapi uvicorn sqlalchemy
uv add --dev pytest black ruff mypy

# Run Python commands (ALWAYS prefix with 'uv run')
uv run python main.py
uv run fastapi dev main.py
uv run pytest
uv run black .

# Only if 'uv add' fails:
uv pip install <package>
```

**Forbidden**: `pip install`, manually editing dependencies in `pyproject.toml`, running Python without `uv run`.

## ⚠️ CRITICAL: User Consent for Downloads

**ABSOLUTELY FORBIDDEN without explicit user approval:**

- ❌ Downloading large files (>10MB) 
- ❌ Downloading AI models (any size)
- ❌ Downloading pre-trained weights, embeddings, or model checkpoints
- ❌ Installing packages that auto-download models (sentence-transformers, spacy models, etc.)
- ❌ Downloading datasets, corpora, or large data files

**Required process:**
1. **STOP** before any download that matches above criteria
2. **EXPLAIN** what will be downloaded, why, and how much disk space it requires
3. **ASK** the user explicitly: "This will download [X MB/GB] of [description]. Proceed?"
4. **WAIT** for clear approval

**Examples requiring consent:**
```bash
# ❌ FORBIDDEN without asking first:
uv add sentence-transformers  # May auto-download models
uv add spacy && uv run python -m spacy download en_core_web_sm
uv add torch torchvision  # Large packages
wget https://example.com/large-dataset.zip
```

When in doubt about file size or model downloads, **ASK THE USER FIRST**.

## Project Structure (Planned)

```
app/
├── main.py              # FastAPI entry point
├── config.py           # Settings with pydantic-settings
├── database.py         # Async SQLAlchemy setup
├── models/             # SQLAlchemy ORM models
├── schemas/            # Pydantic request/response models
├── api/v1/             # API routes by resource
├── services/           # Business logic (matching, auth, reputation)
├── core/               # Security, utils
└── tests/              # Pytest with async support
```

## Development Workflow

```bash
# Setup (first time)
uv sync --all-extras

# Development server with auto-reload
uv run fastapi dev main.py

# Tests with coverage
uv run pytest --cov=app tests/

# Code quality (run before commits)
uv run black . && uv run ruff check --fix . && uv run mypy app/

# Database migrations (when added)
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

## Core Patterns

### Authentication Flow
- OAuth2 with JWT tokens (see PRD §4.3.1 for endpoints)
- Passwords: bcrypt/Argon2 hashing, never plain text
- Token refresh endpoint with rotation strategy
- Rate limiting: 10 requests/minute on auth endpoints

### Geospatial Matching
- PostGIS `ST_DWithin` for location-based queries
- GiST indexes on location columns
- Distance in kilometers, convert to meters for queries
- Matching weights: Location 40%, Skills 30%, Availability 20%, Reputation 10%

### Database Sessions
```python
# Always use async context manager
async with db.begin():
    result = await db.execute(query)
```

### Error Handling
- Specific HTTPException with appropriate status codes
- Log with context: `logger.error("msg", exc_info=True, extra={"user_id": id})`
- NEVER use bare `except:` or suppress errors

## Documentation Requirements

**Every change requires:**
1. **Inline docs**: Google-style docstrings with type hints, examples
2. **CHANGELOG.md**: Append-only with UTC timestamp (format: `### 2025-10-29 14:32 UTC - Added`)
3. **README.md**: Update if public API or setup changes
4. **Git commit**: Stage all → commit with conventional format → push

Example changelog entry:
```markdown
### 2025-10-29 16:45 UTC - Added
- Implemented geospatial matching with PostGIS
- Added GiST index on opportunities.location
- Updated Match model to include distance_km field

### 2025-10-29 16:45 UTC - Performance
- Added Redis caching for opportunities (5min TTL)
- Reduced average match time from 450ms to 180ms
```

## Testing Standards

- All tests use pytest with async support
- Fixtures in `tests/conftest.py`
- TestClient from FastAPI for endpoint tests
- Database: use test DB, transactions rolled back after each test
- **NEVER skip/delete failing tests** - fix code or update test appropriately

Example:
```python
@pytest.fixture
async def test_user(db_session):
    user = User(email="test@example.com", is_verified=True)
    db_session.add(user)
    await db_session.commit()
    return user

async def test_create_opportunity(auth_headers, db_session):
    response = client.post("/api/v1/opportunities", 
                          json={...}, 
                          headers=auth_headers)
    assert response.status_code == 201
    # Verify DB state
    opportunity = await db_session.get(Opportunity, response.json()["id"])
    assert opportunity is not None
```

## Key Business Logic

### Identity Verification (Phase 1 Priority)
- Multi-factor: document upload, community validation, in-person option
- Privacy-preserving: field-level encryption for PII
- Balance: security vs. accessibility (see PRD §3.1.1)

### Reputation System
- Community-based, non-competitive (no leaderboards)
- Time-decay on old reviews
- Weighted by reviewer reputation
- Appeal/dispute process for contested ratings
- Recovery pathways for users with negative feedback

### Matching Algorithm
Location-based with PostgreSQL PostGIS:
```sql
-- Example pattern
SELECT * FROM opportunities 
WHERE status = 'open' 
  AND ST_DWithin(location, ST_MakePoint(lng, lat), max_distance_m)
ORDER BY start_time
```

## Security Checklist

- [ ] All user input validated (Pydantic schemas)
- [ ] Parameterized queries (SQLAlchemy prevents SQL injection)
- [ ] Secrets in `.env`, loaded via pydantic-settings
- [ ] HTTPS/TLS for all communication
- [ ] Rate limiting on sensitive endpoints
- [ ] CORS configured appropriately
- [ ] Never log passwords, tokens, or PII

## Common Pitfalls

1. **Downloading files/models without consent** → ALWAYS ask user first for >10MB or any AI models
2. **Running Python without `uv run`** → Dependencies won't be found
3. **Editing pyproject.toml dependencies** → Use `uv add/remove` instead
4. **Skipping changelog updates** → Required for ALL changes
5. **Bare except clauses** → Use specific exception types
6. **Forgetting async/await** → Database and external calls must be async
7. **Missing type hints** → Required on all function signatures

## Quick Reference

- **API Docs**: Run server, visit `http://localhost:8000/docs`
- **PRD**: `/PRD.md` (complete technical architecture, Phase 1-3 roadmap)
- **Phase 1 Focus**: Identity verification, reputation system, matching algorithm
- **Target**: 10K users by end of Q4 2025, 70% verification completion

## Questions to Answer

Before implementing features, verify:
- Does this align with Phase 1 priorities? (identity, reputation, matching)
- Is geospatial indexing needed? (opportunities with location queries)
- Should this be cached? (frequently accessed, low change rate)
- What's the authentication requirement? (public, authenticated, admin)
- Are we handling PII? (requires field-level encryption, audit logging)
