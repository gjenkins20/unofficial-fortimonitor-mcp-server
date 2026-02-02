"""MCP tools for FortiMonitor operations."""

from .servers import (
    get_servers_tool_definition,
    handle_get_servers,
    get_server_details_tool_definition,
    handle_get_server_details,
)
from .outages import get_outages_tool_definition, handle_get_outages
from .metrics import get_server_metrics_tool_definition, handle_get_server_metrics

__all__ = [
    "get_servers_tool_definition",
    "handle_get_servers",
    "get_server_details_tool_definition",
    "handle_get_server_details",
    "get_outages_tool_definition",
    "handle_get_outages",
    "get_server_metrics_tool_definition",
    "handle_get_server_metrics",
]
