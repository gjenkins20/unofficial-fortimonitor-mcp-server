"""Enhanced server group tools - additional server group operations."""

import logging
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def list_server_group_servers_tool_definition() -> Tool:
    """Return tool definition for listing servers in a specific group."""
    return Tool(
        name="list_server_group_servers",
        description=(
            "List servers that belong to a specific server group. "
            "Returns server details including name, ID, FQDN, and status."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "ID of the server group"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of servers to return (default 50)"
                }
            },
            "required": ["group_id"]
        }
    )


def apply_monitoring_policy_to_group_tool_definition() -> Tool:
    """Return tool definition for applying a monitoring policy to a group."""
    return Tool(
        name="apply_monitoring_policy_to_group",
        description=(
            "Apply a monitoring policy (server template) to all servers in a group. "
            "This configures all group members to be monitored according to the template."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "ID of the server group"
                },
                "template_id": {
                    "type": "integer",
                    "description": "ID of the server template to apply as a monitoring policy"
                }
            },
            "required": ["group_id", "template_id"]
        }
    )


def list_server_group_compound_services_tool_definition() -> Tool:
    """Return tool definition for listing compound services in a group."""
    return Tool(
        name="list_server_group_compound_services",
        description=(
            "List compound services associated with a server group. "
            "Compound services aggregate multiple checks into a single service view."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "ID of the server group"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of compound services to return (default 50)"
                }
            },
            "required": ["group_id"]
        }
    )


def list_child_server_groups_tool_definition() -> Tool:
    """Return tool definition for listing child server groups."""
    return Tool(
        name="list_child_server_groups",
        description=(
            "List child server groups nested under a parent server group. "
            "Server groups can be organized hierarchically."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "ID of the parent server group"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of child groups to return (default 50)"
                }
            },
            "required": ["group_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_list_server_group_servers(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_server_group_servers tool execution."""
    try:
        group_id = arguments["group_id"]
        limit = arguments.get("limit", 50)

        logger.info(f"Listing servers in group {group_id} (limit={limit})")

        response = client.get_server_group_servers(group_id, limit=limit)
        server_list = response.get("server_list", [])
        meta = response.get("meta", {})

        if not server_list:
            return [TextContent(
                type="text",
                text=f"No servers found in server group {group_id}."
            )]

        total_count = meta.get("total_count", len(server_list))

        output_lines = [
            f"**Servers in Group {group_id}**\n",
            f"Found {len(server_list)} server(s) (total: {total_count}):\n"
        ]

        for server in server_list:
            name = server.get("name", "Unknown")
            # Extract ID from URL if present
            server_url = server.get("url", "")
            server_id = "N/A"
            if server_url:
                parts = server_url.rstrip("/").split("/")
                if parts:
                    server_id = parts[-1]

            fqdn = server.get("fqdn", "N/A")
            status = server.get("status", "unknown")

            output_lines.append(f"\n**{name}** (ID: {server_id})")
            output_lines.append(f"  FQDN: {fqdn}")
            output_lines.append(f"  Status: {status}")

        if total_count > len(server_list):
            output_lines.append(
                f"\n(Showing {len(server_list)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server group {arguments.get('group_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error listing group servers: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing group servers")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_apply_monitoring_policy_to_group(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle apply_monitoring_policy_to_group tool execution."""
    try:
        group_id = arguments["group_id"]
        template_id = arguments["template_id"]

        logger.info(f"Applying monitoring policy (template {template_id}) to group {group_id}")

        # Get group and template names for output
        try:
            group = client.get_server_group_details(group_id)
            group_name = group.name
        except Exception:
            group_name = f"ID {group_id}"

        try:
            template = client.get_server_template_details(template_id)
            template_name = template.name
        except Exception:
            template_name = f"ID {template_id}"

        # Apply monitoring policy
        client._request(
            "POST",
            f"server_group/{group_id}/apply_monitoring_policy",
            json_data={
                "server_template": f"{client.base_url}/server_template/{template_id}"
            }
        )

        return [TextContent(
            type="text",
            text=(
                f"**Monitoring Policy Applied**\n\n"
                f"Template '{template_name}' has been applied to all servers "
                f"in group '{group_name}'.\n\n"
                f"All servers in the group will now be monitored according "
                f"to the template's configuration."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server group or template not found."
        )]
    except APIError as e:
        logger.error(f"API error applying monitoring policy: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error applying monitoring policy")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_server_group_compound_services(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_server_group_compound_services tool execution."""
    try:
        group_id = arguments["group_id"]
        limit = arguments.get("limit", 50)

        logger.info(f"Listing compound services for group {group_id}")

        response = client._request(
            "GET",
            f"server_group/{group_id}/compound_service",
            params={"limit": limit}
        )

        services = response.get("compound_service_list", [])
        meta = response.get("meta", {})

        if not services:
            return [TextContent(
                type="text",
                text=f"No compound services found for server group {group_id}."
            )]

        total_count = meta.get("total_count", len(services))

        output_lines = [
            f"**Compound Services in Group {group_id}**\n",
            f"Found {len(services)} compound service(s):\n"
        ]

        for svc in services:
            name = svc.get("name", "Unknown")
            svc_url = svc.get("url", "")
            svc_id = "N/A"
            if svc_url:
                parts = svc_url.rstrip("/").split("/")
                if parts:
                    svc_id = parts[-1]

            description = svc.get("description", "")

            output_lines.append(f"\n**{name}** (ID: {svc_id})")
            if description:
                output_lines.append(f"  Description: {description}")

        if total_count > len(services):
            output_lines.append(
                f"\n(Showing {len(services)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server group {arguments.get('group_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error listing compound services: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing compound services")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_child_server_groups(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_child_server_groups tool execution."""
    try:
        group_id = arguments["group_id"]
        limit = arguments.get("limit", 50)

        logger.info(f"Listing child server groups for group {group_id}")

        response = client._request(
            "GET",
            f"server_group/{group_id}/server_group",
            params={"limit": limit}
        )

        children = response.get("server_group_list", [])
        meta = response.get("meta", {})

        if not children:
            return [TextContent(
                type="text",
                text=f"No child server groups found under group {group_id}."
            )]

        total_count = meta.get("total_count", len(children))

        output_lines = [
            f"**Child Server Groups under Group {group_id}**\n",
            f"Found {len(children)} child group(s):\n"
        ]

        for child in children:
            name = child.get("name", "Unknown")
            child_url = child.get("url", "")
            child_id = "N/A"
            if child_url:
                parts = child_url.rstrip("/").split("/")
                if parts:
                    child_id = parts[-1]

            description = child.get("description", "")
            servers = child.get("servers", [])

            output_lines.append(f"\n**{name}** (ID: {child_id})")
            if description:
                output_lines.append(f"  Description: {description}")
            output_lines.append(f"  Servers: {len(servers)}")

        if total_count > len(children):
            output_lines.append(
                f"\n(Showing {len(children)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server group {arguments.get('group_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error listing child groups: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing child groups")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

SERVER_GROUPS_ENHANCED_TOOL_DEFINITIONS = {
    "list_server_group_servers": list_server_group_servers_tool_definition,
    "apply_monitoring_policy_to_group": apply_monitoring_policy_to_group_tool_definition,
    "list_server_group_compound_services": list_server_group_compound_services_tool_definition,
    "list_child_server_groups": list_child_server_groups_tool_definition,
}

SERVER_GROUPS_ENHANCED_HANDLERS = {
    "list_server_group_servers": handle_list_server_group_servers,
    "apply_monitoring_policy_to_group": handle_apply_monitoring_policy_to_group,
    "list_server_group_compound_services": handle_list_server_group_compound_services,
    "list_child_server_groups": handle_list_child_server_groups,
}
