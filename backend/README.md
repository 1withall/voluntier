# Voluntier Backend

A production-ready, autonomous agent-driven volunteer coordination platform built with FastAPI, Temporal, and modern AI/ML technologies.

## Overview

Voluntier is a comprehensive platform that integrates community members, organizations, and local businesses into a cohesive network to enhance community resilience and social capital. The platform leverages advanced autonomous agents for workflow orchestration, sophisticated AI for decision-making, and robust security mechanisms.

## Architecture

### Core Technologies

- **Backend Framework**: FastAPI with Python 3.12+
- **Workflow Orchestration**: Temporal (containerized local server)
- **Databases**: 
  - PostgreSQL (primary data storage)
  - Redis (caching and session management)
  - Neo4j (knowledge graph and relationships)
- **AI/ML**: vLLM for autonomous decision-making
- **Containerization**: Docker Compose for full-stack deployment
- **Observability**: Prometheus + Grafana for metrics and monitoring

### Key Features

- **Autonomous Agent Control**: All core functionalities operate autonomously with human-in-the-loop for critical decisions
- **Deterministic Architecture**: LLM calls only for complex reasoning; deterministic logic for reliable operations
- **Security-First Design**: AI/ML-enhanced security with adaptive threat detection
- **Comprehensive Accessibility**: Full compliance with international accessibility standards
- **Temporal Workflows**: Reliable, scalable workflow execution for all business processes

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+
- uv package manager

### Setup

1. **Clone and navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Run the setup script**:
   ```bash
   ./scripts/setup.sh
   ```

3. **Start the services**:
   ```bash
   # Start infrastructure
   docker-compose up -d
   
   # Start API server
   uv run uvicorn voluntier.api.main:app --host 0.0.0.0 --port 8080 --reload
   
   # Start Temporal worker (in another terminal)
   uv run voluntier worker
   ```

### Service URLs

- **API Documentation**: http://localhost:8080/docs
- **Temporal Web UI**: http://localhost:8080
- **Neo4j Browser**: http://localhost:7474
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## Development

### Project Structure

```
backend/
├── src/voluntier/           # Main application package
│   ├── api/                # FastAPI routes and endpoints
│   ├── models/             # Database models
│   ├── services/           # Business logic services
│   ├── temporal_workflows/ # Temporal workflows and activities
│   ├── temporal_worker/    # Worker process
│   ├── utils/              # Utility functions
│   └── config.py           # Configuration management
├── config/                 # Configuration files
├── scripts/                # Setup and utility scripts
├── tests/                  # Test suite
├── docker-compose.yml      # Docker services
├── Dockerfile              # API container
├── Dockerfile.worker       # Worker container
└── pyproject.toml          # Python project configuration
```

### Key Components

#### Temporal Workflows

The platform uses Temporal workflows for reliable execution of business processes:

- **VolunteerManagementWorkflow**: User registration, verification, and profile management
- **EventManagementWorkflow**: Event creation, publishing, and volunteer matching
- **NotificationWorkflow**: Multi-channel notification delivery
- **SecurityMonitoringWorkflow**: Threat detection and automated response
- **AgentOrchestrationWorkflow**: Autonomous decision-making and action execution
- **DataSyncWorkflow**: Data synchronization and backup operations

#### Autonomous Agent System

The agent system provides autonomous operation capabilities:

- **Context Analysis**: LLM-powered analysis of situations and recommendations
- **Human-in-the-Loop**: Required approvals for security-sensitive operations
- **Learning System**: Continuous improvement from execution outcomes
- **Memory System**: Neo4j + FAISS hybrid memory for contextual decision-making

#### Security Features

- **Adaptive Threat Detection**: Real-time security monitoring
- **Automated Response**: Immediate mitigation for high-severity threats
- **Audit Logging**: Comprehensive activity tracking
- **Access Control**: Granular permissions and verification levels

### Development Commands

```bash
# Run tests
uv run pytest

# Type checking
uv run mypy src/

# Code formatting
uv run black src/
uv run isort src/

# Linting
uv run flake8 src/

# Database migrations
uv run alembic upgrade head

# CLI help
uv run voluntier --help
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Core settings
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key

# Database URLs
DATABASE_URL=postgresql+asyncpg://voluntier_user:voluntier_password@localhost:5432/voluntier
REDIS_URL=redis://:redis_password@localhost:6379/0
NEO4J_URI=bolt://localhost:7687

# Temporal
TEMPORAL_HOST=localhost:7233
TEMPORAL_TASK_QUEUE=voluntier-task-queue

# AI/LLM
LLM_VLLM_BASE_URL=http://localhost:8000
LLM_DEFAULT_MODEL=microsoft/DialoGPT-medium
```

## Deployment

### Production Deployment

1. **Configure environment variables** for production
2. **Update docker-compose.yml** with production settings
3. **Deploy with Docker Compose**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Scaling

- **Horizontal scaling**: Multiple worker instances
- **Database scaling**: Read replicas and connection pooling
- **Caching**: Redis cluster for distributed caching
- **Load balancing**: Nginx or cloud load balancer

## Monitoring and Observability

### Metrics

- **Application metrics**: Custom Prometheus metrics
- **System metrics**: Container and infrastructure monitoring
- **Business metrics**: Volunteer engagement and event success rates

### Logging

- **Structured logging**: JSON format with correlation IDs
- **Centralized logs**: Aggregation and search capabilities
- **Alert integration**: Critical error notifications

### Tracing

- **Distributed tracing**: OpenTelemetry integration
- **Workflow tracing**: Temporal execution visibility
- **Performance monitoring**: Request timing and bottleneck identification

## Security

### Security Measures

- **Authentication**: JWT with refresh tokens
- **Authorization**: Role-based access control
- **Data encryption**: At rest and in transit
- **Input validation**: Comprehensive request validation
- **Rate limiting**: API endpoint protection
- **Security headers**: CORS, CSP, and security middleware

### Compliance

- **Data privacy**: GDPR and privacy compliance
- **Audit trails**: Complete activity logging
- **Access controls**: Principle of least privilege
- **Incident response**: Automated threat response procedures

## Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines

- **Follow PEP 8** for Python code style
- **Write comprehensive tests** for new features
- **Update documentation** for API changes
- **Use type hints** for all function signatures
- **Follow security best practices**

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=voluntier

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/workflows/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: Available in `/docs` directory
- **Issues**: Report bugs and feature requests on GitHub
- **Community**: Join our Discord for discussions and support

---

Built with ❤️ for community empowerment and volunteer coordination.