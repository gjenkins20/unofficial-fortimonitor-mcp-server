"""Tests for SNMP resource tools — safe PUT payloads, tag operations, and bulk tagging."""

import pytest
from unittest.mock import MagicMock, call
from mcp.types import TextContent

from src.tools.snmp import (
    handle_update_snmp_resource,
    handle_create_snmp_resource,
    handle_get_snmp_resource_details,
    handle_list_server_snmp_resources,
    handle_bulk_tag_snmp_resources,
    _normalize_tags,
    _build_safe_snmp_resource_put_payload,
    _SNMP_RESOURCE_READONLY_FIELDS,
)


# ============================================================================
# _normalize_tags helper
# ============================================================================


class TestNormalizeTags:
    def test_none_returns_empty_list(self):
        assert _normalize_tags(None) == []

    def test_empty_list(self):
        assert _normalize_tags([]) == []

    def test_list_of_strings(self):
        assert _normalize_tags(["web", "prod"]) == ["web", "prod"]

    def test_comma_separated_string(self):
        assert _normalize_tags("web,prod,staging") == ["web", "prod", "staging"]

    def test_comma_separated_with_spaces(self):
        assert _normalize_tags("web , prod , staging") == ["web", "prod", "staging"]

    def test_single_string(self):
        assert _normalize_tags("web") == ["web"]

    def test_empty_string(self):
        assert _normalize_tags("") == []

    def test_list_with_empty_strings_filtered(self):
        assert _normalize_tags(["web", "", "  ", "prod"]) == ["web", "prod"]

    def test_comma_separated_with_empties(self):
        assert _normalize_tags("web,,prod,") == ["web", "prod"]


# ============================================================================
# _build_safe_snmp_resource_put_payload
# ============================================================================


class TestBuildSafePutPayload:
    def _make_current(self, **overrides):
        """Return a typical GET response for an SNMP resource."""
        base = {
            "name": "CPU Usage",
            "frequency": 60,
            "type": "gauge",
            "base_oid": "1.3.6.1.2.1.25.3.3.1.2",
            "version": "2c",
            "community": "public",
            "port": 161,
            "tags": ["existing"],
            # Read-only fields that must NOT appear in payload
            "formatted_name": "CPU Usage (formatted)",
            "template": "https://api2.panopta.com/v2/server_template/123",
            "template_snmp_resource": "https://api2.panopta.com/v2/...",
            "id": 999,
            "url": "https://api2.panopta.com/v2/server/1/snmp_resource/999",
            "status": "active",
            "server_url": "https://api2.panopta.com/v2/server/1",
            "thresholds": [{"warning": 80}],
        }
        base.update(overrides)
        return base

    def test_required_fields_always_present(self):
        current = self._make_current()
        payload = _build_safe_snmp_resource_put_payload(current, {}, ["tag1"])
        assert "name" in payload
        assert "frequency" in payload
        assert "type" in payload
        assert "base_oid" in payload
        assert "version" in payload
        assert "community" in payload

    def test_readonly_fields_excluded(self):
        current = self._make_current()
        payload = _build_safe_snmp_resource_put_payload(current, {}, ["tag1"])
        for field in _SNMP_RESOURCE_READONLY_FIELDS:
            assert field not in payload, f"Read-only field '{field}' found in payload"

    def test_version_defaults_to_2c_when_null(self):
        current = self._make_current(version=None)
        payload = _build_safe_snmp_resource_put_payload(current, {})
        assert payload["version"] == "2c"

    def test_community_defaults_to_public_when_null(self):
        current = self._make_current(community=None)
        payload = _build_safe_snmp_resource_put_payload(current, {})
        assert payload["community"] == "public"

    def test_overrides_take_precedence(self):
        current = self._make_current()
        overrides = {"name": "New Name", "base_oid": "1.2.3.4"}
        payload = _build_safe_snmp_resource_put_payload(current, overrides)
        assert payload["name"] == "New Name"
        assert payload["base_oid"] == "1.2.3.4"

    def test_tags_included_in_payload(self):
        current = self._make_current()
        payload = _build_safe_snmp_resource_put_payload(current, {}, ["web", "prod"])
        assert payload["tags"] == ["web", "prod"]

    def test_optional_writable_fields_included_when_non_null(self):
        current = self._make_current(
            server_interface="eth0",
            user="snmpuser",
            auth_algorithm="SHA",
            auth_key="secret",
            enc_algorithm="AES",
            enc_key="encsecret",
        )
        payload = _build_safe_snmp_resource_put_payload(current, {})
        assert payload["port"] == 161
        assert payload["server_interface"] == "eth0"
        assert payload["user"] == "snmpuser"
        assert payload["auth_algorithm"] == "SHA"

    def test_optional_fields_omitted_when_null(self):
        current = self._make_current(port=None, server_interface=None)
        payload = _build_safe_snmp_resource_put_payload(current, {})
        assert "port" not in payload
        assert "server_interface" not in payload

    def test_tags_none_means_no_tags_key(self):
        current = self._make_current()
        payload = _build_safe_snmp_resource_put_payload(current, {}, None)
        assert "tags" not in payload


# ============================================================================
# handle_update_snmp_resource
# ============================================================================


class TestUpdateSnmpResource:
    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock()
        return client

    def _get_response(self, **overrides):
        base = {
            "name": "CPU Usage",
            "frequency": 60,
            "type": "gauge",
            "base_oid": "1.3.6.1.2.1.25.3.3.1.2",
            "version": "2c",
            "community": "public",
            "tags": ["existing-tag"],
            "url": "https://api2.panopta.com/v2/server/1/snmp_resource/100",
        }
        base.update(overrides)
        return base

    @pytest.mark.asyncio
    async def test_preflight_get_then_put(self, mock_client):
        """Verify the handler does a GET then PUT."""
        mock_client._request.side_effect = [
            self._get_response(),  # GET
            {"success": True},     # PUT
        ]

        result = await handle_update_snmp_resource(
            {"server_id": 1, "resource_id": 100, "tags": ["new-tag"]},
            mock_client
        )

        assert mock_client._request.call_count == 2
        get_call = mock_client._request.call_args_list[0]
        put_call = mock_client._request.call_args_list[1]
        assert get_call[0][0] == "GET"
        assert put_call[0][0] == "PUT"

    @pytest.mark.asyncio
    async def test_tag_merge_no_duplicates(self, mock_client):
        """Tags are merged with existing tags, no duplicates."""
        mock_client._request.side_effect = [
            self._get_response(tags=["web", "prod"]),
            {"success": True},
        ]

        await handle_update_snmp_resource(
            {"server_id": 1, "resource_id": 100, "tags": ["prod", "staging"]},
            mock_client
        )

        put_call = mock_client._request.call_args_list[1]
        put_data = put_call[1]["json_data"]
        assert put_data["tags"] == ["web", "prod", "staging"]

    @pytest.mark.asyncio
    async def test_tag_merge_with_comma_separated_existing(self, mock_client):
        """Handle comma-separated tag string from API."""
        mock_client._request.side_effect = [
            self._get_response(tags="web,prod"),
            {"success": True},
        ]

        await handle_update_snmp_resource(
            {"server_id": 1, "resource_id": 100, "tags": ["staging"]},
            mock_client
        )

        put_call = mock_client._request.call_args_list[1]
        put_data = put_call[1]["json_data"]
        assert put_data["tags"] == ["web", "prod", "staging"]

    @pytest.mark.asyncio
    async def test_readonly_fields_not_in_put(self, mock_client):
        """Read-only fields from GET are not echoed back in PUT."""
        get_resp = self._get_response()
        get_resp["formatted_name"] = "CPU Usage (formatted)"
        get_resp["template"] = "https://api2.panopta.com/v2/server_template/123"
        get_resp["status"] = "active"
        get_resp["thresholds"] = [{"warning": 80}]

        mock_client._request.side_effect = [get_resp, {"success": True}]

        await handle_update_snmp_resource(
            {"server_id": 1, "resource_id": 100, "name": "New Name"},
            mock_client
        )

        put_data = mock_client._request.call_args_list[1][1]["json_data"]
        for field in _SNMP_RESOURCE_READONLY_FIELDS:
            assert field not in put_data

    @pytest.mark.asyncio
    async def test_defaults_version_community_when_null(self, mock_client):
        """version defaults to '2c' and community to 'public' when GET returns null."""
        mock_client._request.side_effect = [
            self._get_response(version=None, community=None),
            {"success": True},
        ]

        await handle_update_snmp_resource(
            {"server_id": 1, "resource_id": 100, "name": "New"},
            mock_client
        )

        put_data = mock_client._request.call_args_list[1][1]["json_data"]
        assert put_data["version"] == "2c"
        assert put_data["community"] == "public"

    @pytest.mark.asyncio
    async def test_oid_maps_to_base_oid(self, mock_client):
        """User-provided 'oid' param maps to 'base_oid' in PUT payload."""
        mock_client._request.side_effect = [
            self._get_response(),
            {"success": True},
        ]

        await handle_update_snmp_resource(
            {"server_id": 1, "resource_id": 100, "oid": "1.2.3.4.5"},
            mock_client
        )

        put_data = mock_client._request.call_args_list[1][1]["json_data"]
        assert put_data["base_oid"] == "1.2.3.4.5"

    @pytest.mark.asyncio
    async def test_tags_only_update_works(self, mock_client):
        """A tags-only update should work (no 'at least one field' error)."""
        mock_client._request.side_effect = [
            self._get_response(),
            {"success": True},
        ]

        result = await handle_update_snmp_resource(
            {"server_id": 1, "resource_id": 100, "tags": ["new-tag"]},
            mock_client
        )

        assert len(result) == 1
        assert "Updated" in result[0].text

    @pytest.mark.asyncio
    async def test_output_shows_tags(self, mock_client):
        mock_client._request.side_effect = [
            self._get_response(tags=[]),
            {"success": True},
        ]

        result = await handle_update_snmp_resource(
            {"server_id": 1, "resource_id": 100, "tags": ["web"]},
            mock_client
        )

        assert "Tags: web" in result[0].text


# ============================================================================
# handle_bulk_tag_snmp_resources
# ============================================================================


class TestBulkTagSnmpResources:
    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock()
        return client

    def _get_response(self, resource_id, tags=None):
        return {
            "name": f"Resource {resource_id}",
            "frequency": 60,
            "type": "gauge",
            "base_oid": f"1.3.6.1.{resource_id}",
            "version": "2c",
            "community": "public",
            "tags": tags or [],
            "url": f"https://api2.panopta.com/v2/server/1/snmp_resource/{resource_id}",
        }

    @pytest.mark.asyncio
    async def test_happy_path(self, mock_client):
        """Tags applied to multiple resources successfully."""
        mock_client._request.side_effect = [
            self._get_response(10),   # GET resource 10
            {"success": True},         # PUT resource 10
            self._get_response(20),   # GET resource 20
            {"success": True},         # PUT resource 20
        ]

        result = await handle_bulk_tag_snmp_resources(
            {"server_id": 1, "resource_ids": [10, 20], "tags": ["web"]},
            mock_client
        )

        assert "Succeeded: 2" in result[0].text
        assert "Skipped" in result[0].text

    @pytest.mark.asyncio
    async def test_idempotent_skip(self, mock_client):
        """Resources that already have all tags are skipped."""
        mock_client._request.side_effect = [
            self._get_response(10, tags=["web", "prod"]),  # Already has both
        ]

        result = await handle_bulk_tag_snmp_resources(
            {"server_id": 1, "resource_ids": [10], "tags": ["web", "prod"]},
            mock_client
        )

        assert "Skipped (already tagged): 1" in result[0].text
        assert "Succeeded: 0" in result[0].text
        # Only 1 call (GET), no PUT since skipped
        assert mock_client._request.call_count == 1

    @pytest.mark.asyncio
    async def test_partial_failure(self, mock_client):
        """One resource fails, others succeed."""
        from src.fortimonitor.exceptions import APIError

        mock_client._request.side_effect = [
            self._get_response(10),    # GET resource 10
            {"success": True},          # PUT resource 10
            APIError("Not found"),      # GET resource 20 fails
        ]

        result = await handle_bulk_tag_snmp_resources(
            {"server_id": 1, "resource_ids": [10, 20], "tags": ["web"]},
            mock_client
        )

        assert "Succeeded: 1" in result[0].text
        assert "Failed: 1" in result[0].text

    @pytest.mark.asyncio
    async def test_over_100_limit(self, mock_client):
        """Rejects more than 100 resources."""
        result = await handle_bulk_tag_snmp_resources(
            {"server_id": 1, "resource_ids": list(range(101)), "tags": ["web"]},
            mock_client
        )

        assert "Maximum 100" in result[0].text

    @pytest.mark.asyncio
    async def test_empty_tags_rejected(self, mock_client):
        result = await handle_bulk_tag_snmp_resources(
            {"server_id": 1, "resource_ids": [10], "tags": []},
            mock_client
        )

        assert "At least one tag" in result[0].text

    @pytest.mark.asyncio
    async def test_tag_merge_preserves_existing(self, mock_client):
        """Existing tags are preserved during merge."""
        mock_client._request.side_effect = [
            self._get_response(10, tags=["existing"]),
            {"success": True},
        ]

        await handle_bulk_tag_snmp_resources(
            {"server_id": 1, "resource_ids": [10], "tags": ["new"]},
            mock_client
        )

        put_call = mock_client._request.call_args_list[1]
        put_data = put_call[1]["json_data"]
        assert "existing" in put_data["tags"]
        assert "new" in put_data["tags"]


# ============================================================================
# handle_create_snmp_resource with tags
# ============================================================================


class TestCreateSnmpResource:
    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_create_with_tags(self, mock_client):
        mock_client._request.return_value = {
            "url": "https://api2.panopta.com/v2/server/1/snmp_resource/200"
        }

        result = await handle_create_snmp_resource(
            {
                "server_id": 1,
                "name": "Disk Usage",
                "oid": "1.3.6.1.2.1.25.2",
                "tags": ["storage", "critical"],
            },
            mock_client
        )

        call_args = mock_client._request.call_args
        data = call_args[1]["json_data"]
        assert data["tags"] == ["storage", "critical"]
        assert "Tags: storage, critical" in result[0].text

    @pytest.mark.asyncio
    async def test_create_with_additional_fields(self, mock_client):
        mock_client._request.return_value = {
            "url": "https://api2.panopta.com/v2/server/1/snmp_resource/201"
        }

        result = await handle_create_snmp_resource(
            {
                "server_id": 1,
                "name": "Bandwidth",
                "oid": "1.3.6.1.2.1.2.2.1.10",
                "frequency": 30,
                "type": "counter",
                "version": "3",
                "community": "private",
            },
            mock_client
        )

        data = mock_client._request.call_args[1]["json_data"]
        assert data["frequency"] == 30
        assert data["type"] == "counter"
        assert data["version"] == "3"
        assert data["community"] == "private"

    @pytest.mark.asyncio
    async def test_create_without_optional_fields(self, mock_client):
        """Optional fields not provided should not appear in POST body."""
        mock_client._request.return_value = {"success": True}

        await handle_create_snmp_resource(
            {"server_id": 1, "name": "Test"},
            mock_client
        )

        data = mock_client._request.call_args[1]["json_data"]
        assert "tags" not in data
        assert "frequency" not in data
        assert "type" not in data


# ============================================================================
# handle_get_snmp_resource_details — field writability annotations
# ============================================================================


class TestGetSnmpResourceDetails:
    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_writability_annotations(self, mock_client):
        mock_client._request.return_value = {
            "name": "CPU Usage",
            "oid": "1.3.6.1.2.1.25.3.3.1.2",
            "tags": ["web", "prod"],
            "status": "active",
        }

        result = await handle_get_snmp_resource_details(
            {"server_id": 1, "resource_id": 100},
            mock_client
        )

        text = result[0].text
        assert "Writable Fields:" in text
        assert "Read-Only Fields:" in text
        assert "formatted_name" in text  # listed as read-only

    @pytest.mark.asyncio
    async def test_tags_normalized_from_list(self, mock_client):
        mock_client._request.return_value = {
            "name": "Test",
            "tags": ["web", "prod"],
        }

        result = await handle_get_snmp_resource_details(
            {"server_id": 1, "resource_id": 100},
            mock_client
        )

        assert "Tags: web, prod" in result[0].text

    @pytest.mark.asyncio
    async def test_tags_normalized_from_string(self, mock_client):
        mock_client._request.return_value = {
            "name": "Test",
            "tags": "web,prod",
        }

        result = await handle_get_snmp_resource_details(
            {"server_id": 1, "resource_id": 100},
            mock_client
        )

        assert "Tags: web, prod" in result[0].text

    @pytest.mark.asyncio
    async def test_empty_tags_shows_none(self, mock_client):
        mock_client._request.return_value = {
            "name": "Test",
            "tags": [],
        }

        result = await handle_get_snmp_resource_details(
            {"server_id": 1, "resource_id": 100},
            mock_client
        )

        assert "Tags: (none)" in result[0].text


# ============================================================================
# handle_list_server_snmp_resources — tag display
# ============================================================================


class TestListServerSnmpResources:
    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._request = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_displays_tags(self, mock_client):
        mock_client._request.return_value = {
            "snmp_resource_list": [
                {
                    "name": "CPU",
                    "url": "https://api2.panopta.com/v2/server/1/snmp_resource/10",
                    "tags": ["web", "critical"],
                }
            ],
            "meta": {"total_count": 1},
        }

        result = await handle_list_server_snmp_resources(
            {"server_id": 1},
            mock_client
        )

        assert "Tags: web, critical" in result[0].text

    @pytest.mark.asyncio
    async def test_no_tags_field_omitted(self, mock_client):
        """Resources without tags should not show a Tags line."""
        mock_client._request.return_value = {
            "snmp_resource_list": [
                {
                    "name": "CPU",
                    "url": "https://api2.panopta.com/v2/server/1/snmp_resource/10",
                }
            ],
            "meta": {"total_count": 1},
        }

        result = await handle_list_server_snmp_resources(
            {"server_id": 1},
            mock_client
        )

        assert "Tags:" not in result[0].text

    @pytest.mark.asyncio
    async def test_comma_separated_tags_normalized(self, mock_client):
        mock_client._request.return_value = {
            "snmp_resource_list": [
                {
                    "name": "Disk",
                    "url": "https://api2.panopta.com/v2/server/1/snmp_resource/20",
                    "tags": "storage,critical",
                }
            ],
            "meta": {"total_count": 1},
        }

        result = await handle_list_server_snmp_resources(
            {"server_id": 1},
            mock_client
        )

        assert "Tags: storage, critical" in result[0].text
