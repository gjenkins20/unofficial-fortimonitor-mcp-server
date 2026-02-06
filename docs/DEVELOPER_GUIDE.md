# FortiMonitor MCP Server - Developer Guide

This guide covers the architecture, development patterns, and operational details
needed to work on the FortiMonitor MCP Server codebase.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Architecture Overview](#architecture-overview)
3. [How to Add New Tools](#how-to-add-new-tools)
4. [API Client Quirks](#api-client-quirks)
5. [Docker Build and Run Instructions](#docker-build-and-run-instructions)
6. [Environment Variable Reference](#environment-variable-reference)
7. [Running Tests](#running-tests)

---

## Project Structure

```
fortimonitor_mcp_server_claude/
├── src/
│   ├── server.py                          # MCP server entrypoint, dispatch registry
│   ├── config.py                          # Pydantic settings from env vars / .env
│   ├── fortimonitor/
│   │   ├── client.py                      # Synchronous HTTP client (requests lib)
│   │   ├── models.py                      # Pydantic data models (~50 models)
│   │   ├── schema.py                      # Schema caching manager
│   │   └── exceptions.py                  # Custom exception hierarchy
│   └── tools/                             # 33 tool module files (241 tools total)
│       ├── servers.py                     # [tuple] GET servers, GET server details
│       ├── outages.py                     # [tuple] GET outages, check_server_health
│       ├── metrics.py                     # [tuple] GET server metrics
│       ├── outage_management.py           # [tuple] acknowledge, add note, get details
│       ├── server_management.py           # [tuple] set status, create/list maintenance
│       ├── bulk_operations.py             # [tuple] bulk ack, bulk tags, search
│       ├── server_groups.py               # [tuple] group CRUD, network services
│       ├── templates.py                   # [tuple] list/detail templates, apply
│       ├── notifications.py               # [tuple] list schedules/contacts/groups
│       ├── agent_resources.py             # [tuple] list resource types, server resources
│       ├── reporting.py                   # [tuple] health summary, stats, exports
│       ├── outage_enhanced.py             # [dict] broadcast, escalate, delay, etc.
│       ├── server_enhanced.py             # [dict] CRUD, attributes, logs, DNS, paths
│       ├── maintenance_enhanced.py        # [dict] detail, update, extend, pause
│       ├── server_groups_enhanced.py      # [dict] members, policy, compound, children
│       ├── templates_enhanced.py          # [dict] create, update, delete, reapply
│       ├── cloud.py                       # [dict] providers, credentials, discovery
│       ├── dem.py                         # [dict] DEM apps, instances, locations
│       ├── compound_services.py           # [dict] CRUD, thresholds, availability
│       ├── dashboards.py                  # [dict] dashboard CRUD
│       ├── status_pages.py                # [dict] status page CRUD
│       ├── rotating_contacts.py           # [dict] on-call rotation management
│       ├── contacts_enhanced.py           # [dict] contact CRUD, contact_info, groups
│       ├── notifications_enhanced.py      # [dict] schedule CUD + sub-resource queries
│       ├── network_services.py            # [dict] server network service CRUD
│       ├── monitoring_nodes.py            # [dict] list/detail monitoring nodes
│       ├── network_service_types.py       # [dict] list/detail network service types
│       ├── users.py                       # [dict] user CRUD + addons
│       ├── reference_data.py              # [dict] account history, roles, timezones
│       ├── snmp.py                        # [dict] SNMP credentials, discovery, resources
│       ├── onsight.py                     # [dict] OnSight CRUD, groups, countermeasures
│       ├── fabric.py                      # [dict] fabric connection CRUD
│       └── countermeasures.py             # [dict] countermeasures, thresholds, metadata
├── tests/
│   ├── conftest.py                        # Shared pytest fixtures (mock_client)
│   ├── test_registry.py                   # Registry integrity (241 tools, no dupes)
│   ├── test_tool_definitions.py           # JSON Schema validation for all tools
│   ├── test_dict_tool_handlers.py         # Handler tests for dict-based modules
│   ├── test_client.py                     # API client unit tests
│   ├── test_server.py                     # Server class tests
│   └── test_tools.py                      # Handler tests for tuple-based modules
├── Dockerfile                             # Multi-stage Docker build
├── docker-compose.yml                     # Docker Compose for easy deployment
├── pyproject.toml                         # Project metadata, pytest/black/mypy config
├── requirements.txt                       # Python dependencies
├── setup.py                               # Setuptools entrypoint
├── .env.example                           # Environment variable template
└── venv/                                  # Virtual environment (not .venv/)
```

**Key naming note:** The virtual environment directory is `venv/`, not `.venv/`.

---

## Architecture Overview

The server follows a three-layer architecture:

```
MCP Client (e.g. Claude Desktop)
        |
        | stdio (JSON-RPC over stdin/stdout)
        v
  +--------------+
  | src/server.py |   <-- MCP protocol handling, tool dispatch registry
  +--------------+
        |
        | calls handler(arguments, client)
        v
  +----------------+
  | src/tools/*.py  |   <-- 33 tool files, 241 async handler functions
  +----------------+
        |
        | calls client._request() or typed client methods
        v
  +---------------------------+
  | src/fortimonitor/client.py |   <-- Synchronous HTTP client (requests lib)
  +---------------------------+
        |
        | HTTPS
        v
  FortiMonitor / Panopta v2 API
  (https://api2.panopta.com/v2)
```

### How the registry works

`server.py` builds a flat dispatch table at module load time by calling
`_build_registry()`. This function iterates over two kinds of tool source:

1. **Tuple-based tools** (the original 11 files, 42 tools) -- each file exports
   pairs of `(definition_func, handler_func)` that are gathered in the
   `_ORIGINAL_TOOLS` list.

2. **Dict-based tools** (the newer 22 files, 199 tools) -- each file exports two
   dicts: `MODULE_TOOL_DEFINITIONS` and `MODULE_HANDLERS`, keyed by tool name.

The result is two module-level objects:

- `_TOOL_DEFINITIONS` -- a `list[mcp.types.Tool]` returned by `list_tools()`.
- `_HANDLER_MAP` -- a `dict[str, Callable]` used by `call_tool()` to dispatch.

When a tool call arrives, `FortiMonitorMCPServer.call_tool()` looks up the
handler by name in `_HANDLER_MAP` and calls it with `(arguments, client)`.

### Request flow

```
call_tool("get_servers", {"limit": 10})
  -> _HANDLER_MAP["get_servers"](arguments, client)
    -> client.get_servers(limit=10)       # tuple-based: typed method
       OR client._request("GET", "/server", params={"limit": 10})  # dict-based
    -> HTTP GET https://api2.panopta.com/v2/server?limit=10&api_key=...
    -> returns JSON dict
  -> handler formats result as List[TextContent]
  -> returned to MCP client
```

---

## How to Add New Tools

**Use the dict-based pattern for all new tool files.** The tuple pattern is
legacy and only used by the original 11 files.

### Step 1: Create the tool file

Create a new file at `src/tools/your_resource.py`:

```python
"""FortiMonitor MCP Tools - Your Resource Name."""

import json
import logging
from typing import List

import mcp.types
from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# -- Helper ------------------------------------------------------------------

def _extract_id_from_url(url: str) -> str:
    """Extract the numeric ID from the tail of an API URL."""
    if url:
        parts = url.rstrip("/").split("/")
        if parts:
            return parts[-1]
    return "N/A"


# -- Tool Definitions --------------------------------------------------------

def list_resources_tool_definition() -> Tool:
    return Tool(
        name="list_resources",
        description="List all resources. Returns name, ID, and key details.",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of results to return.",
                },
            },
        },
    )


def get_resource_details_tool_definition() -> Tool:
    return Tool(
        name="get_resource_details",
        description="Get detailed information about a specific resource by ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "resource_id": {
                    "type": "integer",
                    "description": "The resource ID.",
                },
            },
            "required": ["resource_id"],
        },
    )


# -- Handlers ----------------------------------------------------------------

async def handle_list_resources(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_resources tool execution."""
    try:
        limit = arguments.get("limit", 50)
        result = client._request("GET", "resource", params={"limit": limit})

        items = result.get("resource_list", [])
        if not items:
            return [TextContent(type="text", text="No resources found.")]

        output = f"Found {len(items)} resource(s):\n\n"
        for item in items:
            name = item.get("name", "N/A")
            rid = _extract_id_from_url(item.get("url", ""))
            output += f"- {name} (ID: {rid})\n"

        return [TextContent(type="text", text=output)]

    except APIError as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_get_resource_details(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_resource_details tool execution."""
    try:
        resource_id = arguments["resource_id"]
        result = client._request("GET", f"resource/{resource_id}")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Resource {arguments.get('resource_id')} not found."
        )]
    except APIError as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# -- Export Dicts ------------------------------------------------------------

YOUR_RESOURCE_TOOL_DEFINITIONS = {
    "list_resources": list_resources_tool_definition,
    "get_resource_details": get_resource_details_tool_definition,
}

YOUR_RESOURCE_HANDLERS = {
    "list_resources": handle_list_resources,
    "get_resource_details": handle_get_resource_details,
}
```

**Important conventions:**

- Tool names must be `snake_case`.
- Handler functions are `async` and accept `(arguments: dict, client)`.
- Handlers return `List[TextContent]` -- never raise exceptions to the caller;
  catch them and return error text instead.
- Call `client._request(method, endpoint, params=..., json_data=...)` directly
  rather than adding typed methods to the client class.
- The export dict keys must exactly match the `name` field in the corresponding
  `Tool` object.

### Step 2: Register the module in server.py

Open `src/server.py` and add two things:

**A. Import the dicts** (near the top of the file, with the other dict imports):

```python
from .tools.your_resource import (
    YOUR_RESOURCE_TOOL_DEFINITIONS,
    YOUR_RESOURCE_HANDLERS,
)
```

**B. Add to `_build_registry()`** (inside the `for defn_dict, handler_dict in [...]` loop):

```python
(YOUR_RESOURCE_TOOL_DEFINITIONS, YOUR_RESOURCE_HANDLERS),
```

That is all that is needed. The registry builder will iterate your dicts, call
each definition lambda/function to produce `Tool` objects, and map each tool
name to its handler.

### Step 3: Write tests

Add tests in `tests/test_dict_tool_handlers.py` following the existing pattern:

```python
class TestYourResourceHandlers:
    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_list_resources_success(self, mock_client):
        from src.tools.your_resource import handle_list_resources

        mock_client._request.return_value = {
            "resource_list": [
                {"name": "Res1", "url": "/v2/resource/1"},
            ],
            "meta": {"total_count": 1},
        }
        result = await handle_list_resources({"limit": 50}, mock_client)

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Res1" in result[0].text
        mock_client._request.assert_called_once_with(
            "GET", "resource", params={"limit": 50}
        )

    @pytest.mark.asyncio
    async def test_list_resources_empty(self, mock_client):
        from src.tools.your_resource import handle_list_resources

        mock_client._request.return_value = {"resource_list": [], "meta": {}}
        result = await handle_list_resources({}, mock_client)
        assert "No resources found" in result[0].text
```

Also add your module to the `DICT_MODULES` list in `tests/test_registry.py` so
it is covered by the automated export-consistency checks:

```python
("src.tools.your_resource", "YOUR_RESOURCE_TOOL_DEFINITIONS", "YOUR_RESOURCE_HANDLERS"),
```

### Tuple-based pattern (legacy, for reference only)

The original 11 files export individual functions instead of dicts:

```python
def get_servers_tool_definition() -> Tool:
    return Tool(name="get_servers", ...)

async def handle_get_servers(arguments: dict, client: FortiMonitorClient) -> List[TextContent]:
    # calls client.get_servers(...) -- typed method on the client class
    ...
```

These are registered in `_ORIGINAL_TOOLS` as `(definition_func, handler_func)`
tuples. Do not use this pattern for new work -- it requires adding typed methods
to `client.py` and manually importing each function pair.

---

## API Client Quirks

The FortiMonitor API (Panopta v2) has several behaviors to watch out for.

### IDs are embedded in URL strings

The API does not return numeric `id` fields. Instead, resources have a `url`
field like:

```json
{
  "url": "https://api2.panopta.com/v2/server/12345",
  "name": "web-prod-01"
}
```

To extract the ID, parse the last segment of the URL path:

```python
def _extract_id_from_url(url: str) -> str:
    parts = url.rstrip("/").split("/")
    return parts[-1] if parts else "N/A"
```

The Pydantic models in `models.py` do this via `@property`:

```python
@property
def id(self) -> Optional[int]:
    """Extract server ID from URL."""
    if self.url:
        parts = self.url.rstrip("/").split("/")
        try:
            return int(parts[-1])
        except (ValueError, IndexError):
            return None
    return None
```

### Empty responses for PUT/POST/DELETE

Write operations often return empty response bodies. The client wraps these
as a success dict:

```python
# From client.py _request():
if not response.text or response.text.strip() == "":
    return {"success": True, "status_code": response.status_code}
```

Your handlers should check for this pattern when processing write responses:

```python
response = client._request("POST", "resource", json_data=data)
if isinstance(response, dict) and response.get("url"):
    # API returned the created resource -- extract ID from URL
    resource_id = _extract_id_from_url(response["url"])
elif isinstance(response, dict) and response.get("success"):
    # Empty body -- creation succeeded but no ID returned
    pass
```

### RFC 2822 datetime format

All datetime fields use RFC 2822 format, e.g. `"Thu, 12 Dec 2024 01:33:48 -0000"`.
The Pydantic models parse this with `email.utils.parsedate_to_datetime`:

```python
from email.utils import parsedate_to_datetime

@field_validator("created", "updated", mode="before")
@classmethod
def parse_rfc2822_datetime(cls, v):
    if isinstance(v, str):
        return parsedate_to_datetime(v)
    return v
```

### Endpoint naming conventions

Some endpoint names differ from what you might guess:

| Correct endpoint         | Common wrong name         |
|--------------------------|---------------------------|
| `maintenance_schedule`   | `maintenance_window`      |
| `contact_group`          | `notification_group`      |
| `server_group/{id}/server` | `server_group/{id}` (only returns metadata) |

### Authentication

The API key is passed as a query parameter (`api_key=...`), not in a header.
The client adds this automatically to every request.

### Response list keys

List endpoints return data under a key specific to the resource type. There is
no universal key -- you must check the actual API response:

| Endpoint       | List key               |
|----------------|------------------------|
| `/server`      | `server_list`          |
| `/dashboard`   | `dashboard_list`       |
| `/contact_group` | `contact_group_list` |
| `/user`        | `user_list`            |

All list responses include a `meta` dict with `total_count`, `limit`, `offset`.

### Pagination

Use `limit` and `offset` query parameters for pagination:

```python
result = client._request("GET", "server", params={"limit": 50, "offset": 100})
```

### Retry behavior

The client retries on 500-series errors with exponential backoff (1s, 2s, 4s),
up to 3 attempts. The `requests.Session` also has a `Retry` adapter for
429/500/502/503/504 codes.

### Exception hierarchy

```
FortiMonitorError           # Base exception
├── AuthenticationError     # 401 responses
├── APIError                # General API errors (has .status_code)
│   ├── NotFoundError       # 404 responses
│   └── RateLimitError      # 429 responses
├── ValidationError         # Request validation failures
└── SchemaError             # Schema operation failures
```

---

## Docker Build and Run Instructions

The project uses a multi-stage Docker build. The final image runs as a
non-root user (`mcpuser`) for security.

### Building the image

```bash
docker build -t fortimonitor-mcp .
```

### Running with Docker Compose (recommended)

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your `FORTIMONITOR_API_KEY`.

3. Start the container:
   ```bash
   docker-compose up -d
   ```

4. The container stays alive (`tail -f /dev/null`) and the MCP server is
   invoked on-demand via `docker exec`:
   ```bash
   docker exec -i fortimonitor-mcp python -m src.server
   ```

Docker Compose provides:
- A named volume `fortimonitor-cache` for schema cache persistence.
- Resource limits (1 CPU, 512MB RAM).
- Health check that validates config loads.
- JSON-file logging with 10MB rotation.
- Security hardening (`no-new-privileges`).

### Running with docker directly

```bash
docker run -d \
  --name fortimonitor-mcp \
  --env-file .env \
  fortimonitor-mcp
```

**Important on Windows:** Use `--env-file .env` instead of inline `-e` with
`%VAR%` expansion -- Windows does not expand environment variables the same way.

To invoke the MCP server inside the running container:

```bash
docker exec -i fortimonitor-mcp python -m src.server
```

### Running locally (without Docker)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure env
cp .env.example .env
# Edit .env with your API key

# Run the server
python -m src.server
```

---

## Environment Variable Reference

All configuration is managed by the `Settings` class in `src/config.py`, which
uses `pydantic-settings` to load values from environment variables and `.env`.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FORTIMONITOR_API_KEY` | **Yes** | -- | Your FortiMonitor/Panopta API key |
| `FORTIMONITOR_BASE_URL` | No | `https://api2.panopta.com/v2` | API base URL |
| `MCP_SERVER_NAME` | No | `fortimonitor-mcp` | Server name shown in MCP clients |
| `MCP_SERVER_VERSION` | No | `0.1.0` | Server version string |
| `LOG_LEVEL` | No | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `ENABLE_SCHEMA_CACHE` | No | `true` | Enable caching of API schemas |
| `SCHEMA_CACHE_DIR` | No | `cache/schemas` | Directory for schema cache files |
| `SCHEMA_CACHE_TTL` | No | `86400` | Schema cache TTL in seconds (24 hours) |
| `RATE_LIMIT_REQUESTS` | No | `100` | Max API requests per rate limit period |
| `RATE_LIMIT_PERIOD` | No | `60` | Rate limit period in seconds |

The `Settings` class supports loading from a `.env` file in the project root.
Environment variables take precedence over `.env` file values.

---

## Running Tests

### Prerequisites

Install dev dependencies:

```bash
pip install -r requirements.txt
```

Or install as editable with dev extras:

```bash
pip install -e ".[dev]"
```

### Running the full test suite

```bash
pytest
```

Or with verbose output:

```bash
pytest -v
```

### Running specific test files

```bash
# Registry integrity tests (verifies all 241 tools load without errors)
pytest tests/test_registry.py -v

# Tool definition JSON Schema validation
pytest tests/test_tool_definitions.py -v

# Dict-based handler tests
pytest tests/test_dict_tool_handlers.py -v

# Client tests
pytest tests/test_client.py -v
```

### Running with coverage

```bash
pytest --cov=src --cov-report=term-missing
```

### Test organization

| File | What it tests |
|------|---------------|
| `tests/conftest.py` | Shared fixtures. Provides `mock_client` with a `MagicMock` for `_request()`. |
| `tests/test_registry.py` | Registry integrity: 241 tools registered, no duplicates, every definition has a handler, every handler is async callable, names are snake_case, required fields exist in properties. Also checks each dict-based module's export dicts match. |
| `tests/test_tool_definitions.py` | JSON Schema structure validation for all tool `inputSchema` objects: valid types, required fields are string lists, descriptions are non-empty. |
| `tests/test_dict_tool_handlers.py` | Handler-level tests for dict-based modules. Verifies handlers return `List[TextContent]`, call `client._request` with correct method/endpoint, handle empty results, and handle `APIError`/`NotFoundError` gracefully. |
| `tests/test_client.py` | Unit tests for `FortiMonitorClient`. |
| `tests/test_server.py` | Tests for `FortiMonitorMCPServer` class. |
| `tests/test_tools.py` | Handler tests for the original tuple-based tool modules. |

### Writing new tests

Tests use `unittest.mock.MagicMock` to mock the API client. The `mock_client`
fixture from `conftest.py` provides a pre-configured mock:

```python
@pytest.fixture
def mock_client():
    client = MagicMock()
    client._request = MagicMock()
    return client
```

Tests mock `client._request.return_value` to simulate API responses, then
call the handler and assert on the returned `TextContent` list:

```python
@pytest.mark.asyncio
async def test_list_things(self, mock_client):
    mock_client._request.return_value = {
        "thing_list": [{"name": "Foo", "url": "/v2/thing/1"}],
        "meta": {"total_count": 1},
    }
    result = await handle_list_things({"limit": 50}, mock_client)

    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "Foo" in result[0].text
    mock_client._request.assert_called_once_with(
        "GET", "thing", params={"limit": 50}
    )
```

**Note:** The registry tests patch `src.config.get_settings` with a mock to
avoid requiring a real API key or `.env` file during CI.

### Pytest configuration

From `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

`asyncio_mode = "auto"` means `@pytest.mark.asyncio` is applied automatically
to all async test functions.
