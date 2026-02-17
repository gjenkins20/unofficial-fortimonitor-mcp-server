# FortiMonitor MCP Server

An unofficial [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that connects **Claude Desktop** and **Claude Code** to the [FortiMonitor/Panopta v2 monitoring API](https://api2.panopta.com/v2). Manage your entire monitoring infrastructure through natural language — **241 tools** covering servers, outages, metrics, maintenance windows, notifications, cloud monitoring, SNMP, reporting, and more.

## Quick Start

### 1. Start the container

```bash
docker run -d \
  --name fortimonitor-mcp \
  -e FORTIMONITOR_API_KEY=your-api-key-here \
  --restart unless-stopped \
  --security-opt no-new-privileges:true \
  gjenkins20/fortimonitor-mcp:latest
```

Or with Docker Compose:

```bash
curl -O https://raw.githubusercontent.com/gjenkins20/fortimonitor-mcp-server/main/docker-compose.share.yml
echo "FORTIMONITOR_API_KEY=your-api-key-here" > .env
docker-compose -f docker-compose.share.yml up -d
```

### 2. Connect to Claude Desktop

Add the following to your Claude Desktop config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fortimonitor": {
      "command": "docker",
      "args": ["exec", "-i", "fortimonitor-mcp", "python", "-m", "src.server"]
    }
  }
}
```

Restart Claude Desktop. You now have full FortiMonitor API access through Claude.

## How It Works

This image uses a **keep-alive container pattern**. The container runs continuously in the background and Claude invokes the MCP server on-demand via `docker exec`. Communication happens over stdio (stdin/stdout) — **no network ports are exposed**.

```
Claude Desktop  <--stdio-->  docker exec  <-->  MCP Server  <--HTTPS-->  FortiMonitor API
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `FORTIMONITOR_API_KEY` | **Yes** | — | Your FortiMonitor/Panopta API key |
| `FORTIMONITOR_BASE_URL` | No | `https://api2.panopta.com/v2` | API base URL |
| `LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `RATE_LIMIT_REQUESTS` | No | `100` | Max API requests per rate limit period |
| `RATE_LIMIT_PERIOD` | No | `60` | Rate limit window in seconds |
| `ENABLE_SCHEMA_CACHE` | No | `true` | Cache API schemas for faster startup |
| `SCHEMA_CACHE_TTL` | No | `86400` | Schema cache TTL in seconds (24 hours) |

## Volumes

| Mount Point | Purpose |
|---|---|
| `/app/cache` | Persists API schema cache between container restarts |

```bash
# Using a named volume (recommended)
docker run -d \
  --name fortimonitor-mcp \
  -e FORTIMONITOR_API_KEY=your-key \
  -v fortimonitor-cache:/app/cache \
  gjenkins20/fortimonitor-mcp:latest
```

## Tool Categories (241 Tools)

| Category | Tools | Examples |
|---|---|---|
| Servers | 21 | List, create, update, delete, tag, DNS flush, path monitoring |
| Outages | 22 | Query, acknowledge, escalate, broadcast, delay, historical |
| Metrics & Resources | 6 | Server metrics, agent resources, SNMP metrics |
| Maintenance | 12 | Create, extend, pause, resume, terminate windows |
| Server Groups | 12 | Group CRUD, membership, policies, child groups |
| Templates | 8 | Create, apply, reapply monitoring templates |
| Notifications | 14 | Schedules, contacts, groups, on-call rotations |
| Contacts | 18 | Contact CRUD, contact info, rotating contacts |
| Cloud | 15 | Providers, credentials, discovery, regions |
| DEM | 10 | Applications, instances, locations |
| Compound Services | 11 | Service CRUD, thresholds, availability |
| Dashboards & Status Pages | 10 | Dashboard and public status page CRUD |
| Network Services | 7 | Service CRUD, response time, service types |
| Reporting | 10 | Health summary, statistics, exports, availability |
| SNMP | 12 | Credentials, discovery, resource CRUD |
| OnSight | 12 | On-premises monitoring instances and groups |
| Users & Reference Data | 19 | User CRUD, roles, timezones, account history |
| Countermeasures | 20 | Automated remediation on services and thresholds |
| Bulk Operations | 6 | Bulk acknowledge, bulk tags, advanced search |
| Fabric | 4 | Integration connection management |

## Architectures

Multi-architecture image supporting:

- `linux/amd64`
- `linux/arm64`

## Security

- Runs as non-root user (`mcpuser`, UID 1000)
- No network ports exposed — stdio only
- `no-new-privileges` security option supported
- Multi-stage build excludes build tools from runtime image
- API key passed via environment variable, never baked into the image

## Health Check

The image includes a built-in health check that verifies the configuration can be loaded:

```bash
docker inspect --format='{{.State.Health.Status}}' fortimonitor-mcp
```

## Resource Recommendations

| Resource | Limit | Reservation |
|---|---|---|
| CPU | 1.0 core | 0.25 core |
| Memory | 512 MB | 128 MB |

## Tags

| Tag | Description |
|---|---|
| `latest` | Latest stable release from main branch |
| `X.Y.Z` | Specific version (e.g., `1.0.0`) |
| `X.Y` | Minor version (e.g., `1.0`) |
| `X` | Major version (e.g., `1`) |

## Source Code

[GitHub: gjenkins20/fortimonitor-mcp-server](https://github.com/gjenkins20/fortimonitor-mcp-server)

## License

MIT
