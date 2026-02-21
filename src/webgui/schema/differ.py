"""Schema version comparison.

Compares two UISchema versions and reports added, removed, and modified
pages and elements.
"""

import logging
from typing import List, Optional

from ..models import DiffScope, PageDiff, SchemaDiff, UIPage, UISchema

logger = logging.getLogger(__name__)


def _compare_pages(old_page: UIPage, new_page: UIPage) -> List[str]:
    """Compare two versions of the same page. Returns list of change descriptions."""
    changes = []

    if old_page.title != new_page.title:
        changes.append(f"Title changed: '{old_page.title}' -> '{new_page.title}'")

    # Compare section element counts
    old_elem_count = old_page.element_count
    new_elem_count = new_page.element_count
    if old_elem_count != new_elem_count:
        diff = new_elem_count - old_elem_count
        direction = "added" if diff > 0 else "removed"
        changes.append(f"{abs(diff)} element(s) {direction} (was {old_elem_count}, now {new_elem_count})")

    # Compare form counts
    old_forms = len(old_page.forms)
    new_forms = len(new_page.forms)
    if old_forms != new_forms:
        diff = new_forms - old_forms
        direction = "added" if diff > 0 else "removed"
        changes.append(f"{abs(diff)} form(s) {direction}")

    # Compare modal counts
    old_modals = len(old_page.modals)
    new_modals = len(new_page.modals)
    if old_modals != new_modals:
        diff = new_modals - old_modals
        direction = "added" if diff > 0 else "removed"
        changes.append(f"{abs(diff)} modal(s) {direction}")

    # Compare link counts
    old_links = len(old_page.links)
    new_links = len(new_page.links)
    if old_links != new_links:
        diff = new_links - old_links
        direction = "added" if diff > 0 else "removed"
        changes.append(f"{abs(diff)} link(s) {direction}")

    # Compare section headings
    old_headings = {s.heading for s in old_page.sections}
    new_headings = {s.heading for s in new_page.sections}
    added_sections = new_headings - old_headings
    removed_sections = old_headings - new_headings
    for h in added_sections:
        changes.append(f"Section added: '{h}'")
    for h in removed_sections:
        changes.append(f"Section removed: '{h}'")

    # Detailed element comparison
    if DiffScope.ELEMENTS:
        old_labels = set()
        for s in old_page.sections:
            for e in s.elements:
                old_labels.add((e.type.value, e.label))
        new_labels = set()
        for s in new_page.sections:
            for e in s.elements:
                new_labels.add((e.type.value, e.label))

        for etype, label in new_labels - old_labels:
            changes.append(f"Element added: {etype} '{label}'")
        for etype, label in old_labels - new_labels:
            changes.append(f"Element removed: {etype} '{label}'")

    return changes


def compare_schemas(
    old_schema: UISchema,
    new_schema: UISchema,
    scope: DiffScope = DiffScope.FULL,
) -> SchemaDiff:
    """Compare two schema versions and return a SchemaDiff.

    Args:
        old_schema: The older schema version.
        new_schema: The newer schema version.
        scope: Level of detail for the comparison.

    Returns:
        SchemaDiff with added, removed, and modified pages.
    """
    old_urls = set(old_schema.pages.keys())
    new_urls = set(new_schema.pages.keys())

    pages_added = sorted(new_urls - old_urls)
    pages_removed = sorted(old_urls - new_urls)

    pages_modified = []
    if scope in (DiffScope.PAGES, DiffScope.ELEMENTS, DiffScope.FULL):
        common_urls = old_urls & new_urls
        for url in sorted(common_urls):
            changes = _compare_pages(old_schema.pages[url], new_schema.pages[url])
            if changes:
                pages_modified.append(
                    PageDiff(
                        page_url=url,
                        change_type="modified",
                        details=changes,
                    )
                )

    # Build summary
    parts = []
    if pages_added:
        parts.append(f"{len(pages_added)} page(s) added")
    if pages_removed:
        parts.append(f"{len(pages_removed)} page(s) removed")
    if pages_modified:
        parts.append(f"{len(pages_modified)} page(s) modified")
    if not parts:
        parts.append("No changes detected")
    summary = ", ".join(parts)

    return SchemaDiff(
        crawl_id_old=old_schema.crawl_metadata.crawl_id,
        crawl_id_new=new_schema.crawl_metadata.crawl_id,
        pages_added=pages_added,
        pages_removed=pages_removed,
        pages_modified=pages_modified,
        summary=summary,
    )
