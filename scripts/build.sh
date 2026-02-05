#!/bin/bash
# =============================================================================
# FortiMonitor MCP Server - Docker Build Script
# =============================================================================
#
# Usage:
#   ./scripts/build.sh                    # Build with default settings
#   VERSION=1.0.0 ./scripts/build.sh      # Build with version tag
#   REGISTRY=myregistry ./scripts/build.sh # Build with registry prefix
#
# =============================================================================

set -e

# Configuration
IMAGE_NAME="${IMAGE_NAME:-fortimonitor-mcp}"
VERSION="${VERSION:-latest}"
REGISTRY="${REGISTRY:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN} FortiMonitor MCP Server - Docker Build${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}Building Docker image: ${IMAGE_NAME}:${VERSION}${NC}"
echo ""

# Build the image
docker build \
    --tag "${IMAGE_NAME}:${VERSION}" \
    --tag "${IMAGE_NAME}:latest" \
    --file Dockerfile \
    --progress=plain \
    .

# Tag for registry if specified
if [ -n "$REGISTRY" ]; then
    echo ""
    echo -e "${YELLOW}Tagging for registry: ${REGISTRY}${NC}"
    docker tag "${IMAGE_NAME}:${VERSION}" "${REGISTRY}/${IMAGE_NAME}:${VERSION}"
    docker tag "${IMAGE_NAME}:latest" "${REGISTRY}/${IMAGE_NAME}:latest"
fi

echo ""
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN} Build Complete!${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo "  Image: ${IMAGE_NAME}:${VERSION}"
echo "  Image: ${IMAGE_NAME}:latest"
if [ -n "$REGISTRY" ]; then
    echo "  Registry: ${REGISTRY}/${IMAGE_NAME}:${VERSION}"
    echo "  Registry: ${REGISTRY}/${IMAGE_NAME}:latest"
fi
echo ""
echo "Run with:"
echo "  docker run -e FORTIMONITOR_API_KEY=your-key ${IMAGE_NAME}:latest"
echo ""
