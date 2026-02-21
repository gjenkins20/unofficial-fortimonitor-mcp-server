"""Versioned JSON schema storage.

Saves, loads, lists, and searches crawl schemas stored as JSON files.
Storage location: data/webgui/schemas/{crawl_id}.json
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..models import UISchema

logger = logging.getLogger(__name__)


class SchemaStore:
    """File-based storage for versioned UI schemas."""

    def __init__(self, base_dir: str = "data/webgui/schemas"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _schema_path(self, crawl_id: str) -> Path:
        """Get the file path for a crawl schema."""
        return self.base_dir / f"{crawl_id}.json"

    def save(self, schema: UISchema) -> Path:
        """Save a schema to disk. Returns the file path."""
        path = self._schema_path(schema.crawl_metadata.crawl_id)
        data = schema.model_dump(mode="json")
        path.write_text(json.dumps(data, indent=2, default=str))
        logger.info(f"Saved schema {schema.crawl_metadata.crawl_id} to {path}")
        return path

    def load(self, crawl_id: str) -> Optional[UISchema]:
        """Load a schema by crawl ID. Returns None if not found."""
        path = self._schema_path(crawl_id)
        if not path.exists():
            logger.warning(f"Schema not found: {crawl_id}")
            return None
        try:
            data = json.loads(path.read_text())
            return UISchema.model_validate(data)
        except Exception as e:
            logger.error(f"Error loading schema {crawl_id}: {e}")
            return None

    def list_schemas(self) -> List[Dict]:
        """List all stored schemas with summary info."""
        schemas = []
        for path in sorted(self.base_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(path.read_text())
                meta = data.get("crawl_metadata", {})
                schemas.append({
                    "crawl_id": meta.get("crawl_id", path.stem),
                    "target_url": meta.get("target_url", ""),
                    "application_name": meta.get("application_name", ""),
                    "started_at": meta.get("started_at"),
                    "completed_at": meta.get("completed_at"),
                    "total_pages": meta.get("total_pages", 0),
                    "total_elements": meta.get("total_elements", 0),
                })
            except Exception as e:
                logger.warning(f"Error reading schema file {path}: {e}")
        return schemas

    def get_latest_crawl_id(self) -> Optional[str]:
        """Get the most recent crawl ID."""
        schemas = self.list_schemas()
        return schemas[0]["crawl_id"] if schemas else None

    def delete(self, crawl_id: str) -> bool:
        """Delete a schema. Returns True if deleted."""
        path = self._schema_path(crawl_id)
        if path.exists():
            path.unlink()
            logger.info(f"Deleted schema {crawl_id}")
            return True
        return False

    def search_pages(self, crawl_id: str, query: str) -> List[Dict]:
        """Search pages in a schema by URL, title, or breadcrumb substring match."""
        schema = self.load(crawl_id)
        if not schema:
            return []

        query_lower = query.lower()
        results = []
        for url, page in schema.pages.items():
            matches = (
                query_lower in url.lower()
                or query_lower in page.title.lower()
                or any(query_lower in b.lower() for b in page.breadcrumbs)
            )
            if matches:
                results.append({
                    "page_id": page.page_id,
                    "url": page.url,
                    "title": page.title,
                    "breadcrumbs": page.breadcrumbs,
                    "element_count": page.element_count,
                })
        return results

    def search_elements(self, crawl_id: str, query: str) -> List[Dict]:
        """Search elements across all pages by label or type."""
        schema = self.load(crawl_id)
        if not schema:
            return []

        query_lower = query.lower()
        results = []
        for url, page in schema.pages.items():
            for section in page.sections:
                for elem in section.elements:
                    if (
                        query_lower in elem.label.lower()
                        or query_lower in elem.type.value.lower()
                    ):
                        results.append({
                            "page_url": url,
                            "page_title": page.title,
                            "element_id": elem.element_id,
                            "type": elem.type.value,
                            "label": elem.label,
                            "selector": elem.selector,
                        })
        return results

    def search_forms(self, crawl_id: str, query: str) -> List[Dict]:
        """Search forms across all pages by title or field labels."""
        schema = self.load(crawl_id)
        if not schema:
            return []

        query_lower = query.lower()
        results = []
        for url, page in schema.pages.items():
            for form in page.forms:
                form_matches = query_lower in form.title.lower()
                field_matches = any(
                    query_lower in f.label.lower() for f in form.fields
                )
                if form_matches or field_matches:
                    results.append({
                        "page_url": url,
                        "page_title": page.title,
                        "form_id": form.form_id,
                        "form_title": form.title,
                        "field_count": len(form.fields),
                    })
        return results

    def search_modals(self, crawl_id: str, query: str) -> List[Dict]:
        """Search modals across all pages by title."""
        schema = self.load(crawl_id)
        if not schema:
            return []

        query_lower = query.lower()
        results = []
        for url, page in schema.pages.items():
            for modal in page.modals:
                if query_lower in modal.title.lower():
                    results.append({
                        "page_url": url,
                        "page_title": page.title,
                        "modal_id": modal.modal_id,
                        "modal_title": modal.title,
                        "element_count": len(modal.elements),
                    })
        return results

    def search_flows(self, crawl_id: str, query: str) -> List[Dict]:
        """Search flows by name or step descriptions."""
        schema = self.load(crawl_id)
        if not schema:
            return []

        query_lower = query.lower()
        results = []
        for flow in schema.flows:
            name_match = query_lower in flow.name.lower()
            step_match = any(
                query_lower in s.description.lower() for s in flow.steps
            )
            if name_match or step_match:
                results.append({
                    "flow_id": flow.flow_id,
                    "name": flow.name,
                    "step_count": len(flow.steps),
                })
        return results
