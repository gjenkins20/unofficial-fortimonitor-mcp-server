"""Tests for MCP tools."""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Helper to build API-like URLs
API_BASE = "https://api2.panopta.com/v2"


class TestServerTools:
    """Tests for server-related MCP tools."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock FortiMonitorClient."""
        client = MagicMock()
        return client

    def test_get_servers_tool_definition(self):
        """Test get_servers tool definition."""
        from src.tools.servers import get_servers_tool_definition

        tool = get_servers_tool_definition()

        assert tool.name == "get_servers"
        assert "FortiMonitor" in tool.description
        assert "inputSchema" in dir(tool)
        assert tool.inputSchema["type"] == "object"
        assert "name" in tool.inputSchema["properties"]
        assert "limit" in tool.inputSchema["properties"]

    def test_get_server_details_tool_definition(self):
        """Test get_server_details tool definition."""
        from src.tools.servers import get_server_details_tool_definition

        tool = get_server_details_tool_definition()

        assert tool.name == "get_server_details"
        assert "required" in tool.inputSchema
        assert "server_id" in tool.inputSchema["required"]

    @pytest.mark.asyncio
    async def test_handle_get_servers_success(self, mock_client):
        """Test successful get_servers execution."""
        from src.tools.servers import handle_get_servers
        from src.fortimonitor.models import ServerListResponse, Server

        mock_client.get_servers.return_value = ServerListResponse(
            server_list=[
                Server(url=f"{API_BASE}/server/1", name="test-server-1"),
                Server(url=f"{API_BASE}/server/2", name="test-server-2"),
            ],
            meta={"limit": 50, "offset": 0, "total_count": 2},
        )

        result = await handle_get_servers({"limit": 50}, mock_client)

        assert len(result) == 1
        assert result[0].type == "text"
        assert "test-server-1" in result[0].text
        assert "test-server-2" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_get_servers_empty(self, mock_client):
        """Test get_servers with no results."""
        from src.tools.servers import handle_get_servers
        from src.fortimonitor.models import ServerListResponse

        mock_client.get_servers.return_value = ServerListResponse(
            server_list=[],
            meta={"limit": 50, "offset": 0, "total_count": 0},
        )

        result = await handle_get_servers({}, mock_client)

        assert len(result) == 1
        assert "No servers found" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_get_server_details_success(self, mock_client):
        """Test successful get_server_details execution."""
        from src.tools.servers import handle_get_server_details
        from src.fortimonitor.models import Server

        mock_client.get_server_details.return_value = Server(
            url=f"{API_BASE}/server/123",
            name="production-web-01",
            fqdn="web01.example.com",
            status="active",
        )

        result = await handle_get_server_details({"server_id": 123}, mock_client)

        assert len(result) == 1
        assert "production-web-01" in result[0].text
        assert "web01.example.com" in result[0].text


class TestOutageTools:
    """Tests for outage-related MCP tools."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock FortiMonitorClient."""
        client = MagicMock()
        return client

    def test_get_outages_tool_definition(self):
        """Test get_outages tool definition."""
        from src.tools.outages import get_outages_tool_definition

        tool = get_outages_tool_definition()

        assert tool.name == "get_outages"
        assert "outages" in tool.description.lower()
        assert "hours_back" in tool.inputSchema["properties"]
        assert "active_only" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_handle_get_outages_success(self, mock_client):
        """Test successful get_outages execution."""
        from src.tools.outages import handle_get_outages
        from src.fortimonitor.models import OutageListResponse, Outage
        from datetime import datetime

        mock_client.get_outages.return_value = OutageListResponse(
            outage_list=[
                Outage(
                    url=f"{API_BASE}/outage/1",
                    severity="critical",
                    status="active",
                    start_time=datetime.now(),
                    server_name="test-server",
                )
            ],
            meta={"limit": 50, "offset": 0, "total_count": 1},
        )

        result = await handle_get_outages({"hours_back": 24}, mock_client)

        assert len(result) == 1
        assert "CRITICAL" in result[0].text
        assert "test-server" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_get_outages_active_only(self, mock_client):
        """Test get_outages with active_only flag."""
        from src.tools.outages import handle_get_outages
        from src.fortimonitor.models import OutageListResponse

        mock_client.get_active_outages.return_value = OutageListResponse(
            outage_list=[],
            meta={"limit": 50, "offset": 0, "total_count": 0},
        )

        result = await handle_get_outages({"active_only": True}, mock_client)

        mock_client.get_active_outages.assert_called_once()
        assert "No outages found" in result[0].text


class TestMetricsTools:
    """Tests for metrics-related MCP tools."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock FortiMonitorClient."""
        client = MagicMock()
        return client

    def test_get_server_metrics_tool_definition(self):
        """Test get_server_metrics tool definition."""
        from src.tools.metrics import get_server_metrics_tool_definition

        tool = get_server_metrics_tool_definition()

        assert tool.name == "get_server_metrics"
        assert "required" in tool.inputSchema
        assert "server_id" in tool.inputSchema["required"]

    @pytest.mark.asyncio
    async def test_handle_get_server_metrics_success(self, mock_client):
        """Test successful get_server_metrics execution."""
        from src.tools.metrics import handle_get_server_metrics
        from src.fortimonitor.models import AgentResourceListResponse, AgentResource

        mock_client.get_server_agent_resources.return_value = AgentResourceListResponse(
            agent_resource_list=[
                AgentResource(
                    url=f"{API_BASE}/server/123/agent_resource/1",
                    name="CPU Usage",
                    agent_resource_type="cpu",
                    current_value=45.2,
                    unit="%",
                ),
                AgentResource(
                    url=f"{API_BASE}/server/123/agent_resource/2",
                    name="Memory Usage",
                    agent_resource_type="memory",
                    current_value=72.5,
                    unit="%",
                ),
            ],
            meta={"limit": 50, "offset": 0, "total_count": 2},
        )

        result = await handle_get_server_metrics({"server_id": 123}, mock_client)

        assert len(result) == 1
        assert "CPU Usage" in result[0].text
        assert "Memory Usage" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_get_server_metrics_empty(self, mock_client):
        """Test get_server_metrics with no resources."""
        from src.tools.metrics import handle_get_server_metrics
        from src.fortimonitor.models import AgentResourceListResponse

        mock_client.get_server_agent_resources.return_value = AgentResourceListResponse(
            agent_resource_list=[],
            meta={"limit": 50, "offset": 0, "total_count": 0},
        )

        result = await handle_get_server_metrics({"server_id": 123}, mock_client)

        assert "No agent resources" in result[0].text
