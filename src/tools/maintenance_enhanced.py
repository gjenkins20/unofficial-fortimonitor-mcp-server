"""Enhanced maintenance schedule tools - additional operations beyond basic CRUD."""

import logging
import re
from datetime import datetime
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def get_maintenance_schedule_details_tool_definition() -> Tool:
    """Return tool definition for getting maintenance schedule details."""
    return Tool(
        name="get_maintenance_schedule_details",
        description=(
            "Get detailed information about a specific maintenance schedule, "
            "including name, start/end times, description, notification suppression, "
            "and recurrence settings."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "integer",
                    "description": "The ID of the maintenance schedule",
                },
            },
            "required": ["schedule_id"],
        },
    )


def update_maintenance_schedule_tool_definition() -> Tool:
    """Return tool definition for updating a maintenance schedule."""
    return Tool(
        name="update_maintenance_schedule",
        description=(
            "Update an existing maintenance schedule. "
            "You can change the name, start time, and/or end time. "
            "Only provided fields will be updated."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "integer",
                    "description": "The ID of the maintenance schedule to update",
                },
                "name": {
                    "type": "string",
                    "description": "New name for the maintenance schedule",
                },
                "start_time": {
                    "type": "string",
                    "description": "New start time in ISO format (e.g., '2026-02-05T14:00:00Z')",
                },
                "end_time": {
                    "type": "string",
                    "description": "New end time in ISO format (e.g., '2026-02-05T16:00:00Z')",
                },
            },
            "required": ["schedule_id"],
        },
    )


def delete_maintenance_schedule_tool_definition() -> Tool:
    """Return tool definition for deleting a maintenance schedule."""
    return Tool(
        name="delete_maintenance_schedule",
        description=(
            "Delete a maintenance schedule. "
            "This permanently removes the schedule and cannot be undone."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "integer",
                    "description": "The ID of the maintenance schedule to delete",
                },
            },
            "required": ["schedule_id"],
        },
    )


def extend_maintenance_schedule_tool_definition() -> Tool:
    """Return tool definition for extending a maintenance schedule."""
    return Tool(
        name="extend_maintenance_schedule",
        description=(
            "Extend a maintenance schedule by additional minutes. "
            "Useful when maintenance is taking longer than expected."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "integer",
                    "description": "The ID of the maintenance schedule to extend",
                },
                "minutes": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of minutes to extend the schedule by",
                },
            },
            "required": ["schedule_id", "minutes"],
        },
    )


def pause_maintenance_schedule_tool_definition() -> Tool:
    """Return tool definition for pausing a maintenance schedule."""
    return Tool(
        name="pause_maintenance_schedule",
        description=(
            "Pause an active maintenance schedule. "
            "Monitoring and alerts will resume while the schedule is paused."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "integer",
                    "description": "The ID of the maintenance schedule to pause",
                },
            },
            "required": ["schedule_id"],
        },
    )


def resume_maintenance_schedule_tool_definition() -> Tool:
    """Return tool definition for resuming a paused maintenance schedule."""
    return Tool(
        name="resume_maintenance_schedule",
        description=(
            "Resume a paused maintenance schedule. "
            "Alert suppression will be re-enabled for the remainder of the window."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "integer",
                    "description": "The ID of the maintenance schedule to resume",
                },
            },
            "required": ["schedule_id"],
        },
    )


def terminate_maintenance_schedule_tool_definition() -> Tool:
    """Return tool definition for terminating a maintenance schedule early."""
    return Tool(
        name="terminate_maintenance_schedule",
        description=(
            "Terminate a maintenance schedule early. "
            "Monitoring and alerts will immediately resume for all affected servers."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "integer",
                    "description": "The ID of the maintenance schedule to terminate",
                },
            },
            "required": ["schedule_id"],
        },
    )


def get_server_maintenance_schedules_tool_definition() -> Tool:
    """Return tool definition for getting maintenance schedules for a server."""
    return Tool(
        name="get_server_maintenance_schedules",
        description=(
            "Get maintenance schedules associated with a specific server. "
            "Shows all scheduled, active, and past maintenance windows for the server."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server",
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 100,
                    "description": "Maximum number of schedules to return (default 50)",
                },
            },
            "required": ["server_id"],
        },
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_get_maintenance_schedule_details(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle get_maintenance_schedule_details tool execution."""
    try:
        schedule_id = arguments["schedule_id"]

        logger.info(f"Getting details for maintenance schedule {schedule_id}")

        schedule = client.get_maintenance_schedule_details(schedule_id)

        window_id = schedule.window_id or schedule.id or schedule_id

        output_lines = [
            f"**Maintenance Schedule Details** (ID: {window_id})\n",
            f"Name: {schedule.name}",
        ]

        if schedule.start_time:
            output_lines.append(
                f"Start Time: {schedule.start_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        if schedule.end_time:
            output_lines.append(
                f"End Time: {schedule.end_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        if schedule.description:
            output_lines.append(f"Description: {schedule.description}")

        output_lines.append(
            f"Suppress Notifications: {'Yes' if schedule.suppress_notifications else 'No'}"
        )

        if schedule.recurrence:
            output_lines.append(f"Recurrence: {schedule.recurrence}")

        # Show server count
        output_lines.append(f"Servers: {len(schedule.servers)}")

        # List server IDs if present
        if schedule.servers:
            server_ids = []
            for server_url in schedule.servers[:10]:
                match = re.search(r'/server/(\d+)', server_url)
                if match:
                    server_ids.append(match.group(1))
            if server_ids:
                output_lines.append(f"Server IDs: {', '.join(server_ids)}")
            if len(schedule.servers) > 10:
                output_lines.append(
                    f"  ... and {len(schedule.servers) - 10} more"
                )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Maintenance schedule {arguments.get('schedule_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error getting maintenance schedule details: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error getting maintenance schedule details: {str(e)}",
            )
        ]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_maintenance_schedule(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle update_maintenance_schedule tool execution."""
    try:
        schedule_id = arguments["schedule_id"]
        name = arguments.get("name")
        start_time_str = arguments.get("start_time")
        end_time_str = arguments.get("end_time")

        # Ensure at least one update field is provided
        if not any([name, start_time_str, end_time_str]):
            return [
                TextContent(
                    type="text",
                    text="Error: At least one field (name, start_time, end_time) must be provided for update.",
                )
            ]

        # Parse datetime strings
        start_time = None
        end_time = None

        if start_time_str:
            try:
                start_time = datetime.fromisoformat(
                    start_time_str.replace("Z", "+00:00")
                )
            except ValueError:
                return [
                    TextContent(
                        type="text",
                        text="Error: Invalid start_time format. Use ISO format (e.g., '2026-02-05T14:00:00Z').",
                    )
                ]

        if end_time_str:
            try:
                end_time = datetime.fromisoformat(
                    end_time_str.replace("Z", "+00:00")
                )
            except ValueError:
                return [
                    TextContent(
                        type="text",
                        text="Error: Invalid end_time format. Use ISO format (e.g., '2026-02-05T16:00:00Z').",
                    )
                ]

        logger.info(f"Updating maintenance schedule {schedule_id}")

        updated = client.update_maintenance_schedule(
            schedule_id=schedule_id,
            name=name,
            start_time=start_time,
            end_time=end_time,
        )

        # Format response
        output_lines = [
            "**Maintenance Schedule Updated**\n",
            f"ID: {schedule_id}",
            f"Name: {updated.name}",
        ]

        if updated.start_time:
            output_lines.append(
                f"Start Time: {updated.start_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        if updated.end_time:
            output_lines.append(
                f"End Time: {updated.end_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        # Show what was updated
        changes = []
        if name:
            changes.append("name")
        if start_time:
            changes.append("start time")
        if end_time:
            changes.append("end time")
        output_lines.append(f"\nFields updated: {', '.join(changes)}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Maintenance schedule {arguments.get('schedule_id')} not found.",
            )
        ]
    except ValueError as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except APIError as e:
        logger.error(f"API error updating maintenance schedule: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error updating maintenance schedule: {str(e)}",
            )
        ]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_maintenance_schedule(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle delete_maintenance_schedule tool execution."""
    try:
        schedule_id = arguments["schedule_id"]

        logger.info(f"Deleting maintenance schedule {schedule_id}")

        # Get schedule name before deletion for output
        schedule_name = f"ID {schedule_id}"
        try:
            schedule = client.get_maintenance_schedule_details(schedule_id)
            schedule_name = schedule.name
        except Exception:
            pass

        result = client.delete_maintenance_schedule(schedule_id)

        if result:
            return [
                TextContent(
                    type="text",
                    text=(
                        f"**Maintenance Schedule Deleted**\n\n"
                        f"Schedule '{schedule_name}' (ID: {schedule_id}) has been permanently deleted.\n"
                        f"Monitoring and alerts will resume normally for affected servers."
                    ),
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Error: Failed to delete maintenance schedule {schedule_id}.",
                )
            ]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Maintenance schedule {arguments.get('schedule_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error deleting maintenance schedule: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error deleting maintenance schedule: {str(e)}",
            )
        ]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_extend_maintenance_schedule(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle extend_maintenance_schedule tool execution."""
    try:
        schedule_id = arguments["schedule_id"]
        minutes = arguments["minutes"]

        if minutes < 1:
            return [
                TextContent(
                    type="text",
                    text="Error: Minutes must be a positive integer.",
                )
            ]

        logger.info(f"Extending maintenance schedule {schedule_id} by {minutes} minutes")

        client._request(
            "POST",
            f"maintenance_schedule/{schedule_id}/extend",
            json_data={"minutes": minutes},
        )

        # Format duration display
        if minutes >= 60:
            hours = minutes // 60
            remaining_mins = minutes % 60
            duration_str = f"{hours}h {remaining_mins}m" if remaining_mins else f"{hours}h"
        else:
            duration_str = f"{minutes} minutes"

        return [
            TextContent(
                type="text",
                text=(
                    f"**Maintenance Schedule Extended**\n\n"
                    f"Schedule ID: {schedule_id}\n"
                    f"Extended by: {duration_str}\n\n"
                    f"Alert suppression will continue for the extended duration."
                ),
            )
        ]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Maintenance schedule {arguments.get('schedule_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error extending maintenance schedule: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error extending maintenance schedule: {str(e)}",
            )
        ]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_pause_maintenance_schedule(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle pause_maintenance_schedule tool execution."""
    try:
        schedule_id = arguments["schedule_id"]

        logger.info(f"Pausing maintenance schedule {schedule_id}")

        client._request(
            "POST",
            f"maintenance_schedule/{schedule_id}/pause",
        )

        return [
            TextContent(
                type="text",
                text=(
                    f"**Maintenance Schedule Paused**\n\n"
                    f"Schedule ID: {schedule_id}\n"
                    f"Status: Paused\n\n"
                    f"Monitoring and alerts have resumed. "
                    f"Use resume_maintenance_schedule to re-enable alert suppression."
                ),
            )
        ]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Maintenance schedule {arguments.get('schedule_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error pausing maintenance schedule: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error pausing maintenance schedule: {str(e)}",
            )
        ]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_resume_maintenance_schedule(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle resume_maintenance_schedule tool execution."""
    try:
        schedule_id = arguments["schedule_id"]

        logger.info(f"Resuming maintenance schedule {schedule_id}")

        client._request(
            "POST",
            f"maintenance_schedule/{schedule_id}/resume",
        )

        return [
            TextContent(
                type="text",
                text=(
                    f"**Maintenance Schedule Resumed**\n\n"
                    f"Schedule ID: {schedule_id}\n"
                    f"Status: Active\n\n"
                    f"Alert suppression has been re-enabled for the remainder of the maintenance window."
                ),
            )
        ]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Maintenance schedule {arguments.get('schedule_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error resuming maintenance schedule: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error resuming maintenance schedule: {str(e)}",
            )
        ]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_terminate_maintenance_schedule(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle terminate_maintenance_schedule tool execution."""
    try:
        schedule_id = arguments["schedule_id"]

        logger.info(f"Terminating maintenance schedule {schedule_id}")

        client._request(
            "POST",
            f"maintenance_schedule/{schedule_id}/terminate",
        )

        return [
            TextContent(
                type="text",
                text=(
                    f"**Maintenance Schedule Terminated**\n\n"
                    f"Schedule ID: {schedule_id}\n"
                    f"Status: Terminated\n\n"
                    f"The maintenance window has ended early. "
                    f"Monitoring and alerts have resumed for all affected servers."
                ),
            )
        ]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Maintenance schedule {arguments.get('schedule_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error terminating maintenance schedule: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error terminating maintenance schedule: {str(e)}",
            )
        ]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_server_maintenance_schedules(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle get_server_maintenance_schedules tool execution."""
    try:
        server_id = arguments["server_id"]
        limit = arguments.get("limit", 50)

        logger.info(f"Getting maintenance schedules for server {server_id}")

        response = client._request(
            "GET",
            f"server/{server_id}/maintenance_schedule",
            params={"limit": limit},
        )

        schedules = response.get("maintenance_schedule_list", [])

        if not schedules:
            return [
                TextContent(
                    type="text",
                    text=f"No maintenance schedules found for server {server_id}.",
                )
            ]

        # Get server name for context
        server_name = f"Server {server_id}"
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            pass

        output_lines = [
            f"**Maintenance Schedules for {server_name}** (ID: {server_id})\n",
            f"Found {len(schedules)} schedule(s):\n",
        ]

        for sched in schedules:
            # Extract ID from URL if available
            sched_id = "N/A"
            if sched.get("url"):
                match = re.search(r'/maintenance_schedule/(\d+)', sched["url"])
                if match:
                    sched_id = match.group(1)
            elif sched.get("id"):
                sched_id = sched["id"]

            name = sched.get("name", "Unnamed")
            output_lines.append(f"\n**{name}** (ID: {sched_id})")

            if sched.get("start"):
                output_lines.append(f"  Start: {sched['start']}")
            if sched.get("end"):
                output_lines.append(f"  End: {sched['end']}")
            if sched.get("description"):
                output_lines.append(f"  Description: {sched['description']}")
            if sched.get("recurrence"):
                output_lines.append(f"  Recurrence: {sched['recurrence']}")

        meta = response.get("meta", {})
        total = meta.get("total_count")
        if total and total > len(schedules):
            output_lines.append(f"\n(Showing {len(schedules)} of {total} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Server {arguments.get('server_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error getting server maintenance schedules: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error getting server maintenance schedules: {str(e)}",
            )
        ]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# MODULE EXPORTS
# ============================================================================

MAINTENANCE_ENHANCED_TOOL_DEFINITIONS = {
    "get_maintenance_schedule_details": get_maintenance_schedule_details_tool_definition,
    "update_maintenance_schedule": update_maintenance_schedule_tool_definition,
    "delete_maintenance_schedule": delete_maintenance_schedule_tool_definition,
    "extend_maintenance_schedule": extend_maintenance_schedule_tool_definition,
    "pause_maintenance_schedule": pause_maintenance_schedule_tool_definition,
    "resume_maintenance_schedule": resume_maintenance_schedule_tool_definition,
    "terminate_maintenance_schedule": terminate_maintenance_schedule_tool_definition,
    "get_server_maintenance_schedules": get_server_maintenance_schedules_tool_definition,
}

MAINTENANCE_ENHANCED_HANDLERS = {
    "get_maintenance_schedule_details": handle_get_maintenance_schedule_details,
    "update_maintenance_schedule": handle_update_maintenance_schedule,
    "delete_maintenance_schedule": handle_delete_maintenance_schedule,
    "extend_maintenance_schedule": handle_extend_maintenance_schedule,
    "pause_maintenance_schedule": handle_pause_maintenance_schedule,
    "resume_maintenance_schedule": handle_resume_maintenance_schedule,
    "terminate_maintenance_schedule": handle_terminate_maintenance_schedule,
    "get_server_maintenance_schedules": handle_get_server_maintenance_schedules,
}
