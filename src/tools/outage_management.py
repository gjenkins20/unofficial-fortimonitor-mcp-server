"""Tools for managing outages - Phase 2 Priority 1."""

import logging
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


def acknowledge_outage_tool_definition() -> Tool:
    """Return tool definition for acknowledging an outage."""
    return Tool(
        name="acknowledge_outage",
        description=(
            "Acknowledge an active outage to indicate it has been seen and is being addressed. "
            "This helps track which alerts have been noticed and prevents duplicate responses. "
            "Optionally add a note explaining the acknowledgment or planned action."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "The ID of the outage to acknowledge",
                },
                "note": {
                    "type": "string",
                    "description": "Optional note explaining the acknowledgment or planned response",
                },
            },
            "required": ["outage_id"],
        },
    )


async def handle_acknowledge_outage(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle acknowledge_outage tool execution."""
    try:
        outage_id = arguments["outage_id"]
        note = arguments.get("note")

        logger.info(f"Acknowledging outage {outage_id}")

        # First get current outage details for context
        outage = client.get_outage_details(outage_id=outage_id)

        # Acknowledge the outage using the dedicated endpoint
        client.acknowledge_outage(outage_id=outage_id)

        # Add note/log if provided
        note_added = False
        if note:
            try:
                client.add_outage_log(outage_id=outage_id, entry=note)
                note_added = True
                logger.info(f"Added log to outage {outage_id}")
            except Exception as e:
                logger.warning(f"Failed to add log: {e}")

        # Format response
        output_lines = [
            f"**Outage {outage_id} Acknowledged**\n",
            f"Server: {outage.server_name or 'Unknown'}",
            f"Severity: {outage.severity}",
            f"Status: {outage.status}",
            "Acknowledged: Yes",
        ]

        if note and note_added:
            output_lines.append(f'\nLog added: "{note}"')
        elif note and not note_added:
            output_lines.append(
                "\nWarning: Log could not be added, but outage was acknowledged"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        logger.error(f"Outage {arguments.get('outage_id')} not found")
        return [
            TextContent(
                type="text",
                text=f"Error: Outage {arguments.get('outage_id')} not found. Please verify the outage ID.",
            )
        ]
    except APIError as e:
        logger.error(f"API error acknowledging outage: {e}")
        return [TextContent(type="text", text=f"Error acknowledging outage: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


def add_outage_note_tool_definition() -> Tool:
    """Return tool definition for adding a note to an outage."""
    return Tool(
        name="add_outage_note",
        description=(
            "Add a note or comment to an outage. "
            "Use this to document investigation progress, root cause analysis, "
            "resolution steps, or any other relevant information about the outage."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "The ID of the outage",
                },
                "note": {
                    "type": "string",
                    "description": "The note text to add (max 2000 characters recommended)",
                },
            },
            "required": ["outage_id", "note"],
        },
    )


async def handle_add_outage_note(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle add_outage_note tool execution."""
    try:
        outage_id = arguments["outage_id"]
        note = arguments["note"]

        # Validate note length
        if len(note) > 2000:
            return [
                TextContent(
                    type="text",
                    text="Error: Note is too long. Please keep notes under 2000 characters.",
                )
            ]

        logger.info(f"Adding log to outage {outage_id}")

        # Add the log entry (FortiMonitor uses "outage_log" for notes)
        response = client.add_outage_log(outage_id=outage_id, entry=note)

        # Format response
        output_lines = [
            f"**Log Added to Outage {outage_id}**\n",
            f'Message: "{note}"',
        ]

        # Include any timestamp from response if available
        if isinstance(response, dict) and response.get("created"):
            output_lines.append(f"Created: {response['created']}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        logger.error(f"Outage {arguments.get('outage_id')} not found")
        return [
            TextContent(
                type="text",
                text=f"Error: Outage {arguments.get('outage_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error adding log: {e}")
        return [TextContent(type="text", text=f"Error adding log: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


def get_outage_details_tool_definition() -> Tool:
    """Return tool definition for getting outage details."""
    return Tool(
        name="get_outage_details",
        description=(
            "Get detailed information about a specific outage, including severity, "
            "status, timing, acknowledgment status, and associated server information."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "The ID of the outage",
                }
            },
            "required": ["outage_id"],
        },
    )


async def handle_get_outage_details(
    arguments: dict,
    client: FortiMonitorClient,
) -> List[TextContent]:
    """Handle get_outage_details tool execution."""
    try:
        outage_id = arguments["outage_id"]

        logger.info(f"Getting details for outage {outage_id}")

        # Get detailed outage info (without full=true to avoid 500 errors)
        outage = client.get_outage_details(outage_id=outage_id, full=False)

        # Calculate duration if possible
        duration_str = "Ongoing"
        if outage.end_time:
            if outage.duration:
                minutes = outage.duration // 60
                if minutes < 60:
                    duration_str = f"{minutes} minutes"
                else:
                    hours = minutes // 60
                    remaining_mins = minutes % 60
                    duration_str = f"{hours}h {remaining_mins}m"
            else:
                duration_str = "Resolved"

        # Format response
        output_lines = [
            f"**Outage Details: {outage_id}**\n",
            f"Server: {outage.server_name or outage.server or 'Unknown'}",
            f"Severity: {outage.severity}",
            f"Status: {outage.status}",
            f"Started: {outage.start_time.strftime('%Y-%m-%d %H:%M:%S') if outage.start_time else 'Unknown'}",
            f"Ended: {outage.end_time.strftime('%Y-%m-%d %H:%M:%S') if outage.end_time else 'Ongoing'}",
            f"Duration: {duration_str}",
            f"Acknowledged: {'Yes' if outage.acknowledged else 'No'}",
        ]

        if outage.acknowledged_by:
            output_lines.append(f"Acknowledged by: {outage.acknowledged_by}")
        if outage.acknowledged_at:
            output_lines.append(
                f"Acknowledged at: {outage.acknowledged_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        if outage.message:
            output_lines.append(f"\nMessage: {outage.message}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Outage {arguments.get('outage_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error getting outage details: {e}")
        return [
            TextContent(type="text", text=f"Error getting outage details: {str(e)}")
        ]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]
