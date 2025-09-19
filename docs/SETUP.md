# Development Environment Setup

This guide provides detailed instructions for setting up the Voluntier development environment on different platforms.

## Prerequisites

### Required Software

#### Node.js and npm
- **Node.js**: 18.0.0 or later
- **npm**: 9.0.0 or later

**Installation:**
```bash
# Using Node Version Manager (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# Verify installation
node --version
npm --version
```

#### Python and uv
- **Python**: 3.12 or later
- **uv**: Latest version for package management

**Installation:**
```bash
# Install Python 3.12 (Ubuntu/Debian)
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev

# Install Python 3.12 (macOS with Homebrew)
brew install python@3.12

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
python3.12 --version
uv --version
```

#### Docker and Docker Compose
- **Docker**: Latest stable version
- **Docker Compose**: v2.0 or later

**Installation:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# macOS
brew install --cask docker

# Windows
# Download Docker Desktop from https://docker.com/products/docker-desktop

# Verify installation
docker --version
docker-compose --version
```

#### Git
- **Git**: 2.30 or later

```bash
# Ubuntu/Debian
sudo apt install git

# macOS
brew install git

# Verify installation
git --version
```

### Optional Tools

#### Development Tools
```bash
# VS Code (recommended editor)
# Download from https://code.visualstudio.com/

# Useful VS Code extensions:
# - TypeScript and JavaScript Language Features
# - Python
# - Docker
# - GitLens
# - Prettier
# - ESLint
# - Tailwind CSS IntelliSense

# Alternative editors
brew install --cask cursor    # macOS
# or use vim, emacs, WebStorm, PyCharm
```

#### Database Tools
```bash
# PostgreSQL client
sudo apt install postgresql-client  # Ubuntu/Debian
brew install postgresql             # macOS

# Redis client
sudo apt install redis-tools        # Ubuntu/Debian
brew install redis                  # macOS

# Neo4j Desktop (GUI)
# Download from https://neo4j.com/download/
```

## Project Setup

### 1. Clone the Repository

```bash
# Clone your fork or the main repository
git clone https://github.com/YOUR_USERNAME/voluntier.git
cd voluntier

# Add upstream remote (if working with a fork)
git remote add upstream https://github.com/voluntier/voluntier.git
```

### 2. Frontend Setup

```bash
# Install dependencies
npm install

# Verify installation
npm run type-check
npm run lint

# Start development server
npm run dev
```

**Verify frontend setup:**
- Open http://localhost:5173
- You should see the Voluntier application
- Hot reload should work when you edit files

### 3. Backend Setup

#### Install Dependencies
```bash
cd backend

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Alternative: use the setup script
./scripts/setup.sh
```

#### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env  # or your preferred editor
```

**Required environment variables:**
```bash
# Core settings
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-very-long-secret-key-for-jwt-tokens
API_HOST=0.0.0.0
API_PORT=8080

# Database URLs
DATABASE_URL=postgresql+asyncpg://voluntier_user:voluntier_password@localhost:5432/voluntier
REDIS_URL=redis://:redis_password@localhost:6379/0
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password

# Temporal workflow engine
TEMPORAL_HOST=localhost:7233
TEMPORAL_TASK_QUEUE=voluntier-task-queue

# AI/LLM configuration
LLM_VLLM_BASE_URL=http://localhost:8000
LLM_DEFAULT_MODEL=microsoft/DialoGPT-medium
LLM_OPENAI_API_KEY=your-openai-key-if-using-openai

# Security
SECURITY_THREAT_DETECTION_ENABLED=true
SECURITY_HONEYPOT_ENABLED=true

# File upload
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_UPLOAD_TYPES=pdf,doc,docx,png,jpg,jpeg

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=8081
```

#### Start Infrastructure Services
```bash
# Start all required services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs if there are issues
docker-compose logs
```

**Expected services:**
- PostgreSQL (port 5432)
- Redis (port 6379)
- Neo4j (port 7474, 7687)
- Temporal Server (port 7233, 8080)
- Prometheus (port 9090)
- Grafana (port 3000)

#### Initialize Database
```bash
# Run database migrations
uv run alembic upgrade head

# Create initial data (optional)
uv run python scripts/create_sample_data.py

# Verify database setup
uv run python -c "from voluntier.models import User; print('Database OK')"
```

#### Start Backend Services
```bash
# Terminal 1: Start API server
uv run uvicorn voluntier.api.main:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2: Start Temporal worker
uv run voluntier worker

# Terminal 3: Start agent orchestrator (optional for development)
uv run voluntier agent
```

**Verify backend setup:**
- API docs: http://localhost:8080/docs
- Health check: http://localhost:8080/health
- Temporal UI: http://localhost:8080 (Temporal Web UI)

### 4. Integration Testing

#### Run Tests
```bash
# Frontend tests
npm test

# Backend tests
cd backend
uv run pytest

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/workflows/

# Run with coverage
uv run pytest --cov=voluntier --cov-report=html
```

#### Manual Testing
```bash
# Test API endpoints
curl http://localhost:8080/health

# Test user registration
curl -X POST http://localhost:8080/api/v1/users/register/individual \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123","first_name":"Test","last_name":"User"}'

# Test frontend authentication
# Navigate to http://localhost:5173 and try to sign up
```

## Platform-Specific Setup

### Ubuntu/Debian Linux

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install build dependencies
sudo apt install -y build-essential curl git

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python 3.12
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Logout and login to apply group changes
```

### macOS

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install node python@3.12 git docker
brew install --cask docker

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Start Docker Desktop
open /Applications/Docker.app
```

### Windows (WSL2 recommended)

```powershell
# Install WSL2
wsl --install -d Ubuntu-22.04

# After WSL2 setup, open Ubuntu terminal and follow Ubuntu instructions above

# Alternative: Native Windows setup
# Install Node.js from https://nodejs.org/
# Install Python from https://python.org/
# Install Docker Desktop from https://docker.com/products/docker-desktop/
# Install Git from https://git-scm.com/
```

## Development Workflow

### Daily Development

```bash
# Start all services (one command)
./scripts/dev-start.sh

# Or manually:
# Terminal 1: Frontend
npm run dev

# Terminal 2: Backend API
cd backend && uv run uvicorn voluntier.api.main:app --reload

# Terminal 3: Temporal worker
cd backend && uv run voluntier worker

# Terminal 4: Infrastructure (if not running)
cd backend && docker-compose up -d
```

### Code Quality Checks

```bash
# Frontend
npm run lint          # ESLint
npm run type-check    # TypeScript
npm run format        # Prettier
npm test              # Jest tests

# Backend
cd backend
uv run black src/            # Code formatting
uv run isort src/            # Import sorting
uv run mypy src/             # Type checking
uv run flake8 src/           # Linting
uv run pytest               # Tests
```

### Git Workflow

```bash
# Create feature branch
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add your feature description"

# Push and create PR
git push origin feature/your-feature-name
# Create PR on GitHub
```

## Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using a port
lsof -i :5173  # Frontend port
lsof -i :8080  # Backend port
lsof -i :5432  # PostgreSQL port

# Kill process if needed
kill -9 <PID>

# Use different ports if needed
npm run dev -- --port 3000
uv run uvicorn voluntier.api.main:app --port 8081
```

#### Docker Issues
```bash
# Reset Docker if services won't start
docker-compose down
docker system prune -f
docker-compose up -d

# Check Docker logs
docker-compose logs postgresql
docker-compose logs redis
docker-compose logs neo4j
```

#### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -p 5432 -U voluntier_user -d voluntier

# Test Redis connection
redis-cli -h localhost -p 6379 -a redis_password ping

# Test Neo4j connection
echo "RETURN 'Hello World'" | cypher-shell -u neo4j -p neo4j_password
```

#### Python Environment Issues
```bash
# Recreate virtual environment
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -e .

# Check Python path
which python
python -c "import voluntier; print('OK')"
```

#### Node.js Issues
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

### Performance Issues

#### Frontend
```bash
# Clear browser cache and storage
# Open DevTools > Application > Storage > Clear storage

# Check for TypeScript issues
npm run type-check

# Profile bundle size
npm run build
npm run preview
```

#### Backend
```bash
# Check database performance
docker-compose exec postgresql psql -U voluntier_user -d voluntier -c "SELECT * FROM pg_stat_activity;"

# Monitor Redis memory
docker-compose exec redis redis-cli info memory

# Check Temporal workflows
# Visit http://localhost:8080 for Temporal Web UI
```

### Getting Help

#### Log Files
```bash
# Frontend logs
# Check browser console and network tab

# Backend logs
cd backend
tail -f logs/voluntier.log

# Docker logs
docker-compose logs -f
```

#### Debug Mode
```bash
# Frontend debug mode
npm run dev -- --debug

# Backend debug mode
cd backend
DEBUG=true uv run uvicorn voluntier.api.main:app --reload --log-level debug

# Python debugger
import pdb; pdb.set_trace()  # Add to code for breakpoints
```

#### Community Support
- GitHub Issues: Report bugs and ask questions
- Discussions: General questions and feature requests
- Discord: Real-time community chat (link in README)

## Production Considerations

### Environment Differences

Development vs Production settings:
```bash
# Development
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=["http://localhost:5173"]

# Production
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=["https://your-domain.com"]
SECRET_KEY=very-long-random-secret
```

### Security Setup
```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Set up SSL certificates
# Configure reverse proxy (nginx)
# Set up firewall rules
# Configure monitoring and logging
```

### Deployment Preparation
```bash
# Build frontend for production
npm run build

# Test production build locally
npm run preview

# Build backend Docker image
cd backend
docker build -f Dockerfile -t voluntier-api .

# Test production configuration
ENVIRONMENT=production uv run uvicorn voluntier.api.main:app
```

## IDE Configuration

### VS Code

Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./backend/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "typescript.preferences.importModuleSpecifier": "relative",
  "eslint.workingDirectories": ["src"],
  "tailwindCSS.includeLanguages": {
    "typescript": "javascript",
    "typescriptreact": "javascript"
  }
}
```

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/backend/.venv/bin/uvicorn",
      "args": ["voluntier.api.main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend",
      "envFile": "${workspaceFolder}/backend/.env"
    }
  ]
}
```

### PyCharm

1. Open backend directory as project
2. Configure Python interpreter: Settings > Project > Python Interpreter
3. Select existing virtual environment: `backend/.venv/bin/python`
4. Configure run configuration for FastAPI
5. Enable Django support if using Django features

This completes the comprehensive development environment setup guide. Follow these instructions step by step, and you'll have a fully functional development environment for the Voluntier platform.