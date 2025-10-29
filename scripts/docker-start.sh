#!/bin/bash
# Quick start script for Voluntier Docker deployment
# This script sets up and starts all required services

set -e

echo "==================================="
echo "Voluntier Docker Quick Start"
echo "==================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found. Please install Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

if ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose v2 not found. Please install Docker Compose v2.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose v2 found${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.docker .env
    
    # Generate secrets
    echo -e "${YELLOW}Generating secure passwords...${NC}"
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    REDIS_PASSWORD=$(openssl rand -base64 32)
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
    
    # Update .env
    sed -i.bak "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env
    sed -i.bak "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" .env
    sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    rm .env.bak
    
    echo -e "${GREEN}✓ .env file created with secure passwords${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Make init-db.sh executable
chmod +x scripts/init-db.sh

echo ""
echo "Starting services..."
echo "This may take a few minutes on first run (downloading images)"
echo ""

# Start services
docker compose up -d

echo ""
echo "Waiting for services to become healthy..."
echo ""

# Wait for services
MAX_WAIT=120
ELAPSED=0
ALL_HEALTHY=false

while [ $ELAPSED -lt $MAX_WAIT ]; do
    POSTGRES_HEALTH=$(docker compose ps postgres --format json 2>/dev/null | grep -o '"Health":"[^"]*"' | cut -d'"' -f4 || echo "starting")
    REDIS_HEALTH=$(docker compose ps redis --format json 2>/dev/null | grep -o '"Health":"[^"]*"' | cut -d'"' -f4 || echo "starting")
    TEMPORAL_HEALTH=$(docker compose ps temporal --format json 2>/dev/null | grep -o '"Health":"[^"]*"' | cut -d'"' -f4 || echo "starting")
    API_HEALTH=$(docker compose ps api --format json 2>/dev/null | grep -o '"Health":"[^"]*"' | cut -d'"' -f4 || echo "starting")
    
    echo -ne "\r  PostgreSQL: $POSTGRES_HEALTH  |  Redis: $REDIS_HEALTH  |  Temporal: $TEMPORAL_HEALTH  |  API: $API_HEALTH  "
    
    if [ "$POSTGRES_HEALTH" = "healthy" ] && [ "$REDIS_HEALTH" = "healthy" ] && [ "$TEMPORAL_HEALTH" = "healthy" ] && [ "$API_HEALTH" = "healthy" ]; then
        ALL_HEALTHY=true
        break
    fi
    
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

echo ""
echo ""

if [ "$ALL_HEALTHY" = true ]; then
    echo -e "${GREEN}✓ All services are healthy!${NC}"
else
    echo -e "${YELLOW}⚠ Services are still starting. Check logs with: docker compose logs -f${NC}"
fi

# Show status
echo ""
echo "Service Status:"
docker compose ps

echo ""
echo "==================================="
echo -e "${GREEN}Voluntier is ready!${NC}"
echo "==================================="
echo ""
echo "Access points:"
echo "  API:         http://localhost:8000"
echo "  API Docs:    http://localhost:8000/docs"
echo "  Temporal UI: http://localhost:8233"
echo "  Health:      http://localhost:8000/health"
echo ""
echo "Useful commands:"
echo "  View logs:       docker compose logs -f"
echo "  Stop services:   docker compose down"
echo "  Restart:         docker compose restart"
echo "  Shell access:    docker compose exec api bash"
echo ""
echo "Next steps:"
echo "  1. Create a test user: curl -X POST http://localhost:8000/api/v1/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"test@example.com\",\"password\":\"Test123!\",\"full_name\":\"Test User\"}'"
echo "  2. Read DOCKER.md for detailed documentation"
echo "  3. Read VERIFICATION.md for verification workflow guide"
echo ""
