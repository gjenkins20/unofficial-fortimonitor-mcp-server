"""MCP tools for starting and monitoring UI crawls.

Tools: ui_crawl_start, ui_crawl_status
"""

import asyncio
import logging
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from ..crawler.engine import CrawlEngine
from ..crawler.state import CrawlState
from ..schema.store import SchemaStore

logger = logging.getLogger(__name__)

# Track running crawls (crawl_id -> asyncio.Task)
_active_crawls: Dict[str, asyncio.Task] = {}
_crawl_engines: Dict[str, CrawlEngine] = {}


# =============================================================================
# Tool Definitions
# =============================================================================


def ui_crawl_start_tool_definition() -> Tool:
    """Return tool definition for ui_crawl_start."""
    return Tool(
        name="ui_crawl_start",
        description=(
            "Start an authenticated BFS crawl of a web application. "
            "Discovers pages, extracts interactive elements (buttons, forms, modals, links), "
            "captures screenshots, and builds a structured UI schema. "
            "The crawl runs in the background — use ui_crawl_status to check progress."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "target_url": {
                    "type": "string",
                    "description": "Base URL of the web application to crawl",
                },
                "username": {
                    "type": "string",
                    "description": "Login username or email",
                },
                "password": {
                    "type": "string",
                    "description": "Login password",
                },
                "application_name": {
                    "type": "string",
                    "description": "Name of the application (for labeling). Default: ''",
                    "default": "",
                },
                "max_pages": {
                    "type": "integer",
                    "description": "Maximum number of pages to crawl (default 100)",
                    "default": 100,
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum BFS depth from the start page (default 5)",
                    "default": 5,
                },
                "crawl_delay": {
                    "type": "number",
                    "description": "Delay in seconds between page loads (default 1.0)",
                    "default": 1.0,
                },
                "login_url": {
                    "type": "string",
                    "description": "Login page URL. Defaults to target_url if not specified.",
                },
                "screenshot_enabled": {
                    "type": "boolean",
                    "description": "Capture page screenshots during crawl (default true)",
                    "default": True,
                },
            },
            "required": ["target_url", "username", "password"],
        },
    )


def ui_crawl_status_tool_definition() -> Tool:
    """Return tool definition for ui_crawl_status."""
    return Tool(
        name="ui_crawl_status",
        description=(
            "Check the progress of a UI crawl. Shows status, pages discovered/crawled/remaining, "
            "current page, and any errors. If no crawl_id is provided, shows the latest crawl."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "crawl_id": {
                    "type": "string",
                    "description": "Crawl ID to check. If omitted, shows the latest crawl.",
                },
            },
        },
    )


# =============================================================================
# Handlers
# =============================================================================


async def handle_ui_crawl_start(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_crawl_start tool execution."""
    try:
        target_url = arguments["target_url"]
        username = arguments["username"]
        password = arguments["password"]
        application_name = arguments.get("application_name", "")
        max_pages = arguments.get("max_pages", 100)
        max_depth = arguments.get("max_depth", 5)
        crawl_delay = arguments.get("crawl_delay", 1.0)
        login_url = arguments.get("login_url")
        screenshot_enabled = arguments.get("screenshot_enabled", True)

        engine = CrawlEngine(
            target_url=target_url,
            username=username,
            password=password,
            application_name=application_name,
            max_pages=max_pages,
            max_depth=max_depth,
            crawl_delay=crawl_delay,
            login_url=login_url,
            screenshot_enabled=screenshot_enabled,
        )

        crawl_id = engine.crawl_id

        async def _run_crawl():
            try:
                schema = await engine.crawl()
                store = SchemaStore()
                store.save(schema)
                logger.info(f"Crawl {crawl_id} completed and saved")
            except Exception as e:
                logger.exception(f"Crawl {crawl_id} failed: {e}")
            finally:
                _active_crawls.pop(crawl_id, None)
                _crawl_engines.pop(crawl_id, None)

        task = asyncio.create_task(_run_crawl())
        _active_crawls[crawl_id] = task
        _crawl_engines[crawl_id] = engine

        output = (
            f"**Crawl Started**\n\n"
            f"**Crawl ID:** {crawl_id}\n"
            f"**Target:** {target_url}\n"
            f"**Application:** {application_name or 'N/A'}\n"
            f"**Max Pages:** {max_pages}\n"
            f"**Max Depth:** {max_depth}\n"
            f"**Screenshots:** {'Enabled' if screenshot_enabled else 'Disabled'}\n\n"
            f"Use `ui_crawl_status` with crawl_id `{crawl_id}` to check progress."
        )
        return [TextContent(type="text", text=output)]

    except Exception as e:
        logger.exception("Error starting UI crawl")
        return [TextContent(type="text", text=f"Error starting crawl: {e}")]


async def handle_ui_crawl_status(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_crawl_status tool execution."""
    try:
        crawl_id = arguments.get("crawl_id")

        # If crawl is active, get live progress
        if crawl_id and crawl_id in _crawl_engines:
            progress = _crawl_engines[crawl_id].get_progress()
            output = (
                f"**Crawl Status (Live)**\n\n"
                f"**Crawl ID:** {progress['crawl_id']}\n"
                f"**Status:** {progress['status']}\n"
                f"**Pages Discovered:** {progress['pages_discovered']}\n"
                f"**Pages Crawled:** {progress['pages_crawled']}\n"
                f"**Pages Remaining:** {progress['pages_remaining']}\n"
            )
            if progress.get("errors"):
                output += f"\n**Errors ({len(progress['errors'])}):**\n"
                for err in progress["errors"][:10]:
                    output += f"- {err}\n"
            return [TextContent(type="text", text=output)]

        # Check persisted state
        state = CrawlState()
        if not crawl_id:
            crawls = state.list_crawls()
            if not crawls:
                return [TextContent(type="text", text="No crawls found.")]
            crawl_id = crawls[0]["crawl_id"]

        progress = state.get_progress(crawl_id)
        if not progress:
            return [TextContent(type="text", text=f"No crawl found with ID: {crawl_id}")]

        output = (
            f"**Crawl Status**\n\n"
            f"**Crawl ID:** {progress.crawl_id}\n"
            f"**Status:** {progress.status.value}\n"
            f"**Pages Discovered:** {progress.pages_discovered}\n"
            f"**Pages Crawled:** {progress.pages_crawled}\n"
            f"**Pages Remaining:** {progress.pages_remaining}\n"
        )
        if progress.current_page:
            output += f"**Current Page:** {progress.current_page}\n"
        if progress.errors:
            output += f"\n**Errors ({len(progress.errors)}):**\n"
            for err in progress.errors[:10]:
                output += f"- {err}\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        logger.exception("Error checking crawl status")
        return [TextContent(type="text", text=f"Error checking status: {e}")]


# =============================================================================
# Module Registration (dict pattern)
# =============================================================================

WEBGUI_CRAWL_TOOL_DEFINITIONS = {
    "ui_crawl_start": ui_crawl_start_tool_definition,
    "ui_crawl_status": ui_crawl_status_tool_definition,
}

WEBGUI_CRAWL_HANDLERS = {
    "ui_crawl_start": handle_ui_crawl_start,
    "ui_crawl_status": handle_ui_crawl_status,
}
