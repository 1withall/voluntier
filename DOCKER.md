# Docker Deployment Guide

This guide covers deploying Voluntier using Docker Compose with all required services.

## Prerequisites

- Docker Engine 20.10+ (with Compose v2)
- Docker Compose v2.0+
- 4GB+ RAM available
- 10GB+ disk space

Verify installation:
```bash
docker --version  # Should show 20.10+
docker compose version  # Should show v2.x
```

## Services Overview

The `docker-compose.yaml` includes:

| Service | Image | Purpose | Port |
|---------|-------|---------|------|
| **postgres** | postgis/postgis:17-3.5 | PostgreSQL 17 with PostGIS | 5432 |
| **redis** | redis:7.4-alpine | Caching and sessions | 6379 |
| **temporal** | temporalio/auto-setup:1.27.0 | Workflow orchestration | 7233, 8233 |
| **api** | Custom (FastAPI) | Backend API | 8000 |
| **worker** | Custom (Temporal worker) | Verification workflows | - |
| **migrations** | Custom (Alembic) | Database migrations | - |
| **nginx** | nginx:1.27-alpine | Reverse proxy (optional) | 80, 443 |

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.docker .env

# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))" > secret.txt

# Edit .env with your values
vim .env
```

**Required changes in `.env`:**
```bash
POSTGRES_PASSWORD=your_secure_password_here
REDIS_PASSWORD=another_secure_password_here
SECRET_KEY=paste_generated_secret_key_here
```

### 2. Start All Services

```bash
# Development mode (with auto-reload)
docker compose up -d

# Production mode (with nginx)
docker compose --profile production up -d

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f api
```

### 3. Verify Services

```bash
# Check service health
docker compose ps

# All services should show "healthy" or "running"
# Example output:
# NAME                   STATUS         PORTS
# voluntier-postgres     Up (healthy)   5432/tcp
# voluntier-redis        Up (healthy)   6379/tcp
# voluntier-temporal     Up (healthy)   7233/tcp, 8233/tcp
# voluntier-api          Up (healthy)   8000/tcp
# voluntier-worker       Up             -
```

### 4. Access Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Temporal UI**: http://localhost:8233
- **Health Check**: http://localhost:8000/health

## Development Workflow

### Building Images

```bash
# Build all services
docker compose build

# Build specific service
docker compose build api

# Build without cache
docker compose build --no-cache
```

### Running Commands

```bash
# Run Alembic migrations manually
docker compose run --rm migrations

# Access API shell
docker compose exec api bash

# Run tests
docker compose exec api uv run pytest

# Format code
docker compose exec api uv run black app/

# Check types
docker compose exec api uv run mypy app/
```

### Database Management

```bash
# Access PostgreSQL shell
docker compose exec postgres psql -U voluntier_user -d voluntier

# Run SQL file
docker compose exec -T postgres psql -U voluntier_user -d voluntier < backup.sql

# Create database backup
docker compose exec postgres pg_dump -U voluntier_user voluntier > backup_$(date +%Y%m%d).sql

# Restore database
docker compose exec -T postgres psql -U voluntier_user -d voluntier < backup_20251029.sql
```

### Redis Commands

```bash
# Access Redis CLI
docker compose exec redis redis-cli -a your_redis_password

# Common Redis commands:
# KEYS *              # List all keys
# GET key             # Get value
# FLUSHALL            # Clear all data (caution!)
# INFO                # Server info
```

### Temporal Operations

```bash
# Access Temporal CLI
docker compose exec temporal tctl namespace list

# View workflows
docker compose exec temporal tctl workflow list

# Describe specific workflow
docker compose exec temporal tctl workflow describe --workflow-id verification-1

# Query workflow
docker compose exec temporal tctl workflow query \
  --workflow-id verification-1 \
  --type current_score
```

## Production Deployment

### 1. Prepare Environment

```bash
# Generate strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Update .env
cat > .env << EOF
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
SECRET_KEY=$SECRET_KEY
DEBUG=False
ENVIRONMENT=production
EOF

# Secure the file
chmod 600 .env
```

### 2. SSL/TLS Certificates

```bash
# Create SSL directory
mkdir -p nginx/ssl

# Option A: Let's Encrypt (recommended)
# Install certbot first: apt-get install certbot
certbot certonly --standalone -d your-domain.com

# Copy certificates
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/

# Option B: Self-signed (development only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/CN=localhost"
```

### 3. Update Nginx Configuration

Edit `nginx/nginx.conf` and uncomment the HTTPS server block. Update:
```nginx
server_name your-domain.com;
```

### 4. Deploy

```bash
# Pull latest images
docker compose pull

# Start with production profile
docker compose --profile production up -d

# Verify deployment
docker compose ps
curl https://your-domain.com/health
```

### 5. Enable Automatic Restart

```bash
# Update restart policies in docker-compose.yaml
# Change: restart: unless-stopped
# To: restart: always

# For systemd integration (optional)
sudo tee /etc/systemd/system/voluntier.service << EOF
[Unit]
Description=Voluntier Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/voluntier
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable voluntier
sudo systemctl start voluntier
```

## Monitoring and Logs

### View Logs

```bash
# All services
docker compose logs -f

# Specific service with timestamps
docker compose logs -f --timestamps api

# Last 100 lines
docker compose logs --tail=100 api

# Since specific time
docker compose logs --since 2025-10-29T10:00:00 api
```

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Clean up unused resources
docker system prune -a --volumes
```

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check all services
for service in postgres redis temporal api; do
  echo "=== $service ==="
  docker compose exec $service echo "OK" || echo "FAILED"
done
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker compose logs service-name

# Recreate service
docker compose up -d --force-recreate service-name

# Check configuration
docker compose config
```

### Database Connection Issues

```bash
# Verify PostgreSQL is running
docker compose exec postgres pg_isready -U voluntier_user

# Check connections
docker compose exec postgres psql -U voluntier_user -d voluntier -c "SELECT count(*) FROM pg_stat_activity;"

# Reset database (CAUTION: data loss)
docker compose down -v
docker compose up -d postgres
docker compose run --rm migrations
```

### Temporal Workflow Issues

```bash
# Check Temporal server
docker compose exec temporal tctl cluster health

# Restart worker
docker compose restart worker

# View worker logs
docker compose logs -f worker
```

### Port Conflicts

```bash
# Check what's using ports
lsof -i :8000
lsof -i :5432

# Change ports in docker-compose.yaml
# Example: "8001:8000" instead of "8000:8000"
```

### Out of Memory

```bash
# Check container memory
docker stats --no-stream

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → 4GB+

# Add memory limits to docker-compose.yaml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 512M
```

## Backup and Restore

### Full Backup

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
docker compose exec -T postgres pg_dump -U voluntier_user voluntier > "$BACKUP_DIR/database.sql"

# Backup volumes
docker compose exec postgres tar czf - /var/lib/postgresql/data > "$BACKUP_DIR/postgres_data.tar.gz"
docker compose exec redis tar czf - /data > "$BACKUP_DIR/redis_data.tar.gz"
docker compose exec temporal tar czf - /etc/temporal > "$BACKUP_DIR/temporal_data.tar.gz"

# Backup .env
cp .env "$BACKUP_DIR/.env"

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x backup.sh
./backup.sh
```

### Restore

```bash
# Stop services
docker compose down

# Restore database
docker compose up -d postgres
sleep 10
cat backups/20251029_120000/database.sql | docker compose exec -T postgres psql -U voluntier_user -d voluntier

# Restore volumes (if needed)
docker compose exec -T postgres tar xzf - -C / < backups/20251029_120000/postgres_data.tar.gz

# Restart all services
docker compose up -d
```

## Scaling

### Horizontal Scaling

```bash
# Scale API instances
docker compose up -d --scale api=3

# Scale workers
docker compose up -d --scale worker=5

# Note: Update nginx upstream for multiple API instances
```

### Load Balancing

Update `nginx/nginx.conf`:
```nginx
upstream voluntier_api {
    least_conn;
    server api:8000 max_fails=3 fail_timeout=30s;
    server api_2:8000 max_fails=3 fail_timeout=30s;
    server api_3:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

## Maintenance

### Update Images

```bash
# Pull latest images
docker compose pull

# Recreate containers
docker compose up -d --force-recreate

# Remove old images
docker image prune -a
```

### Clean Up

```bash
# Stop and remove containers
docker compose down

# Remove volumes (CAUTION: data loss)
docker compose down -v

# Remove everything including images
docker compose down --rmi all -v
```

## Performance Tuning

### PostgreSQL

```yaml
# Add to postgres service in docker-compose.yaml
environment:
  POSTGRES_SHARED_BUFFERS: 256MB
  POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
  POSTGRES_WORK_MEM: 16MB
  POSTGRES_MAINTENANCE_WORK_MEM: 128MB
```

### Redis

```yaml
# Add to redis service
command: >
  redis-server
  --appendonly yes
  --requirepass ${REDIS_PASSWORD}
  --maxmemory 256mb
  --maxmemory-policy allkeys-lru
```

### FastAPI Workers

```yaml
# Add to api service
environment:
  UVICORN_WORKERS: 4
  UVICORN_WORKER_CLASS: uvicorn.workers.UvicornWorker
```

## Security Best Practices

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Use strong passwords** - Generate with `openssl rand -base64 32`
3. **Enable HTTPS** - Use Let's Encrypt certificates
4. **Limit network exposure** - Use internal networks for services
5. **Update regularly** - Keep images and dependencies current
6. **Enable firewall** - Only expose necessary ports
7. **Use secrets management** - Docker Secrets or external vault
8. **Regular backups** - Automate with cron jobs
9. **Monitor logs** - Set up log aggregation (ELK, Loki)
10. **Health checks** - Monitor service availability

## Next Steps

- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Configure log aggregation (ELK Stack)
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Implement automated backups
- [ ] Configure auto-scaling
- [ ] Set up SSL certificate auto-renewal
- [ ] Implement blue-green deployments
- [ ] Add container security scanning

## References

- Docker Compose: https://docs.docker.com/compose/
- PostGIS: https://postgis.net/documentation/
- Temporal: https://docs.temporal.io/
- FastAPI: https://fastapi.tiangolo.com/deployment/docker/
- Nginx: https://nginx.org/en/docs/
