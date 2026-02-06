"""Monitoring node tools for FortiMonitor."""

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


def list_monitoring_nodes_tool_definition() -> Tool:
    """Return tool definition for listing monitoring nodes."""
    return Tool(
        name="list_monitoring_nodes",
        description=(
            "List all monitoring nodes in FortiMonitor. Monitoring nodes are "
            "the geographic locations from which monitoring checks are executed "
            "against your servers and services."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of monitoring nodes to return (default 50)"
                }
            }
        }
    )


def get_monitoring_node_details_tool_definition() -> Tool:
    """Return tool definition for getting monitoring node details."""
    return Tool(
        name="get_monitoring_node_details",
        description=(
            "Get detailed information about a specific monitoring node, "
            "including its location, status, and capabilities."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "node_id": {
                    "type": "integer",
                    "description": "ID of the monitoring node"
                }
            },
            "required": ["node_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_list_monitoring_nodes(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_monitoring_nodes tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing monitoring nodes (limit={limit})")

        response = client._request(
            "GET", "monitoring_node", params={"limit": limit}
        )
        nodes = response.get("monitoring_node_list", [])
        meta = response.get("meta", {})

        if not nodes:
            return [TextContent(type="text", text="No monitoring nodes found.")]

        total_count = meta.get("total_count", len(nodes))

        output_lines = [
            "**Monitoring Nodes**\n",
            f"Found {len(nodes)} monitoring node(s):\n"
        ]

        for node in nodes:
            name = node.get("name", "Unknown")
            node_id = _extract_id_from_url(node.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {node_id})")
            if node.get("description"):
                output_lines.append(f"  Description: {node['description']}")
            if node.get("location"):
                output_lines.append(f"  Location: {node['location']}")
            if node.get("status"):
                output_lines.append(f"  Status: {node['status']}")
            if node.get("ip_address"):
                output_lines.append(f"  IP Address: {node['ip_address']}")

        if total_count > len(nodes):
            output_lines.append(
                f"\n(Showing {len(nodes)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing monitoring nodes: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing monitoring nodes")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_monitoring_node_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_monitoring_node_details tool execution."""
    try:
        node_id = arguments["node_id"]

        logger.info(f"Getting monitoring node details for {node_id}")

        response = client._request("GET", f"monitoring_node/{node_id}")

        name = response.get("name", "Unknown")
        output_lines = [f"**Monitoring Node: {name}** (ID: {node_id})\n"]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")
        if response.get("location"):
            output_lines.append(f"Location: {response['location']}")
        if response.get("status"):
            output_lines.append(f"Status: {response['status']}")
        if response.get("ip_address"):
            output_lines.append(f"IP Address: {response['ip_address']}")

        # Include remaining fields
        for key, value in response.items():
            if key not in ("name", "description", "url", "resource_uri",
                          "location", "status", "ip_address") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Monitoring node {arguments.get('node_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting monitoring node details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting monitoring node details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

MONITORING_NODES_TOOL_DEFINITIONS = {
    "list_monitoring_nodes": list_monitoring_nodes_tool_definition,
    "get_monitoring_node_details": get_monitoring_node_details_tool_definition,
}

MONITORING_NODES_HANDLERS = {
    "list_monitoring_nodes": handle_list_monitoring_nodes,
    "get_monitoring_node_details": handle_get_monitoring_node_details,
}
