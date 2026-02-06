"""Server network service CRUD tools for FortiMonitor."""

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


def get_network_service_details_tool_definition() -> Tool:
    """Return tool definition for getting network service details."""
    return Tool(
        name="get_network_service_details",
        description=(
            "Get detailed information about a specific network service (monitoring check) "
            "on a server. Shows check type, port, frequency, and status."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "network_service_id": {
                    "type": "integer",
                    "description": "ID of the network service"
                }
            },
            "required": ["server_id", "network_service_id"]
        }
    )


def create_network_service_tool_definition() -> Tool:
    """Return tool definition for creating a network service."""
    return Tool(
        name="create_network_service",
        description=(
            "Create a new network service (monitoring check) on a server. "
            "This adds a new monitoring check such as HTTP, DNS, TCP, etc."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server to add the check to"
                },
                "network_service_type_id": {
                    "type": "integer",
                    "description": "ID of the network service type (HTTP, DNS, TCP, etc.)"
                },
                "port": {
                    "type": "integer",
                    "description": "Port number to monitor (optional, depends on service type)"
                },
                "frequency": {
                    "type": "integer",
                    "description": "Check frequency in seconds (optional)"
                },
                "name": {
                    "type": "string",
                    "description": "Optional custom name for this check"
                }
            },
            "required": ["server_id", "network_service_type_id"]
        }
    )


def update_network_service_tool_definition() -> Tool:
    """Return tool definition for updating a network service."""
    return Tool(
        name="update_network_service",
        description=(
            "Update an existing network service (monitoring check) on a server. "
            "Can change port, frequency, name, or other settings."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "network_service_id": {
                    "type": "integer",
                    "description": "ID of the network service to update"
                },
                "port": {
                    "type": "integer",
                    "description": "New port number (optional)"
                },
                "frequency": {
                    "type": "integer",
                    "description": "New check frequency in seconds (optional)"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the check (optional)"
                }
            },
            "required": ["server_id", "network_service_id"]
        }
    )


def delete_network_service_tool_definition() -> Tool:
    """Return tool definition for deleting a network service."""
    return Tool(
        name="delete_network_service",
        description=(
            "Delete a network service (monitoring check) from a server. "
            "This permanently removes the check and its monitoring data."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "network_service_id": {
                    "type": "integer",
                    "description": "ID of the network service to delete"
                }
            },
            "required": ["server_id", "network_service_id"]
        }
    )


def get_network_service_response_time_tool_definition() -> Tool:
    """Return tool definition for getting network service response time."""
    return Tool(
        name="get_network_service_response_time",
        description=(
            "Get response time metrics for a specific network service on a server. "
            "Returns time-series data for the specified timescale."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "network_service_id": {
                    "type": "integer",
                    "description": "ID of the network service"
                },
                "timescale": {
                    "type": "string",
                    "default": "day",
                    "description": "Time scale for data (e.g., 'hour', 'day', 'week', 'month')"
                }
            },
            "required": ["server_id", "network_service_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_get_network_service_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_network_service_details tool execution."""
    try:
        server_id = arguments["server_id"]
        ns_id = arguments["network_service_id"]

        logger.info(
            f"Getting network service {ns_id} details for server {server_id}"
        )

        response = client._request(
            "GET", f"server/{server_id}/network_service/{ns_id}"
        )

        name = response.get("name", response.get("display_name", "Unknown"))
        output_lines = [
            f"**Network Service: {name}** (ID: {ns_id})\n",
            f"Server ID: {server_id}"
        ]

        if response.get("network_service_type"):
            type_id = _extract_id_from_url(response["network_service_type"])
            output_lines.append(f"Service Type ID: {type_id}")
        if response.get("port"):
            output_lines.append(f"Port: {response['port']}")
        if response.get("frequency"):
            output_lines.append(f"Frequency: {response['frequency']}s")
        if response.get("status"):
            output_lines.append(f"Status: {response['status']}")

        for key, value in response.items():
            if key not in ("name", "display_name", "url", "resource_uri",
                          "network_service_type", "port", "frequency",
                          "status") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Network service {arguments.get('network_service_id')} not found on server {arguments.get('server_id')}."
        )]
    except APIError as e:
        logger.error(f"API error getting network service details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting network service details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_network_service(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_network_service tool execution."""
    try:
        server_id = arguments["server_id"]
        ns_type_id = arguments["network_service_type_id"]
        port = arguments.get("port")
        frequency = arguments.get("frequency")
        name = arguments.get("name")

        logger.info(f"Creating network service on server {server_id}")

        data = {
            "network_service_type": (
                f"{client.base_url}/network_service_type/{ns_type_id}"
            )
        }
        if port is not None:
            data["port"] = port
        if frequency is not None:
            data["frequency"] = frequency
        if name:
            data["name"] = name

        response = client._request(
            "POST",
            f"server/{server_id}/network_service",
            json_data=data
        )

        output_lines = [
            "**Network Service Created**\n",
            f"Server ID: {server_id}",
            f"Service Type ID: {ns_type_id}"
        ]

        if port:
            output_lines.append(f"Port: {port}")
        if frequency:
            output_lines.append(f"Frequency: {frequency}s")
        if name:
            output_lines.append(f"Name: {name}")

        if isinstance(response, dict) and response.get("url"):
            ns_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Network Service ID: {ns_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error creating network service: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating network service")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_network_service(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_network_service tool execution."""
    try:
        server_id = arguments["server_id"]
        ns_id = arguments["network_service_id"]
        port = arguments.get("port")
        frequency = arguments.get("frequency")
        name = arguments.get("name")

        if port is None and frequency is None and name is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'port', 'frequency', or 'name' must be provided."
            )]

        logger.info(
            f"Updating network service {ns_id} on server {server_id}"
        )

        data = {}
        if port is not None:
            data["port"] = port
        if frequency is not None:
            data["frequency"] = frequency
        if name is not None:
            data["name"] = name

        client._request(
            "PUT",
            f"server/{server_id}/network_service/{ns_id}",
            json_data=data
        )

        output_lines = ["**Network Service Updated**\n"]
        output_lines.append(f"Server ID: {server_id}")
        output_lines.append(f"Network Service ID: {ns_id}")
        if port is not None:
            output_lines.append(f"Port: {port}")
        if frequency is not None:
            output_lines.append(f"Frequency: {frequency}s")
        if name is not None:
            output_lines.append(f"Name: {name}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Network service {arguments.get('network_service_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating network service: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating network service")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_network_service(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_network_service tool execution."""
    try:
        server_id = arguments["server_id"]
        ns_id = arguments["network_service_id"]

        logger.info(
            f"Deleting network service {ns_id} from server {server_id}"
        )

        client._request(
            "DELETE", f"server/{server_id}/network_service/{ns_id}"
        )

        return [TextContent(
            type="text",
            text=(
                f"**Network Service Deleted**\n\n"
                f"Network service {ns_id} has been removed from server {server_id}.\n\n"
                f"Note: Historical monitoring data for this check has been removed."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Network service {arguments.get('network_service_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting network service: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting network service")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_network_service_response_time(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_network_service_response_time tool execution."""
    try:
        server_id = arguments["server_id"]
        ns_id = arguments["network_service_id"]
        timescale = arguments.get("timescale", "day")

        logger.info(
            f"Getting response time for network service {ns_id} "
            f"on server {server_id} (timescale={timescale})"
        )

        response = client._request(
            "GET",
            f"server/{server_id}/network_service/{ns_id}/response_time/{timescale}"
        )

        output_lines = [
            f"**Response Time: Network Service {ns_id} on Server {server_id}**\n",
            f"Timescale: {timescale}\n"
        ]

        if isinstance(response, dict):
            data_points = response.get(
                "data", response.get("response_time_list", [])
            )
            if isinstance(data_points, list) and data_points:
                output_lines.append(f"Data Points: {len(data_points)}\n")
                for point in data_points[:20]:
                    if isinstance(point, dict):
                        time_val = point.get(
                            "time", point.get("timestamp", "")
                        )
                        value = point.get(
                            "value", point.get("response_time", "")
                        )
                        output_lines.append(f"  {time_val}: {value}ms")
                if len(data_points) > 20:
                    output_lines.append(
                        f"  ... and {len(data_points) - 20} more data points"
                    )
            else:
                for key, value in response.items():
                    if key not in ("url", "resource_uri", "success",
                                  "status_code") and value:
                        output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Network service {arguments.get('network_service_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting response time: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting response time")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

NETWORK_SERVICES_TOOL_DEFINITIONS = {
    "get_network_service_details": get_network_service_details_tool_definition,
    "create_network_service": create_network_service_tool_definition,
    "update_network_service": update_network_service_tool_definition,
    "delete_network_service": delete_network_service_tool_definition,
    "get_network_service_response_time": get_network_service_response_time_tool_definition,
}

NETWORK_SERVICES_HANDLERS = {
    "get_network_service_details": handle_get_network_service_details,
    "create_network_service": handle_create_network_service,
    "update_network_service": handle_update_network_service,
    "delete_network_service": handle_delete_network_service,
    "get_network_service_response_time": handle_get_network_service_response_time,
}
