#!/bin/bash

# Shell script for building and pushing Docker images to GitHub Container Registry (GHCR)
# Usage: ./build-and-push.sh [--tag TAG] [--build-only] [--help]

set -euo pipefail

# Configuration
REGISTRY="ghcr.io"
REPOSITORY="gahoccode/importlio-2"
IMAGE_NAME="${REGISTRY}/${REPOSITORY}"
PLATFORMS="linux/amd64,linux/arm64"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BUILD_ONLY=false
CUSTOM_TAG=""

# Functions
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

die() {
    error "$1"
    exit 1
}

show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Build and push Docker image to GitHub Container Registry (GHCR)

OPTIONS:
    --tag TAG       Use custom tag instead of auto-generated tag
    --build-only    Build image without pushing to registry
    --help          Show this help message

EXAMPLES:
    $0                          # Build and push with auto-generated tag
    $0 --tag v1.2.3            # Build and push with custom tag
    $0 --build-only            # Build only, don't push

AUTHENTICATION:
    Set GITHUB_TOKEN environment variable or ensure 'gh' CLI is authenticated

AUTO-GENERATED TAGS:
    - Git tags (v*): Uses the tag name
    - Main branch: Uses 'latest' and 'main' tags
    - Other branches: Uses branch name as tag
    - Fallback: Uses short commit SHA

EOF
}

check_dependencies() {
    log "Checking dependencies..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        die "Docker is not installed or not in PATH"
    fi
    
    # Check Docker Buildx
    if ! docker buildx version &> /dev/null; then
        die "Docker Buildx is not available"
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        die "Git is not installed or not in PATH"
    fi
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir &> /dev/null; then
        die "Not in a git repository"
    fi
    
    success "All dependencies are available"
}

authenticate_ghcr() {
    log "Authenticating with GitHub Container Registry..."
    
    # Try GITHUB_TOKEN first
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        echo "${GITHUB_TOKEN}" | docker login "${REGISTRY}" --username "$(git config user.name || echo 'unknown')" --password-stdin
        success "Authenticated using GITHUB_TOKEN"
        return 0
    fi
    
    # Try GitHub CLI
    if command -v gh &> /dev/null; then
        if gh auth status &> /dev/null; then
            gh auth token | docker login "${REGISTRY}" --username "$(gh api user --jq .login)" --password-stdin
            success "Authenticated using GitHub CLI"
            return 0
        fi
    fi
    
    die "Authentication failed. Please set GITHUB_TOKEN environment variable or authenticate with 'gh auth login'"
}

generate_tags() {
    local tags=()
    
    if [[ -n "$CUSTOM_TAG" ]]; then
        tags=("${IMAGE_NAME}:${CUSTOM_TAG}")
        log "Using custom tag: $CUSTOM_TAG"
    else
        # Check if we're on a git tag
        if git describe --exact-match --tags HEAD &> /dev/null; then
            local git_tag
            git_tag=$(git describe --exact-match --tags HEAD)
            tags=("${IMAGE_NAME}:${git_tag}")
            
            # If it's a version tag (v*), also add semantic version tags
            if [[ $git_tag =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
                local major="${BASH_REMATCH[1]}"
                local minor="${BASH_REMATCH[2]}"
                tags+=("${IMAGE_NAME}:${major}.${minor}")
                tags+=("${IMAGE_NAME}:${major}")
            fi
            
            log "Using git tag: $git_tag"
        else
            # Get current branch
            local branch
            branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
            
            if [[ "$branch" == "main" || "$branch" == "master" ]]; then
                tags=("${IMAGE_NAME}:latest" "${IMAGE_NAME}:main")
                log "Using main branch tags: latest, main"
            elif [[ "$branch" != "HEAD" ]]; then
                # Clean branch name for use as tag
                local clean_branch
                clean_branch=$(echo "$branch" | sed 's/[^a-zA-Z0-9._-]/-/g')
                tags=("${IMAGE_NAME}:${clean_branch}")
                log "Using branch tag: $clean_branch"
            else
                # Fallback to commit SHA
                local commit_sha
                commit_sha=$(git rev-parse --short HEAD)
                tags=("${IMAGE_NAME}:sha-${commit_sha}")
                log "Using commit SHA tag: sha-$commit_sha"
            fi
        fi
    fi
    
    # Convert array to comma-separated string for docker build
    printf -v tag_string '%s,' "${tags[@]}"
    echo "${tag_string%,}"
}

build_image() {
    local tags="$1"
    
    log "Building Docker image with tags: ${tags//,/ }"
    log "Platforms: $PLATFORMS"
    
    # Create buildx builder if it doesn't exist
    if ! docker buildx inspect ghcr-builder &> /dev/null; then
        log "Creating Docker Buildx builder..."
        docker buildx create --name ghcr-builder --use
    else
        docker buildx use ghcr-builder
    fi
    
    # Build arguments
    local build_args=(
        --platform "$PLATFORMS"
        --progress plain
        --pull
    )
    
    # Add tags
    IFS=',' read -ra tag_array <<< "$tags"
    for tag in "${tag_array[@]}"; do
        build_args+=(--tag "$tag")
    done
    
    # Add push flag if not build-only
    if [[ "$BUILD_ONLY" == "false" ]]; then
        build_args+=(--push)
    else
        build_args+=(--load)
        warn "Build-only mode: Image will not be pushed to registry"
    fi
    
    # Execute build
    docker buildx build "${build_args[@]}" .
    
    if [[ "$BUILD_ONLY" == "true" ]]; then
        success "Image built successfully (not pushed)"
    else
        success "Image built and pushed successfully"
    fi
}

test_image() {
    if [[ "$BUILD_ONLY" == "true" ]]; then
        log "Skipping image test in build-only mode"
        return 0
    fi
    
    # Get the first tag for testing
    local first_tag
    first_tag=$(echo "$1" | cut -d',' -f1)
    
    log "Testing image: $first_tag"
    
    # Pull the image we just pushed
    if ! docker pull "$first_tag"; then
        warn "Could not pull image for testing"
        return 0
    fi
    
    # Test the image
    local container_name="test-importfolio-$$"
    
    # Cleanup function
    cleanup_test() {
        docker stop "$container_name" &> /dev/null || true
        docker rm "$container_name" &> /dev/null || true
    }
    
    trap cleanup_test EXIT
    
    # Run container
    if ! docker run --rm -d -p 8080:10000 -e PORT=10000 --name "$container_name" "$first_tag"; then
        warn "Could not start test container"
        return 0
    fi
    
    # Wait for container to start
    log "Waiting for container to start..."
    sleep 10
    
    # Test health endpoint
    if command -v curl &> /dev/null; then
        if curl -f http://localhost:8080/health &> /dev/null; then
            success "Image test passed"
        else
            warn "Health check failed"
        fi
    else
        warn "curl not available, skipping health check"
    fi
    
    cleanup_test
    trap - EXIT
}

cleanup() {
    log "Cleaning up..."
    # Any cleanup tasks can go here
}

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --tag)
                CUSTOM_TAG="$2"
                shift 2
                ;;
            --build-only)
                BUILD_ONLY=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    trap cleanup EXIT
    
    log "Starting Docker build and push process..."
    
    # Run all checks and operations
    check_dependencies
    
    if [[ "$BUILD_ONLY" == "false" ]]; then
        authenticate_ghcr
    fi
    
    local tags
    tags=$(generate_tags)
    
    build_image "$tags"
    
    if [[ "$BUILD_ONLY" == "false" ]]; then
        test_image "$tags"
        
        echo
        success "Build and push completed successfully!"
        log "Images pushed to: $REGISTRY/$REPOSITORY"
        
        # Show the tags that were pushed
        IFS=',' read -ra tag_array <<< "$tags"
        for tag in "${tag_array[@]}"; do
            log "  $tag"
        done
        
        echo
        log "You can now pull and run your image with:"
        log "  docker run -p 8080:10000 -e PORT=10000 ${tag_array[0]}"
    fi
}

# Run main function with all arguments
main "$@"