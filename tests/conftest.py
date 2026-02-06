"""Shared fixtures for FortiMonitor MCP server tests."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_client():
    """Create a mock FortiMonitorClient for handler tests.

    The mock client's _request method is a MagicMock by default.
    Tests should configure return values per-call, e.g.:
        mock_client._request.return_value = {"user_list": [...], "meta": {...}}
    """
    client = MagicMock()
    # Ensure _request is available (dict-based handlers call this directly)
    client._request = MagicMock()
    return client
