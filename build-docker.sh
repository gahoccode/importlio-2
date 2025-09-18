#!/bin/bash

# Cross-platform Docker build script for Mac M1 compatibility
# This script builds for both ARM64 (Mac M1) and AMD64 (deployment)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Building cross-platform Docker image for importfolio...${NC}"

# Check if buildx is available
if ! docker buildx version > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker buildx is not available. Please update Docker Desktop.${NC}"
    exit 1
fi

# Create builder if it doesn't exist
BUILDER_NAME="importfolio-builder"
if ! docker buildx inspect $BUILDER_NAME > /dev/null 2>&1; then
    echo -e "${YELLOW}📦 Creating new buildx builder: $BUILDER_NAME${NC}"
    docker buildx create --name $BUILDER_NAME --use
else
    echo -e "${GREEN}✅ Using existing builder: $BUILDER_NAME${NC}"
    docker buildx use $BUILDER_NAME
fi

# Build for multiple platforms
echo -e "${YELLOW}🔨 Building for linux/amd64 and linux/arm64...${NC}"

docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag importfolio:latest \
    --tag importfolio:$(date +%Y%m%d) \
    --load \
    .

echo -e "${GREEN}✅ Cross-platform build completed successfully!${NC}"
echo -e "${YELLOW}📝 Available images:${NC}"
docker images | grep importfolio | head -5