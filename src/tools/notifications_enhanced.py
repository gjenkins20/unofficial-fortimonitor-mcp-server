"""Enhanced notification schedule management tools for FortiMonitor."""

import logging
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _extract_id_from_url(url: str) -> str:
    """Extract the ID from the end of an API URL."""
    if url:
        parts = url.rstrip("/").split("/")
        if parts:
            return parts[-1]
    return "N/A"


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def create_notification_schedule_tool_definition() -> Tool:
    """Return tool definition for creating a notification schedule."""
    return Tool(
        name="create_notification_schedule",
        description=(
            "Create a new notification schedule that defines when alerts are sent "
            "(e.g., business hours only, 24/7, weekends)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the notification schedule"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description"
                }
            },
            "required": ["name"]
        }
    )


def update_notification_schedule_tool_definition() -> Tool:
    """Return tool definition for updating a notification schedule."""
    return Tool(
        name="update_notification_schedule",
        description="Update an existing notification schedule's name or description.",
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "integer",
                    "description": "ID of the notification schedule to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description (optional)"
                }
            },
            "required": ["schedule_id"]
        }
    )


def delete_notification_schedule_tool_definition() -> Tool:
    """Return tool definition for deleting a notification schedule."""
    return Tool(
        name="delete_notification_schedule",
        description=(
            "Delete a notification schedule. Servers and contact groups using this "
            "schedule will need to be reassigned."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "integer",
                    "description": "ID of the notification schedule to delete"
                }
            },
            "required": ["schedule_id"]
        }
    )


def get_notification_schedule_thresholds_tool_definition() -> Tool:
    """Return tool definition for getting thresholds linked to a schedule."""
    return Tool(
        name="get_notification_schedule_thresholds",
        description=(
            "Get agent resource thresholds associated with a notification schedule. "
            "Shows which alert thresholds use this schedule."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "integer",
                    "description": "ID of the notification schedule"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of thresholds to return (default 50)"
                }
            },
            "required": ["schedule_id"]
        }
    )


def get_notification_schedule_compound_services_tool_definition() -> Tool:
    """Return tool definition for getting compound services linked to a schedule."""
    return Tool(
        name="get_notification_schedule_compound_services",
        description=(
            "Get compound services associated with a notification schedule."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "integer",
                    "description": "ID of the notification schedule"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum results to return (default 50)"
                }
            },
            "required": ["schedule_id"]
        }
    )


def get_notification_schedule_network_services_tool_definition() -> Tool:
    """Return tool definition for getting network services linked to a schedule."""
    return Tool(
        name="get_notification_schedule_network_services",
        description=(
            "Get network services (monitoring checks) associated with a notification schedule."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "integer",
                    "description": "ID of the notification schedule"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum results to return (default 50)"
                }
            },
            "required": ["schedule_id"]
        }
    )


def get_notification_schedule_servers_tool_definition() -> Tool:
    """Return tool definition for getting servers linked to a schedule."""
    return Tool(
        name="get_notification_schedule_servers",
        description=(
            "Get servers associated with a notification schedule. "
            "Shows which servers use this schedule for their alerts."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "integer",
                    "description": "ID of the notification schedule"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum results to return (default 50)"
                }
            },
            "required": ["schedule_id"]
        }
    )


def get_notification_schedule_server_groups_tool_definition() -> Tool:
    """Return tool definition for getting server groups linked to a schedule."""
    return Tool(
        name="get_notification_schedule_server_groups",
        description=(
            "Get server groups associated with a notification schedule."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "integer",
                    "description": "ID of the notification schedule"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum results to return (default 50)"
                }
            },
            "required": ["schedule_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_create_notification_schedule(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_notification_schedule tool execution."""
    try:
        name = arguments["name"]
        description = arguments.get("description")

        logger.info(f"Creating notification schedule: {name}")

        data = {"name": name}
        if description:
            data["description"] = description

        response = client._request(
            "POST", "notification_schedule", json_data=data
        )

        output_lines = [
            "**Notification Schedule Created**\n",
            f"Name: {name}"
        ]

        if description:
            output_lines.append(f"Description: {description}")

        if isinstance(response, dict) and response.get("url"):
            sched_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Schedule ID: {sched_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nSchedule created. Use 'list_notification_schedules' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating notification schedule: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating notification schedule")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_notification_schedule(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_notification_schedule tool execution."""
    try:
        schedule_id = arguments["schedule_id"]
        name = arguments.get("name")
        description = arguments.get("description")

        if name is None and description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name' or 'description' must be provided."
            )]

        logger.info(f"Updating notification schedule {schedule_id}")

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        client._request(
            "PUT", f"notification_schedule/{schedule_id}", json_data=data
        )

        output_lines = ["**Notification Schedule Updated**\n"]
        if name:
            output_lines.append(f"Name: {name}")
        if description is not None:
            output_lines.append(f"Description: Updated")
        output_lines.append(f"Schedule ID: {schedule_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Notification schedule {arguments.get('schedule_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating notification schedule: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating notification schedule")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_notification_schedule(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_notification_schedule tool execution."""
    try:
        schedule_id = arguments["schedule_id"]

        logger.info(f"Deleting notification schedule {schedule_id}")

        try:
            response = client._request(
                "GET", f"notification_schedule/{schedule_id}"
            )
            sched_name = response.get("name", f"ID {schedule_id}")
        except Exception:
            sched_name = f"ID {schedule_id}"

        client._request("DELETE", f"notification_schedule/{schedule_id}")

        return [TextContent(
            type="text",
            text=(
                f"**Notification Schedule Deleted**\n\n"
                f"Schedule '{sched_name}' (ID: {schedule_id}) has been deleted.\n\n"
                f"Note: Servers and contact groups using this schedule will need "
                f"to be reassigned."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Notification schedule {arguments.get('schedule_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting notification schedule: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting notification schedule")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def _handle_schedule_sub_resource(
    arguments: dict,
    client: FortiMonitorClient,
    sub_resource: str,
    list_key: str,
    display_name: str
) -> List[TextContent]:
    """Generic handler for notification schedule sub-resources."""
    try:
        schedule_id = arguments["schedule_id"]
        limit = arguments.get("limit", 50)

        logger.info(
            f"Getting {sub_resource} for notification schedule {schedule_id}"
        )

        response = client._request(
            "GET",
            f"notification_schedule/{schedule_id}/{sub_resource}",
            params={"limit": limit}
        )
        items = response.get(list_key, [])
        meta = response.get("meta", {})

        if not items:
            return [TextContent(
                type="text",
                text=f"No {display_name} found for notification schedule {schedule_id}."
            )]

        total_count = meta.get("total_count", len(items))

        output_lines = [
            f"**{display_name} for Notification Schedule {schedule_id}**\n",
            f"Found {len(items)} item(s):\n"
        ]

        for item in items:
            name = item.get("name", item.get("display_name", "Unknown"))
            item_id = _extract_id_from_url(item.get("url", ""))
            output_lines.append(f"\n**{name}** (ID: {item_id})")

        if total_count > len(items):
            output_lines.append(
                f"\n(Showing {len(items)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Notification schedule {arguments.get('schedule_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting {sub_resource}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception(f"Unexpected error getting {sub_resource}")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_notification_schedule_thresholds(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_notification_schedule_thresholds tool execution."""
    return await _handle_schedule_sub_resource(
        arguments, client,
        "agent_resource_threshold",
        "agent_resource_threshold_list",
        "Agent Resource Thresholds"
    )


async def handle_get_notification_schedule_compound_services(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_notification_schedule_compound_services tool execution."""
    return await _handle_schedule_sub_resource(
        arguments, client,
        "compound_service",
        "compound_service_list",
        "Compound Services"
    )


async def handle_get_notification_schedule_network_services(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_notification_schedule_network_services tool execution."""
    return await _handle_schedule_sub_resource(
        arguments, client,
        "network_service",
        "network_service_list",
        "Network Services"
    )


async def handle_get_notification_schedule_servers(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_notification_schedule_servers tool execution."""
    return await _handle_schedule_sub_resource(
        arguments, client,
        "server",
        "server_list",
        "Servers"
    )


async def handle_get_notification_schedule_server_groups(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_notification_schedule_server_groups tool execution."""
    return await _handle_schedule_sub_resource(
        arguments, client,
        "server_group",
        "server_group_list",
        "Server Groups"
    )


# ============================================================================
# EXPORT DICTS
# ============================================================================

NOTIFICATIONS_ENHANCED_TOOL_DEFINITIONS = {
    "create_notification_schedule": create_notification_schedule_tool_definition,
    "update_notification_schedule": update_notification_schedule_tool_definition,
    "delete_notification_schedule": delete_notification_schedule_tool_definition,
    "get_notification_schedule_thresholds": get_notification_schedule_thresholds_tool_definition,
    "get_notification_schedule_compound_services": get_notification_schedule_compound_services_tool_definition,
    "get_notification_schedule_network_services": get_notification_schedule_network_services_tool_definition,
    "get_notification_schedule_servers": get_notification_schedule_servers_tool_definition,
    "get_notification_schedule_server_groups": get_notification_schedule_server_groups_tool_definition,
}

NOTIFICATIONS_ENHANCED_HANDLERS = {
    "create_notification_schedule": handle_create_notification_schedule,
    "update_notification_schedule": handle_update_notification_schedule,
    "delete_notification_schedule": handle_delete_notification_schedule,
    "get_notification_schedule_thresholds": handle_get_notification_schedule_thresholds,
    "get_notification_schedule_compound_services": handle_get_notification_schedule_compound_services,
    "get_notification_schedule_network_services": handle_get_notification_schedule_network_services,
    "get_notification_schedule_servers": handle_get_notification_schedule_servers,
    "get_notification_schedule_server_groups": handle_get_notification_schedule_server_groups,
}
