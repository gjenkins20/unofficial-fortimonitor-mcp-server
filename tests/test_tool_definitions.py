"""
Tool definition schema validation tests for FortiMonitor MCP server.

These tests verify that:
- All tool inputSchemas are valid JSON Schema structures
- Property types are valid JSON Schema types
- Required fields are lists of strings
- Description strings are meaningful (not empty/whitespace)
- No tool has unreasonable numbers of required params (sanity check)
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

VALID_JSON_SCHEMA_TYPES = {"string", "integer", "number", "boolean", "array", "object", "null"}


@pytest.fixture(scope="module")
def all_tools():
    """Load all tool definitions."""
    mock_settings = MagicMock()
    mock_settings.api_base_url = "https://api2.panopta.com/v2"
    mock_settings.fortimonitor_api_key = "test_key"
    mock_settings.schema_cache_dir = MagicMock()
    mock_settings.schema_cache_dir.mkdir = MagicMock()
    mock_settings.log_level = "WARNING"
    mock_settings.mcp_server_name = "test-server"
    mock_settings.mcp_server_version = "0.0.0-test"

    with patch("src.config.get_settings", return_value=mock_settings):
        if "src.server" in sys.modules:
            del sys.modules["src.server"]
        from src.server import _TOOL_DEFINITIONS
    return _TOOL_DEFINITIONS


class TestInputSchemaStructure:
    """Validate inputSchema structure for every tool."""

    def test_properties_is_dict(self, all_tools):
        """inputSchema.properties is a dict."""
        for tool in all_tools:
            props = tool.inputSchema.get("properties")
            assert isinstance(props, dict), (
                f"Tool '{tool.name}': properties is {type(props)}, expected dict"
            )

    def test_property_types_are_valid(self, all_tools):
        """Every property has a valid JSON Schema type."""
        for tool in all_tools:
            for prop_name, prop_def in tool.inputSchema.get("properties", {}).items():
                if "type" in prop_def:
                    prop_type = prop_def["type"]
                    assert prop_type in VALID_JSON_SCHEMA_TYPES, (
                        f"Tool '{tool.name}', property '{prop_name}': "
                        f"invalid type '{prop_type}'"
                    )

    def test_properties_have_descriptions(self, all_tools):
        """Every property has a description string."""
        for tool in all_tools:
            for prop_name, prop_def in tool.inputSchema.get("properties", {}).items():
                desc = prop_def.get("description", "")
                assert desc and desc.strip(), (
                    f"Tool '{tool.name}', property '{prop_name}': "
                    f"missing or empty description"
                )

    def test_required_is_list_of_strings(self, all_tools):
        """The 'required' field, when present, is a list of strings."""
        for tool in all_tools:
            required = tool.inputSchema.get("required")
            if required is not None:
                assert isinstance(required, list), (
                    f"Tool '{tool.name}': 'required' is {type(required)}, "
                    f"expected list"
                )
                for item in required:
                    assert isinstance(item, str), (
                        f"Tool '{tool.name}': required item {item!r} is not a string"
                    )

    def test_required_count_sanity(self, all_tools):
        """No tool requires more than 10 parameters (sanity check)."""
        for tool in all_tools:
            required = tool.inputSchema.get("required", [])
            assert len(required) <= 10, (
                f"Tool '{tool.name}' requires {len(required)} params — "
                f"seems excessive"
            )


class TestToolDescriptionQuality:
    """Check that tool descriptions are meaningful."""

    def test_description_minimum_length(self, all_tools):
        """Tool descriptions are at least 10 characters."""
        for tool in all_tools:
            assert len(tool.description) >= 10, (
                f"Tool '{tool.name}' description is too short: "
                f"'{tool.description}'"
            )

    def test_description_not_placeholder(self, all_tools):
        """Tool descriptions are not placeholder text."""
        placeholders = {"todo", "fixme", "placeholder", "xxx", "tbd"}
        for tool in all_tools:
            desc_lower = tool.description.lower()
            for ph in placeholders:
                assert ph not in desc_lower, (
                    f"Tool '{tool.name}' description contains "
                    f"placeholder text '{ph}'"
                )

    def test_tool_name_appears_logically(self, all_tools):
        """Tool names and descriptions are semantically related.

        Simple heuristic: at least one word from the tool name (ignoring
        common verbs like get/list/create) appears in the description.
        """
        ignore_verbs = {
            "get", "list", "set", "create", "update", "delete",
            "add", "remove", "apply", "generate", "export", "bulk",
            "search", "check", "flush", "run", "request", "force",
        }
        for tool in all_tools:
            name_words = set(tool.name.split("_")) - ignore_verbs
            desc_lower = tool.description.lower()

            # At least one meaningful name word should appear in description
            # Also check singular forms (e.g., "onsights" -> "onsight")
            if name_words:
                expanded = set()
                for w in name_words:
                    expanded.add(w)
                    if w.endswith("s") and len(w) > 3:
                        expanded.add(w[:-1])  # singular
                    if w.endswith("ies") and len(w) > 4:
                        expanded.add(w[:-3] + "y")  # e.g., "histories" -> "history"
                found = any(w in desc_lower for w in expanded)
                assert found, (
                    f"Tool '{tool.name}': none of {expanded} "
                    f"found in description"
                )


class TestSpecificToolGroups:
    """Spot-check expected tools from each priority group are present."""

    def _tool_names(self, all_tools):
        return {t.name for t in all_tools}

    # Phase 1 (original)
    @pytest.mark.parametrize("expected", [
        "get_servers", "get_server_details",
        "get_outages", "check_server_health",
        "get_server_metrics",
        "acknowledge_outage", "add_outage_note", "get_outage_details",
        "set_server_status", "create_maintenance_window",
    ])
    def test_phase1_tools_present(self, all_tools, expected):
        assert expected in self._tool_names(all_tools), f"Missing Phase 1 tool: {expected}"

    # P2 - Cloud, DEM, Compound Services
    @pytest.mark.parametrize("expected", [
        "list_cloud_providers", "list_cloud_credentials",
        "list_dem_applications", "create_dem_application",
        "list_compound_services", "get_compound_service_details",
    ])
    def test_p2_tools_present(self, all_tools, expected):
        assert expected in self._tool_names(all_tools), f"Missing P2 tool: {expected}"

    # P3 - Dashboards, Status Pages, Contacts, Notifications, Network Services
    @pytest.mark.parametrize("expected", [
        "list_dashboards", "list_status_pages",
        "list_rotating_contacts",
        "create_contact", "create_contact_group",
        "create_notification_schedule",
        "list_server_network_services_crud",
    ])
    def test_p3_tools_present(self, all_tools, expected):
        names = self._tool_names(all_tools)
        # Normalize: some tools may have slightly different names
        # Just check that at least a dashboard tool, status_page tool, etc. exist
        if expected == "list_server_network_services_crud":
            # Check any network service CRUD tool exists
            found = any("network_service" in n for n in names)
            assert found, "No network_service tool found (P3)"
        else:
            assert expected in names, f"Missing P3 tool: {expected}"

    # P4 - Users, SNMP, OnSight, Fabric, Countermeasures, Reference Data
    @pytest.mark.parametrize("expected", [
        "list_users", "create_user",
        "list_snmp_credentials", "request_snmp_discovery",
        "list_onsights", "list_onsight_groups",
        "list_fabric_connections",
        "list_network_service_countermeasures",
        "get_agent_resource_threshold",
        "list_outage_countermeasures",
        "get_outage_preoutage_graph",
        "list_account_history",
    ])
    def test_p4_tools_present(self, all_tools, expected):
        names = self._tool_names(all_tools)
        # reference_data tools may have varying names; check presence
        if expected == "list_account_history":
            found = any("account_history" in n for n in names)
            assert found, "No account_history tool found (P4 reference_data)"
        else:
            assert expected in names, f"Missing P4 tool: {expected}"
