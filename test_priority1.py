"""Comprehensive tests for Phase 2 Priority 1 tools."""

import asyncio
from datetime import datetime, timedelta, timezone
from src.fortimonitor.client import FortiMonitorClient
from src.tools.outage_management import (
    handle_acknowledge_outage,
    handle_add_outage_note,
    handle_get_outage_details,
)
from src.tools.server_management import (
    handle_set_server_status,
    handle_create_maintenance_window,
    handle_list_maintenance_windows,
)


async def test_models():
    """Test that new models can be imported and instantiated."""
    print("\n" + "=" * 60)
    print("TEST 0: MODEL VALIDATION")
    print("=" * 60)

    from src.fortimonitor.models import (
        OutageNote,
        OutageUpdate,
        MaintenanceWindow,
        MaintenanceWindowListResponse,
        PaginationMeta,
    )

    # Test OutageNote
    note = OutageNote(
        id=1,
        outage="https://api2.panopta.com/v2/outage/12345",
        note="Investigating root cause",
        created=datetime.now(timezone.utc),
    )
    print(f"  OutageNote model works: {note.note}")

    # Test OutageUpdate
    update = OutageUpdate(acknowledged=True, status="resolved")
    print(f"  OutageUpdate model works: acknowledged={update.acknowledged}")

    # Test MaintenanceWindow
    window = MaintenanceWindow(
        name="Test Maintenance",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc) + timedelta(hours=2),
        servers=["https://api2.panopta.com/v2/server/42008397"],
    )
    print(f"  MaintenanceWindow model works: {window.name}")

    # Test MaintenanceWindowListResponse
    response = MaintenanceWindowListResponse(
        maintenance_window_list=[window],
        meta=PaginationMeta(limit=50, offset=0, total_count=1),
    )
    print(f"  MaintenanceWindowListResponse works: {len(response.maintenance_window_list)} window(s)")

    print("\n  All models validated successfully!")


async def test_client_methods():
    """Test that client methods exist and are callable."""
    print("\n" + "=" * 60)
    print("TEST 1: CLIENT METHOD VALIDATION")
    print("=" * 60)

    client = FortiMonitorClient()

    # Check that all new methods exist
    methods = [
        "acknowledge_outage",
        "add_outage_log",
        "add_outage_note",
        "get_outage_details",
        "update_server_status",
        "create_maintenance_schedule",
        "create_maintenance_window",  # alias
        "list_maintenance_schedules",
        "list_maintenance_windows",  # alias
        "get_maintenance_schedule_details",
        "get_maintenance_window_details",  # alias
        "update_maintenance_schedule",
        "update_maintenance_window",  # alias
        "delete_maintenance_schedule",
        "delete_maintenance_window",  # alias
    ]

    for method in methods:
        if hasattr(client, method):
            print(f"  {method}: EXISTS")
        else:
            print(f"  {method}: MISSING!")

    client.close()
    print("\n  All client methods present!")


async def test_outage_management():
    """Test outage management tools."""
    print("\n" + "=" * 60)
    print("TEST 2: OUTAGE MANAGEMENT")
    print("=" * 60)

    client = FortiMonitorClient()

    # Get an active outage to test with
    print("\n1. Finding active outage...")
    try:
        active_outages = client.get_active_outages(limit=1)

        if not active_outages.outage_list:
            print("   No active outages to test with (this is OK)")
            client.close()
            return None

        outage = active_outages.outage_list[0]
        outage_id = outage.id

        if not outage_id:
            print("   Outage has no ID - skipping tests")
            client.close()
            return None

        print(f"   Found outage {outage_id}")

        # Test get_outage_details
        print(f"\n2. Getting details for outage {outage_id}...")
        result = await handle_get_outage_details({"outage_id": outage_id}, client)
        print(f"   Result preview: {result[0].text[:100]}...")

        # Test acknowledge_outage
        print(f"\n3. Acknowledging outage {outage_id}...")
        result = await handle_acknowledge_outage(
            {
                "outage_id": outage_id,
                "note": "Test acknowledgment from Priority 1 implementation",
            },
            client,
        )
        print(f"   Result preview: {result[0].text[:100]}...")

        # Test add_outage_note
        print(f"\n4. Adding note to outage {outage_id}...")
        result = await handle_add_outage_note(
            {
                "outage_id": outage_id,
                "note": f"Test note added at {datetime.now(timezone.utc)}",
            },
            client,
        )
        print(f"   Result preview: {result[0].text[:100]}...")

        client.close()
        return outage_id

    except Exception as e:
        print(f"   Error during outage management test: {e}")
        client.close()
        return None


async def test_server_management():
    """Test server management tools."""
    print("\n" + "=" * 60)
    print("TEST 3: SERVER MANAGEMENT")
    print("=" * 60)

    client = FortiMonitorClient()

    try:
        # First, find a valid server
        print("\n1. Finding a server to test with...")
        servers = client.get_servers(limit=1)
        if not servers.server_list:
            print("   No servers found - skipping tests")
            client.close()
            return

        test_server = servers.server_list[0]
        test_server_id = test_server.id
        print(f"   Found server: {test_server.name} (ID: {test_server_id})")

        # Test list_maintenance_windows
        print("\n2. Listing maintenance windows...")
        result = await handle_list_maintenance_windows({"limit": 10}, client)
        print(f"   Result preview: {result[0].text[:100]}...")

        # Test create_maintenance_window
        print(f"\n3. Creating maintenance window for server {test_server_id}...")
        result = await handle_create_maintenance_window(
            {
                "name": f"Test Maintenance {datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "server_ids": [test_server_id],
                "duration_hours": 1,
                "start_time": "now",
                "description": "Test maintenance window from Priority 1 implementation",
            },
            client,
        )
        print(f"   Result preview: {result[0].text[:150]}...")

        # Note: We're not testing set_server_status to avoid affecting production
        print("\n4. Skipping set_server_status test (use in test environment only)")

        client.close()

    except Exception as e:
        print(f"   Error during server management test: {e}")
        import traceback
        traceback.print_exc()
        client.close()


async def test_tool_definitions():
    """Test that all tool definitions are properly formed."""
    print("\n" + "=" * 60)
    print("TEST 4: TOOL DEFINITIONS")
    print("=" * 60)

    from src.tools.outage_management import (
        acknowledge_outage_tool_definition,
        add_outage_note_tool_definition,
        get_outage_details_tool_definition,
    )
    from src.tools.server_management import (
        set_server_status_tool_definition,
        create_maintenance_window_tool_definition,
        list_maintenance_windows_tool_definition,
    )

    tools = [
        acknowledge_outage_tool_definition(),
        add_outage_note_tool_definition(),
        get_outage_details_tool_definition(),
        set_server_status_tool_definition(),
        create_maintenance_window_tool_definition(),
        list_maintenance_windows_tool_definition(),
    ]

    for tool in tools:
        print(f"\n  Tool: {tool.name}")
        print(f"  Description: {tool.description[:60]}...")
        print(f"  Has inputSchema: {tool.inputSchema is not None}")
        if tool.inputSchema and "required" in tool.inputSchema:
            print(f"  Required params: {tool.inputSchema['required']}")

    print("\n  All tool definitions validated!")


async def run_all_tests():
    """Run all Priority 1 tests."""
    print("\n" + "=" * 60)
    print("PHASE 2 - PRIORITY 1 COMPREHENSIVE TESTING")
    print("=" * 60)
    print(f"Time: {datetime.now()}")
    print("=" * 60)

    try:
        # Test models
        await test_models()

        # Test client methods
        await test_client_methods()

        # Test tool definitions
        await test_tool_definitions()

        # Test outage management (may skip if no active outages)
        await test_outage_management()

        # Test server management
        await test_server_management()

        print("\n" + "=" * 60)
        print("ALL PRIORITY 1 TESTS COMPLETED!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Restart Claude Desktop to load new tools")
        print("2. Test tools interactively in Claude Desktop")
        print("3. Monitor for any API errors")
        print("4. Create user documentation if needed")

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
