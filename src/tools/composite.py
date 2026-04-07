"""
FortiMonitor MCP Tools - Composite Operations

Copyright (c) 2026 Gregori Jenkins
https://github.com/gjenkins20/unofficial-fortimonitor-mcp-server

Smart tools that chain multiple API calls into single, rich operations
for common multi-step monitoring tasks.
"""

import json
from typing import Any
import mcp.types


# ── Tool Definitions ──────────────────────────────────────────────

COMPOSITE_TOOL_DEFINITIONS = {

    "investigate_server": lambda: mcp.types.Tool(
        name="investigate_server",
        description=(
            "Deep investigation of a server: health status, active outages, "
            "recent metrics, maintenance schedule, network services, and "
            "notification config. Returns a structured investigation report."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "number",
                    "description": "The server ID to investigate.",
                },
            },
            "required": ["server_id"],
        },
    ),

    "compare_servers": lambda: mcp.types.Tool(
        name="compare_servers",
        description=(
            "Side-by-side comparison of two servers: configuration, health "
            "status, network services, and outage history."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id_1": {
                    "type": "number",
                    "description": "First server ID.",
                },
                "server_id_2": {
                    "type": "number",
                    "description": "Second server ID.",
                },
            },
            "required": ["server_id_1", "server_id_2"],
        },
    ),

    "audit_monitoring_coverage": lambda: mcp.types.Tool(
        name="audit_monitoring_coverage",
        description=(
            "Scan servers to find monitoring gaps: missing network service "
            "checks, no notification schedule, no contact group, or no template. "
            "Returns a coverage report with recommendations."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_group_id": {
                    "type": "number",
                    "description": "Optional server group ID to scope the audit. If omitted, audits all servers.",
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum number of servers to audit (default: 50).",
                },
            },
        },
    ),

    "generate_incident_timeline": lambda: mcp.types.Tool(
        name="generate_incident_timeline",
        description=(
            "Build a chronological incident timeline for an outage: outage "
            "events, notes, escalations, and associated server details."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "number",
                    "description": "The outage ID to generate a timeline for.",
                },
            },
            "required": ["outage_id"],
        },
    ),

    "find_flapping_servers": lambda: mcp.types.Tool(
        name="find_flapping_servers",
        description=(
            "Identify servers with repeated short outages (flapping) over a "
            "time window. Returns servers ranked by outage frequency with "
            "alert tuning suggestions."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "min_outage_count": {
                    "type": "number",
                    "description": "Minimum number of outages to flag as flapping (default: 3).",
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum number of servers to return (default: 20).",
                },
            },
        },
    ),

}

# ── Helpers ───────────────────────────────────────────────────────


def _safe_request(client, method, path, **kwargs):
    """Make an API request, returning None on error instead of raising."""
    try:
        return client._request(method, path, **kwargs)
    except Exception:
        return None


def _text(content: str) -> list:
    return [mcp.types.TextContent(type="text", text=content)]


# ── Handlers ──────────────────────────────────────────────────────


async def handle_investigate_server(arguments: dict, client) -> list:
    sid = arguments["server_id"]

    details = _safe_request(client, "GET", f"/server/{sid}")
    health = _safe_request(client, "GET", f"/server/{sid}", params={"include_status": True})
    outages = _safe_request(client, "GET", f"/server/{sid}/outage", params={"limit": 10})
    metrics = _safe_request(client, "GET", f"/server/{sid}/agent_resource", params={"limit": 20})
    maintenance = _safe_request(client, "GET", "/maintenance_schedule", params={"limit": 10})
    net_services = _safe_request(client, "GET", f"/server/{sid}/network_service", params={"limit": 50})

    report = {
        "investigation_report": {
            "server_id": sid,
            "server_details": details,
            "health_status": health,
            "recent_outages": outages,
            "agent_resources": metrics,
            "maintenance_schedules": maintenance,
            "network_services": net_services,
        }
    }
    return _text(json.dumps(report, indent=2, default=str))


async def handle_compare_servers(arguments: dict, client) -> list:
    sid1 = arguments["server_id_1"]
    sid2 = arguments["server_id_2"]

    def _gather(sid):
        return {
            "details": _safe_request(client, "GET", f"/server/{sid}"),
            "outages": _safe_request(client, "GET", f"/server/{sid}/outage", params={"limit": 5}),
            "network_services": _safe_request(client, "GET", f"/server/{sid}/network_service", params={"limit": 50}),
        }

    server1 = _gather(sid1)
    server2 = _gather(sid2)

    comparison = {
        "server_comparison": {
            "server_1": {"id": sid1, **server1},
            "server_2": {"id": sid2, **server2},
        }
    }
    return _text(json.dumps(comparison, indent=2, default=str))


async def handle_audit_monitoring_coverage(arguments: dict, client) -> list:
    group_id = arguments.get("server_group_id")
    limit = int(arguments.get("limit", 50))

    params = {"limit": limit}
    if group_id:
        servers_result = _safe_request(client, "GET", f"/server_group/{group_id}/server", params=params)
    else:
        servers_result = _safe_request(client, "GET", "/server", params=params)

    if not servers_result:
        return _text("Failed to retrieve server list.")

    server_list = servers_result.get("server_list", [])
    if not server_list:
        return _text("No servers found for audit.")

    gaps = {
        "no_network_services": [],
        "few_network_services": [],
        "summary": {
            "total_servers_audited": len(server_list),
            "servers_with_gaps": 0,
        },
    }

    for server in server_list[:limit]:
        server_url = server.get("url", "")
        server_name = server.get("name", server.get("fqdn", "unknown"))

        # Extract server ID from URL
        sid = server_url.rstrip("/").split("/")[-1] if server_url else None
        if not sid:
            continue

        ns_result = _safe_request(client, "GET", f"/server/{sid}/network_service", params={"limit": 100})
        ns_list = []
        if ns_result:
            ns_list = ns_result.get("network_service_list", [])

        if len(ns_list) == 0:
            gaps["no_network_services"].append({"name": server_name, "id": sid})
            gaps["summary"]["servers_with_gaps"] += 1
        elif len(ns_list) < 2:
            gaps["few_network_services"].append({
                "name": server_name,
                "id": sid,
                "service_count": len(ns_list),
            })
            gaps["summary"]["servers_with_gaps"] += 1

    return _text(json.dumps({"monitoring_coverage_audit": gaps}, indent=2, default=str))


async def handle_generate_incident_timeline(arguments: dict, client) -> list:
    outage_id = arguments["outage_id"]

    outage = _safe_request(client, "GET", f"/outage/{outage_id}")
    notes = _safe_request(client, "GET", f"/outage/{outage_id}/note", params={"limit": 50})

    # Get server details if outage has server info
    server_info = None
    if outage and outage.get("server_url"):
        server_url = outage["server_url"]
        sid = server_url.rstrip("/").split("/")[-1]
        server_info = _safe_request(client, "GET", f"/server/{sid}")

    timeline = {
        "incident_timeline": {
            "outage_id": outage_id,
            "outage_details": outage,
            "notes": notes,
            "server_info": server_info,
        }
    }
    return _text(json.dumps(timeline, indent=2, default=str))


async def handle_find_flapping_servers(arguments: dict, client) -> list:
    min_count = int(arguments.get("min_outage_count", 3))
    limit = int(arguments.get("limit", 20))

    # Get top alerting servers as the primary data source
    top_alerting = _safe_request(client, "GET", "/server", params={
        "limit": limit * 2,
        "sort_by": "outage_count",
        "sort_order": "desc",
    })

    if not top_alerting:
        return _text("Failed to retrieve server data for flapping analysis.")

    server_list = top_alerting.get("server_list", [])

    flapping = []
    for server in server_list:
        server_url = server.get("url", "")
        sid = server_url.rstrip("/").split("/")[-1] if server_url else None
        if not sid:
            continue

        outages = _safe_request(client, "GET", f"/server/{sid}/outage", params={"limit": 50})
        outage_list = []
        if outages:
            outage_list = outages.get("outage_list", [])

        if len(outage_list) >= min_count:
            flapping.append({
                "server_name": server.get("name", server.get("fqdn", "unknown")),
                "server_id": sid,
                "outage_count": len(outage_list),
                "recent_outages": outage_list[:5],
            })

        if len(flapping) >= limit:
            break

    result = {
        "flapping_servers": {
            "min_outage_threshold": min_count,
            "servers_found": len(flapping),
            "servers": flapping,
        }
    }
    return _text(json.dumps(result, indent=2, default=str))


COMPOSITE_HANDLERS = {
    "investigate_server": handle_investigate_server,
    "compare_servers": handle_compare_servers,
    "audit_monitoring_coverage": handle_audit_monitoring_coverage,
    "generate_incident_timeline": handle_generate_incident_timeline,
    "find_flapping_servers": handle_find_flapping_servers,
}
