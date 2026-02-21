"""Tests for WebGUI MCP tool definitions and handlers.

Tests tool definitions have correct fields and handlers are properly registered.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from mcp.types import TextContent

from src.webgui.models import (
    CrawlMetadata,
    ElementType,
    UIElement,
    UIForm,
    UIFormField,
    UIFlow,
    UILink,
    UIModal,
    UIPage,
    UISchema,
    UISection,
    LinkType,
    FlowStep,
)
from src.webgui.tools.crawl_tools import (
    WEBGUI_CRAWL_TOOL_DEFINITIONS,
    WEBGUI_CRAWL_HANDLERS,
    ui_crawl_start_tool_definition,
    ui_crawl_status_tool_definition,
    handle_ui_crawl_status,
)
from src.webgui.tools.schema_tools import (
    WEBGUI_SCHEMA_TOOL_DEFINITIONS,
    WEBGUI_SCHEMA_HANDLERS,
    ui_schema_list_pages_tool_definition,
    ui_schema_get_page_tool_definition,
    ui_schema_search_tool_definition,
    ui_schema_compare_tool_definition,
    ui_screenshot_get_tool_definition,
    handle_ui_schema_list_pages,
    handle_ui_schema_get_page,
    handle_ui_schema_search,
    handle_ui_screenshot_get,
)
from src.webgui.tools.walkthrough_tools import (
    WEBGUI_WALKTHROUGH_TOOL_DEFINITIONS,
    WEBGUI_WALKTHROUGH_HANDLERS,
    ui_generate_walkthrough_tool_definition,
    handle_ui_generate_walkthrough,
)
from src.webgui.schema.store import SchemaStore


# =============================================================================
# Tool Definition Tests
# =============================================================================


class TestCrawlToolDefinitions:
    """Test crawl tool definitions."""

    def test_ui_crawl_start_definition(self):
        tool = ui_crawl_start_tool_definition()
        assert tool.name == "ui_crawl_start"
        assert tool.description
        props = tool.inputSchema["properties"]
        assert "target_url" in props
        assert "username" in props
        assert "password" in props
        assert "target_url" in tool.inputSchema["required"]
        assert "username" in tool.inputSchema["required"]
        assert "password" in tool.inputSchema["required"]

    def test_ui_crawl_status_definition(self):
        tool = ui_crawl_status_tool_definition()
        assert tool.name == "ui_crawl_status"
        assert tool.description
        assert "crawl_id" in tool.inputSchema["properties"]

    def test_crawl_dicts_match(self):
        assert set(WEBGUI_CRAWL_TOOL_DEFINITIONS.keys()) == set(
            WEBGUI_CRAWL_HANDLERS.keys()
        )
        assert len(WEBGUI_CRAWL_TOOL_DEFINITIONS) == 2


class TestSchemaToolDefinitions:
    """Test schema tool definitions."""

    def test_ui_schema_list_pages_definition(self):
        tool = ui_schema_list_pages_tool_definition()
        assert tool.name == "ui_schema_list_pages"
        assert "crawl_id" in tool.inputSchema["properties"]
        assert "filter" in tool.inputSchema["properties"]

    def test_ui_schema_get_page_definition(self):
        tool = ui_schema_get_page_tool_definition()
        assert tool.name == "ui_schema_get_page"
        assert "page_url" in tool.inputSchema["required"]

    def test_ui_schema_search_definition(self):
        tool = ui_schema_search_tool_definition()
        assert tool.name == "ui_schema_search"
        assert "query" in tool.inputSchema["required"]
        assert "search_type" in tool.inputSchema["properties"]

    def test_ui_schema_compare_definition(self):
        tool = ui_schema_compare_tool_definition()
        assert tool.name == "ui_schema_compare"
        assert "crawl_id_old" in tool.inputSchema["required"]

    def test_ui_screenshot_get_definition(self):
        tool = ui_screenshot_get_tool_definition()
        assert tool.name == "ui_screenshot_get"
        assert "screenshot_id" in tool.inputSchema["required"]

    def test_schema_dicts_match(self):
        assert set(WEBGUI_SCHEMA_TOOL_DEFINITIONS.keys()) == set(
            WEBGUI_SCHEMA_HANDLERS.keys()
        )
        assert len(WEBGUI_SCHEMA_TOOL_DEFINITIONS) == 5


class TestWalkthroughToolDefinitions:
    """Test walkthrough tool definitions."""

    def test_ui_generate_walkthrough_definition(self):
        tool = ui_generate_walkthrough_tool_definition()
        assert tool.name == "ui_generate_walkthrough"
        assert "target" in tool.inputSchema["required"]
        props = tool.inputSchema["properties"]
        assert "walkthrough_type" in props
        assert "output_format" in props
        assert "include_screenshots" in props

    def test_walkthrough_dicts_match(self):
        assert set(WEBGUI_WALKTHROUGH_TOOL_DEFINITIONS.keys()) == set(
            WEBGUI_WALKTHROUGH_HANDLERS.keys()
        )
        assert len(WEBGUI_WALKTHROUGH_TOOL_DEFINITIONS) == 1


class TestAllToolsCombined:
    """Test that all 8 tools are properly defined."""

    def test_total_tool_count(self):
        total = (
            len(WEBGUI_CRAWL_TOOL_DEFINITIONS)
            + len(WEBGUI_SCHEMA_TOOL_DEFINITIONS)
            + len(WEBGUI_WALKTHROUGH_TOOL_DEFINITIONS)
        )
        assert total == 8

    def test_no_name_collisions(self):
        all_names = set()
        for d in [
            WEBGUI_CRAWL_TOOL_DEFINITIONS,
            WEBGUI_SCHEMA_TOOL_DEFINITIONS,
            WEBGUI_WALKTHROUGH_TOOL_DEFINITIONS,
        ]:
            for name in d:
                assert name not in all_names, f"Duplicate tool name: {name}"
                all_names.add(name)

    def test_all_tool_names_have_ui_prefix(self):
        for d in [
            WEBGUI_CRAWL_TOOL_DEFINITIONS,
            WEBGUI_SCHEMA_TOOL_DEFINITIONS,
            WEBGUI_WALKTHROUGH_TOOL_DEFINITIONS,
        ]:
            for name in d:
                assert name.startswith("ui_"), f"Tool {name} should start with 'ui_'"


# =============================================================================
# Handler Tests (with mocked SchemaStore)
# =============================================================================


@pytest.fixture
def sample_schema():
    """Create a schema and store it in a temp directory."""
    return UISchema(
        crawl_metadata=CrawlMetadata(
            crawl_id="test-crawl",
            target_url="https://app.example.com",
            application_name="TestApp",
            total_pages=2,
        ),
        pages={
            "/dashboard": UIPage(
                page_id="dashboard",
                url="/dashboard",
                title="Dashboard",
                sections=[
                    UISection(
                        heading="Overview",
                        elements=[
                            UIElement(
                                element_id="btn-refresh",
                                type=ElementType.BUTTON,
                                label="Refresh",
                            ),
                        ],
                    )
                ],
            ),
            "/settings": UIPage(
                page_id="settings",
                url="/settings",
                title="Settings",
                forms=[
                    UIForm(
                        form_id="form-general",
                        title="General",
                        fields=[
                            UIFormField(
                                field_id="name",
                                label="Name",
                                type=ElementType.INPUT,
                                required=True,
                            ),
                        ],
                    )
                ],
            ),
        },
        flows=[
            UIFlow(
                flow_id="test-flow",
                name="Test Flow",
                steps=[
                    FlowStep(
                        step_number=1,
                        page_url="/dashboard",
                        action="click",
                        target="btn-refresh",
                        description="Click Refresh",
                    ),
                ],
            ),
        ],
    )


@pytest.fixture
def mock_store(tmp_path, sample_schema):
    """Create a SchemaStore with a pre-loaded sample schema."""
    store = SchemaStore(base_dir=str(tmp_path / "schemas"))
    store.save(sample_schema)
    return store


class TestCrawlStatusHandler:
    """Test crawl status handler."""

    async def test_no_crawls(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        with patch(
            "src.webgui.tools.crawl_tools.CrawlState"
        ) as mock_state_cls:
            mock_state = MagicMock()
            mock_state.list_crawls.return_value = []
            mock_state_cls.return_value = mock_state

            result = await handle_ui_crawl_status({}, None)
            assert len(result) == 1
            assert "No crawls found" in result[0].text


class TestSchemaListPagesHandler:
    """Test schema list pages handler."""

    async def test_list_pages(self, mock_store, sample_schema):
        with patch(
            "src.webgui.tools.schema_tools.SchemaStore", return_value=mock_store
        ):
            result = await handle_ui_schema_list_pages(
                {"crawl_id": "test-crawl"}, None
            )
            assert len(result) == 1
            assert "Dashboard" in result[0].text
            assert "Settings" in result[0].text

    async def test_list_pages_with_filter(self, mock_store):
        with patch(
            "src.webgui.tools.schema_tools.SchemaStore", return_value=mock_store
        ):
            result = await handle_ui_schema_list_pages(
                {"crawl_id": "test-crawl", "filter": "dashboard"}, None
            )
            assert "Dashboard" in result[0].text
            assert "Settings" not in result[0].text

    async def test_list_pages_not_found(self, mock_store):
        with patch(
            "src.webgui.tools.schema_tools.SchemaStore", return_value=mock_store
        ):
            result = await handle_ui_schema_list_pages(
                {"crawl_id": "nonexistent"}, None
            )
            assert "not found" in result[0].text.lower()


class TestSchemaGetPageHandler:
    """Test schema get page handler."""

    async def test_get_page(self, mock_store):
        with patch(
            "src.webgui.tools.schema_tools.SchemaStore", return_value=mock_store
        ):
            result = await handle_ui_schema_get_page(
                {"page_url": "/dashboard", "crawl_id": "test-crawl"}, None
            )
            assert "Dashboard" in result[0].text
            assert "json" in result[0].text.lower()

    async def test_get_page_not_found(self, mock_store):
        with patch(
            "src.webgui.tools.schema_tools.SchemaStore", return_value=mock_store
        ):
            result = await handle_ui_schema_get_page(
                {"page_url": "/nonexistent", "crawl_id": "test-crawl"}, None
            )
            assert "not found" in result[0].text.lower()


class TestSchemaSearchHandler:
    """Test schema search handler."""

    async def test_search_all(self, mock_store):
        with patch(
            "src.webgui.tools.schema_tools.SchemaStore", return_value=mock_store
        ):
            result = await handle_ui_schema_search(
                {"query": "Dashboard", "crawl_id": "test-crawl"}, None
            )
            assert "Dashboard" in result[0].text

    async def test_search_elements(self, mock_store):
        with patch(
            "src.webgui.tools.schema_tools.SchemaStore", return_value=mock_store
        ):
            result = await handle_ui_schema_search(
                {
                    "query": "Refresh",
                    "search_type": "elements",
                    "crawl_id": "test-crawl",
                },
                None,
            )
            assert "Refresh" in result[0].text


class TestWalkthroughHandler:
    """Test walkthrough generation handler."""

    async def test_generate_navigation(self, mock_store):
        with patch(
            "src.webgui.tools.walkthrough_tools.SchemaStore", return_value=mock_store
        ):
            result = await handle_ui_generate_walkthrough(
                {
                    "target": "/dashboard",
                    "walkthrough_type": "navigation",
                    "crawl_id": "test-crawl",
                },
                None,
            )
            assert "Step 1" in result[0].text

    async def test_generate_task(self, mock_store):
        with patch(
            "src.webgui.tools.walkthrough_tools.SchemaStore", return_value=mock_store
        ):
            result = await handle_ui_generate_walkthrough(
                {
                    "target": "change settings name",
                    "walkthrough_type": "task",
                    "crawl_id": "test-crawl",
                },
                None,
            )
            assert "Step" in result[0].text

    async def test_generate_html_output(self, mock_store):
        with patch(
            "src.webgui.tools.walkthrough_tools.SchemaStore", return_value=mock_store
        ):
            result = await handle_ui_generate_walkthrough(
                {
                    "target": "/dashboard",
                    "walkthrough_type": "section",
                    "output_format": "html",
                    "crawl_id": "test-crawl",
                },
                None,
            )
            assert "<html>" in result[0].text

    async def test_no_crawl_found(self):
        with patch(
            "src.webgui.tools.walkthrough_tools.SchemaStore"
        ) as mock_store_cls:
            mock_store_inst = MagicMock()
            mock_store_inst.get_latest_crawl_id.return_value = None
            mock_store_cls.return_value = mock_store_inst

            result = await handle_ui_generate_walkthrough(
                {"target": "/test"}, None
            )
            assert "No crawls found" in result[0].text
