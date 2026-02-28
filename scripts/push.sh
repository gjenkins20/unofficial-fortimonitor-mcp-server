#!/bin/bash
# =============================================================================
# FortiMonitor MCP Server - Docker Push Script
# =============================================================================
#
# Usage:
#   REGISTRY=your-dockerhub-username ./scripts/push.sh
#   REGISTRY=ghcr.io/your-org VERSION=1.0.0 ./scripts/push.sh
#
# =============================================================================

set -e

# Configuration
IMAGE_NAME="${IMAGE_NAME:-unofficial-fortimonitor-mcp}"
VERSION="${VERSION:-latest}"
REGISTRY="${REGISTRY:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN} FortiMonitor MCP Server - Docker Push${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""

# Check registry is set
if [ -z "$REGISTRY" ]; then
    echo -e "${RED}Error: REGISTRY environment variable is required${NC}"
    echo ""
    echo "Usage: REGISTRY=your-dockerhub-username ./scripts/push.sh"
    exit 1
fi

# Check if image exists
if ! docker image inspect "${IMAGE_NAME}:${VERSION}" > /dev/null 2>&1; then
    echo -e "${RED}Error: Image ${IMAGE_NAME}:${VERSION} not found${NC}"
    echo "Run ./scripts/build.sh first"
    exit 1
fi

echo -e "${YELLOW}Pushing to registry: ${REGISTRY}${NC}"
echo ""

# Tag images for registry
echo "Tagging images..."
docker tag "${IMAGE_NAME}:${VERSION}" "${REGISTRY}/${IMAGE_NAME}:${VERSION}"
docker tag "${IMAGE_NAME}:latest" "${REGISTRY}/${IMAGE_NAME}:latest"

# Push images
echo ""
echo "Pushing ${REGISTRY}/${IMAGE_NAME}:${VERSION}..."
docker push "${REGISTRY}/${IMAGE_NAME}:${VERSION}"

echo ""
echo "Pushing ${REGISTRY}/${IMAGE_NAME}:latest..."
docker push "${REGISTRY}/${IMAGE_NAME}:latest"

echo ""
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN} Push Complete!${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo "  ${REGISTRY}/${IMAGE_NAME}:${VERSION}"
echo "  ${REGISTRY}/${IMAGE_NAME}:latest"
echo ""
echo "Pull with:"
echo "  docker pull ${REGISTRY}/${IMAGE_NAME}:latest"
echo ""
