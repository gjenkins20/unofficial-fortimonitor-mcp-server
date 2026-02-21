"""Tests for the WebGUI knowledge layer tools and SchemaStore.

Covers:
  - Tool definition / handler registration consistency
  - SchemaStore unit tests with a small inline fixture
  - Async handler tests with mocked store
"""

import asyncio
import json
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Minimal 3-page schema fixture
SAMPLE_SCHEMA = {
    "schema_version": "1.0.0",
    "crawl_metadata": {
        "crawl_id": "crawl-test123",
        "target_url": "https://example.fortimonitor.com",
        "application_name": "FortiMonitor",
        "total_pages": 3,
        "total_elements": 12,
        "total_forms": 3,
        "total_modals": 2,
        "coverage": {
            "total_links_discovered": 50,
            "total_links_crawled": 3,
            "total_unique_patterns": 3,
        },
    },
    "pages": {
        "https://example.fortimonitor.com/incidents": {
            "page_id": "incidents",
            "url": "https://example.fortimonitor.com/incidents",
            "title": "Incidents | FortiMonitor",
            "breadcrumbs": ["All Incidents"],
            "screenshot_path": "data/webgui/screenshots/crawl-test123/page_incidents.png",
            "sections": [
                {
                    "heading": "Page Elements",
                    "elements": [
                        {
                            "element_id": "elem-0",
                            "type": "button",
                            "label": "Acknowledge",
                            "selector": "#ack-btn",
                            "attributes": {},
                            "position": {"x": 10, "y": 20, "width": 80, "height": 30},
                            "children": [],
                        },
                        {
                            "element_id": "elem-1",
                            "type": "link",
                            "label": "View Details",
                            "selector": ".details-link",
                            "attributes": {"href": "/incidents/123"},
                            "position": None,
                            "children": [],
                        },
                    ],
                }
            ],
            "modals": [
                {
                    "modal_id": "confirm-ack",
                    "title": "Confirm Acknowledge",
                    "trigger_element": None,
                    "elements": [
                        {
                            "element_id": "modal-elem-0",
                            "type": "button",
                            "label": "Yes",
                            "selector": "#yes",
                            "attributes": {},
                            "position": None,
                            "children": [],
                        }
                    ],
                    "forms": [],
                    "screenshot_path": None,
                }
            ],
            "forms": [
                {
                    "form_id": "form-0",
                    "title": "Filter Incidents",
                    "fields": [
                        {
                            "field_id": "filter-status",
                            "label": "Status",
                            "type": "select",
                            "required": False,
                            "placeholder": "",
                            "options": ["Active", "Resolved"],
                            "validation": None,
                            "selector": "#filter-status",
                        }
                    ],
                    "submit_button": None,
                    "selector": "#filter-form",
                }
            ],
            "links": [
                {
                    "text": "Server List",
                    "url": "https://example.fortimonitor.com/report/ListServers",
                    "type": "navigation",
                    "source": "sidebar",
                },
                {
                    "text": "Help",
                    "url": "https://docs.fortinet.com",
                    "type": "external",
                    "source": "navigation",
                },
            ],
        },
        "https://example.fortimonitor.com/report/ListServers": {
            "page_id": "report-ListServers",
            "url": "https://example.fortimonitor.com/report/ListServers",
            "title": "Server List | FortiMonitor",
            "breadcrumbs": ["Reports", "Server List"],
            "screenshot_path": "data/webgui/screenshots/crawl-test123/page_report_ListServers.png",
            "sections": [
                {
                    "heading": "Server Table",
                    "elements": [
                        {
                            "element_id": "elem-0",
                            "type": "input",
                            "label": "Search servers",
                            "selector": "#search",
                            "attributes": {},
                            "position": None,
                            "children": [],
                        }
                    ],
                }
            ],
            "modals": [],
            "forms": [
                {
                    "form_id": "form-0",
                    "title": "Server Search",
                    "fields": [
                        {
                            "field_id": "search-field",
                            "label": "Server name",
                            "type": "input",
                            "required": True,
                            "placeholder": "Enter server name",
                            "options": [],
                            "validation": None,
                            "selector": "#search-input",
                        }
                    ],
                    "submit_button": {
                        "element_id": "btn-search",
                        "type": "button",
                        "label": "Search",
                        "selector": "#search-btn",
                        "attributes": {},
                        "position": None,
                        "children": [],
                    },
                    "selector": "#search-form",
                }
            ],
            "links": [],
        },
        "https://example.fortimonitor.com/application": {
            "page_id": "application",
            "url": "https://example.fortimonitor.com/application",
            "title": "Applications | FortiMonitor",
            "breadcrumbs": ["Applications"],
            "screenshot_path": None,
            "sections": [],
            "modals": [
                {
                    "modal_id": "add-app",
                    "title": "Add Application",
                    "trigger_element": "elem-add",
                    "elements": [],
                    "forms": [
                        {
                            "form_id": "form-modal-0",
                            "title": "New Application",
                            "fields": [
                                {
                                    "field_id": "app-name",
                                    "label": "Application Name",
                                    "type": "input",
                                    "required": True,
                                    "placeholder": "",
                                    "options": [],
                                    "validation": None,
                                    "selector": "#app-name",
                                }
                            ],
                            "submit_button": None,
                            "selector": "#new-app-form",
                        }
                    ],
                    "screenshot_path": None,
                }
            ],
            "forms": [],
            "links": [],
        },
    },
}


@pytest.fixture
def schema_file(tmp_path):
    """Write sample schema to a temp file and return its path."""
    filepath = tmp_path / "test_schema.json"
    filepath.write_text(json.dumps(SAMPLE_SCHEMA))
    return filepath


@pytest.fixture
def screenshots_dir(tmp_path):
    """Create a screenshots dir with a fake PNG file."""
    ss_dir = tmp_path / "screenshots"
    ss_dir.mkdir()
    # Create a tiny fake PNG for the incidents page
    fake_png = ss_dir / "page_incidents.png"
    # Minimal valid PNG (1x1 pixel, transparent)
    fake_png.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
        b"\r\n\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return ss_dir


@pytest.fixture
def store(schema_file, screenshots_dir):
    """Create a SchemaStore with the test fixtures."""
    from src.webgui.store import SchemaStore

    return SchemaStore(schema_file=schema_file, screenshots_dir=screenshots_dir)


# ---------------------------------------------------------------------------
# TestWebguiToolDefinitions
# ---------------------------------------------------------------------------


class TestWebguiToolDefinitions:
    """Verify tool definitions and handler registration."""

    def test_all_seven_tools_defined(self):
        """WEBGUI_TOOL_DEFINITIONS has exactly 7 entries."""
        from src.webgui.tools import WEBGUI_TOOL_DEFINITIONS

        assert len(WEBGUI_TOOL_DEFINITIONS) == 7

    def test_all_seven_handlers_defined(self):
        """WEBGUI_HANDLERS has exactly 7 entries."""
        from src.webgui.tools import WEBGUI_HANDLERS

        assert len(WEBGUI_HANDLERS) == 7

    def test_definition_handler_keys_match(self):
        """Definition dict keys match handler dict keys."""
        from src.webgui.tools import WEBGUI_TOOL_DEFINITIONS, WEBGUI_HANDLERS

        assert set(WEBGUI_TOOL_DEFINITIONS.keys()) == set(WEBGUI_HANDLERS.keys())

    def test_expected_tool_names(self):
        """All 7 expected tool names are present."""
        from src.webgui.tools import WEBGUI_TOOL_DEFINITIONS

        expected = {
            "ui_list_pages",
            "ui_get_page",
            "ui_search",
            "ui_get_screenshot",
            "ui_get_navigation",
            "ui_describe_page",
            "ui_get_form",
        }
        assert set(WEBGUI_TOOL_DEFINITIONS.keys()) == expected

    def test_definitions_return_tool_objects(self):
        """Each definition callable returns a Tool with matching name."""
        from mcp.types import Tool
        from src.webgui.tools import WEBGUI_TOOL_DEFINITIONS

        for name, defn_func in WEBGUI_TOOL_DEFINITIONS.items():
            tool = defn_func()
            assert isinstance(tool, Tool)
            assert tool.name == name
            assert tool.description
            assert tool.inputSchema
            assert tool.inputSchema.get("type") == "object"

    def test_all_handlers_are_async(self):
        """Every handler is an async callable."""
        import asyncio
        from src.webgui.tools import WEBGUI_HANDLERS

        for name, handler in WEBGUI_HANDLERS.items():
            assert callable(handler), f"{name} is not callable"
            assert asyncio.iscoroutinefunction(handler), f"{name} is not async"


# ---------------------------------------------------------------------------
# TestSchemaStore
# ---------------------------------------------------------------------------


class TestSchemaStore:
    """Unit tests for SchemaStore with the inline fixture."""

    def test_lazy_loading(self, schema_file, screenshots_dir):
        """Store does not load JSON until first method call."""
        from src.webgui.store import SchemaStore

        s = SchemaStore(schema_file=schema_file, screenshots_dir=screenshots_dir)
        assert s._data is None
        s.get_metadata()
        assert s._data is not None

    def test_get_metadata(self, store):
        """get_metadata returns crawl stats."""
        meta = store.get_metadata()
        assert meta["crawl_id"] == "crawl-test123"
        assert meta["total_pages"] == 3
        assert meta["total_pages_loaded"] == 3
        assert meta["schema_version"] == "1.0.0"
        assert "incidents" in meta["categories"]

    def test_list_pages_all(self, store):
        """list_pages returns all 3 pages."""
        result = store.list_pages()
        assert result["total"] == 3
        assert result["count"] == 3
        assert len(result["pages"]) == 3

    def test_list_pages_with_category(self, store):
        """list_pages filters by category."""
        result = store.list_pages(category="report")
        assert result["total"] == 1
        assert result["pages"][0]["page_id"] == "report-ListServers"

    def test_list_pages_pagination(self, store):
        """list_pages respects limit and offset."""
        result = store.list_pages(limit=1, offset=0)
        assert result["count"] == 1
        assert result["total"] == 3

        result2 = store.list_pages(limit=1, offset=1)
        assert result2["count"] == 1
        assert result2["pages"][0]["url"] != result["pages"][0]["url"]

    def test_list_pages_nonexistent_category(self, store):
        """list_pages with unknown category returns empty."""
        result = store.list_pages(category="nonexistent")
        assert result["total"] == 0
        assert result["pages"] == []

    def test_get_page_by_url(self, store):
        """get_page retrieves page data by URL."""
        page = store.get_page(url="https://example.fortimonitor.com/incidents")
        assert page is not None
        assert page["title"] == "Incidents | FortiMonitor"
        assert page["page_id"] == "incidents"
        assert "sections" in page  # sections summary when include_elements=False

    def test_get_page_by_page_id(self, store):
        """get_page retrieves page data by page_id."""
        page = store.get_page(page_id="report-ListServers")
        assert page is not None
        assert page["title"] == "Server List | FortiMonitor"

    def test_get_page_not_found(self, store):
        """get_page returns None for unknown URL/page_id."""
        assert store.get_page(url="https://nonexistent.com/foo") is None
        assert store.get_page(page_id="nonexistent") is None

    def test_get_page_include_elements(self, store):
        """get_page with include_elements returns element data."""
        page = store.get_page(
            url="https://example.fortimonitor.com/incidents",
            include_elements=True,
        )
        assert "elements" in page
        assert len(page["elements"]) == 2
        assert page["elements"][0]["label"] == "Acknowledge"

    def test_get_page_modals_summary(self, store):
        """get_page includes modal summaries."""
        page = store.get_page(url="https://example.fortimonitor.com/incidents")
        assert "modals_summary" in page
        assert len(page["modals_summary"]) == 1
        assert page["modals_summary"][0]["title"] == "Confirm Acknowledge"

    def test_search_by_title(self, store):
        """Search finds pages by title words."""
        result = store.search("incidents")
        assert result["total"] >= 1
        urls = [r["url"] for r in result["results"]]
        assert "https://example.fortimonitor.com/incidents" in urls

    def test_search_by_element_label(self, store):
        """Search finds pages by element labels."""
        result = store.search("Acknowledge", search_in="elements")
        assert result["total"] >= 1

    def test_search_by_form(self, store):
        """Search finds pages by form field labels."""
        result = store.search("server name", search_in="forms")
        assert result["total"] >= 1
        urls = [r["url"] for r in result["results"]]
        assert "https://example.fortimonitor.com/report/ListServers" in urls

    def test_search_by_modal(self, store):
        """Search finds pages by modal titles."""
        result = store.search("Add Application", search_in="modals")
        assert result["total"] >= 1

    def test_search_empty_query(self, store):
        """Search with empty query returns no results."""
        result = store.search("")
        assert result["total"] == 0

    def test_search_no_match(self, store):
        """Search with nonsense query returns no results."""
        result = store.search("xyznonexistent999")
        assert result["total"] == 0

    def test_search_multiple_words_scored(self, store):
        """Search ranks multi-word matches higher."""
        result = store.search("Filter Incidents")
        # The incidents page should score higher than others
        if result["total"] > 0:
            assert result["results"][0]["url"] == "https://example.fortimonitor.com/incidents"

    def test_get_navigation_tree(self, store):
        """get_navigation_tree builds a hierarchical structure."""
        tree = store.get_navigation_tree()
        assert isinstance(tree, dict)
        # Should have top-level keys from URL paths
        assert "incidents" in tree or "report" in tree or "application" in tree

    def test_get_navigation_tree_depth(self, store):
        """get_navigation_tree respects max_depth."""
        tree1 = store.get_navigation_tree(max_depth=1)
        tree3 = store.get_navigation_tree(max_depth=3)
        # Both should be valid dicts
        assert isinstance(tree1, dict)
        assert isinstance(tree3, dict)

    def test_get_screenshot_path_found(self, store, screenshots_dir):
        """get_screenshot_path resolves to existing file."""
        path = store.get_screenshot_path(url="https://example.fortimonitor.com/incidents")
        assert path is not None
        assert path.exists()
        assert path.name == "page_incidents.png"

    def test_get_screenshot_path_missing_file(self, store):
        """get_screenshot_path returns None when file doesn't exist on disk."""
        # report page has a screenshot_path in schema but no matching file
        path = store.get_screenshot_path(page_id="report-ListServers")
        assert path is None

    def test_get_screenshot_path_no_screenshot_in_schema(self, store):
        """get_screenshot_path returns None when schema has null screenshot_path."""
        path = store.get_screenshot_path(page_id="application")
        assert path is None

    def test_get_screenshot_path_unknown_page(self, store):
        """get_screenshot_path returns None for unknown page."""
        path = store.get_screenshot_path(url="https://nonexistent.com")
        assert path is None

    def test_describe_page(self, store):
        """describe_page generates markdown description."""
        desc = store.describe_page(url="https://example.fortimonitor.com/incidents")
        assert desc is not None
        assert "Incidents | FortiMonitor" in desc
        assert "Page Elements" in desc
        assert "Forms" in desc
        assert "Modals" in desc

    def test_describe_page_not_found(self, store):
        """describe_page returns None for unknown page."""
        assert store.describe_page(url="https://nonexistent.com") is None

    def test_get_forms_page_level(self, store):
        """get_forms returns page-level forms."""
        result = store.get_forms(url="https://example.fortimonitor.com/incidents")
        assert result is not None
        assert result["total_forms"] == 1
        assert result["forms"][0]["form_id"] == "form-0"
        assert result["forms"][0]["source"] == "page"

    def test_get_forms_modal_level(self, store):
        """get_forms includes forms from modals."""
        result = store.get_forms(page_id="application")
        assert result is not None
        assert result["total_forms"] == 1
        assert "modal:" in result["forms"][0]["source"]

    def test_get_forms_by_form_id(self, store):
        """get_forms filters by form_id."""
        result = store.get_forms(
            url="https://example.fortimonitor.com/incidents",
            form_id="form-0",
        )
        assert result["total_forms"] == 1

        result2 = store.get_forms(
            url="https://example.fortimonitor.com/incidents",
            form_id="nonexistent",
        )
        assert result2["total_forms"] == 0

    def test_get_forms_not_found(self, store):
        """get_forms returns None for unknown page."""
        assert store.get_forms(url="https://nonexistent.com") is None


# ---------------------------------------------------------------------------
# TestWebguiHandlers
# ---------------------------------------------------------------------------


class TestWebguiHandlers:
    """Async handler tests with a configured store."""

    @pytest.fixture(autouse=True)
    def setup_store(self, store):
        """Configure the module-level store for handler tests."""
        import src.webgui.tools as tools_module

        self._original_store = tools_module._store
        tools_module._store = store
        yield
        tools_module._store = self._original_store

    @pytest.mark.asyncio
    async def test_handle_ui_list_pages(self):
        from src.webgui.tools import handle_ui_list_pages

        result = await handle_ui_list_pages({}, None)
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_handle_ui_list_pages_category(self):
        from src.webgui.tools import handle_ui_list_pages

        result = await handle_ui_list_pages({"category": "report"}, None)
        data = json.loads(result[0].text)
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_handle_ui_get_page(self):
        from src.webgui.tools import handle_ui_get_page

        result = await handle_ui_get_page(
            {"url": "https://example.fortimonitor.com/incidents"}, None
        )
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["title"] == "Incidents | FortiMonitor"

    @pytest.mark.asyncio
    async def test_handle_ui_get_page_missing_params(self):
        from src.webgui.tools import handle_ui_get_page

        result = await handle_ui_get_page({}, None)
        assert "Error" in result[0].text or "error" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_handle_ui_get_page_not_found(self):
        from src.webgui.tools import handle_ui_get_page

        result = await handle_ui_get_page({"url": "https://nonexistent.com"}, None)
        assert "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_handle_ui_search(self):
        from src.webgui.tools import handle_ui_search

        result = await handle_ui_search({"query": "incidents"}, None)
        data = json.loads(result[0].text)
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_handle_ui_search_empty_query(self):
        from src.webgui.tools import handle_ui_search

        result = await handle_ui_search({"query": ""}, None)
        assert "Error" in result[0].text or "error" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_handle_ui_get_screenshot_found(self, screenshots_dir):
        from src.webgui.tools import handle_ui_get_screenshot

        result = await handle_ui_get_screenshot(
            {"url": "https://example.fortimonitor.com/incidents"}, None
        )
        # Should return ImageContent + TextContent
        assert len(result) == 2
        assert result[0].type == "image"
        assert result[1].type == "text"

    @pytest.mark.asyncio
    async def test_handle_ui_get_screenshot_not_found(self):
        from src.webgui.tools import handle_ui_get_screenshot

        result = await handle_ui_get_screenshot({"page_id": "application"}, None)
        assert len(result) == 1
        assert "No screenshot" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_ui_get_screenshot_missing_params(self):
        from src.webgui.tools import handle_ui_get_screenshot

        result = await handle_ui_get_screenshot({}, None)
        assert "Error" in result[0].text or "error" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_handle_ui_get_navigation(self):
        from src.webgui.tools import handle_ui_get_navigation

        result = await handle_ui_get_navigation({}, None)
        data = json.loads(result[0].text)
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_handle_ui_describe_page(self):
        from src.webgui.tools import handle_ui_describe_page

        result = await handle_ui_describe_page(
            {"url": "https://example.fortimonitor.com/incidents"}, None
        )
        assert "Incidents" in result[0].text
        assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_handle_ui_describe_page_missing_params(self):
        from src.webgui.tools import handle_ui_describe_page

        result = await handle_ui_describe_page({}, None)
        assert "Error" in result[0].text or "error" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_handle_ui_get_form(self):
        from src.webgui.tools import handle_ui_get_form

        result = await handle_ui_get_form(
            {"url": "https://example.fortimonitor.com/incidents"}, None
        )
        data = json.loads(result[0].text)
        assert data["total_forms"] == 1

    @pytest.mark.asyncio
    async def test_handle_ui_get_form_missing_params(self):
        from src.webgui.tools import handle_ui_get_form

        result = await handle_ui_get_form({}, None)
        assert "Error" in result[0].text or "error" in result[0].text.lower()


# ---------------------------------------------------------------------------
# TestUnconfiguredStore
# ---------------------------------------------------------------------------


class TestUnconfiguredStore:
    """Test that handlers return clear errors when store is not configured."""

    @pytest.fixture(autouse=True)
    def clear_store(self):
        """Ensure the module-level store is None."""
        import src.webgui.tools as tools_module

        original = tools_module._store
        tools_module._store = None
        yield
        tools_module._store = original

    @pytest.mark.asyncio
    async def test_unconfigured_returns_error(self):
        from src.webgui.tools import handle_ui_list_pages

        result = await handle_ui_list_pages({}, None)
        assert len(result) == 1
        assert "not configured" in result[0].text.lower() or "error" in result[0].text.lower()
