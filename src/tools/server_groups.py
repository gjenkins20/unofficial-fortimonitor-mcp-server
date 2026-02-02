"""Server group management tools - Phase 2 Priority 3."""

import logging
import re
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def list_server_groups_tool_definition() -> Tool:
    """Return tool definition for listing server groups."""
    return Tool(
        name="list_server_groups",
        description=(
            "List all server groups. "
            "Server groups help organize servers for easier management and monitoring."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of groups to return (default 50)"
                }
            }
        }
    )


def get_server_group_details_tool_definition() -> Tool:
    """Return tool definition for getting server group details."""
    return Tool(
        name="get_server_group_details",
        description=(
            "Get detailed information about a specific server group, "
            "including the list of servers in the group."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "ID of the server group"
                }
            },
            "required": ["group_id"]
        }
    )


def create_server_group_tool_definition() -> Tool:
    """Return tool definition for creating a server group."""
    return Tool(
        name="create_server_group",
        description=(
            "Create a new server group. "
            "Groups help organize servers by function, location, or other criteria."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the new server group"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the group"
                },
                "server_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Optional list of server IDs to add to the group"
                }
            },
            "required": ["name"]
        }
    )


def add_servers_to_group_tool_definition() -> Tool:
    """Return tool definition for adding servers to a group."""
    return Tool(
        name="add_servers_to_group",
        description=(
            "Add one or more servers to an existing server group. "
            "Servers already in the group will not be duplicated."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "ID of the server group"
                },
                "server_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List of server IDs to add to the group"
                }
            },
            "required": ["group_id", "server_ids"]
        }
    )


def remove_servers_from_group_tool_definition() -> Tool:
    """Return tool definition for removing servers from a group."""
    return Tool(
        name="remove_servers_from_group",
        description=(
            "Remove one or more servers from a server group. "
            "The servers themselves are not deleted, only removed from the group."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "ID of the server group"
                },
                "server_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List of server IDs to remove from the group"
                }
            },
            "required": ["group_id", "server_ids"]
        }
    )


def delete_server_group_tool_definition() -> Tool:
    """Return tool definition for deleting a server group."""
    return Tool(
        name="delete_server_group",
        description=(
            "Delete a server group. "
            "The servers in the group are NOT deleted, only the group itself."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "ID of the server group to delete"
                }
            },
            "required": ["group_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_list_server_groups(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_server_groups tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing server groups (limit={limit})")

        response = client.list_server_groups(limit=limit)
        groups = response.server_group_list

        if not groups:
            return [TextContent(
                type="text",
                text="No server groups found."
            )]

        output_lines = [
            "**Server Groups**\n",
            f"Found {len(groups)} group(s):\n"
        ]

        for group in groups:
            output_lines.append(f"\n**{group.name}** (ID: {group.id})")
            if group.description:
                output_lines.append(f"  Description: {group.description}")
            output_lines.append(f"  Servers: {group.server_count}")

        if response.total_count and response.total_count > len(groups):
            output_lines.append(f"\n(Showing {len(groups)} of {response.total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing server groups: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing server groups")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_server_group_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_server_group_details tool execution."""
    try:
        group_id = arguments["group_id"]

        logger.info(f"Getting details for server group {group_id}")

        group = client.get_server_group_details(group_id)

        output_lines = [
            f"**Server Group: {group.name}** (ID: {group.id})\n"
        ]

        if group.description:
            output_lines.append(f"Description: {group.description}")

        output_lines.append(f"Total Servers: {group.server_count}")

        if group.created:
            output_lines.append(f"Created: {group.created.strftime('%Y-%m-%d %H:%M')}")

        # List servers in the group
        if group.servers:
            output_lines.append("\n**Servers in Group:**")

            # Extract server IDs and try to get details
            for i, server_url in enumerate(group.servers[:20]):  # Limit to first 20
                match = re.search(r'/server/(\d+)', server_url)
                if match:
                    server_id = int(match.group(1))
                    try:
                        server = client.get_server_details(server_id)
                        output_lines.append(f"  - {server.name} (ID: {server_id})")
                    except Exception:
                        output_lines.append(f"  - Server ID: {server_id}")

            if len(group.servers) > 20:
                output_lines.append(f"  ... and {len(group.servers) - 20} more servers")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server group {arguments.get('group_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting server group details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_server_group(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_server_group tool execution."""
    try:
        name = arguments["name"]
        description = arguments.get("description")
        server_ids = arguments.get("server_ids", [])

        logger.info(f"Creating server group: {name}")

        group = client.create_server_group(
            name=name,
            description=description,
            server_ids=server_ids if server_ids else None
        )

        output_lines = [
            f"**Server Group Created**\n",
            f"Name: {group.name}"
        ]

        # Add ID if available
        if group.id:
            output_lines.append(f"ID: {group.id}")

        if group.description:
            output_lines.append(f"Description: {group.description}")

        server_count = len(server_ids) if server_ids else 0
        if server_count > 0:
            output_lines.append(f"Servers Added: {server_count}")
        else:
            output_lines.append("Servers: Empty group (add servers later)")

        # Add note if ID wasn't immediately available
        if not group.id:
            output_lines.append("\nNote: Group created. Use 'list_server_groups' to find the ID.")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating server group: {e}")
        return [TextContent(type="text", text=f"Error creating group: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_add_servers_to_group(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle add_servers_to_group tool execution."""
    try:
        group_id = arguments["group_id"]
        server_ids = arguments["server_ids"]

        if not server_ids:
            return [TextContent(
                type="text",
                text="Error: No server IDs provided"
            )]

        logger.info(f"Adding {len(server_ids)} servers to group {group_id}")

        # Get group before to compare
        group_before = client.get_server_group_details(group_id)
        count_before = group_before.server_count

        # Add servers
        group = client.add_servers_to_group(group_id, server_ids)

        servers_added = group.server_count - count_before

        output_lines = [
            f"**Servers Added to Group**\n",
            f"Group: {group.name} (ID: {group.id})",
            f"Servers Added: {servers_added}",
            f"Total Servers in Group: {group.server_count}"
        ]

        if servers_added < len(server_ids):
            output_lines.append(
                f"\nNote: {len(server_ids) - servers_added} server(s) were already in the group"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server group {arguments.get('group_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error adding servers to group: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_remove_servers_from_group(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle remove_servers_from_group tool execution."""
    try:
        group_id = arguments["group_id"]
        server_ids = arguments["server_ids"]

        if not server_ids:
            return [TextContent(
                type="text",
                text="Error: No server IDs provided"
            )]

        logger.info(f"Removing {len(server_ids)} servers from group {group_id}")

        # Get group before to compare
        group_before = client.get_server_group_details(group_id)
        count_before = group_before.server_count

        # Remove servers
        group = client.remove_servers_from_group(group_id, server_ids)

        servers_removed = count_before - group.server_count

        output_lines = [
            f"**Servers Removed from Group**\n",
            f"Group: {group.name} (ID: {group.id})",
            f"Servers Removed: {servers_removed}",
            f"Remaining Servers: {group.server_count}"
        ]

        if servers_removed < len(server_ids):
            output_lines.append(
                f"\nNote: {len(server_ids) - servers_removed} server(s) were not in the group"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server group {arguments.get('group_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error removing servers from group: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_server_group(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_server_group tool execution."""
    try:
        group_id = arguments["group_id"]

        logger.info(f"Deleting server group {group_id}")

        # Get group name before deleting
        try:
            group = client.get_server_group_details(group_id)
            group_name = group.name
        except Exception:
            group_name = f"ID {group_id}"

        # Delete the group
        client.delete_server_group(group_id)

        return [TextContent(
            type="text",
            text=f"**Server Group Deleted**\n\nGroup '{group_name}' has been deleted.\n\n"
                 f"Note: Servers that were in this group have NOT been deleted."
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server group {arguments.get('group_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting server group: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]
