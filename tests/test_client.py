"""Tests for FortiMonitor API client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestFortiMonitorClient:
    """Tests for FortiMonitorClient class."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        mock = MagicMock()
        mock.api_base_url = "https://api2.panopta.com/v2"
        mock.fortimonitor_api_key = "test_api_key"
        mock.schema_cache_dir = MagicMock()
        mock.schema_cache_dir.mkdir = MagicMock()
        return mock

    @pytest.fixture
    def client(self, mock_settings):
        """Create a FortiMonitorClient with mocked settings."""
        with patch("src.fortimonitor.client.settings") as mock_settings_func:
            mock_settings_func.return_value = mock_settings
            from src.fortimonitor.client import FortiMonitorClient

            client = FortiMonitorClient(
                base_url="https://api2.panopta.com/v2",
                api_key="test_api_key",
                enable_schema_cache=False,
            )
            return client

    def test_client_initialization(self, client):
        """Test client can be initialized."""
        assert client is not None
        assert client.base_url == "https://api2.panopta.com/v2"
        assert client.api_key == "test_api_key"
        assert client.schema is not None

    def test_client_base_url_strips_trailing_slash(self, mock_settings):
        """Test that trailing slash is stripped from base URL."""
        with patch("src.fortimonitor.client.settings") as mock_settings_func:
            mock_settings_func.return_value = mock_settings
            from src.fortimonitor.client import FortiMonitorClient

            client = FortiMonitorClient(
                base_url="https://api2.panopta.com/v2/",
                api_key="test_api_key",
                enable_schema_cache=False,
            )
            assert client.base_url == "https://api2.panopta.com/v2"

    @patch("requests.Session.request")
    def test_get_servers_returns_response(self, mock_request, client):
        """Test getting server list returns structured response."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "server_list": [
                {"id": 1, "name": "test-server-1"},
                {"id": 2, "name": "test-server-2"},
            ],
            "limit": 50,
            "offset": 0,
            "total_count": 2,
        }
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        response = client.get_servers(limit=50)

        assert hasattr(response, "server_list")
        assert hasattr(response, "limit")
        assert hasattr(response, "offset")
        assert isinstance(response.server_list, list)
        assert len(response.server_list) == 2
        assert response.server_list[0].name == "test-server-1"

    @patch("requests.Session.request")
    def test_get_server_details(self, mock_request, client):
        """Test getting server details."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 123,
            "name": "production-web-01",
            "fqdn": "web01.example.com",
            "status": "active",
        }
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        server = client.get_server_details(123)

        assert server.id == 123
        assert server.name == "production-web-01"
        assert server.fqdn == "web01.example.com"

    @patch("requests.Session.request")
    def test_get_outages(self, mock_request, client):
        """Test getting outages."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "outage_list": [
                {
                    "id": 1,
                    "severity": "critical",
                    "status": "active",
                    "start_time": "2026-01-30T10:00:00Z",
                }
            ],
            "limit": 50,
            "offset": 0,
            "total_count": 1,
        }
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        response = client.get_outages(limit=50)

        assert hasattr(response, "outage_list")
        assert len(response.outage_list) == 1
        assert response.outage_list[0].severity == "critical"

    @patch("requests.Session.request")
    def test_authentication_error(self, mock_request, client):
        """Test authentication error handling."""
        from src.fortimonitor.exceptions import AuthenticationError

        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response

        with pytest.raises(AuthenticationError):
            client.get_servers()

    @patch("requests.Session.request")
    def test_not_found_error(self, mock_request, client):
        """Test not found error handling."""
        from src.fortimonitor.exceptions import NotFoundError

        mock_response = Mock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        with pytest.raises(NotFoundError):
            client.get_server_details(99999)

    @patch("requests.Session.request")
    def test_rate_limit_error(self, mock_request, client):
        """Test rate limit error handling."""
        from src.fortimonitor.exceptions import RateLimitError

        mock_response = Mock()
        mock_response.status_code = 429
        mock_request.return_value = mock_response

        with pytest.raises(RateLimitError):
            client.get_servers()


class TestSchemaManager:
    """Tests for SchemaManager class."""

    @pytest.fixture
    def schema_manager(self, tmp_path):
        """Create a SchemaManager with temp cache directory."""
        from src.fortimonitor.schema import SchemaManager

        return SchemaManager(
            api_key="test_key",
            base_url="https://api2.panopta.com/v2",
            cache_dir=tmp_path,
            enable_cache=True,
        )

    @patch("requests.get")
    def test_get_resource_list(self, mock_get, schema_manager):
        """Test fetching resource list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "apiVersion": "2.0",
            "apis": [
                {"path": "/schema/resources/server", "description": "Server resource"},
                {"path": "/schema/resources/outage", "description": "Outage resource"},
            ],
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        resources = schema_manager.get_resource_list()

        assert "server" in resources
        assert "outage" in resources

    @patch("requests.get")
    def test_get_resource_schema(self, mock_get, schema_manager):
        """Test fetching resource schema."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resourcePath": "/server",
            "apis": [
                {
                    "path": "/server",
                    "operations": [
                        {
                            "method": "GET",
                            "parameters": [
                                {"name": "limit", "type": "integer", "required": False}
                            ],
                        }
                    ],
                }
            ],
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        schema = schema_manager.get_resource_schema("server")

        assert "apis" in schema
        assert schema["resourcePath"] == "/server"

    def test_cache_validation(self, schema_manager, tmp_path):
        """Test cache validation logic."""
        import json
        from datetime import datetime

        # Create a valid cache file
        cache_file = tmp_path / "resource_list.json"
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "resources": ["server", "outage"],
        }
        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        # Cache should be valid (just created)
        assert schema_manager._is_cache_valid(cache_file) is True

        # Non-existent file should be invalid
        assert schema_manager._is_cache_valid(tmp_path / "nonexistent.json") is False
