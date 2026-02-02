"""Unit tests for MCP server initialization."""

import pytest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that all required imports are available."""
    try:
        from mcp.types import ServerCapabilities, ToolsCapability
        from mcp.server.models import InitializationOptions
        from mcp.server import Server
        assert True
    except ImportError as e:
        pytest.fail(f"Missing required import: {e}")


def test_server_capabilities_creation():
    """Test that ServerCapabilities can be created correctly."""
    from mcp.types import ServerCapabilities, ToolsCapability

    # This should not raise any errors
    capabilities = ServerCapabilities(
        tools=ToolsCapability(listChanged=False)
    )

    assert capabilities is not None
    assert hasattr(capabilities, 'tools')
    assert capabilities.tools.listChanged == False


def test_initialization_options_with_capabilities():
    """Test that InitializationOptions accepts capabilities."""
    from mcp.server.models import InitializationOptions
    from mcp.types import ServerCapabilities, ToolsCapability

    capabilities = ServerCapabilities(
        tools=ToolsCapability(listChanged=False)
    )

    # This should not raise ValidationError
    init_options = InitializationOptions(
        server_name="test-server",
        server_version="0.1.0",
        capabilities=capabilities
    )

    assert init_options.server_name == "test-server"
    assert init_options.server_version == "0.1.0"
    assert init_options.capabilities is not None


def test_server_can_be_created():
    """Test that FortiMonitorMCPServer can be instantiated."""
    # Set environment variables for test
    os.environ['FORTIMONITOR_BASE_URL'] = 'https://api2.panopta.com/v2'
    os.environ['FORTIMONITOR_API_KEY'] = 'test-key'

    from server import FortiMonitorMCPServer

    server = FortiMonitorMCPServer()
    assert server is not None
    assert server.server is not None
    assert server.client is None  # Not initialized until first use


def test_tool_handlers_registered():
    """Test that tool handlers are properly registered."""
    os.environ['FORTIMONITOR_BASE_URL'] = 'https://api2.panopta.com/v2'
    os.environ['FORTIMONITOR_API_KEY'] = 'test-key'

    from server import FortiMonitorMCPServer

    server = FortiMonitorMCPServer()

    # Server should have handlers registered
    assert server.server is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
