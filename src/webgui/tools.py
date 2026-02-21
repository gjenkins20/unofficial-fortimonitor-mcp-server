"""WebGUI knowledge layer MCP tools.

Provides 7 read-only tools for querying crawled FortiMonitor WebGUI data:
page listings, page details, search, screenshots, navigation, page
descriptions, and form details.
"""

import base64
import json
import logging
from pathlib import Path
from typing import Any, List

from mcp.types import ImageContent, TextContent, Tool

from .store import SchemaStore

logger = logging.getLogger(__name__)

# Module-level store instance (configured during server init)
_store: SchemaStore | None = None


def configure(schema_file: Path, screenshots_dir: Path) -> None:
    """Configure the WebGUI tools with schema and screenshot paths.

    Called during server initialization.
    """
    global _store
    _store = SchemaStore(schema_file=schema_file, screenshots_dir=screenshots_dir)
    logger.info("WebGUI knowledge layer configured: schema=%s, screenshots=%s",
                schema_file, screenshots_dir)


def _get_store() -> SchemaStore:
    """Get the configured store, raising a clear error if not configured."""
    if _store is None:
        raise RuntimeError(
            "WebGUI knowledge layer not configured. "
            "Ensure the schema file exists at the configured path."
        )
    return _store


# =============================================================================
# Tool Definitions
# =============================================================================


def ui_list_pages_tool_definition() -> Tool:
    return Tool(
        name="ui_list_pages",
        description=(
            "List crawled FortiMonitor WebGUI pages. Returns page summaries "
            "including URL, title, and counts of forms/modals/elements. "
            "Supports filtering by URL category and pagination."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": (
                        "Filter by URL path category (e.g. 'report', 'application', "
                        "'incidents'). Omit to list all pages."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "description": "Max pages to return (default: 50, max: 200)",
                    "default": 50,
                },
                "offset": {
                    "type": "integer",
                    "description": "Pagination offset (default: 0)",
                    "default": 0,
                },
            },
            "required": [],
        },
    )


def ui_get_page_tool_definition() -> Tool:
    return Tool(
        name="ui_get_page",
        description=(
            "Get full details for a specific FortiMonitor WebGUI page including "
            "sections, forms, modals, and navigation links. Provide either "
            "the page URL or page_id."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Full URL of the page (e.g. 'https://my.us01.fortimonitor.com/incidents')",
                },
                "page_id": {
                    "type": "string",
                    "description": "Page ID from the crawl schema (e.g. 'incidents')",
                },
                "include_elements": {
                    "type": "boolean",
                    "description": "Include individual UI element details (default: false, can be large)",
                    "default": False,
                },
            },
            "required": [],
        },
    )


def ui_search_tool_definition() -> Tool:
    return Tool(
        name="ui_search",
        description=(
            "Search FortiMonitor WebGUI pages by element labels, form fields, "
            "page titles, or modal titles. Returns matching pages ranked by "
            "relevance with match type indicators."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Search terms, e.g. 'notification schedule' or 'server group'"
                    ),
                },
                "search_in": {
                    "type": "string",
                    "enum": ["titles", "elements", "forms", "modals"],
                    "description": (
                        "Restrict search to a specific index. Omit to search all."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default: 20)",
                    "default": 20,
                },
            },
            "required": ["query"],
        },
    )


def ui_get_screenshot_tool_definition() -> Tool:
    return Tool(
        name="ui_get_screenshot",
        description=(
            "Retrieve a screenshot of a FortiMonitor WebGUI page as a base64-encoded "
            "PNG image. Provides visual context for understanding page layout."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Full URL of the page",
                },
                "page_id": {
                    "type": "string",
                    "description": "Page ID from the crawl schema",
                },
            },
            "required": [],
        },
    )


def ui_get_navigation_tool_definition() -> Tool:
    return Tool(
        name="ui_get_navigation",
        description=(
            "Get the FortiMonitor WebGUI navigation tree showing how pages "
            "are organized by URL path hierarchy."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth of the navigation tree (default: 3)",
                    "default": 3,
                },
            },
            "required": [],
        },
    )


def ui_describe_page_tool_definition() -> Tool:
    return Tool(
        name="ui_describe_page",
        description=(
            "Generate a human-readable markdown description of a FortiMonitor "
            "WebGUI page including its sections, forms, modals, and navigation "
            "links. Good for understanding what a page does without viewing "
            "raw schema data."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Full URL of the page",
                },
                "page_id": {
                    "type": "string",
                    "description": "Page ID from the crawl schema",
                },
            },
            "required": [],
        },
    )


def ui_get_form_tool_definition() -> Tool:
    return Tool(
        name="ui_get_form",
        description=(
            "Get detailed form information for a FortiMonitor WebGUI page, "
            "including field names, types, required status, and options. "
            "Returns forms from both the page and its modals."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Full URL of the page",
                },
                "page_id": {
                    "type": "string",
                    "description": "Page ID from the crawl schema",
                },
                "form_id": {
                    "type": "string",
                    "description": "Specific form ID to retrieve (omit for all forms on the page)",
                },
            },
            "required": [],
        },
    )


# =============================================================================
# Tool Handlers
# =============================================================================


async def handle_ui_list_pages(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_list_pages tool execution."""
    try:
        store = _get_store()
        category = arguments.get("category")
        limit = min(arguments.get("limit", 50), 200)
        offset = arguments.get("offset", 0)

        result = store.list_pages(category=category, limit=limit, offset=offset)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        logger.exception("Error in ui_list_pages")
        return [TextContent(type="text", text=f"Error listing pages: {e}")]


async def handle_ui_get_page(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_get_page tool execution."""
    try:
        store = _get_store()
        url = arguments.get("url")
        page_id = arguments.get("page_id")
        include_elements = arguments.get("include_elements", False)

        if not url and not page_id:
            return [TextContent(
                type="text",
                text="Error: provide either 'url' or 'page_id' parameter",
            )]

        result = store.get_page(
            url=url, page_id=page_id, include_elements=include_elements
        )
        if result is None:
            identifier = url or page_id
            return [TextContent(
                type="text",
                text=f"Page not found: {identifier}",
            )]

        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        logger.exception("Error in ui_get_page")
        return [TextContent(type="text", text=f"Error getting page: {e}")]


async def handle_ui_search(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_search tool execution."""
    try:
        store = _get_store()
        query = arguments.get("query", "")
        search_in = arguments.get("search_in")
        limit = min(arguments.get("limit", 20), 100)

        if not query:
            return [TextContent(
                type="text",
                text="Error: 'query' parameter is required",
            )]

        result = store.search(query=query, search_in=search_in, limit=limit)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        logger.exception("Error in ui_search")
        return [TextContent(type="text", text=f"Error searching: {e}")]


async def handle_ui_get_screenshot(
    arguments: dict, client: Any
) -> list:
    """Handle ui_get_screenshot tool execution.

    Returns both ImageContent (base64 PNG) and TextContent (context).
    """
    try:
        store = _get_store()
        url = arguments.get("url")
        page_id = arguments.get("page_id")

        if not url and not page_id:
            return [TextContent(
                type="text",
                text="Error: provide either 'url' or 'page_id' parameter",
            )]

        screenshot_path = store.get_screenshot_path(url=url, page_id=page_id)
        if screenshot_path is None:
            identifier = url or page_id
            return [TextContent(
                type="text",
                text=f"No screenshot available for: {identifier}",
            )]

        # Read and encode the screenshot
        with open(screenshot_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # Get page context
        page = store.get_page(url=url, page_id=page_id)
        context = ""
        if page:
            context = f"Screenshot of: {page.get('title', 'Unknown')} ({page.get('url', '')})"

        return [
            ImageContent(type="image", data=image_data, mimeType="image/png"),
            TextContent(type="text", text=context),
        ]
    except Exception as e:
        logger.exception("Error in ui_get_screenshot")
        return [TextContent(type="text", text=f"Error getting screenshot: {e}")]


async def handle_ui_get_navigation(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_get_navigation tool execution."""
    try:
        store = _get_store()
        max_depth = min(arguments.get("max_depth", 3), 10)

        result = store.get_navigation_tree(max_depth=max_depth)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        logger.exception("Error in ui_get_navigation")
        return [TextContent(type="text", text=f"Error getting navigation: {e}")]


async def handle_ui_describe_page(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_describe_page tool execution."""
    try:
        store = _get_store()
        url = arguments.get("url")
        page_id = arguments.get("page_id")

        if not url and not page_id:
            return [TextContent(
                type="text",
                text="Error: provide either 'url' or 'page_id' parameter",
            )]

        description = store.describe_page(url=url, page_id=page_id)
        if description is None:
            identifier = url or page_id
            return [TextContent(
                type="text",
                text=f"Page not found: {identifier}",
            )]

        return [TextContent(type="text", text=description)]
    except Exception as e:
        logger.exception("Error in ui_describe_page")
        return [TextContent(type="text", text=f"Error describing page: {e}")]


async def handle_ui_get_form(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_get_form tool execution."""
    try:
        store = _get_store()
        url = arguments.get("url")
        page_id = arguments.get("page_id")
        form_id = arguments.get("form_id")

        if not url and not page_id:
            return [TextContent(
                type="text",
                text="Error: provide either 'url' or 'page_id' parameter",
            )]

        result = store.get_forms(url=url, page_id=page_id, form_id=form_id)
        if result is None:
            identifier = url or page_id
            return [TextContent(
                type="text",
                text=f"Page not found: {identifier}",
            )]

        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        logger.exception("Error in ui_get_form")
        return [TextContent(type="text", text=f"Error getting forms: {e}")]


# =============================================================================
# Module Registration (dict pattern)
# =============================================================================

WEBGUI_TOOL_DEFINITIONS = {
    "ui_list_pages": ui_list_pages_tool_definition,
    "ui_get_page": ui_get_page_tool_definition,
    "ui_search": ui_search_tool_definition,
    "ui_get_screenshot": ui_get_screenshot_tool_definition,
    "ui_get_navigation": ui_get_navigation_tool_definition,
    "ui_describe_page": ui_describe_page_tool_definition,
    "ui_get_form": ui_get_form_tool_definition,
}

WEBGUI_HANDLERS = {
    "ui_list_pages": handle_ui_list_pages,
    "ui_get_page": handle_ui_get_page,
    "ui_search": handle_ui_search,
    "ui_get_screenshot": handle_ui_get_screenshot,
    "ui_get_navigation": handle_ui_get_navigation,
    "ui_describe_page": handle_ui_describe_page,
    "ui_get_form": handle_ui_get_form,
}
