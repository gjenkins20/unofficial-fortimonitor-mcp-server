# FortiMonitor MCP Server - Docker Quick Start

This guide helps you get started with the FortiMonitor MCP Server container.

## Prerequisites

- Docker Desktop installed and running
- GitHub account (with access to the repository)
- GitHub Personal Access Token with `read:packages` scope
- Your own FortiMonitor API key

## Quick Start

### 1. Create a GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens/new
2. Give it a name (e.g., "Docker Pull Access")
3. Select scope: `read:packages`
4. Click "Generate token" and copy it

### 2. Login to GitHub Container Registry

```bash
docker login ghcr.io -u YOUR_GITHUB_USERNAME
```

When prompted for password, paste your Personal Access Token.

### 3. Pull the Image

```bash
docker pull ghcr.io/gjenkins20/unofficial-fortimonitor-mcp:latest
```

### 3. Create Environment File

Create a `.env` file with your API key:

```bash
# .env
FORTIMONITOR_API_KEY=your-api-key-here
```

### 4. Run with Docker Compose (Recommended)

Save the `docker-compose.share.yml` file and run:

```bash
docker-compose -f docker-compose.share.yml up -d
```

### 5. Run with Docker CLI (Alternative)

```bash
docker run -d \
  --name unofficial-fortimonitor-mcp \
  -e FORTIMONITOR_API_KEY=your-api-key-here \
  --restart unless-stopped \
  ghcr.io/gjenkins20/unofficial-fortimonitor-mcp:latest
```

## Verification

Check the container is running:

```bash
docker ps | grep unofficial-fortimonitor-mcp
```

Test the configuration:

```bash
docker exec unofficial-fortimonitor-mcp python -c "from src.config import get_settings; print('OK')"
```

## Using with Claude Desktop

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json` on Linux/Mac or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "fortimonitor": {
      "command": "docker",
      "args": ["exec", "-i", "unofficial-fortimonitor-mcp", "python", "-m", "src.server"]
    }
  }
}
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FORTIMONITOR_API_KEY` | Yes | - | Your FortiMonitor API key |
| `FORTIMONITOR_BASE_URL` | No | `https://api2.panopta.com/v2` | API base URL |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `RATE_LIMIT_REQUESTS` | No | `100` | Max API requests per period |
| `RATE_LIMIT_PERIOD` | No | `60` | Rate limit period in seconds |

## Troubleshooting

### Container won't start
```bash
docker logs unofficial-fortimonitor-mcp
```

### API key issues
Verify your API key is set correctly:
```bash
docker exec unofficial-fortimonitor-mcp python -c "from src.config import get_settings; s = get_settings(); print(f'API Key set: {bool(s.fortimonitor_api_key)}')"
```

### Update to latest version
```bash
docker pull ghcr.io/gjenkins20/unofficial-fortimonitor-mcp:latest
docker-compose -f docker-compose.share.yml up -d --force-recreate
```

## Support

For issues, contact the repository maintainer.
