"""Main MCP server implementation for FortiMonitor."""

import logging
import asyncio
from typing import Any, List

from mcp.server.models import InitializationOptions
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool, ServerCapabilities, ToolsCapability

from .config import get_settings
from .fortimonitor.client import FortiMonitorClient
from .tools.servers import (
    get_servers_tool_definition,
    handle_get_servers,
    get_server_details_tool_definition,
    handle_get_server_details,
)
from .tools.outages import (
    get_outages_tool_definition,
    handle_get_outages,
    check_server_health_tool_definition,
    handle_check_server_health,
)
from .tools.metrics import (
    get_server_metrics_tool_definition,
    handle_get_server_metrics,
)
from .tools.outage_management import (
    acknowledge_outage_tool_definition,
    handle_acknowledge_outage,
    add_outage_note_tool_definition,
    handle_add_outage_note,
    get_outage_details_tool_definition,
    handle_get_outage_details,
)
from .tools.server_management import (
    set_server_status_tool_definition,
    handle_set_server_status,
    create_maintenance_window_tool_definition,
    handle_create_maintenance_window,
    list_maintenance_windows_tool_definition,
    handle_list_maintenance_windows,
)
from .tools.bulk_operations import (
    bulk_acknowledge_outages_tool_definition,
    handle_bulk_acknowledge_outages,
    bulk_add_tags_tool_definition,
    handle_bulk_add_tags,
    bulk_remove_tags_tool_definition,
    handle_bulk_remove_tags,
    search_servers_advanced_tool_definition,
    handle_search_servers_advanced,
    get_servers_with_active_outages_tool_definition,
    handle_get_servers_with_active_outages,
)
from .tools.server_groups import (
    list_server_groups_tool_definition,
    handle_list_server_groups,
    get_server_group_details_tool_definition,
    handle_get_server_group_details,
    create_server_group_tool_definition,
    handle_create_server_group,
    add_servers_to_group_tool_definition,
    handle_add_servers_to_group,
    remove_servers_from_group_tool_definition,
    handle_remove_servers_from_group,
    delete_server_group_tool_definition,
    handle_delete_server_group,
)
from .tools.templates import (
    list_server_templates_tool_definition,
    handle_list_server_templates,
    get_server_template_details_tool_definition,
    handle_get_server_template_details,
    apply_template_to_server_tool_definition,
    handle_apply_template_to_server,
    apply_template_to_group_tool_definition,
    handle_apply_template_to_group,
)

# Get settings
_settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, _settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class FortiMonitorMCPServer:
    """MCP Server for FortiMonitor integration."""

    def __init__(self):
        """Initialize the FortiMonitor MCP server."""
        self.server = Server(_settings.mcp_server_name)
        self.client: FortiMonitorClient = None
        self._setup_handlers()

        logger.info(
            f"Initialized {_settings.mcp_server_name} v{_settings.mcp_server_version}"
        )

    def _setup_handlers(self):
        """Set up MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                # Phase 1 tools
                get_servers_tool_definition(),
                get_server_details_tool_definition(),
                get_outages_tool_definition(),
                get_server_metrics_tool_definition(),
                check_server_health_tool_definition(),
                # Phase 2 Priority 1 tools
                acknowledge_outage_tool_definition(),
                add_outage_note_tool_definition(),
                get_outage_details_tool_definition(),
                set_server_status_tool_definition(),
                create_maintenance_window_tool_definition(),
                list_maintenance_windows_tool_definition(),
                # Phase 2 Priority 2 tools
                bulk_acknowledge_outages_tool_definition(),
                bulk_add_tags_tool_definition(),
                bulk_remove_tags_tool_definition(),
                search_servers_advanced_tool_definition(),
                get_servers_with_active_outages_tool_definition(),
                # Phase 2 Priority 3 tools - Server Groups
                list_server_groups_tool_definition(),
                get_server_group_details_tool_definition(),
                create_server_group_tool_definition(),
                add_servers_to_group_tool_definition(),
                remove_servers_from_group_tool_definition(),
                delete_server_group_tool_definition(),
                # Phase 2 Priority 3 tools - Templates
                list_server_templates_tool_definition(),
                get_server_template_details_tool_definition(),
                apply_template_to_server_tool_definition(),
                apply_template_to_group_tool_definition(),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> List[TextContent]:
            """Handle tool execution requests."""
            logger.info(f"Tool called: {name}")

            # Ensure client is initialized
            if not self.client:
                self.client = FortiMonitorClient()

            # Route to appropriate handler
            # Phase 1 tools
            if name == "get_servers":
                return await handle_get_servers(arguments, self.client)
            elif name == "get_server_details":
                return await handle_get_server_details(arguments, self.client)
            elif name == "get_outages":
                return await handle_get_outages(arguments, self.client)
            elif name == "get_server_metrics":
                return await handle_get_server_metrics(arguments, self.client)
            elif name == "check_server_health":
                return await handle_check_server_health(arguments, self.client)
            # Phase 2 Priority 1 tools
            elif name == "acknowledge_outage":
                return await handle_acknowledge_outage(arguments, self.client)
            elif name == "add_outage_note":
                return await handle_add_outage_note(arguments, self.client)
            elif name == "get_outage_details":
                return await handle_get_outage_details(arguments, self.client)
            elif name == "set_server_status":
                return await handle_set_server_status(arguments, self.client)
            elif name == "create_maintenance_window":
                return await handle_create_maintenance_window(arguments, self.client)
            elif name == "list_maintenance_windows":
                return await handle_list_maintenance_windows(arguments, self.client)
            # Phase 2 Priority 2 tools
            elif name == "bulk_acknowledge_outages":
                return await handle_bulk_acknowledge_outages(arguments, self.client)
            elif name == "bulk_add_tags":
                return await handle_bulk_add_tags(arguments, self.client)
            elif name == "bulk_remove_tags":
                return await handle_bulk_remove_tags(arguments, self.client)
            elif name == "search_servers_advanced":
                return await handle_search_servers_advanced(arguments, self.client)
            elif name == "get_servers_with_active_outages":
                return await handle_get_servers_with_active_outages(arguments, self.client)
            # Phase 2 Priority 3 tools - Server Groups
            elif name == "list_server_groups":
                return await handle_list_server_groups(arguments, self.client)
            elif name == "get_server_group_details":
                return await handle_get_server_group_details(arguments, self.client)
            elif name == "create_server_group":
                return await handle_create_server_group(arguments, self.client)
            elif name == "add_servers_to_group":
                return await handle_add_servers_to_group(arguments, self.client)
            elif name == "remove_servers_from_group":
                return await handle_remove_servers_from_group(arguments, self.client)
            elif name == "delete_server_group":
                return await handle_delete_server_group(arguments, self.client)
            # Phase 2 Priority 3 tools - Templates
            elif name == "list_server_templates":
                return await handle_list_server_templates(arguments, self.client)
            elif name == "get_server_template_details":
                return await handle_get_server_template_details(arguments, self.client)
            elif name == "apply_template_to_server":
                return await handle_apply_template_to_server(arguments, self.client)
            elif name == "apply_template_to_group":
                return await handle_apply_template_to_group(arguments, self.client)
            else:
                raise ValueError(f"Unknown tool: {name}")

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting FortiMonitor MCP server...")

        try:
            async with stdio_server() as (read_stream, write_stream):
                # Create capabilities using proper MCP types
                capabilities = ServerCapabilities(
                    tools=ToolsCapability(listChanged=False)
                )

                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=_settings.mcp_server_name,
                        server_version=_settings.mcp_server_version,
                        capabilities=capabilities,
                    ),
                )
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.exception("Server error")
            raise
        finally:
            if self.client:
                self.client.close()
            logger.info("FortiMonitor MCP server stopped")


def main():
    """Main entry point."""
    server = FortiMonitorMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
