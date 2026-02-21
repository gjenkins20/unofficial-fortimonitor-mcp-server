"""MCP tools for querying and comparing UI schemas.

Tools: ui_schema_list_pages, ui_schema_get_page, ui_schema_search,
       ui_schema_compare, ui_screenshot_get
"""

import json
import logging
from typing import Any, List

from mcp.types import TextContent, Tool

from ..crawler.screenshots import ScreenshotManager
from ..schema.differ import compare_schemas
from ..schema.store import SchemaStore
from ..models import DiffScope

logger = logging.getLogger(__name__)


# =============================================================================
# Tool Definitions
# =============================================================================


def ui_schema_list_pages_tool_definition() -> Tool:
    """Return tool definition for ui_schema_list_pages."""
    return Tool(
        name="ui_schema_list_pages",
        description=(
            "List all discovered pages from a UI crawl with URLs, titles, element counts, "
            "and breadcrumbs. Optionally filter by substring match."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "crawl_id": {
                    "type": "string",
                    "description": "Crawl ID to query. If omitted, uses the latest crawl.",
                },
                "filter": {
                    "type": "string",
                    "description": "Optional substring to filter pages by URL, title, or breadcrumb.",
                },
            },
        },
    )


def ui_schema_get_page_tool_definition() -> Tool:
    """Return tool definition for ui_schema_get_page."""
    return Tool(
        name="ui_schema_get_page",
        description=(
            "Get the full UI schema for a single page — all sections, elements, forms, "
            "modals, and links. Use this to understand what's on a specific page."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "page_url": {
                    "type": "string",
                    "description": "URL of the page to retrieve",
                },
                "crawl_id": {
                    "type": "string",
                    "description": "Crawl ID. If omitted, uses the latest crawl.",
                },
                "include_screenshots": {
                    "type": "boolean",
                    "description": "Include screenshot paths in output (default true)",
                    "default": True,
                },
            },
            "required": ["page_url"],
        },
    )


def ui_schema_search_tool_definition() -> Tool:
    """Return tool definition for ui_schema_search."""
    return Tool(
        name="ui_schema_search",
        description=(
            "Search across the UI schema for pages, elements, forms, modals, or flows "
            "matching a query string. Useful for finding where a specific feature or "
            "element is located in the UI."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string",
                },
                "search_type": {
                    "type": "string",
                    "enum": ["all", "pages", "elements", "forms", "modals", "flows"],
                    "description": "Type of search: all (default), pages, elements, forms, modals, or flows",
                    "default": "all",
                },
                "crawl_id": {
                    "type": "string",
                    "description": "Crawl ID. If omitted, uses the latest crawl.",
                },
            },
            "required": ["query"],
        },
    )


def ui_schema_compare_tool_definition() -> Tool:
    """Return tool definition for ui_schema_compare."""
    return Tool(
        name="ui_schema_compare",
        description=(
            "Compare two UI schema versions to see what changed between crawls. "
            "Reports added, removed, and modified pages and elements."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "crawl_id_old": {
                    "type": "string",
                    "description": "Older crawl ID to compare from",
                },
                "crawl_id_new": {
                    "type": "string",
                    "description": "Newer crawl ID to compare to. Defaults to latest.",
                },
                "diff_scope": {
                    "type": "string",
                    "enum": ["summary", "pages", "elements", "full"],
                    "description": "Level of detail: summary, pages, elements, or full (default)",
                    "default": "full",
                },
            },
            "required": ["crawl_id_old"],
        },
    )


def ui_screenshot_get_tool_definition() -> Tool:
    """Return tool definition for ui_screenshot_get."""
    return Tool(
        name="ui_screenshot_get",
        description=(
            "Get information about a screenshot captured during a crawl, "
            "including its file path and size."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "screenshot_id": {
                    "type": "string",
                    "description": "Screenshot identifier (filename stem without .png extension)",
                },
                "crawl_id": {
                    "type": "string",
                    "description": "Crawl ID. If omitted, uses the latest crawl.",
                },
                "context": {
                    "type": "string",
                    "enum": ["page", "modal", "flow_step"],
                    "description": "Context of the screenshot (page, modal, or flow_step)",
                    "default": "page",
                },
            },
            "required": ["screenshot_id"],
        },
    )


# =============================================================================
# Handlers
# =============================================================================


def _resolve_crawl_id(crawl_id: str = None) -> str:
    """Resolve a crawl_id, defaulting to the latest if not provided."""
    if crawl_id:
        return crawl_id
    store = SchemaStore()
    latest = store.get_latest_crawl_id()
    if not latest:
        raise ValueError("No crawls found. Run ui_crawl_start first.")
    return latest


async def handle_ui_schema_list_pages(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_schema_list_pages tool execution."""
    try:
        crawl_id = _resolve_crawl_id(arguments.get("crawl_id"))
        filter_str = arguments.get("filter", "")

        store = SchemaStore()
        schema = store.load(crawl_id)
        if not schema:
            return [TextContent(type="text", text=f"Schema not found for crawl: {crawl_id}")]

        pages = []
        for url, page in sorted(schema.pages.items()):
            if filter_str:
                filter_lower = filter_str.lower()
                match = (
                    filter_lower in url.lower()
                    or filter_lower in page.title.lower()
                    or any(filter_lower in b.lower() for b in page.breadcrumbs)
                )
                if not match:
                    continue
            pages.append({
                "url": page.url,
                "title": page.title,
                "breadcrumbs": page.breadcrumbs,
                "element_count": page.element_count,
                "forms": len(page.forms),
                "modals": len(page.modals),
                "links": len(page.links),
            })

        output_lines = [
            f"**Pages in Crawl {crawl_id}**",
            f"({len(pages)} page(s)" + (f" matching '{filter_str}'" if filter_str else "") + ")\n",
        ]

        for p in pages:
            crumbs = " > ".join(p["breadcrumbs"]) if p["breadcrumbs"] else ""
            output_lines.append(f"**{p['title']}**")
            output_lines.append(f"  URL: {p['url']}")
            if crumbs:
                output_lines.append(f"  Breadcrumbs: {crumbs}")
            output_lines.append(
                f"  Elements: {p['element_count']} | Forms: {p['forms']} | "
                f"Modals: {p['modals']} | Links: {p['links']}"
            )
            output_lines.append("")

        if not pages:
            output_lines.append("No pages found.")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.exception("Error listing schema pages")
        return [TextContent(type="text", text=f"Error: {e}")]


async def handle_ui_schema_get_page(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_schema_get_page tool execution."""
    try:
        page_url = arguments["page_url"]
        crawl_id = _resolve_crawl_id(arguments.get("crawl_id"))
        include_screenshots = arguments.get("include_screenshots", True)

        store = SchemaStore()
        schema = store.load(crawl_id)
        if not schema:
            return [TextContent(type="text", text=f"Schema not found for crawl: {crawl_id}")]

        # Find the page
        page = schema.pages.get(page_url)
        if not page:
            # Try partial match
            for url, p in schema.pages.items():
                if page_url in url or url in page_url:
                    page = p
                    break

        if not page:
            return [TextContent(type="text", text=f"Page not found: {page_url}")]

        # Build detailed output
        data = page.model_dump(mode="json")
        if not include_screenshots:
            data.pop("screenshot_path", None)
            for modal in data.get("modals", []):
                modal.pop("screenshot_path", None)

        output = json.dumps(data, indent=2, default=str)
        return [TextContent(type="text", text=f"**Page Schema: {page.title}**\n\n```json\n{output}\n```")]

    except Exception as e:
        logger.exception("Error getting page schema")
        return [TextContent(type="text", text=f"Error: {e}")]


async def handle_ui_schema_search(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_schema_search tool execution."""
    try:
        query = arguments["query"]
        search_type = arguments.get("search_type", "all")
        crawl_id = _resolve_crawl_id(arguments.get("crawl_id"))

        store = SchemaStore()

        output_lines = [f"**Search Results for '{query}'** (crawl: {crawl_id})\n"]

        if search_type in ("all", "pages"):
            results = store.search_pages(crawl_id, query)
            if results:
                output_lines.append(f"### Pages ({len(results)})")
                for r in results:
                    output_lines.append(f"- **{r['title']}** ({r['url']}) — {r['element_count']} elements")
                output_lines.append("")

        if search_type in ("all", "elements"):
            results = store.search_elements(crawl_id, query)
            if results:
                output_lines.append(f"### Elements ({len(results)})")
                for r in results[:20]:
                    output_lines.append(f"- [{r['type']}] **{r['label']}** on {r['page_title']} ({r['page_url']})")
                output_lines.append("")

        if search_type in ("all", "forms"):
            results = store.search_forms(crawl_id, query)
            if results:
                output_lines.append(f"### Forms ({len(results)})")
                for r in results:
                    output_lines.append(f"- **{r['form_title']}** ({r['field_count']} fields) on {r['page_title']}")
                output_lines.append("")

        if search_type in ("all", "modals"):
            results = store.search_modals(crawl_id, query)
            if results:
                output_lines.append(f"### Modals ({len(results)})")
                for r in results:
                    output_lines.append(f"- **{r['modal_title']}** ({r['element_count']} elements) on {r['page_title']}")
                output_lines.append("")

        if search_type in ("all", "flows"):
            results = store.search_flows(crawl_id, query)
            if results:
                output_lines.append(f"### Flows ({len(results)})")
                for r in results:
                    output_lines.append(f"- **{r['name']}** ({r['step_count']} steps)")
                output_lines.append("")

        if len(output_lines) == 1:
            output_lines.append("No results found.")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.exception("Error searching schema")
        return [TextContent(type="text", text=f"Error: {e}")]


async def handle_ui_schema_compare(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_schema_compare tool execution."""
    try:
        crawl_id_old = arguments["crawl_id_old"]
        crawl_id_new = arguments.get("crawl_id_new")
        diff_scope_str = arguments.get("diff_scope", "full")

        store = SchemaStore()

        if not crawl_id_new:
            crawl_id_new = store.get_latest_crawl_id()
            if not crawl_id_new:
                return [TextContent(type="text", text="No latest crawl found for comparison.")]

        old_schema = store.load(crawl_id_old)
        if not old_schema:
            return [TextContent(type="text", text=f"Old schema not found: {crawl_id_old}")]

        new_schema = store.load(crawl_id_new)
        if not new_schema:
            return [TextContent(type="text", text=f"New schema not found: {crawl_id_new}")]

        scope = DiffScope(diff_scope_str)
        diff = compare_schemas(old_schema, new_schema, scope=scope)

        output_lines = [
            f"**Schema Comparison**",
            f"Old: {diff.crawl_id_old} | New: {diff.crawl_id_new}\n",
            f"**Summary:** {diff.summary}\n",
        ]

        if diff.pages_added:
            output_lines.append(f"### Pages Added ({len(diff.pages_added)})")
            for url in diff.pages_added:
                output_lines.append(f"- {url}")
            output_lines.append("")

        if diff.pages_removed:
            output_lines.append(f"### Pages Removed ({len(diff.pages_removed)})")
            for url in diff.pages_removed:
                output_lines.append(f"- {url}")
            output_lines.append("")

        if diff.pages_modified:
            output_lines.append(f"### Pages Modified ({len(diff.pages_modified)})")
            for mod in diff.pages_modified:
                output_lines.append(f"\n**{mod.page_url}**")
                for detail in mod.details:
                    output_lines.append(f"  - {detail}")
            output_lines.append("")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.exception("Error comparing schemas")
        return [TextContent(type="text", text=f"Error: {e}")]


async def handle_ui_screenshot_get(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle ui_screenshot_get tool execution."""
    try:
        screenshot_id = arguments["screenshot_id"]
        crawl_id = _resolve_crawl_id(arguments.get("crawl_id"))

        mgr = ScreenshotManager()
        info = mgr.get_screenshot_info(crawl_id, screenshot_id)

        if info and info["exists"]:
            output = (
                f"**Screenshot Info**\n\n"
                f"**ID:** {info['screenshot_id']}\n"
                f"**Path:** {info['path']}\n"
                f"**Size:** {info['size_bytes']:,} bytes\n"
                f"**Exists:** Yes"
            )
        else:
            output = (
                f"**Screenshot Info**\n\n"
                f"**ID:** {screenshot_id}\n"
                f"**Exists:** No\n"
                f"**Expected Path:** {info['path'] if info else 'Unknown'}"
            )

        return [TextContent(type="text", text=output)]

    except Exception as e:
        logger.exception("Error getting screenshot info")
        return [TextContent(type="text", text=f"Error: {e}")]


# =============================================================================
# Module Registration (dict pattern)
# =============================================================================

WEBGUI_SCHEMA_TOOL_DEFINITIONS = {
    "ui_schema_list_pages": ui_schema_list_pages_tool_definition,
    "ui_schema_get_page": ui_schema_get_page_tool_definition,
    "ui_schema_search": ui_schema_search_tool_definition,
    "ui_schema_compare": ui_schema_compare_tool_definition,
    "ui_screenshot_get": ui_screenshot_get_tool_definition,
}

WEBGUI_SCHEMA_HANDLERS = {
    "ui_schema_list_pages": handle_ui_schema_list_pages,
    "ui_schema_get_page": handle_ui_schema_get_page,
    "ui_schema_search": handle_ui_schema_search,
    "ui_schema_compare": handle_ui_schema_compare,
    "ui_screenshot_get": handle_ui_screenshot_get,
}
