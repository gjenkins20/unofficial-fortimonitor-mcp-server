"""Tests for WebGUI schema store.

Tests CRUD operations, search, and listing of stored schemas.
"""

import json

import pytest

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
)
from src.webgui.schema.store import SchemaStore


@pytest.fixture
def store(tmp_path):
    """Create a SchemaStore backed by a temp directory."""
    return SchemaStore(base_dir=str(tmp_path / "schemas"))


@pytest.fixture
def sample_schema():
    """Create a sample UISchema for testing."""
    return UISchema(
        crawl_metadata=CrawlMetadata(
            crawl_id="test-crawl-001",
            target_url="https://app.example.com",
            application_name="TestApp",
            total_pages=3,
            total_elements=10,
        ),
        pages={
            "/dashboard": UIPage(
                page_id="dashboard",
                url="/dashboard",
                title="Dashboard",
                breadcrumbs=["Home", "Dashboard"],
                sections=[
                    UISection(
                        heading="Overview",
                        elements=[
                            UIElement(
                                element_id="e1",
                                type=ElementType.BUTTON,
                                label="Refresh Data",
                            ),
                            UIElement(
                                element_id="e2",
                                type=ElementType.TABLE,
                                label="Server Status",
                            ),
                        ],
                    )
                ],
                links=[UILink(text="Settings", url="/settings", type=LinkType.NAVIGATION)],
            ),
            "/settings": UIPage(
                page_id="settings",
                url="/settings",
                title="Settings",
                breadcrumbs=["Home", "Settings"],
                forms=[
                    UIForm(
                        form_id="general-form",
                        title="General Settings",
                        fields=[
                            UIFormField(
                                field_id="f1",
                                label="Site Name",
                                type=ElementType.INPUT,
                                required=True,
                            ),
                            UIFormField(
                                field_id="f2",
                                label="Timezone",
                                type=ElementType.SELECT,
                                options=["UTC", "US/Eastern", "US/Pacific"],
                            ),
                        ],
                    )
                ],
                modals=[
                    UIModal(
                        modal_id="confirm-save",
                        title="Save Changes?",
                        elements=[
                            UIElement(
                                element_id="e3",
                                type=ElementType.BUTTON,
                                label="Confirm",
                            )
                        ],
                    )
                ],
            ),
            "/servers": UIPage(
                page_id="servers",
                url="/servers",
                title="Server Management",
                breadcrumbs=["Home", "Servers"],
            ),
        },
        flows=[
            UIFlow(
                flow_id="add-server-flow",
                name="Add a New Server",
                steps=[],
            )
        ],
    )


class TestSchemaStoreCRUD:
    """Test basic CRUD operations."""

    def test_save_and_load(self, store, sample_schema):
        path = store.save(sample_schema)
        assert path.exists()

        loaded = store.load("test-crawl-001")
        assert loaded is not None
        assert loaded.crawl_metadata.crawl_id == "test-crawl-001"
        assert len(loaded.pages) == 3

    def test_load_nonexistent(self, store):
        result = store.load("nonexistent")
        assert result is None

    def test_delete(self, store, sample_schema):
        store.save(sample_schema)
        assert store.delete("test-crawl-001") is True
        assert store.load("test-crawl-001") is None

    def test_delete_nonexistent(self, store):
        assert store.delete("nonexistent") is False

    def test_list_schemas(self, store, sample_schema):
        store.save(sample_schema)

        # Save a second schema
        schema2 = UISchema(
            crawl_metadata=CrawlMetadata(
                crawl_id="test-crawl-002",
                target_url="https://other.example.com",
                application_name="OtherApp",
                total_pages=1,
            ),
            pages={},
        )
        store.save(schema2)

        schemas = store.list_schemas()
        assert len(schemas) == 2
        crawl_ids = {s["crawl_id"] for s in schemas}
        assert "test-crawl-001" in crawl_ids
        assert "test-crawl-002" in crawl_ids

    def test_list_empty(self, store):
        assert store.list_schemas() == []

    def test_get_latest_crawl_id(self, store, sample_schema):
        store.save(sample_schema)
        latest = store.get_latest_crawl_id()
        assert latest == "test-crawl-001"

    def test_get_latest_crawl_id_empty(self, store):
        assert store.get_latest_crawl_id() is None

    def test_save_preserves_all_data(self, store, sample_schema):
        store.save(sample_schema)
        loaded = store.load("test-crawl-001")

        # Check pages
        assert "/dashboard" in loaded.pages
        assert "/settings" in loaded.pages
        assert "/servers" in loaded.pages

        # Check elements
        dashboard = loaded.pages["/dashboard"]
        assert len(dashboard.sections) == 1
        assert len(dashboard.sections[0].elements) == 2

        # Check forms
        settings = loaded.pages["/settings"]
        assert len(settings.forms) == 1
        assert len(settings.forms[0].fields) == 2

        # Check modals
        assert len(settings.modals) == 1
        assert settings.modals[0].title == "Save Changes?"

        # Check flows
        assert len(loaded.flows) == 1
        assert loaded.flows[0].name == "Add a New Server"


class TestSchemaStoreSearch:
    """Test search operations."""

    def test_search_pages_by_url(self, store, sample_schema):
        store.save(sample_schema)
        results = store.search_pages("test-crawl-001", "dashboard")
        assert len(results) == 1
        assert results[0]["url"] == "/dashboard"

    def test_search_pages_by_title(self, store, sample_schema):
        store.save(sample_schema)
        results = store.search_pages("test-crawl-001", "Server Management")
        assert len(results) == 1
        assert results[0]["page_id"] == "servers"

    def test_search_pages_by_breadcrumb(self, store, sample_schema):
        store.save(sample_schema)
        results = store.search_pages("test-crawl-001", "Settings")
        assert len(results) == 1
        assert results[0]["url"] == "/settings"

    def test_search_pages_case_insensitive(self, store, sample_schema):
        store.save(sample_schema)
        results = store.search_pages("test-crawl-001", "DASHBOARD")
        assert len(results) == 1

    def test_search_pages_no_match(self, store, sample_schema):
        store.save(sample_schema)
        results = store.search_pages("test-crawl-001", "nonexistent")
        assert len(results) == 0

    def test_search_pages_nonexistent_crawl(self, store):
        results = store.search_pages("nonexistent", "test")
        assert results == []

    def test_search_elements(self, store, sample_schema):
        store.save(sample_schema)
        results = store.search_elements("test-crawl-001", "Refresh")
        assert len(results) == 1
        assert results[0]["label"] == "Refresh Data"
        assert results[0]["type"] == "button"

    def test_search_elements_by_type(self, store, sample_schema):
        store.save(sample_schema)
        results = store.search_elements("test-crawl-001", "table")
        assert len(results) == 1
        assert results[0]["label"] == "Server Status"

    def test_search_forms(self, store, sample_schema):
        store.save(sample_schema)
        results = store.search_forms("test-crawl-001", "General")
        assert len(results) == 1
        assert results[0]["form_title"] == "General Settings"

    def test_search_forms_by_field(self, store, sample_schema):
        store.save(sample_schema)
        results = store.search_forms("test-crawl-001", "Timezone")
        assert len(results) == 1

    def test_search_modals(self, store, sample_schema):
        store.save(sample_schema)
        results = store.search_modals("test-crawl-001", "Save")
        assert len(results) == 1
        assert results[0]["modal_title"] == "Save Changes?"

    def test_search_flows(self, store, sample_schema):
        store.save(sample_schema)
        results = store.search_flows("test-crawl-001", "server")
        assert len(results) == 1
        assert results[0]["flow_id"] == "add-server-flow"

    def test_search_flows_no_match(self, store, sample_schema):
        store.save(sample_schema)
        results = store.search_flows("test-crawl-001", "nonexistent")
        assert len(results) == 0
