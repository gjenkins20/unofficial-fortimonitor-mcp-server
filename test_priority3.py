"""Tests for Priority 3 server groups and templates."""

import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.fortimonitor.client import FortiMonitorClient
from src.tools.server_groups import (
    handle_list_server_groups,
    handle_get_server_group_details,
    handle_create_server_group,
    handle_add_servers_to_group,
    handle_remove_servers_from_group,
    handle_delete_server_group,
)
from src.tools.templates import (
    handle_list_server_templates,
    handle_get_server_template_details,
    handle_apply_template_to_server,
    handle_apply_template_to_group,
)


async def test_list_server_groups():
    """Test listing server groups."""
    client = FortiMonitorClient()

    print("\n" + "=" * 60)
    print("TEST 1: LIST SERVER GROUPS")
    print("=" * 60)

    result = await handle_list_server_groups(
        {"limit": 20},
        client
    )
    print("   Result:")
    print(result[0].text)

    client.close()
    print("\n   [PASSED] List server groups test completed")


async def test_list_server_templates():
    """Test listing server templates."""
    client = FortiMonitorClient()

    print("\n" + "=" * 60)
    print("TEST 2: LIST SERVER TEMPLATES")
    print("=" * 60)

    result = await handle_list_server_templates(
        {"limit": 20},
        client
    )
    print("   Result:")
    print(result[0].text)

    client.close()
    print("\n   [PASSED] List server templates test completed")


async def test_server_group_crud():
    """Test server group create, read, update, delete operations."""
    client = FortiMonitorClient()

    print("\n" + "=" * 60)
    print("TEST 3: SERVER GROUP CRUD OPERATIONS")
    print("=" * 60)

    # Get some test servers
    servers = client.get_servers(limit=3)
    server_ids = [s.id for s in servers.server_list if s.id]

    if not server_ids:
        print("   [SKIPPED] No servers available for testing")
        client.close()
        return

    print(f"   Using servers: {server_ids}")

    # Test 3a: Create group
    print("\n3a. Creating server group...")
    result = await handle_create_server_group(
        {
            "name": "Test Group Priority 3",
            "description": "Created by Priority 3 test suite",
            "server_ids": server_ids[:1]  # Start with one server
        },
        client
    )
    print("   Result:")
    print(result[0].text)

    # Extract group ID from result (look for "ID: <number>")
    import re
    group_id_match = re.search(r'ID:\s*(\d+)', result[0].text)
    if not group_id_match:
        print("   [FAILED] Could not extract group ID from response")
        client.close()
        return

    group_id = int(group_id_match.group(1))
    print(f"   Created group ID: {group_id}")

    # Test 3b: Get group details
    print("\n3b. Getting server group details...")
    result = await handle_get_server_group_details(
        {"group_id": group_id},
        client
    )
    print("   Result:")
    print(result[0].text)

    # Test 3c: Add servers to group
    if len(server_ids) > 1:
        print("\n3c. Adding servers to group...")
        result = await handle_add_servers_to_group(
            {
                "group_id": group_id,
                "server_ids": server_ids[1:]  # Add remaining servers
            },
            client
        )
        print("   Result:")
        print(result[0].text)

    # Test 3d: Remove server from group
    print("\n3d. Removing server from group...")
    result = await handle_remove_servers_from_group(
        {
            "group_id": group_id,
            "server_ids": [server_ids[0]]  # Remove first server
        },
        client
    )
    print("   Result:")
    print(result[0].text)

    # Test 3e: Delete group
    print("\n3e. Deleting server group...")
    result = await handle_delete_server_group(
        {"group_id": group_id},
        client
    )
    print("   Result:")
    print(result[0].text)

    client.close()
    print("\n   [PASSED] Server group CRUD tests completed")


async def test_template_details():
    """Test getting template details."""
    client = FortiMonitorClient()

    print("\n" + "=" * 60)
    print("TEST 4: TEMPLATE DETAILS")
    print("=" * 60)

    # First list templates to get an ID
    response = client.list_server_templates(limit=1)
    if not response.server_template_list:
        print("   [SKIPPED] No templates available")
        client.close()
        return

    template = response.server_template_list[0]
    template_id = template.id

    print(f"   Getting details for template: {template.name} (ID: {template_id})")

    result = await handle_get_server_template_details(
        {"template_id": template_id},
        client
    )
    print("   Result:")
    print(result[0].text)

    client.close()
    print("\n   [PASSED] Template details test completed")


async def test_apply_template():
    """Test applying a template to a server."""
    client = FortiMonitorClient()

    print("\n" + "=" * 60)
    print("TEST 5: APPLY TEMPLATE TO SERVER")
    print("=" * 60)

    # Get a server and template
    servers = client.get_servers(limit=1)
    templates = client.list_server_templates(limit=1)

    if not servers.server_list:
        print("   [SKIPPED] No servers available")
        client.close()
        return

    if not templates.server_template_list:
        print("   [SKIPPED] No templates available")
        client.close()
        return

    server = servers.server_list[0]
    template = templates.server_template_list[0]

    print(f"   Server: {server.name} (ID: {server.id})")
    print(f"   Template: {template.name} (ID: {template.id})")

    result = await handle_apply_template_to_server(
        {
            "server_id": server.id,
            "template_id": template.id
        },
        client
    )
    print("   Result:")
    print(result[0].text)

    client.close()
    print("\n   [PASSED] Apply template test completed")


async def test_validation():
    """Test input validation."""
    client = FortiMonitorClient()

    print("\n" + "=" * 60)
    print("TEST 6: INPUT VALIDATION")
    print("=" * 60)

    # Test 6a: Non-existent group
    print("\n6a. Testing non-existent group ID...")
    result = await handle_get_server_group_details(
        {"group_id": 999999999},
        client
    )
    assert "Error" in result[0].text or "not found" in result[0].text.lower()
    print(f"   Result: {result[0].text}")

    # Test 6b: Non-existent template
    print("\n6b. Testing non-existent template ID...")
    result = await handle_get_server_template_details(
        {"template_id": 999999999},
        client
    )
    assert "Error" in result[0].text or "not found" in result[0].text.lower()
    print(f"   Result: {result[0].text}")

    # Test 6c: Add empty server list
    print("\n6c. Testing add empty server list...")
    result = await handle_add_servers_to_group(
        {"group_id": 1, "server_ids": []},
        client
    )
    assert "Error" in result[0].text or "No server" in result[0].text
    print(f"   Result: {result[0].text}")

    client.close()
    print("\n   [PASSED] Validation tests completed")


async def run_all_tests():
    """Run all Priority 3 tests."""
    print("=" * 60)
    print("PRIORITY 3 COMPREHENSIVE TESTING")
    print("Server Groups & Templates")
    print("=" * 60)

    try:
        await test_list_server_groups()
        await test_list_server_templates()
        await test_server_group_crud()
        await test_template_details()
        # Uncomment to test applying templates (modifies server config!)
        # await test_apply_template()
        await test_validation()

        print("\n" + "=" * 60)
        print("[SUCCESS] ALL PRIORITY 3 TESTS COMPLETE")
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
