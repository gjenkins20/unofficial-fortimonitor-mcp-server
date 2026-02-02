"""
Test script for Phase 2 Priority 4 - Notifications & Agent Resources.

Tests:
1. Notification Schedules - List and get details
2. Notification Groups - List groups
3. Contacts - List notification contacts
4. Agent Resource Types - List and get details
5. Server Agent Resources - List resources for a server
"""

import asyncio
import sys

# Add src to path for imports
sys.path.insert(0, '.')

from src.fortimonitor.client import FortiMonitorClient
from src.tools.notifications import (
    handle_list_notification_schedules,
    handle_get_notification_schedule_details,
    handle_list_notification_groups,
    handle_list_contacts,
)
from src.tools.agent_resources import (
    handle_list_agent_resource_types,
    handle_get_agent_resource_type_details,
    handle_list_server_resources,
    handle_get_resource_details,
)


def print_separator(title: str):
    """Print a formatted section separator."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


async def test_notification_schedules(client: FortiMonitorClient):
    """Test notification schedule tools."""
    print_separator("TEST: List Notification Schedules")

    result = await handle_list_notification_schedules({"limit": 10}, client)
    print(result[0].text)

    # Try to get details of first schedule if any exist
    if "ID:" in result[0].text:
        # Extract first ID from the output
        import re
        match = re.search(r'\(ID: (\d+)\)', result[0].text)
        if match:
            schedule_id = int(match.group(1))
            print_separator(f"TEST: Get Notification Schedule Details (ID: {schedule_id})")
            detail_result = await handle_get_notification_schedule_details(
                {"schedule_id": schedule_id}, client
            )
            print(detail_result[0].text)


async def test_notification_groups(client: FortiMonitorClient):
    """Test notification group tools."""
    print_separator("TEST: List Notification Groups")

    result = await handle_list_notification_groups({"limit": 10}, client)
    print(result[0].text)


async def test_contacts(client: FortiMonitorClient):
    """Test contact tools."""
    print_separator("TEST: List Contacts")

    result = await handle_list_contacts({"limit": 10}, client)
    print(result[0].text)


async def test_agent_resource_types(client: FortiMonitorClient):
    """Test agent resource type tools."""
    print_separator("TEST: List Agent Resource Types")

    result = await handle_list_agent_resource_types({"limit": 20}, client)
    print(result[0].text)

    # Try to get details of first type if any exist
    if "ID:" in result[0].text:
        import re
        match = re.search(r'\(ID: (\d+)\)', result[0].text)
        if match:
            type_id = int(match.group(1))
            print_separator(f"TEST: Get Agent Resource Type Details (ID: {type_id})")
            detail_result = await handle_get_agent_resource_type_details(
                {"type_id": type_id}, client
            )
            print(detail_result[0].text)


async def test_server_resources(client: FortiMonitorClient, server_id: int):
    """Test server agent resource tools."""
    print_separator(f"TEST: List Server Resources (Server ID: {server_id})")

    result = await handle_list_server_resources(
        {"server_id": server_id, "limit": 10}, client
    )
    print(result[0].text)

    # Try to get details of first resource if any exist
    if "ID:" in result[0].text and "not found" not in result[0].text.lower():
        import re
        matches = re.findall(r'\*\*[^*]+\*\* \(ID: (\d+)\)', result[0].text)
        if matches:
            resource_id = int(matches[0])
            print_separator(f"TEST: Get Resource Details (Resource ID: {resource_id})")
            detail_result = await handle_get_resource_details(
                {"server_id": server_id, "resource_id": resource_id}, client
            )
            print(detail_result[0].text)


async def main():
    """Run all Priority 4 tests."""
    print("\n" + "="*60)
    print(" PHASE 2 PRIORITY 4 TESTS - NOTIFICATIONS & AGENT RESOURCES")
    print("="*60)

    client = FortiMonitorClient()

    try:
        # Test notification tools
        await test_notification_schedules(client)
        await test_notification_groups(client)
        await test_contacts(client)

        # Test agent resource tools
        await test_agent_resource_types(client)

        # Get a server ID for resource tests
        print_separator("Finding a server for resource tests...")
        servers_response = client.get_servers(limit=1)
        if servers_response.server_list:
            server_id = servers_response.server_list[0].id
            print(f"Using server: {servers_response.server_list[0].name} (ID: {server_id})")
            await test_server_resources(client, server_id)
        else:
            print("No servers found - skipping server resource tests")

        print_separator("ALL PRIORITY 4 TESTS COMPLETED")

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
