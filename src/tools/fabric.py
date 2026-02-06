"""Fabric connection management tools for FortiMonitor."""

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


def list_fabric_connections_tool_definition() -> Tool:
    """Return tool definition for listing fabric connections."""
    return Tool(
        name="list_fabric_connections",
        description=(
            "List all fabric connections in FortiMonitor. "
            "Fabric connections represent integrations between FortiMonitor "
            "and other Fortinet or third-party systems."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of fabric connections to return (default 50)"
                }
            }
        }
    )


def get_fabric_connection_details_tool_definition() -> Tool:
    """Return tool definition for getting fabric connection details."""
    return Tool(
        name="get_fabric_connection_details",
        description=(
            "Get detailed information about a specific fabric connection, "
            "including its configuration and status."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "connection_id": {
                    "type": "integer",
                    "description": "ID of the fabric connection"
                }
            },
            "required": ["connection_id"]
        }
    )


def create_fabric_connection_tool_definition() -> Tool:
    """Return tool definition for creating a fabric connection."""
    return Tool(
        name="create_fabric_connection",
        description=(
            "Create a new fabric connection in FortiMonitor. "
            "Fabric connections integrate FortiMonitor with other systems."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the fabric connection"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the fabric connection"
                }
            },
            "required": ["name"]
        }
    )


def delete_fabric_connection_tool_definition() -> Tool:
    """Return tool definition for deleting a fabric connection."""
    return Tool(
        name="delete_fabric_connection",
        description=(
            "Delete a fabric connection from FortiMonitor. "
            "This permanently removes the connection and its configuration."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "connection_id": {
                    "type": "integer",
                    "description": "ID of the fabric connection to delete"
                }
            },
            "required": ["connection_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_list_fabric_connections(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_fabric_connections tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing fabric connections (limit={limit})")

        response = client._request(
            "GET", "fabric_connection", params={"limit": limit}
        )
        connections = response.get("fabric_connection_list", [])
        meta = response.get("meta", {})

        if not connections:
            return [TextContent(type="text", text="No fabric connections found.")]

        total_count = meta.get("total_count", len(connections))

        output_lines = [
            "**Fabric Connections**\n",
            f"Found {len(connections)} fabric connection(s):\n"
        ]

        for conn in connections:
            name = conn.get("name", "Unknown")
            conn_id = _extract_id_from_url(conn.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {conn_id})")
            if conn.get("description"):
                output_lines.append(f"  Description: {conn['description']}")
            if conn.get("status"):
                output_lines.append(f"  Status: {conn['status']}")

        if total_count > len(connections):
            output_lines.append(
                f"\n(Showing {len(connections)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing fabric connections: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing fabric connections")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_fabric_connection_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_fabric_connection_details tool execution."""
    try:
        connection_id = arguments["connection_id"]

        logger.info(f"Getting fabric connection details for {connection_id}")

        response = client._request(
            "GET", f"fabric_connection/{connection_id}"
        )

        name = response.get("name", "Unknown")
        output_lines = [
            f"**Fabric Connection: {name}** (ID: {connection_id})\n"
        ]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")
        if response.get("status"):
            output_lines.append(f"Status: {response['status']}")

        # Include remaining fields
        for key, value in response.items():
            if key not in (
                "name", "description", "url", "resource_uri", "status"
            ) and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Fabric connection {arguments.get('connection_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting fabric connection details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting fabric connection details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_fabric_connection(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_fabric_connection tool execution."""
    try:
        name = arguments["name"]
        description = arguments.get("description")

        logger.info(f"Creating fabric connection: {name}")

        data = {"name": name}
        if description:
            data["description"] = description

        response = client._request(
            "POST", "fabric_connection", json_data=data
        )

        output_lines = [
            "**Fabric Connection Created**\n",
            f"Name: {name}"
        ]

        if description:
            output_lines.append(f"Description: {description}")

        if isinstance(response, dict) and response.get("url"):
            conn_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Connection ID: {conn_id}")
        else:
            output_lines.append(
                "\nConnection created. Use 'list_fabric_connections' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating fabric connection: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating fabric connection")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_fabric_connection(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_fabric_connection tool execution."""
    try:
        connection_id = arguments["connection_id"]

        logger.info(f"Deleting fabric connection {connection_id}")

        # Get name before deleting
        try:
            response = client._request(
                "GET", f"fabric_connection/{connection_id}"
            )
            conn_name = response.get("name", f"ID {connection_id}")
        except Exception:
            conn_name = f"ID {connection_id}"

        client._request("DELETE", f"fabric_connection/{connection_id}")

        return [TextContent(
            type="text",
            text=(
                f"**Fabric Connection Deleted**\n\n"
                f"Fabric connection '{conn_name}' (ID: {connection_id}) "
                f"has been deleted."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Fabric connection {arguments.get('connection_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting fabric connection: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting fabric connection")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

FABRIC_TOOL_DEFINITIONS = {
    "list_fabric_connections": list_fabric_connections_tool_definition,
    "get_fabric_connection_details": get_fabric_connection_details_tool_definition,
    "create_fabric_connection": create_fabric_connection_tool_definition,
    "delete_fabric_connection": delete_fabric_connection_tool_definition,
}

FABRIC_HANDLERS = {
    "list_fabric_connections": handle_list_fabric_connections,
    "get_fabric_connection_details": handle_get_fabric_connection_details,
    "create_fabric_connection": handle_create_fabric_connection,
    "delete_fabric_connection": handle_delete_fabric_connection,
}
