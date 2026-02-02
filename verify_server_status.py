"""Verify if server 42008397 is actually down and why outages aren't being detected."""

import requests
import json
from datetime import datetime

API_KEY = "798413e3-ac02-43b7-a56d-3c5d940417c5"
BASE_URL = "https://api2.panopta.com/v2"
SERVER_ID = 42008397

def get_server_status():
    """Get detailed server status."""
    url = f"{BASE_URL}/server/{SERVER_ID}"
    params = {'api_key': API_KEY}
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        print("="*80)
        print("SERVER INFORMATION")
        print("="*80)
        print(f"ID: {SERVER_ID}")
        print(f"Name: {data.get('name')}")
        print(f"FQDN: {data.get('fqdn')}")
        print(f"Status: {data.get('status')} ⚠️" if data.get('status') != 'active' else f"Status: {data.get('status')} ✅")
        print(f"Created: {data.get('created')}")
        print(f"Updated: {data.get('updated')}")
        print(f"Description: {data.get('description', 'N/A')}")
        print(f"Tags: {data.get('tags', 'None')}")
        print(f"\nServer URL: {data.get('url')}")
        
        if data.get('status') != 'active':
            print(f"\n🚨 WARNING: Server status is '{data.get('status')}' (not 'active')")
            print("This indicates the server may be down or having issues!")
        
        return data
    else:
        print(f"❌ Error getting server: HTTP {response.status_code}")
        print(response.text[:200])
        return None

def check_all_active_outages():
    """Check ALL active outages in the system."""
    url = f"{BASE_URL}/outage/active"
    params = {'api_key': API_KEY, 'limit': 500}
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        outages = data.get('outage_list', [])
        
        print("\n" + "="*80)
        print(f"ALL ACTIVE OUTAGES IN SYSTEM")
        print("="*80)
        print(f"Total active outages: {len(outages)}")
        
        if not outages:
            print("\n✅ No active outages in the entire system.")
            print("If your server is down, this is a DETECTION PROBLEM.")
            return []
        
        # Check if any outages are for our server
        our_server_outages = []
        other_outages = []
        
        for idx, outage in enumerate(outages, 1):
            server_url = outage.get('server', '')
            is_ours = str(SERVER_ID) in server_url
            
            if is_ours:
                our_server_outages.append(outage)
            else:
                other_outages.append(outage)
        
        # Show other outages first
        if other_outages:
            print(f"\n📋 Other servers with active outages: {len(other_outages)}")
            for outage in other_outages[:5]:  # Show first 5
                print(f"   - Server: {outage.get('server', 'N/A')}")
                print(f"     Severity: {outage.get('severity')}, Started: {outage.get('start')}")
        
        # Show our server outages
        if our_server_outages:
            print(f"\n🚨 ACTIVE OUTAGES FOR SERVER {SERVER_ID}: {len(our_server_outages)}")
            for outage in our_server_outages:
                print(f"\n  Outage ID: {outage.get('id')}")
                print(f"  Server: {outage.get('server')}")
                print(f"  Start: {outage.get('start')}")
                print(f"  End: {outage.get('end', 'Ongoing')}")
                print(f"  Severity: {outage.get('severity')}")
                print(f"  Status: {outage.get('status')}")
                print(f"  Acknowledged: {outage.get('acknowledged', False)}")
                print(f"  Message: {outage.get('message', 'N/A')}")
        else:
            print(f"\nℹ️  No active outages found for server {SERVER_ID}")
        
        return our_server_outages
    else:
        print(f"❌ Error getting active outages: HTTP {response.status_code}")
        print(response.text[:200])
        return []

def check_recent_outages():
    """Check recent outages for our server (not just active)."""
    url = f"{BASE_URL}/outage"
    
    # Try different query approaches
    print("\n" + "="*80)
    print(f"RECENT OUTAGES FOR SERVER {SERVER_ID}")
    print("="*80)
    
    # Approach 1: Filter by server parameter
    print("\n1. Using server parameter filter:")
    params1 = {
        'api_key': API_KEY,
        'server': SERVER_ID,
        'limit': 50
    }
    response1 = requests.get(url, params=params1)
    if response1.status_code == 200:
        data1 = response1.json()
        outages1 = data1.get('outage_list', [])
        total1 = data1.get('meta', {}).get('total_count', 0)
        print(f"   Found {len(outages1)} outages (total: {total1})")
        
        if outages1:
            for outage in outages1[:3]:  # Show first 3
                print(f"   - ID: {outage.get('id')}, Severity: {outage.get('severity')}")
                print(f"     Start: {outage.get('start')}, End: {outage.get('end', 'Ongoing')}")
    else:
        print(f"   ❌ Failed: HTTP {response1.status_code}")
        outages1 = []
    
    # Approach 2: Get all recent and filter client-side
    print("\n2. Getting all recent outages and filtering:")
    params2 = {
        'api_key': API_KEY,
        'limit': 100
    }
    response2 = requests.get(url, params=params2)
    if response2.status_code == 200:
        data2 = response2.json()
        all_outages = data2.get('outage_list', [])
        our_outages = [o for o in all_outages if str(SERVER_ID) in str(o.get('server', ''))]
        print(f"   Found {len(our_outages)} outages for our server out of {len(all_outages)} total")
        
        if our_outages:
            for outage in our_outages[:3]:  # Show first 3
                print(f"   - ID: {outage.get('id')}, Severity: {outage.get('severity')}")
                print(f"     Start: {outage.get('start')}, End: {outage.get('end', 'Ongoing')}")
    else:
        print(f"   ❌ Failed: HTTP {response2.status_code}")
        our_outages = []
    
    return outages1 if outages1 else our_outages

def check_server_in_list():
    """Verify server appears in server list."""
    url = f"{BASE_URL}/server"
    params = {
        'api_key': API_KEY,
        'limit': 500
    }
    
    print("\n" + "="*80)
    print(f"VERIFYING SERVER {SERVER_ID} IN SERVER LIST")
    print("="*80)
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        servers = data.get('server_list', [])
        total = data.get('meta', {}).get('total_count', 0)
        
        # Find our server
        our_server = None
        for server in servers:
            if str(SERVER_ID) in str(server.get('url', '')):
                our_server = server
                break
        
        if our_server:
            print(f"✅ Server {SERVER_ID} found in list")
            print(f"   Name: {our_server.get('name')}")
            print(f"   Status: {our_server.get('status')}")
        else:
            print(f"⚠️  Server {SERVER_ID} NOT found in first {len(servers)} servers")
            print(f"   (Total servers: {total})")
        
        return our_server
    else:
        print(f"❌ Failed to get server list: HTTP {response.status_code}")
        return None

# Run all checks
print("\n" + "="*80)
print("FORTIMONITOR SERVER STATUS VERIFICATION")
print("="*80)
print(f"Server ID: {SERVER_ID}")
print(f"Time: {datetime.now()}")
print("="*80)

server = get_server_status()
active_outages = check_all_active_outages()
recent_outages = check_recent_outages()
server_in_list = check_server_in_list()

# Final analysis
print("\n" + "="*80)
print("FINAL ANALYSIS")
print("="*80)

server_status = server.get('status', 'unknown') if server else 'unknown'
print(f"\n1. Server Status: {server_status}")

if server_status == 'active':
    print("   ✅ Server is marked as ACTIVE")
elif server_status == 'inactive':
    print("   🚨 Server is marked as INACTIVE (DOWN!)")
else:
    print(f"   ⚠️  Server has unusual status: {server_status}")

print(f"\n2. Active Outages for Server {SERVER_ID}: {len(active_outages)}")
if active_outages:
    print("   🚨 Active outages detected!")
else:
    print("   ℹ️  No active outages")

print(f"\n3. Recent Outages for Server {SERVER_ID}: {len(recent_outages)}")
if recent_outages:
    print("   ⚠️  Recent outages found in history")
else:
    print("   ℹ️  No recent outages")

# Diagnosis
print("\n" + "="*80)
print("DIAGNOSIS")
print("="*80)

if server_status == 'inactive' and not active_outages:
    print("\n🚨 CRITICAL ISSUE DETECTED:")
    print("   - Server status is 'inactive' (down)")
    print("   - But no active outages are recorded")
    print("\n   CONCLUSION: The MCP server needs to check server.status field,")
    print("   not just rely on outages to detect down servers!")
    
elif server_status == 'active' and not active_outages:
    print("\n✅ Server appears healthy:")
    print("   - Status is 'active'")
    print("   - No active outages")
    print("\n   If you believe the server is down, verify:")
    print("   - Check FortiMonitor web UI")
    print("   - Confirm server ID is correct")
    print("   - Check if monitoring is configured")

elif active_outages:
    print("\n📊 Server has active outages:")
    print("   - MCP should be detecting these")
    print("   - If MCP returns 'no outages', there's a query/filtering bug")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)

if server_status == 'inactive' and not active_outages:
    print("\n1. Add a 'check_server_health' tool that checks server.status")
    print("2. Don't rely solely on outages to detect down servers")
    print("3. Query like: 'Is server X down?' should check both status + outages")

if not active_outages and recent_outages:
    print("\n1. Recent outages exist but none are 'active'")
    print("2. This is normal - outages were resolved")
    print("3. Use time-based queries to see historical issues")

print("\n" + "="*80)
print("Save this output and share with the team.")
print("="*80)
