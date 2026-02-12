# FortiMonitor MCP Server - Implementation Status & Remaining Work
## Updated 2026-02-06

---

## Current State Summary

| Metric | Value |
|--------|-------|
| Total Documented API Endpoints | ~212 |
| **Implemented MCP Tools** | **241 (across 33 tool files)** |
| **Current Coverage** | **~100%** |
| Target Coverage (per engineering doc) | 75%+ ✅ MET |
| Target Tool Count (per engineering doc) | 150+ ✅ MET |
| P1 (Critical Fixes) | ✅ 100% COMPLETE |
| P2 (High-Value Features) | ✅ 100% COMPLETE |
| P3 (Enhanced Features) | ✅ 100% COMPLETE |
| P4 (Complete Coverage) | ✅ 100% COMPLETE |

**All engineering targets exceeded. P1-P4 fully implemented. 241 tools across 33 files.**

---

## Project Structure Reference

```
src/
├── server.py                          # MCP server entrypoint, dispatch registry
├── fortimonitor/
│   ├── client.py                      # Synchronous HTTP client (requests lib)
│   └── models.py                      # Pydantic data models (~50 models)
└── tools/                             # 33 tool module files
    ├── servers.py                     # [tuple] GET servers, GET server details
    ├── outages.py                     # [tuple] GET outages, check_server_health
    ├── metrics.py                     # [tuple] GET server metrics
    ├── outage_management.py           # [tuple] acknowledge, add note, get details
    ├── server_management.py           # [tuple] set status, create/list maintenance
    ├── bulk_operations.py             # [tuple] bulk ack, bulk tags, search, active outages
    ├── server_groups.py               # [tuple] group CRUD, network services
    ├── templates.py                   # [tuple] list/detail templates, apply to server/group
    ├── notifications.py               # [tuple] list schedules/contacts/groups
    ├── agent_resources.py             # [tuple] list resource types, server resources
    ├── reporting.py                   # [tuple] health summary, stats, exports
    ├── outage_enhanced.py             # [dict] 13 tools - broadcast, escalate, delay, historical, etc.
    ├── server_enhanced.py             # [dict] 19 tools - CRUD, attributes, logs, DNS, path monitoring
    ├── maintenance_enhanced.py        # [dict] 9 tools - detail, update, extend, pause, active/pending
    ├── server_groups_enhanced.py      # [dict] 4 tools - members, policy, compound, children
    ├── templates_enhanced.py          # [dict] 4 tools - create, update, delete, reapply
    ├── cloud.py                       # [dict] 15 tools - providers, credentials, discovery
    ├── dem.py                         # [dict] 10 tools - DEM apps, instances, locations, path monitoring
    ├── compound_services.py           # [dict] 11 tools - CRUD, thresholds, availability, ns detail
    ├── dashboards.py                  # [dict] 5 tools - dashboard CRUD
    ├── status_pages.py                # [dict] 5 tools - status page CRUD
    ├── rotating_contacts.py           # [dict] 6 tools - on-call rotation management
    ├── contacts_enhanced.py           # [dict] 12 tools - contact CRUD, contact_info, contact_group CUD
    ├── notifications_enhanced.py      # [dict] 8 tools - schedule CUD + sub-resource queries
    ├── network_services.py            # [dict] 5 tools - server network service CRUD + response time
    ├── monitoring_nodes.py            # [dict] 2 tools - list/detail monitoring nodes
    ├── network_service_types.py       # [dict] 2 tools - list/detail network service types
    ├── users.py                       # [dict] 6 tools - user CRUD + addons
    ├── reference_data.py              # [dict] 13 tools - account history, contact types, roles, timezones, etc.
    ├── snmp.py                        # [dict] 12 tools - SNMP credentials, discovery, resources
    ├── onsight.py                     # [dict] 12 tools - OnSight CRUD, groups, countermeasures
    ├── fabric.py                      # [dict] 4 tools - fabric connection CRUD
    └── countermeasures.py             # [dict] 20 tools - countermeasures, thresholds, metadata
```

### Two Registration Patterns

**Original 11 files (tuple pattern):**
```python
# Each file exports two functions:
def get_tool_definition():
    return mcp.types.Tool(name="tool_name", ...)

async def handle_tool(arguments, client):
    return [TextContent(...)]

# server.py registers as:
_ORIGINAL_TOOLS = [
    (get_tool_definition, handle_tool),
    ...
]
```

**Newer 22 files (dict pattern):**
```python
# Each file exports two dicts:
MODULE_TOOL_DEFINITIONS = {
    "tool_name": lambda: mcp.types.Tool(name="tool_name", ...),
}

MODULE_HANDLERS = {
    "tool_name": handle_tool_func,
}

# server.py _build_registry() iterates these dicts
```

**Use the dict pattern for all new tool files.**

### New Tool Handler Pattern

New dict-based tools call `client._request()` directly:
```python
async def handle_example(arguments: dict, client) -> list:
    result = client._request("GET", "/endpoint", params={"limit": 50})
    return [TextContent(type="text", text=json.dumps(result, indent=2))]
```

### Registering New Modules in server.py

In `server.py`, find `_build_registry()` and add your new module's dicts to the iteration list:
```python
from src.tools.your_new_module import YOUR_MODULE_TOOL_DEFINITIONS, YOUR_MODULE_HANDLERS
```

Then add the tuple `(YOUR_MODULE_TOOL_DEFINITIONS, YOUR_MODULE_HANDLERS)` to the list of dict-based modules iterated in `_build_registry()`.

---

## API Client Notes

- **Base URL**: `https://api2.panopta.com/v2`
- **Auth**: API key passed as query param `api_key` (handled automatically by client)
- **Client is synchronous** — uses `requests`, not `aiohttp`
- **IDs are in URL strings**, not integer fields — models extract via `@property` parsing
- **Empty responses** common for PUT/POST/DELETE — client wraps as `{"success": True}`
- **Datetime format**: RFC 2822
- **Endpoint naming**: `maintenance_schedule` (not `maintenance_window`), `contact_group` (not `notification_group`)

---

## COMPLETED — PRIORITY 3 ✅

All P3 items have been implemented. 45 new tools were added across 6 new files plus 4 patched into existing P2 files.

### Files Created (P3)
- `src/tools/dashboards.py` — 5 tools (dashboard CRUD)
- `src/tools/status_pages.py` — 5 tools (status page CRUD)
- `src/tools/rotating_contacts.py` — 6 tools (on-call rotation management)
- `src/tools/contacts_enhanced.py` — 12 tools (contact CRUD, contact_info CRUD, contact_group CUD)
- `src/tools/notifications_enhanced.py` — 8 tools (schedule CUD + 5 sub-resource GETs)
- `src/tools/network_services.py` — 5 tools (server network service CRUD + response time)

### P2 Gaps Closed
- `dem.py` — Added `update_dem_instance_path_monitoring`, `update_dem_location` (2 tools)
- `compound_services.py` — Added `get_compound_service_network_service_details` (1 tool)
- `maintenance_enhanced.py` — Added `list_active_or_pending_maintenance` (1 tool)

---

## COMPLETED — OPTIONAL P3 Additions ✅

All optional P3 items implemented (9 tools):

| Tool Name | Method | Endpoint | File | Status |
|-----------|--------|----------|------|--------|
| `list_monitoring_nodes` | GET | `/monitoring_node` | `monitoring_nodes.py` | ✅ Done |
| `get_monitoring_node_details` | GET | `/monitoring_node/{id}` | `monitoring_nodes.py` | ✅ Done |
| `list_network_service_types` | GET | `/network_service_type` | `network_service_types.py` | ✅ Done |
| `get_network_service_type_details` | GET | `/network_service_type/{id}` | `network_service_types.py` | ✅ Done |
| `create_historical_outage` | POST | `/historical_outage` | `outage_enhanced.py` | ✅ Done |
| `list_server_path_monitoring` | GET | `/server/{id}/path_monitoring` | `server_enhanced.py` | ✅ Done |
| `create_server_path_monitoring` | POST | `/server/{id}/path_monitoring` | `server_enhanced.py` | ✅ Done |
| `delete_server_path_monitoring` | DELETE | `/server/{id}/path_monitoring/{id}` | `server_enhanced.py` | ✅ Done |
| `get_path_monitoring_results` | GET | `/server/{id}/path_monitoring/{id}/results` | `server_enhanced.py` | ✅ Done |

---

## COMPLETED — PRIORITY 4 (Stretch Goal) ✅

All P4 items implemented (76 tools across 8 new files).

### 4.1 User Management — ✅ `src/tools/users.py` (6 tools)
- `list_users`, `get_user_details`, `create_user`, `update_user`, `delete_user`, `get_user_addons`

### 4.2 Reference Data — ✅ `src/tools/reference_data.py` (13 tools)
- Account history, contact types, roles, timezones, server attribute types (full CRUD), prometheus resource

### 4.3 SNMP Resources — ✅ `src/tools/snmp.py` (12 tools)
- SNMP credentials CRUD, SNMP discovery, server SNMP resource CRUD, SNMP resource metrics

### 4.4 OnSight — ✅ `src/tools/onsight.py` (12 tools)
- OnSight CRUD + countermeasures + servers, OnSight group CRUD

### 4.5 Fabric Connections — ✅ `src/tools/fabric.py` (4 tools)
- Fabric connection list, get, create, delete

### 4.6 Countermeasures — ✅ `src/tools/countermeasures.py` (20 tools)
- Network service countermeasures (5 ops), threshold countermeasures (5 ops)
- Outage countermeasures (2 ops), metadata (1 op), output (1 op)
- Outage metadata (2 ops), preoutage graph (1 op)
- Agent resource threshold management (3 ops)

### 4.7 Threshold Management — ✅ Included in `countermeasures.py`
- GET/PUT/DELETE `/server/{id}/agent_resource/{id}/agent_resource_threshold/{id}`

### 4.8 Public (Unauthenticated) Outage Endpoints — SKIPPED
```
GET/PUT /public/outage/{HASH}/acknowledge
GET/PUT /public/outage/{HASH}/delay/{seconds}
GET/PUT /public/outage/{HASH}/escalate
```
Not applicable for MCP (requires hash, not API key auth).

---

## Minor P2 Gaps — ✅ CLOSED

All P2 gap items have been implemented:

| Item | Endpoint | File | Status |
|------|----------|------|--------|
| DEM path monitoring | `PUT /dem_application/{id}/instance/{id}/path_monitoring` | `dem.py` | ✅ Done |
| DEM location update | `PUT /dem_application/{id}/location` | `dem.py` | ✅ Done |
| Compound service network service detail | `GET /compound_service/{id}/network_service/{ns_id}` | `compound_services.py` | ✅ Done |
| Maintenance active_or_pending | `GET /maintenance_schedule/active_or_pending` | `maintenance_enhanced.py` | ✅ Done |

---

## Implementation History

### Phase 1 (completed previously): 120 tools across 19 files
### Phase 2 — P3 (completed 2026-02-06): +45 tools → 165 total across 25 files

Implementation order was:
1. ✅ **Dashboards** (5 tools) — `dashboards.py`
2. ✅ **Contact CRUD + Contact Group CRUD** (12 tools) — `contacts_enhanced.py`
3. ✅ **Notification Schedule CRUD + sub-resources** (8 tools) — `notifications_enhanced.py`
4. ✅ **Rotating Contacts** (6 tools) — `rotating_contacts.py`
5. ✅ **Status Pages** (5 tools) — `status_pages.py`
6. ✅ **Server Network Service CRUD** (5 tools) — `network_services.py`
7. ✅ **P2 gap closure** (4 tools) — patched `dem.py`, `compound_services.py`, `maintenance_enhanced.py`

### Phase 3 — P4 + P3 leftovers (completed 2026-02-06): +76 tools → 241 total across 33 files

Implementation order was:
1. ✅ **Monitoring nodes** (2 tools) — `monitoring_nodes.py` (new)
2. ✅ **Network service types** (2 tools) — `network_service_types.py` (new)
3. ✅ **Historical outage** (1 tool) — patched `outage_enhanced.py`
4. ✅ **Path monitoring** (4 tools) — patched `server_enhanced.py`
5. ✅ **Users** (6 tools) — `users.py` (new)
6. ✅ **Reference Data** (13 tools) — `reference_data.py` (new)
7. ✅ **SNMP** (12 tools) — `snmp.py` (new)
8. ✅ **OnSight** (12 tools) — `onsight.py` (new)
9. ✅ **Fabric** (4 tools) — `fabric.py` (new)
10. ✅ **Countermeasures + Thresholds** (20 tools) — `countermeasures.py` (new)

**Result: 241 total tools, ~100% coverage. All priorities complete.**

---

## Template for New Tool Files

```python
"""
FortiMonitor MCP Tools - [Resource Name]
[Brief description]
"""

import json
from typing import Any
import mcp.types

# ── Tool Definitions ──────────────────────────────────────────────

RESOURCE_TOOL_DEFINITIONS = {

    "list_resources": lambda: mcp.types.Tool(
        name="list_resources",
        description="List all resources. Returns name, ID, and key details.",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "number",
                    "description": "Maximum number of results to return.",
                },
            },
        },
    ),

    "get_resource_details": lambda: mcp.types.Tool(
        name="get_resource_details",
        description="Get detailed information about a specific resource by ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "resource_id": {
                    "type": "number",
                    "description": "The resource ID.",
                },
            },
            "required": ["resource_id"],
        },
    ),

    # ... more tool definitions
}

# ── Handlers ──────────────────────────────────────────────────────

async def handle_list_resources(arguments: dict, client) -> list:
    params = {}
    if arguments.get("limit"):
        params["limit"] = arguments["limit"]

    result = client._request("GET", "/resource", params=params)

    items = result.get("resource_list", [])
    if not items:
        return [mcp.types.TextContent(type="text", text="No resources found.")]

    output = f"Found {len(items)} resource(s):\n\n"
    for item in items:
        output += f"- {item.get('name', 'N/A')}\n"

    return [mcp.types.TextContent(type="text", text=output)]


async def handle_get_resource_details(arguments: dict, client) -> list:
    resource_id = arguments["resource_id"]
    result = client._request("GET", f"/resource/{resource_id}")
    return [mcp.types.TextContent(type="text", text=json.dumps(result, indent=2))]


# ... more handlers

RESOURCE_HANDLERS = {
    "list_resources": handle_list_resources,
    "get_resource_details": handle_get_resource_details,
    # ... map every tool name to its handler
}
```

---

## Key Reminders

- **Virtual env**: `venv/` (not `.venv/`)
- **Docker**: Use `--env-file .env` when starting container
- **API IDs**: Extracted from URL strings, not integer fields
- **Empty responses**: PUT/POST/DELETE often return empty bodies
- **Response list keys**: Vary by resource — check actual API response for the list key name (e.g., `server_list`, `contact_group_list`, `dashboard_list`, etc.)
- **Pagination**: Use `limit` and `offset` query params
- **Branch**: Working on `master`, main branch is `main`

---

## Post-Implementation Tasks — COMPLETED ✅

### Documentation — Developer Guide ✅
Created `docs/DEVELOPER_GUIDE.md` covering:
- Architecture overview (client → tools → server registry)
- How to add new tools (both tuple and dict patterns)
- API client quirks (ID extraction, empty responses, datetime format)
- Docker build/run instructions
- Environment variable reference

### Documentation — End-User Guide ✅
Created `docs/USER_GUIDE.md` covering:
- Installation and setup (Docker vs local)
- Configuration (API key, base URL)
- Tool reference catalog (all 241 tools with descriptions and parameters)
- Common workflows and usage examples
- Troubleshooting

### Documentation — Windows Deployment Guide ✅
Created `docs/WINDOWS_DEPLOYMENT.md` covering:
- Claude Desktop and Claude Code setup on Windows 10/11

### README Update ✅
Updated `README.md` to reflect full 241-tool implementation with categorized tool table, accurate project structure, and links to all guides.
