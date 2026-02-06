"""Enhanced contact and contact group management tools for FortiMonitor."""

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


def get_contact_details_tool_definition() -> Tool:
    """Return tool definition for getting contact details."""
    return Tool(
        name="get_contact_details",
        description=(
            "Get detailed information about a specific notification contact, "
            "including their contact methods (email, SMS, phone, etc.)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "contact_id": {
                    "type": "integer",
                    "description": "ID of the contact"
                }
            },
            "required": ["contact_id"]
        }
    )


def create_contact_tool_definition() -> Tool:
    """Return tool definition for creating a contact."""
    return Tool(
        name="create_contact",
        description=(
            "Create a new notification contact. Contacts are people who "
            "receive alerts via email, SMS, phone, or other methods."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the contact"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description"
                }
            },
            "required": ["name"]
        }
    )


def update_contact_tool_definition() -> Tool:
    """Return tool definition for updating a contact."""
    return Tool(
        name="update_contact",
        description="Update an existing notification contact's name or description.",
        inputSchema={
            "type": "object",
            "properties": {
                "contact_id": {
                    "type": "integer",
                    "description": "ID of the contact to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the contact (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description (optional)"
                }
            },
            "required": ["contact_id"]
        }
    )


def delete_contact_tool_definition() -> Tool:
    """Return tool definition for deleting a contact."""
    return Tool(
        name="delete_contact",
        description=(
            "Delete a notification contact. This removes them from all "
            "contact groups and notification chains."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "contact_id": {
                    "type": "integer",
                    "description": "ID of the contact to delete"
                }
            },
            "required": ["contact_id"]
        }
    )


def list_contact_info_tool_definition() -> Tool:
    """Return tool definition for listing contact info methods."""
    return Tool(
        name="list_contact_info",
        description=(
            "List all contact methods (email addresses, phone numbers, SMS numbers, etc.) "
            "configured for a specific contact."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "contact_id": {
                    "type": "integer",
                    "description": "ID of the contact"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of contact methods to return (default 50)"
                }
            },
            "required": ["contact_id"]
        }
    )


def get_contact_info_details_tool_definition() -> Tool:
    """Return tool definition for getting contact info details."""
    return Tool(
        name="get_contact_info_details",
        description=(
            "Get detailed information about a specific contact method "
            "(email, SMS, phone, etc.) for a contact."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "contact_id": {
                    "type": "integer",
                    "description": "ID of the contact"
                },
                "contact_info_id": {
                    "type": "integer",
                    "description": "ID of the contact info method"
                }
            },
            "required": ["contact_id", "contact_info_id"]
        }
    )


def create_contact_info_tool_definition() -> Tool:
    """Return tool definition for creating a contact info method."""
    return Tool(
        name="create_contact_info",
        description=(
            "Add a new contact method (email, SMS, phone, etc.) to a contact."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "contact_id": {
                    "type": "integer",
                    "description": "ID of the contact to add the method to"
                },
                "contact_type_id": {
                    "type": "integer",
                    "description": "ID of the contact type (email, SMS, phone, etc.)"
                },
                "value": {
                    "type": "string",
                    "description": "The contact value (e.g., email address, phone number)"
                }
            },
            "required": ["contact_id", "contact_type_id", "value"]
        }
    )


def update_contact_info_tool_definition() -> Tool:
    """Return tool definition for updating a contact info method."""
    return Tool(
        name="update_contact_info",
        description="Update an existing contact method's value or settings.",
        inputSchema={
            "type": "object",
            "properties": {
                "contact_id": {
                    "type": "integer",
                    "description": "ID of the contact"
                },
                "contact_info_id": {
                    "type": "integer",
                    "description": "ID of the contact info method to update"
                },
                "value": {
                    "type": "string",
                    "description": "New value for the contact method"
                }
            },
            "required": ["contact_id", "contact_info_id"]
        }
    )


def delete_contact_info_tool_definition() -> Tool:
    """Return tool definition for deleting a contact info method."""
    return Tool(
        name="delete_contact_info",
        description="Remove a contact method (email, SMS, phone, etc.) from a contact.",
        inputSchema={
            "type": "object",
            "properties": {
                "contact_id": {
                    "type": "integer",
                    "description": "ID of the contact"
                },
                "contact_info_id": {
                    "type": "integer",
                    "description": "ID of the contact info method to delete"
                }
            },
            "required": ["contact_id", "contact_info_id"]
        }
    )


def create_contact_group_tool_definition() -> Tool:
    """Return tool definition for creating a contact group."""
    return Tool(
        name="create_contact_group",
        description=(
            "Create a new contact group. Contact groups define which contacts "
            "receive alerts together."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the contact group"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description"
                }
            },
            "required": ["name"]
        }
    )


def update_contact_group_tool_definition() -> Tool:
    """Return tool definition for updating a contact group."""
    return Tool(
        name="update_contact_group",
        description="Update an existing contact group's name or description.",
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "ID of the contact group to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the contact group (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description (optional)"
                }
            },
            "required": ["group_id"]
        }
    )


def delete_contact_group_tool_definition() -> Tool:
    """Return tool definition for deleting a contact group."""
    return Tool(
        name="delete_contact_group",
        description=(
            "Delete a contact group. The contacts within the group are not deleted."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "ID of the contact group to delete"
                }
            },
            "required": ["group_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_get_contact_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_contact_details tool execution."""
    try:
        contact_id = arguments["contact_id"]

        logger.info(f"Getting contact details for {contact_id}")

        response = client._request("GET", f"contact/{contact_id}")

        name = response.get("name", "Unknown")
        output_lines = [f"**Contact: {name}** (ID: {contact_id})\n"]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        # Show contact info methods if embedded
        contact_info = response.get("contact_info", [])
        if contact_info:
            output_lines.append(f"\n**Contact Methods ({len(contact_info)}):**")
            for info in contact_info:
                if isinstance(info, dict):
                    info_type = info.get("contact_type_name", info.get("type", "Unknown"))
                    info_value = info.get("value", info.get("address", "N/A"))
                    output_lines.append(f"  - {info_type}: {info_value}")
                elif isinstance(info, str):
                    output_lines.append(f"  - {info}")

        for key, value in response.items():
            if key not in ("name", "description", "url", "resource_uri",
                          "contact_info") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Contact {arguments.get('contact_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting contact details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting contact details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_contact(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_contact tool execution."""
    try:
        name = arguments["name"]
        description = arguments.get("description")

        logger.info(f"Creating contact: {name}")

        data = {"name": name}
        if description:
            data["description"] = description

        response = client._request("POST", "contact", json_data=data)

        output_lines = [
            "**Contact Created**\n",
            f"Name: {name}"
        ]

        if description:
            output_lines.append(f"Description: {description}")

        if isinstance(response, dict) and response.get("url"):
            contact_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Contact ID: {contact_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nContact created. Use 'list_contacts' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating contact: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating contact")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_contact(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_contact tool execution."""
    try:
        contact_id = arguments["contact_id"]
        name = arguments.get("name")
        description = arguments.get("description")

        if name is None and description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name' or 'description' must be provided."
            )]

        logger.info(f"Updating contact {contact_id}")

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        client._request("PUT", f"contact/{contact_id}", json_data=data)

        output_lines = ["**Contact Updated**\n"]
        if name:
            output_lines.append(f"Name: {name}")
        if description is not None:
            output_lines.append(f"Description: Updated")
        output_lines.append(f"Contact ID: {contact_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Contact {arguments.get('contact_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating contact: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating contact")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_contact(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_contact tool execution."""
    try:
        contact_id = arguments["contact_id"]

        logger.info(f"Deleting contact {contact_id}")

        try:
            response = client._request("GET", f"contact/{contact_id}")
            contact_name = response.get("name", f"ID {contact_id}")
        except Exception:
            contact_name = f"ID {contact_id}"

        client._request("DELETE", f"contact/{contact_id}")

        return [TextContent(
            type="text",
            text=(
                f"**Contact Deleted**\n\n"
                f"Contact '{contact_name}' (ID: {contact_id}) has been deleted.\n\n"
                f"Note: This contact has been removed from all contact groups "
                f"and notification chains."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Contact {arguments.get('contact_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting contact: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting contact")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_contact_info(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_contact_info tool execution."""
    try:
        contact_id = arguments["contact_id"]
        limit = arguments.get("limit", 50)

        logger.info(f"Listing contact info for contact {contact_id}")

        response = client._request(
            "GET",
            f"contact/{contact_id}/contact_info",
            params={"limit": limit}
        )
        info_list = response.get("contact_info_list", [])
        meta = response.get("meta", {})

        if not info_list:
            return [TextContent(
                type="text",
                text=f"No contact methods found for contact {contact_id}."
            )]

        total_count = meta.get("total_count", len(info_list))

        output_lines = [
            f"**Contact Methods for Contact {contact_id}**\n",
            f"Found {len(info_list)} method(s):\n"
        ]

        for info in info_list:
            info_id = _extract_id_from_url(info.get("url", ""))
            info_type = info.get("contact_type_name", info.get("type", "Unknown"))
            info_value = info.get("value", info.get("address", "N/A"))

            output_lines.append(f"\n**{info_type}** (ID: {info_id})")
            output_lines.append(f"  Value: {info_value}")

            if info.get("verified"):
                output_lines.append(f"  Verified: {info['verified']}")

        if total_count > len(info_list):
            output_lines.append(
                f"\n(Showing {len(info_list)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Contact {arguments.get('contact_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error listing contact info: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing contact info")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_contact_info_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_contact_info_details tool execution."""
    try:
        contact_id = arguments["contact_id"]
        contact_info_id = arguments["contact_info_id"]

        logger.info(
            f"Getting contact info {contact_info_id} for contact {contact_id}"
        )

        response = client._request(
            "GET",
            f"contact/{contact_id}/contact_info/{contact_info_id}"
        )

        info_type = response.get("contact_type_name", response.get("type", "Unknown"))
        info_value = response.get("value", response.get("address", "N/A"))

        output_lines = [
            f"**Contact Method: {info_type}** (ID: {contact_info_id})\n",
            f"Contact ID: {contact_id}",
            f"Value: {info_value}"
        ]

        for key, value in response.items():
            if key not in ("contact_type_name", "type", "value", "address",
                          "url", "resource_uri") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Contact info {arguments.get('contact_info_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting contact info details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting contact info details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_contact_info(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_contact_info tool execution."""
    try:
        contact_id = arguments["contact_id"]
        contact_type_id = arguments["contact_type_id"]
        value = arguments["value"]

        logger.info(f"Creating contact info for contact {contact_id}")

        data = {
            "contact_type": f"{client.base_url}/contact_type/{contact_type_id}",
            "value": value
        }

        response = client._request(
            "POST",
            f"contact/{contact_id}/contact_info",
            json_data=data
        )

        output_lines = [
            "**Contact Method Added**\n",
            f"Contact ID: {contact_id}",
            f"Contact Type ID: {contact_type_id}",
            f"Value: {value}"
        ]

        if isinstance(response, dict) and response.get("url"):
            info_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Contact Info ID: {info_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Contact {arguments.get('contact_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error creating contact info: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating contact info")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_contact_info(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_contact_info tool execution."""
    try:
        contact_id = arguments["contact_id"]
        contact_info_id = arguments["contact_info_id"]
        value = arguments.get("value")

        if value is None:
            return [TextContent(
                type="text",
                text="Error: 'value' must be provided for update."
            )]

        logger.info(
            f"Updating contact info {contact_info_id} for contact {contact_id}"
        )

        data = {"value": value}

        client._request(
            "PUT",
            f"contact/{contact_id}/contact_info/{contact_info_id}",
            json_data=data
        )

        output_lines = [
            "**Contact Method Updated**\n",
            f"Contact ID: {contact_id}",
            f"Contact Info ID: {contact_info_id}",
            f"New Value: {value}"
        ]

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Contact info {arguments.get('contact_info_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating contact info: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating contact info")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_contact_info(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_contact_info tool execution."""
    try:
        contact_id = arguments["contact_id"]
        contact_info_id = arguments["contact_info_id"]

        logger.info(
            f"Deleting contact info {contact_info_id} for contact {contact_id}"
        )

        client._request(
            "DELETE",
            f"contact/{contact_id}/contact_info/{contact_info_id}"
        )

        return [TextContent(
            type="text",
            text=(
                f"**Contact Method Deleted**\n\n"
                f"Contact info ID {contact_info_id} removed from contact {contact_id}."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Contact info {arguments.get('contact_info_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting contact info: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting contact info")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_contact_group(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_contact_group tool execution."""
    try:
        name = arguments["name"]
        description = arguments.get("description")

        logger.info(f"Creating contact group: {name}")

        data = {"name": name}
        if description:
            data["description"] = description

        response = client._request("POST", "contact_group", json_data=data)

        output_lines = [
            "**Contact Group Created**\n",
            f"Name: {name}"
        ]

        if description:
            output_lines.append(f"Description: {description}")

        if isinstance(response, dict) and response.get("url"):
            group_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Group ID: {group_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nGroup created. Use 'list_contact_groups' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating contact group: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating contact group")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_contact_group(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_contact_group tool execution."""
    try:
        group_id = arguments["group_id"]
        name = arguments.get("name")
        description = arguments.get("description")

        if name is None and description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name' or 'description' must be provided."
            )]

        logger.info(f"Updating contact group {group_id}")

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        client._request("PUT", f"contact_group/{group_id}", json_data=data)

        output_lines = ["**Contact Group Updated**\n"]
        if name:
            output_lines.append(f"Name: {name}")
        if description is not None:
            output_lines.append(f"Description: Updated")
        output_lines.append(f"Group ID: {group_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Contact group {arguments.get('group_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating contact group: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating contact group")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_contact_group(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_contact_group tool execution."""
    try:
        group_id = arguments["group_id"]

        logger.info(f"Deleting contact group {group_id}")

        try:
            response = client._request("GET", f"contact_group/{group_id}")
            group_name = response.get("name", f"ID {group_id}")
        except Exception:
            group_name = f"ID {group_id}"

        client._request("DELETE", f"contact_group/{group_id}")

        return [TextContent(
            type="text",
            text=(
                f"**Contact Group Deleted**\n\n"
                f"Contact group '{group_name}' (ID: {group_id}) has been deleted.\n\n"
                f"Note: The contacts within the group are not deleted."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Contact group {arguments.get('group_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting contact group: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting contact group")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

CONTACTS_ENHANCED_TOOL_DEFINITIONS = {
    "get_contact_details": get_contact_details_tool_definition,
    "create_contact": create_contact_tool_definition,
    "update_contact": update_contact_tool_definition,
    "delete_contact": delete_contact_tool_definition,
    "list_contact_info": list_contact_info_tool_definition,
    "get_contact_info_details": get_contact_info_details_tool_definition,
    "create_contact_info": create_contact_info_tool_definition,
    "update_contact_info": update_contact_info_tool_definition,
    "delete_contact_info": delete_contact_info_tool_definition,
    "create_contact_group": create_contact_group_tool_definition,
    "update_contact_group": update_contact_group_tool_definition,
    "delete_contact_group": delete_contact_group_tool_definition,
}

CONTACTS_ENHANCED_HANDLERS = {
    "get_contact_details": handle_get_contact_details,
    "create_contact": handle_create_contact,
    "update_contact": handle_update_contact,
    "delete_contact": handle_delete_contact,
    "list_contact_info": handle_list_contact_info,
    "get_contact_info_details": handle_get_contact_info_details,
    "create_contact_info": handle_create_contact_info,
    "update_contact_info": handle_update_contact_info,
    "delete_contact_info": handle_delete_contact_info,
    "create_contact_group": handle_create_contact_group,
    "update_contact_group": handle_update_contact_group,
    "delete_contact_group": handle_delete_contact_group,
}
