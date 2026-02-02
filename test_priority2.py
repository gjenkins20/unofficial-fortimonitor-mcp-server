"""Tests for Priority 2 bulk operations and advanced search."""

import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.fortimonitor.client import FortiMonitorClient
from src.tools.bulk_operations import (
    handle_bulk_acknowledge_outages,
    handle_bulk_add_tags,
    handle_bulk_remove_tags,
    handle_search_servers_advanced,
    handle_get_servers_with_active_outages,
)


async def test_advanced_search():
    """Test advanced search functionality."""
    client = FortiMonitorClient()

    print("\n" + "=" * 60)
    print("TEST 1: ADVANCED SERVER SEARCH")
    print("=" * 60)

    # Test 1a: Search by status
    print("\n1a. Searching for active servers...")
    result = await handle_search_servers_advanced(
        {"status": "active", "limit": 5},
        client
    )
    print("   Result:")
    print(result[0].text)

    # Test 1b: Search by name pattern
    print("\n1b. Searching servers with name containing 'web'...")
    result = await handle_search_servers_advanced(
        {"name_contains": "web", "limit": 5},
        client
    )
    print("   Result:")
    print(result[0].text)

    # Test 1c: Search with multiple criteria
    print("\n1c. Searching active servers with outages...")
    result = await handle_search_servers_advanced(
        {"status": "active", "has_active_outages": True, "limit": 5},
        client
    )
    print("   Result:")
    print(result[0].text)

    client.close()
    print("\n   [PASSED] Advanced search tests completed")


async def test_servers_with_outages():
    """Test getting servers with active outages."""
    client = FortiMonitorClient()

    print("\n" + "=" * 60)
    print("TEST 2: SERVERS WITH ACTIVE OUTAGES")
    print("=" * 60)

    # Test 2a: Get all servers with outages
    print("\n2a. Getting all servers with active outages...")
    result = await handle_get_servers_with_active_outages(
        {"limit": 20},
        client
    )
    print("   Result:")
    print(result[0].text)

    # Test 2b: Get servers with critical outages only
    print("\n2b. Getting servers with critical outages...")
    result = await handle_get_servers_with_active_outages(
        {"severity": "critical", "limit": 20},
        client
    )
    print("   Result:")
    print(result[0].text)

    client.close()
    print("\n   [PASSED] Servers with outages tests completed")


async def test_bulk_tagging():
    """Test bulk tag operations."""
    client = FortiMonitorClient()

    print("\n" + "=" * 60)
    print("TEST 3: BULK TAG OPERATIONS")
    print("=" * 60)

    # Get some test servers
    servers = client.get_servers(limit=3)
    server_ids = [s.id for s in servers.server_list if s.id]

    if not server_ids:
        print("   [SKIPPED] No servers available for testing")
        client.close()
        return

    print(f"\n   Testing with servers: {server_ids}")

    # Test 3a: Add tags
    print("\n3a. Bulk adding tags...")
    result = await handle_bulk_add_tags(
        {
            "server_ids": server_ids,
            "tags": ["test-priority2", "bulk-test"]
        },
        client
    )
    print("   Result:")
    print(result[0].text)

    # Test 3b: Remove tags
    print("\n3b. Bulk removing tags...")
    result = await handle_bulk_remove_tags(
        {
            "server_ids": server_ids,
            "tags": ["test-priority2", "bulk-test"]
        },
        client
    )
    print("   Result:")
    print(result[0].text)

    client.close()
    print("\n   [PASSED] Bulk tagging tests completed")


async def test_bulk_acknowledge():
    """Test bulk acknowledgment."""
    client = FortiMonitorClient()

    print("\n" + "=" * 60)
    print("TEST 4: BULK OUTAGE ACKNOWLEDGMENT")
    print("=" * 60)

    # Get active outages
    outages = client.get_active_outages(limit=3)
    outage_ids = [o.id for o in outages.outage_list if o.id]

    if not outage_ids:
        print("\n   [INFO] No active outages to test with")
        client.close()
        return

    print(f"\n   Testing with outages: {outage_ids}")

    # Test bulk acknowledge (be careful - this actually acknowledges!)
    print("\n4. Bulk acknowledging outages...")
    result = await handle_bulk_acknowledge_outages(
        {
            "outage_ids": outage_ids,
            "note": "Bulk acknowledgment test from Priority 2 test suite"
        },
        client
    )
    print("   Result:")
    print(result[0].text)

    client.close()
    print("\n   [PASSED] Bulk acknowledgment test completed")


async def test_validation():
    """Test input validation."""
    client = FortiMonitorClient()

    print("\n" + "=" * 60)
    print("TEST 5: INPUT VALIDATION")
    print("=" * 60)

    # Test 5a: Empty outage IDs
    print("\n5a. Testing empty outage IDs...")
    result = await handle_bulk_acknowledge_outages(
        {"outage_ids": []},
        client
    )
    assert "Error" in result[0].text or "No outage" in result[0].text
    print(f"   Result: {result[0].text}")

    # Test 5b: Empty server IDs
    print("\n5b. Testing empty server IDs...")
    result = await handle_bulk_add_tags(
        {"server_ids": [], "tags": ["test"]},
        client
    )
    assert "Error" in result[0].text or "No server" in result[0].text
    print(f"   Result: {result[0].text}")

    # Test 5c: Empty tags
    print("\n5c. Testing empty tags...")
    result = await handle_bulk_add_tags(
        {"server_ids": [1], "tags": []},
        client
    )
    assert "Error" in result[0].text or "No tags" in result[0].text
    print(f"   Result: {result[0].text}")

    # Test 5d: Too many items
    print("\n5d. Testing too many outage IDs...")
    result = await handle_bulk_acknowledge_outages(
        {"outage_ids": list(range(100))},
        client
    )
    assert "Error" in result[0].text or "Too many" in result[0].text
    print(f"   Result: {result[0].text}")

    client.close()
    print("\n   [PASSED] Validation tests completed")


async def run_all_tests():
    """Run all Priority 2 tests."""
    print("=" * 60)
    print("PRIORITY 2 COMPREHENSIVE TESTING")
    print("=" * 60)

    try:
        await test_advanced_search()
        await test_servers_with_outages()
        await test_bulk_tagging()
        # Uncomment to test bulk acknowledgment (this modifies data!)
        # await test_bulk_acknowledge()
        await test_validation()

        print("\n" + "=" * 60)
        print("[SUCCESS] ALL PRIORITY 2 TESTS COMPLETE")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
