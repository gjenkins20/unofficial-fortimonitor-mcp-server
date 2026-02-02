"""Tools for server status and maintenance management - Phase 2 Priority 1."""

import logging
from typing import List
from datetime import datetime, timedelta, timezone

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


def set_server_status_tool_definition() -> Tool:
    """Return tool definition for setting server status."""
    return Tool(
        name="set_server_status",
        description=(
            "Update a server's monitoring status. "
            "Use 'active' to enable monitoring, 'inactive' to disable, or 'paused' to temporarily suspend. "
            "This affects whether the server generates alerts and outages."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server",
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive", "paused"],
                    "description": "New monitoring status for the server",
                },
            },
            "required": ["server_id", "status"],
        },
    )


async def handle_set_server_status(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle set_server_status tool execution."""
    try:
        server_id = arguments["server_id"]
        status = arguments["status"]

        logger.info(f"Setting server {server_id} status to {status}")

        # Get current server info for context
        old_server = client.get_server_details(server_id)
        old_status = old_server.status

        # Update status
        updated_server = client.update_server_status(
            server_id=server_id,
            status=status,
        )

        # Format response
        output_lines = [
            "**Server Status Updated**\n",
            f"Server: {updated_server.name} ({server_id})",
            f"Previous Status: {old_status}",
            f"New Status: {status}",
        ]

        # Add helpful context based on status
        if status == "inactive":
            output_lines.append(
                "\nWarning: Monitoring disabled. Server will not generate alerts."
            )
        elif status == "paused":
            output_lines.append("\nMonitoring paused. Resume when ready.")
        elif status == "active":
            output_lines.append(
                "\nMonitoring enabled. Server will generate alerts normally."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Server {arguments.get('server_id')} not found.",
            )
        ]
    except ValueError as e:
        return [TextContent(type="text", text=f"Error: Invalid status - {str(e)}")]
    except APIError as e:
        logger.error(f"API error updating server status: {e}")
        return [
            TextContent(type="text", text=f"Error updating server status: {str(e)}")
        ]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


def create_maintenance_window_tool_definition() -> Tool:
    """Return tool definition for creating maintenance windows."""
    return Tool(
        name="create_maintenance_window",
        description=(
            "Schedule a maintenance window to suppress alerts for one or more servers. "
            "During the maintenance window, monitoring continues but notifications are suppressed. "
            "Useful for planned maintenance, updates, or reboots."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for this maintenance window",
                },
                "server_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List of server IDs to include in maintenance window",
                },
                "duration_hours": {
                    "type": "number",
                    "description": "Duration in hours (e.g., 2.5 for 2.5 hours)",
                },
                "start_time": {
                    "type": "string",
                    "description": "When to start (ISO format: YYYY-MM-DDTHH:MM:SSZ), or 'now' to start immediately",
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the maintenance",
                },
            },
            "required": ["name", "server_ids", "duration_hours"],
        },
    )


async def handle_create_maintenance_window(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle create_maintenance_window tool execution."""
    try:
        name = arguments["name"]
        server_ids = arguments["server_ids"]
        duration_hours = arguments["duration_hours"]
        start_time_str = arguments.get("start_time", "now")
        description = arguments.get("description")

        # Parse start time
        if start_time_str.lower() == "now":
            start_time = datetime.now(timezone.utc)
        else:
            try:
                start_time = datetime.fromisoformat(
                    start_time_str.replace("Z", "+00:00")
                )
            except ValueError:
                return [
                    TextContent(
                        type="text",
                        text="Error: Invalid start_time format. Use ISO format (e.g., '2026-02-03T14:00:00Z') or 'now'",
                    )
                ]

        # Convert duration to minutes for API
        duration_minutes = int(duration_hours * 60)

        logger.info(f"Creating maintenance schedule: {name} for {len(server_ids)} servers")

        # Create maintenance schedule using correct API method
        window = client.create_maintenance_schedule(
            name=name,
            start_time=start_time,
            duration=duration_minutes,
            servers=server_ids,
            description=description,
        )

        # Calculate end time for display
        end_time = start_time + timedelta(hours=duration_hours)

        # Format response
        window_id = window.window_id or window.id or "N/A"
        output_lines = [
            "**Maintenance Schedule Created**\n",
            f"Name: {window.name}",
            f"ID: {window_id}",
            f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"End: {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')} (approx.)",
            f"Duration: {duration_hours} hours ({duration_minutes} minutes)",
            f"Servers: {len(server_ids)} server(s)",
        ]

        if description:
            output_lines.append(f"\nDescription: {description}")

        output_lines.append(
            "\nNote: Monitoring will continue but alerts will be suppressed during this window."
        )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except ValueError as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except APIError as e:
        logger.error(f"API error creating maintenance schedule: {e}")
        return [
            TextContent(
                type="text", text=f"Error creating maintenance schedule: {str(e)}"
            )
        ]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


def list_maintenance_windows_tool_definition() -> Tool:
    """Return tool definition for listing maintenance windows."""
    return Tool(
        name="list_maintenance_windows",
        description=(
            "List scheduled maintenance windows. "
            "Optionally filter to show only currently active windows."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "active_only": {
                    "type": "boolean",
                    "default": False,
                    "description": "If true, only show currently active maintenance windows",
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 100,
                    "description": "Maximum number of windows to return",
                },
            },
        },
    )


async def handle_list_maintenance_windows(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle list_maintenance_windows tool execution."""
    try:
        active_only = arguments.get("active_only", False)
        limit = arguments.get("limit", 50)

        logger.info(f"Listing maintenance windows (active_only={active_only})")

        # Get maintenance windows
        response = client.list_maintenance_windows(
            limit=limit,
            active_only=active_only,
        )

        windows = response.maintenance_window_list

        if not windows:
            status_text = "active" if active_only else "scheduled"
            return [
                TextContent(
                    type="text",
                    text=f"No {status_text} maintenance windows found.",
                )
            ]

        # Format response
        output_lines = [f"**Maintenance Windows ({len(windows)} found)**\n"]

        for window in windows:
            window_id = window.window_id or window.id or "N/A"
            output_lines.append(f"\n**{window.name}** (ID: {window_id})")

            if window.start_time:
                output_lines.append(
                    f"  Start: {window.start_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            if window.end_time:
                output_lines.append(
                    f"  End: {window.end_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )

            output_lines.append(f"  Servers: {len(window.servers)}")

            if window.description:
                output_lines.append(f"  Description: {window.description}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing maintenance windows: {e}")
        return [
            TextContent(
                type="text", text=f"Error listing maintenance windows: {str(e)}"
            )
        ]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]
