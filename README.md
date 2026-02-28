# Unofficial FortiMonitor MCP Server

> **Disclaimer:** This is an unofficial community project. It is not affiliated with, endorsed by, or supported by Fortinet, Inc. or the FortiMonitor/Panopta team. "FortiMonitor" and "Fortinet" are trademarks of Fortinet, Inc. Use at your own risk.

Model Context Protocol (MCP) server for FortiMonitor/Panopta v2 API integration with Claude AI.

**241 tools** across 33 modules providing near-complete coverage of the FortiMonitor v2 API.

## Features

- **Server Management** — CRUD, tagging, attributes, DNS flush, path monitoring, logs
- **Outage Monitoring** — Query, acknowledge, escalate, broadcast, delay, historical incidents
- **Metrics & Resources** — Agent resources, SNMP resources, thresholds, metric graphs
- **Maintenance Windows** — Create, extend, pause, resume, terminate schedules
- **Server Groups** — Group CRUD, membership, compound services, child groups, monitoring policies
- **Templates** — Create, apply, reapply monitoring templates to servers and groups
- **Notifications** — Schedules, contacts, contact groups, rotating on-call contacts
- **Cloud Monitoring** — Providers, credentials, discovery, regions, services
- **DEM** — Digital Experience Monitoring applications, instances, locations
- **Compound Services** — Aggregated service CRUD, thresholds, availability, response time
- **Dashboards & Status Pages** — CRUD for monitoring dashboards and public status pages
- **Reporting** — System health summary, outage statistics, availability reports, CSV exports
- **SNMP** — Credentials, discovery, resource CRUD, metrics
- **OnSight** — On-premises monitoring instances and groups
- **Fabric Connections** — Integration management
- **Countermeasures** — Automated remediation on network services and thresholds
- **User Management** — User CRUD, roles, addons
- **Reference Data** — Contact types, timezones, roles, account history, server attribute types
- **Docker Support** — Easy deployment via Docker containers
- **Windows Support** — Native deployment on Windows for Claude Desktop and Claude Code

## Quick Start

### Option A: Docker (Recommended)

```bash
# Run with Docker
docker run -d \
  --name fortimonitor-mcp \
  -e FORTIMONITOR_API_KEY=your-api-key-here \
  fortimonitor-mcp:latest

# Or use Docker Compose
cp .env.example .env
# Edit .env and set your API key
docker-compose up -d
```

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for detailed Docker instructions.

### Option B: Local Installation

#### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your FortiMonitor API key
```

### 3. Test connectivity

```bash
python test_connectivity.py
```

### 4. Run the server

```bash
python -m src.server
```

### Option C: Windows (Claude Desktop / Claude Code)

See [docs/WINDOWS_DEPLOYMENT.md](docs/WINDOWS_DEPLOYMENT.md) for step-by-step Windows instructions.

## Configuration

Edit `.env`:

```bash
FORTIMONITOR_BASE_URL=https://api2.panopta.com/v2
FORTIMONITOR_API_KEY=your_api_key_here
LOG_LEVEL=INFO
```

## Available Tools (241)

The server exposes 241 MCP tools organized into the following categories. For full parameter details, see the [End-User Guide](docs/USER_GUIDE.md).

| Category | Module(s) | Tools | Description |
|----------|-----------|-------|-------------|
| **Servers** | `servers`, `server_enhanced` | 21 | List, detail, CRUD, attributes, logs, DNS, path monitoring |
| **Outages** | `outages`, `outage_management`, `outage_enhanced` | 22 | Query, health check, acknowledge, escalate, broadcast, delay, historical |
| **Metrics** | `metrics`, `agent_resources` | 6 | Server metrics, agent resource types, resource details |
| **Maintenance** | `server_management`, `maintenance_enhanced` | 12 | Status management, maintenance window CRUD, extend, pause, resume |
| **Bulk Operations** | `bulk_operations` | 6 | Bulk acknowledge, bulk tags, advanced search, active outages |
| **Server Groups** | `server_groups`, `server_groups_enhanced` | 12 | Group CRUD, membership, policies, compound services, child groups |
| **Templates** | `templates`, `templates_enhanced` | 8 | Template CRUD, apply to server/group, reapply |
| **Notifications** | `notifications`, `notifications_enhanced` | 14 | Schedules, contacts, groups, schedule CRUD, sub-resource queries |
| **Contacts** | `contacts_enhanced`, `rotating_contacts` | 18 | Contact CRUD, contact info, contact groups, on-call rotations |
| **Cloud** | `cloud` | 15 | Providers, credentials, discovery, regions, services |
| **DEM** | `dem` | 10 | Applications, instances, locations, path monitoring |
| **Compound Services** | `compound_services` | 11 | Service CRUD, thresholds, availability, network services, response time |
| **Dashboards** | `dashboards` | 5 | Dashboard CRUD |
| **Status Pages** | `status_pages` | 5 | Public status page CRUD |
| **Network Services** | `network_services` | 5 | Server network service CRUD, response time |
| **Monitoring Nodes** | `monitoring_nodes` | 2 | List and detail monitoring nodes |
| **Network Service Types** | `network_service_types` | 2 | List and detail service types |
| **Reporting** | `reporting` | 10 | Health summary, statistics, top alerting, exports, availability reports |
| **Users** | `users` | 6 | User CRUD, addons |
| **Reference Data** | `reference_data` | 13 | Account history, contact types, roles, timezones, attribute types |
| **SNMP** | `snmp` | 12 | Credentials CRUD, discovery, resource CRUD, metrics |
| **OnSight** | `onsight` | 12 | OnSight CRUD, groups, countermeasures, servers |
| **Fabric** | `fabric` | 4 | Fabric connection CRUD |
| **Countermeasures** | `countermeasures` | 20 | Network service & threshold countermeasures, outage metadata, thresholds |

## Integration with Claude Desktop

Add to Claude Desktop config (`claude_desktop_config.json`):

### Option A: Using Docker (Recommended)

First, ensure the container is running:
```bash
docker-compose up -d
```

Then add to your Claude Desktop config:
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

### Option B: Using Local Python

```json
{
  "mcpServers": {
    "fortimonitor": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/unofficial-fortimonitor-mcp-server",
      "env": {
        "FORTIMONITOR_BASE_URL": "https://api2.panopta.com/v2",
        "FORTIMONITOR_API_KEY": "your_key"
      }
    }
  }
}
```

## API Documentation

The server automatically discovers and caches FortiMonitor API schemas for validation and documentation. Schemas are cached in `cache/schemas/` by default.

### Schema Endpoints

- `/schema/resources` - Lists all available API resources
- `/schema/resources/{resource_name}` - Get schema for specific resource

## Development

### Run tests

```bash
pytest tests/ -v
```

### Run tests with coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

### Format code

```bash
black src/ tests/
```

### Type checking

```bash
mypy src/
```

### Lint

```bash
flake8 src/ tests/
```

## Project Structure

```
unofficial-fortimonitor-mcp-server/
├── README.md
├── FORTIMONITOR_API_DOCS.md        # FortiMonitor API documentation
├── Dockerfile                      # Container definition
├── docker-compose.yml              # Docker Compose config
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .gitignore
├── .dockerignore
├── test_connectivity.py
├── scripts/                        # Build and deployment scripts
│   ├── build.sh / build.bat
│   ├── test-container.sh / test-container.bat
│   ├── push.sh
│   └── release.sh
├── .github/
│   └── workflows/
│       └── docker-build.yml        # CI/CD pipeline
├── src/
│   ├── __init__.py
│   ├── __main__.py
│   ├── server.py                   # MCP server entrypoint, dispatch registry
│   ├── config.py                   # Pydantic settings from env vars / .env
│   ├── fortimonitor/
│   │   ├── client.py               # Synchronous HTTP client (requests lib)
│   │   ├── schema.py               # Schema discovery & caching
│   │   ├── models.py               # Pydantic data models (~50 models)
│   │   └── exceptions.py           # Custom exceptions
│   └── tools/                      # 33 tool module files (241 tools)
│       ├── servers.py              # Server list/detail
│       ├── server_enhanced.py      # Server CRUD, attributes, logs, path monitoring
│       ├── outages.py              # Outage queries, health check
│       ├── outage_management.py    # Acknowledge, notes, details
│       ├── outage_enhanced.py      # Broadcast, escalate, delay, historical
│       ├── metrics.py              # Server metrics
│       ├── agent_resources.py      # Agent resource types & details
│       ├── server_management.py    # Status management, maintenance
│       ├── maintenance_enhanced.py # Maintenance CRUD, extend, pause
│       ├── bulk_operations.py      # Bulk ops, advanced search
│       ├── server_groups.py        # Server group CRUD
│       ├── server_groups_enhanced.py # Group members, policies, children
│       ├── templates.py            # Template list/detail/apply
│       ├── templates_enhanced.py   # Template CRUD, reapply
│       ├── notifications.py        # Notification schedules/contacts/groups
│       ├── notifications_enhanced.py # Schedule CRUD, sub-resources
│       ├── contacts_enhanced.py    # Contact CRUD, info, groups
│       ├── rotating_contacts.py    # On-call rotation management
│       ├── network_services.py     # Network service CRUD, response time
│       ├── network_service_types.py # Service type list/detail
│       ├── monitoring_nodes.py     # Monitoring node list/detail
│       ├── cloud.py                # Cloud providers, credentials, discovery
│       ├── dem.py                  # DEM applications, instances, locations
│       ├── compound_services.py    # Compound service CRUD, thresholds
│       ├── dashboards.py           # Dashboard CRUD
│       ├── status_pages.py         # Status page CRUD
│       ├── reporting.py            # Health, stats, exports, availability
│       ├── users.py                # User CRUD, addons
│       ├── reference_data.py       # Account history, types, roles, timezones
│       ├── snmp.py                 # SNMP credentials, discovery, resources
│       ├── onsight.py              # OnSight CRUD, groups
│       ├── fabric.py               # Fabric connection CRUD
│       └── countermeasures.py      # Countermeasures, thresholds, metadata
├── tests/
│   ├── conftest.py                 # Test fixtures
│   ├── test_client.py              # API client tests
│   ├── test_tools.py               # Original tool tests
│   ├── test_tool_definitions.py    # Tool definition validation
│   ├── test_dict_tool_handlers.py  # Dict-pattern handler tests
│   ├── test_registry.py            # Registry build tests
│   └── test_server.py              # Server integration tests
├── cache/
│   └── schemas/                    # Cached API schemas
└── docs/
    ├── USER_GUIDE.md               # End-user guide
    ├── DEVELOPER_GUIDE.md          # Developer/contributor guide
    └── WINDOWS_DEPLOYMENT.md       # Windows setup for Claude Desktop/Code
```

## Troubleshooting

### Authentication Errors

- Verify API key in `.env`
- Check base URL is correct (`https://api2.panopta.com/v2`)
- Test API key with curl:
  ```bash
  curl "https://api2.panopta.com/v2/server?api_key=YOUR_KEY&limit=1"
  ```

### Schema Discovery Failures

- Check network connectivity
- Verify `cache/schemas/` directory exists and is writable
- Clear cache and retry: `rm -rf cache/schemas/*`

### MCP Server Not Appearing in Claude

- Check Claude Desktop config syntax
- Verify file paths are absolute
- Restart Claude Desktop completely
- Check server logs for startup errors

## About the Developer

Built by **Gregori Jenkins** — originally from Chicago, a humble student of Computer Science, and a proud cat dad.

[Connect on LinkedIn](https://www.linkedin.com/in/gregorijenkins)

## License

MIT License — see [LICENSE](LICENSE) for details.
