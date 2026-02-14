# Unofficial FortiMonitor MCP Server - Docker Image
# Multi-stage build for smaller final image

# =============================================================================
# Stage 1: Builder - Install dependencies
# =============================================================================
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Create a separate requirements file for production only
RUN grep -v "^pytest\|^black\|^flake8\|^mypy\|^types-" requirements.txt > requirements-prod.txt || cp requirements.txt requirements-prod.txt

# Upgrade pip and wheel to fix security vulnerabilities (CVE-2025-8869, CVE-2026-24049)
RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# Install Python dependencies to user directory
RUN pip install --no-cache-dir --user -r requirements-prod.txt

# =============================================================================
# Stage 2: Runtime - Final production image
# =============================================================================
FROM python:3.11-slim

# Labels
LABEL org.opencontainers.image.title="Unofficial FortiMonitor MCP Server"
LABEL org.opencontainers.image.description="Model Context Protocol server for FortiMonitor/Panopta integration"
LABEL org.opencontainers.image.version="1.0.20260205"
LABEL org.opencontainers.image.authors="gjenkins20@gmail.com"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, wheel, and setuptools to fix security vulnerabilities
# CVE-2025-8869 (pip), CVE-2026-24049 (wheel), CVE-2026-23949 (jaraco.context in setuptools)
RUN pip install --no-cache-dir --upgrade pip wheel setuptools --root-user-action=ignore

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash mcpuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/mcpuser/.local

# Copy application code
COPY --chown=mcpuser:mcpuser src/ ./src/
COPY --chown=mcpuser:mcpuser pyproject.toml ./
COPY --chown=mcpuser:mcpuser setup.py ./

# Create cache directory with proper permissions
RUN mkdir -p /app/cache/schemas && chown -R mcpuser:mcpuser /app/cache

# Switch to non-root user
USER mcpuser

# Add local packages to PATH
ENV PATH=/home/mcpuser/.local/bin:$PATH

# Set Python path
ENV PYTHONPATH=/app

# Set default environment variables
ENV FORTIMONITOR_BASE_URL=https://api2.panopta.com/v2
ENV MCP_SERVER_NAME=unofficial-fortimonitor-mcp
ENV MCP_SERVER_VERSION=1.0.20260205
ENV LOG_LEVEL=INFO
ENV ENABLE_SCHEMA_CACHE=true
ENV SCHEMA_CACHE_DIR=/app/cache/schemas
ENV SCHEMA_CACHE_TTL=86400
ENV RATE_LIMIT_REQUESTS=100
ENV RATE_LIMIT_PERIOD=60

# Health check - verify configuration can be loaded
# Note: This requires FORTIMONITOR_API_KEY to be set
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "from src.config import get_settings; s = get_settings(); print('OK')" || exit 1

# Run the MCP server
# Uses stdio for MCP protocol communication
# CMD ["python", "-m", "src.server"]

# The Dockerfile must have this at the end -- gjenkins@20260502
# Keep container alive - MCP server invoked via 'docker exec' on-demand
CMD ["tail", "-f", "/dev/null"]