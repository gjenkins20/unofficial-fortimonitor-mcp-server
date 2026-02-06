"""Digital Experience Monitoring (DEM) tools for FortiMonitor."""

import logging
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def list_dem_applications_tool_definition() -> Tool:
    """Return tool definition for listing DEM applications."""
    return Tool(
        name="list_dem_applications",
        description=(
            "List all Digital Experience Monitoring (DEM) applications. "
            "DEM applications monitor end-user experience for web applications and services."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of applications to return (default 50)"
                }
            }
        }
    )


def create_dem_application_tool_definition() -> Tool:
    """Return tool definition for creating a DEM application."""
    return Tool(
        name="create_dem_application",
        description=(
            "Create a new DEM application for monitoring end-user experience."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the DEM application"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the application"
                }
            },
            "required": ["name"]
        }
    )


def get_dem_application_details_tool_definition() -> Tool:
    """Return tool definition for getting DEM application details."""
    return Tool(
        name="get_dem_application_details",
        description=(
            "Get detailed information about a specific DEM application."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "application_id": {
                    "type": "integer",
                    "description": "ID of the DEM application"
                }
            },
            "required": ["application_id"]
        }
    )


def update_dem_application_tool_definition() -> Tool:
    """Return tool definition for updating a DEM application."""
    return Tool(
        name="update_dem_application",
        description=(
            "Update an existing DEM application's name or description."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "application_id": {
                    "type": "integer",
                    "description": "ID of the DEM application to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the application (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description for the application (optional)"
                }
            },
            "required": ["application_id"]
        }
    )


def delete_dem_application_tool_definition() -> Tool:
    """Return tool definition for deleting a DEM application."""
    return Tool(
        name="delete_dem_application",
        description=(
            "Delete a DEM application and all its associated monitoring instances."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "application_id": {
                    "type": "integer",
                    "description": "ID of the DEM application to delete"
                }
            },
            "required": ["application_id"]
        }
    )


def list_dem_instances_tool_definition() -> Tool:
    """Return tool definition for listing DEM instances."""
    return Tool(
        name="list_dem_instances",
        description=(
            "List monitoring instances for a specific DEM application. "
            "Instances represent individual monitoring checks within the application."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "application_id": {
                    "type": "integer",
                    "description": "ID of the DEM application"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of instances to return (default 50)"
                }
            },
            "required": ["application_id"]
        }
    )


def create_dem_instance_tool_definition() -> Tool:
    """Return tool definition for creating a DEM instance."""
    return Tool(
        name="create_dem_instance",
        description=(
            "Create a new monitoring instance within a DEM application."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "application_id": {
                    "type": "integer",
                    "description": "ID of the DEM application"
                },
                "template": {
                    "type": "string",
                    "description": "Optional template to use for the instance configuration"
                }
            },
            "required": ["application_id"]
        }
    )


def get_dem_locations_tool_definition() -> Tool:
    """Return tool definition for getting DEM locations."""
    return Tool(
        name="get_dem_locations",
        description=(
            "Get available monitoring locations for a DEM application. "
            "Locations are geographic points from which monitoring checks are executed."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "application_id": {
                    "type": "integer",
                    "description": "ID of the DEM application"
                }
            },
            "required": ["application_id"]
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


async def handle_list_dem_applications(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_dem_applications tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing DEM applications (limit={limit})")

        response = client._request("GET", "dem_application", params={"limit": limit})
        applications = response.get("dem_application_list", [])
        meta = response.get("meta", {})

        if not applications:
            return [TextContent(type="text", text="No DEM applications found.")]

        total_count = meta.get("total_count", len(applications))

        output_lines = [
            "**DEM Applications**\n",
            f"Found {len(applications)} application(s):\n"
        ]

        for app in applications:
            name = app.get("name", "Unknown")
            app_id = _extract_id_from_url(app.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {app_id})")
            if app.get("description"):
                output_lines.append(f"  Description: {app['description']}")

        if total_count > len(applications):
            output_lines.append(
                f"\n(Showing {len(applications)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing DEM applications: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing DEM applications")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_dem_application(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_dem_application tool execution."""
    try:
        name = arguments["name"]
        description = arguments.get("description")

        logger.info(f"Creating DEM application: {name}")

        data = {"name": name}
        if description:
            data["description"] = description

        response = client._request("POST", "dem_application", json_data=data)

        output_lines = [
            "**DEM Application Created**\n",
            f"Name: {name}"
        ]

        if description:
            output_lines.append(f"Description: {description}")

        if isinstance(response, dict) and response.get("url"):
            app_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Application ID: {app_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nApplication created. Use 'list_dem_applications' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating DEM application: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating DEM application")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_dem_application_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_dem_application_details tool execution."""
    try:
        application_id = arguments["application_id"]

        logger.info(f"Getting DEM application details for {application_id}")

        response = client._request("GET", f"dem_application/{application_id}")

        name = response.get("name", "Unknown")
        output_lines = [f"**DEM Application: {name}** (ID: {application_id})\n"]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        for key, value in response.items():
            if key not in ("name", "description", "url", "resource_uri") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: DEM application {arguments.get('application_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting DEM application details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting DEM application details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_dem_application(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_dem_application tool execution."""
    try:
        application_id = arguments["application_id"]
        name = arguments.get("name")
        description = arguments.get("description")

        if name is None and description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name' or 'description' must be provided."
            )]

        logger.info(f"Updating DEM application {application_id}")

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        client._request("PUT", f"dem_application/{application_id}", json_data=data)

        output_lines = ["**DEM Application Updated**\n"]
        if name:
            output_lines.append(f"Name: {name}")
        if description is not None:
            output_lines.append(f"Description: Updated")
        output_lines.append(f"Application ID: {application_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: DEM application {arguments.get('application_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating DEM application: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating DEM application")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_dem_application(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_dem_application tool execution."""
    try:
        application_id = arguments["application_id"]

        logger.info(f"Deleting DEM application {application_id}")

        # Get name before deleting
        try:
            response = client._request("GET", f"dem_application/{application_id}")
            app_name = response.get("name", f"ID {application_id}")
        except Exception:
            app_name = f"ID {application_id}"

        client._request("DELETE", f"dem_application/{application_id}")

        return [TextContent(
            type="text",
            text=(
                f"**DEM Application Deleted**\n\n"
                f"Application '{app_name}' (ID: {application_id}) has been deleted.\n\n"
                f"Note: All associated monitoring instances have been removed."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: DEM application {arguments.get('application_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting DEM application: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting DEM application")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_dem_instances(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_dem_instances tool execution."""
    try:
        application_id = arguments["application_id"]
        limit = arguments.get("limit", 50)

        logger.info(f"Listing DEM instances for application {application_id}")

        response = client._request(
            "GET",
            f"dem_application/{application_id}/instance",
            params={"limit": limit}
        )
        instances = response.get("instance_list", [])
        meta = response.get("meta", {})

        if not instances:
            return [TextContent(
                type="text",
                text=f"No instances found for DEM application {application_id}."
            )]

        total_count = meta.get("total_count", len(instances))

        output_lines = [
            f"**DEM Instances for Application {application_id}**\n",
            f"Found {len(instances)} instance(s):\n"
        ]

        for inst in instances:
            name = inst.get("name", "Unknown")
            inst_id = _extract_id_from_url(inst.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {inst_id})")
            if inst.get("status"):
                output_lines.append(f"  Status: {inst['status']}")
            if inst.get("template"):
                output_lines.append(f"  Template: {inst['template']}")

        if total_count > len(instances):
            output_lines.append(
                f"\n(Showing {len(instances)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: DEM application {arguments.get('application_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error listing DEM instances: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing DEM instances")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_dem_instance(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_dem_instance tool execution."""
    try:
        application_id = arguments["application_id"]
        template = arguments.get("template")

        logger.info(f"Creating DEM instance for application {application_id}")

        data = {}
        if template:
            data["template"] = template

        response = client._request(
            "POST",
            f"dem_application/{application_id}/instance",
            json_data=data if data else None
        )

        output_lines = [
            "**DEM Instance Created**\n",
            f"Application ID: {application_id}"
        ]

        if template:
            output_lines.append(f"Template: {template}")

        if isinstance(response, dict) and response.get("url"):
            inst_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Instance ID: {inst_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nInstance created. Use 'list_dem_instances' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: DEM application {arguments.get('application_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error creating DEM instance: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating DEM instance")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_dem_locations(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_dem_locations tool execution."""
    try:
        application_id = arguments["application_id"]

        logger.info(f"Getting DEM locations for application {application_id}")

        response = client._request(
            "GET",
            f"dem_application/{application_id}/location"
        )
        locations = response.get("location_list", [])
        meta = response.get("meta", {})

        if not locations:
            return [TextContent(
                type="text",
                text=f"No monitoring locations found for DEM application {application_id}."
            )]

        total_count = meta.get("total_count", len(locations))

        output_lines = [
            f"**DEM Locations for Application {application_id}**\n",
            f"Found {len(locations)} location(s):\n"
        ]

        for loc in locations:
            name = loc.get("name", "Unknown")
            loc_id = _extract_id_from_url(loc.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {loc_id})")
            if loc.get("region"):
                output_lines.append(f"  Region: {loc['region']}")
            if loc.get("country"):
                output_lines.append(f"  Country: {loc['country']}")

        if total_count > len(locations):
            output_lines.append(
                f"\n(Showing {len(locations)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: DEM application {arguments.get('application_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting DEM locations: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting DEM locations")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

DEM_TOOL_DEFINITIONS = {
    "list_dem_applications": list_dem_applications_tool_definition,
    "create_dem_application": create_dem_application_tool_definition,
    "get_dem_application_details": get_dem_application_details_tool_definition,
    "update_dem_application": update_dem_application_tool_definition,
    "delete_dem_application": delete_dem_application_tool_definition,
    "list_dem_instances": list_dem_instances_tool_definition,
    "create_dem_instance": create_dem_instance_tool_definition,
    "get_dem_locations": get_dem_locations_tool_definition,
}

DEM_HANDLERS = {
    "list_dem_applications": handle_list_dem_applications,
    "create_dem_application": handle_create_dem_application,
    "get_dem_application_details": handle_get_dem_application_details,
    "update_dem_application": handle_update_dem_application,
    "delete_dem_application": handle_delete_dem_application,
    "list_dem_instances": handle_list_dem_instances,
    "create_dem_instance": handle_create_dem_instance,
    "get_dem_locations": handle_get_dem_locations,
}
