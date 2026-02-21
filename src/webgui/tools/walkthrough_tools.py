"""MCP tool for generating step-by-step walkthroughs.

Tool: ui_generate_walkthrough
"""

import logging
from typing import Any, List

from mcp.types import TextContent, Tool

from ..models import WalkthroughType
from ..schema.store import SchemaStore
from ..walkthrough.formatters import format_html, format_markdown
from ..walkthrough.generator import generate_walkthrough

logger = logging.getLogger(__name__)


# =============================================================================
# Tool Definition
# =============================================================================


def ui_generate_walkthrough_tool_definition() -> Tool:
    """Return tool definition for ui_generate_walkthrough."""
    return Tool(
        name="ui_generate_walkthrough",
        description=(
            "Generate step-by-step walkthrough instructions from a UI schema. "
            "Supports four types: navigation (how to reach a page), task (how to accomplish "
            "something), section (guide to all elements on a page), and flow (playback of a "
            "recorded user flow). Returns formatted Markdown or HTML."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": (
                        "What to generate a walkthrough for. Meaning depends on walkthrough_type: "
                        "navigation/section = page URL, task = task description, flow = flow_id."
                    ),
                },
                "walkthrough_type": {
                    "type": "string",
                    "enum": ["navigation", "task", "section", "flow"],
                    "description": "Type of walkthrough to generate (default: navigation)",
                    "default": "navigation",
                },
                "output_format": {
                    "type": "string",
                    "enum": ["markdown", "html"],
                    "description": "Output format (default: markdown)",
                    "default": "markdown",
                },
                "include_screenshots": {
                    "type": "boolean",
                    "description": "Include screenshot references in output (default true)",
                    "default": True,
                },
                "crawl_id": {
                    "type": "string",
                    "description": "Crawl ID to generate from. If omitted, uses the latest crawl.",
                },
            },
            "required": ["target"],
        },
    )


# =============================================================================
# Handler
# =============================================================================


async def handle_ui_generate_walkthrough(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_generate_walkthrough tool execution."""
    try:
        target = arguments["target"]
        wt_type_str = arguments.get("walkthrough_type", "navigation")
        output_format = arguments.get("output_format", "markdown")
        include_screenshots = arguments.get("include_screenshots", True)
        crawl_id = arguments.get("crawl_id")

        store = SchemaStore()

        if not crawl_id:
            crawl_id = store.get_latest_crawl_id()
            if not crawl_id:
                return [TextContent(
                    type="text",
                    text="No crawls found. Run ui_crawl_start first.",
                )]

        schema = store.load(crawl_id)
        if not schema:
            return [TextContent(type="text", text=f"Schema not found for crawl: {crawl_id}")]

        wt_type = WalkthroughType(wt_type_str)
        walkthrough = generate_walkthrough(schema, target, wt_type)

        if output_format == "html":
            output = format_html(walkthrough, include_screenshots=include_screenshots)
        else:
            output = format_markdown(walkthrough, include_screenshots=include_screenshots)

        return [TextContent(type="text", text=output)]

    except Exception as e:
        logger.exception("Error generating walkthrough")
        return [TextContent(type="text", text=f"Error generating walkthrough: {e}")]


# =============================================================================
# Module Registration (dict pattern)
# =============================================================================

WEBGUI_WALKTHROUGH_TOOL_DEFINITIONS = {
    "ui_generate_walkthrough": ui_generate_walkthrough_tool_definition,
}

WEBGUI_WALKTHROUGH_HANDLERS = {
    "ui_generate_walkthrough": handle_ui_generate_walkthrough,
}
