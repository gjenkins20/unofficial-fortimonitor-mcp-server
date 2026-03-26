"""Tests for license utilization and addon catalog tools."""

import pytest
from unittest.mock import MagicMock, call
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp.types import TextContent
from src.fortimonitor.exceptions import APIError


class TestGetLicenseUtilization:
    """Test get_license_utilization handler."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_utilization_without_entitlements(self, mock_client, monkeypatch):
        """Test report without LICENSE_ENTITLEMENTS configured."""
        from src.tools.license_utilization import handle_get_license_utilization

        monkeypatch.delenv("LICENSE_ENTITLEMENTS", raising=False)

        mock_client._request.side_effect = [
            # GET /server
            {
                "server_list": [
                    {"billing_type": "instance.basic", "device_type": "server", "device_sub_type": ""},
                    {"billing_type": "instance.basic", "device_type": "server", "device_sub_type": ""},
                    {"billing_type": "instance.advanced", "device_type": "network_device", "device_sub_type": "fortinet.fortigate"},
                ],
                "meta": {"total_count": 3},
            },
            # GET /addon
            {
                "addon_list": [
                    {"textkey": "instance.basic", "name": "Basic Node"},
                    {"textkey": "instance.advanced", "name": "Advanced Node"},
                ],
                "meta": {"total_count": 2},
            },
        ]

        result = await handle_get_license_utilization({}, mock_client)

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        text = result[0].text
        assert "License Utilization Report" in text
        assert "Basic Node: 2 active" in text
        assert "Advanced Node: 1 active" in text
        assert "Total Instances: 3" in text
        assert "Configure LICENSE_ENTITLEMENTS" in text
        assert "support.fortinet.com" in text

    @pytest.mark.asyncio
    async def test_utilization_with_entitlements(self, mock_client, monkeypatch):
        """Test report with LICENSE_ENTITLEMENTS configured."""
        from src.tools.license_utilization import handle_get_license_utilization

        monkeypatch.setenv(
            "LICENSE_ENTITLEMENTS",
            '{"instance.basic": 100, "instance.advanced": 10}',
        )

        mock_client._request.side_effect = [
            # GET /server
            {
                "server_list": [
                    {"billing_type": "instance.basic", "device_type": "server", "device_sub_type": ""},
                    {"billing_type": "instance.basic", "device_type": "server", "device_sub_type": ""},
                    {"billing_type": "instance.advanced", "device_type": "network_device", "device_sub_type": "fortinet.fortigate"},
                    {"billing_type": "instance.advanced", "device_type": "network_device", "device_sub_type": "fortinet.fortigate"},
                    {"billing_type": "instance.advanced", "device_type": "network_device", "device_sub_type": "fortinet.fortigate"},
                    {"billing_type": "instance.advanced", "device_type": "cloud", "device_sub_type": "aws.ec2"},
                    {"billing_type": "instance.advanced", "device_type": "cloud", "device_sub_type": "aws.ec2"},
                    {"billing_type": "instance.advanced", "device_type": "cloud", "device_sub_type": "aws.ec2"},
                    {"billing_type": "instance.advanced", "device_type": "cloud", "device_sub_type": "aws.ec2"},
                    {"billing_type": "instance.advanced", "device_type": "cloud", "device_sub_type": "aws.ec2"},
                    {"billing_type": "instance.advanced", "device_type": "server", "device_sub_type": ""},
                    {"billing_type": "instance.advanced", "device_type": "server", "device_sub_type": ""},
                ],
                "meta": {"total_count": 12},
            },
            # GET /addon
            {
                "addon_list": [
                    {"textkey": "instance.basic", "name": "Basic Node"},
                    {"textkey": "instance.advanced", "name": "Advanced Node"},
                ],
                "meta": {"total_count": 2},
            },
        ]

        result = await handle_get_license_utilization({}, mock_client)

        text = result[0].text
        assert "Advanced Node: 10 / 10 used (100.0%)" in text
        assert "Basic Node: 2 / 100 used (2.0%)" in text
        assert "Total Instances: 12" in text
        assert "OVER LIMIT" in text

    @pytest.mark.asyncio
    async def test_utilization_high_usage_warning(self, mock_client, monkeypatch):
        """Test warning when utilization exceeds 80%."""
        from src.tools.license_utilization import handle_get_license_utilization

        monkeypatch.setenv("LICENSE_ENTITLEMENTS", '{"instance.basic": 10}')

        mock_client._request.side_effect = [
            {
                "server_list": [
                    {"billing_type": "instance.basic", "device_type": "server", "device_sub_type": ""}
                    for _ in range(9)
                ],
                "meta": {"total_count": 9},
            },
            {"addon_list": [{"textkey": "instance.basic", "name": "Basic Node"}], "meta": {}},
        ]

        result = await handle_get_license_utilization({}, mock_client)

        text = result[0].text
        assert "90.0%" in text
        assert "HIGH USAGE" in text

    @pytest.mark.asyncio
    async def test_utilization_empty_servers(self, mock_client, monkeypatch):
        """Test report with no servers."""
        from src.tools.license_utilization import handle_get_license_utilization

        monkeypatch.delenv("LICENSE_ENTITLEMENTS", raising=False)

        mock_client._request.side_effect = [
            {"server_list": [], "meta": {"total_count": 0}},
            {"addon_list": [], "meta": {}},
        ]

        result = await handle_get_license_utilization({}, mock_client)

        text = result[0].text
        assert "Total Instances: 0" in text

    @pytest.mark.asyncio
    async def test_utilization_pagination(self, mock_client, monkeypatch):
        """Test that pagination fetches all servers."""
        from src.tools.license_utilization import handle_get_license_utilization

        monkeypatch.delenv("LICENSE_ENTITLEMENTS", raising=False)

        # First page: 500 servers, total_count says 502
        page1_servers = [
            {"billing_type": "instance.basic", "device_type": "server", "device_sub_type": ""}
            for _ in range(500)
        ]
        page2_servers = [
            {"billing_type": "instance.basic", "device_type": "server", "device_sub_type": ""}
            for _ in range(2)
        ]

        mock_client._request.side_effect = [
            {"server_list": page1_servers, "meta": {"total_count": 502}},
            {"server_list": page2_servers, "meta": {"total_count": 502}},
            {"addon_list": [{"textkey": "instance.basic", "name": "Basic Node"}], "meta": {}},
        ]

        result = await handle_get_license_utilization({}, mock_client)

        text = result[0].text
        assert "Total Instances: 502" in text
        # Verify pagination calls
        assert mock_client._request.call_count == 3
        calls = mock_client._request.call_args_list
        assert calls[0] == call("GET", "server", params={"limit": 500, "offset": 0})
        assert calls[1] == call("GET", "server", params={"limit": 500, "offset": 500})

    @pytest.mark.asyncio
    async def test_utilization_api_error(self, mock_client, monkeypatch):
        """Test graceful handling of API errors."""
        from src.tools.license_utilization import handle_get_license_utilization

        monkeypatch.delenv("LICENSE_ENTITLEMENTS", raising=False)

        mock_client._request.side_effect = APIError("Connection failed")

        result = await handle_get_license_utilization({}, mock_client)

        assert "Error" in result[0].text

    @pytest.mark.asyncio
    async def test_utilization_invalid_entitlements_json(self, mock_client, monkeypatch):
        """Test graceful handling of invalid LICENSE_ENTITLEMENTS JSON."""
        from src.tools.license_utilization import handle_get_license_utilization

        monkeypatch.setenv("LICENSE_ENTITLEMENTS", "not-valid-json")

        mock_client._request.side_effect = [
            {
                "server_list": [
                    {"billing_type": "instance.basic", "device_type": "server", "device_sub_type": ""},
                ],
                "meta": {"total_count": 1},
            },
            {"addon_list": [], "meta": {}},
        ]

        result = await handle_get_license_utilization({}, mock_client)

        text = result[0].text
        # Should still produce a report (without entitlements)
        assert "Total Instances: 1" in text
        assert "Configure LICENSE_ENTITLEMENTS" in text

    @pytest.mark.asyncio
    async def test_utilization_subtype_breakdown(self, mock_client, monkeypatch):
        """Test device sub-type breakdown in report."""
        from src.tools.license_utilization import handle_get_license_utilization

        monkeypatch.delenv("LICENSE_ENTITLEMENTS", raising=False)

        mock_client._request.side_effect = [
            {
                "server_list": [
                    {"billing_type": "instance.advanced", "device_type": "network_device", "device_sub_type": "fortinet.fortigate"},
                    {"billing_type": "instance.advanced", "device_type": "network_device", "device_sub_type": "fortinet.fortigate"},
                    {"billing_type": "instance.advanced", "device_type": "cloud", "device_sub_type": "aws.ec2"},
                ],
                "meta": {"total_count": 3},
            },
            {"addon_list": [{"textkey": "instance.advanced", "name": "Advanced Node"}], "meta": {}},
        ]

        result = await handle_get_license_utilization({}, mock_client)

        text = result[0].text
        assert "network_device (fortinet.fortigate): 2" in text
        assert "cloud (aws.ec2): 1" in text


class TestListAddonCatalog:
    """Test list_addon_catalog handler."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_list_addons_success(self, mock_client):
        from src.tools.license_utilization import handle_list_addon_catalog

        mock_client._request.return_value = {
            "addon_list": [
                {"name": "Basic Node", "textkey": "instance.basic", "description": "Basic monitoring"},
                {"name": "Advanced Node", "textkey": "instance.advanced", "description": "Advanced monitoring"},
            ],
            "meta": {"total_count": 2},
        }

        result = await handle_list_addon_catalog({}, mock_client)

        assert len(result) == 1
        text = result[0].text
        assert "Addon Catalog" in text
        assert "Basic Node" in text
        assert "`instance.basic`" in text
        assert "Advanced Node" in text
        assert "`instance.advanced`" in text
        assert "LICENSE_ENTITLEMENTS" in text
        mock_client._request.assert_called_once_with(
            "GET", "addon", params={"limit": 100}
        )

    @pytest.mark.asyncio
    async def test_list_addons_empty(self, mock_client):
        from src.tools.license_utilization import handle_list_addon_catalog

        mock_client._request.return_value = {"addon_list": [], "meta": {}}

        result = await handle_list_addon_catalog({}, mock_client)
        assert "No addons found" in result[0].text

    @pytest.mark.asyncio
    async def test_list_addons_custom_limit(self, mock_client):
        from src.tools.license_utilization import handle_list_addon_catalog

        mock_client._request.return_value = {
            "addon_list": [{"name": "Basic", "textkey": "instance.basic"}],
            "meta": {"total_count": 1},
        }

        await handle_list_addon_catalog({"limit": 25}, mock_client)

        mock_client._request.assert_called_once_with(
            "GET", "addon", params={"limit": 25}
        )

    @pytest.mark.asyncio
    async def test_list_addons_api_error(self, mock_client):
        from src.tools.license_utilization import handle_list_addon_catalog

        mock_client._request.side_effect = APIError("Connection failed")

        result = await handle_list_addon_catalog({}, mock_client)
        assert "Error" in result[0].text


class TestToolDefinitions:
    """Test tool definitions are valid."""

    def test_get_license_utilization_definition(self):
        from src.tools.license_utilization import get_license_utilization_tool_definition

        tool = get_license_utilization_tool_definition()
        assert tool.name == "get_license_utilization"
        assert "utilization" in tool.description.lower()

    def test_list_addon_catalog_definition(self):
        from src.tools.license_utilization import list_addon_catalog_tool_definition

        tool = list_addon_catalog_tool_definition()
        assert tool.name == "list_addon_catalog"
        assert "addon" in tool.description.lower()
