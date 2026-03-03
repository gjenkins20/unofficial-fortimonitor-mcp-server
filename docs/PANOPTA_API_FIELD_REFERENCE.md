# Panopta API Field & Behavior Reference

Real-world findings from testing against multiple FortiMonitor instances, including both direct-managed and Fabric-managed deployments. The Fabric-managed instance (184 fabric connections, 0 direct servers, 10 users, 266 maintenance windows, 500+ outages) exposed most of these edge cases due to its high volume and different API behavior.

> **Note:** The MCP server codebase already handles all of these correctly. This document serves as reference for anyone building against the Panopta v2 API.

---

## 1. Outage Object — Field Mapping

The outage object returned by `/outage` does **not** contain an `id` field. Several other assumed fields are also absent or behave differently than expected.

### Actual Fields

```
acknowledged, compound_service, compound_service_id, compound_service_name,
description, end_time, exclude_from_availability, has_active_maintenance,
hash, metadata, metric_tags, network_service_type_list, next_action,
server, server_fqdn, server_group_id, server_group_name, server_id,
server_name, severity, start_time, status, summary, tags, type, url
```

### Field Corrections

| Assumed Field | Actual Field | Notes |
|---|---|---|
| `id` | **Does not exist** | Extract from `url`: `https://api2.panopta.com/v2/outage/2659350711` → `2659350711` |
| `hash` | Exists | Short alphanumeric ID (e.g., `cneYwxTMVD9y2NE`). Alternate identifier |
| `active` (boolean) | **Does not exist** | Use `status` field instead |
| `status` | Exists | Values: `"active"`, `"resolved"` |
| `acknowledged` | **Not a boolean** | `None` when unacknowledged. A **full user object (dict)** when acknowledged, containing `display_name`, `url`, `contact_info`, `roles`, etc. |
| `resolved` | **Does not exist** | Use `end_time` (present when resolved, `None` when active) |
| `end` | **Does not exist** | Use `end_time` |
| `start` | **Does not exist** | Use `start_time` |
| `severity` | Exists | Values: `"critical"`, `"warning"`, `"info"` |
| `server_name` | Exists | Direct string, not nested |
| `server` | Exists | URL reference: `https://api2.panopta.com/v2/server/40896864` |

### How This Codebase Handles It

- **ID extraction:** `models.py` — `Outage.id` `@property` parses the `url` field
- **Acknowledged:** `@field_validator("acknowledged")` converts dict/None → bool
- **DateTime fields:** Model uses `start_time` and `end_time` directly

---

## 2. Active Outage Filtering — `?active_only=true` Unreliable

The `/outage?active_only=true` query parameter does **not work** on all instances. On at least one Fabric-managed instance, it returns the exact same result set as `/outage` (both returned 500 records with identical content).

### Recommended Approach

Use a separate endpoint (`/outage/active`) rather than a query parameter. If that's unavailable, always filter locally by `status == "active"`.

### Why Scanning May Be Needed

Outages are returned newest-first. Active outages that started weeks or months ago can be buried thousands of records deep. A simple 50- or 500-record cap will miss them.

### How This Codebase Handles It

- `client.py` switches to the `/outage/active` endpoint when `active_only=True`
- Same pattern for maintenance windows: `/maintenance_schedule/active`

---

## 3. Pagination — Silent Page Size Caps

Some endpoints silently cap page size at **50 results**, regardless of the `limit` parameter sent.

### Example

```
Request:  GET /outage?limit=200&offset=0
Response: 50 results  ← API silently capped at 50

Naive logic: 50 < 200 → "must be the last page" → WRONG
```

### Recommended Approach

Detect actual page size from the first response, or use the pagination metadata (`total_count`, `next` URL) returned by the API.

### Confirmed Affected Endpoints

- `/outage` — Caps at 50 per page
- `/maintenance_schedule` — Caps at 50 per page

### How This Codebase Handles It

- `PaginationMeta` model captures `total_count`, `next`, `previous` from API responses
- Tool handlers use `total_count` and `next` URL, never `len(results) < limit`

---

## 4. Server Group — No Member Information in List Response

The `/server_group` list endpoint returns **no member count or server list information**.

### Actual Fields from List Endpoint

```
location, name, notification_schedule, override_location,
server_group, tags, url
```

### Key Field Notes

| Field | Purpose |
|---|---|
| `server_group` | **Parent group** URL reference (e.g., `.../server_group/630117`). NOT a list of child groups. `null` for top-level groups |
| `notification_schedule` | URL reference to assigned schedule, or `null` |
| `url` | This group's own URL (contains group ID) |

### What's NOT Present

- `server_list`, `server_count`, `member_count`, `child_groups`, `compound_service_list`, `server_template`, `monitoring_policy`

### To Get Member Info

Must call per-group: `GET /server_group/{group_id}/server`

### How This Codebase Handles It

- `ServerGroup.server_count` is a `@property` calculated from the `servers` list, not an expected API field

---

## 5. Maintenance Window — Status Field and Filter Issues

Maintenance windows have a `status` field that includes `"deleted"` (not just `"active"` / `"completed"`). The `?active_only=true` filter does not work on all instances.

### Actual Fields

```
current_end_time, current_start_time, description, disrupt_active_outages,
duration, exclude_from_availability, limited_metrics, monitoring, name,
next_start_time, notification_schedule, original_end_time, original_start_time,
pause_all_checks, recurrence_description, recurrence_interval, recurrence_type,
show_in_public_report, status, tag_match, tags, targets, url, weekdays
```

### Status Values Observed

- `"deleted"` — Expired/removed windows (majority of records)
- `"active"` — Currently in-progress
- `"scheduled"` — Upcoming

### Key Insight

One instance had **266 total maintenance windows** but most had `status: "deleted"`. Without status filtering, reports showed 266 as the active count — severely misleading.

### How This Codebase Handles It

- Uses endpoint switching (`/maintenance_schedule/active` vs `/maintenance_schedule`) rather than relying on query parameter filtering

---

## 6. Fabric-Managed Instance Behavior

When FortiMonitor is deployed in Fabric-managed mode (devices discovered via FortiGate integrations), the `/server` endpoint may **timeout** or return 0 results.

### Detection

```python
servers = api.get("/server")            # Returns 0 or timeout
fabric = api.get("/fabric_connection")  # Returns 184

if len(servers) == 0 and len(fabric) > 0:
    deployment_model = "Fabric-Managed"
```

### Implications

- Server-centric tools may return empty results
- Monitoring is done through fabric connections and OnSight agents
- Server groups exist and contain devices via fabric discovery, not direct registration
- The `/server` timeout is expected behavior, not an error

### How This Codebase Handles It

- 30-second timeout with exponential backoff retry on all requests
- Dedicated fabric tools exist in `src/tools/fabric.py`

---

## 7. User Object — Contact Info Structure

The `contact_info` field on user objects is a **list of contact method objects**, not a simple count or string.

### Example

```json
{
  "display_name": "Travis.VanFleet",
  "username": "Travis.VanFleet@ledcor.com",
  "contact_info": [
    {
      "detail": "Travis.VanFleet@ledcor.com",
      "type": "https://api2.panopta.com/v2/contact_type/61",
      "url": "https://api2.panopta.com/v2/contact/567052/contact_info/541983"
    }
  ],
  "roles": ["https://api2.panopta.com/v2/role/668"],
  "created": "Mon, 28 Apr 2025 16:18:52 -0000",
  "url": "https://api2.panopta.com/v2/user/320336"
}
```

This same structure appears inside the outage `acknowledged` field when an outage has been acknowledged.

### How This Codebase Handles It

- Contact info fetched from separate endpoint (`contact/{id}/contact_info`) with defensive `.get()` patterns

---

## 8. URL References as IDs — Universal Pattern

Many Panopta API objects use `url` fields instead of `id` fields. The ID must be extracted from the URL.

### Pattern

```python
def extract_id(url: str) -> str:
    """Extract numeric ID from a Panopta API URL reference."""
    if url and "/" in url:
        return url.rstrip("/").split("/")[-1]
    return ""
```

### Examples

```
https://api2.panopta.com/v2/outage/2659350711           → 2659350711
https://api2.panopta.com/v2/server/40896864              → 40896864
https://api2.panopta.com/v2/server_group/628195          → 628195
https://api2.panopta.com/v2/maintenance_schedule/2445628 → 2445628
```

### Affected Objects

Outages, Servers, Server Groups, Maintenance Windows, Users, Notification Schedules, Contact Types

### How This Codebase Handles It

- Consistent `@property def id()` pattern across all Pydantic models in `models.py`

---

## Quick Reference — Fix Priority for New Implementations

### Critical (Incorrect Data)

1. **Outage active detection** — Use `status == "active"`, not an `active` boolean
2. **Outage ID extraction** — Parse from `url` field; no `id` field exists
3. **Acknowledged field** — Is a user object dict, not boolean
4. **Pagination** — Detect actual page size; don't assume `limit` is honored

### High (Data Gaps)

5. **Active outage filtering** — `?active_only=true` unreliable; use `/outage/active` endpoint or filter locally
6. **Maintenance window status** — Filter by `status` field; `?active_only=true` unreliable
7. **Server group members** — List endpoint has no member info; requires per-group API call

### Medium (Edge Cases)

8. **Fabric-managed instances** — `/server` may timeout; use `/fabric_connection` as alternative
9. **URL-based ID extraction** — Universal pattern across all object types

---

## Test Matrix

| Test | Direct Instance | Fabric-Managed Instance |
|---|---|---|
| `/outage` returns `id` field | Verify | Not present |
| `/outage?active_only=true` works | Verify | Returns all outages |
| `/server` returns results | Expected | Timeout / empty |
| `/server_group` has member info | Verify | No member fields |
| `/maintenance_schedule?active_only=true` works | Verify | Returns all windows |
| Pagination respects `limit` param | Verify | Silently caps at 50 |

---

## 9. SNMP Resource PUT — Undocumented Payload Constraints

The `PUT /server/{id}/snmp_resource/{id}` endpoint has strict undocumented requirements. Sending a partial payload (e.g., only `name` or only `tags`) returns HTTP 500. These findings were discovered during development of the SNMP Resource Tag Applier CLI.

### 9.1 Template URL References Cause 500

Including `template` or `template_snmp_resource` fields in the PUT body causes a 500 error. These are URL references (e.g., `https://api2.panopta.com/v2/server_template/...`) that the API cannot process in a write context.

**Solution:** Always strip template-related fields from the PUT payload.

### 9.2 Required Non-Null Fields: `version` and `community`

For resources inherited from a server template, the GET response may return `null` for `version` and `community`. However, the PUT endpoint requires these to be non-null strings.

**Solution:** Default `version` to `"2c"` and `community` to `"public"` when the GET response returns null.

### 9.3 Read-Only Fields Cause 500

Including any of these fields in the PUT body causes a 500 error:

| Field | Why |
|---|---|
| `formatted_name` | Server-generated display name |
| `template` | URL reference to parent template |
| `template_snmp_resource` | URL reference to template resource |
| `id` / `url` / `resource_url` / `server_url` | Object identity fields |
| `status` | Server-managed state |
| `thresholds` | Managed via separate endpoint |

### 9.4 Tags-Only Payload Causes 500

Sending `{"tags": ["my-tag"]}` without the core required fields causes a 500 error. The API requires `name`, `frequency`, `type`, and `base_oid` in every PUT request.

**Solution:** Always perform a pre-flight GET to capture current field values, then merge any changes into a complete payload.

### 9.5 Null Fields Trigger Validation Errors

If the GET response contains null values for optional fields (e.g., `port`, `server_interface`), echoing those nulls back in the PUT body may trigger validation errors.

**Solution:** Only include optional fields in the PUT payload when they have non-null values.

### 9.6 Tag Data Type Inconsistency

The API may return tags as either a JSON array `["tag1", "tag2"]` or a comma-separated string `"tag1,tag2"`. Both formats have been observed across different resources and API versions.

**Solution:** Normalize tags on read — handle both list and comma-separated string formats.

### Safe PUT Payload Template

The correct pattern for updating an SNMP resource:

```
1. GET current state
2. Build payload with REQUIRED fields from GET: name, frequency, type, base_oid
3. Default version ("2c") and community ("public") if null
4. Include OPTIONAL fields only if non-null: port, server_interface, user, auth_*, enc_*
5. Merge tags (set union, no duplicates)
6. Apply user overrides on top
7. NEVER include: template, template_snmp_resource, formatted_name, id, url, status, thresholds
8. PUT the complete payload
```

### How This Codebase Handles It

- `src/tools/snmp.py` — `_build_safe_snmp_resource_put_payload()` implements the safe payload pattern
- `_normalize_tags()` handles both list and comma-separated string formats
- `_SNMP_RESOURCE_READONLY_FIELDS` constant lists all fields to exclude from PUT payloads
- Pre-flight GET is performed before every PUT in `handle_update_snmp_resource` and `handle_bulk_tag_snmp_resources`

---

*Source: Field testing against production FortiMonitor instances, February–March 2026*
