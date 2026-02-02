# FortiMonitor MCP Phase 1 - Revision Summary

## What Changed and Why

This document summarizes the key differences between the original Phase 1 implementation plan and the revised version based on actual FortiMonitor/Panopta API documentation.

---

## Critical API Endpoint Corrections

### Original (Incorrect) → Revised (Correct)

| Operation | Original Endpoint | Actual Endpoint |
|-----------|------------------|-----------------|
| List servers | `/servers` | `/server` |
| Server details | `/servers/{id}` | `/server/{server_id}` |
| List alerts | `/alerts` | `/outage` |
| Active alerts | N/A | `/outage/active` |
| Server metrics | `/servers/{id}/metrics` | `/server/{server_id}/agent_resource` |

---

## New Components Added

### 1. Schema Discovery System (`schema.py`)

**Why**: FortiMonitor provides runtime API schema documentation at:
- `/schema/resources` - Lists all 33 available resources
- `/schema/resources/{resource_name}` - Gets detailed schema for each resource

**Benefits**:
- Runtime validation of API requests
- Self-documenting API operations
- Parameter requirement checking
- Automatic schema caching (24-hour TTL)

**Usage**:
```python
client = FortiMonitorClient()
# Schema manager is automatically initialized
resources = client.schema.get_resource_list()  # Get all available resources
schema = client.schema.get_resource_schema('server')  # Get server schema
```

### 2. Enhanced Data Models

**New Response Models**:
- `ServerListResponse` - Includes pagination metadata
- `OutageListResponse` - Structured outage responses
- `PaginatedResponse` - Base class for paginated responses

**Pagination Structure**:
```python
{
    "server_list": [...],  # Not "servers"!
    "limit": 50,
    "offset": 0,
    "total_count": 76,
    "next": "https://api2.panopta.com/v2/server?limit=50&offset=50"
}
```

---

## API Parameter Corrections

### Server List (`/server`)

**Original (Generic)**:
```python
params = {
    "limit": 100,
    "offset": 0,
    "group_id": group_id,
    "status": status
}
```

**Revised (Actual API)**:
```python
params = {
    "limit": 50,  # Default is 50, not 100
    "offset": 0,
    "tag_filter_mode": "or",  # Required when using tags
    "attribute_filter_mode": "or",  # Required when using attributes
    "name": name,  # Partial match supported
    "fqdn": fqdn,
    "server_group": server_group_id,  # Not "group_id"
    "status": status,
    "tags": "tag1,tag2",  # Comma-separated, not array
    "full": "true"  # String boolean, not Python bool
}
```

### Outages (`/outage`)

**Original**:
```python
params = {
    "server_id": server_id,
    "severity": severity,
    "acknowledged": True  # Boolean
}
```

**Revised**:
```python
params = {
    "server": server_id,  # Not "server_id"!
    "severity": severity,
    "status": "active",  # or "resolved"
    "start_time": "2026-01-30 10:00:00",  # Specific format
    "end_time": "2026-01-30 18:00:00"
}
```

**New Endpoint**: `/outage/active` - Dedicated endpoint for active outages only

---

## Authentication Changes

### Original
```python
headers = {
    "Authorization": f"Bearer {api_key}"
}
```

### Revised
```python
# API key passed as query parameter, not header
params = {
    "api_key": api_key,
    # ... other params
}
```

---

## Tool Naming Changes

### Tool Renamings

| Original | Revised | Reason |
|----------|---------|--------|
| `get_alerts` | `get_outages` | Matches actual API terminology |
| `get_metrics` | `get_server_metrics` | More descriptive, matches API structure |

### New Tool Parameters

**get_servers**:
- Added: `fqdn`, `tags`, `tag_filter_mode`
- Changed: `group_id` → `server_group`

**get_outages**:
- Added: `active_only` (uses `/outage/active` endpoint)
- Changed: Default `limit` from 100 to 50
- Changed: Time parameters use specific format

**get_server_metrics**:
- Returns list of agent resources, not time-series data
- Each resource shows current value and metadata

---

## Response Structure Changes

### Server List Response

**Original Expected**:
```json
{
  "servers": [...]
}
```

**Actual**:
```json
{
  "server_list": [...],
  "limit": 50,
  "offset": 0,
  "total_count": 76,
  "next": "https://..."
}
```

### Outage List Response

**Original Expected**:
```json
{
  "alerts": [...]
}
```

**Actual**:
```json
{
  "outage_list": [...],
  "limit": 50,
  "offset": 0,
  "total_count": 15
}
```

### Agent Resource Response

**Actual Structure**:
```json
{
  "agent_resource_list": [
    {
      "id": 123,
      "name": "CPU Usage",
      "resource_type": "cpu",
      "current_value": 45.2,
      "unit": "%",
      "last_check": "2026-01-30T15:30:00Z"
    }
  ]
}
```

---

## Configuration Updates

### New Environment Variables

```bash
# Schema Caching
ENABLE_SCHEMA_CACHE=true
SCHEMA_CACHE_DIR=cache/schemas
SCHEMA_CACHE_TTL=86400  # 24 hours
```

### Directory Structure Addition

```
fortimonitor-mcp-server/
├── cache/
│   └── schemas/              # NEW: Cached API schemas
│       ├── resource_list.json
│       ├── server_schema.json
│       ├── outage_schema.json
│       └── ...
```

---

## Error Handling Improvements

### Schema-Aware Validation

**Before**:
```python
# Just send request and hope for the best
response = client._request("GET", "/servers", params=params)
```

**After**:
```python
# Validate parameters against schema before sending
is_valid, errors = client.schema.validate_parameters(
    'server', '/server', 'GET', params
)
if not is_valid:
    raise ValidationError(f"Invalid parameters: {errors}")
```

### Better Error Messages

**Before**:
```
Error: 400 Bad Request
```

**After**:
```
Error: Missing required parameter: start_time
Expected format: YYYY-MM-DD HH:MM:SS
See /schema/resources/account_history for details
```

---

## Testing Updates

### New Test Script

`test_connectivity.py` now tests:
1. ✓ Server list endpoint (`/server`)
2. ✓ Server details endpoint (`/server/{id}`)
3. ✓ Active outages endpoint (`/outage/active`)
4. ✓ Schema discovery (`/schema/resources`)
5. ✓ Pagination handling

### Expected Test Output

```
Testing FortiMonitor API connectivity...
✓ Client initialized
✓ Server list endpoint works! Found 5 servers
  Total count: 76
  Pagination: limit=5, offset=0

✓ First server: production-web-01 (ID: 12345)
✓ Server details endpoint works for server production-web-01

✓ Active outages endpoint works! Found 3 active outages

✓ Schema discovery works! Found 33 resources
  Sample resources: server, outage, server_group, user, contact

✅ All connectivity tests passed!
```

---

## Migration Guide for Existing Code

If you already implemented the original plan, here's what to change:

### 1. Update Client Endpoints

```python
# OLD
response = self._request("GET", "/servers", params=params)

# NEW
response = self._request("GET", "/server", params=params)
```

### 2. Update Response Parsing

```python
# OLD
servers = response.get("servers", [])

# NEW
servers = response.get("server_list", [])
```

### 3. Update Parameter Names

```python
# OLD
params = {"group_id": 123, "server_id": 456}

# NEW
params = {"server_group": 123, "server": 456}
```

### 4. Add API Key to Query Params

```python
# OLD
self.session.headers.update({
    "Authorization": f"Bearer {self.api_key}"
})

# NEW
params["api_key"] = self.api_key
```

### 5. Initialize Schema Manager

```python
# Add to __init__
from .schema import SchemaManager

class FortiMonitorClient:
    def __init__(self, ...):
        # ... existing code ...
        self.schema = SchemaManager(self.api_key, self.base_url)
```

---

## Benefits of Revised Implementation

### 1. Accuracy
✅ Uses actual FortiMonitor API endpoints and parameters
✅ Response parsing matches actual API structure
✅ No more 404 errors from incorrect endpoints

### 2. Robustness
✅ Schema validation prevents invalid requests
✅ Better error messages with specific requirements
✅ Automatic schema caching reduces API calls

### 3. Maintainability
✅ Self-documenting through schema discovery
✅ Easy to add new endpoints (schema provides structure)
✅ Runtime validation catches issues early

### 4. Future-Proof
✅ Schema discovery means API changes are automatically detected
✅ Cached schemas can be updated on demand
✅ Parameter requirements are always current

---

## Quick Reference

### Key Files Changed

| File | Original Size | Revised Size | Key Changes |
|------|--------------|--------------|-------------|
| `client.py` | ~250 lines | ~400 lines | +Schema integration, correct endpoints |
| `models.py` | ~100 lines | ~150 lines | +Pagination models, correct field names |
| `exceptions.py` | ~40 lines | ~50 lines | +SchemaError |
| NEW: `schema.py` | N/A | ~250 lines | Complete schema discovery system |

### Key Concepts to Remember

1. **Endpoint names are singular**: `/server`, not `/servers`
2. **Response arrays have `_list` suffix**: `server_list`, not `servers`
3. **API key goes in query params**: `?api_key=...`, not header
4. **Filter modes are required**: `tag_filter_mode=or` when using tags
5. **Booleans are strings**: `full=true`, not `full=True`
6. **Time format is specific**: `YYYY-MM-DD HH:MM:SS`

---

## What Stays the Same

✅ Project structure (directories and organization)
✅ MCP protocol implementation
✅ Tool handler patterns
✅ Configuration management approach
✅ Logging and error handling strategy
✅ Testing methodology
✅ Claude Desktop integration method

---

## Questions?

If you encounter issues with the revised implementation:

1. **Test connectivity first**: Run `test_connectivity.py`
2. **Check schema cache**: Look in `cache/schemas/` for downloaded schemas
3. **Enable DEBUG logging**: Set `LOG_LEVEL=DEBUG` in `.env`
4. **Review actual API responses**: Check logs for raw JSON
5. **Consult schema docs**: Look at cached schema files for parameter details

---

**Document Version**: 1.0  
**Corresponds to**: Phase 1 Implementation Guide v2.0 (REVISED)  
**Date**: January 2026
