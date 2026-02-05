# Docker Deployment Guide

This guide explains how to deploy the FortiMonitor MCP Server using Docker.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed
- FortiMonitor API key (from your FortiMonitor/Panopta account)

## Quick Start

### Option 1: Docker Run (Simplest)

```bash
docker run -d \
  --name fortimonitor-mcp \
  -e FORTIMONITOR_API_KEY=your-api-key-here \
  fortimonitor-mcp:latest
```

### Option 2: Docker Compose (Recommended)

1. **Clone the repository** (or download docker-compose.yml):
   ```bash
   git clone https://github.com/your-org/fortimonitor-mcp.git
   cd fortimonitor-mcp
   ```

2. **Create your environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` and set your API key**:
   ```bash
   FORTIMONITOR_API_KEY=your-actual-api-key
   ```

4. **Start the container**:
   ```bash
   docker-compose up -d
   ```

5. **Check status**:
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

## Building from Source

If you want to build the Docker image locally:

### Linux/macOS

```bash
# Build
./scripts/build.sh

# Test
./scripts/test-container.sh

# Run
docker run -e FORTIMONITOR_API_KEY=your-key fortimonitor-mcp:latest
```

### Windows

```cmd
REM Build
scripts\build.bat

REM Test
scripts\test-container.bat

REM Run
docker run -e FORTIMONITOR_API_KEY=your-key fortimonitor-mcp:latest
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FORTIMONITOR_API_KEY` | **Yes** | - | Your FortiMonitor API key |
| `FORTIMONITOR_BASE_URL` | No | `https://api2.panopta.com/v2` | API endpoint URL |
| `MCP_SERVER_NAME` | No | `fortimonitor-mcp` | Server identifier |
| `MCP_SERVER_VERSION` | No | `1.0.0` | Server version |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ENABLE_SCHEMA_CACHE` | No | `true` | Enable API schema caching |
| `SCHEMA_CACHE_TTL` | No | `86400` | Cache TTL in seconds (24 hours) |
| `RATE_LIMIT_REQUESTS` | No | `100` | Max requests per period |
| `RATE_LIMIT_PERIOD` | No | `60` | Rate limit period in seconds |

### Using Environment Variables Directly

```bash
docker run -d \
  --name fortimonitor-mcp \
  -e FORTIMONITOR_API_KEY=your-key \
  -e LOG_LEVEL=DEBUG \
  -e RATE_LIMIT_REQUESTS=200 \
  fortimonitor-mcp:latest
```

### Using an Environment File

Create a file named `my-config.env`:

```env
FORTIMONITOR_API_KEY=your-api-key
LOG_LEVEL=INFO
ENABLE_SCHEMA_CACHE=true
```

Run with the env file:

```bash
docker run -d \
  --name fortimonitor-mcp \
  --env-file my-config.env \
  fortimonitor-mcp:latest
```

## Integration with Claude Desktop

### Step 1: Ensure the Container is Running

```bash
# Using Docker Compose
docker-compose up -d

# Or using Docker directly
docker run -d --name fortimonitor-mcp -e FORTIMONITOR_API_KEY=your-key fortimonitor-mcp:latest
```

### Step 2: Configure Claude Desktop

Edit your Claude Desktop configuration file:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

Add the FortiMonitor MCP server:

```json
{
  "mcpServers": {
    "fortimonitor": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "fortimonitor-mcp",
        "python",
        "-m",
        "src.server"
      ]
    }
  }
}
```

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop to load the new configuration.

### Step 4: Verify Connection

In Claude Desktop, you should now see FortiMonitor tools available. Try asking:

> "Show me all servers monitored by FortiMonitor"

## Container Management

### View Logs

```bash
# Docker Compose
docker-compose logs -f

# Docker directly
docker logs -f fortimonitor-mcp
```

### Stop the Container

```bash
# Docker Compose
docker-compose down

# Docker directly
docker stop fortimonitor-mcp
```

### Restart the Container

```bash
# Docker Compose
docker-compose restart

# Docker directly
docker restart fortimonitor-mcp
```

### Update to Latest Version

```bash
# Pull latest image (if using a registry)
docker pull your-registry/fortimonitor-mcp:latest

# Restart with Docker Compose
docker-compose pull
docker-compose up -d

# Or rebuild from source
./scripts/build.sh
docker-compose up -d
```

### Remove Container and Data

```bash
# Docker Compose (keeps volumes)
docker-compose down

# Docker Compose (removes volumes too)
docker-compose down -v

# Docker directly
docker stop fortimonitor-mcp
docker rm fortimonitor-mcp
```

## Resource Limits

The default docker-compose.yml includes resource limits:

- **CPU**: 1.0 cores (limit), 0.25 cores (reservation)
- **Memory**: 512MB (limit), 128MB (reservation)

Adjust these in `docker-compose.yml` if needed:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 256M
```

## Health Checks

The container includes a health check that verifies configuration loading. View health status:

```bash
docker inspect --format='{{.State.Health.Status}}' fortimonitor-mcp
```

Possible statuses:
- `starting` - Container is starting up
- `healthy` - Configuration loaded successfully
- `unhealthy` - Configuration failed (check API key)

## Troubleshooting

### Container Won't Start

1. **Check logs**:
   ```bash
   docker logs fortimonitor-mcp
   ```

2. **Verify API key is set**:
   ```bash
   docker exec fortimonitor-mcp printenv FORTIMONITOR_API_KEY
   ```

3. **Test configuration loading**:
   ```bash
   docker exec fortimonitor-mcp python -c "from src.config import get_settings; print('OK')"
   ```

### API Connection Issues

1. **Test network connectivity**:
   ```bash
   docker exec fortimonitor-mcp python -c "import requests; r = requests.get('https://api2.panopta.com/v2'); print(r.status_code)"
   ```

2. **Verify API key works**:
   ```bash
   docker exec fortimonitor-mcp python -c "
   from src.fortimonitor.client import FortiMonitorClient
   c = FortiMonitorClient()
   r = c.get_servers(limit=1)
   print(f'Success: {len(r.server_list)} servers')
   "
   ```

### Claude Desktop Not Connecting

1. **Verify container is running**:
   ```bash
   docker ps | grep fortimonitor-mcp
   ```

2. **Test the exec command manually**:
   ```bash
   echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | \
     docker exec -i fortimonitor-mcp python -m src.server
   ```

3. **Check Claude Desktop logs** for connection errors

### Performance Issues

1. **Check container resource usage**:
   ```bash
   docker stats fortimonitor-mcp
   ```

2. **Increase resource limits** in docker-compose.yml if needed

3. **Enable caching** (it's on by default):
   ```bash
   -e ENABLE_SCHEMA_CACHE=true
   ```

## Security Considerations

### API Key Protection

- Never commit your `.env` file to version control
- Use Docker secrets for production environments
- Consider using a secrets manager for enterprise deployments

### Using Docker Secrets (Swarm Mode)

```bash
# Create the secret
echo "your-api-key" | docker secret create fortimonitor_api_key -

# Reference in docker-compose.yml
services:
  fortimonitor-mcp:
    secrets:
      - fortimonitor_api_key
    environment:
      - FORTIMONITOR_API_KEY_FILE=/run/secrets/fortimonitor_api_key

secrets:
  fortimonitor_api_key:
    external: true
```

### Container Security

The container runs as a non-root user (`mcpuser`, UID 1000) for security. The Dockerfile includes:

- Multi-stage build (smaller attack surface)
- Non-root user
- No unnecessary packages
- Health checks enabled

## Publishing to a Registry

### Docker Hub

```bash
# Login
docker login

# Build and push
REGISTRY=your-dockerhub-username ./scripts/push.sh
```

### GitHub Container Registry

```bash
# Login
echo $GITHUB_TOKEN | docker login ghcr.io -u your-username --password-stdin

# Build and push
REGISTRY=ghcr.io/your-org ./scripts/push.sh
```

### Private Registry

```bash
# Login
docker login your-registry.com

# Build and push
REGISTRY=your-registry.com/your-org ./scripts/push.sh
```

## Available Tools

Once connected, the following FortiMonitor tools are available in Claude:

### Server Management
- `get_servers` - List monitored servers
- `get_server_details` - Get detailed server information
- `set_server_status` - Enable/disable server monitoring
- `search_servers_advanced` - Advanced server search

### Outage Management
- `get_outages` - List current/historical outages
- `get_outage_details` - Get outage details
- `acknowledge_outage` - Acknowledge an outage
- `add_outage_note` - Add notes to outages
- `bulk_acknowledge_outages` - Bulk acknowledge

### Metrics & Health
- `get_server_metrics` - Get performance metrics
- `check_server_health` - Quick health check
- `get_system_health_summary` - Overall health summary

### Server Groups
- `list_server_groups` - List groups
- `create_server_group` - Create groups
- `add_servers_to_group` - Add servers to groups

### Maintenance
- `create_maintenance_window` - Schedule maintenance
- `list_maintenance_windows` - List windows

### Reporting
- `get_outage_statistics` - Outage stats
- `get_server_statistics` - Server stats
- `generate_availability_report` - Availability reports

...and more! Ask Claude "What FortiMonitor tools are available?" for the full list.
