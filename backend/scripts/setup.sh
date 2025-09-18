#!/bin/bash

# Voluntier Backend Development Setup Script

set -e

echo "🚀 Setting up Voluntier Backend Development Environment"
echo "======================================================"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your actual configuration values!"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
uv sync

# Start infrastructure services
echo "🐳 Starting infrastructure services..."
docker-compose up -d postgres redis neo4j temporal temporal-web vllm prometheus grafana

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check PostgreSQL
echo -n "PostgreSQL: "
if docker-compose exec -T postgres pg_isready -U voluntier_user -d voluntier >/dev/null 2>&1; then
    echo "✅ Ready"
else
    echo "❌ Not ready"
fi

# Check Redis
echo -n "Redis: "
if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
    echo "✅ Ready"
else
    echo "❌ Not ready"
fi

# Check Neo4j
echo -n "Neo4j: "
if docker-compose exec -T neo4j cypher-shell -u neo4j -p neo4j_password "RETURN 1" >/dev/null 2>&1; then
    echo "✅ Ready"
else
    echo "❌ Not ready"
fi

# Check Temporal
echo -n "Temporal: "
if curl -s http://localhost:7233 >/dev/null 2>&1; then
    echo "✅ Ready"
else
    echo "❌ Not ready"
fi

# Run database migrations
echo "🗄️  Running database migrations..."
# uv run alembic upgrade head

# Seed database with sample data (optional)
echo "🌱 Seeding database with sample data..."
# uv run python scripts/seed_data.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "🔗 Service URLs:"
echo "   API Documentation: http://localhost:8080/docs"
echo "   Temporal Web UI: http://localhost:8080"
echo "   Neo4j Browser: http://localhost:7474"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "🚀 To start the services:"
echo "   API Server: uv run uvicorn voluntier.api.main:app --host 0.0.0.0 --port 8080 --reload"
echo "   Temporal Worker: uv run voluntier worker"
echo ""
echo "📚 For more commands:"
echo "   uv run voluntier --help"
echo ""