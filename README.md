# Voluntier - Community Volunteer Coordination Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Frontend Status](https://img.shields.io/badge/Frontend-React%2BTypeScript-blue)](src/)
[![Backend Status](https://img.shields.io/badge/Backend-FastAPI%2BPython-green)](backend/)
[![Security](https://img.shields.io/badge/Security-Enterprise%20Grade-red)](SECURITY.md)

A comprehensive, autonomous agent-driven platform for coordinating volunteer activities, facilitating community engagement, and managing local resources with enterprise-grade security and reliability.

## 🌟 Overview

Voluntier integrates individual community members, non-commercial organizations, and local businesses into a cohesive network to enhance community resilience and social capital. The platform features advanced autonomous agents, sophisticated AI decision-making, and robust security mechanisms.

### Key Features

- **🤖 Autonomous Agent Control**: AI-driven workflow orchestration with human oversight
- **🔒 Enterprise Security**: ML-powered threat detection and automated response
- **⚡ Temporal Workflows**: Reliable, distributed workflow execution
- **🧠 Hybrid Memory System**: Neo4j + FAISS for intelligent context management
- **📱 Responsive Design**: Accessible, mobile-first user interface
- **🔍 Real-time Monitoring**: Comprehensive observability and telemetry
- **📊 Project Management**: Professional PDF templates and planning tools
- **🛡️ Comprehensive Security**: Multi-layer validation and threat protection
- **📋 Event Management**: Advanced organization dashboard with security validation
- **📄 Document Generation**: Industry-standard project management templates

## 🏗️ Architecture

```
voluntier/
├── src/                    # Frontend React Application
│   ├── components/         # Reusable UI components
│   ├── services/          # Frontend business logic
│   ├── types/             # TypeScript type definitions
│   └── ...                # Additional frontend modules
├── backend/               # Production Backend (FastAPI + Temporal)
│   ├── src/voluntier/     # Main application package
│   ├── config/            # Configuration files
│   ├── scripts/           # Setup and utility scripts
│   └── tests/             # Comprehensive test suite
├── docs/                  # Documentation
├── SECURITY.md           # Security documentation
├── PRD.md                # Product requirements
└── README.md             # This file
```

### Technology Stack

#### Frontend
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom design system
- **Components**: Shadcn/ui component library
- **Icons**: Phosphor Icons
- **Animations**: Framer Motion (planned)

#### Backend
- **API**: FastAPI with Python 3.12+
- **Workflows**: Temporal for reliable task orchestration
- **Databases**: PostgreSQL, Redis, Neo4j
- **AI/ML**: vLLM for autonomous decision-making
- **Security**: Custom ML-based threat detection
- **Monitoring**: Prometheus + Grafana

#### Infrastructure
- **Containerization**: Docker Compose
- **Package Management**: uv (Python), npm (Node.js)
- **CI/CD**: GitHub Actions (planned)
- **Deployment**: Local/on-premises first

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ with npm
- **Python** 3.12+
- **Docker** and Docker Compose
- **uv** package manager (`pip install uv`)

### Frontend Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:5173
```

### Backend Development

```bash
# Navigate to backend
cd backend

# Run setup script
./scripts/setup.sh

# Start infrastructure services
docker-compose up -d

# Start API server
uv run uvicorn voluntier.api.main:app --reload

# Start Temporal worker (new terminal)
uv run voluntier worker
```

### Service URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8080/docs
- **Temporal UI**: http://localhost:8080
- **Neo4j Browser**: http://localhost:7474
- **Grafana**: http://localhost:3000

## 📁 Project Structure

### Frontend (`/src`)

```
src/
├── components/
│   ├── ui/                # Shadcn/ui base components
│   ├── signup/            # User registration forms
│   ├── profiles/          # User profile management
│   ├── onboarding/        # Guided setup processes
│   ├── upload/            # Document upload components
│   ├── notifications/     # Real-time notification system
│   ├── verification/      # Identity verification components
│   └── OrganizationDashboard.tsx  # Comprehensive event management
├── services/              # Frontend business logic
│   ├── telemetry.ts       # Analytics and tracking
│   ├── documentUpload.ts  # Document processing
│   ├── notifications.ts   # Notification management
│   └── ...                # Additional services
├── types/                 # TypeScript definitions
│   ├── auth.ts           # Authentication types
│   ├── profiles.ts       # User profile types
│   ├── documents.ts      # Document types
│   └── ...               # Additional type definitions
├── utils/                 # Utility functions
│   └── pdfGenerator.ts    # Professional PDF template generation
├── data/                 # Sample data and test accounts
├── hooks/                # Custom React hooks
├── lib/                  # Utility functions
└── styles/               # CSS and theming
```

### Backend (`/backend`)

```
backend/
├── src/voluntier/
│   ├── api/              # FastAPI routes and endpoints
│   ├── models/           # Database models (SQLAlchemy)
│   ├── services/         # Business logic services
│   ├── temporal_workflows/ # Temporal workflows and activities
│   ├── security/         # Security components
│   ├── utils/            # Utility functions
│   └── config.py         # Configuration management
├── config/               # Docker and deployment configs
├── scripts/              # Setup and maintenance scripts
├── tests/                # Comprehensive test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── workflows/        # Temporal workflow tests
└── docs/                 # API and architecture documentation
```

## 🔐 Security

The platform implements enterprise-grade security with:

- **ML-based Threat Detection**: Real-time anomaly detection
- **Adaptive Response**: Automated threat mitigation
- **Zero Trust Architecture**: Verify every request
- **Comprehensive Auditing**: Full activity logging
- **Data Encryption**: At rest and in transit

See [SECURITY.md](SECURITY.md) for detailed security documentation.

## 👥 User Types

### Individual Users
- Personal volunteer profiles
- Skill tracking and verification
- Event registration and participation
- Impact measurement and gamification

### Organizations
- Event creation and management
- Volunteer coordination
- Resource sharing
- Community impact reporting

### Businesses
- Corporate volunteer programs
- Resource donation tracking
- Community partnership management
- CSR reporting and analytics

## 🔄 Workflows

The platform uses Temporal workflows for reliable execution:

- **User Management**: Registration, verification, and profile updates
- **Event Coordination**: Creation, publishing, and volunteer matching
- **Document Processing**: Upload, verification, and storage
- **Notification Delivery**: Multi-channel communication
- **Security Monitoring**: Threat detection and response
- **Agent Orchestration**: Autonomous decision-making

## 📊 Monitoring & Observability

- **Telemetry**: Comprehensive user analytics
- **Performance Metrics**: Real-time system monitoring
- **Business Intelligence**: Community impact analytics
- **Security Dashboards**: Threat landscape visibility
- **Audit Trails**: Complete activity logging

## 🧪 Testing

```bash
# Frontend tests
npm test

# Backend tests
cd backend
uv run pytest

# Run with coverage
uv run pytest --cov=voluntier

# Integration tests
uv run pytest tests/integration/
```

## 📚 Documentation

- **[Product Requirements](PRD.md)**: Detailed feature specifications
- **[Security Documentation](SECURITY.md)**: Comprehensive security guide
- **[Backend Documentation](backend/README.md)**: Backend setup and architecture
- **[API Documentation](http://localhost:8080/docs)**: Interactive API docs (when running)
- **[Document Upload Guide](DOCUMENT_UPLOAD_README.md)**: Document processing system

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Follow existing code patterns
4. **Add tests**: Ensure comprehensive test coverage
5. **Update documentation**: Keep docs current
6. **Submit a pull request**: Describe your changes clearly

### Development Guidelines

- **Code Style**: Follow existing patterns and conventions
- **TypeScript**: Use strict typing throughout
- **Security**: Follow security best practices
- **Testing**: Write tests for new functionality
- **Documentation**: Update relevant documentation

## 🏢 Organization Event Management

### Comprehensive Event Creation

Organizations have access to a sophisticated event creation system with:

#### Security-First Form Design
- **Multi-layer Validation**: XSS protection, injection prevention, input sanitization
- **Real-time Feedback**: Immediate validation and error correction
- **Secure Data Handling**: All inputs validated against security threats
- **Audit Logging**: Complete tracking of all creation attempts

#### Professional Project Management Integration
- **8 Industry-Standard Templates**: Based on PMBOK Guide and Agile best practices
  - Project Charter
  - Scope Management Plan
  - Risk Management Plan
  - Communication Management Plan
  - Stakeholder Management Plan
  - Schedule Management Plan
  - Cost Management Plan
  - Quality Management Plan
- **Event Planning Checklist**: Comprehensive timeline-based planning guide
- **PDF Generation**: Professional, editable documents for offline use
- **Pre-filled Information**: Event details automatically populated

#### Advanced Event Configuration
- **Comprehensive Details**: Multi-tab form with 40+ configurable fields
- **Accessibility Features**: Full WCAG compliance and accessibility options
- **Safety Requirements**: Background checks, training, age restrictions
- **Remote Participation**: Virtual meeting integration and hybrid events
- **Smart Validation**: Date logic, contact verification, URL validation

### Document Management

Organizations can download professionally formatted project management documents that include:

- **Fillable PDF Forms**: Industry-standard templates with event information pre-populated
- **Security Compliance**: Documents designed for organizational storage, not app database
- **Professional Formatting**: Clean, branded layouts suitable for organizational use
- **Version Control**: Timestamped documents for tracking and management

For detailed information, see [Organization Event Management Documentation](docs/organization-event-management.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Report bugs and feature requests via GitHub Issues
- **Documentation**: Comprehensive guides in the `/docs` directory
- **Security**: Report security vulnerabilities via [SECURITY.md](SECURITY.md)

## 🙏 Acknowledgments

Built with modern web technologies and best practices for community empowerment and volunteer coordination.

---

**Note**: This application is designed for production deployment outside of the GitHub Spark environment. The full backend system requires local infrastructure setup with Docker Compose.