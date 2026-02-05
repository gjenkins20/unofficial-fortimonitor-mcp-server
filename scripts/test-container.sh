#!/bin/bash
# =============================================================================
# FortiMonitor MCP Server - Container Test Script
# =============================================================================
#
# Usage:
#   ./scripts/test-container.sh                              # Basic tests
#   FORTIMONITOR_API_KEY=your-key ./scripts/test-container.sh  # Full tests with API
#
# =============================================================================

set -e

# Configuration
IMAGE_NAME="${IMAGE_NAME:-fortimonitor-mcp}"
VERSION="${VERSION:-latest}"
API_KEY="${FORTIMONITOR_API_KEY:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN} FortiMonitor MCP Server - Container Tests${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""

TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local test_cmd="$2"

    echo -n "Testing: $test_name... "

    if eval "$test_cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test 1: Image exists
run_test "Image exists" "docker image inspect ${IMAGE_NAME}:${VERSION}"

# Test 2: Container starts (with dummy key for basic test)
run_test "Container starts" "docker run --rm -e FORTIMONITOR_API_KEY=test-key ${IMAGE_NAME}:${VERSION} python -c 'print(\"Container OK\")'"

# Test 3: Python imports work
run_test "Python imports" "docker run --rm -e FORTIMONITOR_API_KEY=test-key ${IMAGE_NAME}:${VERSION} python -c 'from src.server import FortiMonitorMCPServer; print(\"Imports OK\")'"

# Test 4: Config module loads
run_test "Config module" "docker run --rm -e FORTIMONITOR_API_KEY=test-key ${IMAGE_NAME}:${VERSION} python -c 'from src.config import get_settings; print(\"Config OK\")'"

# Test 5: MCP module available
run_test "MCP module" "docker run --rm -e FORTIMONITOR_API_KEY=test-key ${IMAGE_NAME}:${VERSION} python -c 'from mcp.server import Server; print(\"MCP OK\")'"

# Test 6: Environment variable handling
run_test "Env var handling" "docker run --rm -e FORTIMONITOR_API_KEY=my-test-key-123 ${IMAGE_NAME}:${VERSION} python -c 'from src.config import get_settings; s = get_settings(); assert s.fortimonitor_api_key == \"my-test-key-123\", \"Key mismatch\"'"

# Test 7: Cache directory exists and is writable
run_test "Cache directory" "docker run --rm -e FORTIMONITOR_API_KEY=test-key ${IMAGE_NAME}:${VERSION} python -c 'import os; os.makedirs(\"/app/cache/schemas\", exist_ok=True); open(\"/app/cache/test.txt\", \"w\").write(\"test\"); print(\"Cache OK\")'"

# Test 8: Non-root user
run_test "Non-root user" "docker run --rm -e FORTIMONITOR_API_KEY=test-key ${IMAGE_NAME}:${VERSION} python -c 'import os; assert os.getuid() != 0, \"Running as root!\"; print(\"Non-root OK\")'"

# Test 9: Tool definitions load
run_test "Tool definitions" "docker run --rm -e FORTIMONITOR_API_KEY=test-key ${IMAGE_NAME}:${VERSION} python -c 'from src.tools.servers import get_servers_tool_definition; t = get_servers_tool_definition(); assert t.name == \"get_servers\"; print(\"Tools OK\")'"

# Test 10: API connectivity (only if real API key provided)
if [ -n "$API_KEY" ] && [ "$API_KEY" != "test-key" ]; then
    echo ""
    echo -e "${YELLOW}Running API connectivity test...${NC}"
    run_test "API connectivity" "docker run --rm -e FORTIMONITOR_API_KEY=${API_KEY} ${IMAGE_NAME}:${VERSION} python -c 'from src.fortimonitor.client import FortiMonitorClient; c = FortiMonitorClient(); r = c.get_servers(limit=1); print(f\"API OK: {len(r.server_list)} servers\")'"
else
    echo ""
    echo -e "${YELLOW}Skipping API test (no API key provided)${NC}"
    echo "Set FORTIMONITOR_API_KEY to run API connectivity test"
fi

# Summary
echo ""
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN} Test Summary${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo -e "  Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "  Failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
