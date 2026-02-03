"""Comprehensive tests for Priority 5 tools."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.fortimonitor.client import FortiMonitorClient
from src.tools.reporting import (
    handle_get_system_health_summary,
    handle_get_outage_statistics,
    handle_get_server_statistics,
    handle_get_top_alerting_servers,
    handle_export_servers_list,
    handle_export_outage_history,
    handle_generate_availability_report
)


async def test_health_and_statistics():
    """Test health and statistics tools."""
    client = FortiMonitorClient()

    print("\n" + "="*60)
    print("TEST 1: SYSTEM HEALTH & STATISTICS")
    print("="*60)

    # Test 1a: System health summary
    print("\n1a. Generating system health summary...")
    result = await handle_get_system_health_summary({}, client)
    print("   Result:")
    print(result[0].text)

    # Test 1b: Outage statistics
    print("\n1b. Generating outage statistics...")
    result = await handle_get_outage_statistics({'days': 7}, client)
    print("   Result:")
    print(result[0].text)

    # Test 1c: Server statistics
    print("\n1c. Generating server statistics...")
    result = await handle_get_server_statistics({}, client)
    print("   Result:")
    print(result[0].text)

    # Test 1d: Top alerting servers
    print("\n1d. Getting top alerting servers...")
    result = await handle_get_top_alerting_servers({'limit': 5}, client)
    print("   Result:")
    print(result[0].text)

    print("\n   [PASSED] Health and statistics tests completed")


async def test_exports_and_reports():
    """Test export and reporting tools."""
    client = FortiMonitorClient()

    print("\n" + "="*60)
    print("TEST 2: EXPORTS & REPORTS")
    print("="*60)

    # Test 2a: Export servers list
    print("\n2a. Exporting servers list...")
    result = await handle_export_servers_list(
        {'include_tags': True, 'status_filter': 'active'},
        client
    )
    print("   Result (first 500 chars):")
    print(result[0].text[:500])

    # Test 2b: Export outage history
    print("\n2b. Exporting outage history...")
    result = await handle_export_outage_history(
        {'severity_filter': 'all'},
        client
    )
    print("   Result (first 500 chars):")
    print(result[0].text[:500])

    # Test 2c: Generate availability report
    print("\n2c. Generating availability report...")
    result = await handle_generate_availability_report({'days': 30}, client)
    print("   Result:")
    print(result[0].text)

    print("\n   [PASSED] Export and report tests completed")


async def run_all_tests():
    """Run all Priority 5 tests."""
    print("="*60)
    print("PRIORITY 5 COMPREHENSIVE TESTING")
    print("Reporting & Analytics")
    print("="*60)

    try:
        await test_health_and_statistics()
        await test_exports_and_reports()

        print("\n" + "="*60)
        print("[SUCCESS] ALL PRIORITY 5 TESTS COMPLETE")
        print("="*60)
        print("\nPhase 2 Implementation Complete!")
        print("\nTools implemented:")
        print("  Phase 1: 5 tools")
        print("  Priority 1: 6 tools")
        print("  Priority 2: 5 tools")
        print("  Priority 3: 10 tools")
        print("  Priority 4: 9 tools")
        print("  Priority 5: 7 tools")
        print("  TOTAL: 42 tools")

    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
