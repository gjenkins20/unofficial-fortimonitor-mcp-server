"""
Tests for MCP Resource data feeds.

Verifies that all 4 resources are defined, have handlers,
and produce valid JSON from mocked API responses.
"""

import json
import pytest
from unittest.mock import MagicMock

from src.resources.feeds import (
    RESOURCES,
    RESOURCE_HANDLERS,
    read_active_outages,
    read_health_summary,
    read_upcoming_maintenance,
    read_recent_alerts,
)


class TestResourceDefinitions:

    def test_resource_count(self):
        assert len(RESOURCES) == 4

    def test_handler_count(self):
        assert len(RESOURCE_HANDLERS) == 4

    def test_all_resources_have_handlers(self):
        for resource in RESOURCES:
            uri = str(resource.uri)
            assert uri in RESOURCE_HANDLERS, f"Resource '{uri}' missing handler"

    @pytest.mark.parametrize("uri", [
        "fortimonitor://outages/active",
        "fortimonitor://health/summary",
        "fortimonitor://maintenance/upcoming",
        "fortimonitor://alerts/recent",
    ])
    def test_resource_uri_in_handlers(self, uri):
        assert uri in RESOURCE_HANDLERS

    def test_resources_have_descriptions(self):
        for resource in RESOURCES:
            assert resource.description
            assert resource.name
            assert resource.mimeType == "application/json"


@pytest.fixture
def mock_client():
    client = MagicMock()
    client._request = MagicMock(return_value={})
    return client


class TestActiveOutages:

    @pytest.mark.asyncio
    async def test_returns_outage_list(self, mock_client):
        mock_client._request.return_value = {
            "outage_list": [{"id": 1, "status": "active"}]
        }
        result = await read_active_outages(mock_client)
        data = json.loads(result)
        assert data["active_outages"]["count"] == 1

    @pytest.mark.asyncio
    async def test_handles_empty(self, mock_client):
        mock_client._request.return_value = {"outage_list": []}
        result = await read_active_outages(mock_client)
        data = json.loads(result)
        assert data["active_outages"]["count"] == 0

    @pytest.mark.asyncio
    async def test_handles_api_error(self, mock_client):
        mock_client._request.side_effect = Exception("API down")
        result = await read_active_outages(mock_client)
        data = json.loads(result)
        assert data["active_outages"]["count"] == 0


class TestHealthSummary:

    @pytest.mark.asyncio
    async def test_returns_summary(self, mock_client):
        mock_client._request.side_effect = [
            {"server_list": [{"id": 1}], "meta": {"total_count": 100}},
            {"outage_list": [{"id": 1}], "meta": {"total_count": 5}},
        ]
        result = await read_health_summary(mock_client)
        data = json.loads(result)
        assert data["health_summary"]["total_servers"] == 100
        assert data["health_summary"]["active_outage_count"] == 5
        assert data["health_summary"]["servers_up"] == 95


class TestUpcomingMaintenance:

    @pytest.mark.asyncio
    async def test_returns_schedules(self, mock_client):
        mock_client._request.return_value = {
            "maintenance_schedule_list": [{"id": 1, "name": "Patch Tuesday"}]
        }
        result = await read_upcoming_maintenance(mock_client)
        data = json.loads(result)
        assert data["upcoming_maintenance"]["count"] == 1


class TestRecentAlerts:

    @pytest.mark.asyncio
    async def test_returns_alerts(self, mock_client):
        mock_client._request.return_value = {
            "outage_list": [{"id": 1}, {"id": 2}]
        }
        result = await read_recent_alerts(mock_client)
        data = json.loads(result)
        assert data["recent_alerts"]["count"] == 2
