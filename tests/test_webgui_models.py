"""Tests for WebGUI Pydantic models.

Verifies model creation, serialization round-trip, and computed properties.
"""

import json
from datetime import datetime

import pytest

from src.webgui.models import (
    CrawlMetadata,
    CrawlProgress,
    CrawlStatus,
    DiffScope,
    ElementType,
    FlowStep,
    LinkType,
    NavNode,
    PageDiff,
    SchemaDiff,
    UIElement,
    UIFlow,
    UIForm,
    UIFormField,
    UILink,
    UIModal,
    UIPage,
    UISchema,
    UISection,
    Walkthrough,
    WalkthroughStep,
    WalkthroughType,
)


class TestEnums:
    """Test enum values are correct."""

    def test_element_types(self):
        assert ElementType.BUTTON == "button"
        assert ElementType.INPUT == "input"
        assert ElementType.TABLE == "table"
        assert ElementType.DROPDOWN == "dropdown"

    def test_link_types(self):
        assert LinkType.NAVIGATION == "navigation"
        assert LinkType.EXTERNAL == "external"

    def test_crawl_status(self):
        assert CrawlStatus.PENDING == "pending"
        assert CrawlStatus.RUNNING == "running"
        assert CrawlStatus.COMPLETED == "completed"
        assert CrawlStatus.FAILED == "failed"

    def test_walkthrough_types(self):
        assert WalkthroughType.NAVIGATION == "navigation"
        assert WalkthroughType.TASK == "task"

    def test_diff_scope(self):
        assert DiffScope.SUMMARY == "summary"
        assert DiffScope.FULL == "full"


class TestUIElement:
    """Test UIElement model."""

    def test_create_basic_element(self):
        elem = UIElement(
            element_id="btn-1",
            type=ElementType.BUTTON,
            label="Save",
            selector="#save-btn",
        )
        assert elem.element_id == "btn-1"
        assert elem.type == ElementType.BUTTON
        assert elem.label == "Save"
        assert elem.children == []

    def test_element_with_children(self):
        child = UIElement(element_id="opt-1", type=ElementType.MENU_ITEM, label="Option 1")
        parent = UIElement(
            element_id="dropdown-1",
            type=ElementType.DROPDOWN,
            label="Menu",
            children=[child],
        )
        assert len(parent.children) == 1
        assert parent.children[0].label == "Option 1"

    def test_element_with_attributes(self):
        elem = UIElement(
            element_id="input-1",
            type=ElementType.INPUT,
            label="Email",
            attributes={"placeholder": "user@example.com", "required": True},
        )
        assert elem.attributes["placeholder"] == "user@example.com"
        assert elem.attributes["required"] is True

    def test_element_serialization_roundtrip(self):
        elem = UIElement(
            element_id="test-1",
            type=ElementType.CHECKBOX,
            label="Agree",
            position={"x": 10, "y": 20, "width": 100, "height": 30},
        )
        data = elem.model_dump(mode="json")
        restored = UIElement.model_validate(data)
        assert restored.element_id == elem.element_id
        assert restored.type == elem.type
        assert restored.position == elem.position


class TestUIForm:
    """Test UIForm and UIFormField models."""

    def test_create_form(self):
        field = UIFormField(
            field_id="f-1",
            label="Username",
            type=ElementType.INPUT,
            required=True,
            placeholder="Enter username",
        )
        submit = UIElement(
            element_id="submit-1", type=ElementType.BUTTON, label="Login"
        )
        form = UIForm(
            form_id="login-form",
            title="Login",
            fields=[field],
            submit_button=submit,
        )
        assert form.form_id == "login-form"
        assert len(form.fields) == 1
        assert form.fields[0].required is True
        assert form.submit_button.label == "Login"

    def test_form_field_with_options(self):
        field = UIFormField(
            field_id="role-select",
            label="Role",
            type=ElementType.SELECT,
            options=["Admin", "User", "Guest"],
        )
        assert len(field.options) == 3


class TestUIModal:
    """Test UIModal model."""

    def test_create_modal(self):
        modal = UIModal(
            modal_id="confirm-delete",
            title="Confirm Delete",
            trigger_element="btn-delete",
            elements=[
                UIElement(element_id="ok-btn", type=ElementType.BUTTON, label="OK"),
                UIElement(
                    element_id="cancel-btn", type=ElementType.BUTTON, label="Cancel"
                ),
            ],
        )
        assert modal.modal_id == "confirm-delete"
        assert len(modal.elements) == 2


class TestUIPage:
    """Test UIPage model."""

    def test_create_page(self):
        page = UIPage(
            page_id="dashboard",
            url="https://app.example.com/dashboard",
            title="Dashboard",
            breadcrumbs=["Home", "Dashboard"],
        )
        assert page.page_id == "dashboard"
        assert page.element_count == 0

    def test_page_element_count(self):
        page = UIPage(
            page_id="settings",
            url="https://app.example.com/settings",
            title="Settings",
            sections=[
                UISection(
                    heading="General",
                    elements=[
                        UIElement(element_id="e1", type=ElementType.INPUT, label="Name"),
                        UIElement(element_id="e2", type=ElementType.INPUT, label="Email"),
                    ],
                )
            ],
            forms=[
                UIForm(
                    form_id="f1",
                    title="Profile",
                    fields=[
                        UIFormField(field_id="ff1", label="Bio", type=ElementType.TEXTAREA)
                    ],
                )
            ],
            modals=[
                UIModal(
                    modal_id="m1",
                    title="Confirm",
                    elements=[
                        UIElement(element_id="e3", type=ElementType.BUTTON, label="OK")
                    ],
                )
            ],
        )
        # 2 section elements + 1 form field + 1 modal element
        assert page.element_count == 4

    def test_page_serialization_roundtrip(self):
        page = UIPage(
            page_id="test",
            url="https://example.com/test",
            title="Test Page",
            links=[UILink(text="Home", url="/", type=LinkType.NAVIGATION)],
        )
        data = json.loads(json.dumps(page.model_dump(mode="json")))
        restored = UIPage.model_validate(data)
        assert restored.page_id == "test"
        assert len(restored.links) == 1
        assert restored.links[0].type == LinkType.NAVIGATION


class TestNavNode:
    """Test NavNode tree model."""

    def test_nested_nav_tree(self):
        tree = NavNode(
            label="Root",
            url="/",
            children=[
                NavNode(label="Dashboard", url="/dashboard"),
                NavNode(
                    label="Settings",
                    url="/settings",
                    children=[
                        NavNode(label="General", url="/settings/general"),
                        NavNode(label="Security", url="/settings/security"),
                    ],
                ),
            ],
        )
        assert len(tree.children) == 2
        assert len(tree.children[1].children) == 2
        assert tree.children[1].children[0].label == "General"


class TestUIFlow:
    """Test UIFlow and FlowStep models."""

    def test_create_flow(self):
        flow = UIFlow(
            flow_id="add-server",
            name="Add a New Server",
            steps=[
                FlowStep(
                    step_number=1,
                    page_url="/servers",
                    action="click",
                    target="#add-btn",
                    description="Click the Add Server button",
                ),
                FlowStep(
                    step_number=2,
                    page_url="/servers/new",
                    action="fill",
                    target="#hostname",
                    description="Enter the server hostname",
                ),
            ],
        )
        assert flow.flow_id == "add-server"
        assert len(flow.steps) == 2
        assert flow.steps[0].action == "click"


class TestCrawlModels:
    """Test CrawlMetadata and CrawlProgress models."""

    def test_crawl_metadata(self):
        meta = CrawlMetadata(
            crawl_id="crawl-001",
            target_url="https://app.example.com",
            application_name="MyApp",
            started_at=datetime(2025, 1, 15, 10, 0, 0),
            total_pages=25,
            total_elements=150,
        )
        assert meta.crawl_id == "crawl-001"
        assert meta.total_pages == 25

    def test_crawl_progress(self):
        progress = CrawlProgress(
            crawl_id="crawl-001",
            status=CrawlStatus.RUNNING,
            pages_discovered=30,
            pages_crawled=15,
            pages_remaining=15,
            current_page="https://app.example.com/settings",
        )
        assert progress.status == CrawlStatus.RUNNING
        assert progress.pages_remaining == 15


class TestUISchema:
    """Test top-level UISchema model."""

    def test_create_full_schema(self):
        schema = UISchema(
            schema_version="1.0.0",
            crawl_metadata=CrawlMetadata(
                crawl_id="crawl-001",
                target_url="https://app.example.com",
                application_name="TestApp",
                total_pages=2,
            ),
            navigation_tree=NavNode(
                label="Root",
                url="/",
                children=[NavNode(label="Home", url="/home")],
            ),
            pages={
                "/home": UIPage(page_id="home", url="/home", title="Home"),
                "/about": UIPage(page_id="about", url="/about", title="About"),
            },
            flows=[
                UIFlow(flow_id="f1", name="Login Flow", steps=[]),
            ],
        )
        assert schema.schema_version == "1.0.0"
        assert len(schema.pages) == 2
        assert len(schema.flows) == 1

    def test_schema_json_roundtrip(self):
        schema = UISchema(
            crawl_metadata=CrawlMetadata(
                crawl_id="roundtrip-test",
                target_url="https://example.com",
            ),
            pages={
                "/": UIPage(
                    page_id="root",
                    url="/",
                    title="Root",
                    sections=[
                        UISection(
                            heading="Main",
                            elements=[
                                UIElement(
                                    element_id="e1",
                                    type=ElementType.BUTTON,
                                    label="Click Me",
                                )
                            ],
                        )
                    ],
                )
            },
        )
        json_str = json.dumps(schema.model_dump(mode="json"), default=str)
        data = json.loads(json_str)
        restored = UISchema.model_validate(data)
        assert restored.crawl_metadata.crawl_id == "roundtrip-test"
        assert len(restored.pages["/"]. sections) == 1
        assert restored.pages["/"].sections[0].elements[0].label == "Click Me"

    def test_empty_schema(self):
        schema = UISchema(
            crawl_metadata=CrawlMetadata(
                crawl_id="empty",
                target_url="https://example.com",
            ),
        )
        assert schema.pages == {}
        assert schema.flows == []
        assert schema.navigation_tree is None


class TestWalkthroughModels:
    """Test Walkthrough and WalkthroughStep models."""

    def test_create_walkthrough(self):
        wt = Walkthrough(
            title="How to Add a Server",
            walkthrough_type=WalkthroughType.TASK,
            description="Step-by-step guide to adding a new server",
            steps=[
                WalkthroughStep(
                    step_number=1,
                    instruction="Navigate to the Servers page",
                    page_url="/servers",
                ),
                WalkthroughStep(
                    step_number=2,
                    instruction="Click the 'Add Server' button",
                    page_url="/servers",
                    element_ref="btn-add",
                    note="The button is in the top-right corner",
                ),
            ],
            source_crawl_id="crawl-001",
        )
        assert wt.walkthrough_type == WalkthroughType.TASK
        assert len(wt.steps) == 2


class TestDiffModels:
    """Test SchemaDiff and PageDiff models."""

    def test_create_diff(self):
        diff = SchemaDiff(
            crawl_id_old="crawl-001",
            crawl_id_new="crawl-002",
            pages_added=["/new-page"],
            pages_removed=["/old-page"],
            pages_modified=[
                PageDiff(
                    page_url="/settings",
                    change_type="modified",
                    details=["Added 2 new form fields", "Removed 'Legacy' section"],
                )
            ],
            summary="1 page added, 1 page removed, 1 page modified",
        )
        assert len(diff.pages_added) == 1
        assert len(diff.pages_removed) == 1
        assert len(diff.pages_modified) == 1
        assert diff.pages_modified[0].change_type == "modified"
