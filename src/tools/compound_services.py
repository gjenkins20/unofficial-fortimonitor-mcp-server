"""Compound service management tools for FortiMonitor."""

import logging
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def list_compound_services_tool_definition() -> Tool:
    """Return tool definition for listing compound services."""
    return Tool(
        name="list_compound_services",
        description=(
            "List all compound services. Compound services aggregate multiple "
            "server checks into a single logical service for unified monitoring."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of compound services to return (default 50)"
                }
            }
        }
    )


def create_compound_service_tool_definition() -> Tool:
    """Return tool definition for creating a compound service."""
    return Tool(
        name="create_compound_service",
        description=(
            "Create a new compound service that aggregates multiple server checks "
            "into a single logical service."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the compound service"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the compound service"
                },
                "server_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Optional list of server IDs to include in the compound service"
                }
            },
            "required": ["name"]
        }
    )


def get_compound_service_details_tool_definition() -> Tool:
    """Return tool definition for getting compound service details."""
    return Tool(
        name="get_compound_service_details",
        description=(
            "Get detailed information about a specific compound service."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "service_id": {
                    "type": "integer",
                    "description": "ID of the compound service"
                }
            },
            "required": ["service_id"]
        }
    )


def update_compound_service_tool_definition() -> Tool:
    """Return tool definition for updating a compound service."""
    return Tool(
        name="update_compound_service",
        description=(
            "Update an existing compound service's name or description."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "service_id": {
                    "type": "integer",
                    "description": "ID of the compound service to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the compound service (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description for the compound service (optional)"
                }
            },
            "required": ["service_id"]
        }
    )


def delete_compound_service_tool_definition() -> Tool:
    """Return tool definition for deleting a compound service."""
    return Tool(
        name="delete_compound_service",
        description=(
            "Delete a compound service. The underlying servers and checks are not affected."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "service_id": {
                    "type": "integer",
                    "description": "ID of the compound service to delete"
                }
            },
            "required": ["service_id"]
        }
    )


def list_compound_service_thresholds_tool_definition() -> Tool:
    """Return tool definition for listing compound service thresholds."""
    return Tool(
        name="list_compound_service_thresholds",
        description=(
            "List agent resource thresholds configured for a compound service. "
            "Thresholds define alerting conditions for monitored metrics."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "service_id": {
                    "type": "integer",
                    "description": "ID of the compound service"
                }
            },
            "required": ["service_id"]
        }
    )


def get_compound_service_availability_tool_definition() -> Tool:
    """Return tool definition for getting compound service availability."""
    return Tool(
        name="get_compound_service_availability",
        description=(
            "Get availability data for a compound service over a specified time range."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "service_id": {
                    "type": "integer",
                    "description": "ID of the compound service"
                },
                "start_time": {
                    "type": "string",
                    "description": "Start time for the availability window (e.g. '2024-01-01 00:00:00')"
                },
                "end_time": {
                    "type": "string",
                    "description": "End time for the availability window (e.g. '2024-01-31 23:59:59')"
                }
            },
            "required": ["service_id", "start_time", "end_time"]
        }
    )


def list_compound_service_network_services_tool_definition() -> Tool:
    """Return tool definition for listing network services in a compound service."""
    return Tool(
        name="list_compound_service_network_services",
        description=(
            "List network services (checks) associated with a compound service."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "service_id": {
                    "type": "integer",
                    "description": "ID of the compound service"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of network services to return (default 50)"
                }
            },
            "required": ["service_id"]
        }
    )


def get_compound_service_response_time_tool_definition() -> Tool:
    """Return tool definition for getting compound service response time."""
    return Tool(
        name="get_compound_service_response_time",
        description=(
            "Get response time metrics for a compound service. "
            "Shows how quickly the service responds to monitoring checks."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "service_id": {
                    "type": "integer",
                    "description": "ID of the compound service"
                },
                "timescale": {
                    "type": "string",
                    "default": "day",
                    "description": "Time scale for aggregation (e.g. 'hour', 'day', 'week')"
                }
            },
            "required": ["service_id"]
        }
    )


def list_compound_service_outages_tool_definition() -> Tool:
    """Return tool definition for listing compound service outages."""
    return Tool(
        name="list_compound_service_outages",
        description=(
            "List outages (alerts) for a specific compound service."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "service_id": {
                    "type": "integer",
                    "description": "ID of the compound service"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of outages to return (default 50)"
                }
            },
            "required": ["service_id"]
        }
    )


def get_compound_service_network_service_details_tool_definition() -> Tool:
    """Return tool definition for getting a specific network service in a compound service."""
    return Tool(
        name="get_compound_service_network_service_details",
        description=(
            "Get detailed information about a specific network service within a compound service."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "service_id": {
                    "type": "integer",
                    "description": "ID of the compound service"
                },
                "network_service_id": {
                    "type": "integer",
                    "description": "ID of the network service"
                }
            },
            "required": ["service_id", "network_service_id"]
        }
    )


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
# TOOL HANDLERS
# ============================================================================


async def handle_list_compound_services(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_compound_services tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing compound services (limit={limit})")

        response = client._request("GET", "compound_service", params={"limit": limit})
        services = response.get("compound_service_list", [])
        meta = response.get("meta", {})

        if not services:
            return [TextContent(type="text", text="No compound services found.")]

        total_count = meta.get("total_count", len(services))

        output_lines = [
            "**Compound Services**\n",
            f"Found {len(services)} service(s):\n"
        ]

        for svc in services:
            name = svc.get("name", "Unknown")
            svc_id = _extract_id_from_url(svc.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {svc_id})")
            if svc.get("description"):
                output_lines.append(f"  Description: {svc['description']}")

        if total_count > len(services):
            output_lines.append(f"\n(Showing {len(services)} of {total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing compound services: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing compound services")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_compound_service(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_compound_service tool execution."""
    try:
        name = arguments["name"]
        description = arguments.get("description")
        server_ids = arguments.get("server_ids", [])

        logger.info(f"Creating compound service: {name}")

        data = {"name": name}
        if description:
            data["description"] = description
        if server_ids:
            data["servers"] = [
                f"{client.base_url}/server/{sid}" for sid in server_ids
            ]

        response = client._request("POST", "compound_service", json_data=data)

        output_lines = [
            "**Compound Service Created**\n",
            f"Name: {name}"
        ]

        if description:
            output_lines.append(f"Description: {description}")

        if server_ids:
            output_lines.append(f"Servers: {len(server_ids)} server(s) included")

        if isinstance(response, dict) and response.get("url"):
            svc_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Service ID: {svc_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nService created. Use 'list_compound_services' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating compound service: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating compound service")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_compound_service_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_compound_service_details tool execution."""
    try:
        service_id = arguments["service_id"]

        logger.info(f"Getting compound service details for {service_id}")

        response = client._request("GET", f"compound_service/{service_id}")

        name = response.get("name", "Unknown")
        output_lines = [f"**Compound Service: {name}** (ID: {service_id})\n"]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        # Show servers if present
        servers = response.get("servers", [])
        if servers:
            output_lines.append(f"\n**Servers ({len(servers)}):**")
            for srv_url in servers[:20]:
                srv_id = _extract_id_from_url(srv_url)
                output_lines.append(f"  - Server ID: {srv_id}")
            if len(servers) > 20:
                output_lines.append(f"  ... and {len(servers) - 20} more")

        for key, value in response.items():
            if key not in ("name", "description", "url", "resource_uri", "servers") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Compound service {arguments.get('service_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting compound service details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting compound service details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_compound_service(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_compound_service tool execution."""
    try:
        service_id = arguments["service_id"]
        name = arguments.get("name")
        description = arguments.get("description")

        if name is None and description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name' or 'description' must be provided."
            )]

        logger.info(f"Updating compound service {service_id}")

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        client._request("PUT", f"compound_service/{service_id}", json_data=data)

        output_lines = ["**Compound Service Updated**\n"]
        if name:
            output_lines.append(f"Name: {name}")
        if description is not None:
            output_lines.append(f"Description: Updated")
        output_lines.append(f"Service ID: {service_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Compound service {arguments.get('service_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating compound service: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating compound service")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_compound_service(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_compound_service tool execution."""
    try:
        service_id = arguments["service_id"]

        logger.info(f"Deleting compound service {service_id}")

        # Get name before deleting
        try:
            response = client._request("GET", f"compound_service/{service_id}")
            svc_name = response.get("name", f"ID {service_id}")
        except Exception:
            svc_name = f"ID {service_id}"

        client._request("DELETE", f"compound_service/{service_id}")

        return [TextContent(
            type="text",
            text=(
                f"**Compound Service Deleted**\n\n"
                f"Compound service '{svc_name}' (ID: {service_id}) has been deleted.\n\n"
                f"Note: The underlying servers and checks are not affected."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Compound service {arguments.get('service_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting compound service: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting compound service")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_compound_service_thresholds(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_compound_service_thresholds tool execution."""
    try:
        service_id = arguments["service_id"]

        logger.info(f"Listing thresholds for compound service {service_id}")

        response = client._request(
            "GET",
            f"compound_service/{service_id}/agent_resource_threshold"
        )
        thresholds = response.get("agent_resource_threshold_list", [])
        meta = response.get("meta", {})

        if not thresholds:
            return [TextContent(
                type="text",
                text=f"No thresholds configured for compound service {service_id}."
            )]

        total_count = meta.get("total_count", len(thresholds))

        output_lines = [
            f"**Thresholds for Compound Service {service_id}**\n",
            f"Found {len(thresholds)} threshold(s):\n"
        ]

        for threshold in thresholds:
            name = threshold.get("name", "Unknown")
            threshold_id = _extract_id_from_url(threshold.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {threshold_id})")
            if threshold.get("warning_threshold"):
                output_lines.append(f"  Warning: {threshold['warning_threshold']}")
            if threshold.get("critical_threshold"):
                output_lines.append(f"  Critical: {threshold['critical_threshold']}")
            if threshold.get("agent_resource_type"):
                type_id = _extract_id_from_url(threshold["agent_resource_type"])
                output_lines.append(f"  Resource Type ID: {type_id}")

        if total_count > len(thresholds):
            output_lines.append(
                f"\n(Showing {len(thresholds)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Compound service {arguments.get('service_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error listing thresholds: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing thresholds")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_compound_service_availability(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_compound_service_availability tool execution."""
    try:
        service_id = arguments["service_id"]
        start_time = arguments["start_time"]
        end_time = arguments["end_time"]

        logger.info(f"Getting availability for compound service {service_id}")

        response = client._request(
            "GET",
            f"compound_service/{service_id}/availability",
            params={"start_time": start_time, "end_time": end_time}
        )

        output_lines = [
            f"**Availability for Compound Service {service_id}**\n",
            f"Period: {start_time} to {end_time}\n"
        ]

        # Format availability data from response
        if isinstance(response, dict):
            availability = response.get("availability")
            if availability is not None:
                output_lines.append(f"Availability: {availability}%")

            uptime = response.get("uptime")
            if uptime is not None:
                output_lines.append(f"Uptime: {uptime}")

            downtime = response.get("downtime")
            if downtime is not None:
                output_lines.append(f"Downtime: {downtime}")

            # Include any other relevant fields
            for key, value in response.items():
                if key not in ("availability", "uptime", "downtime", "url",
                               "resource_uri", "success", "status_code") and value:
                    output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Compound service {arguments.get('service_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting availability: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting availability")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_compound_service_network_services(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_compound_service_network_services tool execution."""
    try:
        service_id = arguments["service_id"]
        limit = arguments.get("limit", 50)

        logger.info(f"Listing network services for compound service {service_id}")

        response = client._request(
            "GET",
            f"compound_service/{service_id}/network_service",
            params={"limit": limit}
        )
        network_services = response.get("network_service_list", [])
        meta = response.get("meta", {})

        if not network_services:
            return [TextContent(
                type="text",
                text=f"No network services found for compound service {service_id}."
            )]

        total_count = meta.get("total_count", len(network_services))

        output_lines = [
            f"**Network Services for Compound Service {service_id}**\n",
            f"Found {len(network_services)} service(s):\n"
        ]

        for ns in network_services:
            name = ns.get("name", ns.get("display_name", "Unknown"))
            ns_id = _extract_id_from_url(ns.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {ns_id})")
            if ns.get("status"):
                output_lines.append(f"  Status: {ns['status']}")
            if ns.get("port"):
                output_lines.append(f"  Port: {ns['port']}")
            if ns.get("frequency"):
                output_lines.append(f"  Frequency: {ns['frequency']}s")

        if total_count > len(network_services):
            output_lines.append(
                f"\n(Showing {len(network_services)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Compound service {arguments.get('service_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error listing network services: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing network services")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_compound_service_response_time(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_compound_service_response_time tool execution."""
    try:
        service_id = arguments["service_id"]
        timescale = arguments.get("timescale", "day")

        logger.info(f"Getting response time for compound service {service_id}")

        response = client._request(
            "GET",
            f"compound_service/{service_id}/response_time",
            params={"timescale": timescale}
        )

        output_lines = [
            f"**Response Time for Compound Service {service_id}**\n",
            f"Timescale: {timescale}\n"
        ]

        # Format response time data
        if isinstance(response, dict):
            # Handle data points if present
            data_points = response.get("data", response.get("response_time_list", []))
            if isinstance(data_points, list) and data_points:
                output_lines.append(f"Data Points: {len(data_points)}\n")
                for point in data_points[:20]:
                    if isinstance(point, dict):
                        time_val = point.get("time", point.get("timestamp", ""))
                        value = point.get("value", point.get("response_time", ""))
                        output_lines.append(f"  {time_val}: {value}ms")
                if len(data_points) > 20:
                    output_lines.append(f"  ... and {len(data_points) - 20} more data points")
            else:
                # Include any summary fields
                for key, value in response.items():
                    if key not in ("url", "resource_uri", "success", "status_code") and value:
                        output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Compound service {arguments.get('service_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting response time: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting response time")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_compound_service_outages(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_compound_service_outages tool execution."""
    try:
        service_id = arguments["service_id"]
        limit = arguments.get("limit", 50)

        logger.info(f"Listing outages for compound service {service_id}")

        response = client._request(
            "GET",
            f"compound_service/{service_id}/outage",
            params={"limit": limit}
        )
        outages = response.get("outage_list", [])
        meta = response.get("meta", {})

        if not outages:
            return [TextContent(
                type="text",
                text=f"No outages found for compound service {service_id}."
            )]

        total_count = meta.get("total_count", len(outages))

        output_lines = [
            f"**Outages for Compound Service {service_id}**\n",
            f"Found {len(outages)} outage(s):\n"
        ]

        for outage in outages:
            outage_id = _extract_id_from_url(outage.get("url", ""))
            severity = outage.get("severity", "unknown")
            status = outage.get("status", "unknown")
            start = outage.get("start_time", "N/A")

            severity_label = {
                "critical": "[CRIT]",
                "warning": "[WARN]",
                "info": "[INFO]"
            }.get(severity, f"[{severity.upper()}]")

            output_lines.append(f"\n{severity_label} **Outage {outage_id}**")
            output_lines.append(f"  Severity: {severity}")
            output_lines.append(f"  Status: {status}")
            output_lines.append(f"  Started: {start}")

            if outage.get("end_time"):
                output_lines.append(f"  Ended: {outage['end_time']}")

            acknowledged = outage.get("acknowledged", False)
            output_lines.append(f"  Acknowledged: {'Yes' if acknowledged else 'No'}")

        if total_count > len(outages):
            output_lines.append(
                f"\n(Showing {len(outages)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Compound service {arguments.get('service_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error listing outages: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing outages")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_compound_service_network_service_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_compound_service_network_service_details tool execution."""
    try:
        service_id = arguments["service_id"]
        ns_id = arguments["network_service_id"]

        logger.info(
            f"Getting network service {ns_id} details "
            f"for compound service {service_id}"
        )

        response = client._request(
            "GET",
            f"compound_service/{service_id}/network_service/{ns_id}"
        )

        name = response.get("name", response.get("display_name", "Unknown"))
        output_lines = [
            f"**Network Service: {name}** (ID: {ns_id})\n",
            f"Compound Service ID: {service_id}"
        ]

        if response.get("status"):
            output_lines.append(f"Status: {response['status']}")
        if response.get("port"):
            output_lines.append(f"Port: {response['port']}")
        if response.get("frequency"):
            output_lines.append(f"Frequency: {response['frequency']}s")

        # Include any other relevant fields
        for key, value in response.items():
            if key not in ("name", "display_name", "url", "resource_uri",
                          "status", "port", "frequency") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Network service {arguments.get('network_service_id')} "
                f"not found in compound service {arguments.get('service_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error getting compound service network service: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting compound service network service")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

COMPOUND_SERVICES_TOOL_DEFINITIONS = {
    "list_compound_services": list_compound_services_tool_definition,
    "create_compound_service": create_compound_service_tool_definition,
    "get_compound_service_details": get_compound_service_details_tool_definition,
    "update_compound_service": update_compound_service_tool_definition,
    "delete_compound_service": delete_compound_service_tool_definition,
    "list_compound_service_thresholds": list_compound_service_thresholds_tool_definition,
    "get_compound_service_availability": get_compound_service_availability_tool_definition,
    "list_compound_service_network_services": list_compound_service_network_services_tool_definition,
    "get_compound_service_response_time": get_compound_service_response_time_tool_definition,
    "list_compound_service_outages": list_compound_service_outages_tool_definition,
    "get_compound_service_network_service_details": get_compound_service_network_service_details_tool_definition,
}

COMPOUND_SERVICES_HANDLERS = {
    "list_compound_services": handle_list_compound_services,
    "create_compound_service": handle_create_compound_service,
    "get_compound_service_details": handle_get_compound_service_details,
    "update_compound_service": handle_update_compound_service,
    "delete_compound_service": handle_delete_compound_service,
    "list_compound_service_thresholds": handle_list_compound_service_thresholds,
    "get_compound_service_availability": handle_get_compound_service_availability,
    "list_compound_service_network_services": handle_list_compound_service_network_services,
    "get_compound_service_response_time": handle_get_compound_service_response_time,
    "list_compound_service_outages": handle_list_compound_service_outages,
    "get_compound_service_network_service_details": handle_get_compound_service_network_service_details,
}
