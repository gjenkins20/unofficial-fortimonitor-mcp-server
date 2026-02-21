"""Workflow store for WebGUI walkthrough definitions.

Lazy-loads workflow YAML and provides list/get/search operations.
Each workflow is a sequence of steps referencing crawled WebGUI pages.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .store import SchemaStore

logger = logging.getLogger(__name__)


class WorkflowStore:
    """Read-only store for WebGUI workflow definitions.

    Loads workflow YAML lazily on first access and enriches steps
    with page metadata from the SchemaStore.
    """

    def __init__(self, workflows_file: Path, schema_store: SchemaStore):
        self._file = Path(workflows_file)
        self._schema_store = schema_store
        self._data: Optional[Dict] = None

    def _ensure_loaded(self) -> None:
        """Load YAML on first access. Logs warnings for unresolvable page_ids."""
        if self._data is not None:
            return

        if not self._file.exists():
            logger.warning("Workflows file not found: %s", self._file)
            self._data = {}
            return

        logger.info("Loading workflows from %s", self._file)
        with open(self._file, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        self._data = raw.get("workflows", {}) if raw else {}

        # Validate that step page_ids exist in schema
        for wf_id, wf in self._data.items():
            for i, step in enumerate(wf.get("steps", [])):
                page_id = step.get("page_id")
                if page_id:
                    page = self._schema_store.get_page(page_id=page_id)
                    if page is None:
                        logger.warning(
                            "Workflow '%s' step %d references unknown page_id '%s'",
                            wf_id,
                            i + 1,
                            page_id,
                        )

        logger.info("Loaded %d workflows", len(self._data))

    def _tokenize(self, text: str) -> List[str]:
        """Split text into lowercase word tokens."""
        return re.findall(r"[a-z0-9]+", text.lower())

    def list_workflows(self, query: Optional[str] = None) -> Dict[str, Any]:
        """Return all workflows, optionally filtered by keyword.

        Searches title, description, and tags for matching words.
        """
        self._ensure_loaded()

        workflows = []
        query_tokens = self._tokenize(query) if query else []

        for wf_id, wf in self._data.items():
            if query_tokens:
                # Build searchable text from title + description + tags
                searchable = " ".join([
                    wf.get("title", ""),
                    wf.get("description", ""),
                    " ".join(wf.get("tags", [])),
                ])
                searchable_tokens = set(self._tokenize(searchable))
                if not any(qt in searchable_tokens for qt in query_tokens):
                    continue

            workflows.append({
                "id": wf_id,
                "title": wf.get("title", ""),
                "description": wf.get("description", ""),
                "tags": wf.get("tags", []),
                "step_count": len(wf.get("steps", [])),
            })

        return {
            "total": len(workflows),
            "workflows": workflows,
        }

    def get_workflow(
        self, workflow_id: str, step: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Return a workflow with enriched step data, or a single step.

        Args:
            workflow_id: The workflow identifier.
            step: 1-based step number. If provided, returns only that step.

        Returns:
            Workflow dict with enriched steps, or None if not found.
        """
        self._ensure_loaded()

        wf = self._data.get(workflow_id)
        if wf is None:
            return None

        enriched_steps = []
        for i, s in enumerate(wf.get("steps", [])):
            enriched = self._enrich_step(s, i + 1)
            enriched_steps.append(enriched)

        # Single step requested
        if step is not None:
            if step < 1 or step > len(enriched_steps):
                return None
            return {
                "id": workflow_id,
                "title": wf.get("title", ""),
                "description": wf.get("description", ""),
                "tags": wf.get("tags", []),
                "total_steps": len(enriched_steps),
                "step": enriched_steps[step - 1],
            }

        return {
            "id": workflow_id,
            "title": wf.get("title", ""),
            "description": wf.get("description", ""),
            "tags": wf.get("tags", []),
            "total_steps": len(enriched_steps),
            "steps": enriched_steps,
        }

    def _enrich_step(self, step: Dict, step_number: int) -> Dict[str, Any]:
        """Enrich a workflow step with page metadata from SchemaStore."""
        page_id = step.get("page_id")
        page_title = None
        page_url = None
        screenshot_path = None

        if page_id:
            page = self._schema_store.get_page(page_id=page_id)
            if page:
                page_title = page.get("title")
                page_url = page.get("url")

            sp = self._schema_store.get_screenshot_path(page_id=page_id)
            if sp:
                screenshot_path = str(sp)

        return {
            "step_number": step_number,
            "title": step.get("title", ""),
            "instruction": step.get("instruction", ""),
            "page_id": page_id,
            "page_title": page_title,
            "page_url": page_url,
            "screenshot_path": screenshot_path,
            "highlight_element": step.get("highlight_element"),
            "highlight_form": step.get("highlight_form"),
        }
