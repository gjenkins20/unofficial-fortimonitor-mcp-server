"""MCP tools for outage (alert) operations."""

from typing import List
from datetime import datetime, timedelta
import logging

from mcp.types import Tool, TextContent
from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import FortiMonitorError

logger = logging.getLogger(__name__)


def get_outages_tool_definition() -> Tool:
    """Define the get_outages MCP tool."""
    return Tool(
        name="get_outages",
        description=(
            "Query FortiMonitor outages (alerts) with various filters. "
            "Returns active and recent outages for monitored servers."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "Filter by specific server ID",
                },
                "severity": {
                    "type": "string",
                    "description": "Filter by outage severity",
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "resolved"],
                    "description": "Filter by outage status",
                },
                "hours_back": {
                    "type": "integer",
                    "default": 24,
                    "minimum": 1,
                    "maximum": 168,
                    "description": "How many hours back to search (default: 24)",
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 500,
                    "description": "Maximum number of outages to return",
                },
                "active_only": {
                    "type": "boolean",
                    "default": False,
                    "description": "Only return active outages",
                },
            },
        },
    )


async def handle_get_outages(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_outages tool execution."""
    try:
        server_id = arguments.get("server_id")
        severity = arguments.get("severity")
        status = arguments.get("status")
        hours_back = arguments.get("hours_back", 24)
        limit = arguments.get("limit", 50)
        active_only = arguments.get("active_only", False)

        logger.info(
            f"Getting outages: server_id={server_id}, severity={severity}, "
            f"status={status}, hours_back={hours_back}, active_only={active_only}"
        )

        # Use active outages endpoint if requested
        if active_only:
            response = client.get_active_outages(server_id=server_id, limit=limit)
        else:
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)

            response = client.get_outages(
                server_id=server_id,
                severity=severity,
                status=status,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )

        if not response.outage_list:
            time_desc = "active" if active_only else f"in the last {hours_back} hours"
            return [
                TextContent(
                    type="text",
                    text=f"No outages found {time_desc} matching the specified criteria.",
                )
            ]

        # Group outages by severity
        outages_by_severity = {"critical": [], "warning": [], "info": [], "other": []}
        for outage in response.outage_list:
            severity_key = outage.severity.lower()
            if severity_key not in outages_by_severity:
                severity_key = "other"
            outages_by_severity[severity_key].append(outage)

        # Format outage list
        time_desc = "active" if active_only else f"in the last {hours_back} hours"
        result_parts = [
            f"Found {response.total_count or len(response.outage_list)} total outage(s) {time_desc} "
            f"(showing {len(response.outage_list)}):\n"
        ]

        for sev in ["critical", "warning", "info", "other"]:
            sev_outages = outages_by_severity[sev]
            if sev_outages:
                result_parts.append(f"\n**{sev.upper()} ({len(sev_outages)})**:")
                for outage in sev_outages:
                    ack_status = (
                        "✓ Acknowledged" if outage.acknowledged else "⚠ Not Acknowledged"
                    )
                    duration = (
                        f"{outage.duration // 60}m" if outage.duration else "ongoing"
                    )
                    outage_info = (
                        f"\n  Outage ID: {outage.id}\n"
                        f"  Server: {outage.server_name or 'N/A'}\n"
                        f"  Status: {outage.status} | {ack_status}\n"
                        f"  Duration: {duration}\n"
                        f"  Start: {outage.start_time}\n"
                    )
                    if outage.message:
                        outage_info += f"  Message: {outage.message}\n"
                    result_parts.append(outage_info)

        return [TextContent(type="text", text="".join(result_parts))]

    except FortiMonitorError as e:
        logger.error(f"FortiMonitor API error: {e}")
        return [TextContent(type="text", text=f"Error retrieving outages: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in get_outages")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]
