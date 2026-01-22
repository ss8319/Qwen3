#!/usr/bin/env bash
#
# Build script for Qwen3 Docker environment
# Usage: ./docker/build.sh [OPTIONS]

set -e

IMAGE_NAME="qwen3:latest"
VLLM_IMAGE_NAME="qwen3-vllm:latest"
DOCKERFILE_PATH="docker/Dockerfile"
BUILD_CONTEXT="."

function usage() {
    echo '
Usage: bash docker/build.sh [OPTIONS]

Options:
    -i, --image-name IMAGE_NAME       Base image name (default: qwen3:latest)
    -v, --vllm-image IMAGE_NAME       vLLM image name (default: qwen3-vllm:latest)
    -t, --tag TAG                     Tag for images (default: latest)
    --base-only                       Build only base image (no vLLM)
    --vllm-only                       Build only vLLM image (requires base image)
    --no-cache                        Build without cache
    -h, --help                        Show this help message

Examples:
    # Build both base and vLLM images (default)
    bash docker/build.sh

    # Build only base image (no vLLM)
    bash docker/build.sh --base-only

    # Build only vLLM image (assumes base exists)
    bash docker/build.sh --vllm-only

    # Build with custom tag
    bash docker/build.sh -t v1.0

    # Build without cache
    bash docker/build.sh --no-cache
'
}

TAG="latest"
NO_CACHE=""
BUILD_MODE="both"  # Options: both, base-only, vllm-only

while [[ "$1" != "" ]]; do
    case $1 in
        -i | --image-name )
            shift
            IMAGE_NAME=$1
            ;;
        -v | --vllm-image )
            shift
            VLLM_IMAGE_NAME=$1
            ;;
        -t | --tag )
            shift
            TAG=$1
            IMAGE_NAME="qwen3:${TAG}"
            VLLM_IMAGE_NAME="qwen3-vllm:${TAG}"
            ;;
        --base-only )
            BUILD_MODE="base-only"
            ;;
        --vllm-only )
            BUILD_MODE="vllm-only"
            ;;
        --no-cache )
            NO_CACHE="--no-cache"
            ;;
        -h | --help )
            usage
            exit 0
            ;;
        * )
            echo "Unknown argument: $1"
            usage
            exit 1
            ;;
    esac
    shift
done

echo "Building Qwen3 Docker images..."
echo "Build mode: ${BUILD_MODE}"
echo "Base image: ${IMAGE_NAME}"
echo "vLLM image: ${VLLM_IMAGE_NAME}"
echo ""

# Build base image if needed
if [[ "$BUILD_MODE" == "both" || "$BUILD_MODE" == "base-only" ]]; then
    echo "Step 1: Building base Qwen3 image..."
    docker build ${NO_CACHE} \
        --target final-base \
        -t ${IMAGE_NAME} \
        -f ${DOCKERFILE_PATH} \
        ${BUILD_CONTEXT} || {
        echo "Failed to build base image"
        exit 1
    }
    echo "✓ Base image built successfully: ${IMAGE_NAME}"
fi

# Build vLLM image if needed
if [[ "$BUILD_MODE" == "both" || "$BUILD_MODE" == "vllm-only" ]]; then
    if [[ "$BUILD_MODE" == "vllm-only" ]]; then
        echo "Step 1: Building vLLM-enabled Qwen3 image (using existing base)..."
    else
        echo ""
        echo "Step 2: Building vLLM-enabled Qwen3 image..."
    fi
    
    docker build ${NO_CACHE} \
        --target final \
        -t ${VLLM_IMAGE_NAME} \
        -f ${DOCKERFILE_PATH} \
        ${BUILD_CONTEXT} || {
        echo "Failed to build vLLM image"
        if [[ "$BUILD_MODE" == "vllm-only" ]]; then
            echo "Note: Make sure base image ${IMAGE_NAME} exists. Build it with --base-only first."
        fi
        exit 1
    }
    echo "✓ vLLM image built successfully: ${VLLM_IMAGE_NAME}"
fi

echo ""
echo "✓ Build complete!"
echo ""
echo "Available images:"
if [[ "$BUILD_MODE" == "both" || "$BUILD_MODE" == "base-only" ]]; then
    echo "  - ${IMAGE_NAME} (base environment)"
fi
if [[ "$BUILD_MODE" == "both" || "$BUILD_MODE" == "vllm-only" ]]; then
    echo "  - ${VLLM_IMAGE_NAME} (with vLLM support)"
fi
echo ""
if [[ "$BUILD_MODE" == "both" || "$BUILD_MODE" == "vllm-only" ]]; then
    echo "To run the container:"
    echo "  docker run --gpus all -it --rm ${VLLM_IMAGE_NAME}"
elif [[ "$BUILD_MODE" == "base-only" ]]; then
    echo "To run the container:"
    echo "  docker run --gpus all -it --rm ${IMAGE_NAME}"
fi

