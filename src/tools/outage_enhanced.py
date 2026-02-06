"""Enhanced outage operations - additional outage management MCP tools."""

import logging
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def list_active_outages_tool_definition() -> Tool:
    """Return tool definition for listing active outages."""
    return Tool(
        name="list_active_outages",
        description=(
            "List only active (currently ongoing) outages. "
            "Optionally filter by server ID."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "Optional server ID to filter active outages for a specific server",
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 500,
                    "description": "Maximum number of outages to return (default 50)",
                },
            },
        },
    )


def list_resolved_outages_tool_definition() -> Tool:
    """Return tool definition for listing resolved outages."""
    return Tool(
        name="list_resolved_outages",
        description=(
            "List resolved (no longer active) outages. "
            "Optionally filter by server ID."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "Optional server ID to filter resolved outages for a specific server",
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 500,
                    "description": "Maximum number of outages to return (default 50)",
                },
            },
        },
    )


def broadcast_outage_tool_definition() -> Tool:
    """Return tool definition for broadcasting an outage message."""
    return Tool(
        name="broadcast_outage",
        description=(
            "Broadcast a message about an outage to all configured notification contacts. "
            "Use this to send additional updates or information about an ongoing incident."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "The ID of the outage to broadcast about",
                },
                "message": {
                    "type": "string",
                    "description": "The message to broadcast about the outage",
                },
            },
            "required": ["outage_id", "message"],
        },
    )


def escalate_outage_tool_definition() -> Tool:
    """Return tool definition for escalating an outage."""
    return Tool(
        name="escalate_outage",
        description=(
            "Escalate an outage to the next notification level. "
            "This triggers the next escalation tier in the notification chain."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "The ID of the outage to escalate",
                },
            },
            "required": ["outage_id"],
        },
    )


def delay_outage_tool_definition() -> Tool:
    """Return tool definition for delaying outage notifications."""
    return Tool(
        name="delay_outage",
        description=(
            "Delay outage notifications by a specified number of minutes. "
            "Useful to temporarily suppress alerts while investigating or performing maintenance."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "The ID of the outage to delay notifications for",
                },
                "minutes": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of minutes to delay notifications",
                },
            },
            "required": ["outage_id", "minutes"],
        },
    )


def force_resolve_outage_tool_definition() -> Tool:
    """Return tool definition for force resolving an outage."""
    return Tool(
        name="force_resolve_outage",
        description=(
            "Force resolve a manual or custom incident. "
            "Use this when an outage needs to be manually closed."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "The ID of the outage to force resolve",
                },
            },
            "required": ["outage_id"],
        },
    )


def set_outage_lead_tool_definition() -> Tool:
    """Return tool definition for setting the outage lead."""
    return Tool(
        name="set_outage_lead",
        description=(
            "Set the lead person on an outage. "
            "The lead is the primary person responsible for managing the incident."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "The ID of the outage",
                },
                "user_url": {
                    "type": "string",
                    "description": "The API URL of the user to set as lead (e.g. /api/v2/contact/123)",
                },
            },
            "required": ["outage_id", "user_url"],
        },
    )


def add_outage_summary_tool_definition() -> Tool:
    """Return tool definition for adding an outage summary."""
    return Tool(
        name="add_outage_summary",
        description=(
            "Add a summary to an outage. "
            "Use this to provide a high-level description of the incident for reporting."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "The ID of the outage",
                },
                "summary": {
                    "type": "string",
                    "description": "The summary text for the outage",
                },
            },
            "required": ["outage_id", "summary"],
        },
    )


def set_outage_tags_tool_definition() -> Tool:
    """Return tool definition for setting outage tags."""
    return Tool(
        name="set_outage_tags",
        description=(
            "Set incident tags on an outage. "
            "Tags help categorize and filter outages for reporting and analysis."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "The ID of the outage",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tags to set on the outage",
                },
            },
            "required": ["outage_id", "tags"],
        },
    )


def get_outage_actions_tool_definition() -> Tool:
    """Return tool definition for getting outage notification actions."""
    return Tool(
        name="get_outage_actions",
        description=(
            "Get notification actions taken for an outage. "
            "Shows what notifications were sent, to whom, and when."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "The ID of the outage",
                },
            },
            "required": ["outage_id"],
        },
    )


def list_outage_logs_tool_definition() -> Tool:
    """Return tool definition for listing outage log entries."""
    return Tool(
        name="list_outage_logs",
        description=(
            "List log entries for an outage. "
            "Shows the timeline of events, notes, and status changes for an incident."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "The ID of the outage",
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 500,
                    "description": "Maximum number of log entries to return (default 50)",
                },
            },
            "required": ["outage_id"],
        },
    )


def update_outage_description_tool_definition() -> Tool:
    """Return tool definition for updating outage description."""
    return Tool(
        name="update_outage_description",
        description=(
            "Update the description of a custom incident. "
            "Use this to modify the description text of a manually created outage."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_id": {
                    "type": "integer",
                    "description": "The ID of the outage",
                },
                "description": {
                    "type": "string",
                    "description": "The new description for the outage",
                },
            },
            "required": ["outage_id", "description"],
        },
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_list_active_outages(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_active_outages tool execution."""
    try:
        params = {"limit": arguments.get("limit", 50)}
        server_id = arguments.get("server_id")
        if server_id is not None:
            params["server_id"] = server_id

        logger.info(f"Listing active outages with params: {params}")

        response = client._request("GET", "/outage/active", params=params)

        outage_list = response.get("outage_list", [])
        total_count = response.get("meta", {}).get("total_count", len(outage_list))

        if not outage_list:
            filter_desc = f" for server {server_id}" if server_id else ""
            return [
                TextContent(
                    type="text",
                    text=f"No active outages found{filter_desc}.",
                )
            ]

        filter_desc = f" for server {server_id}" if server_id else ""
        output_lines = [
            f"**Active Outages{filter_desc}**\n",
            f"Showing {len(outage_list)} of {total_count} total:\n",
        ]

        for outage in outage_list:
            outage_id = _extract_id_from_url(outage.get("url", ""))
            server_name = outage.get("server_name", "N/A")
            severity = outage.get("severity", "unknown")
            status = outage.get("status", "unknown")
            start_time = outage.get("start_time", "Unknown")
            message = outage.get("message", "")
            acknowledged = outage.get("acknowledged", False)

            ack_str = "Acknowledged" if acknowledged else "Not Acknowledged"
            output_lines.append(f"- **Outage {outage_id}** | {severity.upper()}")
            output_lines.append(f"  Server: {server_name}")
            output_lines.append(f"  Status: {status} | {ack_str}")
            output_lines.append(f"  Started: {start_time}")
            if message:
                output_lines.append(f"  Message: {message}")
            output_lines.append("")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(type="text", text="Error: Resource not found.")
        ]
    except APIError as e:
        logger.error(f"API error listing active outages: {e}")
        return [TextContent(type="text", text=f"Error listing active outages: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in list_active_outages")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_resolved_outages(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_resolved_outages tool execution."""
    try:
        params = {"limit": arguments.get("limit", 50)}
        server_id = arguments.get("server_id")
        if server_id is not None:
            params["server_id"] = server_id

        logger.info(f"Listing resolved outages with params: {params}")

        response = client._request("GET", "/outage/resolved", params=params)

        outage_list = response.get("outage_list", [])
        total_count = response.get("meta", {}).get("total_count", len(outage_list))

        if not outage_list:
            filter_desc = f" for server {server_id}" if server_id else ""
            return [
                TextContent(
                    type="text",
                    text=f"No resolved outages found{filter_desc}.",
                )
            ]

        filter_desc = f" for server {server_id}" if server_id else ""
        output_lines = [
            f"**Resolved Outages{filter_desc}**\n",
            f"Showing {len(outage_list)} of {total_count} total:\n",
        ]

        for outage in outage_list:
            outage_id = _extract_id_from_url(outage.get("url", ""))
            server_name = outage.get("server_name", "N/A")
            severity = outage.get("severity", "unknown")
            start_time = outage.get("start_time", "Unknown")
            end_time = outage.get("end_time", "Unknown")
            duration = outage.get("duration", None)
            message = outage.get("message", "")

            duration_str = f"{duration // 60}m" if duration else "N/A"
            output_lines.append(f"- **Outage {outage_id}** | {severity.upper()}")
            output_lines.append(f"  Server: {server_name}")
            output_lines.append(f"  Started: {start_time}")
            output_lines.append(f"  Ended: {end_time}")
            output_lines.append(f"  Duration: {duration_str}")
            if message:
                output_lines.append(f"  Message: {message}")
            output_lines.append("")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(type="text", text="Error: Resource not found.")
        ]
    except APIError as e:
        logger.error(f"API error listing resolved outages: {e}")
        return [TextContent(type="text", text=f"Error listing resolved outages: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in list_resolved_outages")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_broadcast_outage(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle broadcast_outage tool execution."""
    try:
        outage_id = arguments["outage_id"]
        message = arguments["message"]

        logger.info(f"Broadcasting message for outage {outage_id}")

        client._request(
            "POST",
            f"outage/{outage_id}/broadcast",
            json_data={"message": message},
        )

        output_lines = [
            f"**Outage {outage_id} - Broadcast Sent**\n",
            f"Message: \"{message}\"",
        ]

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Outage {arguments.get('outage_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error broadcasting outage: {e}")
        return [TextContent(type="text", text=f"Error broadcasting outage: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in broadcast_outage")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_escalate_outage(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle escalate_outage tool execution."""
    try:
        outage_id = arguments["outage_id"]

        logger.info(f"Escalating outage {outage_id}")

        client._request("POST", f"outage/{outage_id}/escalate")

        output_lines = [
            f"**Outage {outage_id} - Escalated**\n",
            "The outage has been escalated to the next notification level.",
        ]

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Outage {arguments.get('outage_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error escalating outage: {e}")
        return [TextContent(type="text", text=f"Error escalating outage: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in escalate_outage")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delay_outage(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delay_outage tool execution."""
    try:
        outage_id = arguments["outage_id"]
        minutes = arguments["minutes"]

        logger.info(f"Delaying outage {outage_id} notifications by {minutes} minutes")

        client._request(
            "POST",
            f"outage/{outage_id}/delay",
            json_data={"minutes": minutes},
        )

        output_lines = [
            f"**Outage {outage_id} - Notifications Delayed**\n",
            f"Notifications delayed by {minutes} minute(s).",
        ]

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Outage {arguments.get('outage_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error delaying outage: {e}")
        return [TextContent(type="text", text=f"Error delaying outage: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in delay_outage")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_force_resolve_outage(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle force_resolve_outage tool execution."""
    try:
        outage_id = arguments["outage_id"]

        logger.info(f"Force resolving outage {outage_id}")

        client._request("POST", f"outage/{outage_id}/force_resolve")

        output_lines = [
            f"**Outage {outage_id} - Force Resolved**\n",
            "The outage has been force resolved.",
        ]

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Outage {arguments.get('outage_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error force resolving outage: {e}")
        return [TextContent(type="text", text=f"Error force resolving outage: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in force_resolve_outage")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_set_outage_lead(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle set_outage_lead tool execution."""
    try:
        outage_id = arguments["outage_id"]
        user_url = arguments["user_url"]

        logger.info(f"Setting lead for outage {outage_id} to {user_url}")

        client._request(
            "PUT",
            f"outage/{outage_id}/lead",
            json_data={"who": user_url},
        )

        output_lines = [
            f"**Outage {outage_id} - Lead Set**\n",
            f"Lead assigned to: {user_url}",
        ]

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Outage {arguments.get('outage_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error setting outage lead: {e}")
        return [TextContent(type="text", text=f"Error setting outage lead: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in set_outage_lead")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_add_outage_summary(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle add_outage_summary tool execution."""
    try:
        outage_id = arguments["outage_id"]
        summary = arguments["summary"]

        logger.info(f"Adding summary to outage {outage_id}")

        client._request(
            "PUT",
            f"outage/{outage_id}/summary",
            json_data={"summary": summary},
        )

        output_lines = [
            f"**Outage {outage_id} - Summary Added**\n",
            f"Summary: \"{summary}\"",
        ]

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Outage {arguments.get('outage_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error adding outage summary: {e}")
        return [TextContent(type="text", text=f"Error adding outage summary: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in add_outage_summary")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_set_outage_tags(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle set_outage_tags tool execution."""
    try:
        outage_id = arguments["outage_id"]
        tags = arguments["tags"]

        logger.info(f"Setting tags on outage {outage_id}: {tags}")

        client._request(
            "PUT",
            f"outage/{outage_id}/tags",
            json_data={"tags": tags},
        )

        output_lines = [
            f"**Outage {outage_id} - Tags Set**\n",
            f"Tags: {', '.join(tags)}",
        ]

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Outage {arguments.get('outage_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error setting outage tags: {e}")
        return [TextContent(type="text", text=f"Error setting outage tags: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in set_outage_tags")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_outage_actions(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_outage_actions tool execution."""
    try:
        outage_id = arguments["outage_id"]

        logger.info(f"Getting notification actions for outage {outage_id}")

        response = client._request("GET", f"outage/{outage_id}/actions")

        action_list = response.get("action_list", [])

        if not action_list:
            return [
                TextContent(
                    type="text",
                    text=f"No notification actions found for outage {outage_id}.",
                )
            ]

        output_lines = [
            f"**Notification Actions for Outage {outage_id}**\n",
            f"Found {len(action_list)} action(s):\n",
        ]

        for action in action_list:
            action_type = action.get("type", "unknown")
            contact = action.get("contact", "N/A")
            status = action.get("status", "unknown")
            timestamp = action.get("time", "Unknown")
            message = action.get("message", "")

            output_lines.append(f"- **{action_type}**")
            output_lines.append(f"  Contact: {contact}")
            output_lines.append(f"  Status: {status}")
            output_lines.append(f"  Time: {timestamp}")
            if message:
                output_lines.append(f"  Message: {message}")
            output_lines.append("")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Outage {arguments.get('outage_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error getting outage actions: {e}")
        return [TextContent(type="text", text=f"Error getting outage actions: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in get_outage_actions")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_outage_logs(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_outage_logs tool execution."""
    try:
        outage_id = arguments["outage_id"]
        limit = arguments.get("limit", 50)

        logger.info(f"Listing logs for outage {outage_id} (limit={limit})")

        response = client._request(
            "GET",
            f"outage/{outage_id}/outage_log",
            params={"limit": limit},
        )

        log_list = response.get("outage_log_list", [])
        total_count = response.get("meta", {}).get("total_count", len(log_list))

        if not log_list:
            return [
                TextContent(
                    type="text",
                    text=f"No log entries found for outage {outage_id}.",
                )
            ]

        output_lines = [
            f"**Log Entries for Outage {outage_id}**\n",
            f"Showing {len(log_list)} of {total_count} total:\n",
        ]

        for log_entry in log_list:
            entry_text = log_entry.get("entry", log_entry.get("text", ""))
            created = log_entry.get("created", "Unknown")
            author = log_entry.get("author", "")

            output_lines.append(f"- [{created}]")
            if author:
                output_lines.append(f"  Author: {author}")
            output_lines.append(f"  {entry_text}")
            output_lines.append("")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Outage {arguments.get('outage_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error listing outage logs: {e}")
        return [TextContent(type="text", text=f"Error listing outage logs: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in list_outage_logs")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_outage_description(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_outage_description tool execution."""
    try:
        outage_id = arguments["outage_id"]
        description = arguments["description"]

        logger.info(f"Updating description for outage {outage_id}")

        client._request(
            "PUT",
            f"outage/{outage_id}/description",
            json_data={"description": description},
        )

        output_lines = [
            f"**Outage {outage_id} - Description Updated**\n",
            f"Description: \"{description}\"",
        ]

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [
            TextContent(
                type="text",
                text=f"Error: Outage {arguments.get('outage_id')} not found.",
            )
        ]
    except APIError as e:
        logger.error(f"API error updating outage description: {e}")
        return [
            TextContent(type="text", text=f"Error updating outage description: {str(e)}")
        ]
    except Exception as e:
        logger.exception("Unexpected error in update_outage_description")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _extract_id_from_url(url: str) -> str:
    """Extract the numeric ID from a FortiMonitor API URL.

    FortiMonitor embeds IDs in URL strings like '/api/v2/outage/12345'.
    Returns the last numeric segment, or 'N/A' if not parseable.
    """
    if not url:
        return "N/A"
    parts = url.rstrip("/").split("/")
    for part in reversed(parts):
        if part.isdigit():
            return part
    return "N/A"


# ============================================================================
# EXPORTED DICTS
# ============================================================================


OUTAGE_ENHANCED_TOOL_DEFINITIONS = {
    "list_active_outages": list_active_outages_tool_definition,
    "list_resolved_outages": list_resolved_outages_tool_definition,
    "broadcast_outage": broadcast_outage_tool_definition,
    "escalate_outage": escalate_outage_tool_definition,
    "delay_outage": delay_outage_tool_definition,
    "force_resolve_outage": force_resolve_outage_tool_definition,
    "set_outage_lead": set_outage_lead_tool_definition,
    "add_outage_summary": add_outage_summary_tool_definition,
    "set_outage_tags": set_outage_tags_tool_definition,
    "get_outage_actions": get_outage_actions_tool_definition,
    "list_outage_logs": list_outage_logs_tool_definition,
    "update_outage_description": update_outage_description_tool_definition,
}

OUTAGE_ENHANCED_HANDLERS = {
    "list_active_outages": handle_list_active_outages,
    "list_resolved_outages": handle_list_resolved_outages,
    "broadcast_outage": handle_broadcast_outage,
    "escalate_outage": handle_escalate_outage,
    "delay_outage": handle_delay_outage,
    "force_resolve_outage": handle_force_resolve_outage,
    "set_outage_lead": handle_set_outage_lead,
    "add_outage_summary": handle_add_outage_summary,
    "set_outage_tags": handle_set_outage_tags,
    "get_outage_actions": handle_get_outage_actions,
    "list_outage_logs": handle_list_outage_logs,
    "update_outage_description": handle_update_outage_description,
}
