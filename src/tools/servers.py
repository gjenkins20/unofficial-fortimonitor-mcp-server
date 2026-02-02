"""MCP tools for server operations."""

from typing import Optional, List
import logging

from mcp.types import Tool, TextContent
from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import FortiMonitorError

logger = logging.getLogger(__name__)


def get_servers_tool_definition() -> Tool:
    """Define the get_servers MCP tool."""
    return Tool(
        name="get_servers",
        description=(
            "List all monitored servers in FortiMonitor. "
            "Supports filtering by name, FQDN, server group, status, and tags."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Filter by server name (partial match)",
                },
                "fqdn": {"type": "string", "description": "Filter by FQDN"},
                "server_group": {
                    "type": "integer",
                    "description": "Filter by server group ID",
                },
                "status": {"type": "string", "description": "Filter by server status"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by tags",
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 1000,
                    "description": "Maximum number of servers to return",
                },
                "offset": {
                    "type": "integer",
                    "default": 0,
                    "minimum": 0,
                    "description": "Offset for pagination",
                },
            },
        },
    )


async def handle_get_servers(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_servers tool execution."""
    try:
        name = arguments.get("name")
        fqdn = arguments.get("fqdn")
        server_group = arguments.get("server_group")
        status = arguments.get("status")
        tags = arguments.get("tags")
        limit = arguments.get("limit", 50)
        offset = arguments.get("offset", 0)

        logger.info(f"Getting servers: name={name}, status={status}, limit={limit}")

        response = client.get_servers(
            name=name,
            fqdn=fqdn,
            server_group=server_group,
            status=status,
            tags=tags,
            limit=limit,
            offset=offset,
        )

        if not response.server_list:
            return [
                TextContent(
                    type="text",
                    text="No servers found matching the specified criteria.",
                )
            ]

        # Format server list
        server_list = []
        for server in response.server_list:
            server_info = (
                f"**Server ID: {server.id}**\n"
                f"Name: {server.name}\n"
                f"FQDN: {server.fqdn or 'N/A'}\n"
                f"Status: {server.status or 'N/A'}\n"
                f"Tags: {', '.join(server.tags) if server.tags else 'None'}\n"
            )
            server_list.append(server_info)

        # Add pagination info
        result_text = (
            f"Found {response.total_count or len(response.server_list)} total server(s) "
            f"(showing {len(response.server_list)} starting at offset {response.offset}):\n\n"
        )
        result_text += "\n---\n".join(server_list)

        if response.next:
            result_text += (
                f"\n\n*More results available (use offset={response.offset + response.limit})*"
            )

        return [TextContent(type="text", text=result_text)]

    except FortiMonitorError as e:
        logger.error(f"FortiMonitor API error: {e}")
        return [TextContent(type="text", text=f"Error retrieving servers: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in get_servers")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


def get_server_details_tool_definition() -> Tool:
    """Define the get_server_details MCP tool."""
    return Tool(
        name="get_server_details",
        description="Get detailed information about a specific server by ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server to retrieve",
                },
                "full": {
                    "type": "boolean",
                    "default": False,
                    "description": "Resolve all URLs to actual objects",
                },
            },
            "required": ["server_id"],
        },
    )


async def handle_get_server_details(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_server_details tool execution."""
    try:
        server_id = arguments["server_id"]
        full = arguments.get("full", False)

        logger.info(f"Getting details for server {server_id}")

        server = client.get_server_details(server_id, full=full)

        # Format detailed server information
        details = (
            f"**Server Details for ID {server.id}**\n\n"
            f"Name: {server.name}\n"
            f"FQDN: {server.fqdn or 'N/A'}\n"
            f"Description: {server.description or 'N/A'}\n"
            f"Status: {server.status or 'N/A'}\n"
            f"Server Key: {server.server_key or 'N/A'}\n"
            f"Partner Server ID: {server.partner_server_id or 'N/A'}\n"
            f"Tags: {', '.join(server.tags) if server.tags else 'None'}\n"
            f"Created: {server.created or 'N/A'}\n"
            f"Updated: {server.updated or 'N/A'}\n"
        )

        if server.attributes:
            details += "\n**Attributes:**\n"
            attr_dict = server.get_attributes_dict()
            for key, value in attr_dict.items():
                details += f"  - {key}: {value}\n"

        return [TextContent(type="text", text=details)]

    except FortiMonitorError as e:
        logger.error(f"FortiMonitor API error: {e}")
        return [
            TextContent(type="text", text=f"Error retrieving server details: {str(e)}")
        ]
    except Exception as e:
        logger.exception("Unexpected error in get_server_details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]
