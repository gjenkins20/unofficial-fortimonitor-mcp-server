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
                get_servers_tool_definition(),
                get_server_details_tool_definition(),
                get_outages_tool_definition(),
                get_server_metrics_tool_definition(),
                check_server_health_tool_definition(),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> List[TextContent]:
            """Handle tool execution requests."""
            logger.info(f"Tool called: {name}")

            # Ensure client is initialized
            if not self.client:
                self.client = FortiMonitorClient()

            # Route to appropriate handler
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
