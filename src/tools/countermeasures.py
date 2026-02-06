"""Countermeasure, threshold, and outage metadata management tools for FortiMonitor."""

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
# TOOL DEFINITIONS - Network Service Countermeasures
# ============================================================================


def list_network_service_countermeasures_tool_definition() -> Tool:
    """Return tool definition for listing network service countermeasures."""
    return Tool(
        name="list_network_service_countermeasures",
        description=(
            "List countermeasures configured on a specific network service "
            "for a server. Countermeasures are automated remediation scripts "
            "that run when an outage is detected."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "ns_id": {
                    "type": "integer",
                    "description": "ID of the network service"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of countermeasures to return (default 50)"
                }
            },
            "required": ["server_id", "ns_id"]
        }
    )


def get_network_service_countermeasure_details_tool_definition() -> Tool:
    """Return tool definition for getting network service countermeasure details."""
    return Tool(
        name="get_network_service_countermeasure_details",
        description=(
            "Get detailed information about a specific countermeasure "
            "on a network service, including its script and configuration."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "ns_id": {
                    "type": "integer",
                    "description": "ID of the network service"
                },
                "cm_id": {
                    "type": "integer",
                    "description": "ID of the countermeasure"
                }
            },
            "required": ["server_id", "ns_id", "cm_id"]
        }
    )


def create_network_service_countermeasure_tool_definition() -> Tool:
    """Return tool definition for creating a network service countermeasure."""
    return Tool(
        name="create_network_service_countermeasure",
        description=(
            "Create a new countermeasure on a network service. "
            "Countermeasures are automated remediation scripts triggered during outages."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "ns_id": {
                    "type": "integer",
                    "description": "ID of the network service"
                },
                "name": {
                    "type": "string",
                    "description": "Name for the countermeasure (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "Description of the countermeasure (optional)"
                },
                "script": {
                    "type": "string",
                    "description": "Script content to execute as a countermeasure (optional)"
                }
            },
            "required": ["server_id", "ns_id"]
        }
    )


def update_network_service_countermeasure_tool_definition() -> Tool:
    """Return tool definition for updating a network service countermeasure."""
    return Tool(
        name="update_network_service_countermeasure",
        description=(
            "Update an existing countermeasure on a network service. "
            "Can change the name, description, or script."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "ns_id": {
                    "type": "integer",
                    "description": "ID of the network service"
                },
                "cm_id": {
                    "type": "integer",
                    "description": "ID of the countermeasure to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description (optional)"
                },
                "script": {
                    "type": "string",
                    "description": "New script content (optional)"
                }
            },
            "required": ["server_id", "ns_id", "cm_id"]
        }
    )


def delete_network_service_countermeasure_tool_definition() -> Tool:
    """Return tool definition for deleting a network service countermeasure."""
    return Tool(
        name="delete_network_service_countermeasure",
        description=(
            "Delete a countermeasure from a network service. "
            "This permanently removes the countermeasure and its script."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "ns_id": {
                    "type": "integer",
                    "description": "ID of the network service"
                },
                "cm_id": {
                    "type": "integer",
                    "description": "ID of the countermeasure to delete"
                }
            },
            "required": ["server_id", "ns_id", "cm_id"]
        }
    )


# ============================================================================
# TOOL DEFINITIONS - Threshold Countermeasures
# ============================================================================


def list_threshold_countermeasures_tool_definition() -> Tool:
    """Return tool definition for listing threshold countermeasures."""
    return Tool(
        name="list_threshold_countermeasures",
        description=(
            "List countermeasures configured on an agent resource threshold. "
            "These are automated remediation scripts triggered when a "
            "threshold is breached on an agent resource."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "ar_id": {
                    "type": "integer",
                    "description": "ID of the agent resource"
                },
                "threshold_id": {
                    "type": "integer",
                    "description": "ID of the agent resource threshold"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of countermeasures to return (default 50)"
                }
            },
            "required": ["server_id", "ar_id", "threshold_id"]
        }
    )


def get_threshold_countermeasure_details_tool_definition() -> Tool:
    """Return tool definition for getting threshold countermeasure details."""
    return Tool(
        name="get_threshold_countermeasure_details",
        description=(
            "Get detailed information about a specific countermeasure "
            "on an agent resource threshold."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "ar_id": {
                    "type": "integer",
                    "description": "ID of the agent resource"
                },
                "threshold_id": {
                    "type": "integer",
                    "description": "ID of the agent resource threshold"
                },
                "cm_id": {
                    "type": "integer",
                    "description": "ID of the countermeasure"
                }
            },
            "required": ["server_id", "ar_id", "threshold_id", "cm_id"]
        }
    )


def create_threshold_countermeasure_tool_definition() -> Tool:
    """Return tool definition for creating a threshold countermeasure."""
    return Tool(
        name="create_threshold_countermeasure",
        description=(
            "Create a new countermeasure on an agent resource threshold. "
            "Runs an automated remediation script when the threshold is breached."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "ar_id": {
                    "type": "integer",
                    "description": "ID of the agent resource"
                },
                "threshold_id": {
                    "type": "integer",
                    "description": "ID of the agent resource threshold"
                },
                "name": {
                    "type": "string",
                    "description": "Name for the countermeasure (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "Description of the countermeasure (optional)"
                },
                "script": {
                    "type": "string",
                    "description": "Script content to execute as a countermeasure (optional)"
                }
            },
            "required": ["server_id", "ar_id", "threshold_id"]
        }
    )


def update_threshold_countermeasure_tool_definition() -> Tool:
    """Return tool definition for updating a threshold countermeasure."""
    return Tool(
        name="update_threshold_countermeasure",
        description=(
            "Update an existing countermeasure on an agent resource threshold. "
            "Can change the name, description, or script."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "ar_id": {
                    "type": "integer",
                    "description": "ID of the agent resource"
                },
                "threshold_id": {
                    "type": "integer",
                    "description": "ID of the agent resource threshold"
                },
                "cm_id": {
                    "type": "integer",
                    "description": "ID of the countermeasure to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description (optional)"
                },
                "script": {
                    "type": "string",
                    "description": "New script content (optional)"
                }
            },
            "required": ["server_id", "ar_id", "threshold_id", "cm_id"]
        }
    )


def delete_threshold_countermeasure_tool_definition() -> Tool:
    """Return tool definition for deleting a threshold countermeasure."""
    return Tool(
        name="delete_threshold_countermeasure",
        description=(
            "Delete a countermeasure from an agent resource threshold. "
            "This permanently removes the countermeasure and its script."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "ar_id": {
                    "type": "integer",
                    "description": "ID of the agent resource"
                },
                "threshold_id": {
                    "type": "integer",
                    "description": "ID of the agent resource threshold"
                },
                "cm_id": {
                    "type": "integer",
                    "description": "ID of the countermeasure to delete"
                }
            },
            "required": ["server_id", "ar_id", "threshold_id", "cm_id"]
        }
    )


# ============================================================================
# TOOL DEFINITIONS - Outage Countermeasures
# ============================================================================


def list_outage_countermeasures_tool_definition() -> Tool:
    """Return tool definition for listing outage countermeasures."""
    return Tool(
        name="list_outage_countermeasures",
        description=(
            "List countermeasures that were executed or are configured "
            "for a specific outage."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "ID of the outage"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of countermeasures to return (default 50)"
                }
            },
            "required": ["outage_id"]
        }
    )


def get_outage_countermeasure_details_tool_definition() -> Tool:
    """Return tool definition for getting outage countermeasure details."""
    return Tool(
        name="get_outage_countermeasure_details",
        description=(
            "Get detailed information about a specific countermeasure "
            "associated with an outage, including execution status and results."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "ID of the outage"
                },
                "cm_id": {
                    "type": "integer",
                    "description": "ID of the countermeasure"
                }
            },
            "required": ["outage_id", "cm_id"]
        }
    )


# ============================================================================
# TOOL DEFINITIONS - Outage Countermeasure Metadata & Output
# ============================================================================


def get_outage_countermeasure_metadata_tool_definition() -> Tool:
    """Return tool definition for getting outage countermeasure metadata."""
    return Tool(
        name="get_outage_countermeasure_metadata",
        description=(
            "Get metadata about countermeasures for a specific outage. "
            "Shows configuration and execution metadata for all "
            "countermeasures associated with the outage."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "ID of the outage"
                }
            },
            "required": ["outage_id"]
        }
    )


def get_outage_countermeasure_output_tool_definition() -> Tool:
    """Return tool definition for getting outage countermeasure output."""
    return Tool(
        name="get_outage_countermeasure_output",
        description=(
            "Get the output produced by countermeasures executed during "
            "a specific outage. Shows script execution results, stdout, "
            "and stderr from countermeasure runs."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "ID of the outage"
                }
            },
            "required": ["outage_id"]
        }
    )


# ============================================================================
# TOOL DEFINITIONS - Outage Metadata
# ============================================================================


def list_outage_metadata_tool_definition() -> Tool:
    """Return tool definition for listing outage metadata."""
    return Tool(
        name="list_outage_metadata",
        description=(
            "List metadata entries associated with a specific outage. "
            "Outage metadata contains additional context and diagnostic "
            "information collected during the outage."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "ID of the outage"
                }
            },
            "required": ["outage_id"]
        }
    )


def get_outage_metadata_details_tool_definition() -> Tool:
    """Return tool definition for getting outage metadata details."""
    return Tool(
        name="get_outage_metadata_details",
        description=(
            "Get detailed information about a specific outage metadata "
            "entry, including its key, value, and associated context."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "ID of the outage"
                },
                "metadata_id": {
                    "type": "integer",
                    "description": "ID of the metadata entry"
                }
            },
            "required": ["outage_id", "metadata_id"]
        }
    )


# ============================================================================
# TOOL DEFINITIONS - Outage Preoutage Graph
# ============================================================================


def get_outage_preoutage_graph_tool_definition() -> Tool:
    """Return tool definition for getting outage preoutage graph data."""
    return Tool(
        name="get_outage_preoutage_graph",
        description=(
            "Get pre-outage graph data for a specific outage. "
            "This returns metric data from before the outage started, "
            "useful for identifying trends that led to the incident."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "ID of the outage"
                }
            },
            "required": ["outage_id"]
        }
    )


# ============================================================================
# TOOL DEFINITIONS - Threshold Management
# ============================================================================


def get_agent_resource_threshold_tool_definition() -> Tool:
    """Return tool definition for getting an agent resource threshold."""
    return Tool(
        name="get_agent_resource_threshold",
        description=(
            "Get detailed information about a specific threshold configured "
            "on an agent resource, including warning and critical threshold "
            "values and configuration."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "ar_id": {
                    "type": "integer",
                    "description": "ID of the agent resource"
                },
                "threshold_id": {
                    "type": "integer",
                    "description": "ID of the agent resource threshold"
                }
            },
            "required": ["server_id", "ar_id", "threshold_id"]
        }
    )


def update_agent_resource_threshold_tool_definition() -> Tool:
    """Return tool definition for updating an agent resource threshold."""
    return Tool(
        name="update_agent_resource_threshold",
        description=(
            "Update an agent resource threshold. Can change the warning "
            "threshold, critical threshold, or name."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "ar_id": {
                    "type": "integer",
                    "description": "ID of the agent resource"
                },
                "threshold_id": {
                    "type": "integer",
                    "description": "ID of the agent resource threshold to update"
                },
                "warning_threshold": {
                    "type": "number",
                    "description": "New warning threshold value (optional)"
                },
                "critical_threshold": {
                    "type": "number",
                    "description": "New critical threshold value (optional)"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the threshold (optional)"
                }
            },
            "required": ["server_id", "ar_id", "threshold_id"]
        }
    )


def delete_agent_resource_threshold_tool_definition() -> Tool:
    """Return tool definition for deleting an agent resource threshold."""
    return Tool(
        name="delete_agent_resource_threshold",
        description=(
            "Delete an agent resource threshold. This removes the "
            "threshold and stops alerting based on it."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "ar_id": {
                    "type": "integer",
                    "description": "ID of the agent resource"
                },
                "threshold_id": {
                    "type": "integer",
                    "description": "ID of the agent resource threshold to delete"
                }
            },
            "required": ["server_id", "ar_id", "threshold_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS - Network Service Countermeasures
# ============================================================================


async def handle_list_network_service_countermeasures(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_network_service_countermeasures tool execution."""
    try:
        server_id = arguments["server_id"]
        ns_id = arguments["ns_id"]
        limit = arguments.get("limit", 50)

        logger.info(
            f"Listing countermeasures for network service {ns_id} "
            f"on server {server_id} (limit={limit})"
        )

        response = client._request(
            "GET",
            f"server/{server_id}/network_service/{ns_id}/countermeasure",
            params={"limit": limit}
        )
        countermeasures = response.get("countermeasure_list", [])
        meta = response.get("meta", {})

        if not countermeasures:
            return [TextContent(
                type="text",
                text=(
                    f"No countermeasures found for network service {ns_id} "
                    f"on server {server_id}."
                )
            )]

        total_count = meta.get("total_count", len(countermeasures))

        output_lines = [
            f"**Network Service Countermeasures**\n",
            f"Server ID: {server_id} | Network Service ID: {ns_id}\n",
            f"Found {len(countermeasures)} countermeasure(s):\n"
        ]

        for cm in countermeasures:
            name = cm.get("name", "Unknown")
            cm_id = _extract_id_from_url(cm.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {cm_id})")
            if cm.get("description"):
                output_lines.append(f"  Description: {cm['description']}")
            if cm.get("script"):
                output_lines.append(f"  Script: (configured)")

        if total_count > len(countermeasures):
            output_lines.append(
                f"\n(Showing {len(countermeasures)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Network service {arguments.get('ns_id')} not found "
                f"on server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error listing network service countermeasures: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing network service countermeasures")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_network_service_countermeasure_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_network_service_countermeasure_details tool execution."""
    try:
        server_id = arguments["server_id"]
        ns_id = arguments["ns_id"]
        cm_id = arguments["cm_id"]

        logger.info(
            f"Getting countermeasure {cm_id} for network service {ns_id} "
            f"on server {server_id}"
        )

        response = client._request(
            "GET",
            f"server/{server_id}/network_service/{ns_id}/countermeasure/{cm_id}"
        )

        name = response.get("name", "Unknown")
        output_lines = [
            f"**Countermeasure: {name}** (ID: {cm_id})\n",
            f"Server ID: {server_id}",
            f"Network Service ID: {ns_id}"
        ]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")
        if response.get("script"):
            output_lines.append(f"Script:\n{response['script']}")

        for key, value in response.items():
            if key not in (
                "name", "description", "url", "resource_uri", "script"
            ) and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Countermeasure {arguments.get('cm_id')} not found "
                f"for network service {arguments.get('ns_id')} "
                f"on server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error getting countermeasure details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting countermeasure details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_network_service_countermeasure(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_network_service_countermeasure tool execution."""
    try:
        server_id = arguments["server_id"]
        ns_id = arguments["ns_id"]
        name = arguments.get("name")
        description = arguments.get("description")
        script = arguments.get("script")

        logger.info(
            f"Creating countermeasure for network service {ns_id} "
            f"on server {server_id}"
        )

        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        if script:
            data["script"] = script

        response = client._request(
            "POST",
            f"server/{server_id}/network_service/{ns_id}/countermeasure",
            json_data=data
        )

        output_lines = [
            "**Countermeasure Created**\n",
            f"Server ID: {server_id}",
            f"Network Service ID: {ns_id}"
        ]

        if name:
            output_lines.append(f"Name: {name}")
        if description:
            output_lines.append(f"Description: {description}")
        if script:
            output_lines.append(f"Script: (configured)")

        if isinstance(response, dict) and response.get("url"):
            new_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Countermeasure ID: {new_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Network service {arguments.get('ns_id')} not found "
                f"on server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error creating countermeasure: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating countermeasure")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_network_service_countermeasure(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_network_service_countermeasure tool execution."""
    try:
        server_id = arguments["server_id"]
        ns_id = arguments["ns_id"]
        cm_id = arguments["cm_id"]
        name = arguments.get("name")
        description = arguments.get("description")
        script = arguments.get("script")

        if name is None and description is None and script is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name', 'description', or 'script' must be provided."
            )]

        logger.info(
            f"Updating countermeasure {cm_id} for network service {ns_id} "
            f"on server {server_id}"
        )

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if script is not None:
            data["script"] = script

        client._request(
            "PUT",
            f"server/{server_id}/network_service/{ns_id}/countermeasure/{cm_id}",
            json_data=data
        )

        output_lines = [
            "**Countermeasure Updated**\n",
            f"Server ID: {server_id}",
            f"Network Service ID: {ns_id}",
            f"Countermeasure ID: {cm_id}"
        ]

        if name is not None:
            output_lines.append(f"Name: {name}")
        if description is not None:
            output_lines.append(f"Description: Updated")
        if script is not None:
            output_lines.append(f"Script: Updated")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Countermeasure {arguments.get('cm_id')} not found "
                f"for network service {arguments.get('ns_id')} "
                f"on server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error updating countermeasure: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating countermeasure")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_network_service_countermeasure(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_network_service_countermeasure tool execution."""
    try:
        server_id = arguments["server_id"]
        ns_id = arguments["ns_id"]
        cm_id = arguments["cm_id"]

        logger.info(
            f"Deleting countermeasure {cm_id} from network service {ns_id} "
            f"on server {server_id}"
        )

        client._request(
            "DELETE",
            f"server/{server_id}/network_service/{ns_id}/countermeasure/{cm_id}"
        )

        return [TextContent(
            type="text",
            text=(
                f"**Countermeasure Deleted**\n\n"
                f"Countermeasure {cm_id} has been removed from "
                f"network service {ns_id} on server {server_id}."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Countermeasure {arguments.get('cm_id')} not found "
                f"for network service {arguments.get('ns_id')} "
                f"on server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error deleting countermeasure: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting countermeasure")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# TOOL HANDLERS - Threshold Countermeasures
# ============================================================================


async def handle_list_threshold_countermeasures(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_threshold_countermeasures tool execution."""
    try:
        server_id = arguments["server_id"]
        ar_id = arguments["ar_id"]
        threshold_id = arguments["threshold_id"]
        limit = arguments.get("limit", 50)

        logger.info(
            f"Listing countermeasures for threshold {threshold_id} on "
            f"agent resource {ar_id} on server {server_id} (limit={limit})"
        )

        response = client._request(
            "GET",
            f"server/{server_id}/agent_resource/{ar_id}"
            f"/agent_resource_threshold/{threshold_id}/countermeasure",
            params={"limit": limit}
        )
        countermeasures = response.get("countermeasure_list", [])
        meta = response.get("meta", {})

        if not countermeasures:
            return [TextContent(
                type="text",
                text=(
                    f"No countermeasures found for threshold {threshold_id} on "
                    f"agent resource {ar_id} on server {server_id}."
                )
            )]

        total_count = meta.get("total_count", len(countermeasures))

        output_lines = [
            f"**Threshold Countermeasures**\n",
            f"Server ID: {server_id} | Agent Resource ID: {ar_id} | "
            f"Threshold ID: {threshold_id}\n",
            f"Found {len(countermeasures)} countermeasure(s):\n"
        ]

        for cm in countermeasures:
            name = cm.get("name", "Unknown")
            cm_id = _extract_id_from_url(cm.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {cm_id})")
            if cm.get("description"):
                output_lines.append(f"  Description: {cm['description']}")
            if cm.get("script"):
                output_lines.append(f"  Script: (configured)")

        if total_count > len(countermeasures):
            output_lines.append(
                f"\n(Showing {len(countermeasures)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Threshold {arguments.get('threshold_id')} not found on "
                f"agent resource {arguments.get('ar_id')} on "
                f"server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error listing threshold countermeasures: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing threshold countermeasures")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_threshold_countermeasure_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_threshold_countermeasure_details tool execution."""
    try:
        server_id = arguments["server_id"]
        ar_id = arguments["ar_id"]
        threshold_id = arguments["threshold_id"]
        cm_id = arguments["cm_id"]

        logger.info(
            f"Getting countermeasure {cm_id} for threshold {threshold_id} on "
            f"agent resource {ar_id} on server {server_id}"
        )

        response = client._request(
            "GET",
            f"server/{server_id}/agent_resource/{ar_id}"
            f"/agent_resource_threshold/{threshold_id}/countermeasure/{cm_id}"
        )

        name = response.get("name", "Unknown")
        output_lines = [
            f"**Threshold Countermeasure: {name}** (ID: {cm_id})\n",
            f"Server ID: {server_id}",
            f"Agent Resource ID: {ar_id}",
            f"Threshold ID: {threshold_id}"
        ]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")
        if response.get("script"):
            output_lines.append(f"Script:\n{response['script']}")

        for key, value in response.items():
            if key not in (
                "name", "description", "url", "resource_uri", "script"
            ) and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Countermeasure {arguments.get('cm_id')} not found "
                f"for threshold {arguments.get('threshold_id')} on "
                f"agent resource {arguments.get('ar_id')} on "
                f"server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error getting threshold countermeasure details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting threshold countermeasure details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_threshold_countermeasure(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_threshold_countermeasure tool execution."""
    try:
        server_id = arguments["server_id"]
        ar_id = arguments["ar_id"]
        threshold_id = arguments["threshold_id"]
        name = arguments.get("name")
        description = arguments.get("description")
        script = arguments.get("script")

        logger.info(
            f"Creating countermeasure for threshold {threshold_id} on "
            f"agent resource {ar_id} on server {server_id}"
        )

        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        if script:
            data["script"] = script

        response = client._request(
            "POST",
            f"server/{server_id}/agent_resource/{ar_id}"
            f"/agent_resource_threshold/{threshold_id}/countermeasure",
            json_data=data
        )

        output_lines = [
            "**Threshold Countermeasure Created**\n",
            f"Server ID: {server_id}",
            f"Agent Resource ID: {ar_id}",
            f"Threshold ID: {threshold_id}"
        ]

        if name:
            output_lines.append(f"Name: {name}")
        if description:
            output_lines.append(f"Description: {description}")
        if script:
            output_lines.append(f"Script: (configured)")

        if isinstance(response, dict) and response.get("url"):
            new_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Countermeasure ID: {new_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Threshold {arguments.get('threshold_id')} not found on "
                f"agent resource {arguments.get('ar_id')} on "
                f"server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error creating threshold countermeasure: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating threshold countermeasure")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_threshold_countermeasure(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_threshold_countermeasure tool execution."""
    try:
        server_id = arguments["server_id"]
        ar_id = arguments["ar_id"]
        threshold_id = arguments["threshold_id"]
        cm_id = arguments["cm_id"]
        name = arguments.get("name")
        description = arguments.get("description")
        script = arguments.get("script")

        if name is None and description is None and script is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name', 'description', or 'script' must be provided."
            )]

        logger.info(
            f"Updating countermeasure {cm_id} for threshold {threshold_id} on "
            f"agent resource {ar_id} on server {server_id}"
        )

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if script is not None:
            data["script"] = script

        client._request(
            "PUT",
            f"server/{server_id}/agent_resource/{ar_id}"
            f"/agent_resource_threshold/{threshold_id}/countermeasure/{cm_id}",
            json_data=data
        )

        output_lines = [
            "**Threshold Countermeasure Updated**\n",
            f"Server ID: {server_id}",
            f"Agent Resource ID: {ar_id}",
            f"Threshold ID: {threshold_id}",
            f"Countermeasure ID: {cm_id}"
        ]

        if name is not None:
            output_lines.append(f"Name: {name}")
        if description is not None:
            output_lines.append(f"Description: Updated")
        if script is not None:
            output_lines.append(f"Script: Updated")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Countermeasure {arguments.get('cm_id')} not found "
                f"for threshold {arguments.get('threshold_id')} on "
                f"agent resource {arguments.get('ar_id')} on "
                f"server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error updating threshold countermeasure: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating threshold countermeasure")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_threshold_countermeasure(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_threshold_countermeasure tool execution."""
    try:
        server_id = arguments["server_id"]
        ar_id = arguments["ar_id"]
        threshold_id = arguments["threshold_id"]
        cm_id = arguments["cm_id"]

        logger.info(
            f"Deleting countermeasure {cm_id} from threshold {threshold_id} on "
            f"agent resource {ar_id} on server {server_id}"
        )

        client._request(
            "DELETE",
            f"server/{server_id}/agent_resource/{ar_id}"
            f"/agent_resource_threshold/{threshold_id}/countermeasure/{cm_id}"
        )

        return [TextContent(
            type="text",
            text=(
                f"**Threshold Countermeasure Deleted**\n\n"
                f"Countermeasure {cm_id} has been removed from "
                f"threshold {threshold_id} on agent resource {ar_id} "
                f"on server {server_id}."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Countermeasure {arguments.get('cm_id')} not found "
                f"for threshold {arguments.get('threshold_id')} on "
                f"agent resource {arguments.get('ar_id')} on "
                f"server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error deleting threshold countermeasure: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting threshold countermeasure")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# TOOL HANDLERS - Outage Countermeasures
# ============================================================================


async def handle_list_outage_countermeasures(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_outage_countermeasures tool execution."""
    try:
        outage_id = arguments["outage_id"]
        limit = arguments.get("limit", 50)

        logger.info(
            f"Listing countermeasures for outage {outage_id} (limit={limit})"
        )

        response = client._request(
            "GET",
            f"outage/{outage_id}/countermeasure",
            params={"limit": limit}
        )
        countermeasures = response.get("countermeasure_list", [])
        meta = response.get("meta", {})

        if not countermeasures:
            return [TextContent(
                type="text",
                text=f"No countermeasures found for outage {outage_id}."
            )]

        total_count = meta.get("total_count", len(countermeasures))

        output_lines = [
            f"**Outage Countermeasures**\n",
            f"Outage ID: {outage_id}\n",
            f"Found {len(countermeasures)} countermeasure(s):\n"
        ]

        for cm in countermeasures:
            name = cm.get("name", "Unknown")
            cm_id = _extract_id_from_url(cm.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {cm_id})")
            if cm.get("description"):
                output_lines.append(f"  Description: {cm['description']}")
            if cm.get("status"):
                output_lines.append(f"  Status: {cm['status']}")

        if total_count > len(countermeasures):
            output_lines.append(
                f"\n(Showing {len(countermeasures)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Outage {arguments.get('outage_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error listing outage countermeasures: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing outage countermeasures")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_outage_countermeasure_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_outage_countermeasure_details tool execution."""
    try:
        outage_id = arguments["outage_id"]
        cm_id = arguments["cm_id"]

        logger.info(
            f"Getting countermeasure {cm_id} for outage {outage_id}"
        )

        response = client._request(
            "GET", f"outage/{outage_id}/countermeasure/{cm_id}"
        )

        name = response.get("name", "Unknown")
        output_lines = [
            f"**Outage Countermeasure: {name}** (ID: {cm_id})\n",
            f"Outage ID: {outage_id}"
        ]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")
        if response.get("status"):
            output_lines.append(f"Status: {response['status']}")
        if response.get("script"):
            output_lines.append(f"Script:\n{response['script']}")

        for key, value in response.items():
            if key not in (
                "name", "description", "url", "resource_uri",
                "status", "script"
            ) and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Countermeasure {arguments.get('cm_id')} not found "
                f"for outage {arguments.get('outage_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error getting outage countermeasure details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting outage countermeasure details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# TOOL HANDLERS - Outage Countermeasure Metadata & Output
# ============================================================================


async def handle_get_outage_countermeasure_metadata(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_outage_countermeasure_metadata tool execution."""
    try:
        outage_id = arguments["outage_id"]

        logger.info(
            f"Getting countermeasure metadata for outage {outage_id}"
        )

        response = client._request(
            "GET", f"outage/{outage_id}/countermeasure_metadata"
        )

        output_lines = [
            f"**Outage Countermeasure Metadata**\n",
            f"Outage ID: {outage_id}\n"
        ]

        if isinstance(response, dict):
            for key, value in response.items():
                if key not in ("url", "resource_uri") and value:
                    output_lines.append(f"{key}: {value}")
        elif isinstance(response, list):
            if not response:
                return [TextContent(
                    type="text",
                    text=f"No countermeasure metadata found for outage {outage_id}."
                )]
            for item in response:
                if isinstance(item, dict):
                    for key, value in item.items():
                        if key not in ("url", "resource_uri") and value:
                            output_lines.append(f"{key}: {value}")
                    output_lines.append("")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Outage {arguments.get('outage_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting countermeasure metadata: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting countermeasure metadata")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_outage_countermeasure_output(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_outage_countermeasure_output tool execution."""
    try:
        outage_id = arguments["outage_id"]

        logger.info(
            f"Getting countermeasure output for outage {outage_id}"
        )

        response = client._request(
            "GET", f"outage/{outage_id}/countermeasure_output"
        )

        output_lines = [
            f"**Outage Countermeasure Output**\n",
            f"Outage ID: {outage_id}\n"
        ]

        if isinstance(response, dict):
            for key, value in response.items():
                if key not in ("url", "resource_uri") and value:
                    output_lines.append(f"{key}: {value}")
        elif isinstance(response, list):
            if not response:
                return [TextContent(
                    type="text",
                    text=f"No countermeasure output found for outage {outage_id}."
                )]
            for item in response:
                if isinstance(item, dict):
                    name = item.get("name", "Unknown")
                    output_lines.append(f"\n**{name}**")
                    for key, value in item.items():
                        if key not in ("name", "url", "resource_uri") and value:
                            output_lines.append(f"  {key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Outage {arguments.get('outage_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting countermeasure output: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting countermeasure output")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# TOOL HANDLERS - Outage Metadata
# ============================================================================


async def handle_list_outage_metadata(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_outage_metadata tool execution."""
    try:
        outage_id = arguments["outage_id"]

        logger.info(f"Listing metadata for outage {outage_id}")

        response = client._request(
            "GET", f"outage/{outage_id}/outage_metadata"
        )
        metadata_list = response.get("outage_metadata_list", [])
        meta = response.get("meta", {})

        if not metadata_list:
            return [TextContent(
                type="text",
                text=f"No metadata found for outage {outage_id}."
            )]

        total_count = meta.get("total_count", len(metadata_list))

        output_lines = [
            f"**Outage Metadata**\n",
            f"Outage ID: {outage_id}\n",
            f"Found {len(metadata_list)} metadata entry(ies):\n"
        ]

        for entry in metadata_list:
            name = entry.get("name", entry.get("key", "Unknown"))
            entry_id = _extract_id_from_url(entry.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {entry_id})")
            if entry.get("value"):
                output_lines.append(f"  Value: {entry['value']}")
            if entry.get("description"):
                output_lines.append(f"  Description: {entry['description']}")

        if total_count > len(metadata_list):
            output_lines.append(
                f"\n(Showing {len(metadata_list)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Outage {arguments.get('outage_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error listing outage metadata: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing outage metadata")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_outage_metadata_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_outage_metadata_details tool execution."""
    try:
        outage_id = arguments["outage_id"]
        metadata_id = arguments["metadata_id"]

        logger.info(
            f"Getting metadata {metadata_id} for outage {outage_id}"
        )

        response = client._request(
            "GET",
            f"outage/{outage_id}/outage_metadata/{metadata_id}"
        )

        name = response.get("name", response.get("key", "Unknown"))
        output_lines = [
            f"**Outage Metadata: {name}** (ID: {metadata_id})\n",
            f"Outage ID: {outage_id}"
        ]

        if response.get("value"):
            output_lines.append(f"Value: {response['value']}")
        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        for key, value in response.items():
            if key not in (
                "name", "key", "value", "description", "url", "resource_uri"
            ) and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Metadata {arguments.get('metadata_id')} not found "
                f"for outage {arguments.get('outage_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error getting outage metadata details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting outage metadata details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# TOOL HANDLERS - Outage Preoutage Graph
# ============================================================================


async def handle_get_outage_preoutage_graph(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_outage_preoutage_graph tool execution."""
    try:
        outage_id = arguments["outage_id"]

        logger.info(f"Getting preoutage graph for outage {outage_id}")

        response = client._request(
            "GET", f"outage/{outage_id}/preoutage_graph"
        )

        output_lines = [
            f"**Pre-Outage Graph Data**\n",
            f"Outage ID: {outage_id}\n"
        ]

        if isinstance(response, dict):
            data_points = response.get(
                "data", response.get("data_points", [])
            )
            if isinstance(data_points, list) and data_points:
                output_lines.append(f"Data Points: {len(data_points)}\n")
                for point in data_points[:20]:
                    if isinstance(point, dict):
                        time_val = point.get(
                            "time", point.get("timestamp", "")
                        )
                        value = point.get(
                            "value", point.get("metric", "")
                        )
                        output_lines.append(f"  {time_val}: {value}")
                if len(data_points) > 20:
                    output_lines.append(
                        f"  ... and {len(data_points) - 20} more data points"
                    )
            else:
                for key, value in response.items():
                    if key not in (
                        "url", "resource_uri", "success", "status_code"
                    ) and value:
                        output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Outage {arguments.get('outage_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting preoutage graph: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting preoutage graph")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# TOOL HANDLERS - Threshold Management
# ============================================================================


async def handle_get_agent_resource_threshold(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_agent_resource_threshold tool execution."""
    try:
        server_id = arguments["server_id"]
        ar_id = arguments["ar_id"]
        threshold_id = arguments["threshold_id"]

        logger.info(
            f"Getting threshold {threshold_id} for agent resource {ar_id} "
            f"on server {server_id}"
        )

        response = client._request(
            "GET",
            f"server/{server_id}/agent_resource/{ar_id}"
            f"/agent_resource_threshold/{threshold_id}"
        )

        name = response.get("name", "Unknown")
        output_lines = [
            f"**Agent Resource Threshold: {name}** (ID: {threshold_id})\n",
            f"Server ID: {server_id}",
            f"Agent Resource ID: {ar_id}"
        ]

        if response.get("warning_threshold") is not None:
            output_lines.append(
                f"Warning Threshold: {response['warning_threshold']}"
            )
        if response.get("critical_threshold") is not None:
            output_lines.append(
                f"Critical Threshold: {response['critical_threshold']}"
            )
        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        for key, value in response.items():
            if key not in (
                "name", "description", "url", "resource_uri",
                "warning_threshold", "critical_threshold"
            ) and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Threshold {arguments.get('threshold_id')} not found "
                f"for agent resource {arguments.get('ar_id')} on "
                f"server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error getting agent resource threshold: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting agent resource threshold")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_agent_resource_threshold(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_agent_resource_threshold tool execution."""
    try:
        server_id = arguments["server_id"]
        ar_id = arguments["ar_id"]
        threshold_id = arguments["threshold_id"]
        warning_threshold = arguments.get("warning_threshold")
        critical_threshold = arguments.get("critical_threshold")
        name = arguments.get("name")

        if (warning_threshold is None and critical_threshold is None
                and name is None):
            return [TextContent(
                type="text",
                text=(
                    "Error: At least one of 'warning_threshold', "
                    "'critical_threshold', or 'name' must be provided."
                )
            )]

        logger.info(
            f"Updating threshold {threshold_id} for agent resource {ar_id} "
            f"on server {server_id}"
        )

        data = {}
        if warning_threshold is not None:
            data["warning_threshold"] = warning_threshold
        if critical_threshold is not None:
            data["critical_threshold"] = critical_threshold
        if name is not None:
            data["name"] = name

        client._request(
            "PUT",
            f"server/{server_id}/agent_resource/{ar_id}"
            f"/agent_resource_threshold/{threshold_id}",
            json_data=data
        )

        output_lines = [
            "**Agent Resource Threshold Updated**\n",
            f"Server ID: {server_id}",
            f"Agent Resource ID: {ar_id}",
            f"Threshold ID: {threshold_id}"
        ]

        if name is not None:
            output_lines.append(f"Name: {name}")
        if warning_threshold is not None:
            output_lines.append(f"Warning Threshold: {warning_threshold}")
        if critical_threshold is not None:
            output_lines.append(f"Critical Threshold: {critical_threshold}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Threshold {arguments.get('threshold_id')} not found "
                f"for agent resource {arguments.get('ar_id')} on "
                f"server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error updating agent resource threshold: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating agent resource threshold")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_agent_resource_threshold(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_agent_resource_threshold tool execution."""
    try:
        server_id = arguments["server_id"]
        ar_id = arguments["ar_id"]
        threshold_id = arguments["threshold_id"]

        logger.info(
            f"Deleting threshold {threshold_id} from agent resource {ar_id} "
            f"on server {server_id}"
        )

        client._request(
            "DELETE",
            f"server/{server_id}/agent_resource/{ar_id}"
            f"/agent_resource_threshold/{threshold_id}"
        )

        return [TextContent(
            type="text",
            text=(
                f"**Agent Resource Threshold Deleted**\n\n"
                f"Threshold {threshold_id} has been removed from "
                f"agent resource {ar_id} on server {server_id}.\n\n"
                f"Alerting based on this threshold has been stopped."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: Threshold {arguments.get('threshold_id')} not found "
                f"for agent resource {arguments.get('ar_id')} on "
                f"server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error deleting agent resource threshold: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting agent resource threshold")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

COUNTERMEASURES_TOOL_DEFINITIONS = {
    # Network service countermeasures
    "list_network_service_countermeasures": list_network_service_countermeasures_tool_definition,
    "get_network_service_countermeasure_details": get_network_service_countermeasure_details_tool_definition,
    "create_network_service_countermeasure": create_network_service_countermeasure_tool_definition,
    "update_network_service_countermeasure": update_network_service_countermeasure_tool_definition,
    "delete_network_service_countermeasure": delete_network_service_countermeasure_tool_definition,
    # Threshold countermeasures
    "list_threshold_countermeasures": list_threshold_countermeasures_tool_definition,
    "get_threshold_countermeasure_details": get_threshold_countermeasure_details_tool_definition,
    "create_threshold_countermeasure": create_threshold_countermeasure_tool_definition,
    "update_threshold_countermeasure": update_threshold_countermeasure_tool_definition,
    "delete_threshold_countermeasure": delete_threshold_countermeasure_tool_definition,
    # Outage countermeasures
    "list_outage_countermeasures": list_outage_countermeasures_tool_definition,
    "get_outage_countermeasure_details": get_outage_countermeasure_details_tool_definition,
    # Outage countermeasure metadata & output
    "get_outage_countermeasure_metadata": get_outage_countermeasure_metadata_tool_definition,
    "get_outage_countermeasure_output": get_outage_countermeasure_output_tool_definition,
    # Outage metadata
    "list_outage_metadata": list_outage_metadata_tool_definition,
    "get_outage_metadata_details": get_outage_metadata_details_tool_definition,
    # Outage preoutage graph
    "get_outage_preoutage_graph": get_outage_preoutage_graph_tool_definition,
    # Threshold management
    "get_agent_resource_threshold": get_agent_resource_threshold_tool_definition,
    "update_agent_resource_threshold": update_agent_resource_threshold_tool_definition,
    "delete_agent_resource_threshold": delete_agent_resource_threshold_tool_definition,
}

COUNTERMEASURES_HANDLERS = {
    # Network service countermeasures
    "list_network_service_countermeasures": handle_list_network_service_countermeasures,
    "get_network_service_countermeasure_details": handle_get_network_service_countermeasure_details,
    "create_network_service_countermeasure": handle_create_network_service_countermeasure,
    "update_network_service_countermeasure": handle_update_network_service_countermeasure,
    "delete_network_service_countermeasure": handle_delete_network_service_countermeasure,
    # Threshold countermeasures
    "list_threshold_countermeasures": handle_list_threshold_countermeasures,
    "get_threshold_countermeasure_details": handle_get_threshold_countermeasure_details,
    "create_threshold_countermeasure": handle_create_threshold_countermeasure,
    "update_threshold_countermeasure": handle_update_threshold_countermeasure,
    "delete_threshold_countermeasure": handle_delete_threshold_countermeasure,
    # Outage countermeasures
    "list_outage_countermeasures": handle_list_outage_countermeasures,
    "get_outage_countermeasure_details": handle_get_outage_countermeasure_details,
    # Outage countermeasure metadata & output
    "get_outage_countermeasure_metadata": handle_get_outage_countermeasure_metadata,
    "get_outage_countermeasure_output": handle_get_outage_countermeasure_output,
    # Outage metadata
    "list_outage_metadata": handle_list_outage_metadata,
    "get_outage_metadata_details": handle_get_outage_metadata_details,
    # Outage preoutage graph
    "get_outage_preoutage_graph": handle_get_outage_preoutage_graph,
    # Threshold management
    "get_agent_resource_threshold": handle_get_agent_resource_threshold,
    "update_agent_resource_threshold": handle_update_agent_resource_threshold,
    "delete_agent_resource_threshold": handle_delete_agent_resource_threshold,
}
