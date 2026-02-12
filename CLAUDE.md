# CLAUDE.md — Project Context for Claude Code Sessions

## What This Project Is

FortiMonitor MCP Server — a Model Context Protocol server that exposes 241 tools for the FortiMonitor/Panopta v2 monitoring API. It connects Claude Desktop or Claude Code to a live FortiMonitor instance.

## Key Files

- `src/server.py` — MCP entrypoint, tool dispatch registry (`_build_registry()`)
- `src/fortimonitor/client.py` — Synchronous HTTP client (requests lib), all API calls go through `_request()`
- `src/fortimonitor/models.py` — Pydantic data models (~50 models)
- `src/tools/` — 33 tool module files containing all 241 tools
- `REMAINING_WORK_INSTRUCTIONS.md` — Full implementation status, coding patterns, API quirks reference

## Architecture

```
Claude <-> MCP Protocol <-> server.py (dispatch) <-> tools/*.py (handlers) <-> client.py <-> FortiMonitor API
```

## Two Tool Registration Patterns

**Original 11 files (tuple pattern):** Export `get_tool_definition()` and `handle_tool()` functions. Registered in `_ORIGINAL_TOOLS` list.

**Newer 22 files (dict pattern):** Export `MODULE_TOOL_DEFINITIONS` and `MODULE_HANDLERS` dicts. Registered via `_build_registry()`. **Use this pattern for all new tools.**

## Adding a New Tool

1. Create or edit a file in `src/tools/` using the dict pattern
2. Define tool in `MODULE_TOOL_DEFINITIONS` dict (lambda returning `mcp.types.Tool`)
3. Write async handler: `async def handle_xyz(arguments: dict, client) -> list`
4. Handler calls `client._request("METHOD", "/endpoint", params=...)` and returns `[TextContent(...)]`
5. Map tool name to handler in `MODULE_HANDLERS` dict
6. Import and register in `server.py` `_build_registry()`

## API Client Quirks

- **Base URL**: `https://api2.panopta.com/v2`
- **Auth**: API key as query param (handled automatically)
- **Client is synchronous** — uses `requests`, not `aiohttp`
- **IDs are in URL strings** — models extract via `@property` parsing, not integer fields
- **Empty responses** — PUT/POST/DELETE often return empty bodies; client wraps as `{"success": True}`
- **Datetime format**: RFC 2822
- **Response list keys vary** — e.g. `server_list`, `contact_group_list`, `dashboard_list`
- **Pagination**: `limit` and `offset` query params

## Running Tests

```bash
pytest tests/ -v
```

Tests use mocked API responses. No live API key needed for testing.

## Branches

- `main` — primary branch (PR target)
- `master` — working branch

## Environment

- Python 3.11+
- Virtual env: `venv/` directory (some machines may use `.venv/`)
- Config via `.env` file or environment variables
- Docker deployment also supported
