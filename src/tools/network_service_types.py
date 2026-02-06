"""Network service type tools for FortiMonitor."""

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


def list_network_service_types_tool_definition() -> Tool:
    """Return tool definition for listing network service types."""
    return Tool(
        name="list_network_service_types",
        description=(
            "List all available network service types in FortiMonitor. "
            "Network service types define the kinds of monitoring checks "
            "that can be applied to servers (e.g., HTTP, DNS, TCP, ICMP, SMTP)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of network service types to return (default 50)"
                }
            }
        }
    )


def get_network_service_type_details_tool_definition() -> Tool:
    """Return tool definition for getting network service type details."""
    return Tool(
        name="get_network_service_type_details",
        description=(
            "Get detailed information about a specific network service type, "
            "including its configuration options, default port, and protocol."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "type_id": {
                    "type": "integer",
                    "description": "ID of the network service type"
                }
            },
            "required": ["type_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_list_network_service_types(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_network_service_types tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing network service types (limit={limit})")

        response = client._request(
            "GET", "network_service_type", params={"limit": limit}
        )
        service_types = response.get("network_service_type_list", [])
        meta = response.get("meta", {})

        if not service_types:
            return [TextContent(
                type="text", text="No network service types found."
            )]

        total_count = meta.get("total_count", len(service_types))

        output_lines = [
            "**Network Service Types**\n",
            f"Found {len(service_types)} network service type(s):\n"
        ]

        for stype in service_types:
            name = stype.get("name", "Unknown")
            type_id = _extract_id_from_url(stype.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {type_id})")
            if stype.get("description"):
                output_lines.append(f"  Description: {stype['description']}")
            if stype.get("default_port"):
                output_lines.append(
                    f"  Default Port: {stype['default_port']}"
                )
            if stype.get("protocol"):
                output_lines.append(f"  Protocol: {stype['protocol']}")

        if total_count > len(service_types):
            output_lines.append(
                f"\n(Showing {len(service_types)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing network service types: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing network service types")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_network_service_type_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_network_service_type_details tool execution."""
    try:
        type_id = arguments["type_id"]

        logger.info(f"Getting network service type details for {type_id}")

        response = client._request(
            "GET", f"network_service_type/{type_id}"
        )

        name = response.get("name", "Unknown")
        output_lines = [
            f"**Network Service Type: {name}** (ID: {type_id})\n"
        ]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")
        if response.get("default_port"):
            output_lines.append(
                f"Default Port: {response['default_port']}"
            )
        if response.get("protocol"):
            output_lines.append(f"Protocol: {response['protocol']}")

        # Include remaining fields
        for key, value in response.items():
            if key not in ("name", "description", "url", "resource_uri",
                          "default_port", "protocol") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Network service type {arguments.get('type_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting network service type details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception(
            "Unexpected error getting network service type details"
        )
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

NETWORK_SERVICE_TYPES_TOOL_DEFINITIONS = {
    "list_network_service_types": list_network_service_types_tool_definition,
    "get_network_service_type_details": get_network_service_type_details_tool_definition,
}

NETWORK_SERVICE_TYPES_HANDLERS = {
    "list_network_service_types": handle_list_network_service_types,
    "get_network_service_type_details": handle_get_network_service_type_details,
}
