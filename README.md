# FortiMonitor MCP Server

Model Context Protocol (MCP) server for FortiMonitor/Panopta v2 API integration with Claude AI.

## Features

- **Server Management**: List and retrieve details for monitored servers
- **Outage Monitoring**: Query active and resolved outages (alerts)
- **Metrics Access**: Retrieve agent resource metrics for servers
- **Schema Discovery**: Runtime API schema validation and caching
- **Real-time Integration**: Direct API access during Claude conversations
- **Docker Support**: Easy deployment via Docker containers

## Quick Start

### Option A: Docker (Recommended)

The easiest way to run the FortiMonitor MCP Server:

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

## Configuration

Edit `.env`:

```bash
FORTIMONITOR_BASE_URL=https://api2.panopta.com/v2
FORTIMONITOR_API_KEY=your_api_key_here
LOG_LEVEL=INFO
```

## Available Tools

### 1. get_servers

List monitored servers with filtering support.

**Parameters:**
- `name` (string): Filter by server name (partial match)
- `fqdn` (string): Filter by FQDN
- `server_group` (integer): Filter by server group ID
- `status` (string): Filter by server status
- `tags` (array): Filter by tags
- `limit` (integer): Maximum results (default: 50)
- `offset` (integer): Pagination offset

**Example**: "Show me all servers in production"

### 2. get_server_details

Get detailed information about a specific server.

**Parameters:**
- `server_id` (integer, required): ID of the server
- `full` (boolean): Resolve all URLs to actual objects

**Example**: "Get details for server 12345"

### 3. get_outages

Query outages (alerts) with various filters.

**Parameters:**
- `server_id` (integer): Filter by specific server ID
- `severity` (string): Filter by outage severity
- `status` (string): Filter by status (active, resolved)
- `hours_back` (integer): How many hours back to search (default: 24)
- `limit` (integer): Maximum results (default: 50)
- `active_only` (boolean): Only return active outages

**Example**: "Show me critical outages from the last 6 hours"

### 4. get_server_metrics

Retrieve agent resource metrics for a server.

**Parameters:**
- `server_id` (integer, required): ID of the server
- `limit` (integer): Maximum resources to return (default: 50)
- `full` (boolean): Resolve all URLs to actual objects

**Example**: "Show metrics for server 12345"

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
      "cwd": "/path/to/fortimonitor-mcp-server",
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
fortimonitor-mcp-server/
├── README.md
├── DOCKER_DEPLOYMENT.md       # Docker deployment guide
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Docker Compose config
├── requirements.txt
├── setup.py
├── pyproject.toml
├── .env.example
├── .gitignore
├── .dockerignore
├── test_connectivity.py
├── scripts/                   # Build and deployment scripts
│   ├── build.sh / build.bat
│   ├── test-container.sh / test-container.bat
│   ├── push.sh
│   └── release.sh
├── .github/
│   └── workflows/
│       └── docker-build.yml   # CI/CD pipeline
├── src/
│   ├── __init__.py
│   ├── __main__.py
│   ├── server.py              # Main MCP server
│   ├── config.py              # Configuration management
│   ├── fortimonitor/
│   │   ├── __init__.py
│   │   ├── client.py          # FortiMonitor API client
│   │   ├── schema.py          # Schema discovery & validation
│   │   ├── models.py          # Data models
│   │   └── exceptions.py      # Custom exceptions
│   └── tools/
│       ├── __init__.py
│       ├── servers.py         # Server-related tools
│       ├── outages.py         # Outage-related tools
│       └── metrics.py         # Metrics-related tools
├── tests/
│   ├── __init__.py
│   ├── test_client.py
│   └── test_tools.py
├── cache/
│   └── schemas/               # Cached API schemas
└── docs/
    ├── API_REFERENCE.md
    └── DEPLOYMENT.md
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

## License

MIT License
