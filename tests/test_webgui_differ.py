"""Tests for WebGUI schema differ.

Tests that diffs correctly detect added, removed, and modified pages.
"""

import pytest

from src.webgui.models import (
    CrawlMetadata,
    DiffScope,
    ElementType,
    UIElement,
    UIForm,
    UIFormField,
    UILink,
    UIModal,
    UIPage,
    UISchema,
    UISection,
)
from src.webgui.schema.differ import compare_schemas


@pytest.fixture
def base_schema():
    """Create a base schema for diff testing."""
    return UISchema(
        crawl_metadata=CrawlMetadata(
            crawl_id="old-crawl",
            target_url="https://app.example.com",
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
                            UIElement(element_id="e1", type=ElementType.BUTTON, label="Refresh"),
                            UIElement(element_id="e2", type=ElementType.TABLE, label="Status"),
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
                        form_id="f1",
                        title="General",
                        fields=[
                            UIFormField(field_id="ff1", label="Name", type=ElementType.INPUT),
                        ],
                    )
                ],
            ),
            "/old-page": UIPage(
                page_id="old-page",
                url="/old-page",
                title="Old Page",
            ),
        },
    )


class TestSchemaComparison:
    """Test schema diff operations."""

    def test_no_changes(self, base_schema):
        diff = compare_schemas(base_schema, base_schema)
        assert diff.pages_added == []
        assert diff.pages_removed == []
        assert diff.pages_modified == []
        assert "No changes" in diff.summary

    def test_page_added(self, base_schema):
        new_schema = base_schema.model_copy(deep=True)
        new_schema.crawl_metadata.crawl_id = "new-crawl"
        new_schema.pages["/new-page"] = UIPage(
            page_id="new-page", url="/new-page", title="New Page"
        )

        diff = compare_schemas(base_schema, new_schema)
        assert "/new-page" in diff.pages_added
        assert "1 page(s) added" in diff.summary

    def test_page_removed(self, base_schema):
        new_schema = base_schema.model_copy(deep=True)
        new_schema.crawl_metadata.crawl_id = "new-crawl"
        del new_schema.pages["/old-page"]

        diff = compare_schemas(base_schema, new_schema)
        assert "/old-page" in diff.pages_removed
        assert "1 page(s) removed" in diff.summary

    def test_page_title_changed(self, base_schema):
        new_schema = base_schema.model_copy(deep=True)
        new_schema.crawl_metadata.crawl_id = "new-crawl"
        new_schema.pages["/dashboard"].title = "Main Dashboard"

        diff = compare_schemas(base_schema, new_schema)
        assert len(diff.pages_modified) == 1
        mod = diff.pages_modified[0]
        assert mod.page_url == "/dashboard"
        assert any("Title changed" in d for d in mod.details)

    def test_elements_added(self, base_schema):
        new_schema = base_schema.model_copy(deep=True)
        new_schema.crawl_metadata.crawl_id = "new-crawl"
        new_schema.pages["/dashboard"].sections[0].elements.append(
            UIElement(element_id="e3", type=ElementType.INPUT, label="Search")
        )

        diff = compare_schemas(base_schema, new_schema)
        assert len(diff.pages_modified) >= 1
        mod = next(m for m in diff.pages_modified if m.page_url == "/dashboard")
        assert any("element" in d.lower() for d in mod.details)

    def test_elements_removed(self, base_schema):
        new_schema = base_schema.model_copy(deep=True)
        new_schema.crawl_metadata.crawl_id = "new-crawl"
        new_schema.pages["/dashboard"].sections[0].elements.pop()

        diff = compare_schemas(base_schema, new_schema)
        assert len(diff.pages_modified) >= 1

    def test_form_added(self, base_schema):
        new_schema = base_schema.model_copy(deep=True)
        new_schema.crawl_metadata.crawl_id = "new-crawl"
        new_schema.pages["/dashboard"].forms.append(
            UIForm(
                form_id="f2",
                title="Filter",
                fields=[UIFormField(field_id="ff2", label="Query", type=ElementType.INPUT)],
            )
        )

        diff = compare_schemas(base_schema, new_schema)
        mod = next(m for m in diff.pages_modified if m.page_url == "/dashboard")
        assert any("form" in d.lower() for d in mod.details)

    def test_modal_added(self, base_schema):
        new_schema = base_schema.model_copy(deep=True)
        new_schema.crawl_metadata.crawl_id = "new-crawl"
        new_schema.pages["/settings"].modals.append(
            UIModal(modal_id="m1", title="Confirm")
        )

        diff = compare_schemas(base_schema, new_schema)
        mod = next(m for m in diff.pages_modified if m.page_url == "/settings")
        assert any("modal" in d.lower() for d in mod.details)

    def test_combined_changes(self, base_schema):
        new_schema = base_schema.model_copy(deep=True)
        new_schema.crawl_metadata.crawl_id = "new-crawl"

        # Add a page
        new_schema.pages["/new"] = UIPage(page_id="new", url="/new", title="New")
        # Remove a page
        del new_schema.pages["/old-page"]
        # Modify a page
        new_schema.pages["/dashboard"].title = "Updated Dashboard"

        diff = compare_schemas(base_schema, new_schema)
        assert len(diff.pages_added) == 1
        assert len(diff.pages_removed) == 1
        assert len(diff.pages_modified) >= 1
        assert "added" in diff.summary
        assert "removed" in diff.summary
        assert "modified" in diff.summary

    def test_summary_scope(self, base_schema):
        new_schema = base_schema.model_copy(deep=True)
        new_schema.crawl_metadata.crawl_id = "new-crawl"
        new_schema.pages["/dashboard"].title = "Changed"

        diff = compare_schemas(base_schema, new_schema, scope=DiffScope.SUMMARY)
        # Summary scope doesn't detect page modifications (only added/removed)
        assert diff.crawl_id_old == "old-crawl"
        assert diff.crawl_id_new == "new-crawl"

    def test_section_heading_changes(self, base_schema):
        new_schema = base_schema.model_copy(deep=True)
        new_schema.crawl_metadata.crawl_id = "new-crawl"
        new_schema.pages["/dashboard"].sections[0].heading = "Summary"

        diff = compare_schemas(base_schema, new_schema)
        mod = next(m for m in diff.pages_modified if m.page_url == "/dashboard")
        assert any("Section added" in d or "Section removed" in d for d in mod.details)
