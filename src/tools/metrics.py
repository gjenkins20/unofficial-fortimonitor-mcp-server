"""MCP tools for metrics operations."""

from typing import List, Dict
import logging

from mcp.types import Tool, TextContent
from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import FortiMonitorError, APIError, NotFoundError

logger = logging.getLogger(__name__)


def get_server_metrics_tool_definition() -> Tool:
    """Define the get_server_metrics MCP tool."""
    return Tool(
        name="get_server_metrics",
        description=(
            "Retrieve agent resource metrics for a specific server. "
            "Shows available monitoring resources (CPU, memory, disk, etc.)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description":"ID of the server to retrieve metrics for",
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 100,
                    "description":"Maximum number of resources to return (max 100)",
                },
                # REMOVED: full parameter - causes 500 errors in FortiMonitor API
            },
            "required": ["server_id"],
        },
    )


async def handle_get_server_metrics(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_server_metrics tool execution."""
    try:
        server_id = arguments["server_id"]
        limit = arguments.get("limit", 50)

        # Cap limit at 100 to avoid issues
        if limit > 100:
            logger.warning(f"Reducing limit from {limit} to 100")
            limit = 100

        logger.info(f"Getting metrics for server {server_id} (limit={limit})")

        # CRITICAL: Never use full=true - it causes HTTP 500 errors
        response = client.get_server_agent_resources(
            server_id=server_id,
            limit=limit,
            full=False  # Must be False - API bug with full=true
        )

        if not response.agent_resource_list:
            return [
                TextContent(
                    type="text",
                    text=f"No agent resources (metrics) found for server {server_id}.",
                )
            ]

        # Group resources by type
        resources_by_type: Dict[str, list] = {}
        for resource in response.agent_resource_list:
            res_type = resource.resource_type or "unknown"
            if res_type not in resources_by_type:
                resources_by_type[res_type] = []
            resources_by_type[res_type].append(resource)

        # Format results
        result_parts = [
            f"**Agent Resources for Server {server_id}**\n\n"
            f"Found {len(response.agent_resource_list)} resource(s):\n"
        ]

        for res_type, type_resources in resources_by_type.items():
            result_parts.append(
                f"\n**{res_type.upper()} Resources ({len(type_resources)})**:"
            )
            for resource in type_resources:
                # Try current_value first, then value field
                val = resource.current_value if resource.current_value is not None else resource.value
                current_val = (
                    f"{val} {resource.unit or ''}"
                    if val is not None
                    else "N/A"
                )
                status_info = f"  Status: {resource.status}\n" if resource.status else ""
                resource_info = (
                    f"\n  ID: {resource.id}\n"
                    f"  Name: {resource.name}\n"
                    f"  Label: {resource.label or 'N/A'}\n"
                    f"  Current Value: {current_val}\n"
                    f"{status_info}"
                    f"  Last Check: {resource.last_check or 'N/A'}\n"
                )
                result_parts.append(resource_info)

        return [TextContent(type="text", text="".join(result_parts))]

    except NotFoundError:
        logger.error(f"Server {server_id} not found")
        return [
            TextContent(
                type="text",
                text=f"Server {server_id} not found. Please verify the server ID.",
            )
        ]
    except APIError as e:
        # Provide context-aware error messages for API errors
        if e.status_code == 500:
            logger.error(f"FortiMonitor API error (500) for server {server_id}")
            return [
                TextContent(
                    type="text",
                    text=(
                        f"Unable to retrieve metrics for server {server_id}.\n\n"
                        f"Error: {str(e)}\n\n"
                        f"This may indicate:\n"
                        f"- Server doesn't have monitoring agents installed\n"
                        f"- Agent resources aren't configured\n"
                        f"- FortiMonitor API is experiencing issues\n\n"
                        f"Try: get_server_details to check server configuration"
                    ),
                )
            ]
        else:
            logger.error(f"FortiMonitor API error: {e}")
            return [
                TextContent(type="text", text=f"Error retrieving metrics: {str(e)}")
            ]
    except FortiMonitorError as e:
        logger.error(f"FortiMonitor error: {e}")
        return [TextContent(type="text", text=f"Error retrieving metrics: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in get_server_metrics")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]
