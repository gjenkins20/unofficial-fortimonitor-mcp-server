"""Screenshot capture and file management.

Handles full-page, modal, and element screenshots during crawling.
Screenshots are stored in data/webgui/screenshots/{crawl_id}/.
"""

import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ScreenshotManager:
    """Manages screenshot capture and storage for crawl operations."""

    def __init__(self, base_dir: str = "data/webgui/screenshots"):
        self.base_dir = Path(base_dir)

    def _crawl_dir(self, crawl_id: str) -> Path:
        """Get the screenshot directory for a crawl."""
        d = self.base_dir / crawl_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Convert a URL or string to a safe filename."""
        name = re.sub(r"https?://", "", name)
        name = re.sub(r"[^\w\-.]", "_", name)
        name = re.sub(r"_+", "_", name).strip("_")
        return name[:200]  # Limit filename length

    def page_screenshot_path(self, crawl_id: str, page_url: str) -> Path:
        """Get the path for a page screenshot (does not take the screenshot)."""
        d = self._crawl_dir(crawl_id)
        filename = f"page_{self._sanitize_filename(page_url)}.png"
        return d / filename

    def modal_screenshot_path(
        self, crawl_id: str, page_url: str, modal_id: str
    ) -> Path:
        """Get the path for a modal screenshot."""
        d = self._crawl_dir(crawl_id)
        filename = f"modal_{self._sanitize_filename(page_url)}_{modal_id}.png"
        return d / filename

    def element_screenshot_path(
        self, crawl_id: str, page_url: str, element_id: str
    ) -> Path:
        """Get the path for an element screenshot."""
        d = self._crawl_dir(crawl_id)
        filename = f"elem_{self._sanitize_filename(page_url)}_{element_id}.png"
        return d / filename

    async def capture_page(self, page, crawl_id: str, page_url: str) -> Optional[str]:
        """Capture a full-page screenshot using a Playwright Page object.

        Args:
            page: Playwright Page instance.
            crawl_id: Current crawl identifier.
            page_url: URL of the page being captured.

        Returns:
            Path to the saved screenshot, or None on failure.
        """
        path = self.page_screenshot_path(crawl_id, page_url)
        try:
            await page.screenshot(path=str(path), full_page=True)
            logger.info(f"Captured page screenshot: {path}")
            return str(path)
        except Exception as e:
            logger.error(f"Failed to capture page screenshot for {page_url}: {e}")
            return None

    async def capture_modal(
        self, page, crawl_id: str, page_url: str, modal_id: str, selector: str
    ) -> Optional[str]:
        """Capture a screenshot of a modal dialog.

        Args:
            page: Playwright Page instance.
            crawl_id: Current crawl identifier.
            page_url: URL of the page containing the modal.
            modal_id: Modal identifier.
            selector: CSS selector for the modal element.

        Returns:
            Path to the saved screenshot, or None on failure.
        """
        path = self.modal_screenshot_path(crawl_id, page_url, modal_id)
        try:
            element = page.locator(selector)
            await element.screenshot(path=str(path))
            logger.info(f"Captured modal screenshot: {path}")
            return str(path)
        except Exception as e:
            logger.error(f"Failed to capture modal screenshot {modal_id}: {e}")
            return None

    def get_screenshot_info(
        self, crawl_id: str, screenshot_id: str
    ) -> Optional[dict]:
        """Get info about a screenshot by ID (filename stem).

        Args:
            crawl_id: Crawl identifier.
            screenshot_id: Screenshot filename stem (without extension).

        Returns:
            Dict with path, exists, size info, or None if crawl dir missing.
        """
        d = self._crawl_dir(crawl_id)
        path = d / f"{screenshot_id}.png"
        if path.exists():
            stat = path.stat()
            return {
                "screenshot_id": screenshot_id,
                "path": str(path),
                "exists": True,
                "size_bytes": stat.st_size,
            }
        return {
            "screenshot_id": screenshot_id,
            "path": str(path),
            "exists": False,
            "size_bytes": 0,
        }

    def list_screenshots(self, crawl_id: str) -> list:
        """List all screenshots for a crawl."""
        d = self.base_dir / crawl_id
        if not d.exists():
            return []
        return [
            {
                "screenshot_id": p.stem,
                "path": str(p),
                "size_bytes": p.stat().st_size,
            }
            for p in sorted(d.glob("*.png"))
        ]
