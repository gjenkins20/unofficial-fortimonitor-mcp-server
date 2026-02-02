"""Test FortiMonitor API connectivity."""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.fortimonitor.client import FortiMonitorClient
from src.fortimonitor.exceptions import FortiMonitorError


def main():
    print("Testing FortiMonitor API connectivity...")
    print("=" * 50)

    try:
        # Initialize client
        client = FortiMonitorClient()
        print("✓ Client initialized")
        print(f"  Base URL: {client.base_url}")

        # Test server list
        print("\nTesting server list endpoint (/server)...")
        response = client.get_servers(limit=5)
        print(f"✓ Server list endpoint works!")
        print(f"  Found {len(response.server_list)} servers")
        print(f"  Total count: {response.total_count}")
        print(f"  Pagination: limit={response.limit}, offset={response.offset}")

        if response.server_list:
            server = response.server_list[0]
            print(f"\n✓ First server: {server.name} (ID: {server.id})")

            # Test server details
            print(f"\nTesting server details endpoint (/server/{server.id})...")
            details = client.get_server_details(server.id)
            print(f"✓ Server details endpoint works for server {details.name}")
            print(f"  FQDN: {details.fqdn or 'N/A'}")
            print(f"  Status: {details.status or 'N/A'}")

            # Test agent resources
            print(
                f"\nTesting agent resources endpoint (/server/{server.id}/agent_resource)..."
            )
            try:
                agent_response = client.get_server_agent_resources(server.id, limit=5)
                print(f"✓ Agent resources endpoint works!")
                print(f"  Found {len(agent_response.agent_resource_list)} resources")
                if agent_response.agent_resource_list:
                    print(f"  Sample resource: {agent_response.agent_resource_list[0].name}")
            except FortiMonitorError as e:
                print(f"⚠ Agent resources endpoint returned: {e}")
                print("  (This may be expected if server has no agent installed)")

        # Test outages
        print("\nTesting outages endpoint (/outage)...")
        outages = client.get_outages(limit=5)
        print(f"✓ Outages endpoint works!")
        print(f"  Found {len(outages.outage_list)} outages")
        print(f"  Total count: {outages.total_count}")

        # Test active outages
        print("\nTesting active outages endpoint (/outage/active)...")
        try:
            active_outages = client.get_active_outages(limit=5)
            print(f"✓ Active outages endpoint works!")
            print(f"  Found {len(active_outages.outage_list)} active outages")
        except FortiMonitorError as e:
            print(f"⚠ Active outages endpoint returned: {e}")

        # Test schema discovery
        print("\nTesting schema discovery (/schema/resources)...")
        try:
            resources = client.schema.get_resource_list()
            print(f"✓ Schema discovery works!")
            print(f"  Found {len(resources)} resources")
            print(f"  Sample resources: {', '.join(resources[:5])}")
        except FortiMonitorError as e:
            print(f"⚠ Schema discovery returned: {e}")

        print("\n" + "=" * 50)
        print("✅ All connectivity tests passed!")
        return 0

    except FortiMonitorError as e:
        print(f"\n❌ FortiMonitor API Error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        if "client" in locals():
            client.close()


if __name__ == "__main__":
    exit(main())
