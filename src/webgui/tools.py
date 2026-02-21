"""WebGUI knowledge layer MCP tools.

Provides 10 read-only tools for querying crawled FortiMonitor WebGUI data:
page listings, page details, search, screenshots, navigation, page
descriptions, form details, walkthrough listing/retrieval, and screenshot
cropping with element highlighting.
"""

import base64
import io
import json
import logging
from pathlib import Path
from typing import Any, List, Optional

from mcp.types import ImageContent, TextContent, Tool

from .store import SchemaStore
from .workflows import WorkflowStore

logger = logging.getLogger(__name__)

# Module-level store instances (configured during server init)
_store: SchemaStore | None = None
_workflow_store: WorkflowStore | None = None


def configure(
    schema_file: Path,
    screenshots_dir: Path,
    workflows_file: Optional[Path] = None,
) -> None:
    """Configure the WebGUI tools with schema, screenshot, and workflow paths.

    Called during server initialization.
    """
    global _store, _workflow_store
    _store = SchemaStore(schema_file=schema_file, screenshots_dir=screenshots_dir)
    logger.info("WebGUI knowledge layer configured: schema=%s, screenshots=%s",
                schema_file, screenshots_dir)

    if workflows_file and workflows_file.exists():
        _workflow_store = WorkflowStore(
            workflows_file=workflows_file, schema_store=_store
        )
        logger.info("WebGUI workflows configured: %s", workflows_file)
    else:
        _workflow_store = None
        if workflows_file:
            logger.warning("Workflows file not found: %s", workflows_file)


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


def ui_list_walkthroughs_tool_definition() -> Tool:
    return Tool(
        name="ui_list_walkthroughs",
        description=(
            "List available FortiMonitor WebGUI walkthroughs — step-by-step "
            "task guides for common workflows like scheduling maintenance or "
            "investigating incidents. Supports keyword search."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Optional keyword to filter walkthroughs by title, "
                        "description, or tags (e.g. 'maintenance', 'incident')"
                    ),
                },
            },
            "required": [],
        },
    )


def ui_get_walkthrough_tool_definition() -> Tool:
    return Tool(
        name="ui_get_walkthrough",
        description=(
            "Get a specific FortiMonitor WebGUI walkthrough with step-by-step "
            "instructions. Each step includes the page to navigate to, what "
            "to do there, and screenshot paths for visual reference."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "workflow_id": {
                    "type": "string",
                    "description": "Workflow ID from ui_list_walkthroughs",
                },
                "step": {
                    "type": "integer",
                    "description": "Return only a specific step (1-based). Omit for all steps.",
                },
            },
            "required": ["workflow_id"],
        },
    )


def ui_crop_screenshot_tool_definition() -> Tool:
    return Tool(
        name="ui_crop_screenshot",
        description=(
            "Crop and optionally annotate a region of a FortiMonitor WebGUI "
            "page screenshot around a specific UI element. Returns a cropped "
            "PNG image focused on the element. Falls back to the full "
            "screenshot if the element's position is unknown."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "Page ID from the crawl schema",
                },
                "url": {
                    "type": "string",
                    "description": "Full URL of the page (alternative to page_id)",
                },
                "element_id": {
                    "type": "string",
                    "description": (
                        "Element ID to crop around (e.g. 'elem-5'). If omitted "
                        "or if position data is unavailable, the full screenshot "
                        "is returned."
                    ),
                },
                "padding": {
                    "type": "integer",
                    "description": "Pixels of padding around the crop box (default: 20)",
                    "default": 20,
                },
                "annotate": {
                    "type": "boolean",
                    "description": (
                        "Draw a red border around the element within the crop "
                        "(default: false)"
                    ),
                    "default": False,
                },
            },
            "required": [],
        },
    )


# =============================================================================
# Walkthrough & Crop Handlers
# =============================================================================


async def handle_ui_list_walkthroughs(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_list_walkthroughs tool execution."""
    try:
        if _workflow_store is None:
            return [TextContent(
                type="text",
                text="No walkthroughs available — workflow definitions not configured.",
            )]

        query = arguments.get("query")
        result = _workflow_store.list_workflows(query=query)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        logger.exception("Error in ui_list_walkthroughs")
        return [TextContent(type="text", text=f"Error listing walkthroughs: {e}")]


async def handle_ui_get_walkthrough(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_get_walkthrough tool execution."""
    try:
        if _workflow_store is None:
            return [TextContent(
                type="text",
                text="No walkthroughs available — workflow definitions not configured.",
            )]

        workflow_id = arguments.get("workflow_id")
        if not workflow_id:
            return [TextContent(
                type="text",
                text="Error: 'workflow_id' parameter is required",
            )]

        step = arguments.get("step")
        result = _workflow_store.get_workflow(workflow_id=workflow_id, step=step)
        if result is None:
            msg = f"Walkthrough not found: {workflow_id}"
            if step is not None:
                msg += f" (step {step})"
            return [TextContent(type="text", text=msg)]

        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        logger.exception("Error in ui_get_walkthrough")
        return [TextContent(type="text", text=f"Error getting walkthrough: {e}")]


async def handle_ui_crop_screenshot(
    arguments: dict, client: Any
) -> list:
    """Handle ui_crop_screenshot tool execution.

    Returns ImageContent (cropped/full PNG) + TextContent context.
    """
    try:
        store = _get_store()
        url = arguments.get("url")
        page_id = arguments.get("page_id")
        element_id = arguments.get("element_id")
        padding = arguments.get("padding", 20)
        annotate = arguments.get("annotate", False)

        if not url and not page_id:
            return [TextContent(
                type="text",
                text="Error: provide either 'url' or 'page_id' parameter",
            )]

        # Get the screenshot
        screenshot_path = store.get_screenshot_path(url=url, page_id=page_id)
        if screenshot_path is None:
            identifier = url or page_id
            return [TextContent(
                type="text",
                text=f"No screenshot available for: {identifier}",
            )]

        # Try to get element position for cropping
        position = None
        if element_id:
            position = store.get_element_position(
                url=url, page_id=page_id, element_id=element_id
            )

        from PIL import Image, ImageDraw

        img = Image.open(screenshot_path)
        img_width, img_height = img.size
        context_parts = []

        if position:
            # Crop around the element with padding
            x = position["x"]
            y = position["y"]
            w = position["width"]
            h = position["height"]

            left = max(0, x - padding)
            top = max(0, y - padding)
            right = min(img_width, x + w + padding)
            bottom = min(img_height, y + h + padding)

            # If element is entirely off-screen, fall back to full screenshot
            if left >= right or top >= bottom:
                position = None  # triggers the fallback path below

        if position:
            cropped = img.crop((left, top, right, bottom))

            if annotate:
                draw = ImageDraw.Draw(cropped)
                # Element position within the crop
                elem_left = x - left
                elem_top = y - top
                elem_right = elem_left + w
                elem_bottom = elem_top + h
                for offset in range(3):
                    draw.rectangle(
                        [
                            elem_left - offset,
                            elem_top - offset,
                            elem_right + offset,
                            elem_bottom + offset,
                        ],
                        outline="red",
                    )

            # Encode cropped image
            buf = io.BytesIO()
            cropped.save(buf, format="PNG")
            image_data = base64.b64encode(buf.getvalue()).decode("utf-8")

            context_parts.append(
                f"Cropped screenshot around element '{element_id}' "
                f"(position: x={x}, y={y}, {w}x{h}px, padding={padding}px)"
            )
        else:
            # Return full screenshot
            with open(screenshot_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            if element_id:
                context_parts.append(
                    f"Full screenshot returned — element '{element_id}' "
                    f"position data is not available. Look for the element "
                    f"manually in the screenshot."
                )
            else:
                context_parts.append("Full page screenshot (no element_id specified)")

        # Add page context
        page = store.get_page(url=url, page_id=page_id)
        if page:
            context_parts.append(
                f"Page: {page.get('title', 'Unknown')} ({page.get('url', '')})"
            )

        return [
            ImageContent(type="image", data=image_data, mimeType="image/png"),
            TextContent(type="text", text="\n".join(context_parts)),
        ]
    except Exception as e:
        logger.exception("Error in ui_crop_screenshot")
        return [TextContent(type="text", text=f"Error cropping screenshot: {e}")]


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
    "ui_list_walkthroughs": ui_list_walkthroughs_tool_definition,
    "ui_get_walkthrough": ui_get_walkthrough_tool_definition,
    "ui_crop_screenshot": ui_crop_screenshot_tool_definition,
}

WEBGUI_HANDLERS = {
    "ui_list_pages": handle_ui_list_pages,
    "ui_get_page": handle_ui_get_page,
    "ui_search": handle_ui_search,
    "ui_get_screenshot": handle_ui_get_screenshot,
    "ui_get_navigation": handle_ui_get_navigation,
    "ui_describe_page": handle_ui_describe_page,
    "ui_get_form": handle_ui_get_form,
    "ui_list_walkthroughs": handle_ui_list_walkthroughs,
    "ui_get_walkthrough": handle_ui_get_walkthrough,
    "ui_crop_screenshot": handle_ui_crop_screenshot,
}
