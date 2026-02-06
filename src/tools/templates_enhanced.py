"""Enhanced server template tools - create, update, delete, and reapply templates."""

import logging
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def create_server_template_tool_definition() -> Tool:
    """Return tool definition for creating a server template."""
    return Tool(
        name="create_server_template",
        description=(
            "Create a new server monitoring template. "
            "Templates define what metrics and services to monitor on servers."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the new server template"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the template"
                }
            },
            "required": ["name"]
        }
    )


def update_server_template_tool_definition() -> Tool:
    """Return tool definition for updating a server template."""
    return Tool(
        name="update_server_template",
        description=(
            "Update an existing server template's name or description."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "template_id": {
                    "type": "integer",
                    "description": "ID of the server template to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the template (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description for the template (optional)"
                }
            },
            "required": ["template_id"]
        }
    )


def delete_server_template_tool_definition() -> Tool:
    """Return tool definition for deleting a server template."""
    return Tool(
        name="delete_server_template",
        description=(
            "Delete a server monitoring template. "
            "Servers using this template will no longer receive updates from it."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "template_id": {
                    "type": "integer",
                    "description": "ID of the server template to delete"
                }
            },
            "required": ["template_id"]
        }
    )


def reapply_server_template_tool_definition() -> Tool:
    """Return tool definition for reapplying a server template."""
    return Tool(
        name="reapply_server_template",
        description=(
            "Reapply a server template to all servers currently using it. "
            "Useful after making changes to a template to push updates to all servers."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "template_id": {
                    "type": "integer",
                    "description": "ID of the server template to reapply"
                }
            },
            "required": ["template_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_create_server_template(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_server_template tool execution."""
    try:
        name = arguments["name"]
        description = arguments.get("description")

        logger.info(f"Creating server template: {name}")

        data = {"name": name}
        if description:
            data["description"] = description

        response = client._request("POST", "server_template", json_data=data)

        output_lines = [
            "**Server Template Created**\n",
            f"Name: {name}"
        ]

        if description:
            output_lines.append(f"Description: {description}")

        # Try to extract ID from response
        if isinstance(response, dict):
            if response.get("url"):
                parts = response["url"].rstrip("/").split("/")
                if parts:
                    output_lines.append(f"ID: {parts[-1]}")
            elif response.get("success"):
                output_lines.append(
                    "\nTemplate created. Use 'list_server_templates' to find the ID."
                )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating template: {e}")
        return [TextContent(type="text", text=f"Error creating template: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating template")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_server_template(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_server_template tool execution."""
    try:
        template_id = arguments["template_id"]
        name = arguments.get("name")
        description = arguments.get("description")

        if name is None and description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name' or 'description' must be provided."
            )]

        logger.info(f"Updating server template {template_id}")

        # Get current template for comparison
        try:
            current = client.get_server_template_details(template_id)
            current_name = current.name
        except Exception:
            current_name = f"ID {template_id}"

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        client._request("PUT", f"server_template/{template_id}", json_data=data)

        output_lines = ["**Server Template Updated**\n"]

        if name and name != current_name:
            output_lines.append(f"Name: '{current_name}' -> '{name}'")
        elif name:
            output_lines.append(f"Name: {name} (unchanged)")

        if description is not None:
            output_lines.append(f"Description: Updated")

        output_lines.append(f"Template ID: {template_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Template {arguments.get('template_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating template: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating template")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_server_template(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_server_template tool execution."""
    try:
        template_id = arguments["template_id"]

        logger.info(f"Deleting server template {template_id}")

        # Get template name before deleting
        try:
            template = client.get_server_template_details(template_id)
            template_name = template.name
        except Exception:
            template_name = f"ID {template_id}"

        # Delete the template
        client._request("DELETE", f"server_template/{template_id}")

        return [TextContent(
            type="text",
            text=(
                f"**Server Template Deleted**\n\n"
                f"Template '{template_name}' (ID: {template_id}) has been deleted.\n\n"
                f"Note: Servers that were using this template will no longer "
                f"receive monitoring updates from it."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Template {arguments.get('template_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting template: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting template")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_reapply_server_template(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle reapply_server_template tool execution."""
    try:
        template_id = arguments["template_id"]

        logger.info(f"Reapplying server template {template_id}")

        # Get template name for output
        try:
            template = client.get_server_template_details(template_id)
            template_name = template.name
        except Exception:
            template_name = f"ID {template_id}"

        # Reapply the template
        client._request("POST", f"server_template/{template_id}/reapply")

        return [TextContent(
            type="text",
            text=(
                f"**Server Template Reapplied**\n\n"
                f"Template '{template_name}' (ID: {template_id}) has been reapplied "
                f"to all servers currently using it.\n\n"
                f"Monitoring configuration updates will propagate to all associated servers."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Template {arguments.get('template_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error reapplying template: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error reapplying template")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

TEMPLATES_ENHANCED_TOOL_DEFINITIONS = {
    "create_server_template": create_server_template_tool_definition,
    "update_server_template": update_server_template_tool_definition,
    "delete_server_template": delete_server_template_tool_definition,
    "reapply_server_template": reapply_server_template_tool_definition,
}

TEMPLATES_ENHANCED_HANDLERS = {
    "create_server_template": handle_create_server_template,
    "update_server_template": handle_update_server_template,
    "delete_server_template": handle_delete_server_template,
    "reapply_server_template": handle_reapply_server_template,
}
