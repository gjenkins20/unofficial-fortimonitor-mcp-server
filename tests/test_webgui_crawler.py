"""Tests for WebGUI crawler engine.

Uses mocked Playwright Page/Browser to test BFS discovery,
authentication, element extraction, and state persistence.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.webgui.crawler.authenticator import authenticate
from src.webgui.crawler.extractor import (
    _classify_link,
    _map_element_type,
    build_navigation_tree,
)
from src.webgui.crawler.screenshots import ScreenshotManager
from src.webgui.crawler.state import CrawlState
from src.webgui.models import CrawlStatus, ElementType, LinkType


# =============================================================================
# Authenticator Tests
# =============================================================================


class TestAuthenticator:
    """Test login authentication."""

    @pytest.fixture
    def mock_page(self):
        page = AsyncMock()
        page.url = "https://app.example.com/dashboard"

        # Create a locator mock that properly chains .first
        def make_locator(*args, **kwargs):
            loc = MagicMock()
            first_loc = AsyncMock()
            first_loc.is_visible = AsyncMock(return_value=True)
            first_loc.fill = AsyncMock()
            first_loc.click = AsyncMock()
            loc.first = first_loc
            return loc

        page.locator = MagicMock(side_effect=make_locator)
        page.goto = AsyncMock()
        page.wait_for_url = AsyncMock()
        return page

    async def test_authenticate_success(self, mock_page):
        result = await authenticate(
            mock_page,
            "https://app.example.com/login",
            "user@example.com",
            "password123",
        )
        assert result is True
        mock_page.goto.assert_called_once()
        mock_page.wait_for_url.assert_called_once()

    async def test_authenticate_no_username_field(self, mock_page):
        # Make all locators invisible
        def make_invisible_locator(*args, **kwargs):
            loc = MagicMock()
            first_loc = AsyncMock()
            first_loc.is_visible = AsyncMock(return_value=False)
            loc.first = first_loc
            return loc

        mock_page.locator = MagicMock(side_effect=make_invisible_locator)

        result = await authenticate(
            mock_page,
            "https://app.example.com/login",
            "user@example.com",
            "password123",
        )
        assert result is False

    async def test_authenticate_navigation_timeout(self, mock_page):
        mock_page.wait_for_url = AsyncMock(side_effect=Exception("Timeout"))

        result = await authenticate(
            mock_page,
            "https://app.example.com/login",
            "user@example.com",
            "password123",
        )
        assert result is False


# =============================================================================
# Extractor Tests
# =============================================================================


class TestExtractor:
    """Test element type mapping and link classification."""

    def test_map_element_type_button(self):
        assert _map_element_type("button") == ElementType.BUTTON
        assert _map_element_type("submit") == ElementType.BUTTON

    def test_map_element_type_input(self):
        assert _map_element_type("text") == ElementType.INPUT
        assert _map_element_type("email") == ElementType.INPUT
        assert _map_element_type("password") == ElementType.INPUT

    def test_map_element_type_select(self):
        assert _map_element_type("select") == ElementType.SELECT
        assert _map_element_type("select-one") == ElementType.SELECT

    def test_map_element_type_checkbox(self):
        assert _map_element_type("checkbox") == ElementType.CHECKBOX

    def test_map_element_type_unknown(self):
        assert _map_element_type("unknown-type") == ElementType.OTHER

    def test_classify_link_navigation(self):
        assert _classify_link("https://app.example.com/settings", "https://app.example.com") == LinkType.NAVIGATION

    def test_classify_link_external(self):
        assert _classify_link("https://other.com/page", "https://app.example.com") == LinkType.EXTERNAL

    def test_classify_link_anchor(self):
        assert _classify_link("#section", "https://app.example.com") == LinkType.ANCHOR

    def test_build_navigation_tree(self):
        items = [
            {"label": "Home", "url": "https://app.example.com/"},
            {"label": "Settings", "url": "https://app.example.com/settings"},
            {"label": "Home", "url": "https://app.example.com/"},  # duplicate
        ]
        tree = build_navigation_tree(items, "https://app.example.com")
        assert tree.label == "Root"
        assert len(tree.children) == 2  # deduped

    def test_build_navigation_tree_empty(self):
        tree = build_navigation_tree([], "https://app.example.com")
        assert tree.label == "Root"
        assert len(tree.children) == 0


# =============================================================================
# Screenshot Manager Tests
# =============================================================================


class TestScreenshotManager:
    """Test screenshot path generation and info."""

    @pytest.fixture
    def mgr(self, tmp_path):
        return ScreenshotManager(str(tmp_path / "screenshots"))

    def test_page_screenshot_path(self, mgr):
        path = mgr.page_screenshot_path("crawl-001", "https://app.example.com/dashboard")
        assert "crawl-001" in str(path)
        assert path.suffix == ".png"
        assert "page_" in path.name

    def test_modal_screenshot_path(self, mgr):
        path = mgr.modal_screenshot_path("crawl-001", "https://app.example.com/settings", "confirm-modal")
        assert "modal_" in path.name
        assert "confirm-modal" in path.name

    def test_element_screenshot_path(self, mgr):
        path = mgr.element_screenshot_path("crawl-001", "https://app.example.com/page", "btn-1")
        assert "elem_" in path.name
        assert "btn-1" in path.name

    def test_sanitize_filename(self):
        result = ScreenshotManager._sanitize_filename("https://app.example.com/path?query=1#frag")
        assert "https" not in result
        assert "?" not in result
        assert "#" not in result
        assert len(result) <= 200

    def test_get_screenshot_info_not_exists(self, mgr):
        info = mgr.get_screenshot_info("crawl-001", "nonexistent")
        assert info is not None
        assert info["exists"] is False

    def test_get_screenshot_info_exists(self, mgr, tmp_path):
        # Create a fake screenshot
        d = tmp_path / "screenshots" / "crawl-001"
        d.mkdir(parents=True, exist_ok=True)
        f = d / "test-shot.png"
        f.write_bytes(b"fake png data")

        info = mgr.get_screenshot_info("crawl-001", "test-shot")
        assert info["exists"] is True
        assert info["size_bytes"] == 13

    def test_list_screenshots_empty(self, mgr):
        assert mgr.list_screenshots("nonexistent") == []

    def test_list_screenshots(self, mgr, tmp_path):
        d = tmp_path / "screenshots" / "crawl-001"
        d.mkdir(parents=True, exist_ok=True)
        (d / "shot1.png").write_bytes(b"data1")
        (d / "shot2.png").write_bytes(b"data2")

        shots = mgr.list_screenshots("crawl-001")
        assert len(shots) == 2


# =============================================================================
# Crawl State Tests
# =============================================================================


class TestCrawlState:
    """Test crawl state persistence."""

    @pytest.fixture
    def state(self, tmp_path):
        return CrawlState(str(tmp_path / "crawl_state"))

    def test_save_and_load(self, state):
        state.save(
            crawl_id="crawl-001",
            status=CrawlStatus.RUNNING,
            visited={"https://app.example.com/"},
            queue=["https://app.example.com/settings"],
            errors=[],
            current_page="https://app.example.com/",
            started_at=datetime(2025, 1, 15, 10, 0, 0),
        )
        data = state.load("crawl-001")
        assert data is not None
        assert data["status"] == "running"
        assert len(data["visited"]) == 1
        assert len(data["queue"]) == 1

    def test_load_nonexistent(self, state):
        assert state.load("nonexistent") is None

    def test_get_progress(self, state):
        state.save(
            crawl_id="crawl-001",
            status=CrawlStatus.RUNNING,
            visited={"url1", "url2"},
            queue=["url3"],
            errors=["Error on url4"],
            started_at=datetime(2025, 1, 15, 10, 0, 0),
        )
        progress = state.get_progress("crawl-001")
        assert progress is not None
        assert progress.status == CrawlStatus.RUNNING
        assert progress.pages_crawled == 2
        assert progress.pages_remaining == 1
        assert progress.pages_discovered == 3
        assert len(progress.errors) == 1

    def test_get_progress_nonexistent(self, state):
        assert state.get_progress("nonexistent") is None

    def test_delete(self, state):
        state.save(
            crawl_id="crawl-001",
            status=CrawlStatus.COMPLETED,
            visited=set(),
            queue=[],
            errors=[],
        )
        assert state.delete("crawl-001") is True
        assert state.load("crawl-001") is None

    def test_delete_nonexistent(self, state):
        assert state.delete("nonexistent") is False

    def test_list_crawls(self, state):
        for i in range(3):
            state.save(
                crawl_id=f"crawl-{i:03d}",
                status=CrawlStatus.COMPLETED,
                visited=set(),
                queue=[],
                errors=[],
            )
        crawls = state.list_crawls()
        assert len(crawls) == 3
