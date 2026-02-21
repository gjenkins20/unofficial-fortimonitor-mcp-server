"""
Registry integrity tests for FortiMonitor MCP server.

These tests verify that:
- All 241 tools are registered and loadable
- No duplicate tool names exist
- Every tool definition has a matching handler
- Every handler has a matching tool definition
- Tool names are consistent between definition and handler maps
- The server module loads without errors
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Helpers to collect all tool modules without triggering settings validation
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def registry():
    """Build the full tool registry (definitions + handler map).

    We patch get_settings so the module can be imported without a real
    FortiMonitor API key or .env file.
    """
    mock_settings = MagicMock()
    mock_settings.api_base_url = "https://api2.panopta.com/v2"
    mock_settings.fortimonitor_api_key = "test_key"
    mock_settings.schema_cache_dir = MagicMock()
    mock_settings.schema_cache_dir.mkdir = MagicMock()
    mock_settings.log_level = "WARNING"
    mock_settings.mcp_server_name = "test-server"
    mock_settings.mcp_server_version = "0.0.0-test"

    with patch("src.config.get_settings", return_value=mock_settings):
        # Force-reimport to ensure clean state
        if "src.server" in sys.modules:
            del sys.modules["src.server"]
        from src.server import _TOOL_DEFINITIONS, _HANDLER_MAP

    return _TOOL_DEFINITIONS, _HANDLER_MAP


class TestRegistryIntegrity:
    """Verify the tool registry loads correctly."""

    def test_total_tool_count(self, registry):
        """All 248 tools are registered (241 original + 7 WebGUI)."""
        defns, handlers = registry
        assert len(defns) >= 248, (
            f"Expected at least 248 tools, got {len(defns)}"
        )

    def test_definition_handler_count_match(self, registry):
        """Number of definitions matches number of handlers."""
        defns, handlers = registry
        assert len(defns) == len(handlers), (
            f"Definitions ({len(defns)}) != Handlers ({len(handlers)})"
        )

    def test_no_duplicate_tool_names(self, registry):
        """No two tools share the same name."""
        defns, _ = registry
        names = [t.name for t in defns]
        dupes = [n for n in names if names.count(n) > 1]
        assert len(dupes) == 0, f"Duplicate tool names: {set(dupes)}"

    def test_every_definition_has_handler(self, registry):
        """Every tool definition has a corresponding handler in the map."""
        defns, handlers = registry
        for tool in defns:
            assert tool.name in handlers, (
                f"Tool '{tool.name}' has a definition but no handler"
            )

    def test_every_handler_has_definition(self, registry):
        """Every handler key has a corresponding tool definition."""
        defns, handlers = registry
        defn_names = {t.name for t in defns}
        for name in handlers:
            assert name in defn_names, (
                f"Handler '{name}' exists but has no tool definition"
            )

    def test_all_handlers_are_callable(self, registry):
        """Every handler is an async callable."""
        _, handlers = registry
        import asyncio
        for name, handler in handlers.items():
            assert callable(handler), (
                f"Handler for '{name}' is not callable"
            )
            assert asyncio.iscoroutinefunction(handler), (
                f"Handler for '{name}' is not an async function"
            )

    def test_all_definitions_have_name(self, registry):
        """Every tool definition has a non-empty name."""
        defns, _ = registry
        for tool in defns:
            assert tool.name, "Found a tool definition with empty name"

    def test_all_definitions_have_description(self, registry):
        """Every tool definition has a non-empty description."""
        defns, _ = registry
        for tool in defns:
            assert tool.description, (
                f"Tool '{tool.name}' has an empty description"
            )

    def test_all_definitions_have_input_schema(self, registry):
        """Every tool definition has an inputSchema."""
        defns, _ = registry
        for tool in defns:
            assert tool.inputSchema is not None, (
                f"Tool '{tool.name}' has no inputSchema"
            )
            assert tool.inputSchema.get("type") == "object", (
                f"Tool '{tool.name}' inputSchema type is not 'object'"
            )


class TestToolNameConventions:
    """Verify tool naming follows project conventions."""

    def test_names_are_snake_case(self, registry):
        """All tool names use snake_case."""
        defns, _ = registry
        import re
        pattern = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
        for tool in defns:
            assert pattern.match(tool.name), (
                f"Tool '{tool.name}' is not snake_case"
            )

    def test_no_excessively_long_names(self, registry):
        """Tool names are reasonable length (< 80 chars)."""
        defns, _ = registry
        for tool in defns:
            assert len(tool.name) < 80, (
                f"Tool '{tool.name}' name is too long ({len(tool.name)} chars)"
            )


class TestRequiredFieldsInSchemas:
    """Verify that 'required' fields in schemas reference valid properties."""

    def test_required_fields_exist_in_properties(self, registry):
        """Every field listed in 'required' also appears in 'properties'."""
        defns, _ = registry
        for tool in defns:
            schema = tool.inputSchema
            required = schema.get("required", [])
            properties = schema.get("properties", {})
            for field in required:
                assert field in properties, (
                    f"Tool '{tool.name}': required field '{field}' "
                    f"not found in properties"
                )


class TestDictModuleExportConsistency:
    """Verify dict-based modules export matching definition and handler dicts."""

    # All dict-based modules to check
    DICT_MODULES = [
        ("src.tools.outage_enhanced", "OUTAGE_ENHANCED_TOOL_DEFINITIONS", "OUTAGE_ENHANCED_HANDLERS"),
        ("src.tools.server_enhanced", "SERVER_ENHANCED_TOOL_DEFINITIONS", "SERVER_ENHANCED_HANDLERS"),
        ("src.tools.maintenance_enhanced", "MAINTENANCE_ENHANCED_TOOL_DEFINITIONS", "MAINTENANCE_ENHANCED_HANDLERS"),
        ("src.tools.server_groups_enhanced", "SERVER_GROUPS_ENHANCED_TOOL_DEFINITIONS", "SERVER_GROUPS_ENHANCED_HANDLERS"),
        ("src.tools.templates_enhanced", "TEMPLATES_ENHANCED_TOOL_DEFINITIONS", "TEMPLATES_ENHANCED_HANDLERS"),
        ("src.tools.cloud", "CLOUD_TOOL_DEFINITIONS", "CLOUD_HANDLERS"),
        ("src.tools.dem", "DEM_TOOL_DEFINITIONS", "DEM_HANDLERS"),
        ("src.tools.compound_services", "COMPOUND_SERVICES_TOOL_DEFINITIONS", "COMPOUND_SERVICES_HANDLERS"),
        ("src.tools.dashboards", "DASHBOARDS_TOOL_DEFINITIONS", "DASHBOARDS_HANDLERS"),
        ("src.tools.status_pages", "STATUS_PAGES_TOOL_DEFINITIONS", "STATUS_PAGES_HANDLERS"),
        ("src.tools.rotating_contacts", "ROTATING_CONTACTS_TOOL_DEFINITIONS", "ROTATING_CONTACTS_HANDLERS"),
        ("src.tools.contacts_enhanced", "CONTACTS_ENHANCED_TOOL_DEFINITIONS", "CONTACTS_ENHANCED_HANDLERS"),
        ("src.tools.notifications_enhanced", "NOTIFICATIONS_ENHANCED_TOOL_DEFINITIONS", "NOTIFICATIONS_ENHANCED_HANDLERS"),
        ("src.tools.network_services", "NETWORK_SERVICES_TOOL_DEFINITIONS", "NETWORK_SERVICES_HANDLERS"),
        ("src.tools.monitoring_nodes", "MONITORING_NODES_TOOL_DEFINITIONS", "MONITORING_NODES_HANDLERS"),
        ("src.tools.network_service_types", "NETWORK_SERVICE_TYPES_TOOL_DEFINITIONS", "NETWORK_SERVICE_TYPES_HANDLERS"),
        ("src.tools.users", "USERS_TOOL_DEFINITIONS", "USERS_HANDLERS"),
        ("src.tools.reference_data", "REFERENCE_DATA_TOOL_DEFINITIONS", "REFERENCE_DATA_HANDLERS"),
        ("src.tools.snmp", "SNMP_TOOL_DEFINITIONS", "SNMP_HANDLERS"),
        ("src.tools.onsight", "ONSIGHT_TOOL_DEFINITIONS", "ONSIGHT_HANDLERS"),
        ("src.tools.fabric", "FABRIC_TOOL_DEFINITIONS", "FABRIC_HANDLERS"),
        ("src.tools.countermeasures", "COUNTERMEASURES_TOOL_DEFINITIONS", "COUNTERMEASURES_HANDLERS"),
        ("src.webgui.tools", "WEBGUI_TOOL_DEFINITIONS", "WEBGUI_HANDLERS"),
    ]

    @pytest.mark.parametrize("module_path,defn_name,handler_name", DICT_MODULES)
    def test_definition_handler_keys_match(self, module_path, defn_name, handler_name):
        """Definition dict keys match handler dict keys for each module."""
        import importlib

        mock_settings = MagicMock()
        mock_settings.api_base_url = "https://api2.panopta.com/v2"
        mock_settings.fortimonitor_api_key = "test_key"
        mock_settings.schema_cache_dir = MagicMock()
        mock_settings.schema_cache_dir.mkdir = MagicMock()
        mock_settings.log_level = "WARNING"

        with patch("src.config.get_settings", return_value=mock_settings):
            mod = importlib.import_module(module_path)

        defn_dict = getattr(mod, defn_name)
        handler_dict = getattr(mod, handler_name)

        defn_keys = set(defn_dict.keys())
        handler_keys = set(handler_dict.keys())

        missing_handlers = defn_keys - handler_keys
        missing_defns = handler_keys - defn_keys

        assert not missing_handlers, (
            f"{module_path}: definitions without handlers: {missing_handlers}"
        )
        assert not missing_defns, (
            f"{module_path}: handlers without definitions: {missing_defns}"
        )

    @pytest.mark.parametrize("module_path,defn_name,handler_name", DICT_MODULES)
    def test_definition_callables_return_tool(self, module_path, defn_name, handler_name):
        """Each entry in the definition dict returns a Tool when called."""
        import importlib
        from mcp.types import Tool

        mock_settings = MagicMock()
        mock_settings.api_base_url = "https://api2.panopta.com/v2"
        mock_settings.fortimonitor_api_key = "test_key"
        mock_settings.schema_cache_dir = MagicMock()
        mock_settings.schema_cache_dir.mkdir = MagicMock()
        mock_settings.log_level = "WARNING"

        with patch("src.config.get_settings", return_value=mock_settings):
            mod = importlib.import_module(module_path)

        defn_dict = getattr(mod, defn_name)

        for name, defn_func in defn_dict.items():
            tool = defn_func()
            assert isinstance(tool, Tool), (
                f"{module_path}.{defn_name}['{name}'] did not return a Tool object"
            )
            assert tool.name == name, (
                f"{module_path}: key '{name}' returned tool named '{tool.name}'"
            )
