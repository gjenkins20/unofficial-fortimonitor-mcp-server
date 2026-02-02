"""Pre-flight check script to validate server.py before running."""

import sys
from pathlib import Path


def check_imports():
    """Check that all required imports work."""
    print("Checking imports...")
    try:
        from mcp.types import ServerCapabilities, ToolsCapability
        from mcp.server.models import InitializationOptions
        from mcp.server import Server
        print("  All MCP imports available")
        return True
    except ImportError as e:
        print(f"  Missing import: {e}")
        print("\nRun: pip install --upgrade mcp")
        return False


def check_capabilities_construction():
    """Check that capabilities can be constructed."""
    print("\nChecking ServerCapabilities construction...")
    try:
        from mcp.types import ServerCapabilities, ToolsCapability

        capabilities = ServerCapabilities(
            tools=ToolsCapability(listChanged=False)
        )
        print("  ServerCapabilities can be created")
        return True
    except Exception as e:
        print(f"  Cannot create ServerCapabilities: {e}")
        return False


def check_initialization_options():
    """Check that InitializationOptions accepts capabilities."""
    print("\nChecking InitializationOptions...")
    try:
        from mcp.server.models import InitializationOptions
        from mcp.types import ServerCapabilities, ToolsCapability

        capabilities = ServerCapabilities(
            tools=ToolsCapability(listChanged=False)
        )

        init_options = InitializationOptions(
            server_name="test",
            server_version="0.1.0",
            capabilities=capabilities
        )
        print("  InitializationOptions accepts capabilities")
        return True
    except Exception as e:
        print(f"  InitializationOptions error: {e}")
        return False


def check_env_variables():
    """Check that required environment variables are set."""
    print("\nChecking environment variables...")
    import os

    # Try to load .env file if dotenv is available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("  python-dotenv not installed, trying to read .env manually...")
        try:
            env_file = Path(".env")
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
                print("  Loaded .env manually")
        except Exception as e:
            print(f"  Could not load .env: {e}")

    required = ['FORTIMONITOR_BASE_URL', 'FORTIMONITOR_API_KEY']
    missing = []

    for var in required:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            print(f"  Found {var}")

    if missing:
        print(f"  Missing environment variables: {', '.join(missing)}")
        print("\nCreate a .env file with:")
        for var in missing:
            print(f"  {var}=your_value_here")
        return False
    else:
        print("  All required environment variables set")
        return True


def check_server_file():
    """Check that server.py has the correct imports."""
    print("\nChecking server.py imports...")

    server_file = Path("src/server.py")
    if not server_file.exists():
        print("  src/server.py not found")
        return False

    content = server_file.read_text()

    required_imports = [
        "from mcp.types import",
        "ServerCapabilities",
        "ToolsCapability"
    ]

    missing = []
    for imp in required_imports:
        if imp not in content:
            missing.append(imp)

    if missing:
        print(f"  Missing imports in server.py: {', '.join(missing)}")
        print("\nAdd to imports:")
        print("  from mcp.types import TextContent, Tool, ServerCapabilities, ToolsCapability")
        return False
    else:
        print("  server.py has correct imports")
        return True


def main():
    """Run all checks."""
    print("=" * 60)
    print("FortiMonitor MCP Server Pre-Flight Check")
    print("=" * 60)

    checks = [
        check_imports,
        check_capabilities_construction,
        check_initialization_options,
        check_env_variables,
        check_server_file
    ]

    results = [check() for check in checks]

    print("\n" + "=" * 60)
    if all(results):
        print("ALL CHECKS PASSED - Server should start successfully!")
        print("\nRun: python -m src.server")
        return 0
    else:
        print("SOME CHECKS FAILED - Fix issues above before running server")
        return 1


if __name__ == "__main__":
    sys.exit(main())
