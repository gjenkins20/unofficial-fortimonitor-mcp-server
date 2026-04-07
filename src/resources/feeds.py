"""
FortiMonitor MCP Resources - Live Data Feeds

Copyright (c) 2026 Gregori Jenkins
https://github.com/gjenkins20/unofficial-fortimonitor-mcp-server

Exposes structured data endpoints that MCP clients can read without
invoking tools. Each resource fetches live data from the FortiMonitor API.
"""

import json
from typing import Optional

from mcp.types import Resource


# ── Resource Definitions ─────────────────────────────────────────────

RESOURCES = [
    Resource(
        uri="fortimonitor://outages/active",
        name="Active Outages",
        description="Current active outages across all monitored servers. Refreshed on each read.",
        mimeType="application/json",
    ),
    Resource(
        uri="fortimonitor://health/summary",
        name="Health Summary",
        description="Aggregate server health: total servers, up/down counts, outage statistics.",
        mimeType="application/json",
    ),
    Resource(
        uri="fortimonitor://maintenance/upcoming",
        name="Upcoming Maintenance",
        description="Active and pending maintenance windows for the next 7 days.",
        mimeType="application/json",
    ),
    Resource(
        uri="fortimonitor://alerts/recent",
        name="Recent Alerts",
        description="Recent outage activity (latest 25 outages across all servers).",
        mimeType="application/json",
    ),
]


# ── Resource Handlers ────────────────────────────────────────────────

def _safe_request(client, method, path, **kwargs):
    """Make an API request, returning empty dict on error."""
    try:
        return client._request(method, path, **kwargs)
    except Exception as e:
        return {"error": str(e)}


async def read_active_outages(client) -> str:
    """Fetch active outages."""
    result = _safe_request(client, "GET", "/outage", params={
        "limit": 50,
        "status": "active",
    })
    outage_list = result.get("outage_list", [])

    output = {
        "active_outages": {
            "count": len(outage_list),
            "outages": outage_list,
        }
    }
    return json.dumps(output, indent=2, default=str)


async def read_health_summary(client) -> str:
    """Fetch aggregate health summary."""
    servers = _safe_request(client, "GET", "/server", params={"limit": 1})
    outages = _safe_request(client, "GET", "/outage", params={"limit": 1, "status": "active"})

    # Extract counts from pagination metadata
    total_servers = servers.get("meta", {}).get("total_count", 0) if isinstance(servers.get("meta"), dict) else 0
    active_outages = outages.get("meta", {}).get("total_count", 0) if isinstance(outages.get("meta"), dict) else 0

    # Fallback: count from list length if no meta
    if not total_servers and "server_list" in servers:
        total_servers = len(servers["server_list"])
    if not active_outages and "outage_list" in outages:
        active_outages = len(outages["outage_list"])

    output = {
        "health_summary": {
            "total_servers": total_servers,
            "active_outage_count": active_outages,
            "servers_up": max(0, total_servers - active_outages),
        }
    }
    return json.dumps(output, indent=2, default=str)


async def read_upcoming_maintenance(client) -> str:
    """Fetch active or pending maintenance windows."""
    result = _safe_request(client, "GET", "/maintenance_schedule/active_or_pending",
                           params={"limit": 25})

    schedule_list = result.get("maintenance_schedule_list", [])

    output = {
        "upcoming_maintenance": {
            "count": len(schedule_list),
            "schedules": schedule_list,
        }
    }
    return json.dumps(output, indent=2, default=str)


async def read_recent_alerts(client) -> str:
    """Fetch recent outages (all statuses)."""
    result = _safe_request(client, "GET", "/outage", params={"limit": 25})

    outage_list = result.get("outage_list", [])

    output = {
        "recent_alerts": {
            "count": len(outage_list),
            "outages": outage_list,
        }
    }
    return json.dumps(output, indent=2, default=str)


# Map resource URI -> handler function
RESOURCE_HANDLERS = {
    "fortimonitor://outages/active": read_active_outages,
    "fortimonitor://health/summary": read_health_summary,
    "fortimonitor://maintenance/upcoming": read_upcoming_maintenance,
    "fortimonitor://alerts/recent": read_recent_alerts,
}
