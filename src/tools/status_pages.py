"""Status page management tools for FortiMonitor."""

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


def list_status_pages_tool_definition() -> Tool:
    """Return tool definition for listing status pages."""
    return Tool(
        name="list_status_pages",
        description=(
            "List all public status pages configured in FortiMonitor. "
            "Status pages provide public-facing service status information."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of status pages to return (default 50)"
                }
            }
        }
    )


def get_status_page_details_tool_definition() -> Tool:
    """Return tool definition for getting status page details."""
    return Tool(
        name="get_status_page_details",
        description=(
            "Get detailed information about a specific status page."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "status_page_id": {
                    "type": "integer",
                    "description": "ID of the status page"
                }
            },
            "required": ["status_page_id"]
        }
    )


def create_status_page_tool_definition() -> Tool:
    """Return tool definition for creating a status page."""
    return Tool(
        name="create_status_page",
        description=(
            "Create a new public status page for communicating service status "
            "to customers and stakeholders."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the status page"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the status page"
                }
            },
            "required": ["name"]
        }
    )


def update_status_page_tool_definition() -> Tool:
    """Return tool definition for updating a status page."""
    return Tool(
        name="update_status_page",
        description=(
            "Update an existing status page's name or description."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "status_page_id": {
                    "type": "integer",
                    "description": "ID of the status page to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the status page (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description for the status page (optional)"
                }
            },
            "required": ["status_page_id"]
        }
    )


def delete_status_page_tool_definition() -> Tool:
    """Return tool definition for deleting a status page."""
    return Tool(
        name="delete_status_page",
        description=(
            "Delete a public status page. This permanently removes the page."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "status_page_id": {
                    "type": "integer",
                    "description": "ID of the status page to delete"
                }
            },
            "required": ["status_page_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_list_status_pages(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_status_pages tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing status pages (limit={limit})")

        response = client._request("GET", "status_page", params={"limit": limit})
        pages = response.get("status_page_list", [])
        meta = response.get("meta", {})

        if not pages:
            return [TextContent(type="text", text="No status pages found.")]

        total_count = meta.get("total_count", len(pages))

        output_lines = [
            "**Status Pages**\n",
            f"Found {len(pages)} status page(s):\n"
        ]

        for page in pages:
            name = page.get("name", "Unknown")
            page_id = _extract_id_from_url(page.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {page_id})")
            if page.get("description"):
                output_lines.append(f"  Description: {page['description']}")
            if page.get("public_url"):
                output_lines.append(f"  Public URL: {page['public_url']}")

        if total_count > len(pages):
            output_lines.append(f"\n(Showing {len(pages)} of {total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing status pages: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing status pages")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_status_page_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_status_page_details tool execution."""
    try:
        status_page_id = arguments["status_page_id"]

        logger.info(f"Getting status page details for {status_page_id}")

        response = client._request("GET", f"status_page/{status_page_id}")

        name = response.get("name", "Unknown")
        output_lines = [f"**Status Page: {name}** (ID: {status_page_id})\n"]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")
        if response.get("public_url"):
            output_lines.append(f"Public URL: {response['public_url']}")

        for key, value in response.items():
            if key not in ("name", "description", "url", "resource_uri",
                          "public_url") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Status page {arguments.get('status_page_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting status page details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting status page details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_status_page(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_status_page tool execution."""
    try:
        name = arguments["name"]
        description = arguments.get("description")

        logger.info(f"Creating status page: {name}")

        data = {"name": name}
        if description:
            data["description"] = description

        response = client._request("POST", "status_page", json_data=data)

        output_lines = [
            "**Status Page Created**\n",
            f"Name: {name}"
        ]

        if description:
            output_lines.append(f"Description: {description}")

        if isinstance(response, dict) and response.get("url"):
            page_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Status Page ID: {page_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nStatus page created. Use 'list_status_pages' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating status page: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating status page")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_status_page(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_status_page tool execution."""
    try:
        status_page_id = arguments["status_page_id"]
        name = arguments.get("name")
        description = arguments.get("description")

        if name is None and description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name' or 'description' must be provided."
            )]

        logger.info(f"Updating status page {status_page_id}")

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        client._request("PUT", f"status_page/{status_page_id}", json_data=data)

        output_lines = ["**Status Page Updated**\n"]
        if name:
            output_lines.append(f"Name: {name}")
        if description is not None:
            output_lines.append(f"Description: Updated")
        output_lines.append(f"Status Page ID: {status_page_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Status page {arguments.get('status_page_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating status page: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating status page")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_status_page(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_status_page tool execution."""
    try:
        status_page_id = arguments["status_page_id"]

        logger.info(f"Deleting status page {status_page_id}")

        try:
            response = client._request("GET", f"status_page/{status_page_id}")
            page_name = response.get("name", f"ID {status_page_id}")
        except Exception:
            page_name = f"ID {status_page_id}"

        client._request("DELETE", f"status_page/{status_page_id}")

        return [TextContent(
            type="text",
            text=(
                f"**Status Page Deleted**\n\n"
                f"Status page '{page_name}' (ID: {status_page_id}) has been deleted."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Status page {arguments.get('status_page_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting status page: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting status page")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

STATUS_PAGES_TOOL_DEFINITIONS = {
    "list_status_pages": list_status_pages_tool_definition,
    "get_status_page_details": get_status_page_details_tool_definition,
    "create_status_page": create_status_page_tool_definition,
    "update_status_page": update_status_page_tool_definition,
    "delete_status_page": delete_status_page_tool_definition,
}

STATUS_PAGES_HANDLERS = {
    "list_status_pages": handle_list_status_pages,
    "get_status_page_details": handle_get_status_page_details,
    "create_status_page": handle_create_status_page,
    "update_status_page": handle_update_status_page,
    "delete_status_page": handle_delete_status_page,
}
