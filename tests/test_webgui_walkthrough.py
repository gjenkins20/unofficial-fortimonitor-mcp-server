"""Tests for WebGUI walkthrough generation.

Tests navigation paths, task matching, section guides, and flow playback.
"""

import pytest

from src.webgui.models import (
    CrawlMetadata,
    ElementType,
    FlowStep,
    UIElement,
    UIFlow,
    UIForm,
    UIFormField,
    UILink,
    UIModal,
    UIPage,
    UISchema,
    UISection,
    WalkthroughType,
    LinkType,
)
from src.webgui.walkthrough.formatters import format_html, format_markdown
from src.webgui.walkthrough.generator import (
    generate_flow_walkthrough,
    generate_navigation_walkthrough,
    generate_section_walkthrough,
    generate_task_walkthrough,
    generate_walkthrough,
)


@pytest.fixture
def sample_schema():
    """Create a multi-page schema for walkthrough testing."""
    return UISchema(
        crawl_metadata=CrawlMetadata(
            crawl_id="wt-test",
            target_url="https://app.example.com",
            application_name="TestApp",
        ),
        pages={
            "https://app.example.com/": UIPage(
                page_id="home",
                url="https://app.example.com/",
                title="Home",
                links=[
                    UILink(text="Dashboard", url="https://app.example.com/dashboard", type=LinkType.NAVIGATION),
                    UILink(text="Settings", url="https://app.example.com/settings", type=LinkType.NAVIGATION),
                ],
            ),
            "https://app.example.com/dashboard": UIPage(
                page_id="dashboard",
                url="https://app.example.com/dashboard",
                title="Dashboard",
                sections=[
                    UISection(
                        heading="Server Overview",
                        elements=[
                            UIElement(element_id="refresh-btn", type=ElementType.BUTTON, label="Refresh Data"),
                            UIElement(element_id="status-table", type=ElementType.TABLE, label="Server Status"),
                        ],
                    )
                ],
                links=[
                    UILink(text="Add Server", url="https://app.example.com/servers/add", type=LinkType.NAVIGATION),
                ],
            ),
            "https://app.example.com/settings": UIPage(
                page_id="settings",
                url="https://app.example.com/settings",
                title="Settings",
                forms=[
                    UIForm(
                        form_id="general-settings",
                        title="General Settings",
                        fields=[
                            UIFormField(
                                field_id="site-name", label="Site Name",
                                type=ElementType.INPUT, required=True,
                            ),
                            UIFormField(
                                field_id="timezone", label="Timezone",
                                type=ElementType.SELECT,
                                options=["UTC", "US/Eastern", "US/Pacific"],
                            ),
                        ],
                        submit_button=UIElement(
                            element_id="save-btn", type=ElementType.BUTTON, label="Save Settings"
                        ),
                    )
                ],
                modals=[
                    UIModal(
                        modal_id="confirm-save",
                        title="Confirm Changes",
                        trigger_element="save-btn",
                    )
                ],
            ),
            "https://app.example.com/servers/add": UIPage(
                page_id="servers-add",
                url="https://app.example.com/servers/add",
                title="Add Server",
                forms=[
                    UIForm(
                        form_id="add-server-form",
                        title="Add Server",
                        fields=[
                            UIFormField(
                                field_id="hostname", label="Hostname",
                                type=ElementType.INPUT, required=True,
                            ),
                            UIFormField(
                                field_id="ip-address", label="IP Address",
                                type=ElementType.INPUT,
                            ),
                        ],
                        submit_button=UIElement(
                            element_id="create-btn", type=ElementType.BUTTON, label="Create Server"
                        ),
                    )
                ],
            ),
        },
        flows=[
            UIFlow(
                flow_id="add-server-flow",
                name="Add a New Server",
                steps=[
                    FlowStep(
                        step_number=1,
                        page_url="https://app.example.com/dashboard",
                        action="click",
                        target="Add Server",
                        description="Click 'Add Server' on the dashboard",
                    ),
                    FlowStep(
                        step_number=2,
                        page_url="https://app.example.com/servers/add",
                        action="fill",
                        target="hostname",
                        description="Enter the server hostname",
                    ),
                    FlowStep(
                        step_number=3,
                        page_url="https://app.example.com/servers/add",
                        action="click",
                        target="create-btn",
                        description="Click 'Create Server' to submit",
                    ),
                ],
            )
        ],
    )


# =============================================================================
# Navigation Walkthrough Tests
# =============================================================================


class TestNavigationWalkthrough:
    """Test navigation walkthrough generation."""

    def test_navigate_to_dashboard(self, sample_schema):
        wt = generate_navigation_walkthrough(
            sample_schema, "https://app.example.com/dashboard"
        )
        assert wt.walkthrough_type == WalkthroughType.NAVIGATION
        assert len(wt.steps) >= 1
        assert "Dashboard" in wt.title

    def test_navigate_to_nested_page(self, sample_schema):
        wt = generate_navigation_walkthrough(
            sample_schema, "https://app.example.com/servers/add"
        )
        assert len(wt.steps) >= 1
        # Should include at least the target page
        urls = [s.page_url for s in wt.steps]
        assert "https://app.example.com/servers/add" in urls

    def test_navigate_to_unknown_page(self, sample_schema):
        wt = generate_navigation_walkthrough(
            sample_schema, "https://app.example.com/nonexistent"
        )
        assert len(wt.steps) >= 1
        assert wt.walkthrough_type == WalkthroughType.NAVIGATION

    def test_navigation_has_source_crawl(self, sample_schema):
        wt = generate_navigation_walkthrough(
            sample_schema, "https://app.example.com/dashboard"
        )
        assert wt.source_crawl_id == "wt-test"


# =============================================================================
# Task Walkthrough Tests
# =============================================================================


class TestTaskWalkthrough:
    """Test task-based walkthrough generation."""

    def test_task_add_server(self, sample_schema):
        wt = generate_task_walkthrough(sample_schema, "add a new server")
        assert wt.walkthrough_type == WalkthroughType.TASK
        assert len(wt.steps) >= 1
        # Should find the Add Server page
        urls = [s.page_url for s in wt.steps if s.page_url]
        assert any("servers/add" in u for u in urls)

    def test_task_change_settings(self, sample_schema):
        wt = generate_task_walkthrough(sample_schema, "change settings timezone")
        assert len(wt.steps) >= 1

    def test_task_no_match(self, sample_schema):
        wt = generate_task_walkthrough(sample_schema, "zzz nonexistent task zzz")
        assert len(wt.steps) >= 1
        # Should have a "no match" message
        assert "No matching" in wt.steps[0].instruction

    def test_task_includes_form_steps(self, sample_schema):
        wt = generate_task_walkthrough(sample_schema, "add server hostname")
        # Should include form field steps if the add server page matches
        has_field_step = any("Hostname" in s.instruction for s in wt.steps)
        assert has_field_step


# =============================================================================
# Section Walkthrough Tests
# =============================================================================


class TestSectionWalkthrough:
    """Test section/page guide generation."""

    def test_section_dashboard(self, sample_schema):
        wt = generate_section_walkthrough(
            sample_schema, "https://app.example.com/dashboard"
        )
        assert wt.walkthrough_type == WalkthroughType.SECTION
        assert "Dashboard" in wt.title
        # Should document the section and its elements
        assert len(wt.steps) >= 2

    def test_section_settings(self, sample_schema):
        wt = generate_section_walkthrough(
            sample_schema, "https://app.example.com/settings"
        )
        # Should document forms and modals
        instructions = " ".join(s.instruction for s in wt.steps)
        assert "Form:" in instructions or "General Settings" in instructions
        assert "Modal" in instructions

    def test_section_not_found(self, sample_schema):
        wt = generate_section_walkthrough(
            sample_schema, "https://other-domain.com/nonexistent"
        )
        assert "not found" in wt.steps[0].instruction.lower()

    def test_section_empty_page(self, sample_schema):
        wt = generate_section_walkthrough(
            sample_schema, "https://app.example.com/"
        )
        # Home page has no interactive elements (only links)
        assert len(wt.steps) >= 1


# =============================================================================
# Flow Walkthrough Tests
# =============================================================================


class TestFlowWalkthrough:
    """Test flow playback walkthrough generation."""

    def test_flow_add_server(self, sample_schema):
        wt = generate_flow_walkthrough(sample_schema, "add-server-flow")
        assert wt.walkthrough_type == WalkthroughType.FLOW
        assert len(wt.steps) == 3
        assert "Add Server" in wt.steps[0].instruction
        assert "hostname" in wt.steps[1].instruction.lower()
        assert "Create Server" in wt.steps[2].instruction

    def test_flow_not_found(self, sample_schema):
        wt = generate_flow_walkthrough(sample_schema, "nonexistent-flow")
        assert "not found" in wt.steps[0].instruction.lower()


# =============================================================================
# Dispatch Tests
# =============================================================================


class TestWalkthroughDispatch:
    """Test the main generate_walkthrough dispatcher."""

    def test_dispatch_navigation(self, sample_schema):
        wt = generate_walkthrough(
            sample_schema, "https://app.example.com/settings", WalkthroughType.NAVIGATION
        )
        assert wt.walkthrough_type == WalkthroughType.NAVIGATION

    def test_dispatch_task(self, sample_schema):
        wt = generate_walkthrough(
            sample_schema, "add server", WalkthroughType.TASK
        )
        assert wt.walkthrough_type == WalkthroughType.TASK

    def test_dispatch_section(self, sample_schema):
        wt = generate_walkthrough(
            sample_schema, "https://app.example.com/dashboard", WalkthroughType.SECTION
        )
        assert wt.walkthrough_type == WalkthroughType.SECTION

    def test_dispatch_flow(self, sample_schema):
        wt = generate_walkthrough(
            sample_schema, "add-server-flow", WalkthroughType.FLOW
        )
        assert wt.walkthrough_type == WalkthroughType.FLOW


# =============================================================================
# Formatter Tests
# =============================================================================


class TestFormatters:
    """Test Markdown and HTML output formatting."""

    def test_format_markdown(self, sample_schema):
        wt = generate_navigation_walkthrough(
            sample_schema, "https://app.example.com/dashboard"
        )
        md = format_markdown(wt)
        assert "# " in md
        assert "Step 1" in md
        assert "navigation" in md.lower()

    def test_format_markdown_no_screenshots(self, sample_schema):
        wt = generate_navigation_walkthrough(
            sample_schema, "https://app.example.com/dashboard"
        )
        md = format_markdown(wt, include_screenshots=False)
        assert "Screenshot:" not in md

    def test_format_html(self, sample_schema):
        wt = generate_navigation_walkthrough(
            sample_schema, "https://app.example.com/dashboard"
        )
        html = format_html(wt)
        assert "<html>" in html
        assert "Step 1" in html
        assert "<h1>" in html

    def test_format_html_no_screenshots(self, sample_schema):
        wt = generate_navigation_walkthrough(
            sample_schema, "https://app.example.com/dashboard"
        )
        html = format_html(wt, include_screenshots=False)
        assert "Screenshot:" not in html

    def test_format_html_escapes_special_chars(self, sample_schema):
        from src.webgui.walkthrough.formatters import _html_escape

        assert _html_escape("<script>") == "&lt;script&gt;"
        assert _html_escape('"test"') == "&quot;test&quot;"
        assert _html_escape("a & b") == "a &amp; b"
