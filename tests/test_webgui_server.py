"""Smoke tests for the standalone WebGUI MCP server entry point."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestWebGUIServerRegistry:
    """Verify the standalone server builds its registry correctly."""

    def test_tool_definitions_count(self):
        from src.webgui.server import _TOOL_DEFINITIONS

        assert len(_TOOL_DEFINITIONS) == 10

    def test_handler_map_count(self):
        from src.webgui.server import _HANDLER_MAP

        assert len(_HANDLER_MAP) == 10

    def test_all_tools_have_handlers(self):
        from src.webgui.server import _TOOL_DEFINITIONS, _HANDLER_MAP

        tool_names = {t.name for t in _TOOL_DEFINITIONS}
        handler_names = set(_HANDLER_MAP.keys())
        assert tool_names == handler_names

    def test_expected_tool_names(self):
        from src.webgui.server import _TOOL_DEFINITIONS

        names = {t.name for t in _TOOL_DEFINITIONS}
        expected = {
            "ui_list_pages",
            "ui_get_page",
            "ui_search",
            "ui_get_screenshot",
            "ui_get_navigation",
            "ui_describe_page",
            "ui_get_form",
            "ui_list_walkthroughs",
            "ui_get_walkthrough",
            "ui_crop_screenshot",
        }
        assert names == expected

    def test_server_instantiates(self):
        """WebGUIMCPServer can be created (schema file missing is OK — it warns)."""
        from src.webgui.server import WebGUIMCPServer

        server = WebGUIMCPServer()
        assert server.server is not None


class TestMainServerExcludesWebGUI:
    """Verify the main server no longer includes WebGUI tools."""

    def test_no_webgui_tools_in_main_registry(self):
        from src.server import _TOOL_DEFINITIONS

        names = {t.name for t in _TOOL_DEFINITIONS}
        webgui_names = {
            "ui_list_pages",
            "ui_get_page",
            "ui_search",
            "ui_get_screenshot",
            "ui_get_navigation",
            "ui_describe_page",
            "ui_get_form",
            "ui_list_walkthroughs",
            "ui_get_walkthrough",
            "ui_crop_screenshot",
        }
        assert names.isdisjoint(webgui_names), (
            f"Main server still contains WebGUI tools: {names & webgui_names}"
        )

    def test_main_server_tool_count(self):
        from src.server import _TOOL_DEFINITIONS

        assert len(_TOOL_DEFINITIONS) == 250, (
            f"Expected 250 tools in main server, got {len(_TOOL_DEFINITIONS)}"
        )
