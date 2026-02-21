"""Schema store for WebGUI crawl data.

Lazy-loads the crawl JSON schema and builds in-memory indexes for fast
querying of page structure, UI elements, forms, modals, and navigation.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class SchemaStore:
    """Read-only store for crawled WebGUI schema data.

    Loads the schema JSON lazily on first access and builds word-level
    indexes for fast lookups across page titles, element labels, form
    fields, and modal titles.
    """

    def __init__(self, schema_file: Path, screenshots_dir: Path):
        self._schema_file = Path(schema_file)
        self._screenshots_dir = Path(screenshots_dir)
        self._data: Optional[Dict] = None
        # Indexes (built once on load)
        self._title_index: Dict[str, List[str]] = {}  # word -> [url, ...]
        self._element_index: Dict[str, List[str]] = {}  # word -> [url, ...]
        self._form_index: Dict[str, List[str]] = {}  # word -> [url, ...]
        self._modal_index: Dict[str, List[str]] = {}  # word -> [url, ...]
        self._page_id_map: Dict[str, str] = {}  # page_id -> url
        self._url_categories: Dict[str, List[str]] = {}  # category -> [url, ...]

    def _ensure_loaded(self) -> None:
        """Load schema and build indexes if not already done."""
        if self._data is not None:
            return

        logger.info("Loading WebGUI schema from %s", self._schema_file)
        with open(self._schema_file, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        logger.info("Schema loaded, building indexes...")
        self._build_indexes()
        logger.info("Indexes built for %d pages", len(self._data.get("pages", {})))

    def _tokenize(self, text: str) -> List[str]:
        """Split text into lowercase word tokens."""
        return re.findall(r"[a-z0-9]+", text.lower())

    def _add_to_index(
        self, index: Dict[str, List[str]], text: str, url: str
    ) -> None:
        """Add all words from text to the given index, mapped to url."""
        for word in self._tokenize(text):
            if url not in index.get(word, []):
                index.setdefault(word, []).append(url)

    def _categorize_url(self, url: str) -> str:
        """Extract a category from a URL path (first path segment)."""
        parsed = urlparse(url)
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        return parts[0] if parts else "root"

    def _build_indexes(self) -> None:
        """Build in-memory indexes from loaded schema data."""
        pages = self._data.get("pages", {})

        for url, page in pages.items():
            page_id = page.get("page_id", "")
            title = page.get("title", "")

            # page_id -> url map
            if page_id:
                self._page_id_map[page_id] = url

            # URL category map
            category = self._categorize_url(url)
            self._url_categories.setdefault(category, []).append(url)

            # Title index
            if title:
                self._add_to_index(self._title_index, title, url)

            # Element label index (from sections)
            for section in page.get("sections", []):
                for elem in section.get("elements", []):
                    label = elem.get("label", "")
                    if label:
                        self._add_to_index(self._element_index, label, url)

            # Form field index
            for form in page.get("forms", []):
                form_title = form.get("title", "")
                if form_title:
                    self._add_to_index(self._form_index, form_title, url)
                for field in form.get("fields", []):
                    label = field.get("label", "")
                    if label:
                        self._add_to_index(self._form_index, label, url)

            # Modal title index
            for modal in page.get("modals", []):
                modal_title = modal.get("title", "")
                if modal_title:
                    self._add_to_index(self._modal_index, modal_title, url)
                # Also index modal form fields
                for form in modal.get("forms", []):
                    for field in form.get("fields", []):
                        label = field.get("label", "")
                        if label:
                            self._add_to_index(self._modal_index, label, url)

    def _resolve_url(self, url: Optional[str] = None, page_id: Optional[str] = None) -> Optional[str]:
        """Resolve a page_id to a URL, or validate a URL exists."""
        self._ensure_loaded()
        if url:
            if url in self._data["pages"]:
                return url
            return None
        if page_id:
            return self._page_id_map.get(page_id)
        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_metadata(self) -> Dict[str, Any]:
        """Return crawl metadata and summary statistics."""
        self._ensure_loaded()
        meta = dict(self._data.get("crawl_metadata", {}))
        meta["schema_version"] = self._data.get("schema_version", "unknown")
        meta["total_pages_loaded"] = len(self._data.get("pages", {}))
        meta["categories"] = sorted(self._url_categories.keys())
        return meta

    def list_pages(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List crawled pages with pagination.

        Returns page summaries (url, title, page_id, category) without
        the full element/form/modal data.
        """
        self._ensure_loaded()
        pages = self._data.get("pages", {})

        if category:
            urls = self._url_categories.get(category, [])
        else:
            urls = list(pages.keys())

        urls_sorted = sorted(urls)
        total = len(urls_sorted)
        page_slice = urls_sorted[offset : offset + limit]

        summaries = []
        for url in page_slice:
            page = pages[url]
            summaries.append(
                {
                    "url": url,
                    "title": page.get("title", ""),
                    "page_id": page.get("page_id", ""),
                    "category": self._categorize_url(url),
                    "num_sections": len(page.get("sections", [])),
                    "num_forms": len(page.get("forms", [])),
                    "num_modals": len(page.get("modals", [])),
                    "num_links": len(page.get("links", [])),
                    "has_screenshot": page.get("screenshot_path") is not None,
                }
            )

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "count": len(summaries),
            "pages": summaries,
        }

    def get_page(
        self,
        url: Optional[str] = None,
        page_id: Optional[str] = None,
        include_elements: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Get full page data by URL or page_id.

        By default, omits individual element details from sections to
        keep response size manageable. Set include_elements=True for
        full element data (capped at 500 elements).
        """
        resolved_url = self._resolve_url(url=url, page_id=page_id)
        if not resolved_url:
            return None

        page = self._data["pages"][resolved_url]
        result = {
            "url": resolved_url,
            "title": page.get("title", ""),
            "page_id": page.get("page_id", ""),
            "breadcrumbs": page.get("breadcrumbs", []),
            "category": self._categorize_url(resolved_url),
            "has_screenshot": page.get("screenshot_path") is not None,
            "links": page.get("links", []),
            "forms": page.get("forms", []),
            "modals_summary": [
                {
                    "modal_id": m.get("modal_id", ""),
                    "title": m.get("title", ""),
                    "num_elements": len(m.get("elements", [])),
                    "num_forms": len(m.get("forms", [])),
                }
                for m in page.get("modals", [])
            ],
        }

        if include_elements:
            all_elements = []
            for section in page.get("sections", []):
                for elem in section.get("elements", []):
                    all_elements.append(elem)
                    if len(all_elements) >= 500:
                        break
                if len(all_elements) >= 500:
                    break
            result["elements"] = all_elements
            result["elements_truncated"] = len(all_elements) >= 500
        else:
            # Provide section summaries
            result["sections"] = [
                {
                    "heading": s.get("heading", ""),
                    "num_elements": len(s.get("elements", [])),
                }
                for s in page.get("sections", [])
            ]

        return result

    def search(
        self,
        query: str,
        search_in: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Search across indexed content using word-level matching.

        Args:
            query: Search terms (space-separated words).
            search_in: Restrict to "titles", "elements", "forms", or
                       "modals". None searches all.
            limit: Max results to return.

        Returns dict with results list, each containing url, title,
        match_type, and relevance score.
        """
        self._ensure_loaded()
        tokens = self._tokenize(query)
        if not tokens:
            return {"query": query, "results": [], "total": 0}

        # Choose which indexes to search
        indexes_to_search = []
        if search_in == "titles":
            indexes_to_search = [("title", self._title_index)]
        elif search_in == "elements":
            indexes_to_search = [("element", self._element_index)]
        elif search_in == "forms":
            indexes_to_search = [("form", self._form_index)]
        elif search_in == "modals":
            indexes_to_search = [("modal", self._modal_index)]
        else:
            indexes_to_search = [
                ("title", self._title_index),
                ("element", self._element_index),
                ("form", self._form_index),
                ("modal", self._modal_index),
            ]

        # Score URLs: count how many query tokens match in each index
        url_scores: Dict[str, Dict] = {}  # url -> {score, match_types}

        for match_type, index in indexes_to_search:
            for token in tokens:
                for url in index.get(token, []):
                    if url not in url_scores:
                        url_scores[url] = {"score": 0, "match_types": set()}
                    url_scores[url]["score"] += 1
                    url_scores[url]["match_types"].add(match_type)

        # Sort by score descending
        scored = sorted(url_scores.items(), key=lambda x: x[1]["score"], reverse=True)
        scored = scored[:limit]

        pages = self._data.get("pages", {})
        results = []
        for url, info in scored:
            page = pages.get(url, {})
            results.append(
                {
                    "url": url,
                    "title": page.get("title", ""),
                    "page_id": page.get("page_id", ""),
                    "match_types": sorted(info["match_types"]),
                    "relevance_score": info["score"],
                }
            )

        return {
            "query": query,
            "total": len(results),
            "results": results,
        }

    def get_navigation_tree(self, max_depth: int = 3) -> Dict[str, Any]:
        """Build a hierarchical navigation tree from URL paths.

        Groups pages by URL path segments up to max_depth.
        """
        self._ensure_loaded()
        pages = self._data.get("pages", {})

        tree: Dict[str, Any] = {"children": {}, "pages": []}

        for url, page in pages.items():
            parsed = urlparse(url)
            parts = [p for p in parsed.path.strip("/").split("/") if p]
            parts = parts[:max_depth]

            node = tree
            for part in parts:
                if part not in node["children"]:
                    node["children"][part] = {"children": {}, "pages": []}
                node = node["children"][part]

            node["pages"].append(
                {
                    "url": url,
                    "title": page.get("title", ""),
                    "page_id": page.get("page_id", ""),
                }
            )

        return self._serialize_tree(tree)

    def _serialize_tree(self, node: Dict) -> Dict[str, Any]:
        """Convert tree to a clean serializable dict."""
        result: Dict[str, Any] = {}
        if node["pages"]:
            result["pages"] = node["pages"]
        for name, child in sorted(node["children"].items()):
            result[name] = self._serialize_tree(child)
        return result

    def get_screenshot_path(
        self, url: Optional[str] = None, page_id: Optional[str] = None
    ) -> Optional[Path]:
        """Resolve the filesystem path to a page's screenshot.

        The schema stores paths like "data/webgui/screenshots/crawl-xxx/file.png"
        but actual files live in the configured screenshots_dir. We extract the
        filename and look for it there.
        """
        resolved_url = self._resolve_url(url=url, page_id=page_id)
        if not resolved_url:
            return None

        page = self._data["pages"][resolved_url]
        schema_path = page.get("screenshot_path")
        if not schema_path:
            return None

        # Extract just the filename from the schema path
        filename = Path(schema_path).name
        actual_path = self._screenshots_dir / filename

        if actual_path.exists():
            return actual_path
        return None

    def describe_page(
        self, url: Optional[str] = None, page_id: Optional[str] = None
    ) -> Optional[str]:
        """Generate a human-readable markdown description of a page.

        Includes title, breadcrumbs, sections summary, forms, modals,
        and navigation links.
        """
        resolved_url = self._resolve_url(url=url, page_id=page_id)
        if not resolved_url:
            return None

        page = self._data["pages"][resolved_url]
        title = page.get("title", "Untitled")
        breadcrumbs = page.get("breadcrumbs", [])

        lines = [f"# {title}", ""]

        if breadcrumbs:
            lines.append(f"**Breadcrumbs:** {' > '.join(breadcrumbs)}")
            lines.append("")

        lines.append(f"**URL:** `{resolved_url}`")
        lines.append("")

        # Sections summary
        sections = page.get("sections", [])
        if sections:
            total_elements = sum(len(s.get("elements", [])) for s in sections)
            lines.append(f"## Page Elements ({total_elements} total)")
            lines.append("")
            for section in sections:
                heading = section.get("heading", "Unnamed Section")
                elements = section.get("elements", [])
                # Summarize element types
                type_counts: Dict[str, int] = {}
                for elem in elements:
                    etype = elem.get("type", "unknown")
                    type_counts[etype] = type_counts.get(etype, 0) + 1
                type_summary = ", ".join(
                    f"{count} {etype}{'s' if count > 1 else ''}"
                    for etype, count in sorted(type_counts.items())
                )
                lines.append(f"- **{heading}**: {type_summary}")
            lines.append("")

        # Forms
        forms = page.get("forms", [])
        if forms:
            lines.append(f"## Forms ({len(forms)})")
            lines.append("")
            for form in forms:
                ftitle = form.get("title", "Untitled Form")
                fields = form.get("fields", [])
                field_names = [f.get("label", "?") for f in fields[:10]]
                lines.append(
                    f"- **{ftitle}** ({len(fields)} fields): "
                    + ", ".join(field_names)
                    + ("..." if len(fields) > 10 else "")
                )
            lines.append("")

        # Modals
        modals = page.get("modals", [])
        if modals:
            lines.append(f"## Modals/Dialogs ({len(modals)})")
            lines.append("")
            for modal in modals:
                mtitle = modal.get("title", "Untitled Modal")
                mforms = modal.get("forms", [])
                melems = modal.get("elements", [])
                parts = []
                if melems:
                    parts.append(f"{len(melems)} elements")
                if mforms:
                    parts.append(f"{len(mforms)} forms")
                detail = ", ".join(parts) if parts else "empty"
                lines.append(f"- **{mtitle}** ({detail})")
            lines.append("")

        # Links
        links = page.get("links", [])
        if links:
            nav_links = [l for l in links if l.get("type") == "navigation"]
            action_links = [l for l in links if l.get("type") == "action"]
            external_links = [l for l in links if l.get("type") == "external"]

            lines.append(f"## Links ({len(links)} total)")
            lines.append("")
            if nav_links:
                lines.append(
                    f"- **Navigation:** {len(nav_links)} links to other pages"
                )
            if action_links:
                lines.append(f"- **Actions:** {len(action_links)} action links")
            if external_links:
                lines.append(
                    f"- **External:** {len(external_links)} external links"
                )
            lines.append("")

        return "\n".join(lines)

    def get_element_position(
        self,
        url: Optional[str] = None,
        page_id: Optional[str] = None,
        element_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get an element's position {x, y, width, height} or None.

        Searches all sections on the page for the given element_id.
        Returns None if the page/element isn't found or position is null.
        """
        if not element_id:
            return None

        resolved_url = self._resolve_url(url=url, page_id=page_id)
        if not resolved_url:
            return None

        page = self._data["pages"][resolved_url]
        for section in page.get("sections", []):
            for elem in section.get("elements", []):
                if elem.get("element_id") == element_id:
                    pos = elem.get("position")
                    if pos and isinstance(pos, dict):
                        return pos
                    return None

        return None

    def get_forms(
        self,
        url: Optional[str] = None,
        page_id: Optional[str] = None,
        form_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get form details for a page, optionally filtered by form_id.

        Returns forms from both the page level and within modals.
        """
        resolved_url = self._resolve_url(url=url, page_id=page_id)
        if not resolved_url:
            return None

        page = self._data["pages"][resolved_url]
        all_forms = []

        # Page-level forms
        for form in page.get("forms", []):
            all_forms.append({"source": "page", **form})

        # Modal forms
        for modal in page.get("modals", []):
            for form in modal.get("forms", []):
                all_forms.append(
                    {
                        "source": f"modal:{modal.get('modal_id', '')}",
                        "modal_title": modal.get("title", ""),
                        **form,
                    }
                )

        if form_id:
            all_forms = [f for f in all_forms if f.get("form_id") == form_id]

        return {
            "url": resolved_url,
            "title": page.get("title", ""),
            "total_forms": len(all_forms),
            "forms": all_forms,
        }
