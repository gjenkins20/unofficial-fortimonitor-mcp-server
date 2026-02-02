"""Agent resource management tools - Phase 2 Priority 4."""

import logging
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def list_agent_resource_types_tool_definition() -> Tool:
    """Return tool definition for listing agent resource types."""
    return Tool(
        name="list_agent_resource_types",
        description=(
            "List all available agent resource types (metric types). "
            "These are the different types of metrics that can be monitored "
            "(e.g., CPU, memory, disk, network, custom metrics)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of types to return (default 50)"
                }
            }
        }
    )


def get_agent_resource_type_details_tool_definition() -> Tool:
    """Return tool definition for getting agent resource type details."""
    return Tool(
        name="get_agent_resource_type_details",
        description=(
            "Get detailed information about a specific agent resource type, "
            "including its category, unit of measurement, and monitoring configuration."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "type_id": {
                    "type": "integer",
                    "description": "The ID of the agent resource type"
                }
            },
            "required": ["type_id"]
        }
    )


def list_server_resources_tool_definition() -> Tool:
    """Return tool definition for listing server resources."""
    return Tool(
        name="list_server_resources",
        description=(
            "List all agent resources (metrics) being monitored on a specific server. "
            "Shows what metrics are actively being collected."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of resources to return (default 50)"
                }
            },
            "required": ["server_id"]
        }
    )


def get_resource_details_tool_definition() -> Tool:
    """Return tool definition for getting resource details."""
    return Tool(
        name="get_resource_details",
        description=(
            "Get detailed information about a specific agent resource "
            "(monitored metric on a server), including current value and thresholds."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server"
                },
                "resource_id": {
                    "type": "integer",
                    "description": "The ID of the agent resource"
                }
            },
            "required": ["server_id", "resource_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_list_agent_resource_types(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_agent_resource_types tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing agent resource types (limit={limit})")

        response = client.list_agent_resource_types(limit=limit)
        types = response.agent_resource_type_list

        if not types:
            return [TextContent(
                type="text",
                text="No agent resource types found."
            )]

        # Group by category if available
        by_category = {}
        for resource_type in types:
            category = resource_type.category or "Other"
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(resource_type)

        output_lines = [
            f"**Agent Resource Types**\n",
            f"Found {len(types)} type(s):\n"
        ]

        for category, category_types in sorted(by_category.items()):
            output_lines.append(f"\n**{category.title()}** ({len(category_types)} types):")

            for rt in category_types[:10]:  # Show first 10 per category
                unit_str = f" ({rt.unit})" if rt.unit else ""
                output_lines.append(f"  - {rt.name}{unit_str} (ID: {rt.id})")

            if len(category_types) > 10:
                output_lines.append(f"  ... and {len(category_types) - 10} more")

        if response.total_count and response.total_count > len(types):
            output_lines.append(f"\n(Showing {len(types)} of {response.total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing agent resource types: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_agent_resource_type_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_agent_resource_type_details tool execution."""
    try:
        type_id = arguments["type_id"]

        logger.info(f"Getting agent resource type details {type_id}")

        resource_type = client.get_agent_resource_type_details(type_id)

        output_lines = [
            f"**Agent Resource Type: {resource_type.name}** (ID: {resource_type.id})\n"
        ]

        if resource_type.category:
            output_lines.append(f"Category: {resource_type.category}")

        if resource_type.unit:
            output_lines.append(f"Unit: {resource_type.unit}")

        if resource_type.monitoring_type:
            output_lines.append(f"Monitoring Type: {resource_type.monitoring_type}")

        if resource_type.description:
            output_lines.append(f"\nDescription: {resource_type.description}")

        if resource_type.created:
            output_lines.append(f"\nCreated: {resource_type.created.strftime('%Y-%m-%d %H:%M')}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Agent resource type {arguments.get('type_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting resource type details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_server_resources(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_server_resources tool execution."""
    try:
        server_id = arguments["server_id"]
        limit = arguments.get("limit", 50)

        logger.info(f"Listing agent resources for server {server_id}")

        # Get server details for context
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"Server {server_id}"

        # Get agent resources
        response = client.list_server_agent_resources(server_id, limit=limit)
        resources = response.agent_resource_list

        if not resources:
            return [TextContent(
                type="text",
                text=f"No agent resources found for {server_name}."
            )]

        output_lines = [
            f"**Agent Resources for {server_name}**\n",
            f"Found {len(resources)} monitored metric(s):\n"
        ]

        for resource in resources:
            output_lines.append(f"\n**{resource.name}** (ID: {resource.id})")

            if resource.resource_type:
                output_lines.append(f"  Type: {resource.resource_type}")

            if resource.current_value is not None:
                unit = resource.unit or ""
                output_lines.append(f"  Current Value: {resource.current_value} {unit}".strip())

            if resource.status:
                output_lines.append(f"  Status: {resource.status}")

            if resource.last_check:
                output_lines.append(f"  Last Check: {resource.last_check.strftime('%Y-%m-%d %H:%M')}")

        if response.total_count and response.total_count > len(resources):
            output_lines.append(f"\n(Showing {len(resources)} of {response.total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error listing server resources: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_resource_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_resource_details tool execution."""
    try:
        server_id = arguments["server_id"]
        resource_id = arguments["resource_id"]

        logger.info(f"Getting agent resource details {resource_id} for server {server_id}")

        # Get all resources for the server and find the one we want
        response = client.list_server_agent_resources(server_id, limit=500)

        resource = None
        for r in response.agent_resource_list:
            if r.id == resource_id:
                resource = r
                break

        if not resource:
            return [TextContent(
                type="text",
                text=f"Error: Agent resource {resource_id} not found on server {server_id}."
            )]

        # Get server name for context
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"Server {server_id}"

        output_lines = [
            f"**Agent Resource: {resource.name}** (ID: {resource.id})\n",
            f"Server: {server_name}"
        ]

        if resource.resource_type:
            output_lines.append(f"Resource Type: {resource.resource_type}")

        if resource.current_value is not None:
            unit = resource.unit or ""
            output_lines.append(f"Current Value: {resource.current_value} {unit}".strip())

        if resource.status:
            output_lines.append(f"Status: {resource.status}")

        if resource.label:
            output_lines.append(f"Label: {resource.label}")

        if resource.last_check:
            output_lines.append(f"Last Check: {resource.last_check.strftime('%Y-%m-%d %H:%M:%S')}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting resource details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]
