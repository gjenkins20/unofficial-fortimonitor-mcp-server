"""Server template management tools - Phase 2 Priority 3."""

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


def list_server_templates_tool_definition() -> Tool:
    """Return tool definition for listing server templates."""
    return Tool(
        name="list_server_templates",
        description=(
            "List all server monitoring templates. "
            "Templates define what metrics and services to monitor on a server."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description":"Maximum number of templates to return (default 50)"
                }
            }
        }
    )


def get_server_template_details_tool_definition() -> Tool:
    """Return tool definition for getting template details."""
    return Tool(
        name="get_server_template_details",
        description=(
            "Get detailed information about a specific server template, "
            "including the agent resource types and network services it monitors."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "template_id": {
                    "type": "integer",
                    "description":"ID of the server template"
                }
            },
            "required": ["template_id"]
        }
    )


def apply_template_to_server_tool_definition() -> Tool:
    """Return tool definition for applying a template to a server."""
    return Tool(
        name="apply_template_to_server",
        description=(
            "Apply a monitoring template to a server. "
            "This configures the server to be monitored according to the template's settings."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description":"ID of the server to configure"
                },
                "template_id": {
                    "type": "integer",
                    "description":"ID of the template to apply"
                }
            },
            "required": ["server_id", "template_id"]
        }
    )


def apply_template_to_group_tool_definition() -> Tool:
    """Return tool definition for applying a template to all servers in a group."""
    return Tool(
        name="apply_template_to_group",
        description=(
            "Apply a monitoring template to all servers in a server group. "
            "This is useful for standardizing monitoring across multiple servers."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description":"ID of the server group"
                },
                "template_id": {
                    "type": "integer",
                    "description":"ID of the template to apply"
                }
            },
            "required": ["group_id", "template_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_list_server_templates(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_server_templates tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing server templates (limit={limit})")

        response = client.list_server_templates(limit=limit)
        templates = response.server_template_list

        if not templates:
            return [TextContent(
                type="text",
                text="No server templates found."
            )]

        output_lines = [
            "**Server Templates**\n",
            f"Found {len(templates)} template(s):\n"
        ]

        for template in templates:
            output_lines.append(f"\n**{template.name}** (ID: {template.id})")
            if template.description:
                output_lines.append(f"  Description: {template.description}")

            # Count monitored items
            resource_count = len(template.agent_resource_types)
            service_count = len(template.network_services)
            output_lines.append(f"  Agent Resources: {resource_count}")
            output_lines.append(f"  Network Services: {service_count}")

        if response.total_count and response.total_count > len(templates):
            output_lines.append(f"\n(Showing {len(templates)} of {response.total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing templates: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing templates")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_server_template_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_server_template_details tool execution."""
    try:
        template_id = arguments["template_id"]

        logger.info(f"Getting details for template {template_id}")

        template = client.get_server_template_details(template_id)

        output_lines = [
            f"**Server Template: {template.name}** (ID: {template.id})\n"
        ]

        if template.description:
            output_lines.append(f"Description: {template.description}")

        if template.created:
            output_lines.append(f"Created: {template.created.strftime('%Y-%m-%d %H:%M')}")

        # List agent resource types
        if template.agent_resource_types:
            output_lines.append(f"\n**Agent Resource Types ({len(template.agent_resource_types)}):**")
            for i, resource_url in enumerate(template.agent_resource_types[:10]):
                # Extract resource type name from URL if possible
                match = re.search(r'/agent_resource_type/(\d+)', resource_url)
                if match:
                    output_lines.append(f"  - Resource Type ID: {match.group(1)}")
                else:
                    output_lines.append(f"  - {resource_url}")

            if len(template.agent_resource_types) > 10:
                output_lines.append(f"  ... and {len(template.agent_resource_types) - 10} more")

        # List network services
        if template.network_services:
            output_lines.append(f"\n**Network Services ({len(template.network_services)}):**")
            for i, service_url in enumerate(template.network_services[:10]):
                match = re.search(r'/network_service/(\d+)', service_url)
                if match:
                    output_lines.append(f"  - Network Service ID: {match.group(1)}")
                else:
                    output_lines.append(f"  - {service_url}")

            if len(template.network_services) > 10:
                output_lines.append(f"  ... and {len(template.network_services) - 10} more")

        # Notification group
        if template.notification_group:
            output_lines.append(f"\nNotification Group: {template.notification_group}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Template {arguments.get('template_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting template details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_apply_template_to_server(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle apply_template_to_server tool execution."""
    try:
        server_id = arguments["server_id"]
        template_id = arguments["template_id"]

        logger.info(f"Applying template {template_id} to server {server_id}")

        # Get server and template names for output
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"ID {server_id}"

        try:
            template = client.get_server_template_details(template_id)
            template_name = template.name
        except Exception:
            template_name = f"ID {template_id}"

        # Apply the template
        client.apply_template_to_server(server_id, template_id)

        return [TextContent(
            type="text",
            text=f"**Template Applied**\n\n"
                 f"Template '{template_name}' has been applied to server '{server_name}'.\n\n"
                 f"The server will now be monitored according to the template's configuration."
        )]

    except NotFoundError as e:
        return [TextContent(
            type="text",
            text=f"Error: Server or template not found. {str(e)}"
        )]
    except APIError as e:
        logger.error(f"API error applying template: {e}")
        return [TextContent(type="text", text=f"Error applying template: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_apply_template_to_group(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle apply_template_to_group tool execution."""
    try:
        group_id = arguments["group_id"]
        template_id = arguments["template_id"]

        logger.info(f"Applying template {template_id} to group {group_id}")

        # Get group details
        group = client.get_server_group_details(group_id)

        if not group.servers:
            return [TextContent(
                type="text",
                text=f"Error: Server group '{group.name}' has no servers."
            )]

        # Get template name
        try:
            template = client.get_server_template_details(template_id)
            template_name = template.name
        except Exception:
            template_name = f"ID {template_id}"

        # Apply template to each server
        success_count = 0
        failed_servers = []

        for server_url in group.servers:
            match = re.search(r'/server/(\d+)', server_url)
            if match:
                server_id = int(match.group(1))
                try:
                    client.apply_template_to_server(server_id, template_id)
                    success_count += 1
                except Exception as e:
                    failed_servers.append((server_id, str(e)))

        output_lines = [
            f"**Template Applied to Group**\n",
            f"Group: {group.name}",
            f"Template: {template_name}",
            f"Servers Processed: {len(group.servers)}",
            f"Successful: {success_count}",
            f"Failed: {len(failed_servers)}"
        ]

        if failed_servers:
            output_lines.append("\n**Failed Applications:**")
            for server_id, error in failed_servers[:10]:
                output_lines.append(f"  - Server {server_id}: {error}")
            if len(failed_servers) > 10:
                output_lines.append(f"  ... and {len(failed_servers) - 10} more")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server group {arguments.get('group_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error applying template to group: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]
