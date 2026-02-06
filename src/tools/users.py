"""User management tools for FortiMonitor."""

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


def list_users_tool_definition() -> Tool:
    """Return tool definition for listing users."""
    return Tool(
        name="list_users",
        description=(
            "List all users in FortiMonitor. "
            "Shows user name, email, and role information."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of users to return (default 50)"
                }
            }
        }
    )


def get_user_details_tool_definition() -> Tool:
    """Return tool definition for getting user details."""
    return Tool(
        name="get_user_details",
        description=(
            "Get detailed information about a specific user by ID."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "ID of the user"
                }
            },
            "required": ["user_id"]
        }
    )


def create_user_tool_definition() -> Tool:
    """Return tool definition for creating a user."""
    return Tool(
        name="create_user",
        description=(
            "Create a new user in FortiMonitor. "
            "Requires a name and email address."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the user"
                },
                "email": {
                    "type": "string",
                    "description": "Email address of the user"
                },
                "role": {
                    "type": "string",
                    "description": "Role to assign to the user (optional)"
                }
            },
            "required": ["name", "email"]
        }
    )


def update_user_tool_definition() -> Tool:
    """Return tool definition for updating a user."""
    return Tool(
        name="update_user",
        description=(
            "Update an existing user's name, email, or role. "
            "At least one field must be provided."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "ID of the user to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the user (optional)"
                },
                "email": {
                    "type": "string",
                    "description": "New email address for the user (optional)"
                },
                "role": {
                    "type": "string",
                    "description": "New role for the user (optional)"
                }
            },
            "required": ["user_id"]
        }
    )


def delete_user_tool_definition() -> Tool:
    """Return tool definition for deleting a user."""
    return Tool(
        name="delete_user",
        description=(
            "Delete a user from FortiMonitor. "
            "This permanently removes the user account."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "ID of the user to delete"
                }
            },
            "required": ["user_id"]
        }
    )


def get_user_addons_tool_definition() -> Tool:
    """Return tool definition for getting user addons."""
    return Tool(
        name="get_user_addons",
        description=(
            "Get addon information for users. "
            "Shows available addons and their configuration."
        ),
        inputSchema={
            "type": "object",
            "properties": {}
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_list_users(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_users tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing users (limit={limit})")

        response = client._request("GET", "user", params={"limit": limit})
        users = response.get("user_list", [])
        meta = response.get("meta", {})

        if not users:
            return [TextContent(type="text", text="No users found.")]

        total_count = meta.get("total_count", len(users))

        output_lines = [
            "**Users**\n",
            f"Found {len(users)} user(s):\n"
        ]

        for user in users:
            name = user.get("name", "Unknown")
            url = user.get("url", "")
            user_id = _extract_id_from_url(url)
            email = user.get("email", "N/A")
            role = user.get("role", "")

            output_lines.append(f"\n**{name}** (ID: {user_id})")
            output_lines.append(f"  Email: {email}")
            if role:
                output_lines.append(f"  Role: {role}")

        if total_count > len(users):
            output_lines.append(f"\n(Showing {len(users)} of {total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing users: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing users")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_user_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_user_details tool execution."""
    try:
        user_id = arguments["user_id"]

        logger.info(f"Getting user details for {user_id}")

        response = client._request("GET", f"user/{user_id}")

        name = response.get("name", "Unknown")
        output_lines = [f"**User: {name}** (ID: {user_id})\n"]

        if response.get("email"):
            output_lines.append(f"Email: {response['email']}")
        if response.get("role"):
            output_lines.append(f"Role: {response['role']}")

        # Include any other fields from the response
        for key, value in response.items():
            if key not in ("name", "email", "role", "url", "resource_uri") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: User {arguments.get('user_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting user details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting user details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_user(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_user tool execution."""
    try:
        name = arguments["name"]
        email = arguments["email"]
        role = arguments.get("role")

        logger.info(f"Creating user: {name}")

        data = {
            "name": name,
            "email": email,
        }
        if role:
            data["role"] = role

        response = client._request("POST", "user", json_data=data)

        output_lines = [
            "**User Created**\n",
            f"Name: {name}",
            f"Email: {email}"
        ]

        if role:
            output_lines.append(f"Role: {role}")

        if isinstance(response, dict) and response.get("url"):
            new_user_id = _extract_id_from_url(response["url"])
            output_lines.append(f"User ID: {new_user_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nUser created. Use 'list_users' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating user: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating user")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_user(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_user tool execution."""
    try:
        user_id = arguments["user_id"]
        name = arguments.get("name")
        email = arguments.get("email")
        role = arguments.get("role")

        if name is None and email is None and role is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name', 'email', or 'role' must be provided."
            )]

        logger.info(f"Updating user {user_id}")

        data = {}
        if name is not None:
            data["name"] = name
        if email is not None:
            data["email"] = email
        if role is not None:
            data["role"] = role

        client._request("PUT", f"user/{user_id}", json_data=data)

        output_lines = ["**User Updated**\n"]
        if name:
            output_lines.append(f"Name: {name}")
        if email:
            output_lines.append(f"Email: {email}")
        if role:
            output_lines.append(f"Role: {role}")
        output_lines.append(f"User ID: {user_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: User {arguments.get('user_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating user: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating user")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_user(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_user tool execution."""
    try:
        user_id = arguments["user_id"]

        logger.info(f"Deleting user {user_id}")

        # Get name before deleting
        try:
            response = client._request("GET", f"user/{user_id}")
            user_name = response.get("name", f"ID {user_id}")
        except Exception:
            user_name = f"ID {user_id}"

        client._request("DELETE", f"user/{user_id}")

        return [TextContent(
            type="text",
            text=(
                f"**User Deleted**\n\n"
                f"User '{user_name}' (ID: {user_id}) has been deleted."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: User {arguments.get('user_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting user: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting user")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_user_addons(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_user_addons tool execution."""
    try:
        logger.info("Getting user addons")

        response = client._request("GET", "user/getaddons")

        if not response:
            return [TextContent(type="text", text="No addon information available.")]

        output_lines = ["**User Addons**\n"]

        if isinstance(response, dict):
            for key, value in response.items():
                if key not in ("url", "resource_uri"):
                    output_lines.append(f"{key}: {value}")
        elif isinstance(response, list):
            for addon in response:
                if isinstance(addon, dict):
                    name = addon.get("name", "Unknown")
                    addon_id = _extract_id_from_url(addon.get("url", ""))
                    output_lines.append(f"\n**{name}** (ID: {addon_id})")
                    for key, value in addon.items():
                        if key not in ("name", "url", "resource_uri") and value:
                            output_lines.append(f"  {key}: {value}")
                else:
                    output_lines.append(f"  - {addon}")
        else:
            output_lines.append(str(response))

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error getting user addons: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting user addons")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

USERS_TOOL_DEFINITIONS = {
    "list_users": list_users_tool_definition,
    "get_user_details": get_user_details_tool_definition,
    "create_user": create_user_tool_definition,
    "update_user": update_user_tool_definition,
    "delete_user": delete_user_tool_definition,
    "get_user_addons": get_user_addons_tool_definition,
}

USERS_HANDLERS = {
    "list_users": handle_list_users,
    "get_user_details": handle_get_user_details,
    "create_user": handle_create_user,
    "update_user": handle_update_user,
    "delete_user": handle_delete_user,
    "get_user_addons": handle_get_user_addons,
}
