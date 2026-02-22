"""Standalone MCP server for FortiMonitor WebGUI knowledge tools.

Exposes the 10 WebGUI tools (page listings, search, screenshots, navigation,
walkthroughs, cropping) as an independent MCP server.  No FortiMonitor API
client is needed — all data comes from static crawl artifacts.

Configuration via environment variables (with defaults matching the main
server's former config):

    WEBGUI_SCHEMA_FILE      — path to crawl schema JSON
    WEBGUI_SCREENSHOTS_DIR  — directory containing page screenshots
    WEBGUI_WORKFLOWS_FILE   — path to workflow definitions YAML
    LOG_LEVEL               — logging level (default: INFO)
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, List

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import ServerCapabilities, TextContent, Tool, ToolsCapability

from .tools import (
    WEBGUI_HANDLERS,
    WEBGUI_TOOL_DEFINITIONS,
    configure as configure_webgui,
)

_SERVER_NAME = "fortimonitor-webgui"
_SERVER_VERSION = "1.0.0"

# Defaults mirror the values formerly in src/config.py
_DEFAULT_SCHEMA_FILE = "data/schemas/crawl-31e23c1bfdd1.json"
_DEFAULT_SCREENSHOTS_DIR = "data/crawl-31e23c1bfdd1"
_DEFAULT_WORKFLOWS_FILE = "data/workflows.yaml"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool registry (built once at module level)
# ---------------------------------------------------------------------------

def _build_registry():
    """Build tool definitions and handler map from the WebGUI module."""
    tool_definitions: List[Tool] = []
    handler_map = {}

    for name, defn_func in WEBGUI_TOOL_DEFINITIONS.items():
        tool = defn_func()
        tool_definitions.append(tool)
        handler_map[name] = WEBGUI_HANDLERS[name]

    return tool_definitions, handler_map


_TOOL_DEFINITIONS, _HANDLER_MAP = _build_registry()


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

class WebGUIMCPServer:
    """Standalone MCP server for FortiMonitor WebGUI knowledge tools."""

    def __init__(self):
        self.server = Server(_SERVER_NAME)
        self._setup_handlers()
        self._configure_stores()

        logger.info(
            "Initialized %s v%s with %d tools",
            _SERVER_NAME,
            _SERVER_VERSION,
            len(_TOOL_DEFINITIONS),
        )

    def _configure_stores(self):
        """Load schema / screenshot / workflow paths from environment."""
        schema_file = Path(
            os.environ.get("WEBGUI_SCHEMA_FILE", _DEFAULT_SCHEMA_FILE)
        )
        screenshots_dir = Path(
            os.environ.get("WEBGUI_SCREENSHOTS_DIR", _DEFAULT_SCREENSHOTS_DIR)
        )
        workflows_file = Path(
            os.environ.get("WEBGUI_WORKFLOWS_FILE", _DEFAULT_WORKFLOWS_FILE)
        )

        if schema_file.exists():
            configure_webgui(
                schema_file=schema_file,
                screenshots_dir=screenshots_dir,
                workflows_file=workflows_file,
            )
        else:
            logger.warning(
                "WebGUI schema file not found at %s — tools will return "
                "errors until the schema is available.",
                schema_file,
            )

    def _setup_handlers(self):
        """Register MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return _TOOL_DEFINITIONS

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list:
            logger.info("Tool called: %s", name)

            handler = _HANDLER_MAP.get(name)
            if handler:
                # WebGUI tools never use the FortiMonitor client
                return await handler(arguments, None)

            raise ValueError(f"Unknown tool: {name}")

    async def run(self):
        """Run the MCP server over stdio."""
        logger.info("Starting %s MCP server...", _SERVER_NAME)

        try:
            async with stdio_server() as (read_stream, write_stream):
                capabilities = ServerCapabilities(
                    tools=ToolsCapability(listChanged=False)
                )
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=_SERVER_NAME,
                        server_version=_SERVER_VERSION,
                        capabilities=capabilities,
                    ),
                )
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception:
            logger.exception("Server error")
            raise
        finally:
            logger.info("%s MCP server stopped", _SERVER_NAME)


def main():
    """Entry point for the fortimonitor-webgui console script."""
    server = WebGUIMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
