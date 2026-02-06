"""OnSight and OnSight Group management tools for FortiMonitor."""

import logging
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def list_onsights_tool_definition() -> Tool:
    """Return tool definition for listing OnSight instances."""
    return Tool(
        name="list_onsights",
        description=(
            "List all OnSight instances configured in FortiMonitor. "
            "OnSight provides on-premises monitoring capabilities."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of OnSight instances to return (default 50)"
                }
            }
        }
    )


def get_onsight_details_tool_definition() -> Tool:
    """Return tool definition for getting OnSight details."""
    return Tool(
        name="get_onsight_details",
        description=(
            "Get detailed information about a specific OnSight instance."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "onsight_id": {
                    "type": "integer",
                    "description": "ID of the OnSight instance"
                }
            },
            "required": ["onsight_id"]
        }
    )


def create_onsight_tool_definition() -> Tool:
    """Return tool definition for creating an OnSight instance."""
    return Tool(
        name="create_onsight",
        description=(
            "Create a new OnSight instance for on-premises monitoring."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the OnSight instance"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the OnSight instance"
                }
            },
            "required": ["name"]
        }
    )


def update_onsight_tool_definition() -> Tool:
    """Return tool definition for updating an OnSight instance."""
    return Tool(
        name="update_onsight",
        description=(
            "Update an existing OnSight instance's name or description."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "onsight_id": {
                    "type": "integer",
                    "description": "ID of the OnSight instance to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the OnSight instance (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description for the OnSight instance (optional)"
                }
            },
            "required": ["onsight_id"]
        }
    )


def delete_onsight_tool_definition() -> Tool:
    """Return tool definition for deleting an OnSight instance."""
    return Tool(
        name="delete_onsight",
        description=(
            "Delete an OnSight instance. "
            "This permanently removes the OnSight and its configuration."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "onsight_id": {
                    "type": "integer",
                    "description": "ID of the OnSight instance to delete"
                }
            },
            "required": ["onsight_id"]
        }
    )


def get_onsight_countermeasures_tool_definition() -> Tool:
    """Return tool definition for getting OnSight countermeasures."""
    return Tool(
        name="get_onsight_countermeasures",
        description=(
            "Get countermeasure metadata for a specific OnSight instance. "
            "Countermeasures are automated responses to detected issues."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "onsight_id": {
                    "type": "integer",
                    "description": "ID of the OnSight instance"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of countermeasures to return (default 50)"
                }
            },
            "required": ["onsight_id"]
        }
    )


def get_onsight_servers_tool_definition() -> Tool:
    """Return tool definition for getting OnSight servers."""
    return Tool(
        name="get_onsight_servers",
        description=(
            "Get servers associated with a specific OnSight instance. "
            "Shows which servers are monitored by this OnSight."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "onsight_id": {
                    "type": "integer",
                    "description": "ID of the OnSight instance"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of servers to return (default 50)"
                }
            },
            "required": ["onsight_id"]
        }
    )


def list_onsight_groups_tool_definition() -> Tool:
    """Return tool definition for listing OnSight groups."""
    return Tool(
        name="list_onsight_groups",
        description=(
            "List all OnSight groups. "
            "OnSight groups organize multiple OnSight instances for easier management."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of groups to return (default 50)"
                }
            }
        }
    )


def get_onsight_group_details_tool_definition() -> Tool:
    """Return tool definition for getting OnSight group details."""
    return Tool(
        name="get_onsight_group_details",
        description=(
            "Get detailed information about a specific OnSight group."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "ID of the OnSight group"
                }
            },
            "required": ["group_id"]
        }
    )


def create_onsight_group_tool_definition() -> Tool:
    """Return tool definition for creating an OnSight group."""
    return Tool(
        name="create_onsight_group",
        description=(
            "Create a new OnSight group for organizing OnSight instances."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the OnSight group"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the OnSight group"
                }
            },
            "required": ["name"]
        }
    )


def update_onsight_group_tool_definition() -> Tool:
    """Return tool definition for updating an OnSight group."""
    return Tool(
        name="update_onsight_group",
        description=(
            "Update an existing OnSight group's name or description."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "ID of the OnSight group to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the OnSight group (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description for the OnSight group (optional)"
                }
            },
            "required": ["group_id"]
        }
    )


def delete_onsight_group_tool_definition() -> Tool:
    """Return tool definition for deleting an OnSight group."""
    return Tool(
        name="delete_onsight_group",
        description=(
            "Delete an OnSight group. "
            "The OnSight instances in the group are NOT deleted, only the group itself."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "ID of the OnSight group to delete"
                }
            },
            "required": ["group_id"]
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


async def handle_list_onsights(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_onsights tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing OnSight instances (limit={limit})")

        response = client._request("GET", "onsight", params={"limit": limit})
        onsights = response.get("onsight_list", [])
        meta = response.get("meta", {})

        if not onsights:
            return [TextContent(type="text", text="No OnSight instances found.")]

        total_count = meta.get("total_count", len(onsights))

        output_lines = [
            "**OnSight Instances**\n",
            f"Found {len(onsights)} instance(s):\n"
        ]

        for onsight in onsights:
            name = onsight.get("name", "Unknown")
            onsight_id = _extract_id_from_url(onsight.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {onsight_id})")
            if onsight.get("description"):
                output_lines.append(f"  Description: {onsight['description']}")
            if onsight.get("status"):
                output_lines.append(f"  Status: {onsight['status']}")

        if total_count > len(onsights):
            output_lines.append(
                f"\n(Showing {len(onsights)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing OnSight instances: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing OnSight instances")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_onsight_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_onsight_details tool execution."""
    try:
        onsight_id = arguments["onsight_id"]

        logger.info(f"Getting OnSight details for {onsight_id}")

        response = client._request("GET", f"onsight/{onsight_id}")

        name = response.get("name", "Unknown")
        output_lines = [f"**OnSight: {name}** (ID: {onsight_id})\n"]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        for key, value in response.items():
            if key not in ("name", "description", "url", "resource_uri") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: OnSight {arguments.get('onsight_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting OnSight details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting OnSight details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_onsight(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_onsight tool execution."""
    try:
        name = arguments["name"]
        description = arguments.get("description")

        logger.info(f"Creating OnSight instance: {name}")

        data = {"name": name}
        if description:
            data["description"] = description

        response = client._request("POST", "onsight", json_data=data)

        output_lines = [
            "**OnSight Instance Created**\n",
            f"Name: {name}"
        ]

        if description:
            output_lines.append(f"Description: {description}")

        if isinstance(response, dict) and response.get("url"):
            onsight_id = _extract_id_from_url(response["url"])
            output_lines.append(f"OnSight ID: {onsight_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nOnSight created. Use 'list_onsights' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating OnSight instance: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating OnSight instance")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_onsight(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_onsight tool execution."""
    try:
        onsight_id = arguments["onsight_id"]
        name = arguments.get("name")
        description = arguments.get("description")

        if name is None and description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name' or 'description' must be provided."
            )]

        logger.info(f"Updating OnSight instance {onsight_id}")

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        client._request("PUT", f"onsight/{onsight_id}", json_data=data)

        output_lines = ["**OnSight Instance Updated**\n"]
        if name:
            output_lines.append(f"Name: {name}")
        if description is not None:
            output_lines.append(f"Description: Updated")
        output_lines.append(f"OnSight ID: {onsight_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: OnSight {arguments.get('onsight_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating OnSight instance: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating OnSight instance")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_onsight(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_onsight tool execution."""
    try:
        onsight_id = arguments["onsight_id"]

        logger.info(f"Deleting OnSight instance {onsight_id}")

        # Get name before deleting
        try:
            response = client._request("GET", f"onsight/{onsight_id}")
            onsight_name = response.get("name", f"ID {onsight_id}")
        except Exception:
            onsight_name = f"ID {onsight_id}"

        client._request("DELETE", f"onsight/{onsight_id}")

        return [TextContent(
            type="text",
            text=(
                f"**OnSight Instance Deleted**\n\n"
                f"OnSight '{onsight_name}' (ID: {onsight_id}) has been deleted.\n\n"
                f"Note: This permanently removes the OnSight and its configuration."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: OnSight {arguments.get('onsight_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting OnSight instance: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting OnSight instance")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_onsight_countermeasures(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_onsight_countermeasures tool execution."""
    try:
        onsight_id = arguments["onsight_id"]
        limit = arguments.get("limit", 50)

        logger.info(
            f"Getting countermeasures for OnSight {onsight_id} (limit={limit})"
        )

        response = client._request(
            "GET",
            f"onsight/{onsight_id}/countermeasure_metadata",
            params={"limit": limit}
        )
        countermeasures = response.get("countermeasure_metadata_list", [])
        meta = response.get("meta", {})

        if not countermeasures:
            return [TextContent(
                type="text",
                text=f"No countermeasures found for OnSight {onsight_id}."
            )]

        total_count = meta.get("total_count", len(countermeasures))

        output_lines = [
            f"**Countermeasures for OnSight {onsight_id}**\n",
            f"Found {len(countermeasures)} countermeasure(s):\n"
        ]

        for cm in countermeasures:
            name = cm.get("name", "Unknown")
            cm_id = _extract_id_from_url(cm.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {cm_id})")
            if cm.get("description"):
                output_lines.append(f"  Description: {cm['description']}")
            if cm.get("type"):
                output_lines.append(f"  Type: {cm['type']}")
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
            text=f"Error: OnSight {arguments.get('onsight_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting OnSight countermeasures: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting OnSight countermeasures")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_onsight_servers(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_onsight_servers tool execution."""
    try:
        onsight_id = arguments["onsight_id"]
        limit = arguments.get("limit", 50)

        logger.info(
            f"Getting servers for OnSight {onsight_id} (limit={limit})"
        )

        response = client._request(
            "GET",
            f"onsight/{onsight_id}/servers",
            params={"limit": limit}
        )
        servers = response.get("server_list", [])
        meta = response.get("meta", {})

        if not servers:
            return [TextContent(
                type="text",
                text=f"No servers found for OnSight {onsight_id}."
            )]

        total_count = meta.get("total_count", len(servers))

        output_lines = [
            f"**Servers for OnSight {onsight_id}**\n",
            f"Found {len(servers)} server(s):\n"
        ]

        for server in servers:
            name = server.get("name", "Unknown")
            server_id = _extract_id_from_url(server.get("url", ""))
            fqdn = server.get("fqdn", "N/A")

            output_lines.append(f"\n**{name}** (ID: {server_id})")
            output_lines.append(f"  FQDN: {fqdn}")
            if server.get("status"):
                output_lines.append(f"  Status: {server['status']}")

        if total_count > len(servers):
            output_lines.append(
                f"\n(Showing {len(servers)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: OnSight {arguments.get('onsight_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting OnSight servers: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting OnSight servers")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_onsight_groups(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_onsight_groups tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing OnSight groups (limit={limit})")

        response = client._request("GET", "onsight_group", params={"limit": limit})
        groups = response.get("onsight_group_list", [])
        meta = response.get("meta", {})

        if not groups:
            return [TextContent(type="text", text="No OnSight groups found.")]

        total_count = meta.get("total_count", len(groups))

        output_lines = [
            "**OnSight Groups**\n",
            f"Found {len(groups)} group(s):\n"
        ]

        for group in groups:
            name = group.get("name", "Unknown")
            group_id = _extract_id_from_url(group.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {group_id})")
            if group.get("description"):
                output_lines.append(f"  Description: {group['description']}")

        if total_count > len(groups):
            output_lines.append(
                f"\n(Showing {len(groups)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing OnSight groups: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing OnSight groups")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_onsight_group_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_onsight_group_details tool execution."""
    try:
        group_id = arguments["group_id"]

        logger.info(f"Getting OnSight group details for {group_id}")

        response = client._request("GET", f"onsight_group/{group_id}")

        name = response.get("name", "Unknown")
        output_lines = [f"**OnSight Group: {name}** (ID: {group_id})\n"]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        for key, value in response.items():
            if key not in ("name", "description", "url", "resource_uri") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: OnSight group {arguments.get('group_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting OnSight group details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting OnSight group details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_onsight_group(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_onsight_group tool execution."""
    try:
        name = arguments["name"]
        description = arguments.get("description")

        logger.info(f"Creating OnSight group: {name}")

        data = {"name": name}
        if description:
            data["description"] = description

        response = client._request("POST", "onsight_group", json_data=data)

        output_lines = [
            "**OnSight Group Created**\n",
            f"Name: {name}"
        ]

        if description:
            output_lines.append(f"Description: {description}")

        if isinstance(response, dict) and response.get("url"):
            group_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Group ID: {group_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nGroup created. Use 'list_onsight_groups' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating OnSight group: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating OnSight group")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_onsight_group(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_onsight_group tool execution."""
    try:
        group_id = arguments["group_id"]
        name = arguments.get("name")
        description = arguments.get("description")

        if name is None and description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name' or 'description' must be provided."
            )]

        logger.info(f"Updating OnSight group {group_id}")

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        client._request("PUT", f"onsight_group/{group_id}", json_data=data)

        output_lines = ["**OnSight Group Updated**\n"]
        if name:
            output_lines.append(f"Name: {name}")
        if description is not None:
            output_lines.append(f"Description: Updated")
        output_lines.append(f"Group ID: {group_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: OnSight group {arguments.get('group_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating OnSight group: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating OnSight group")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_onsight_group(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_onsight_group tool execution."""
    try:
        group_id = arguments["group_id"]

        logger.info(f"Deleting OnSight group {group_id}")

        # Get name before deleting
        try:
            response = client._request("GET", f"onsight_group/{group_id}")
            group_name = response.get("name", f"ID {group_id}")
        except Exception:
            group_name = f"ID {group_id}"

        client._request("DELETE", f"onsight_group/{group_id}")

        return [TextContent(
            type="text",
            text=(
                f"**OnSight Group Deleted**\n\n"
                f"Group '{group_name}' (ID: {group_id}) has been deleted.\n\n"
                f"Note: The OnSight instances in the group are NOT deleted, "
                f"only the group itself."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: OnSight group {arguments.get('group_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting OnSight group: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting OnSight group")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

ONSIGHT_TOOL_DEFINITIONS = {
    "list_onsights": list_onsights_tool_definition,
    "get_onsight_details": get_onsight_details_tool_definition,
    "create_onsight": create_onsight_tool_definition,
    "update_onsight": update_onsight_tool_definition,
    "delete_onsight": delete_onsight_tool_definition,
    "get_onsight_countermeasures": get_onsight_countermeasures_tool_definition,
    "get_onsight_servers": get_onsight_servers_tool_definition,
    "list_onsight_groups": list_onsight_groups_tool_definition,
    "get_onsight_group_details": get_onsight_group_details_tool_definition,
    "create_onsight_group": create_onsight_group_tool_definition,
    "update_onsight_group": update_onsight_group_tool_definition,
    "delete_onsight_group": delete_onsight_group_tool_definition,
}

ONSIGHT_HANDLERS = {
    "list_onsights": handle_list_onsights,
    "get_onsight_details": handle_get_onsight_details,
    "create_onsight": handle_create_onsight,
    "update_onsight": handle_update_onsight,
    "delete_onsight": handle_delete_onsight,
    "get_onsight_countermeasures": handle_get_onsight_countermeasures,
    "get_onsight_servers": handle_get_onsight_servers,
    "list_onsight_groups": handle_list_onsight_groups,
    "get_onsight_group_details": handle_get_onsight_group_details,
    "create_onsight_group": handle_create_onsight_group,
    "update_onsight_group": handle_update_onsight_group,
    "delete_onsight_group": handle_delete_onsight_group,
}
