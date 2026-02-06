"""
Handler tests for dict-based tool modules (P2–P4).

These tests verify that handlers:
- Return List[TextContent] on success
- Call client._request with the correct HTTP method and endpoint path
- Handle empty results gracefully
- Handle API errors gracefully (return error text, don't raise)
- Handle NotFoundError gracefully
- Validate required arguments
"""

import pytest
from unittest.mock import MagicMock, call
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp.types import TextContent
from src.fortimonitor.exceptions import APIError, NotFoundError


# ===================================================================
# Users (P4)
# ===================================================================

class TestUsersHandlers:
    """Test user management tool handlers."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_list_users_success(self, mock_client):
        from src.tools.users import handle_list_users

        mock_client._request.return_value = {
            "user_list": [
                {"name": "Alice", "url": "/v2/user/1", "email": "alice@example.com"},
                {"name": "Bob", "url": "/v2/user/2", "email": "bob@example.com"},
            ],
            "meta": {"total_count": 2},
        }

        result = await handle_list_users({"limit": 50}, mock_client)

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Alice" in result[0].text
        assert "Bob" in result[0].text
        mock_client._request.assert_called_once_with(
            "GET", "user", params={"limit": 50}
        )

    @pytest.mark.asyncio
    async def test_list_users_empty(self, mock_client):
        from src.tools.users import handle_list_users

        mock_client._request.return_value = {"user_list": [], "meta": {}}

        result = await handle_list_users({}, mock_client)
        assert "No users found" in result[0].text

    @pytest.mark.asyncio
    async def test_get_user_details_success(self, mock_client):
        from src.tools.users import handle_get_user_details

        mock_client._request.return_value = {
            "name": "Alice",
            "email": "alice@example.com",
            "role": "admin",
            "url": "/v2/user/1",
        }

        result = await handle_get_user_details({"user_id": 1}, mock_client)
        assert "Alice" in result[0].text
        assert "admin" in result[0].text

    @pytest.mark.asyncio
    async def test_get_user_details_not_found(self, mock_client):
        from src.tools.users import handle_get_user_details

        mock_client._request.side_effect = NotFoundError("Not found")

        result = await handle_get_user_details({"user_id": 999}, mock_client)
        assert "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_client):
        from src.tools.users import handle_create_user

        mock_client._request.return_value = {"url": "/v2/user/42"}

        result = await handle_create_user(
            {"name": "New User", "email": "new@example.com"}, mock_client
        )
        assert "Created" in result[0].text
        assert "42" in result[0].text

    @pytest.mark.asyncio
    async def test_update_user_no_fields(self, mock_client):
        from src.tools.users import handle_update_user

        result = await handle_update_user({"user_id": 1}, mock_client)
        assert "Error" in result[0].text
        assert "at least one" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_user_success(self, mock_client):
        from src.tools.users import handle_update_user

        mock_client._request.return_value = {"success": True}

        result = await handle_update_user(
            {"user_id": 1, "name": "Updated"}, mock_client
        )
        assert "Updated" in result[0].text

    @pytest.mark.asyncio
    async def test_delete_user_success(self, mock_client):
        from src.tools.users import handle_delete_user

        # First call: GET to fetch name, second call: DELETE
        mock_client._request.side_effect = [
            {"name": "Old User"},
            {"success": True},
        ]

        result = await handle_delete_user({"user_id": 5}, mock_client)
        assert "Deleted" in result[0].text
        assert "Old User" in result[0].text

    @pytest.mark.asyncio
    async def test_get_user_addons_success(self, mock_client):
        from src.tools.users import handle_get_user_addons

        mock_client._request.return_value = {"addon_count": 3, "plan": "premium"}

        result = await handle_get_user_addons({}, mock_client)
        assert "Addons" in result[0].text

    @pytest.mark.asyncio
    async def test_api_error_returns_error_text(self, mock_client):
        from src.tools.users import handle_list_users

        mock_client._request.side_effect = APIError("Server error")

        result = await handle_list_users({}, mock_client)
        assert "Error" in result[0].text


# ===================================================================
# Fabric (P4)
# ===================================================================

class TestFabricHandlers:
    """Test fabric connection tool handlers."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_list_fabric_connections_success(self, mock_client):
        from src.tools.fabric import handle_list_fabric_connections

        mock_client._request.return_value = {
            "fabric_connection_list": [
                {"name": "FortiGate Link", "url": "/v2/fabric_connection/10"},
            ],
            "meta": {"total_count": 1},
        }

        result = await handle_list_fabric_connections({"limit": 50}, mock_client)
        assert "FortiGate Link" in result[0].text
        mock_client._request.assert_called_once_with(
            "GET", "fabric_connection", params={"limit": 50}
        )

    @pytest.mark.asyncio
    async def test_list_fabric_connections_empty(self, mock_client):
        from src.tools.fabric import handle_list_fabric_connections

        mock_client._request.return_value = {
            "fabric_connection_list": [], "meta": {}
        }

        result = await handle_list_fabric_connections({}, mock_client)
        assert "No fabric connections found" in result[0].text

    @pytest.mark.asyncio
    async def test_create_fabric_connection_success(self, mock_client):
        from src.tools.fabric import handle_create_fabric_connection

        mock_client._request.return_value = {"url": "/v2/fabric_connection/99"}

        result = await handle_create_fabric_connection(
            {"name": "New Link"}, mock_client
        )
        assert "Created" in result[0].text
        assert "99" in result[0].text

    @pytest.mark.asyncio
    async def test_delete_fabric_connection_not_found(self, mock_client):
        from src.tools.fabric import handle_delete_fabric_connection

        mock_client._request.side_effect = NotFoundError("Not found")

        result = await handle_delete_fabric_connection(
            {"connection_id": 999}, mock_client
        )
        assert "not found" in result[0].text.lower()


# ===================================================================
# Countermeasures (P4)
# ===================================================================

class TestCountermeasuresHandlers:
    """Test countermeasure and threshold tool handlers."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_list_network_service_countermeasures(self, mock_client):
        from src.tools.countermeasures import handle_list_network_service_countermeasures

        mock_client._request.return_value = {
            "countermeasure_list": [
                {"name": "Restart Service", "url": "/v2/cm/1"},
            ],
            "meta": {"total_count": 1},
        }

        result = await handle_list_network_service_countermeasures(
            {"server_id": 1, "ns_id": 2}, mock_client
        )
        assert "Restart Service" in result[0].text
        mock_client._request.assert_called_once_with(
            "GET",
            "server/1/network_service/2/countermeasure",
            params={"limit": 50},
        )

    @pytest.mark.asyncio
    async def test_list_network_service_countermeasures_empty(self, mock_client):
        from src.tools.countermeasures import handle_list_network_service_countermeasures

        mock_client._request.return_value = {
            "countermeasure_list": [], "meta": {}
        }

        result = await handle_list_network_service_countermeasures(
            {"server_id": 1, "ns_id": 2}, mock_client
        )
        assert "No countermeasures found" in result[0].text

    @pytest.mark.asyncio
    async def test_create_network_service_countermeasure(self, mock_client):
        from src.tools.countermeasures import handle_create_network_service_countermeasure

        mock_client._request.return_value = {
            "url": "/v2/server/1/network_service/2/countermeasure/5"
        }

        result = await handle_create_network_service_countermeasure(
            {"server_id": 1, "ns_id": 2, "name": "Auto-fix", "script": "echo ok"},
            mock_client,
        )
        assert "Created" in result[0].text

    @pytest.mark.asyncio
    async def test_update_ns_countermeasure_no_fields(self, mock_client):
        from src.tools.countermeasures import handle_update_network_service_countermeasure

        result = await handle_update_network_service_countermeasure(
            {"server_id": 1, "ns_id": 2, "cm_id": 3}, mock_client
        )
        assert "Error" in result[0].text

    @pytest.mark.asyncio
    async def test_delete_network_service_countermeasure(self, mock_client):
        from src.tools.countermeasures import handle_delete_network_service_countermeasure

        mock_client._request.return_value = {"success": True}

        result = await handle_delete_network_service_countermeasure(
            {"server_id": 1, "ns_id": 2, "cm_id": 3}, mock_client
        )
        assert "Deleted" in result[0].text

    @pytest.mark.asyncio
    async def test_get_agent_resource_threshold(self, mock_client):
        from src.tools.countermeasures import handle_get_agent_resource_threshold

        mock_client._request.return_value = {
            "name": "CPU Warn",
            "warning_threshold": 80,
            "critical_threshold": 95,
        }

        result = await handle_get_agent_resource_threshold(
            {"server_id": 1, "ar_id": 10, "threshold_id": 5}, mock_client
        )
        assert "CPU Warn" in result[0].text
        assert "80" in result[0].text
        assert "95" in result[0].text

    @pytest.mark.asyncio
    async def test_update_threshold_no_fields(self, mock_client):
        from src.tools.countermeasures import handle_update_agent_resource_threshold

        result = await handle_update_agent_resource_threshold(
            {"server_id": 1, "ar_id": 10, "threshold_id": 5}, mock_client
        )
        assert "Error" in result[0].text

    @pytest.mark.asyncio
    async def test_update_threshold_success(self, mock_client):
        from src.tools.countermeasures import handle_update_agent_resource_threshold

        mock_client._request.return_value = {"success": True}

        result = await handle_update_agent_resource_threshold(
            {
                "server_id": 1,
                "ar_id": 10,
                "threshold_id": 5,
                "warning_threshold": 70,
                "critical_threshold": 90,
            },
            mock_client,
        )
        assert "Updated" in result[0].text

    @pytest.mark.asyncio
    async def test_list_outage_countermeasures(self, mock_client):
        from src.tools.countermeasures import handle_list_outage_countermeasures

        mock_client._request.return_value = {
            "countermeasure_list": [
                {"name": "Restart", "url": "/v2/cm/1", "status": "completed"},
            ],
            "meta": {"total_count": 1},
        }

        result = await handle_list_outage_countermeasures(
            {"outage_id": 100}, mock_client
        )
        assert "Restart" in result[0].text

    @pytest.mark.asyncio
    async def test_get_outage_preoutage_graph(self, mock_client):
        from src.tools.countermeasures import handle_get_outage_preoutage_graph

        mock_client._request.return_value = {
            "data": [
                {"time": "2026-01-30T09:55:00Z", "value": 45.2},
                {"time": "2026-01-30T09:56:00Z", "value": 72.1},
            ]
        }

        result = await handle_get_outage_preoutage_graph(
            {"outage_id": 100}, mock_client
        )
        assert "Pre-Outage Graph" in result[0].text
        assert "Data Points: 2" in result[0].text

    @pytest.mark.asyncio
    async def test_list_threshold_countermeasures_endpoint(self, mock_client):
        """Verify the deeply nested endpoint path is correct."""
        from src.tools.countermeasures import handle_list_threshold_countermeasures

        mock_client._request.return_value = {
            "countermeasure_list": [], "meta": {}
        }

        await handle_list_threshold_countermeasures(
            {"server_id": 1, "ar_id": 2, "threshold_id": 3}, mock_client
        )

        mock_client._request.assert_called_once_with(
            "GET",
            "server/1/agent_resource/2/agent_resource_threshold/3/countermeasure",
            params={"limit": 50},
        )


# ===================================================================
# SNMP (P4) — endpoint path checks
# ===================================================================

class TestSNMPHandlerEndpoints:
    """Verify SNMP handlers call the correct API endpoints."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock(return_value={
            "snmp_credential_list": [], "snmp_resource_list": [],
            "meta": {}, "success": True,
        })
        return client

    @pytest.mark.asyncio
    async def test_list_snmp_credentials_endpoint(self, mock_client):
        from src.tools.snmp import handle_list_snmp_credentials

        await handle_list_snmp_credentials({}, mock_client)
        mock_client._request.assert_called_once()
        call_args = mock_client._request.call_args
        assert call_args[0][0] == "GET"
        assert "snmp_credential" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_request_snmp_discovery_endpoint(self, mock_client):
        from src.tools.snmp import handle_request_snmp_discovery

        await handle_request_snmp_discovery({"server_id": 42}, mock_client)
        call_args = mock_client._request.call_args
        assert call_args[0][0] == "PUT"
        assert "server/42/snmp_discovery" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_snmp_resource_metric_endpoint(self, mock_client):
        from src.tools.snmp import handle_get_snmp_resource_metric

        mock_client._request.return_value = {}

        await handle_get_snmp_resource_metric(
            {"server_id": 1, "resource_id": 2, "timescale": "day"}, mock_client
        )
        call_args = mock_client._request.call_args
        assert "server/1/snmp_resource/2/metric/day" in call_args[0][1]


# ===================================================================
# OnSight (P4) — basic handler tests
# ===================================================================

class TestOnSightHandlers:
    """Test OnSight tool handlers."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_list_onsights_success(self, mock_client):
        from src.tools.onsight import handle_list_onsights

        mock_client._request.return_value = {
            "onsight_list": [
                {"name": "OnSight-1", "url": "/v2/onsight/1"},
            ],
            "meta": {"total_count": 1},
        }

        result = await handle_list_onsights({}, mock_client)
        assert "OnSight-1" in result[0].text

    @pytest.mark.asyncio
    async def test_list_onsights_empty(self, mock_client):
        from src.tools.onsight import handle_list_onsights

        mock_client._request.return_value = {
            "onsight_list": [], "meta": {}
        }

        result = await handle_list_onsights({}, mock_client)
        assert "No" in result[0].text or "no" in result[0].text

    @pytest.mark.asyncio
    async def test_list_onsight_groups_endpoint(self, mock_client):
        from src.tools.onsight import handle_list_onsight_groups

        mock_client._request.return_value = {
            "onsight_group_list": [], "meta": {}
        }

        await handle_list_onsight_groups({}, mock_client)
        call_args = mock_client._request.call_args
        assert "onsight_group" in call_args[0][1]


# ===================================================================
# Reference Data (P4) — basic handler tests
# ===================================================================

class TestReferenceDataHandlers:
    """Test reference data tool handlers."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_list_timezones(self, mock_client):
        from src.tools.reference_data import handle_list_timezones

        mock_client._request.return_value = {
            "timezone_list": [
                {"name": "US/Eastern", "url": "/v2/timezone/1"},
                {"name": "US/Pacific", "url": "/v2/timezone/2"},
            ],
            "meta": {"total_count": 2},
        }

        result = await handle_list_timezones({}, mock_client)
        assert "US/Eastern" in result[0].text or "timezone" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_list_roles(self, mock_client):
        from src.tools.reference_data import handle_list_roles

        mock_client._request.return_value = {
            "role_list": [
                {"name": "Admin", "url": "/v2/role/1"},
            ],
            "meta": {"total_count": 1},
        }

        result = await handle_list_roles({}, mock_client)
        assert "Admin" in result[0].text or "role" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_client):
        from src.tools.reference_data import handle_list_timezones

        mock_client._request.side_effect = APIError("Server error")

        result = await handle_list_timezones({}, mock_client)
        assert "Error" in result[0].text


# ===================================================================
# Cloud (P2) — endpoint path checks
# ===================================================================

class TestCloudHandlerEndpoints:
    """Verify cloud handlers call the correct API endpoints."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock(return_value={
            "cloud_provider_list": [], "cloud_credential_list": [],
            "cloud_region_list": [], "cloud_service_list": [],
            "meta": {},
        })
        return client

    @pytest.mark.asyncio
    async def test_list_cloud_providers(self, mock_client):
        from src.tools.cloud import handle_list_cloud_providers

        await handle_list_cloud_providers({}, mock_client)
        call_args = mock_client._request.call_args
        assert call_args[0][0] == "GET"
        assert "cloud_provider" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_list_cloud_credentials(self, mock_client):
        from src.tools.cloud import handle_list_cloud_credentials

        await handle_list_cloud_credentials({}, mock_client)
        call_args = mock_client._request.call_args
        assert "cloud_credential" in call_args[0][1]


# ===================================================================
# Monitoring Nodes + Network Service Types (P3 leftovers)
# ===================================================================

class TestMonitoringNodesHandlers:
    """Test monitoring node tool handlers."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_list_monitoring_nodes(self, mock_client):
        from src.tools.monitoring_nodes import handle_list_monitoring_nodes

        mock_client._request.return_value = {
            "monitoring_node_list": [
                {"name": "us-east-1", "url": "/v2/monitoring_node/1"},
            ],
            "meta": {"total_count": 1},
        }

        result = await handle_list_monitoring_nodes({}, mock_client)
        assert "us-east-1" in result[0].text

    @pytest.mark.asyncio
    async def test_list_monitoring_nodes_empty(self, mock_client):
        from src.tools.monitoring_nodes import handle_list_monitoring_nodes

        mock_client._request.return_value = {
            "monitoring_node_list": [], "meta": {}
        }

        result = await handle_list_monitoring_nodes({}, mock_client)
        text = result[0].text.lower()
        assert "no" in text or "0" in text or "empty" in text


class TestNetworkServiceTypesHandlers:
    """Test network service type tool handlers."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_list_network_service_types(self, mock_client):
        from src.tools.network_service_types import handle_list_network_service_types

        mock_client._request.return_value = {
            "network_service_type_list": [
                {"name": "HTTP", "url": "/v2/network_service_type/1"},
            ],
            "meta": {"total_count": 1},
        }

        result = await handle_list_network_service_types({}, mock_client)
        assert "HTTP" in result[0].text
