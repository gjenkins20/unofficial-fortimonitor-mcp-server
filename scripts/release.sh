#!/bin/bash
# =============================================================================
# FortiMonitor MCP Server - Release Script
# =============================================================================
#
# Creates a new release by building, tagging, and pushing to registry.
#
# Usage:
#   REGISTRY=your-dockerhub-username ./scripts/release.sh 1.0.0
#
# =============================================================================

set -e

# Configuration
IMAGE_NAME="${IMAGE_NAME:-unofficial-fortimonitor-mcp}"
REGISTRY="${REGISTRY:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for version argument
if [ -z "$1" ]; then
    echo -e "${RED}Error: Version argument required${NC}"
    echo ""
    echo "Usage: ./scripts/release.sh <version>"
    echo "Example: ./scripts/release.sh 1.0.0"
    exit 1
fi

VERSION="$1"

# Validate version format (semver)
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}Error: Invalid version format${NC}"
    echo "Version must be in semver format: X.Y.Z"
    exit 1
fi

# Check registry is set
if [ -z "$REGISTRY" ]; then
    echo -e "${RED}Error: REGISTRY environment variable is required${NC}"
    echo ""
    echo "Usage: REGISTRY=your-dockerhub-username ./scripts/release.sh ${VERSION}"
    exit 1
fi

echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN} FortiMonitor MCP Server - Release ${VERSION}${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Step 1: Build
echo -e "${YELLOW}Step 1: Building image...${NC}"
VERSION="$VERSION" ./scripts/build.sh

# Step 2: Test
echo ""
echo -e "${YELLOW}Step 2: Running tests...${NC}"
VERSION="$VERSION" ./scripts/test-container.sh

# Step 3: Push
echo ""
echo -e "${YELLOW}Step 3: Pushing to registry...${NC}"
VERSION="$VERSION" REGISTRY="$REGISTRY" ./scripts/push.sh

# Step 4: Git tag (optional)
echo ""
echo -e "${YELLOW}Step 4: Git tagging...${NC}"
if git rev-parse "v${VERSION}" >/dev/null 2>&1; then
    echo "Git tag v${VERSION} already exists, skipping"
else
    read -p "Create git tag v${VERSION}? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git tag -a "v${VERSION}" -m "Release version ${VERSION}"
        echo "Created tag v${VERSION}"

        read -p "Push tag to origin? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git push origin "v${VERSION}"
            echo "Pushed tag to origin"
        fi
    fi
fi

echo ""
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN} Release ${VERSION} Complete!${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo "Docker image: ${REGISTRY}/${IMAGE_NAME}:${VERSION}"
echo ""
echo "Users can now run:"
echo "  docker pull ${REGISTRY}/${IMAGE_NAME}:${VERSION}"
echo "  docker run -e FORTIMONITOR_API_KEY=their-key ${REGISTRY}/${IMAGE_NAME}:${VERSION}"
echo ""
