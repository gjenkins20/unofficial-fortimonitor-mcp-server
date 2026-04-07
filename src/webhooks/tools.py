"""
FortiMonitor MCP Tools - Webhook Event Tools

Copyright (c) 2026 Gregori Jenkins
https://github.com/gjenkins20/unofficial-fortimonitor-mcp-server

MCP tools for querying webhook events received by the embedded receiver.
"""

import json
import mcp.types

from .receiver import event_store


# ── Tool Definitions ──────────────────────────────────────────────

WEBHOOK_TOOL_DEFINITIONS = {

    "list_webhook_events": lambda: mcp.types.Tool(
        name="list_webhook_events",
        description=(
            "List recent webhook events received from FortiMonitor. "
            "Events include outage notifications, escalations, and maintenance alerts."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "number",
                    "description": "Maximum number of events to return (default: 25).",
                },
                "event_type": {
                    "type": "string",
                    "description": (
                        "Filter by event type: outage_started, outage_cleared, "
                        "outage_update, escalation, maintenance, unknown."
                    ),
                },
            },
        },
    ),

    "get_webhook_status": lambda: mcp.types.Tool(
        name="get_webhook_status",
        description=(
            "Get the status of the webhook receiver: whether it's running, "
            "total events received, and port configuration."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),

    "clear_webhook_events": lambda: mcp.types.Tool(
        name="clear_webhook_events",
        description="Clear all stored webhook events.",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),

}


# ── Handlers ──────────────────────────────────────────────────────


async def handle_list_webhook_events(arguments: dict, client) -> list:
    limit = int(arguments.get("limit", 25))
    event_type = arguments.get("event_type")

    events = event_store.get_recent(limit=limit, event_type=event_type)

    output = {
        "webhook_events": {
            "count": len(events),
            "total_stored": event_store.count(),
            "events": events,
        }
    }
    return [mcp.types.TextContent(type="text", text=json.dumps(output, indent=2, default=str))]


async def handle_get_webhook_status(arguments: dict, client) -> list:
    # Import here to avoid circular dependency at module load
    from .receiver import WebhookReceiver

    output = {
        "webhook_status": {
            "total_events_stored": event_store.count(),
        }
    }
    return [mcp.types.TextContent(type="text", text=json.dumps(output, indent=2))]


async def handle_clear_webhook_events(arguments: dict, client) -> list:
    count = event_store.count()
    event_store.clear()
    return [mcp.types.TextContent(
        type="text",
        text=f"Cleared {count} webhook events.",
    )]


WEBHOOK_HANDLERS = {
    "list_webhook_events": handle_list_webhook_events,
    "get_webhook_status": handle_get_webhook_status,
    "clear_webhook_events": handle_clear_webhook_events,
}
