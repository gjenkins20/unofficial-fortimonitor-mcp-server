"""
Tests for composite operation tools.

Verifies that all 5 composite tools are defined, have handlers,
and produce correct output from mocked API responses.
"""

import json
import pytest
from unittest.mock import MagicMock

from src.tools.composite import (
    COMPOSITE_TOOL_DEFINITIONS,
    COMPOSITE_HANDLERS,
    handle_investigate_server,
    handle_compare_servers,
    handle_audit_monitoring_coverage,
    handle_generate_incident_timeline,
    handle_find_flapping_servers,
)


class TestCompositeDefinitions:
    """Verify composite tool definitions."""

    def test_tool_count(self):
        assert len(COMPOSITE_TOOL_DEFINITIONS) == 5

    def test_handler_count(self):
        assert len(COMPOSITE_HANDLERS) == 5

    def test_all_tools_have_handlers(self):
        for name in COMPOSITE_TOOL_DEFINITIONS:
            assert name in COMPOSITE_HANDLERS, f"Tool '{name}' missing handler"

    @pytest.mark.parametrize("name", [
        "investigate_server",
        "compare_servers",
        "audit_monitoring_coverage",
        "generate_incident_timeline",
        "find_flapping_servers",
    ])
    def test_tool_definition_valid(self, name):
        tool = COMPOSITE_TOOL_DEFINITIONS[name]()
        assert tool.name == name
        assert tool.description
        assert tool.inputSchema


@pytest.fixture
def mock_client():
    """Create a mock FortiMonitor client."""
    client = MagicMock()
    client._request = MagicMock(return_value={"success": True})
    return client


class TestInvestigateServer:

    @pytest.mark.asyncio
    async def test_returns_report(self, mock_client):
        mock_client._request.return_value = {"name": "test-server", "fqdn": "test.example.com"}
        result = await handle_investigate_server({"server_id": 123}, mock_client)
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "investigation_report" in data
        assert data["investigation_report"]["server_id"] == 123

    @pytest.mark.asyncio
    async def test_handles_api_error(self, mock_client):
        mock_client._request.side_effect = Exception("API error")
        result = await handle_investigate_server({"server_id": 999}, mock_client)
        assert len(result) == 1
        data = json.loads(result[0].text)
        # Should return None for each section instead of raising
        report = data["investigation_report"]
        assert report["server_details"] is None


class TestCompareServers:

    @pytest.mark.asyncio
    async def test_returns_comparison(self, mock_client):
        mock_client._request.return_value = {"name": "server-a"}
        result = await handle_compare_servers({"server_id_1": 1, "server_id_2": 2}, mock_client)
        data = json.loads(result[0].text)
        assert "server_comparison" in data
        assert data["server_comparison"]["server_1"]["id"] == 1
        assert data["server_comparison"]["server_2"]["id"] == 2


class TestAuditMonitoringCoverage:

    @pytest.mark.asyncio
    async def test_returns_audit(self, mock_client):
        mock_client._request.side_effect = [
            # First call: server list
            {"server_list": [
                {"url": "/server/10", "name": "server-a"},
                {"url": "/server/20", "name": "server-b"},
            ]},
            # Second call: network services for server 10
            {"network_service_list": []},
            # Third call: network services for server 20
            {"network_service_list": [{"name": "HTTP"}]},
        ]
        result = await handle_audit_monitoring_coverage({}, mock_client)
        data = json.loads(result[0].text)
        audit = data["monitoring_coverage_audit"]
        assert audit["summary"]["total_servers_audited"] == 2
        assert len(audit["no_network_services"]) == 1
        assert audit["no_network_services"][0]["name"] == "server-a"

    @pytest.mark.asyncio
    async def test_handles_empty_server_list(self, mock_client):
        mock_client._request.return_value = {"server_list": []}
        result = await handle_audit_monitoring_coverage({}, mock_client)
        assert "No servers found" in result[0].text


class TestGenerateIncidentTimeline:

    @pytest.mark.asyncio
    async def test_returns_timeline(self, mock_client):
        mock_client._request.side_effect = [
            # Outage details
            {"outage_id": 555, "status": "active", "server_url": "/server/10"},
            # Notes
            {"note_list": [{"text": "Investigating"}]},
            # Server info
            {"name": "web-01"},
        ]
        result = await handle_generate_incident_timeline({"outage_id": 555}, mock_client)
        data = json.loads(result[0].text)
        assert data["incident_timeline"]["outage_id"] == 555


class TestFindFlappingServers:

    @pytest.mark.asyncio
    async def test_returns_flapping(self, mock_client):
        mock_client._request.side_effect = [
            # Server list
            {"server_list": [
                {"url": "/server/1", "name": "flapper"},
            ]},
            # Outages for server 1
            {"outage_list": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]},
        ]
        result = await handle_find_flapping_servers({"min_outage_count": 3}, mock_client)
        data = json.loads(result[0].text)
        assert data["flapping_servers"]["servers_found"] == 1
        assert data["flapping_servers"]["servers"][0]["outage_count"] == 4

    @pytest.mark.asyncio
    async def test_no_flapping_when_below_threshold(self, mock_client):
        mock_client._request.side_effect = [
            {"server_list": [{"url": "/server/1", "name": "stable"}]},
            {"outage_list": [{"id": 1}]},
        ]
        result = await handle_find_flapping_servers({"min_outage_count": 5}, mock_client)
        data = json.loads(result[0].text)
        assert data["flapping_servers"]["servers_found"] == 0
