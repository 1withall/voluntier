# Multi-stage Dockerfile for Voluntier FastAPI application
# Uses UV for dependency management and Python 3.13

# Build stage: Install dependencies
FROM python:3.13-slim AS builder

# Install UV package manager
COPY --from=ghcr.io/astral-sh/uv:0.6.2 /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Set environment variables for UV
ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (without dev dependencies)
RUN uv sync --frozen --no-dev --no-install-project

# Production stage: Run application
FROM python:3.13-slim AS production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r voluntier && useradd -r -g voluntier voluntier

# Set working directory
WORKDIR /app

# Copy UV from builder
COPY --from=ghcr.io/astral-sh/uv:0.6.2 /uv /usr/local/bin/uv

# Copy installed dependencies from builder
COPY --from=builder --chown=voluntier:voluntier /app/.venv /app/.venv

# Copy application code
COPY --chown=voluntier:voluntier . .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Switch to non-root user
USER voluntier

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Development stage: Include dev dependencies
FROM production AS development

# Install system dependencies for development
USER root
RUN apt-get update && apt-get install -y \
    git \
    make \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Copy dev dependencies lock file
COPY --chown=voluntier:voluntier pyproject.toml uv.lock ./

# Install dev dependencies
RUN uv sync --frozen --no-install-project

# Switch back to non-root user
USER voluntier

# Run with auto-reload for development
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
