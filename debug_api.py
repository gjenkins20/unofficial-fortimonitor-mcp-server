"""Direct API testing to isolate the 500 error issue."""

import requests
from datetime import datetime, timedelta

# Your API details
API_KEY = "798413e3-ac02-43b7-a56d-3c5d940417c5"
BASE_URL = "https://api2.panopta.com/v2"
SERVER_ID = 42008397

def test_endpoint(endpoint, params=None):
    """Test an API endpoint directly."""
    url = f"{BASE_URL}/{endpoint}"
    if params is None:
        params = {}
    params['api_key'] = API_KEY
    
    print(f"\n{'='*80}")
    print(f"Testing: {endpoint}")
    print(f"Params: {params}")
    print(f"{'='*80}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse Preview:")
            if isinstance(data, dict):
                for key, value in list(data.items())[:5]:
                    print(f"  {key}: {str(value)[:100]}")
            else:
                print(str(data)[:500])
            return data
        else:
            print(f"\nError Response:")
            print(response.text[:500])
            return None
    except Exception as e:
        print(f"\nException: {type(e).__name__}: {e}")
        return None

print("\n" + "="*80)
print("FORTIMONITOR API DIRECT TESTING")
print("="*80)
print(f"Testing server: {SERVER_ID}")
print(f"Time: {datetime.now()}")

# Test 1: Get server details (baseline - should work)
print("\n" + "="*80)
print("TEST 1: Server Details (BASELINE - should work)")
print("="*80)
server_data = test_endpoint(f"server/{SERVER_ID}")

# Test 2: Get metrics WITHOUT full parameter
print("\n" + "="*80)
print("TEST 2: Metrics WITHOUT full=true (should work)")
print("="*80)
metrics_simple = test_endpoint(
    f"server/{SERVER_ID}/agent_resource",
    {"limit": 10}
)

# Test 3: Get metrics WITH full=true (this is what's failing)
print("\n" + "="*80)
print("TEST 3: Metrics WITH full=true (THIS IS FAILING IN MCP)")
print("="*80)
metrics_full = test_endpoint(
    f"server/{SERVER_ID}/agent_resource",
    {"limit": 10, "full": "true"}
)

# Test 4: Get ALL active outages (not filtered by server)
print("\n" + "="*80)
print("TEST 4: ALL Active Outages (no server filter)")
print("="*80)
active_outages = test_endpoint("outage/active", {"limit": 100})

# Test 5: Get outages for this specific server
print("\n" + "="*80)
print(f"TEST 5: Outages filtered by server {SERVER_ID}")
print("="*80)
server_outages = test_endpoint("outage", {"server": SERVER_ID, "limit": 100})

# Test 6: Get recent outages without server filter
print("\n" + "="*80)
print("TEST 6: Recent outages (no server filter, shows pagination)")
print("="*80)
recent_outages = test_endpoint("outage", {"limit": 20})

# Test 7: Check server list to see if our server appears
print("\n" + "="*80)
print("TEST 7: Server List (verify server exists)")
print("="*80)
server_list = test_endpoint("server", {"limit": 100})

print("\n" + "="*80)
print("ANALYSIS & RESULTS")
print("="*80)

print("\n1. SERVER INFORMATION:")
if server_data:
    print(f"   Status: {server_data.get('status', 'unknown')}")
    print(f"   Name: {server_data.get('name', 'N/A')}")
    print(f"   FQDN: {server_data.get('fqdn', 'N/A')}")
else:
    print("   ❌ Could not retrieve server data")

print("\n2. METRICS TESTS:")
if metrics_simple:
    count = len(metrics_simple.get('agent_resource_list', []))
    print(f"   ✅ WITHOUT full=true: SUCCESS ({count} resources)")
else:
    print(f"   ❌ WITHOUT full=true: FAILED")

if metrics_full:
    count = len(metrics_full.get('agent_resource_list', []))
    print(f"   ✅ WITH full=true: SUCCESS ({count} resources)")
else:
    print(f"   ❌ WITH full=true: FAILED (This is the problem!)")

print("\n3. OUTAGE DETECTION:")
if active_outages:
    total_active = len(active_outages.get('outage_list', []))
    print(f"   Active outages in system: {total_active}")
    
    # Check if any are for our server
    our_outages = []
    for outage in active_outages.get('outage_list', []):
        if str(SERVER_ID) in str(outage.get('server', '')):
            our_outages.append(outage)
    
    if our_outages:
        print(f"   🚨 ACTIVE OUTAGES FOR SERVER {SERVER_ID}: {len(our_outages)}")
        for outage in our_outages:
            print(f"      - ID: {outage.get('id')}, Severity: {outage.get('severity')}")
    else:
        print(f"   ℹ️  No active outages for server {SERVER_ID}")
else:
    print(f"   ❌ Could not retrieve active outages")

if server_outages:
    total = server_outages.get('meta', {}).get('total_count', 0)
    showing = len(server_outages.get('outage_list', []))
    print(f"   Server-specific outages: {showing} shown, {total} total")
else:
    print(f"   ❌ Could not retrieve server-specific outages")

print("\n4. VERDICT:")
if server_data and server_data.get('status') != 'active':
    print(f"   ⚠️  SERVER STATUS IS: {server_data.get('status').upper()}")
    print("   This may indicate the server is down!")

if metrics_simple and not metrics_full:
    print("   ⚠️  METRICS WORK WITHOUT full=true BUT FAIL WITH IT")
    print("   Solution: Remove full parameter from tool definition")

if not active_outages or (active_outages and not any(str(SERVER_ID) in str(o.get('server', '')) for o in active_outages.get('outage_list', []))):
    if server_data and server_data.get('status') != 'active':
        print("   🚨 CRITICAL: Server appears down but no outages detected!")
        print("   This is a detection problem - need to check server status directly")

print("\n" + "="*80)
print("RECOMMENDATIONS:")
print("="*80)
print("\n1. If 'full=true' fails: Remove 'full' parameter from get_server_metrics tool")
print("2. If server is down but no outages: Add tool to check server.status field")
print("3. If outages exist but not detected: Fix query parameters or filtering")
print("\nSave this output and share with the team for analysis.")
