"""Tests for FortiMonitor API client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestFortiMonitorClient:
    """Tests for FortiMonitorClient class."""

    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Set env vars needed by Settings."""
        monkeypatch.setenv("FORTIMONITOR_API_KEY", "test_api_key")
        monkeypatch.setenv("FORTIMONITOR_BASE_URL", "https://api2.panopta.com/v2")

    @pytest.fixture
    def client(self, mock_env, tmp_path):
        """Create a FortiMonitorClient with mocked settings."""
        from src.fortimonitor.client import FortiMonitorClient

        client = FortiMonitorClient(
            base_url="https://api2.panopta.com/v2",
            api_key="test_api_key",
            enable_schema_cache=False,
            schema_cache_dir=tmp_path,
        )
        return client

    def test_client_initialization(self, client):
        """Test client can be initialized."""
        assert client is not None
        assert client.base_url == "https://api2.panopta.com/v2"
        assert client.api_key == "test_api_key"
        assert client.schema is not None

    def test_client_base_url_strips_trailing_slash(self, mock_env, tmp_path):
        """Test that trailing slash is stripped from base URL."""
        from src.fortimonitor.client import FortiMonitorClient

        client = FortiMonitorClient(
            base_url="https://api2.panopta.com/v2/",
            api_key="test_api_key",
            enable_schema_cache=False,
            schema_cache_dir=tmp_path,
        )
        assert client.base_url == "https://api2.panopta.com/v2"

    @patch("requests.Session.request")
    def test_get_servers_returns_response(self, mock_request, client):
        """Test getting server list returns structured response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"server_list": [], "meta": {}}'
        mock_response.json.return_value = {
            "server_list": [
                {"url": "https://api2.panopta.com/v2/server/1", "name": "test-server-1"},
                {"url": "https://api2.panopta.com/v2/server/2", "name": "test-server-2"},
            ],
            "meta": {
                "limit": 50,
                "offset": 0,
                "total_count": 2,
            },
        }
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        response = client.get_servers(limit=50)

        assert hasattr(response, "server_list")
        assert isinstance(response.server_list, list)
        assert len(response.server_list) == 2
        assert response.server_list[0].name == "test-server-1"
        assert response.server_list[0].id == 1

    @patch("requests.Session.request")
    def test_get_server_details(self, mock_request, client):
        """Test getting server details."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"url": "...", "name": "..."}'
        mock_response.json.return_value = {
            "url": "https://api2.panopta.com/v2/server/123",
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

    # ------------------------------------------------------------------
    # update_server: must resend the API's required fields (name, fqdn,
    # server_group) on every PUT, since PUT /server/{id} is a full-object
    # update. Regression coverage for FMN-294.
    # ------------------------------------------------------------------

    @staticmethod
    def _server_get_response(server_group="https://api2.panopta.com/v2/server_group/920634"):
        """Mock GET /server/{id} response used by update_server's read step."""
        resp = Mock()
        resp.status_code = 200
        resp.text = "{}"  # non-empty so _request parses JSON
        resp.json.return_value = {
            "url": "https://api2.panopta.com/v2/server/123",
            "name": "old-name",
            "fqdn": "web01.example.com",
            "server_group": server_group,
            "status": "active",
        }
        resp.raise_for_status = Mock()
        return resp

    @staticmethod
    def _put_204_response():
        """Mock empty 204 response for the PUT step."""
        resp = Mock()
        resp.status_code = 204
        resp.text = ""
        resp.raise_for_status = Mock()
        return resp

    @patch("requests.Session.request")
    def test_update_server_sends_required_fields(self, mock_request, client):
        """A name change must include name, fqdn and server_group in the PUT body."""
        mock_request.side_effect = [self._server_get_response(), self._put_204_response()]

        client.update_server(123, name="new-name")

        assert mock_request.call_count == 2
        get_call, put_call = mock_request.call_args_list
        assert get_call.kwargs["method"] == "GET"
        assert put_call.kwargs["method"] == "PUT"
        assert put_call.kwargs["url"].endswith("/server/123")
        assert put_call.kwargs["json"] == {
            "name": "new-name",
            "fqdn": "web01.example.com",
            "server_group": "https://api2.panopta.com/v2/server_group/920634",
        }

    @patch("requests.Session.request")
    def test_update_server_name_only_preserves_fqdn_and_group(self, mock_request, client):
        """Caller supplies only name; fqdn/server_group are pulled from current state."""
        mock_request.side_effect = [self._server_get_response(), self._put_204_response()]

        client.update_server(123, name="renamed")

        body = mock_request.call_args_list[1].kwargs["json"]
        assert body["fqdn"] == "web01.example.com"
        assert body["server_group"] == "https://api2.panopta.com/v2/server_group/920634"

    @patch("requests.Session.request")
    def test_update_server_defaults_name_when_only_description(self, mock_request, client):
        """Updating only the description still sends the current name (required field)."""
        mock_request.side_effect = [self._server_get_response(), self._put_204_response()]

        client.update_server(123, description="new description")

        body = mock_request.call_args_list[1].kwargs["json"]
        assert body["name"] == "old-name"
        assert body["description"] == "new description"
        assert body["fqdn"] == "web01.example.com"
        assert body["server_group"] == "https://api2.panopta.com/v2/server_group/920634"

    @patch("requests.Session.request")
    def test_update_server_missing_server_group_raises(self, mock_request, client):
        """If the current server has no server_group, fail with a clear error and no PUT."""
        mock_request.side_effect = [self._server_get_response(server_group=None)]

        with pytest.raises(ValueError, match="fqdn/server_group"):
            client.update_server(123, name="new-name")

        # Only the GET happened; no PUT was attempted.
        assert mock_request.call_count == 1
        assert mock_request.call_args_list[0].kwargs["method"] == "GET"

    @patch("requests.Session.request")
    def test_update_server_invalid_status_raises(self, mock_request, client):
        """Invalid status fails fast, before any network call."""
        with pytest.raises(ValueError, match="Status must be one of"):
            client.update_server(123, status="bogus")

        mock_request.assert_not_called()

    @patch("requests.Session.request")
    def test_update_server_requires_at_least_one_field(self, mock_request, client):
        """No fields provided is an error and makes no network call."""
        with pytest.raises(ValueError, match="At least one field"):
            client.update_server(123)

        mock_request.assert_not_called()

    @patch("requests.Session.request")
    def test_get_outages(self, mock_request, client):
        """Test getting outages."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"outage_list": [], "meta": {}}'
        mock_response.json.return_value = {
            "outage_list": [
                {
                    "url": "https://api2.panopta.com/v2/outage/1",
                    "severity": "critical",
                    "status": "active",
                    "start_time": "2026-01-30T10:00:00Z",
                }
            ],
            "meta": {
                "limit": 50,
                "offset": 0,
                "total_count": 1,
            },
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
        mock_response.text = "Unauthorized"
        mock_request.return_value = mock_response

        with pytest.raises(AuthenticationError):
            client.get_servers()

    @patch("requests.Session.request")
    def test_not_found_error(self, mock_request, client):
        """Test not found error handling."""
        from src.fortimonitor.exceptions import NotFoundError

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_request.return_value = mock_response

        with pytest.raises(NotFoundError):
            client.get_server_details(99999)

    @patch("requests.Session.request")
    def test_rate_limit_error(self, mock_request, client):
        """Test rate limit error handling."""
        from src.fortimonitor.exceptions import RateLimitError

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Too many requests"
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
