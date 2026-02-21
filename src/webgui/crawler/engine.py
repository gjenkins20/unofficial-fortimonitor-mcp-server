"""Core Playwright crawl engine.

Performs BFS page discovery: authenticate, visit pages, extract elements,
capture screenshots, and build a UISchema.
"""

import asyncio
import logging
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

from ..models import (
    CrawlMetadata,
    CrawlStatus,
    UIPage,
    UISchema,
)
from .authenticator import authenticate
from .extractor import build_navigation_tree, extract_page_elements
from .screenshots import ScreenshotManager
from .state import CrawlState

logger = logging.getLogger(__name__)


class CrawlEngine:
    """Playwright-based BFS web crawler that builds UISchema."""

    def __init__(
        self,
        target_url: str,
        username: str,
        password: str,
        application_name: str = "",
        max_pages: int = 100,
        max_depth: int = 5,
        crawl_delay: float = 1.0,
        login_url: Optional[str] = None,
        screenshot_enabled: bool = True,
        headless: bool = True,
        data_dir: str = "data/webgui",
        timeout: int = 30000,
    ):
        self.target_url = target_url.rstrip("/")
        self.username = username
        self.password = password
        self.application_name = application_name
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.crawl_delay = crawl_delay
        self.login_url = login_url or target_url
        self.screenshot_enabled = screenshot_enabled
        self.headless = headless
        self.timeout = timeout

        self.crawl_id = f"crawl-{uuid.uuid4().hex[:12]}"
        self.screenshot_mgr = ScreenshotManager(f"{data_dir}/screenshots")
        self.crawl_state = CrawlState(f"{data_dir}/crawl_state")

        # BFS state
        self._visited: Set[str] = set()
        self._queue: deque = deque()
        self._pages: Dict[str, UIPage] = {}
        self._all_nav_items: List[Dict] = []
        self._errors: List[str] = []
        self._status = CrawlStatus.PENDING
        self._started_at: Optional[datetime] = None

    def _is_same_origin(self, url: str) -> bool:
        """Check if a URL belongs to the same origin as the target."""
        parsed = urlparse(url)
        target_parsed = urlparse(self.target_url)
        return parsed.netloc == target_parsed.netloc

    def _normalize_url(self, url: str) -> str:
        """Normalize a URL by removing fragments and trailing slashes."""
        parsed = urlparse(url)
        # Remove fragment, keep everything else
        normalized = parsed._replace(fragment="").geturl()
        return normalized.rstrip("/")

    async def crawl(self) -> UISchema:
        """Run the full crawl and return a UISchema.

        Launches a Playwright browser, authenticates, then BFS crawls
        all same-origin pages up to max_pages/max_depth limits.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError(
                "Playwright is required for crawling. "
                "Install with: pip install 'fortimonitor-mcp-server[webgui]' "
                "&& playwright install chromium"
            )

        self._status = CrawlStatus.RUNNING
        self._started_at = datetime.now(timezone.utc)
        self._save_state()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()
            page.set_default_timeout(self.timeout)

            try:
                # Authenticate
                auth_success = await authenticate(
                    page, self.login_url, self.username, self.password,
                    timeout=self.timeout,
                )
                if not auth_success:
                    self._errors.append("Authentication failed")
                    self._status = CrawlStatus.FAILED
                    self._save_state()
                    return self._build_schema()

                # Seed the BFS queue with the current page after login
                start_url = self._normalize_url(page.url)
                self._queue.append((start_url, 0))

                # BFS loop
                while self._queue and len(self._visited) < self.max_pages:
                    url, depth = self._queue.popleft()
                    url = self._normalize_url(url)

                    if url in self._visited:
                        continue
                    if depth > self.max_depth:
                        continue
                    if not self._is_same_origin(url):
                        continue

                    self._visited.add(url)
                    self._save_state(current_page=url)
                    logger.info(
                        f"Crawling [{len(self._visited)}/{self.max_pages}] "
                        f"depth={depth}: {url}"
                    )

                    try:
                        await page.goto(url, wait_until="networkidle", timeout=self.timeout)
                        await asyncio.sleep(self.crawl_delay)

                        # Extract page data
                        page_data = await extract_page_elements(page, url)

                        # Capture screenshot
                        screenshot_path = None
                        if self.screenshot_enabled:
                            screenshot_path = await self.screenshot_mgr.capture_page(
                                page, self.crawl_id, url
                            )

                        # Build UIPage
                        page_id = urlparse(url).path.strip("/").replace("/", "-") or "root"
                        ui_page = UIPage(
                            page_id=page_id,
                            url=url,
                            title=page_data["title"],
                            breadcrumbs=page_data["breadcrumbs"],
                            screenshot_path=screenshot_path,
                            sections=page_data["sections"],
                            forms=page_data["forms"],
                            modals=page_data["modals"],
                            links=page_data["links"],
                        )
                        self._pages[url] = ui_page

                        # Collect nav items
                        self._all_nav_items.extend(page_data["nav_items"])

                        # Enqueue discovered links
                        for link in page_data["links"]:
                            link_url = self._normalize_url(link.url)
                            if (
                                link_url not in self._visited
                                and self._is_same_origin(link_url)
                            ):
                                self._queue.append((link_url, depth + 1))

                    except Exception as e:
                        error_msg = f"Error crawling {url}: {str(e)}"
                        logger.error(error_msg)
                        self._errors.append(error_msg)

                self._status = CrawlStatus.COMPLETED

            except Exception as e:
                self._errors.append(f"Crawl error: {str(e)}")
                self._status = CrawlStatus.FAILED
                logger.exception("Fatal crawl error")

            finally:
                await browser.close()
                self._save_state()

        return self._build_schema()

    def _save_state(self, current_page: Optional[str] = None) -> None:
        """Persist current crawl state."""
        self.crawl_state.save(
            crawl_id=self.crawl_id,
            status=self._status,
            visited=self._visited,
            queue=[item[0] if isinstance(item, tuple) else item for item in self._queue],
            errors=self._errors,
            current_page=current_page,
            started_at=self._started_at,
        )

    def _build_schema(self) -> UISchema:
        """Build the final UISchema from collected data."""
        nav_tree = None
        if self._all_nav_items:
            nav_tree = build_navigation_tree(self._all_nav_items, self.target_url)

        total_elements = sum(p.element_count for p in self._pages.values())
        total_forms = sum(len(p.forms) for p in self._pages.values())
        total_modals = sum(len(p.modals) for p in self._pages.values())

        return UISchema(
            schema_version="1.0.0",
            crawl_metadata=CrawlMetadata(
                crawl_id=self.crawl_id,
                target_url=self.target_url,
                application_name=self.application_name,
                started_at=self._started_at,
                completed_at=datetime.now(timezone.utc),
                total_pages=len(self._pages),
                total_elements=total_elements,
                total_forms=total_forms,
                total_modals=total_modals,
            ),
            navigation_tree=nav_tree,
            pages=self._pages,
        )

    def get_progress(self) -> dict:
        """Get current crawl progress as a dict."""
        return {
            "crawl_id": self.crawl_id,
            "status": self._status.value,
            "pages_discovered": len(self._visited) + len(self._queue),
            "pages_crawled": len(self._visited),
            "pages_remaining": len(self._queue),
            "current_page": None,
            "errors": self._errors,
        }
