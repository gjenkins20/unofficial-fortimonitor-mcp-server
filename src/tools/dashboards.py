"""Dashboard management tools for FortiMonitor."""

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


def list_dashboards_tool_definition() -> Tool:
    """Return tool definition for listing dashboards."""
    return Tool(
        name="list_dashboards",
        description=(
            "List all dashboards configured in FortiMonitor. "
            "Dashboards provide visual overviews of monitoring data."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of dashboards to return (default 50)"
                }
            }
        }
    )


def get_dashboard_details_tool_definition() -> Tool:
    """Return tool definition for getting dashboard details."""
    return Tool(
        name="get_dashboard_details",
        description=(
            "Get detailed information about a specific dashboard, "
            "including its configuration and widgets."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "dashboard_id": {
                    "type": "integer",
                    "description": "ID of the dashboard"
                }
            },
            "required": ["dashboard_id"]
        }
    )


def create_dashboard_tool_definition() -> Tool:
    """Return tool definition for creating a dashboard."""
    return Tool(
        name="create_dashboard",
        description=(
            "Create a new monitoring dashboard in FortiMonitor."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the dashboard"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the dashboard"
                }
            },
            "required": ["name"]
        }
    )


def update_dashboard_tool_definition() -> Tool:
    """Return tool definition for updating a dashboard."""
    return Tool(
        name="update_dashboard",
        description=(
            "Update an existing dashboard's name or description."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "dashboard_id": {
                    "type": "integer",
                    "description": "ID of the dashboard to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the dashboard (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description for the dashboard (optional)"
                }
            },
            "required": ["dashboard_id"]
        }
    )


def delete_dashboard_tool_definition() -> Tool:
    """Return tool definition for deleting a dashboard."""
    return Tool(
        name="delete_dashboard",
        description=(
            "Delete a dashboard. This permanently removes the dashboard "
            "and all its widget configurations."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "dashboard_id": {
                    "type": "integer",
                    "description": "ID of the dashboard to delete"
                }
            },
            "required": ["dashboard_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_list_dashboards(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_dashboards tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing dashboards (limit={limit})")

        response = client._request("GET", "dashboard", params={"limit": limit})
        dashboards = response.get("dashboard_list", [])
        meta = response.get("meta", {})

        if not dashboards:
            return [TextContent(type="text", text="No dashboards found.")]

        total_count = meta.get("total_count", len(dashboards))

        output_lines = [
            "**Dashboards**\n",
            f"Found {len(dashboards)} dashboard(s):\n"
        ]

        for dash in dashboards:
            name = dash.get("name", "Unknown")
            dash_id = _extract_id_from_url(dash.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {dash_id})")
            if dash.get("description"):
                output_lines.append(f"  Description: {dash['description']}")

        if total_count > len(dashboards):
            output_lines.append(f"\n(Showing {len(dashboards)} of {total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing dashboards: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing dashboards")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_dashboard_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_dashboard_details tool execution."""
    try:
        dashboard_id = arguments["dashboard_id"]

        logger.info(f"Getting dashboard details for {dashboard_id}")

        response = client._request("GET", f"dashboard/{dashboard_id}")

        name = response.get("name", "Unknown")
        output_lines = [f"**Dashboard: {name}** (ID: {dashboard_id})\n"]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        # Show widgets if present
        widgets = response.get("widgets", response.get("widget_list", []))
        if widgets:
            output_lines.append(f"\n**Widgets ({len(widgets)}):**")
            for widget in widgets[:20]:
                if isinstance(widget, dict):
                    w_name = widget.get("name", widget.get("title", "Unnamed"))
                    w_type = widget.get("type", widget.get("widget_type", "unknown"))
                    output_lines.append(f"  - {w_name} (type: {w_type})")
                else:
                    output_lines.append(f"  - {widget}")
            if len(widgets) > 20:
                output_lines.append(f"  ... and {len(widgets) - 20} more")

        # Include other fields
        for key, value in response.items():
            if key not in ("name", "description", "url", "resource_uri",
                          "widgets", "widget_list") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Dashboard {arguments.get('dashboard_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting dashboard details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting dashboard details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_dashboard(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_dashboard tool execution."""
    try:
        name = arguments["name"]
        description = arguments.get("description")

        logger.info(f"Creating dashboard: {name}")

        data = {"name": name}
        if description:
            data["description"] = description

        response = client._request("POST", "dashboard", json_data=data)

        output_lines = [
            "**Dashboard Created**\n",
            f"Name: {name}"
        ]

        if description:
            output_lines.append(f"Description: {description}")

        if isinstance(response, dict) and response.get("url"):
            dash_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Dashboard ID: {dash_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nDashboard created. Use 'list_dashboards' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating dashboard: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating dashboard")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_dashboard(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_dashboard tool execution."""
    try:
        dashboard_id = arguments["dashboard_id"]
        name = arguments.get("name")
        description = arguments.get("description")

        if name is None and description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name' or 'description' must be provided."
            )]

        logger.info(f"Updating dashboard {dashboard_id}")

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        client._request("PUT", f"dashboard/{dashboard_id}", json_data=data)

        output_lines = ["**Dashboard Updated**\n"]
        if name:
            output_lines.append(f"Name: {name}")
        if description is not None:
            output_lines.append(f"Description: Updated")
        output_lines.append(f"Dashboard ID: {dashboard_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Dashboard {arguments.get('dashboard_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating dashboard: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating dashboard")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_dashboard(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_dashboard tool execution."""
    try:
        dashboard_id = arguments["dashboard_id"]

        logger.info(f"Deleting dashboard {dashboard_id}")

        # Get name before deleting
        try:
            response = client._request("GET", f"dashboard/{dashboard_id}")
            dash_name = response.get("name", f"ID {dashboard_id}")
        except Exception:
            dash_name = f"ID {dashboard_id}"

        client._request("DELETE", f"dashboard/{dashboard_id}")

        return [TextContent(
            type="text",
            text=(
                f"**Dashboard Deleted**\n\n"
                f"Dashboard '{dash_name}' (ID: {dashboard_id}) has been deleted."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Dashboard {arguments.get('dashboard_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting dashboard: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting dashboard")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

DASHBOARDS_TOOL_DEFINITIONS = {
    "list_dashboards": list_dashboards_tool_definition,
    "get_dashboard_details": get_dashboard_details_tool_definition,
    "create_dashboard": create_dashboard_tool_definition,
    "update_dashboard": update_dashboard_tool_definition,
    "delete_dashboard": delete_dashboard_tool_definition,
}

DASHBOARDS_HANDLERS = {
    "list_dashboards": handle_list_dashboards,
    "get_dashboard_details": handle_get_dashboard_details,
    "create_dashboard": handle_create_dashboard,
    "update_dashboard": handle_update_dashboard,
    "delete_dashboard": handle_delete_dashboard,
}
