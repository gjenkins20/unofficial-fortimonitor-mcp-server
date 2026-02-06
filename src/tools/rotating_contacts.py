"""Rotating contact (on-call rotation) management tools for FortiMonitor."""

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


def list_rotating_contacts_tool_definition() -> Tool:
    """Return tool definition for listing rotating contacts."""
    return Tool(
        name="list_rotating_contacts",
        description=(
            "List all rotating contact schedules (on-call rotations). "
            "Rotating contacts define which team members receive alerts "
            "on a rotating schedule."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of rotating contacts to return (default 50)"
                }
            }
        }
    )


def get_rotating_contact_details_tool_definition() -> Tool:
    """Return tool definition for getting rotating contact details."""
    return Tool(
        name="get_rotating_contact_details",
        description=(
            "Get detailed information about a specific rotating contact schedule, "
            "including rotation members and schedule configuration."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "rotating_contact_id": {
                    "type": "integer",
                    "description": "ID of the rotating contact schedule"
                }
            },
            "required": ["rotating_contact_id"]
        }
    )


def create_rotating_contact_tool_definition() -> Tool:
    """Return tool definition for creating a rotating contact."""
    return Tool(
        name="create_rotating_contact",
        description=(
            "Create a new rotating contact schedule (on-call rotation). "
            "Defines which contacts receive alerts on a rotating basis."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the rotating contact schedule"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the rotation"
                }
            },
            "required": ["name"]
        }
    )


def update_rotating_contact_tool_definition() -> Tool:
    """Return tool definition for updating a rotating contact."""
    return Tool(
        name="update_rotating_contact",
        description=(
            "Update an existing rotating contact schedule's name or description."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "rotating_contact_id": {
                    "type": "integer",
                    "description": "ID of the rotating contact schedule to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the rotation (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description for the rotation (optional)"
                }
            },
            "required": ["rotating_contact_id"]
        }
    )


def delete_rotating_contact_tool_definition() -> Tool:
    """Return tool definition for deleting a rotating contact."""
    return Tool(
        name="delete_rotating_contact",
        description=(
            "Delete a rotating contact schedule. "
            "The underlying contacts are not deleted, only the rotation schedule."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "rotating_contact_id": {
                    "type": "integer",
                    "description": "ID of the rotating contact schedule to delete"
                }
            },
            "required": ["rotating_contact_id"]
        }
    )


def get_rotating_contact_active_tool_definition() -> Tool:
    """Return tool definition for getting currently active rotating contact."""
    return Tool(
        name="get_rotating_contact_active",
        description=(
            "Get the currently active (on-call) contact for a rotating contact schedule. "
            "Shows who is currently responsible for receiving alerts."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "rotating_contact_id": {
                    "type": "integer",
                    "description": "ID of the rotating contact schedule"
                }
            },
            "required": ["rotating_contact_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_list_rotating_contacts(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_rotating_contacts tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing rotating contacts (limit={limit})")

        response = client._request(
            "GET", "rotating_contact", params={"limit": limit}
        )
        rotations = response.get("rotating_contact_list", [])
        meta = response.get("meta", {})

        if not rotations:
            return [TextContent(
                type="text", text="No rotating contact schedules found."
            )]

        total_count = meta.get("total_count", len(rotations))

        output_lines = [
            "**Rotating Contact Schedules**\n",
            f"Found {len(rotations)} rotation(s):\n"
        ]

        for rotation in rotations:
            name = rotation.get("name", "Unknown")
            rot_id = _extract_id_from_url(rotation.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {rot_id})")
            if rotation.get("description"):
                output_lines.append(f"  Description: {rotation['description']}")
            if rotation.get("rotation_type"):
                output_lines.append(f"  Type: {rotation['rotation_type']}")

        if total_count > len(rotations):
            output_lines.append(
                f"\n(Showing {len(rotations)} of {total_count} total)"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing rotating contacts: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing rotating contacts")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_rotating_contact_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_rotating_contact_details tool execution."""
    try:
        rotating_contact_id = arguments["rotating_contact_id"]

        logger.info(f"Getting rotating contact details for {rotating_contact_id}")

        response = client._request(
            "GET", f"rotating_contact/{rotating_contact_id}"
        )

        name = response.get("name", "Unknown")
        output_lines = [
            f"**Rotating Contact: {name}** (ID: {rotating_contact_id})\n"
        ]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")
        if response.get("rotation_type"):
            output_lines.append(f"Rotation Type: {response['rotation_type']}")

        # Show members if present
        members = response.get("contacts", response.get("members", []))
        if members:
            output_lines.append(f"\n**Members ({len(members)}):**")
            for member in members[:20]:
                if isinstance(member, dict):
                    m_name = member.get("name", "Unknown")
                    output_lines.append(f"  - {m_name}")
                elif isinstance(member, str):
                    m_id = _extract_id_from_url(member)
                    output_lines.append(f"  - Contact ID: {m_id}")
            if len(members) > 20:
                output_lines.append(f"  ... and {len(members) - 20} more")

        for key, value in response.items():
            if key not in ("name", "description", "url", "resource_uri",
                          "rotation_type", "contacts", "members") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Rotating contact {arguments.get('rotating_contact_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting rotating contact details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting rotating contact details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_rotating_contact(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_rotating_contact tool execution."""
    try:
        name = arguments["name"]
        description = arguments.get("description")

        logger.info(f"Creating rotating contact: {name}")

        data = {"name": name}
        if description:
            data["description"] = description

        response = client._request(
            "POST", "rotating_contact", json_data=data
        )

        output_lines = [
            "**Rotating Contact Created**\n",
            f"Name: {name}"
        ]

        if description:
            output_lines.append(f"Description: {description}")

        if isinstance(response, dict) and response.get("url"):
            rot_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Rotating Contact ID: {rot_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nRotation created. Use 'list_rotating_contacts' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating rotating contact: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating rotating contact")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_rotating_contact(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_rotating_contact tool execution."""
    try:
        rotating_contact_id = arguments["rotating_contact_id"]
        name = arguments.get("name")
        description = arguments.get("description")

        if name is None and description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name' or 'description' must be provided."
            )]

        logger.info(f"Updating rotating contact {rotating_contact_id}")

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        client._request(
            "PUT", f"rotating_contact/{rotating_contact_id}", json_data=data
        )

        output_lines = ["**Rotating Contact Updated**\n"]
        if name:
            output_lines.append(f"Name: {name}")
        if description is not None:
            output_lines.append(f"Description: Updated")
        output_lines.append(f"Rotating Contact ID: {rotating_contact_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Rotating contact {arguments.get('rotating_contact_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating rotating contact: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating rotating contact")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_rotating_contact(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_rotating_contact tool execution."""
    try:
        rotating_contact_id = arguments["rotating_contact_id"]

        logger.info(f"Deleting rotating contact {rotating_contact_id}")

        try:
            response = client._request(
                "GET", f"rotating_contact/{rotating_contact_id}"
            )
            rot_name = response.get("name", f"ID {rotating_contact_id}")
        except Exception:
            rot_name = f"ID {rotating_contact_id}"

        client._request("DELETE", f"rotating_contact/{rotating_contact_id}")

        return [TextContent(
            type="text",
            text=(
                f"**Rotating Contact Deleted**\n\n"
                f"Rotation '{rot_name}' (ID: {rotating_contact_id}) has been deleted.\n\n"
                f"Note: The underlying contacts are not affected."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Rotating contact {arguments.get('rotating_contact_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting rotating contact: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting rotating contact")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_rotating_contact_active(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_rotating_contact_active tool execution."""
    try:
        rotating_contact_id = arguments["rotating_contact_id"]

        logger.info(
            f"Getting active contact for rotation {rotating_contact_id}"
        )

        response = client._request(
            "GET", f"rotating_contact/{rotating_contact_id}/active"
        )

        output_lines = [
            f"**Active On-Call Contact for Rotation {rotating_contact_id}**\n"
        ]

        if isinstance(response, dict):
            name = response.get("name", "Unknown")
            output_lines.append(f"Currently On-Call: {name}")

            if response.get("email"):
                output_lines.append(f"Email: {response['email']}")
            if response.get("phone"):
                output_lines.append(f"Phone: {response['phone']}")

            for key, value in response.items():
                if key not in ("name", "email", "phone", "url",
                              "resource_uri") and value:
                    output_lines.append(f"{key}: {value}")
        elif isinstance(response, list) and response:
            output_lines.append(f"Active contacts: {len(response)}")
            for contact in response[:10]:
                if isinstance(contact, dict):
                    c_name = contact.get("name", "Unknown")
                    output_lines.append(f"  - {c_name}")
        else:
            output_lines.append("No active on-call contact found.")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Rotating contact {arguments.get('rotating_contact_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting active rotating contact: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting active rotating contact")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

ROTATING_CONTACTS_TOOL_DEFINITIONS = {
    "list_rotating_contacts": list_rotating_contacts_tool_definition,
    "get_rotating_contact_details": get_rotating_contact_details_tool_definition,
    "create_rotating_contact": create_rotating_contact_tool_definition,
    "update_rotating_contact": update_rotating_contact_tool_definition,
    "delete_rotating_contact": delete_rotating_contact_tool_definition,
    "get_rotating_contact_active": get_rotating_contact_active_tool_definition,
}

ROTATING_CONTACTS_HANDLERS = {
    "list_rotating_contacts": handle_list_rotating_contacts,
    "get_rotating_contact_details": handle_get_rotating_contact_details,
    "create_rotating_contact": handle_create_rotating_contact,
    "update_rotating_contact": handle_update_rotating_contact,
    "delete_rotating_contact": handle_delete_rotating_contact,
    "get_rotating_contact_active": handle_get_rotating_contact_active,
}
