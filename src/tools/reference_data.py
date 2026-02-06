"""Reference data tools for FortiMonitor (account history, contact types, roles, timezones, etc.)."""

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


def list_account_history_tool_definition() -> Tool:
    """Return tool definition for listing account history."""
    return Tool(
        name="list_account_history",
        description=(
            "List account history entries for the FortiMonitor account. "
            "Shows recent account activity and changes."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of history entries to return (default 50)"
                }
            }
        }
    )


def list_contact_types_tool_definition() -> Tool:
    """Return tool definition for listing contact types."""
    return Tool(
        name="list_contact_types",
        description=(
            "List all available contact types in FortiMonitor. "
            "Contact types define the notification methods available "
            "(e.g., email, SMS, phone, webhook)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of contact types to return (default 50)"
                }
            }
        }
    )


def get_contact_type_details_tool_definition() -> Tool:
    """Return tool definition for getting contact type details."""
    return Tool(
        name="get_contact_type_details",
        description=(
            "Get detailed information about a specific contact type, "
            "including its configuration and capabilities."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "type_id": {
                    "type": "integer",
                    "description": "ID of the contact type"
                }
            },
            "required": ["type_id"]
        }
    )


def list_roles_tool_definition() -> Tool:
    """Return tool definition for listing roles."""
    return Tool(
        name="list_roles",
        description=(
            "List all available roles in FortiMonitor. "
            "Roles define permissions and access levels for users."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of roles to return (default 50)"
                }
            }
        }
    )


def get_role_details_tool_definition() -> Tool:
    """Return tool definition for getting role details."""
    return Tool(
        name="get_role_details",
        description=(
            "Get detailed information about a specific role, "
            "including its permissions and capabilities."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "role_id": {
                    "type": "integer",
                    "description": "ID of the role"
                }
            },
            "required": ["role_id"]
        }
    )


def list_timezones_tool_definition() -> Tool:
    """Return tool definition for listing timezones."""
    return Tool(
        name="list_timezones",
        description=(
            "List all available timezones in FortiMonitor. "
            "Timezones are used for scheduling notifications, "
            "maintenance windows, and report generation."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 100,
                    "description": "Maximum number of timezones to return (default 100)"
                }
            }
        }
    )


def get_timezone_details_tool_definition() -> Tool:
    """Return tool definition for getting timezone details."""
    return Tool(
        name="get_timezone_details",
        description=(
            "Get detailed information about a specific timezone, "
            "including its offset and display name."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "timezone_id": {
                    "type": "integer",
                    "description": "ID of the timezone"
                }
            },
            "required": ["timezone_id"]
        }
    )


def list_server_attribute_types_tool_definition() -> Tool:
    """Return tool definition for listing server attribute types."""
    return Tool(
        name="list_server_attribute_types",
        description=(
            "List all server attribute types defined in FortiMonitor. "
            "Server attribute types define the kinds of custom metadata "
            "that can be attached to servers."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of attribute types to return (default 50)"
                }
            }
        }
    )


def get_server_attribute_type_details_tool_definition() -> Tool:
    """Return tool definition for getting server attribute type details."""
    return Tool(
        name="get_server_attribute_type_details",
        description=(
            "Get detailed information about a specific server attribute type, "
            "including its name and configuration."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "type_id": {
                    "type": "integer",
                    "description": "ID of the server attribute type"
                }
            },
            "required": ["type_id"]
        }
    )


def create_server_attribute_type_tool_definition() -> Tool:
    """Return tool definition for creating a server attribute type."""
    return Tool(
        name="create_server_attribute_type",
        description=(
            "Create a new server attribute type. Attribute types define "
            "custom metadata fields that can be assigned to servers."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the new attribute type"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the attribute type"
                }
            },
            "required": ["name"]
        }
    )


def update_server_attribute_type_tool_definition() -> Tool:
    """Return tool definition for updating a server attribute type."""
    return Tool(
        name="update_server_attribute_type",
        description=(
            "Update an existing server attribute type's name or description."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "type_id": {
                    "type": "integer",
                    "description": "ID of the server attribute type to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the attribute type (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description for the attribute type (optional)"
                }
            },
            "required": ["type_id"]
        }
    )


def delete_server_attribute_type_tool_definition() -> Tool:
    """Return tool definition for deleting a server attribute type."""
    return Tool(
        name="delete_server_attribute_type",
        description=(
            "Delete a server attribute type. Any attributes of this type "
            "on existing servers may be affected."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "type_id": {
                    "type": "integer",
                    "description": "ID of the server attribute type to delete"
                }
            },
            "required": ["type_id"]
        }
    )


def create_prometheus_resource_tool_definition() -> Tool:
    """Return tool definition for creating a Prometheus resource."""
    return Tool(
        name="create_prometheus_resource",
        description=(
            "Create a new Prometheus resource on a server. "
            "This sets up Prometheus metric collection for the specified server."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server to create the Prometheus resource on"
                },
                "name": {
                    "type": "string",
                    "description": "Optional name for the Prometheus resource"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the Prometheus resource"
                }
            },
            "required": ["server_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_list_account_history(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_account_history tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing account history (limit={limit})")

        response = client._request(
            "GET", "account_history", params={"limit": limit}
        )
        entries = response.get("account_history_list", [])
        meta = response.get("meta", {})

        if not entries:
            return [TextContent(
                type="text", text="No account history entries found."
            )]

        total_count = meta.get("total_count", len(entries))

        output_lines = [
            "**Account History**\n",
            f"Found {len(entries)} entr(ies):\n"
        ]

        for entry in entries:
            entry_id = _extract_id_from_url(entry.get("url", ""))
            output_lines.append(f"\n**Entry ID: {entry_id}**")

            if entry.get("description"):
                output_lines.append(f"  Description: {entry['description']}")
            if entry.get("timestamp"):
                output_lines.append(f"  Timestamp: {entry['timestamp']}")
            if entry.get("user"):
                output_lines.append(f"  User: {entry['user']}")
            if entry.get("action"):
                output_lines.append(f"  Action: {entry['action']}")

            # Display any additional fields
            for key, value in entry.items():
                if key not in ("url", "resource_uri", "description",
                              "timestamp", "user", "action") and value:
                    output_lines.append(f"  {key}: {value}")

        if total_count > len(entries):
            output_lines.append(
                f"\n(Showing {len(entries)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing account history: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing account history")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_contact_types(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_contact_types tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing contact types (limit={limit})")

        response = client._request(
            "GET", "contact_type", params={"limit": limit}
        )
        contact_types = response.get("contact_type_list", [])
        meta = response.get("meta", {})

        if not contact_types:
            return [TextContent(
                type="text", text="No contact types found."
            )]

        total_count = meta.get("total_count", len(contact_types))

        output_lines = [
            "**Contact Types**\n",
            f"Found {len(contact_types)} contact type(s):\n"
        ]

        for ct in contact_types:
            name = ct.get("name", "Unknown")
            ct_id = _extract_id_from_url(ct.get("url", ""))
            output_lines.append(f"\n**{name}** (ID: {ct_id})")

            if ct.get("description"):
                output_lines.append(f"  Description: {ct['description']}")

            for key, value in ct.items():
                if key not in ("name", "description", "url",
                              "resource_uri") and value:
                    output_lines.append(f"  {key}: {value}")

        if total_count > len(contact_types):
            output_lines.append(
                f"\n(Showing {len(contact_types)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing contact types: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing contact types")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_contact_type_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_contact_type_details tool execution."""
    try:
        type_id = arguments["type_id"]

        logger.info(f"Getting contact type details for {type_id}")

        response = client._request(
            "GET", f"contact_type/{type_id}"
        )

        name = response.get("name", "Unknown")
        output_lines = [
            f"**Contact Type: {name}** (ID: {type_id})\n"
        ]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        for key, value in response.items():
            if key not in ("name", "description", "url",
                          "resource_uri") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Contact type {arguments.get('type_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting contact type details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting contact type details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_roles(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_roles tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing roles (limit={limit})")

        response = client._request(
            "GET", "role", params={"limit": limit}
        )
        roles = response.get("role_list", [])
        meta = response.get("meta", {})

        if not roles:
            return [TextContent(
                type="text", text="No roles found."
            )]

        total_count = meta.get("total_count", len(roles))

        output_lines = [
            "**Roles**\n",
            f"Found {len(roles)} role(s):\n"
        ]

        for role in roles:
            name = role.get("name", "Unknown")
            role_id = _extract_id_from_url(role.get("url", ""))
            output_lines.append(f"\n**{name}** (ID: {role_id})")

            if role.get("description"):
                output_lines.append(f"  Description: {role['description']}")

            for key, value in role.items():
                if key not in ("name", "description", "url",
                              "resource_uri") and value:
                    output_lines.append(f"  {key}: {value}")

        if total_count > len(roles):
            output_lines.append(
                f"\n(Showing {len(roles)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing roles: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing roles")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_role_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_role_details tool execution."""
    try:
        role_id = arguments["role_id"]

        logger.info(f"Getting role details for {role_id}")

        response = client._request(
            "GET", f"role/{role_id}"
        )

        name = response.get("name", "Unknown")
        output_lines = [
            f"**Role: {name}** (ID: {role_id})\n"
        ]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        # Show permissions if present
        permissions = response.get("permissions", [])
        if permissions:
            output_lines.append(f"\n**Permissions ({len(permissions)}):**")
            for perm in permissions[:30]:
                if isinstance(perm, dict):
                    perm_name = perm.get("name", "Unknown")
                    output_lines.append(f"  - {perm_name}")
                elif isinstance(perm, str):
                    output_lines.append(f"  - {perm}")
            if len(permissions) > 30:
                output_lines.append(f"  ... and {len(permissions) - 30} more")

        for key, value in response.items():
            if key not in ("name", "description", "url",
                          "resource_uri", "permissions") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Role {arguments.get('role_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting role details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting role details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_timezones(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_timezones tool execution."""
    try:
        limit = arguments.get("limit", 100)

        logger.info(f"Listing timezones (limit={limit})")

        response = client._request(
            "GET", "timezone", params={"limit": limit}
        )
        timezones = response.get("timezone_list", [])
        meta = response.get("meta", {})

        if not timezones:
            return [TextContent(
                type="text", text="No timezones found."
            )]

        total_count = meta.get("total_count", len(timezones))

        output_lines = [
            "**Timezones**\n",
            f"Found {len(timezones)} timezone(s):\n"
        ]

        for tz in timezones:
            name = tz.get("name", "Unknown")
            tz_id = _extract_id_from_url(tz.get("url", ""))
            output_lines.append(f"\n**{name}** (ID: {tz_id})")

            if tz.get("offset"):
                output_lines.append(f"  Offset: {tz['offset']}")
            if tz.get("description"):
                output_lines.append(f"  Description: {tz['description']}")

            for key, value in tz.items():
                if key not in ("name", "offset", "description", "url",
                              "resource_uri") and value:
                    output_lines.append(f"  {key}: {value}")

        if total_count > len(timezones):
            output_lines.append(
                f"\n(Showing {len(timezones)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing timezones: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing timezones")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_timezone_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_timezone_details tool execution."""
    try:
        timezone_id = arguments["timezone_id"]

        logger.info(f"Getting timezone details for {timezone_id}")

        response = client._request(
            "GET", f"timezone/{timezone_id}"
        )

        name = response.get("name", "Unknown")
        output_lines = [
            f"**Timezone: {name}** (ID: {timezone_id})\n"
        ]

        if response.get("offset"):
            output_lines.append(f"Offset: {response['offset']}")
        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        for key, value in response.items():
            if key not in ("name", "offset", "description", "url",
                          "resource_uri") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Timezone {arguments.get('timezone_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting timezone details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting timezone details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_server_attribute_types(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_server_attribute_types tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing server attribute types (limit={limit})")

        response = client._request(
            "GET", "server_attribute_type", params={"limit": limit}
        )
        attr_types = response.get("server_attribute_type_list", [])
        meta = response.get("meta", {})

        if not attr_types:
            return [TextContent(
                type="text", text="No server attribute types found."
            )]

        total_count = meta.get("total_count", len(attr_types))

        output_lines = [
            "**Server Attribute Types**\n",
            f"Found {len(attr_types)} attribute type(s):\n"
        ]

        for at in attr_types:
            name = at.get("name", "Unknown")
            at_id = _extract_id_from_url(at.get("url", ""))
            output_lines.append(f"\n**{name}** (ID: {at_id})")

            if at.get("description"):
                output_lines.append(f"  Description: {at['description']}")

            for key, value in at.items():
                if key not in ("name", "description", "url",
                              "resource_uri") and value:
                    output_lines.append(f"  {key}: {value}")

        if total_count > len(attr_types):
            output_lines.append(
                f"\n(Showing {len(attr_types)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing server attribute types: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing server attribute types")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_server_attribute_type_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_server_attribute_type_details tool execution."""
    try:
        type_id = arguments["type_id"]

        logger.info(f"Getting server attribute type details for {type_id}")

        response = client._request(
            "GET", f"server_attribute_type/{type_id}"
        )

        name = response.get("name", "Unknown")
        output_lines = [
            f"**Server Attribute Type: {name}** (ID: {type_id})\n"
        ]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        for key, value in response.items():
            if key not in ("name", "description", "url",
                          "resource_uri") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server attribute type {arguments.get('type_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting server attribute type details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting server attribute type details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_server_attribute_type(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_server_attribute_type tool execution."""
    try:
        name = arguments["name"]
        description = arguments.get("description")

        logger.info(f"Creating server attribute type: {name}")

        data = {"name": name}
        if description:
            data["description"] = description

        response = client._request(
            "POST", "server_attribute_type", json_data=data
        )

        output_lines = [
            "**Server Attribute Type Created**\n",
            f"Name: {name}"
        ]

        if description:
            output_lines.append(f"Description: {description}")

        if isinstance(response, dict) and response.get("url"):
            at_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Attribute Type ID: {at_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nAttribute type created. Use 'list_server_attribute_types' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating server attribute type: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating server attribute type")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_server_attribute_type(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_server_attribute_type tool execution."""
    try:
        type_id = arguments["type_id"]
        name = arguments.get("name")
        description = arguments.get("description")

        if name is None and description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name' or 'description' must be provided."
            )]

        logger.info(f"Updating server attribute type {type_id}")

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        client._request(
            "PUT", f"server_attribute_type/{type_id}", json_data=data
        )

        output_lines = ["**Server Attribute Type Updated**\n"]
        if name:
            output_lines.append(f"Name: {name}")
        if description is not None:
            output_lines.append(f"Description: Updated")
        output_lines.append(f"Attribute Type ID: {type_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server attribute type {arguments.get('type_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating server attribute type: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating server attribute type")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_server_attribute_type(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_server_attribute_type tool execution."""
    try:
        type_id = arguments["type_id"]

        logger.info(f"Deleting server attribute type {type_id}")

        # Try to get the name before deleting
        try:
            response = client._request(
                "GET", f"server_attribute_type/{type_id}"
            )
            type_name = response.get("name", f"ID {type_id}")
        except Exception:
            type_name = f"ID {type_id}"

        client._request("DELETE", f"server_attribute_type/{type_id}")

        return [TextContent(
            type="text",
            text=(
                f"**Server Attribute Type Deleted**\n\n"
                f"Attribute type '{type_name}' (ID: {type_id}) has been deleted.\n\n"
                f"Note: Existing server attributes of this type may be affected."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server attribute type {arguments.get('type_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting server attribute type: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting server attribute type")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_prometheus_resource(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_prometheus_resource tool execution."""
    try:
        server_id = arguments["server_id"]
        name = arguments.get("name")
        description = arguments.get("description")

        logger.info(f"Creating Prometheus resource on server {server_id}")

        data = {"server_id": server_id}
        if name:
            data["name"] = name
        if description:
            data["description"] = description

        response = client._request(
            "POST", "prometheus_resource", json_data=data
        )

        output_lines = [
            "**Prometheus Resource Created**\n",
            f"Server ID: {server_id}"
        ]

        if name:
            output_lines.append(f"Name: {name}")
        if description:
            output_lines.append(f"Description: {description}")

        if isinstance(response, dict) and response.get("url"):
            res_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Resource ID: {res_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nPrometheus resource created successfully."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error creating Prometheus resource: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating Prometheus resource")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

REFERENCE_DATA_TOOL_DEFINITIONS = {
    "list_account_history": list_account_history_tool_definition,
    "list_contact_types": list_contact_types_tool_definition,
    "get_contact_type_details": get_contact_type_details_tool_definition,
    "list_roles": list_roles_tool_definition,
    "get_role_details": get_role_details_tool_definition,
    "list_timezones": list_timezones_tool_definition,
    "get_timezone_details": get_timezone_details_tool_definition,
    "list_server_attribute_types": list_server_attribute_types_tool_definition,
    "get_server_attribute_type_details": get_server_attribute_type_details_tool_definition,
    "create_server_attribute_type": create_server_attribute_type_tool_definition,
    "update_server_attribute_type": update_server_attribute_type_tool_definition,
    "delete_server_attribute_type": delete_server_attribute_type_tool_definition,
    "create_prometheus_resource": create_prometheus_resource_tool_definition,
}

REFERENCE_DATA_HANDLERS = {
    "list_account_history": handle_list_account_history,
    "list_contact_types": handle_list_contact_types,
    "get_contact_type_details": handle_get_contact_type_details,
    "list_roles": handle_list_roles,
    "get_role_details": handle_get_role_details,
    "list_timezones": handle_list_timezones,
    "get_timezone_details": handle_get_timezone_details,
    "list_server_attribute_types": handle_list_server_attribute_types,
    "get_server_attribute_type_details": handle_get_server_attribute_type_details,
    "create_server_attribute_type": handle_create_server_attribute_type,
    "update_server_attribute_type": handle_update_server_attribute_type,
    "delete_server_attribute_type": handle_delete_server_attribute_type,
    "create_prometheus_resource": handle_create_prometheus_resource,
}
