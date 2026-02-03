"""Notification management tools - Phase 2 Priority 4."""

import logging
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def list_notification_schedules_tool_definition() -> Tool:
    """Return tool definition for listing notification schedules."""
    return Tool(
        name="list_notification_schedules",
        description=(
            "List all notification schedules. Notification schedules define when "
            "alerts are sent (e.g., business hours only, 24/7, weekends, etc.)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of schedules to return (default 50)"
                }
            }
        }
    )


def get_notification_schedule_details_tool_definition() -> Tool:
    """Return tool definition for getting notification schedule details."""
    return Tool(
        name="get_notification_schedule_details",
        description=(
            "Get detailed information about a specific notification schedule, "
            "including all time intervals when notifications are active."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "integer",
                    "description": "The ID of the notification schedule"
                }
            },
            "required": ["schedule_id"]
        }
    )


def list_contact_groups_tool_definition() -> Tool:
    """Return tool definition for listing contact groups."""
    return Tool(
        name="list_contact_groups",
        description=(
            "List all contact groups. Contact groups define which contacts "
            "receive alerts together."
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


def get_contact_group_details_tool_definition() -> Tool:
    """Return tool definition for getting contact group details."""
    return Tool(
        name="get_contact_group_details",
        description=(
            "Get detailed information about a specific contact group, "
            "including all contacts in the group."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "The ID of the contact group"
                }
            },
            "required": ["group_id"]
        }
    )


def list_contacts_tool_definition() -> Tool:
    """Return tool definition for listing contacts."""
    return Tool(
        name="list_contacts",
        description=(
            "List all notification contacts. Contacts are people who receive alerts "
            "via email, SMS, phone, or other methods."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of contacts to return (default 50)"
                }
            }
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_list_notification_schedules(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_notification_schedules tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing notification schedules (limit={limit})")

        response = client.list_notification_schedules(limit=limit)
        schedules = response.notification_schedule_list

        if not schedules:
            return [TextContent(
                type="text",
                text="No notification schedules found."
            )]

        output_lines = [
            f"**Notification Schedules**\n",
            f"Found {len(schedules)} schedule(s):\n"
        ]

        for schedule in schedules:
            output_lines.append(f"\n**{schedule.name}** (ID: {schedule.id})")
            if schedule.schedule_type:
                output_lines.append(f"  Type: {schedule.schedule_type}")
            if schedule.timezone:
                output_lines.append(f"  Timezone: {schedule.timezone}")
            if schedule.intervals:
                output_lines.append(f"  Intervals: {len(schedule.intervals)} configured")

        if response.total_count and response.total_count > len(schedules):
            output_lines.append(f"\n(Showing {len(schedules)} of {response.total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing notification schedules: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_notification_schedule_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_notification_schedule_details tool execution."""
    try:
        schedule_id = arguments["schedule_id"]

        logger.info(f"Getting notification schedule details {schedule_id}")

        schedule = client.get_notification_schedule_details(schedule_id)

        output_lines = [
            f"**Notification Schedule: {schedule.name}** (ID: {schedule.id})\n"
        ]

        if schedule.schedule_type:
            output_lines.append(f"Type: {schedule.schedule_type}")
        if schedule.timezone:
            output_lines.append(f"Timezone: {schedule.timezone}")

        if schedule.intervals:
            output_lines.append(f"\n**Active Intervals** ({len(schedule.intervals)}):")
            for i, interval in enumerate(schedule.intervals[:10], 1):
                if isinstance(interval, dict):
                    day = interval.get("day", interval.get("day_of_week", "Unknown"))
                    start = interval.get("start", interval.get("start_time", "Unknown"))
                    end = interval.get("end", interval.get("end_time", "Unknown"))
                    output_lines.append(f"  {i}. {day}: {start} - {end}")
                else:
                    output_lines.append(f"  {i}. {interval}")

            if len(schedule.intervals) > 10:
                output_lines.append(f"  ... and {len(schedule.intervals) - 10} more")

        if schedule.created:
            output_lines.append(f"\nCreated: {schedule.created.strftime('%Y-%m-%d %H:%M')}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Notification schedule {arguments.get('schedule_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting schedule details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_contact_groups(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_contact_groups tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing contact groups (limit={limit})")

        response = client.list_contact_groups(limit=limit)
        groups = response.contact_group_list

        if not groups:
            return [TextContent(
                type="text",
                text="No contact groups found."
            )]

        output_lines = [
            f"**Contact Groups**\n",
            f"Found {len(groups)} group(s):\n"
        ]

        for group in groups:
            output_lines.append(f"\n**{group.name}** (ID: {group.id})")
            output_lines.append(f"  Contacts: {group.contact_count}")
            if group.notification_schedule:
                output_lines.append(f"  Has notification schedule configured")

        if response.total_count and response.total_count > len(groups):
            output_lines.append(f"\n(Showing {len(groups)} of {response.total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                "Error accessing FortiMonitor endpoint: /v2/contact_group\n\n"
                "This endpoint may not be available in your FortiMonitor version. "
                "You can still use list_contacts to see individual contacts."
            )
        )]
    except APIError as e:
        logger.error(f"API error accessing /v2/contact_group: {e}")
        return [TextContent(
            type="text",
            text=(
                f"Error accessing FortiMonitor endpoint: /v2/contact_group\n\n"
                f"Error details: {str(e)}\n\n"
                f"This endpoint may not be available in your FortiMonitor version. "
                f"You can still use list_contacts to see individual contacts."
            )
        )]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_contact_group_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_contact_group_details tool execution."""
    try:
        group_id = arguments["group_id"]

        logger.info(f"Getting contact group details {group_id}")

        group = client.get_contact_group_details(group_id)

        output_lines = [
            f"**Contact Group: {group.name}** (ID: {group.id})\n"
        ]

        # Show contacts
        output_lines.append(f"Total Contacts: {group.contact_count}")

        if group.contacts:
            output_lines.append("\n**Contact URLs:**")
            for contact_url in group.contacts[:10]:
                output_lines.append(f"  - {contact_url}")
            if len(group.contacts) > 10:
                output_lines.append(f"  ... and {len(group.contacts) - 10} more")

        # Show notification schedule
        if group.notification_schedule:
            output_lines.append(f"\n**Notification Schedule:**")
            output_lines.append(f"  {group.notification_schedule}")

        if group.created:
            output_lines.append(f"\nCreated: {group.created.strftime('%Y-%m-%d %H:%M')}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Contact group {arguments.get('group_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting contact group: {e}")
        return [TextContent(
            type="text",
            text=f"Error accessing /v2/contact_group/{arguments.get('group_id')}: {str(e)}"
        )]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_contacts(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_contacts tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing contacts (limit={limit})")

        response = client.list_contacts(limit=limit)
        contacts = response.contact_list

        if not contacts:
            return [TextContent(
                type="text",
                text="No contacts found."
            )]

        output_lines = [
            f"**Notification Contacts**\n",
            f"Found {len(contacts)} contact(s):\n"
        ]

        for contact in contacts:
            output_lines.append(f"\n**{contact.name}** (ID: {contact.id})")
            if contact.email:
                output_lines.append(f"  Email: {contact.email}")
            if contact.phone:
                output_lines.append(f"  Phone: {contact.phone}")
            if contact.sms:
                output_lines.append(f"  SMS: {contact.sms}")
            if contact.notification_methods:
                methods = ", ".join(contact.notification_methods)
                output_lines.append(f"  Methods: {methods}")

        if response.total_count and response.total_count > len(contacts):
            output_lines.append(f"\n(Showing {len(contacts)} of {response.total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing contacts: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]
