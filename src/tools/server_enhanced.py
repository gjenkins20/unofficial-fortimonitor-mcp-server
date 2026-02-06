"""Enhanced server sub-resource operations as MCP tools."""

import json
import logging
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def create_server_tool_definition() -> Tool:
    """Return tool definition for creating a server."""
    return Tool(
        name="create_server",
        description=(
            "Create a new monitored server in FortiMonitor. "
            "Requires a name and FQDN. Optionally assign to a server group, "
            "apply a monitoring template, and add tags."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the new server",
                },
                "fqdn": {
                    "type": "string",
                    "description": "Fully qualified domain name or IP address",
                },
                "server_group": {
                    "type": "integer",
                    "description": "Optional server group ID to assign the server to",
                },
                "server_template": {
                    "type": "integer",
                    "description": "Optional server template ID to apply monitoring configuration",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of tags to assign to the server",
                },
            },
            "required": ["name", "fqdn"],
        },
    )


def update_server_tool_definition() -> Tool:
    """Return tool definition for updating a server."""
    return Tool(
        name="update_server",
        description=(
            "Update properties of an existing monitored server. "
            "Can update name, description, tags, and monitoring status."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server to update",
                },
                "name": {
                    "type": "string",
                    "description": "New server name",
                },
                "description": {
                    "type": "string",
                    "description": "New server description",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "New list of tags (replaces existing tags)",
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive", "paused"],
                    "description": "New monitoring status for the server",
                },
            },
            "required": ["server_id"],
        },
    )


def delete_server_tool_definition() -> Tool:
    """Return tool definition for deleting a server."""
    return Tool(
        name="delete_server",
        description=(
            "Delete a monitored server from FortiMonitor. "
            "This permanently removes the server and all its monitoring data."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server to delete",
                },
            },
            "required": ["server_id"],
        },
    )


def get_server_availability_tool_definition() -> Tool:
    """Return tool definition for getting server availability data."""
    return Tool(
        name="get_server_availability",
        description=(
            "Get server availability/uptime data for a specific time range. "
            "Returns availability percentage and outage details."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server",
                },
                "start_time": {
                    "type": "string",
                    "description": "Start of time range in ISO datetime format (e.g., 2026-01-01T00:00:00Z)",
                },
                "end_time": {
                    "type": "string",
                    "description": "End of time range in ISO datetime format (e.g., 2026-02-01T00:00:00Z)",
                },
            },
            "required": ["server_id", "start_time", "end_time"],
        },
    )


def get_server_outages_tool_definition() -> Tool:
    """Return tool definition for getting server outages."""
    return Tool(
        name="get_server_outages",
        description=(
            "Get outages for a specific server. "
            "Returns a list of outage events associated with the server."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server",
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 500,
                    "description": "Maximum number of outages to return (default 50)",
                },
            },
            "required": ["server_id"],
        },
    )


def list_server_attributes_tool_definition() -> Tool:
    """Return tool definition for listing server attributes."""
    return Tool(
        name="list_server_attributes",
        description=(
            "List custom attributes for a server. "
            "Server attributes are key-value pairs for custom metadata."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server",
                },
            },
            "required": ["server_id"],
        },
    )


def create_server_attribute_tool_definition() -> Tool:
    """Return tool definition for creating a server attribute."""
    return Tool(
        name="create_server_attribute",
        description=(
            "Create a custom attribute on a server. "
            "Attributes are key-value pairs for storing custom metadata."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server",
                },
                "name": {
                    "type": "string",
                    "description": "Attribute name (key)",
                },
                "value": {
                    "type": "string",
                    "description": "Attribute value",
                },
            },
            "required": ["server_id", "name", "value"],
        },
    )


def update_server_attribute_tool_definition() -> Tool:
    """Return tool definition for updating a server attribute."""
    return Tool(
        name="update_server_attribute",
        description=(
            "Update the value of an existing server attribute."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server",
                },
                "attribute_id": {
                    "type": "integer",
                    "description": "The ID of the attribute to update",
                },
                "value": {
                    "type": "string",
                    "description": "New attribute value",
                },
            },
            "required": ["server_id", "attribute_id", "value"],
        },
    )


def delete_server_attribute_tool_definition() -> Tool:
    """Return tool definition for deleting a server attribute."""
    return Tool(
        name="delete_server_attribute",
        description=(
            "Delete a custom attribute from a server."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server",
                },
                "attribute_id": {
                    "type": "integer",
                    "description": "The ID of the attribute to delete",
                },
            },
            "required": ["server_id", "attribute_id"],
        },
    )


def get_agent_resource_details_tool_definition() -> Tool:
    """Return tool definition for getting agent resource details."""
    return Tool(
        name="get_agent_resource_details",
        description=(
            "Get detailed information about a specific agent resource on a server. "
            "Returns resource configuration, current value, thresholds, and status."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server",
                },
                "resource_id": {
                    "type": "integer",
                    "description": "The ID of the agent resource",
                },
            },
            "required": ["server_id", "resource_id"],
        },
    )


def get_agent_resource_metric_tool_definition() -> Tool:
    """Return tool definition for getting agent resource metric data."""
    return Tool(
        name="get_agent_resource_metric",
        description=(
            "Get metric graph data for an agent resource. "
            "Returns time-series data points for the specified timescale."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server",
                },
                "resource_id": {
                    "type": "integer",
                    "description": "The ID of the agent resource",
                },
                "timescale": {
                    "type": "string",
                    "enum": ["hour", "day", "week", "month"],
                    "default": "day",
                    "description": "Time range for metric data (default: day)",
                },
            },
            "required": ["server_id", "resource_id"],
        },
    )


def list_server_logs_tool_definition() -> Tool:
    """Return tool definition for listing server logs."""
    return Tool(
        name="list_server_logs",
        description=(
            "List log entries for a server. "
            "Returns recent server log entries including system and user-added logs."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server",
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 500,
                    "description": "Maximum number of log entries to return (default 50)",
                },
            },
            "required": ["server_id"],
        },
    )


def create_server_log_tool_definition() -> Tool:
    """Return tool definition for creating a server log entry."""
    return Tool(
        name="create_server_log",
        description=(
            "Add a log entry to a server. "
            "Useful for documenting actions taken, notes, or observations."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server",
                },
                "entry": {
                    "type": "string",
                    "description": "Log entry text to add",
                },
            },
            "required": ["server_id", "entry"],
        },
    )


def create_custom_incident_tool_definition() -> Tool:
    """Return tool definition for creating a custom incident."""
    return Tool(
        name="create_custom_incident",
        description=(
            "Create a custom incident on a server. "
            "Use this to manually trigger an incident for a known issue."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server",
                },
                "description": {
                    "type": "string",
                    "description": "Description of the incident",
                },
                "severity": {
                    "type": "string",
                    "enum": ["critical", "warning", "info"],
                    "default": "critical",
                    "description": "Severity level of the incident (default: critical)",
                },
            },
            "required": ["server_id", "description"],
        },
    )


def flush_server_dns_tool_definition() -> Tool:
    """Return tool definition for flushing server DNS."""
    return Tool(
        name="flush_server_dns",
        description=(
            "Flush the DNS cache for a server. "
            "Forces re-resolution of the server's FQDN on the next check."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "The ID of the server",
                },
            },
            "required": ["server_id"],
        },
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_create_server(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle create_server tool execution."""
    try:
        name = arguments["name"]
        fqdn = arguments["fqdn"]
        server_group = arguments.get("server_group")
        server_template = arguments.get("server_template")
        tags = arguments.get("tags")

        logger.info(f"Creating server: {name} ({fqdn})")

        # Build request data
        data = {
            "name": name,
            "fqdn": fqdn,
        }

        if server_group is not None:
            data["server_group"] = f"{client.base_url}/server_group/{server_group}"

        if server_template is not None:
            data["server_template"] = f"{client.base_url}/server_template/{server_template}"

        if tags:
            data["tags"] = tags

        response = client._request("POST", "server", json_data=data)

        # Format response
        output_lines = [
            "**Server Created**\n",
            f"Name: {name}",
            f"FQDN: {fqdn}",
        ]

        if server_group is not None:
            output_lines.append(f"Server Group: {server_group}")
        if server_template is not None:
            output_lines.append(f"Server Template: {server_template}")
        if tags:
            output_lines.append(f"Tags: {', '.join(tags)}")

        # Try to extract server ID from response
        if isinstance(response, dict):
            server_id = response.get("id")
            if server_id:
                output_lines.append(f"Server ID: {server_id}")
            elif response.get("url"):
                # ID may be embedded in URL
                url = response["url"]
                try:
                    server_id = url.rstrip("/").split("/")[-1]
                    output_lines.append(f"Server ID: {server_id}")
                except Exception:
                    pass

        output_lines.append(
            "\nNote: Use 'get_servers' to verify the server was created and find its ID."
        )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating server: {e}")
        return [TextContent(type="text", text=f"Error creating server: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating server")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_server(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle update_server tool execution."""
    try:
        server_id = arguments["server_id"]
        name = arguments.get("name")
        description = arguments.get("description")
        tags = arguments.get("tags")
        status = arguments.get("status")

        if not any([name, description, tags is not None, status]):
            return [TextContent(
                type="text",
                text="Error: At least one field (name, description, tags, status) must be provided."
            )]

        logger.info(f"Updating server {server_id}")

        # Get current server info for context
        try:
            old_server = client.get_server_details(server_id)
            server_name = old_server.name
        except Exception:
            server_name = f"Server {server_id}"

        # Perform update
        response = client.update_server(
            server_id,
            name=name,
            description=description,
            tags=tags,
            status=status,
        )

        # Format response
        output_lines = [
            "**Server Updated**\n",
            f"Server: {server_name} (ID: {server_id})",
        ]

        if name:
            output_lines.append(f"Name: {name}")
        if description:
            output_lines.append(f"Description: {description}")
        if tags is not None:
            output_lines.append(f"Tags: {', '.join(tags) if tags else 'None'}")
        if status:
            output_lines.append(f"Status: {status}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except ValueError as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except APIError as e:
        logger.error(f"API error updating server: {e}")
        return [TextContent(type="text", text=f"Error updating server: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating server")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_server(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle delete_server tool execution."""
    try:
        server_id = arguments["server_id"]

        logger.info(f"Deleting server {server_id}")

        # Get server name before deleting
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"ID {server_id}"

        # Delete the server
        client._request("DELETE", f"server/{server_id}")

        return [TextContent(
            type="text",
            text=(
                f"**Server Deleted**\n\n"
                f"Server '{server_name}' (ID: {server_id}) has been permanently deleted.\n\n"
                f"Warning: All monitoring data for this server has been removed."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting server: {e}")
        return [TextContent(type="text", text=f"Error deleting server: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting server")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_server_availability(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle get_server_availability tool execution."""
    try:
        server_id = arguments["server_id"]
        start_time = arguments["start_time"]
        end_time = arguments["end_time"]

        logger.info(f"Getting availability for server {server_id}")

        # Get server name for context
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"Server {server_id}"

        response = client._request(
            "GET",
            f"server/{server_id}/availability",
            params={"start_time": start_time, "end_time": end_time},
        )

        output_lines = [
            f"**Server Availability: {server_name}** (ID: {server_id})\n",
            f"Period: {start_time} to {end_time}\n",
        ]

        if isinstance(response, dict):
            availability = response.get("availability")
            if availability is not None:
                output_lines.append(f"Availability: {availability}%")

            total_downtime = response.get("total_downtime")
            if total_downtime is not None:
                output_lines.append(f"Total Downtime: {total_downtime}")

            outage_count = response.get("outage_count")
            if outage_count is not None:
                output_lines.append(f"Outage Count: {outage_count}")

            # Show any additional fields from the response
            known_keys = {"availability", "total_downtime", "outage_count", "success", "status_code"}
            extra_fields = {k: v for k, v in response.items() if k not in known_keys}
            if extra_fields:
                output_lines.append("\n**Additional Details:**")
                for key, value in extra_fields.items():
                    output_lines.append(f"  {key}: {value}")
        else:
            output_lines.append(f"Response: {response}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting server availability: {e}")
        return [TextContent(type="text", text=f"Error getting availability: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting server availability")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_server_outages(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle get_server_outages tool execution."""
    try:
        server_id = arguments["server_id"]
        limit = arguments.get("limit", 50)

        logger.info(f"Getting outages for server {server_id}")

        # Get server name for context
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"Server {server_id}"

        response = client._request(
            "GET",
            f"server/{server_id}/outage",
            params={"limit": limit},
        )

        # Parse outage list from response
        outage_list = []
        if isinstance(response, dict):
            outage_list = response.get("outage_list", response.get("outages", []))
            if not outage_list and "outage_list" not in response and "outages" not in response:
                # Response might be the list itself in some formats
                if isinstance(response.get("results"), list):
                    outage_list = response["results"]

        if not outage_list:
            return [TextContent(
                type="text",
                text=f"No outages found for {server_name} (ID: {server_id})."
            )]

        output_lines = [
            f"**Outages for {server_name}** (ID: {server_id})\n",
            f"Found {len(outage_list)} outage(s):\n",
        ]

        for outage in outage_list:
            if isinstance(outage, dict):
                outage_id = outage.get("id", "N/A")
                severity = outage.get("severity", "N/A")
                status = outage.get("status", "N/A")
                start = outage.get("start_time", "N/A")
                end = outage.get("end_time", "Active")
                description = outage.get("description", "")

                output_lines.append(f"\n**Outage {outage_id}**")
                output_lines.append(f"  Severity: {severity}")
                output_lines.append(f"  Status: {status}")
                output_lines.append(f"  Start: {start}")
                output_lines.append(f"  End: {end}")
                if description:
                    output_lines.append(f"  Description: {description}")
            else:
                output_lines.append(f"  - {outage}")

        # Pagination info
        if isinstance(response, dict):
            total = response.get("total_count") or response.get("meta", {}).get("total_count")
            if total and total > len(outage_list):
                output_lines.append(f"\n(Showing {len(outage_list)} of {total} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting server outages: {e}")
        return [TextContent(type="text", text=f"Error getting outages: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting server outages")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_server_attributes(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle list_server_attributes tool execution."""
    try:
        server_id = arguments["server_id"]

        logger.info(f"Listing attributes for server {server_id}")

        # Get server name for context
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"Server {server_id}"

        response = client._request("GET", f"server/{server_id}/server_attribute")

        # Parse attribute list
        attr_list = []
        if isinstance(response, dict):
            attr_list = (
                response.get("server_attribute_list", [])
                or response.get("attributes", [])
                or response.get("results", [])
            )

        if not attr_list:
            return [TextContent(
                type="text",
                text=f"No custom attributes found for {server_name} (ID: {server_id})."
            )]

        output_lines = [
            f"**Server Attributes for {server_name}** (ID: {server_id})\n",
            f"Found {len(attr_list)} attribute(s):\n",
        ]

        for attr in attr_list:
            if isinstance(attr, dict):
                attr_id = attr.get("id", "N/A")
                attr_name = attr.get("name", "N/A")
                attr_value = attr.get("value", "N/A")
                output_lines.append(f"  - **{attr_name}**: {attr_value} (ID: {attr_id})")
            else:
                output_lines.append(f"  - {attr}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error listing server attributes: {e}")
        return [TextContent(type="text", text=f"Error listing attributes: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing server attributes")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_server_attribute(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle create_server_attribute tool execution."""
    try:
        server_id = arguments["server_id"]
        name = arguments["name"]
        value = arguments["value"]

        logger.info(f"Creating attribute '{name}' on server {server_id}")

        # Get server name for context
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"Server {server_id}"

        response = client._request(
            "POST",
            f"server/{server_id}/server_attribute",
            json_data={"name": name, "value": value},
        )

        output_lines = [
            "**Server Attribute Created**\n",
            f"Server: {server_name} (ID: {server_id})",
            f"Name: {name}",
            f"Value: {value}",
        ]

        # Try to extract attribute ID from response
        if isinstance(response, dict):
            attr_id = response.get("id")
            if attr_id:
                output_lines.append(f"Attribute ID: {attr_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error creating server attribute: {e}")
        return [TextContent(type="text", text=f"Error creating attribute: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating server attribute")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_server_attribute(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle update_server_attribute tool execution."""
    try:
        server_id = arguments["server_id"]
        attribute_id = arguments["attribute_id"]
        value = arguments["value"]

        logger.info(f"Updating attribute {attribute_id} on server {server_id}")

        # Get server name for context
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"Server {server_id}"

        client._request(
            "PUT",
            f"server/{server_id}/server_attribute/{attribute_id}",
            json_data={"value": value},
        )

        output_lines = [
            "**Server Attribute Updated**\n",
            f"Server: {server_name} (ID: {server_id})",
            f"Attribute ID: {attribute_id}",
            f"New Value: {value}",
        ]

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server or attribute not found (server_id={arguments.get('server_id')}, attribute_id={arguments.get('attribute_id')})."
        )]
    except APIError as e:
        logger.error(f"API error updating server attribute: {e}")
        return [TextContent(type="text", text=f"Error updating attribute: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating server attribute")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_server_attribute(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle delete_server_attribute tool execution."""
    try:
        server_id = arguments["server_id"]
        attribute_id = arguments["attribute_id"]

        logger.info(f"Deleting attribute {attribute_id} from server {server_id}")

        # Get server name for context
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"Server {server_id}"

        client._request(
            "DELETE",
            f"server/{server_id}/server_attribute/{attribute_id}",
        )

        return [TextContent(
            type="text",
            text=(
                f"**Server Attribute Deleted**\n\n"
                f"Server: {server_name} (ID: {server_id})\n"
                f"Attribute ID: {attribute_id} has been removed."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server or attribute not found (server_id={arguments.get('server_id')}, attribute_id={arguments.get('attribute_id')})."
        )]
    except APIError as e:
        logger.error(f"API error deleting server attribute: {e}")
        return [TextContent(type="text", text=f"Error deleting attribute: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting server attribute")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_agent_resource_details(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle get_agent_resource_details tool execution."""
    try:
        server_id = arguments["server_id"]
        resource_id = arguments["resource_id"]

        logger.info(f"Getting agent resource {resource_id} details for server {server_id}")

        # Get server name for context
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"Server {server_id}"

        response = client._request(
            "GET",
            f"server/{server_id}/agent_resource/{resource_id}",
        )

        output_lines = [
            f"**Agent Resource Details** (Server: {server_name}, ID: {server_id})\n",
        ]

        if isinstance(response, dict):
            res_name = response.get("name", "N/A")
            output_lines.append(f"Resource: {res_name} (ID: {resource_id})")

            if response.get("resource_type"):
                output_lines.append(f"Type: {response['resource_type']}")
            if response.get("current_value") is not None:
                unit = response.get("unit", "")
                output_lines.append(f"Current Value: {response['current_value']} {unit}".strip())
            if response.get("status"):
                output_lines.append(f"Status: {response['status']}")
            if response.get("label"):
                output_lines.append(f"Label: {response['label']}")
            if response.get("last_check"):
                output_lines.append(f"Last Check: {response['last_check']}")

            # Threshold information
            if response.get("warning_threshold") is not None:
                output_lines.append(f"Warning Threshold: {response['warning_threshold']}")
            if response.get("critical_threshold") is not None:
                output_lines.append(f"Critical Threshold: {response['critical_threshold']}")

            # Show any additional fields
            known_keys = {
                "name", "resource_type", "current_value", "unit", "status",
                "label", "last_check", "warning_threshold", "critical_threshold",
                "id", "url", "success", "status_code",
            }
            extra_fields = {k: v for k, v in response.items() if k not in known_keys}
            if extra_fields:
                output_lines.append("\n**Additional Details:**")
                for key, value in extra_fields.items():
                    output_lines.append(f"  {key}: {value}")
        else:
            output_lines.append(f"Response: {response}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} or resource {arguments.get('resource_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting agent resource details: {e}")
        return [TextContent(type="text", text=f"Error getting resource details: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting agent resource details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_agent_resource_metric(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle get_agent_resource_metric tool execution."""
    try:
        server_id = arguments["server_id"]
        resource_id = arguments["resource_id"]
        timescale = arguments.get("timescale", "day")

        logger.info(
            f"Getting metric data for resource {resource_id} on server {server_id} "
            f"(timescale={timescale})"
        )

        # Get server name for context
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"Server {server_id}"

        response = client._request(
            "GET",
            f"server/{server_id}/agent_resource/{resource_id}/metric",
            params={"timescale": timescale},
        )

        output_lines = [
            f"**Agent Resource Metric Data** (Server: {server_name})\n",
            f"Resource ID: {resource_id}",
            f"Timescale: {timescale}\n",
        ]

        if isinstance(response, dict):
            # Try to extract data points
            data_points = (
                response.get("data_points", [])
                or response.get("data", [])
                or response.get("metrics", [])
            )

            if data_points:
                output_lines.append(f"Data Points: {len(data_points)}")

                # Show summary statistics if numeric
                values = []
                for dp in data_points:
                    if isinstance(dp, dict):
                        val = dp.get("value") or dp.get("y")
                        if val is not None:
                            try:
                                values.append(float(val))
                            except (ValueError, TypeError):
                                pass
                    elif isinstance(dp, (int, float)):
                        values.append(float(dp))

                if values:
                    output_lines.append(f"\n**Summary Statistics:**")
                    output_lines.append(f"  Min: {min(values):.2f}")
                    output_lines.append(f"  Max: {max(values):.2f}")
                    output_lines.append(f"  Average: {sum(values) / len(values):.2f}")
                    output_lines.append(f"  Latest: {values[-1]:.2f}")

                # Show last few data points
                output_lines.append(f"\n**Recent Data Points** (last 10):")
                for dp in data_points[-10:]:
                    if isinstance(dp, dict):
                        ts = dp.get("timestamp") or dp.get("x") or dp.get("time", "")
                        val = dp.get("value") or dp.get("y", "N/A")
                        output_lines.append(f"  {ts}: {val}")
                    else:
                        output_lines.append(f"  {dp}")
            else:
                # Show raw response fields
                known_keys = {"success", "status_code"}
                extra_fields = {k: v for k, v in response.items() if k not in known_keys}
                if extra_fields:
                    for key, value in extra_fields.items():
                        if isinstance(value, list) and len(value) > 10:
                            output_lines.append(f"{key}: [{len(value)} items]")
                        else:
                            output_lines.append(f"{key}: {value}")
                else:
                    output_lines.append("No metric data available for this timescale.")
        else:
            output_lines.append(f"Response: {response}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} or resource {arguments.get('resource_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting agent resource metric: {e}")
        return [TextContent(type="text", text=f"Error getting metric data: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting agent resource metric")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_server_logs(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle list_server_logs tool execution."""
    try:
        server_id = arguments["server_id"]
        limit = arguments.get("limit", 50)

        logger.info(f"Listing logs for server {server_id}")

        # Get server name for context
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"Server {server_id}"

        response = client._request(
            "GET",
            f"server/{server_id}/server_log",
            params={"limit": limit},
        )

        # Parse log list
        log_list = []
        if isinstance(response, dict):
            log_list = (
                response.get("server_log_list", [])
                or response.get("logs", [])
                or response.get("results", [])
            )

        if not log_list:
            return [TextContent(
                type="text",
                text=f"No log entries found for {server_name} (ID: {server_id})."
            )]

        output_lines = [
            f"**Server Logs for {server_name}** (ID: {server_id})\n",
            f"Found {len(log_list)} log entry(ies):\n",
        ]

        for log_entry in log_list:
            if isinstance(log_entry, dict):
                log_id = log_entry.get("id", "N/A")
                entry = log_entry.get("entry", "N/A")
                created = log_entry.get("created", "N/A")
                author = log_entry.get("author", "")

                output_lines.append(f"\n**Log #{log_id}** ({created})")
                if author:
                    output_lines.append(f"  Author: {author}")
                output_lines.append(f"  {entry}")
            else:
                output_lines.append(f"  - {log_entry}")

        # Pagination info
        if isinstance(response, dict):
            total = response.get("total_count") or response.get("meta", {}).get("total_count")
            if total and total > len(log_list):
                output_lines.append(f"\n(Showing {len(log_list)} of {total} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error listing server logs: {e}")
        return [TextContent(type="text", text=f"Error listing logs: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing server logs")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_server_log(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle create_server_log tool execution."""
    try:
        server_id = arguments["server_id"]
        entry = arguments["entry"]

        logger.info(f"Adding log entry to server {server_id}")

        # Get server name for context
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"Server {server_id}"

        response = client._request(
            "POST",
            f"server/{server_id}/server_log",
            json_data={"entry": entry},
        )

        output_lines = [
            "**Server Log Entry Added**\n",
            f"Server: {server_name} (ID: {server_id})",
            f"Entry: {entry}",
        ]

        # Try to extract log ID from response
        if isinstance(response, dict):
            log_id = response.get("id")
            if log_id:
                output_lines.append(f"Log ID: {log_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error creating server log: {e}")
        return [TextContent(type="text", text=f"Error creating log entry: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating server log")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_custom_incident(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle create_custom_incident tool execution."""
    try:
        server_id = arguments["server_id"]
        description = arguments["description"]
        severity = arguments.get("severity", "critical")

        logger.info(f"Creating custom incident on server {server_id} (severity={severity})")

        # Get server name for context
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
        except Exception:
            server_name = f"Server {server_id}"

        response = client._request(
            "POST",
            f"server/{server_id}/custom_incident",
            json_data={"description": description, "severity": severity},
        )

        output_lines = [
            "**Custom Incident Created**\n",
            f"Server: {server_name} (ID: {server_id})",
            f"Severity: {severity}",
            f"Description: {description}",
        ]

        # Try to extract incident ID from response
        if isinstance(response, dict):
            incident_id = response.get("id")
            if incident_id:
                output_lines.append(f"Incident ID: {incident_id}")

        output_lines.append(
            "\nNote: This incident will trigger notifications according to the server's alert configuration."
        )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error creating custom incident: {e}")
        return [TextContent(type="text", text=f"Error creating incident: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating custom incident")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_flush_server_dns(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle flush_server_dns tool execution."""
    try:
        server_id = arguments["server_id"]

        logger.info(f"Flushing DNS for server {server_id}")

        # Get server name for context
        try:
            server = client.get_server_details(server_id)
            server_name = server.name
            server_fqdn = server.fqdn or "N/A"
        except Exception:
            server_name = f"Server {server_id}"
            server_fqdn = "N/A"

        client._request("POST", f"server/{server_id}/flush_dns")

        return [TextContent(
            type="text",
            text=(
                f"**DNS Cache Flushed**\n\n"
                f"Server: {server_name} (ID: {server_id})\n"
                f"FQDN: {server_fqdn}\n\n"
                f"The DNS cache has been flushed. The server's FQDN will be "
                f"re-resolved on the next monitoring check."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error flushing DNS: {e}")
        return [TextContent(type="text", text=f"Error flushing DNS: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error flushing DNS")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# MODULE EXPORTS
# ============================================================================

SERVER_ENHANCED_TOOL_DEFINITIONS = {
    "create_server": create_server_tool_definition,
    "update_server": update_server_tool_definition,
    "delete_server": delete_server_tool_definition,
    "get_server_availability": get_server_availability_tool_definition,
    "get_server_outages": get_server_outages_tool_definition,
    "list_server_attributes": list_server_attributes_tool_definition,
    "create_server_attribute": create_server_attribute_tool_definition,
    "update_server_attribute": update_server_attribute_tool_definition,
    "delete_server_attribute": delete_server_attribute_tool_definition,
    "get_agent_resource_details": get_agent_resource_details_tool_definition,
    "get_agent_resource_metric": get_agent_resource_metric_tool_definition,
    "list_server_logs": list_server_logs_tool_definition,
    "create_server_log": create_server_log_tool_definition,
    "create_custom_incident": create_custom_incident_tool_definition,
    "flush_server_dns": flush_server_dns_tool_definition,
}

SERVER_ENHANCED_HANDLERS = {
    "create_server": handle_create_server,
    "update_server": handle_update_server,
    "delete_server": handle_delete_server,
    "get_server_availability": handle_get_server_availability,
    "get_server_outages": handle_get_server_outages,
    "list_server_attributes": handle_list_server_attributes,
    "create_server_attribute": handle_create_server_attribute,
    "update_server_attribute": handle_update_server_attribute,
    "delete_server_attribute": handle_delete_server_attribute,
    "get_agent_resource_details": handle_get_agent_resource_details,
    "get_agent_resource_metric": handle_get_agent_resource_metric,
    "list_server_logs": handle_list_server_logs,
    "create_server_log": handle_create_server_log,
    "create_custom_incident": handle_create_custom_incident,
    "flush_server_dns": handle_flush_server_dns,
}
