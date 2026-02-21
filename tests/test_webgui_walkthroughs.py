"""Tests for WebGUI walkthrough tools: WorkflowStore, crop screenshot, handlers.

Covers:
  - WorkflowStore unit tests (lazy loading, list, get, search, enrichment)
  - Screenshot cropping with Pillow (position, padding, annotation, fallbacks)
  - Async handler integration tests for the 3 new tools
"""

import asyncio
import base64
import io
import json
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Fixtures — sample schema (reused from test_webgui_tools pattern)
# ---------------------------------------------------------------------------

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
                            "position": {"x": 100, "y": 200, "width": 80, "height": 30},
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
                        {
                            "element_id": "elem-edge",
                            "type": "button",
                            "label": "Edge Button",
                            "selector": "#edge-btn",
                            "attributes": {},
                            "position": {"x": -10, "y": 1060, "width": 50, "height": 30},
                            "children": [],
                        },
                    ],
                }
            ],
            "modals": [],
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
            "links": [],
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
            "forms": [],
            "links": [],
        },
        "https://example.fortimonitor.com/config/maintenance": {
            "page_id": "config-maintenance",
            "url": "https://example.fortimonitor.com/config/maintenance",
            "title": "Maintenance Schedules | FortiMonitor",
            "breadcrumbs": ["Configuration", "Maintenance Schedules"],
            "screenshot_path": None,
            "sections": [],
            "modals": [],
            "forms": [],
            "links": [],
        },
    },
}


SAMPLE_WORKFLOWS_YAML = """\
workflows:

  test-workflow:
    title: "Test Workflow"
    description: "A workflow for testing purposes."
    tags: [test, incidents, maintenance]
    steps:
      - title: "Open incidents page"
        page_id: "incidents"
        instruction: >
          Navigate to the Incidents page to see active incidents.
        highlight_element: "elem-0"
        highlight_form: "form-0"
      - title: "Open server list"
        page_id: "report-ListServers"
        instruction: >
          Navigate to the Server List page.
        highlight_element: null
        highlight_form: null
      - title: "Open maintenance"
        page_id: "config-maintenance"
        instruction: >
          Navigate to Maintenance Schedules.
        highlight_element: null
        highlight_form: null

  another-workflow:
    title: "Alert Configuration"
    description: "Configure alert notification settings."
    tags: [alerts, notifications]
    steps:
      - title: "Open incidents"
        page_id: "incidents"
        instruction: >
          Start from the incidents page.
        highlight_element: null
        highlight_form: null
"""


@pytest.fixture
def schema_file(tmp_path):
    """Write sample schema to a temp file and return its path."""
    filepath = tmp_path / "test_schema.json"
    filepath.write_text(json.dumps(SAMPLE_SCHEMA))
    return filepath


@pytest.fixture
def screenshots_dir(tmp_path):
    """Create a screenshots dir with a real PNG for Pillow to open."""
    from PIL import Image

    ss_dir = tmp_path / "screenshots"
    ss_dir.mkdir()

    # Create a 200x200 white PNG (large enough for crop tests)
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    img.save(ss_dir / "page_incidents.png")

    # Also create one for the server list page
    img2 = Image.new("RGB", (200, 200), color=(200, 200, 200))
    img2.save(ss_dir / "page_report_ListServers.png")

    return ss_dir


@pytest.fixture
def store(schema_file, screenshots_dir):
    """Create a SchemaStore with the test fixtures."""
    from src.webgui.store import SchemaStore

    return SchemaStore(schema_file=schema_file, screenshots_dir=screenshots_dir)


@pytest.fixture
def workflows_file(tmp_path):
    """Write sample workflows YAML to a temp file."""
    filepath = tmp_path / "workflows.yaml"
    filepath.write_text(SAMPLE_WORKFLOWS_YAML)
    return filepath


@pytest.fixture
def workflow_store(store, workflows_file):
    """Create a WorkflowStore with test data."""
    from src.webgui.workflows import WorkflowStore

    return WorkflowStore(workflows_file=workflows_file, schema_store=store)


# ---------------------------------------------------------------------------
# TestWorkflowStore
# ---------------------------------------------------------------------------


class TestWorkflowStore:
    """Unit tests for WorkflowStore."""

    def test_lazy_loading(self, store, workflows_file):
        """YAML is not loaded until first method call."""
        from src.webgui.workflows import WorkflowStore

        ws = WorkflowStore(workflows_file=workflows_file, schema_store=store)
        assert ws._data is None
        ws.list_workflows()
        assert ws._data is not None

    def test_list_workflows(self, workflow_store):
        """Returns all workflows with expected fields."""
        result = workflow_store.list_workflows()
        assert result["total"] == 2
        ids = [w["id"] for w in result["workflows"]]
        assert "test-workflow" in ids
        assert "another-workflow" in ids
        for wf in result["workflows"]:
            assert "title" in wf
            assert "description" in wf
            assert "tags" in wf
            assert "step_count" in wf

    def test_list_workflows_with_query(self, workflow_store):
        """Filters workflows by keyword in title/description/tags."""
        result = workflow_store.list_workflows(query="alert")
        assert result["total"] == 1
        assert result["workflows"][0]["id"] == "another-workflow"

    def test_list_workflows_query_matches_tags(self, workflow_store):
        """Query matches against tags."""
        result = workflow_store.list_workflows(query="maintenance")
        assert result["total"] == 1
        assert result["workflows"][0]["id"] == "test-workflow"

    def test_list_workflows_no_match(self, workflow_store):
        """Returns empty list when no workflows match query."""
        result = workflow_store.list_workflows(query="nonexistent")
        assert result["total"] == 0
        assert result["workflows"] == []

    def test_get_workflow(self, workflow_store):
        """Returns full workflow with enriched step data."""
        result = workflow_store.get_workflow("test-workflow")
        assert result is not None
        assert result["id"] == "test-workflow"
        assert result["title"] == "Test Workflow"
        assert result["total_steps"] == 3
        assert len(result["steps"]) == 3
        # Check step structure
        step1 = result["steps"][0]
        assert step1["step_number"] == 1
        assert step1["title"] == "Open incidents page"
        assert step1["page_id"] == "incidents"
        assert step1["highlight_element"] == "elem-0"
        assert step1["highlight_form"] == "form-0"

    def test_get_workflow_single_step(self, workflow_store):
        """Returns only the requested step."""
        result = workflow_store.get_workflow("test-workflow", step=2)
        assert result is not None
        assert "step" in result
        assert "steps" not in result
        assert result["step"]["step_number"] == 2
        assert result["step"]["page_id"] == "report-ListServers"
        assert result["total_steps"] == 3

    def test_get_workflow_step_out_of_range(self, workflow_store):
        """Returns None for out-of-range step number."""
        assert workflow_store.get_workflow("test-workflow", step=0) is None
        assert workflow_store.get_workflow("test-workflow", step=99) is None

    def test_get_workflow_unknown_id(self, workflow_store):
        """Returns None for unknown workflow ID."""
        assert workflow_store.get_workflow("nonexistent") is None

    def test_missing_yaml_file(self, store, tmp_path):
        """Returns empty results when YAML file doesn't exist."""
        from src.webgui.workflows import WorkflowStore

        ws = WorkflowStore(
            workflows_file=tmp_path / "does-not-exist.yaml",
            schema_store=store,
        )
        result = ws.list_workflows()
        assert result["total"] == 0
        assert ws.get_workflow("anything") is None

    def test_step_page_enrichment(self, workflow_store):
        """Steps include page_title and page_url from schema."""
        result = workflow_store.get_workflow("test-workflow")
        step1 = result["steps"][0]
        assert step1["page_title"] == "Incidents | FortiMonitor"
        assert step1["page_url"] == "https://example.fortimonitor.com/incidents"

    def test_step_screenshot_path(self, workflow_store):
        """Steps include screenshot_path when screenshot file exists."""
        result = workflow_store.get_workflow("test-workflow")
        # incidents page has a screenshot
        step1 = result["steps"][0]
        assert step1["screenshot_path"] is not None
        assert "page_incidents.png" in step1["screenshot_path"]

    def test_step_no_screenshot(self, workflow_store):
        """Steps with no screenshot file return None screenshot_path."""
        result = workflow_store.get_workflow("test-workflow")
        # config-maintenance has screenshot_path=None in schema
        step3 = result["steps"][2]
        assert step3["screenshot_path"] is None


# ---------------------------------------------------------------------------
# TestGetElementPosition
# ---------------------------------------------------------------------------


class TestGetElementPosition:
    """Tests for SchemaStore.get_element_position()."""

    def test_valid_position(self, store):
        """Returns position dict for element with position data."""
        pos = store.get_element_position(page_id="incidents", element_id="elem-0")
        assert pos is not None
        assert pos["x"] == 100
        assert pos["y"] == 200
        assert pos["width"] == 80
        assert pos["height"] == 30

    def test_null_position(self, store):
        """Returns None for element with null position."""
        pos = store.get_element_position(page_id="incidents", element_id="elem-1")
        assert pos is None

    def test_unknown_element(self, store):
        """Returns None for nonexistent element_id."""
        pos = store.get_element_position(page_id="incidents", element_id="elem-999")
        assert pos is None

    def test_unknown_page(self, store):
        """Returns None for nonexistent page."""
        pos = store.get_element_position(page_id="nonexistent", element_id="elem-0")
        assert pos is None

    def test_no_element_id(self, store):
        """Returns None when element_id is not provided."""
        pos = store.get_element_position(page_id="incidents", element_id=None)
        assert pos is None


# ---------------------------------------------------------------------------
# TestCropScreenshot
# ---------------------------------------------------------------------------


class TestCropScreenshot:
    """Tests for the ui_crop_screenshot handler."""

    @pytest.fixture(autouse=True)
    def setup_store(self, store):
        """Inject the test store into the tools module."""
        import src.webgui.tools as tools_mod

        tools_mod._store = store
        yield
        tools_mod._store = None

    @pytest.mark.asyncio
    async def test_crop_with_valid_position(self, store):
        """Returns cropped ImageContent smaller than original when position exists."""
        from src.webgui.tools import handle_ui_crop_screenshot

        result = await handle_ui_crop_screenshot(
            {"page_id": "incidents", "element_id": "elem-0", "padding": 10},
            client=None,
        )
        # Should return ImageContent + TextContent
        assert len(result) == 2
        assert result[0].type == "image"
        assert result[1].type == "text"
        assert "elem-0" in result[1].text
        assert "Cropped" in result[1].text

        # Verify the image is smaller than the original 200x200
        from PIL import Image

        img_data = base64.b64decode(result[0].data)
        img = Image.open(io.BytesIO(img_data))
        assert img.width < 200 or img.height < 200

    @pytest.mark.asyncio
    async def test_crop_with_annotation(self, store):
        """Annotated image is returned with red border drawn."""
        from src.webgui.tools import handle_ui_crop_screenshot

        result = await handle_ui_crop_screenshot(
            {
                "page_id": "incidents",
                "element_id": "elem-0",
                "padding": 10,
                "annotate": True,
            },
            client=None,
        )
        assert result[0].type == "image"
        # Verify it's a valid PNG
        img_data = base64.b64decode(result[0].data)
        from PIL import Image

        img = Image.open(io.BytesIO(img_data))
        assert img.format == "PNG"

    @pytest.mark.asyncio
    async def test_crop_with_padding(self, store):
        """Padding is applied around the crop box."""
        from src.webgui.tools import handle_ui_crop_screenshot

        # Small padding
        result_small = await handle_ui_crop_screenshot(
            {"page_id": "incidents", "element_id": "elem-0", "padding": 5},
            client=None,
        )
        # Large padding
        result_large = await handle_ui_crop_screenshot(
            {"page_id": "incidents", "element_id": "elem-0", "padding": 50},
            client=None,
        )

        from PIL import Image

        img_small = Image.open(io.BytesIO(base64.b64decode(result_small[0].data)))
        img_large = Image.open(io.BytesIO(base64.b64decode(result_large[0].data)))

        # Larger padding should produce a larger (or equal) crop
        assert img_large.width >= img_small.width
        assert img_large.height >= img_small.height

    @pytest.mark.asyncio
    async def test_crop_null_position_returns_full(self, store):
        """Falls back to full screenshot + text note when position is null."""
        from src.webgui.tools import handle_ui_crop_screenshot

        result = await handle_ui_crop_screenshot(
            {"page_id": "incidents", "element_id": "elem-1"},
            client=None,
        )
        assert len(result) == 2
        assert result[0].type == "image"
        assert "position data is not available" in result[1].text

    @pytest.mark.asyncio
    async def test_crop_no_element_id_returns_full(self, store):
        """Returns full screenshot when no element_id is provided."""
        from src.webgui.tools import handle_ui_crop_screenshot

        result = await handle_ui_crop_screenshot(
            {"page_id": "incidents"},
            client=None,
        )
        assert len(result) == 2
        assert result[0].type == "image"
        assert "no element_id specified" in result[1].text

    @pytest.mark.asyncio
    async def test_crop_nonexistent_page(self, store):
        """Returns error text for unknown page."""
        from src.webgui.tools import handle_ui_crop_screenshot

        result = await handle_ui_crop_screenshot(
            {"page_id": "nonexistent"},
            client=None,
        )
        assert len(result) == 1
        assert "No screenshot available" in result[0].text

    @pytest.mark.asyncio
    async def test_crop_clamps_to_bounds(self, store):
        """Element off-screen falls back to full screenshot gracefully."""
        from src.webgui.tools import handle_ui_crop_screenshot

        # elem-edge has position x=-10, y=1060 — entirely off the 200x200 image
        result = await handle_ui_crop_screenshot(
            {"page_id": "incidents", "element_id": "elem-edge", "padding": 30},
            client=None,
        )
        assert result[0].type == "image"
        # Falls back to full screenshot since element is off-screen
        assert "position data is not available" in result[1].text

    @pytest.mark.asyncio
    async def test_crop_nonexistent_element(self, store):
        """Returns full screenshot + note for unknown element_id."""
        from src.webgui.tools import handle_ui_crop_screenshot

        result = await handle_ui_crop_screenshot(
            {"page_id": "incidents", "element_id": "elem-999"},
            client=None,
        )
        assert len(result) == 2
        assert result[0].type == "image"
        assert "position data is not available" in result[1].text

    @pytest.mark.asyncio
    async def test_crop_missing_url_and_page_id(self, store):
        """Returns error when neither url nor page_id is provided."""
        from src.webgui.tools import handle_ui_crop_screenshot

        result = await handle_ui_crop_screenshot({}, client=None)
        assert len(result) == 1
        assert "provide either" in result[0].text


# ---------------------------------------------------------------------------
# TestWalkthroughHandlers
# ---------------------------------------------------------------------------


class TestWalkthroughHandlers:
    """Async handler tests for walkthrough tools."""

    @pytest.fixture(autouse=True)
    def setup_stores(self, store, workflow_store):
        """Inject test stores into the tools module."""
        import src.webgui.tools as tools_mod

        tools_mod._store = store
        tools_mod._workflow_store = workflow_store
        yield
        tools_mod._store = None
        tools_mod._workflow_store = None

    @pytest.mark.asyncio
    async def test_handle_ui_list_walkthroughs(self):
        """Returns JSON with workflow list."""
        from src.webgui.tools import handle_ui_list_walkthroughs

        result = await handle_ui_list_walkthroughs({}, client=None)
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["total"] == 2
        assert len(data["workflows"]) == 2

    @pytest.mark.asyncio
    async def test_handle_ui_list_walkthroughs_with_query(self):
        """Filtered results via query parameter."""
        from src.webgui.tools import handle_ui_list_walkthroughs

        result = await handle_ui_list_walkthroughs({"query": "alert"}, client=None)
        data = json.loads(result[0].text)
        assert data["total"] == 1
        assert data["workflows"][0]["id"] == "another-workflow"

    @pytest.mark.asyncio
    async def test_handle_ui_get_walkthrough(self):
        """Returns full workflow JSON with enriched steps."""
        from src.webgui.tools import handle_ui_get_walkthrough

        result = await handle_ui_get_walkthrough(
            {"workflow_id": "test-workflow"}, client=None
        )
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["id"] == "test-workflow"
        assert len(data["steps"]) == 3
        # Check enrichment
        assert data["steps"][0]["page_title"] == "Incidents | FortiMonitor"

    @pytest.mark.asyncio
    async def test_handle_ui_get_walkthrough_unknown(self):
        """Returns error text for unknown workflow_id."""
        from src.webgui.tools import handle_ui_get_walkthrough

        result = await handle_ui_get_walkthrough(
            {"workflow_id": "nonexistent"}, client=None
        )
        assert "not found" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_ui_get_walkthrough_single_step(self):
        """Returns single step when step param is provided."""
        from src.webgui.tools import handle_ui_get_walkthrough

        result = await handle_ui_get_walkthrough(
            {"workflow_id": "test-workflow", "step": 1}, client=None
        )
        data = json.loads(result[0].text)
        assert "step" in data
        assert "steps" not in data
        assert data["step"]["step_number"] == 1

    @pytest.mark.asyncio
    async def test_handle_ui_crop_screenshot(self):
        """Returns ImageContent for a valid crop request."""
        from src.webgui.tools import handle_ui_crop_screenshot

        result = await handle_ui_crop_screenshot(
            {"page_id": "incidents", "element_id": "elem-0"},
            client=None,
        )
        assert result[0].type == "image"
        assert result[1].type == "text"

    @pytest.mark.asyncio
    async def test_handle_ui_get_walkthrough_missing_workflow_id(self):
        """Returns error when workflow_id is missing."""
        from src.webgui.tools import handle_ui_get_walkthrough

        result = await handle_ui_get_walkthrough({}, client=None)
        assert "required" in result[0].text


# ---------------------------------------------------------------------------
# TestWalkthroughsNotConfigured
# ---------------------------------------------------------------------------


class TestWalkthroughsNotConfigured:
    """Tests when workflow store is not configured."""

    @pytest.fixture(autouse=True)
    def setup_no_workflow(self, store):
        """Set store but no workflow_store."""
        import src.webgui.tools as tools_mod

        tools_mod._store = store
        tools_mod._workflow_store = None
        yield
        tools_mod._store = None

    @pytest.mark.asyncio
    async def test_list_walkthroughs_not_configured(self):
        """Returns friendly message when workflows not configured."""
        from src.webgui.tools import handle_ui_list_walkthroughs

        result = await handle_ui_list_walkthroughs({}, client=None)
        assert "not configured" in result[0].text

    @pytest.mark.asyncio
    async def test_get_walkthrough_not_configured(self):
        """Returns friendly message when workflows not configured."""
        from src.webgui.tools import handle_ui_get_walkthrough

        result = await handle_ui_get_walkthrough(
            {"workflow_id": "anything"}, client=None
        )
        assert "not configured" in result[0].text


# ---------------------------------------------------------------------------
# TestToolDefinitions
# ---------------------------------------------------------------------------


class TestNewToolDefinitions:
    """Verify the 3 new tools are registered in WEBGUI_TOOL_DEFINITIONS."""

    def test_new_tools_in_definitions(self):
        """The 3 new tools appear in WEBGUI_TOOL_DEFINITIONS."""
        from src.webgui.tools import WEBGUI_TOOL_DEFINITIONS

        assert "ui_list_walkthroughs" in WEBGUI_TOOL_DEFINITIONS
        assert "ui_get_walkthrough" in WEBGUI_TOOL_DEFINITIONS
        assert "ui_crop_screenshot" in WEBGUI_TOOL_DEFINITIONS

    def test_new_tools_in_handlers(self):
        """The 3 new tools appear in WEBGUI_HANDLERS."""
        from src.webgui.tools import WEBGUI_HANDLERS

        assert "ui_list_walkthroughs" in WEBGUI_HANDLERS
        assert "ui_get_walkthrough" in WEBGUI_HANDLERS
        assert "ui_crop_screenshot" in WEBGUI_HANDLERS

    def test_total_tool_count(self):
        """Total WebGUI tools is now 10 (7 original + 3 new)."""
        from src.webgui.tools import WEBGUI_TOOL_DEFINITIONS, WEBGUI_HANDLERS

        assert len(WEBGUI_TOOL_DEFINITIONS) == 10
        assert len(WEBGUI_HANDLERS) == 10

    def test_definitions_return_tool_objects(self):
        """All new definition functions return Tool instances."""
        from mcp.types import Tool
        from src.webgui.tools import WEBGUI_TOOL_DEFINITIONS

        for name in ["ui_list_walkthroughs", "ui_get_walkthrough", "ui_crop_screenshot"]:
            tool = WEBGUI_TOOL_DEFINITIONS[name]()
            assert isinstance(tool, Tool)
            assert tool.name == name
