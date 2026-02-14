# FortiMonitor MCP Server — Project Detail

> A comprehensive technical overview of the project's architecture, major components, novel features, and operational design.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Data Flow Diagram](#data-flow-diagram)
4. [Major Components](#major-components)
   - [MCP Server Core](#1-mcp-server-core-srcserverpy)
   - [Configuration Manager](#2-configuration-manager-srcconfigpy)
   - [FortiMonitor API Client](#3-fortimonitor-api-client-srcfortimonitorclientpy)
   - [Data Models](#4-data-models-srcfortimonitormodelspy)
   - [Schema Manager](#5-schema-manager-srcfortimonitorschemapy)
   - [Exception Hierarchy](#6-exception-hierarchy-srcfortimonitorexceptionspy)
   - [Tool Modules](#7-tool-modules-srctools)
   - [Docker Infrastructure](#8-docker-infrastructure)
5. [Tool Registry Architecture](#tool-registry-architecture)
6. [Complete Tool Inventory](#complete-tool-inventory)
7. [Novel Features](#novel-features)
8. [Security & Resilience Design](#security--resilience-design)
9. [Deployment Architecture](#deployment-architecture)
10. [Technology Stack](#technology-stack)

---

## Project Overview

The **FortiMonitor MCP Server** is a Python application that implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) to bridge the FortiMonitor/Panopta infrastructure monitoring platform with Claude AI. It wraps the entire FortiMonitor REST API (200+ endpoints) into **241 conversational tools** organized across **33 modules**, enabling DevOps and SRE teams to manage their monitoring infrastructure through natural language.

---

## High-Level Architecture

```
+----------------------------------------------------------------------+
|                        USER'S ENVIRONMENT                            |
|                                                                      |
|  +------------------+       MCP (stdio)       +-------------------+  |
|  |                  | <---------------------> |                   |  |
|  |  Claude Desktop  |   JSON-RPC over stdin   |  FortiMonitor     |  |
|  |  (or any MCP     |       / stdout          |  MCP Server       |  |
|  |   client)        |                         |  (Python 3.9+)    |  |
|  |                  |                         |                   |  |
|  +------------------+                         +--------+----------+  |
|                                                        |             |
+--------------------------------------------------------|-------------+
                                                         |
                                               HTTPS REST API
                                             (api_key auth via
                                              query parameter)
                                                         |
                                                         v
                                          +------------------------------+
                                          |                              |
                                          |  FortiMonitor / Panopta      |
                                          |  Cloud Platform              |
                                          |  https://api2.panopta.com/v2 |
                                          |                              |
                                          +------------------------------+
```

---

## Data Flow Diagram

The following illustrates the lifecycle of a single user request from natural language to API response:

```
User: "Show me all servers with active outages"
  |
  v
+-------------------+
| Claude Desktop    |  1. User speaks in natural language
| (MCP Client)      |
+--------+----------+
         |
         | 2. MCP call_tool("get_servers_with_active_outages", {...})
         |    [JSON-RPC over stdio]
         v
+-------------------+
| MCP Server Core   |  3. Dispatches to handler via _HANDLER_MAP lookup
| (server.py)       |
+--------+----------+
         |
         | 4. Handler invoked: handle_get_servers_with_active_outages()
         v
+-------------------+
| Tool Handler      |  5. Validates arguments, transforms parameters
| (bulk_operations) |
+--------+----------+
         |
         | 6. Calls client methods (get_active_outages, get_servers, etc.)
         v
+-------------------+
| FortiMonitor      |  7. Builds HTTP request with retry logic
| API Client        |     - Adds API key as query param
| (client.py)       |     - Sets JSON headers
+--------+----------+     - Retries on 429/5xx with backoff
         |
         | 8. GET https://api2.panopta.com/v2/outage/active?api_key=...
         v
+-------------------+
| FortiMonitor      |  9. Returns JSON response
| Cloud API         |
+--------+----------+
         |
         | 10. Raw JSON response
         v
+-------------------+
| Pydantic Models   |  11. Parses response into typed models
| (models.py)       |      - URL-based ID extraction
|                   |      - RFC 2822 date parsing
+--------+----------+      - Field aliasing
         |
         | 12. Structured data objects
         v
+-------------------+
| Tool Handler      |  13. Formats results as MCP TextContent
| (bulk_operations) |
+--------+----------+
         |
         | 14. MCP response: List[TextContent]
         v
+-------------------+
| Claude Desktop    |  15. Claude presents natural language summary
| (MCP Client)      |      to the user
+-------------------+
```

---

## Major Components

### 1. MCP Server Core (`src/server.py`)

The central orchestrator that wires together the MCP protocol, tool registry, and API client.

```
+------------------------------------------+
|        FortiMonitorMCPServer             |
|------------------------------------------|
| - server: mcp.Server                     |
| - client: FortiMonitorClient (lazy)      |
|------------------------------------------|
| + __init__()                             |
|   - Creates MCP Server instance          |
|   - Registers protocol handlers          |
|   - Logs tool count on startup           |
|                                          |
| + _setup_handlers()                      |
|   - @server.list_tools() -> 241 tools    |
|   - @server.call_tool() -> dispatch      |
|     via _HANDLER_MAP[name]               |
|                                          |
| + run()                                  |
|   - Opens stdio transport                |
|   - Advertises ToolsCapability           |
|   - Runs event loop until shutdown       |
+------------------------------------------+
          |
          | Built at module load time
          v
+------------------------------------------+
|        _build_registry()                 |
|------------------------------------------|
| Aggregates tools from two patterns:      |
|                                          |
| Pattern A (Tuple):                       |
|   _ORIGINAL_TOOLS list of                |
|   (definition_func, handler_func) pairs  |
|   -> 44 tools from 11 modules            |
|                                          |
| Pattern B (Dict):                        |
|   TOOL_DEFINITIONS / HANDLERS dicts      |
|   {name: func} from 22 modules           |
|   -> 197 tools from 22 modules           |
|                                          |
| Output:                                  |
|   _TOOL_DEFINITIONS: List[Tool] (241)    |
|   _HANDLER_MAP: Dict[str, Callable]      |
+------------------------------------------+
```

**Key design decisions:**
- **Lazy client initialization** — The `FortiMonitorClient` is not instantiated until the first tool call, avoiding startup failures if the API key is missing or the API is unreachable.
- **Module-level registry build** — `_build_registry()` runs once at import time, producing a flat list and lookup dictionary for O(1) tool dispatch.

---

### 2. Configuration Manager (`src/config.py`)

Centralized configuration using Pydantic Settings with environment variable and `.env` file support.

```
+------------------------------------------+
|        Settings (BaseSettings)           |
|------------------------------------------|
| FortiMonitor API:                        |
|   fortimonitor_base_url  [HttpUrl]       |
|   fortimonitor_api_key   [str, required] |
|                                          |
| MCP Server:                              |
|   mcp_server_name        [str]           |
|   mcp_server_version     [str]           |
|   log_level              [str]           |
|                                          |
| Schema Caching:                          |
|   enable_schema_cache    [bool]          |
|   schema_cache_dir       [Path]          |
|   schema_cache_ttl       [int, 86400s]   |
|                                          |
| Rate Limiting:                           |
|   rate_limit_requests    [int, 100]      |
|   rate_limit_period      [int, 60s]      |
|------------------------------------------|
| Sources (priority order):                |
|   1. Environment variables               |
|   2. .env file                           |
|   3. Default values                      |
+------------------------------------------+
```

---

### 3. FortiMonitor API Client (`src/fortimonitor/client.py`)

The HTTP client that handles all communication with the FortiMonitor REST API.

```
+--------------------------------------------------+
|           FortiMonitorClient                      |
|--------------------------------------------------|
| - base_url: str                                  |
| - api_key: str                                   |
| - session: requests.Session                      |
| - schema: SchemaManager                          |
|--------------------------------------------------|
| Core:                                            |
|   _request(method, endpoint, params, json_data)  |
|     - Adds api_key to query params               |
|     - Retry loop (3 attempts, exponential)       |
|     - Maps HTTP status -> exceptions             |
|     - Returns parsed JSON dict                   |
|                                                  |
| Server Operations:         (6 methods)           |
|   get_servers()                                  |
|   get_server_details()                           |
|   update_server_status()                         |
|   update_server()                                |
|   ...                                            |
|                                                  |
| Outage Operations:         (5 methods)           |
|   get_outages()                                  |
|   get_active_outages()                           |
|   acknowledge_outage()                           |
|   add_outage_log() / add_outage_note()           |
|   get_outage_details()                           |
|                                                  |
| Maintenance Operations:    (5 methods)           |
|   create_maintenance_schedule()                  |
|   list_maintenance_schedules()                   |
|   get/update/delete_maintenance_schedule()       |
|                                                  |
| Server Group Operations:   (8 methods)           |
|   list/get/create/update/delete_server_group()   |
|   add/remove_servers_from_group()                |
|   get_group_members_complete()                   |
|                                                  |
| Template Operations:       (3 methods)           |
|   list/get_server_template[s]()                  |
|   apply_template_to_server()                     |
|                                                  |
| Notification Operations:   (5 methods)           |
|   list/get_notification_schedule[s]()            |
|   list/get_contact_group[s]()                    |
|   list_contacts() / get_contact_details()        |
|                                                  |
| Agent Resource Operations: (3 methods)           |
|   list_agent_resource_types()                    |
|   get_agent_resource_type_details()              |
|   list_server_agent_resources()                  |
+--------------------------------------------------+
```

**Retry architecture:**

```
Request attempt 1
    |
    +--> Success (2xx) ----> Return parsed JSON
    |
    +--> 500 error --------> Wait 1s --> Attempt 2
    |                                      |
    |                          +--> 500 -> Wait 2s --> Attempt 3
    |                          |                         |
    |                          |             +--> 500 -> Raise APIError
    |                          |             |
    |                          +--> Success  +--> Success
    |
    +--> 401 -----------------> Raise AuthenticationError
    +--> 404 -----------------> Raise NotFoundError
    +--> 429 -----------------> Raise RateLimitError
    +--> 4xx -----------------> Raise APIError
    |
    +--> ConnectionError -----> Wait 1s --> Retry (same pattern)


Additionally: requests.Session has HTTPAdapter with:
  - Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
  This provides a second layer of retry at the transport level.
```

---

### 4. Data Models (`src/fortimonitor/models.py`)

~50 Pydantic models that parse and validate FortiMonitor API responses.

```
Model Hierarchy:
================

PaginationMeta                   (shared across all list responses)

Server  ----+
Outage  ----+--- Core resource models
AgentResource --+

MaintenanceWindow               Scheduling models
ServerGroup                     Organization models
ServerTemplate                  Configuration models

NotificationSchedule  ---+
ContactGroup         ----+---- Alerting models
Contact              ----+

CloudProvider     ---+
CloudCredential  ----+
CloudDiscovery   ----+--- Cloud integration models
CloudRegion      ----+
CloudService     ----+

DEMApplication   ---+
DEMInstance      ----+--- Digital Experience Monitoring models

CompoundService  ---+
AgentResourceThreshold --+--- Service dependency models

NetworkService               Network monitoring models

OutageLog     ---+
OutageAction  ----+--- Outage detail models
OutageNote    ----+

ServerAttribute  ---+
ServerLog       ----+--- Server detail models

*ListResponse wrappers for each (with PaginationMeta)
```

**URL-based ID extraction pattern** (applied to every model):

```
FortiMonitor API returns:
  { "url": "https://api2.panopta.com/v2/server/12345", "name": "prod-web-01", ... }

Pydantic model provides:
  @property
  def id(self) -> Optional[int]:
      parts = self.url.rstrip("/").split("/")
      return int(parts[-1])    # Extracts 12345

This pattern is repeated across ALL resource models:
  Server.id, Outage.id, ServerGroup.id, Contact.id,
  CloudProvider.id, DEMApplication.id, NetworkService.id, etc.
```

**RFC 2822 date parsing** (applied to all datetime fields):

```
API sends:    "Thu, 12 Dec 2024 01:33:48 -0000"   (RFC 2822)
Validator:    @field_validator("created", "updated", mode="before")
              def parse_rfc2822_datetime(cls, v):
                  return parsedate_to_datetime(v)   # email.utils
Result:       datetime(2024, 12, 12, 1, 33, 48, tzinfo=timezone.utc)
```

---

### 5. Schema Manager (`src/fortimonitor/schema.py`)

Runtime API schema discovery with file-based caching.

```
+-------------------------------------------------+
|           SchemaManager                         |
|-------------------------------------------------|
| - api_key, base_url                             |
| - cache_dir: Path (default: cache/schemas/)     |
| - cache_ttl: int  (default: 86400s / 24h)      |
| - _resource_list: List[str]  (in-memory)        |
| - _schemas: Dict[str, Dict]  (in-memory)        |
|-------------------------------------------------|
| get_resource_list() -> List[str]                |
|   Fetch: GET /schema/resources                  |
|   Cache: resource_list.json                     |
|                                                 |
| get_resource_schema(name) -> Dict               |
|   Fetch: GET /schema/resources/{name}           |
|   Cache: {name}_schema.json                     |
|                                                 |
| get_operation_parameters(resource, path, method)|
|   -> List[Dict] of parameter definitions        |
|                                                 |
| validate_parameters(resource, path, method,     |
|                     provided_params)            |
|   -> (is_valid: bool, errors: List[str])        |
|                                                 |
| clear_cache()                                   |
+-------------------------------------------------+

Caching Strategy:
=================
              Request for schema
                     |
                     v
            +--------+--------+
            | In-memory cache? |
            +--------+--------+
              Yes |       | No
                  v       v
            Return    +--------+--------+
                      | File cache      |
                      | valid (< TTL)?  |
                      +--------+--------+
                        Yes |       | No
                            v       v
                      Load file   Fetch from API
                      into mem    -> Save to file
                          |       -> Save to mem
                          v       |
                       Return  <--+
```

---

### 6. Exception Hierarchy (`src/fortimonitor/exceptions.py`)

Custom exceptions for granular error handling:

```
FortiMonitorError (base)
    |
    +-- AuthenticationError      HTTP 401
    |
    +-- APIError                 HTTP 4xx/5xx (generic)
    |     |
    |     +-- NotFoundError      HTTP 404
    |     |
    |     +-- RateLimitError     HTTP 429
    |
    +-- ValidationError          Invalid request parameters
    |
    +-- SchemaError              Schema fetch/parse failures
```

---

### 7. Tool Modules (`src/tools/`)

The largest part of the codebase — 33 Python files containing 241 tool definitions and their async handler functions.

```
src/tools/
|
+-- Phase 1: Core Monitoring (Tuple Pattern) -------- 44 tools
|   |
|   +-- servers.py ................. 2 tools   (list, detail)
|   +-- outages.py ................. 2 tools   (list, health check)
|   +-- metrics.py ................. 1 tool    (server metrics)
|   +-- outage_management.py ....... 3 tools   (acknowledge, note, detail)
|   +-- server_management.py ....... 3 tools   (status, maintenance CRUD)
|   +-- bulk_operations.py ......... 5 tools   (bulk ack, tags, search)
|   +-- server_groups.py ........... 8 tools   (group CRUD, network svc)
|   +-- templates.py ............... 4 tools   (list, detail, apply x2)
|   +-- notifications.py ........... 5 tools   (schedules, contacts)
|   +-- agent_resources.py ......... 4 tools   (types, server resources)
|   +-- reporting.py ............... 7 tools   (health, stats, exports)
|
+-- Phase 1 Enhanced (Dict Pattern) ----------------- 49 tools
|   |
|   +-- outage_enhanced.py ........ 13 tools   (broadcast, escalate, delay, ...)
|   +-- server_enhanced.py ........ 19 tools   (CRUD, attributes, logs, DNS, ...)
|   +-- maintenance_enhanced.py .... 9 tools   (update, extend, pause, ...)
|   +-- server_groups_enhanced.py .. 4 tools   (members, policy, ...)
|   +-- templates_enhanced.py ...... 4 tools   (create, update, delete, ...)
|
+-- Phase 2: Extended Monitoring (Dict Pattern) ------ 36 tools
|   |
|   +-- cloud.py .................. 15 tools   (providers, creds, discovery, ...)
|   +-- dem.py .................... 10 tools   (DEM apps, instances, ...)
|   +-- compound_services.py ...... 11 tools   (service deps, thresholds, ...)
|
+-- Phase 3: Platform Management (Dict Pattern) ------ 67 tools
|   |
|   +-- dashboards.py .............. 5 tools   (dashboard CRUD)
|   +-- status_pages.py ............ 5 tools   (status page CRUD)
|   +-- rotating_contacts.py ....... 6 tools   (on-call rotations)
|   +-- contacts_enhanced.py ...... 12 tools   (contact CRUD, info, groups)
|   +-- notifications_enhanced.py .. 8 tools   (schedule CRUD, sub-resources)
|   +-- network_services.py ........ 5 tools   (server network svc CRUD)
|   +-- monitoring_nodes.py ........ 2 tools   (list, detail)
|   +-- network_service_types.py ... 2 tools   (list, detail)
|   +-- snmp.py ................... 12 tools   (credentials, discovery, resources)
|   +-- fabric.py .................. 4 tools   (fabric connection CRUD)
|   +-- countermeasures.py ........ 20 tools   (countermeasures, thresholds, ...)
|
+-- Phase 4: Administration (Dict Pattern) ----------- 31 tools
    |
    +-- users.py ................... 6 tools   (user CRUD, addons)
    +-- reference_data.py ......... 13 tools   (account history, types, roles, ...)
    +-- onsight.py ................ 12 tools   (OnSight CRUD, groups, ...)

                                         TOTAL: 241 tools
```

**Tool handler anatomy** (every handler follows this pattern):

```python
async def handle_tool_name(arguments: dict, client: FortiMonitorClient) -> List[TextContent]:
    """
    1. Extract and validate arguments
    2. Call client method(s)
    3. Format response as human-readable text
    4. Return [TextContent(type="text", text=formatted_result)]
    """
```

---

### 8. Docker Infrastructure

```
+---------------------------------------------------------------------+
|  Docker Multi-Stage Build                                           |
|                                                                     |
|  Stage 1: builder (python:3.11-slim)                                |
|    - Install gcc build tools                                        |
|    - Filter dev dependencies (pytest, black, etc.)                  |
|    - pip install --user production deps only                        |
|                                                                     |
|  Stage 2: runtime (python:3.11-slim)                                |
|    - ca-certificates only                                           |
|    - Non-root user: mcpuser (UID 1000)                              |
|    - Copy Python packages from builder                              |
|    - Copy application source                                        |
|    - Healthcheck: verify config loads                               |
|    - CMD: tail -f /dev/null (keep-alive)                            |
+---------------------------------------------------------------------+

Docker Compose Configuration:
+---------------------------------------------------------------------+
|  Service: fortimonitor-mcp                                          |
|    - Named volume: fortimonitor-cache -> /app/cache                 |
|    - Resource limits: 1 CPU, 512MB RAM                              |
|    - Resource reservations: 0.25 CPU, 128MB RAM                     |
|    - Restart: unless-stopped                                        |
|    - Security: no-new-privileges                                    |
|    - Logging: json-file, 10MB max, 3 files rotation                 |
|    - Health check: every 60s, 10s timeout                           |
|    - stdin_open: true (for MCP stdio protocol)                      |
+---------------------------------------------------------------------+

Invocation Pattern:
  Claude Desktop config -> docker exec -i fortimonitor-mcp python -m src.server
  (Container stays alive; MCP server invoked on-demand per session)
```

---

## Tool Registry Architecture

The registry unifies two registration patterns into a single dispatch table:

```
                 _build_registry()
                       |
          +------------+------------+
          |                         |
    Tuple Pattern              Dict Pattern
  (11 original modules)     (22 enhanced modules)
          |                         |
  For each (defn_func,       For each {name: defn_func},
            handler_func):          {name: handler_func}:
    tool = defn_func()         tool = defn_func()
    map[tool.name] = handler   map[name] = handler
          |                         |
          +------------+------------+
                       |
                       v
         +----------------------------+
         | _TOOL_DEFINITIONS (241)    |  List[Tool]
         | _HANDLER_MAP     (241)    |  Dict[str, Callable]
         +----------------------------+
                       |
                       v
            @server.call_tool()
              handler = _HANDLER_MAP.get(name)
              return await handler(arguments, client)
```

---

## Complete Tool Inventory

| Category | Module | Count | Key Operations |
|----------|--------|------:|----------------|
| **Servers** | servers, server_enhanced | 21 | List, detail, CRUD, attributes, logs, DNS, path monitoring |
| **Outages** | outages, outage_management, outage_enhanced | 18 | List, detail, acknowledge, escalate, broadcast, delay, history |
| **Maintenance** | server_management, maintenance_enhanced | 12 | Create, update, extend, pause, list active/pending |
| **Server Groups** | server_groups, server_groups_enhanced | 12 | CRUD, member management, policy, compound services |
| **Templates** | templates, templates_enhanced | 8 | List, detail, create, update, delete, apply, reapply |
| **Notifications** | notifications, notifications_enhanced | 13 | Schedule CRUD, sub-resource queries |
| **Contacts** | contacts_enhanced, rotating_contacts | 18 | Contact CRUD, contact_info, on-call rotations |
| **Agent Resources** | agent_resources | 4 | Types, server resources, details |
| **Metrics & Reporting** | metrics, reporting | 8 | Server metrics, health summary, stats, exports, availability |
| **Cloud** | cloud | 15 | Providers, credentials, discovery, regions, services |
| **DEM** | dem | 10 | Applications, instances, locations, path monitoring |
| **Compound Services** | compound_services | 11 | CRUD, thresholds, availability |
| **Dashboards** | dashboards | 5 | Dashboard CRUD |
| **Status Pages** | status_pages | 5 | Status page CRUD |
| **Network Services** | network_services, network_service_types | 7 | Server network service CRUD, types |
| **Monitoring Nodes** | monitoring_nodes | 2 | List, detail |
| **SNMP** | snmp | 12 | Credentials, discovery, resources |
| **OnSight** | onsight | 12 | OnSight CRUD, groups, countermeasures |
| **Fabric** | fabric | 4 | Fabric connection CRUD |
| **Countermeasures** | countermeasures | 20 | Countermeasures, thresholds, metadata, output |
| **Users** | users | 6 | User CRUD, addons |
| **Reference Data** | reference_data | 13 | Account history, contact types, roles, timezones, server attribute types |
| **Bulk Operations** | bulk_operations | 5 | Bulk acknowledge, tag add/remove, advanced search |
| | | **241** | |

---

## Novel Features

These are capabilities newly provided by this project that did not previously exist:

### 1. Conversational Infrastructure Monitoring
No prior tool allowed an operator to ask, in plain English, something like *"Show me the top 5 servers by outage count this month, then create a maintenance window for the worst one."* This project makes the entire FortiMonitor API surface available through natural language.

### 2. Transparent URL-ID Abstraction
FortiMonitor's API returns resource identifiers as full URL strings (e.g., `https://api2.panopta.com/v2/server/123`). This project transparently extracts integer IDs via `@property` methods on every model, so users and tool handlers work with simple numbers while the client constructs URLs automatically.

### 3. RFC 2822 Date Normalization
The FortiMonitor API uses RFC 2822 date format (e.g., `"Thu, 12 Dec 2024 01:33:48 -0000"`) which is uncommon in modern REST APIs. The project's Pydantic validators automatically parse these into standard Python `datetime` objects, normalizing them for consistent display and comparison.

### 4. Runtime API Schema Discovery
The `SchemaManager` fetches live schema definitions from FortiMonitor's `/schema/resources` endpoint and caches them locally. This enables parameter validation against the actual API contract at runtime, rather than relying on hardcoded assumptions.

### 5. Dual-Layer Retry with Exponential Backoff
The client implements two independent retry mechanisms:
- **Application-level**: Custom retry loop in `_request()` with exponential backoff (1s, 2s, 4s) for 500 errors and connection failures.
- **Transport-level**: `requests.HTTPAdapter` with `urllib3.Retry` for 429/5xx status codes.

### 6. Keep-Alive Container Pattern
Rather than running the MCP server as the container's main process (which would exit after each session), the Dockerfile uses `tail -f /dev/null` to keep the container alive as a persistent sidecar. The MCP server is invoked on-demand via `docker exec`, enabling instant session startup without container restart overhead.

### 7. Complete API Coverage in a Single MCP Server
With 241 tools across 33 modules, this is a comprehensive MCP implementation that covers virtually 100% of the FortiMonitor v2 API surface. Most MCP servers expose a handful of tools; this project demonstrates that a single server can scale to expose an entire enterprise API platform.

### 8. Composite Operations
Several tools compose multiple API calls into higher-level operations:
- `get_servers_with_active_outages` correlates outages with server details in a single tool call.
- `get_group_members_complete` fetches group details, member servers, and their network services, combining 3+ API calls.
- `generate_availability_report` and reporting tools aggregate data across multiple endpoints.

---

## Security & Resilience Design

```
+------------------------------------------------------------------+
|                     SECURITY LAYERS                              |
|                                                                  |
|  Container Level:                                                |
|    +-- Non-root user (mcpuser, UID 1000)                         |
|    +-- no-new-privileges security option                         |
|    +-- Resource limits (1 CPU, 512MB RAM)                        |
|    +-- JSON file logging with rotation (10MB x 3)                |
|                                                                  |
|  Network Level:                                                  |
|    +-- HTTPS only (API communication)                            |
|    +-- API key passed as query parameter (per FortiMonitor spec) |
|    +-- No ports exposed by container                             |
|    +-- stdio transport only (no HTTP server)                     |
|                                                                  |
|  Application Level:                                              |
|    +-- Pydantic validation on all inputs/outputs                 |
|    +-- Custom exception hierarchy with status code mapping       |
|    +-- Rate limiting configuration (100 req/60s default)         |
|    +-- Structured logging for audit trail                        |
|                                                                  |
|  Resilience:                                                     |
|    +-- Dual-layer retry (application + transport)                |
|    +-- Exponential backoff (1s, 2s, 4s)                          |
|    +-- 30s request timeout                                       |
|    +-- Graceful shutdown (client.close() in finally block)       |
|    +-- Health checks (every 60s)                                 |
|    +-- Schema cache with configurable TTL                        |
+------------------------------------------------------------------+
```

---

## Deployment Architecture

```
Deployment Option A: Docker (Recommended)
==========================================

  +------------------+          docker exec -i          +------------------+
  |  Claude Desktop  | ----(stdin/stdout via MCP)-----> |  fortimonitor-   |
  |                  |                                  |  mcp container   |
  +------------------+                                  +--------+---------+
                                                                 |
     claude_desktop_config.json:                                 |
     {                                                   HTTPS   |
       "mcpServers": {                                           |
         "fortimonitor": {                                       v
           "command": "docker",                         +------------------+
           "args": ["exec", "-i",                       |  FortiMonitor    |
                    "fortimonitor-mcp",                 |  Cloud API       |
                    "python", "-m",                     +------------------+
                    "src.server"]
         }
       }
     }


Deployment Option B: Local Python
===================================

  +------------------+          stdin/stdout            +------------------+
  |  Claude Desktop  | ----(direct process)-----------> |  python -m       |
  |                  |                                  |  src.server      |
  +------------------+                                  +--------+---------+
                                                                 |
     claude_desktop_config.json:                         HTTPS   |
     {                                                           |
       "mcpServers": {                                           v
         "fortimonitor": {                              +------------------+
           "command": "python",                         |  FortiMonitor    |
           "args": ["-m", "src.server"],                |  Cloud API       |
           "cwd": "/path/to/project",                   +------------------+
           "env": { "FORTIMONITOR_API_KEY": "..." }
         }
       }
     }
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Runtime** | Python 3.9+ | Primary language |
| **MCP Protocol** | mcp >= 0.9.0 | Claude AI integration via Model Context Protocol |
| **Data Validation** | Pydantic >= 2.5.0, pydantic-settings >= 2.1.0 | Request/response models, environment config |
| **HTTP Client** | requests >= 2.31.0, httpx >= 0.25.0 | FortiMonitor API communication |
| **Date Parsing** | python-dateutil >= 2.8.2 | RFC 2822 datetime handling |
| **Logging** | structlog >= 23.2.0 | Structured logging |
| **Environment** | python-dotenv >= 1.0.0 | `.env` file loading |
| **Containerization** | Docker (python:3.11-slim), Docker Compose | Production deployment |
| **CI/CD** | GitHub Actions | Multi-arch builds to Docker Hub and GHCR |
| **Testing** | pytest, pytest-asyncio, pytest-cov | Unit and integration tests |
| **Quality** | black, flake8, mypy | Formatting, linting, type checking |

---

*Document generated for the FortiMonitor MCP Server project, v0.1.0 (Alpha).*
