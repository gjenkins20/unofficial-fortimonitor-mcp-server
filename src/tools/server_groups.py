"""Server group management tools - Phase 2 Priority 3."""

import asyncio
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
            "List all server groups with their names and IDs. "
            "Server groups help organize servers for easier management and monitoring. "
            "This tool also fetches the actual member count for each group. "
            "For full server details within a group, use get_server_group_details instead."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description":"Maximum number of groups to return (default 50)"
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
            "including the complete list of member servers and their network services. "
            "Use this tool to find out how many servers are in a group or to see "
            "which servers belong to a group."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description":"ID of the server group"
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
                    "description":"Optional list of server IDs to add to the group"
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
                    "description":"ID of the server group"
                },
                "server_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description":"List of server IDs to add to the group"
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
                    "description":"ID of the server group"
                },
                "server_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description":"List of server IDs to remove from the group"
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
                    "description":"ID of the server group to delete"
                }
            },
            "required": ["group_id"]
        }
    )


def update_server_group_tool_definition() -> Tool:
    """Return tool definition for updating a server group."""
    return Tool(
        name="update_server_group",
        description=(
            "Update server group name and/or description without recreating the group. "
            "Preserves all existing server memberships."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "ID of the server group to update"
                },
                "name": {
                    "type": "string",
                    "description": "New group name (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New group description (optional)"
                }
            },
            "required": ["group_id"]
        }
    )


def get_server_network_services_tool_definition() -> Tool:
    """Return tool definition for getting server network services."""
    return Tool(
        name="get_server_network_services",
        description=(
            "List network services (DNS checks, HTTP checks, TCP checks, etc.) "
            "monitored on a specific server. Network services are monitoring checks "
            "that run against the server from external monitoring nodes."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of services to return (default 50)"
                }
            },
            "required": ["server_id"]
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

        # Fetch actual member counts concurrently for all groups.
        # The list/detail API endpoints do NOT return server membership data,
        # so we must query /server_group/{id}/server for each group.
        # Using asyncio.to_thread for concurrent execution since the client
        # is synchronous (requests-based).
        def _fetch_count(group_id):
            """Fetch server count for a single group."""
            try:
                resp = client.get_server_group_servers(group_id, limit=1)
                return resp.get("meta", {}).get("total_count", 0)
            except Exception as e:
                logger.warning(
                    f"Could not fetch member count for group {group_id}: {e}"
                )
                return None

        # Launch all count fetches concurrently
        count_tasks = [
            asyncio.to_thread(_fetch_count, group.id) for group in groups
        ]
        counts = await asyncio.gather(*count_tasks)

        for group, count in zip(groups, counts):
            output_lines.append(f"\n**{group.name}** (ID: {group.id})")
            if group.description:
                output_lines.append(f"  Description: {group.description}")

            if count is not None:
                output_lines.append(f"  Servers: {count}")
            else:
                output_lines.append("  Servers: (unable to retrieve count)")

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

        logger.info(f"Getting complete details for server group {group_id}")

        # Use the enhanced method that also fetches network services
        result = client.get_group_members_complete(group_id)
        group = result["group"]

        output_lines = [
            f"**Server Group: {group.name}** (ID: {group.id})\n"
        ]

        if group.description:
            output_lines.append(f"Description: {group.description}")

        output_lines.append(f"Total Servers: {result['total_servers']}")
        output_lines.append(f"Total Network Services: {result['total_network_services']}")
        output_lines.append(f"Total Monitored Instances: {result['total_instances']}")

        discovery = result.get("discovery_method", "unknown")
        if discovery == "server_group_filter":
            output_lines.append(
                "Note: Members discovered via server_group filter "
                "(group server endpoint was unavailable)"
            )

        if group.created:
            output_lines.append(f"Created: {group.created.strftime('%Y-%m-%d %H:%M')}")

        # List servers with their network services
        if result["servers"]:
            output_lines.append("\n**Servers in Group:**")

            for i, srv in enumerate(result["servers"][:20]):
                status_str = f" [{srv['status']}]" if srv.get("status") else ""
                name = srv.get("name") or f"Server {srv['id']}"
                output_lines.append(f"\n  **{name}** (ID: {srv['id']}){status_str}")

                if srv.get("fqdn"):
                    output_lines.append(f"    FQDN: {srv['fqdn']}")

                # Show network services for this server
                if srv.get("network_services"):
                    output_lines.append(f"    Network Services ({len(srv['network_services'])}):")
                    for ns in srv["network_services"][:10]:
                        ns_name = ns.display_name
                        ns_status = f" [{ns.status}]" if ns.status else ""
                        ns_port = f" port:{ns.port}" if ns.port else ""
                        output_lines.append(f"      - {ns_name}{ns_port}{ns_status}")

                    if len(srv["network_services"]) > 10:
                        output_lines.append(
                            f"      ... and {len(srv['network_services']) - 10} more"
                        )

            if len(result["servers"]) > 20:
                output_lines.append(
                    f"\n  ... and {len(result['servers']) - 20} more servers"
                )

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


async def handle_update_server_group(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_server_group tool execution."""
    try:
        group_id = arguments["group_id"]
        new_name = arguments.get("name")
        new_description = arguments.get("description")

        if not new_name and new_description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name' or 'description' must be provided."
            )]

        logger.info(f"Updating server group {group_id}")

        # Get current group for comparison
        current_group = client.get_server_group_details(group_id)
        current_name = current_group.name

        # Perform update
        updated_group = client.update_server_group(
            group_id,
            name=new_name,
            description=new_description
        )

        output_lines = ["**Server Group Updated**\n"]

        if new_name and new_name != current_name:
            output_lines.append(f"Name: '{current_name}' -> '{new_name}'")
        elif new_name:
            output_lines.append(f"Name: {new_name} (unchanged)")

        if new_description is not None:
            output_lines.append(f"Description: Updated")

        output_lines.append(f"Group ID: {group_id}")
        output_lines.append(f"Servers: {updated_group.server_count} (preserved)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server group {arguments.get('group_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating server group: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_server_network_services(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_server_network_services tool execution."""
    try:
        server_id = arguments["server_id"]
        limit = arguments.get("limit", 50)

        logger.info(f"Getting network services for server {server_id}")

        # Get server name for context
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"Server {server_id}"

        # Get network services
        response = client.get_server_network_services(server_id, limit=limit)
        services = response.network_service_list

        if not services:
            return [TextContent(
                type="text",
                text=f"No network services found for {server_name} (ID: {server_id})."
            )]

        output_lines = [
            f"**Network Services for {server_name}** (ID: {server_id})\n",
            f"Found {len(services)} service(s):\n"
        ]

        for ns in services:
            ns_name = ns.display_name
            output_lines.append(f"\n  **{ns_name}** (ID: {ns.id})")

            if ns.status:
                output_lines.append(f"    Status: {ns.status}")
            if ns.severity:
                output_lines.append(f"    Severity: {ns.severity}")
            if ns.port:
                output_lines.append(f"    Port: {ns.port}")
            if ns.frequency:
                output_lines.append(f"    Check Frequency: {ns.frequency}s")

        if response.total_count and response.total_count > len(services):
            output_lines.append(
                f"\n(Showing {len(services)} of {response.total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting network services: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]
