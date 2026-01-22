#!/usr/bin/env bash
#
# Quick run script for Qwen3 Docker container
# Usage: ./docker/run.sh [OPTIONS]

set -e

IMAGE_NAME="qwen3-vllm:latest"
CONTAINER_NAME="qwen3-container"
WORKSPACE="/raid/scratch/shamus/Qwen3"

function usage() {
    echo '
Usage: bash docker/run.sh [OPTIONS]

Options:
    -i, --image IMAGE_NAME          Docker image name (default: qwen3-vllm:latest)
    -n, --name CONTAINER_NAME       Container name (default: qwen3-container)
    -w, --workspace PATH            Workspace path to mount (default: current dir)
    -p, --port PORT                 Port to expose (default: 8000)
    -d, --detach                    Run in detached mode
    --bash                          Start bash shell (default)
    --vllm MODEL                    Start vLLM server with model
    -h, --help                      Show this help message

Examples:
    # Interactive bash shell
    bash docker/run.sh

    # Start vLLM server
    bash docker/run.sh --vllm Qwen/Qwen3-8B

    # Run in detached mode
    bash docker/run.sh -d --vllm Qwen/Qwen3-8B
'
}

PORT=8000
DETACH=""
VLLM_MODEL=""
CMD="/bin/bash"

while [[ "$1" != "" ]]; do
    case $1 in
        -i | --image )
            shift
            IMAGE_NAME=$1
            ;;
        -n | --name )
            shift
            CONTAINER_NAME=$1
            ;;
        -w | --workspace )
            shift
            WORKSPACE=$1
            ;;
        -p | --port )
            shift
            PORT=$1
            ;;
        -d | --detach )
            DETACH="-d"
            ;;
        --bash )
            CMD="/bin/bash"
            ;;
        --vllm )
            shift
            VLLM_MODEL=$1
            CMD="vllm serve ${VLLM_MODEL} --port 8000 --host 0.0.0.0"
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

# Use current directory if workspace not specified
if [ "$WORKSPACE" = "/raid/scratch/shamus/Qwen3" ] && [ ! -d "$WORKSPACE" ]; then
    WORKSPACE=$(pwd)
fi

echo "Starting container..."
echo "  Image: ${IMAGE_NAME}"
echo "  Container: ${CONTAINER_NAME}"
echo "  Workspace: ${WORKSPACE}"
echo "  Port: ${PORT}"
echo ""

# Build docker run command
# Add -it for interactive mode unless running detached
INTERACTIVE_FLAGS=""
if [ -z "$DETACH" ]; then
    INTERACTIVE_FLAGS="-it"
fi

DOCKER_CMD="docker run --gpus all ${INTERACTIVE_FLAGS} ${DETACH} --name ${CONTAINER_NAME} --rm"
DOCKER_CMD="${DOCKER_CMD} -v ${WORKSPACE}:/workspace"
DOCKER_CMD="${DOCKER_CMD} -p ${PORT}:8000"
DOCKER_CMD="${DOCKER_CMD} ${IMAGE_NAME} ${CMD}"

echo "Running: ${DOCKER_CMD}"
echo ""

eval ${DOCKER_CMD}

if [ -z "$DETACH" ]; then
    echo ""
    echo "Container exited."
else
    echo ""
    echo "Container started in detached mode."
    echo "View logs: docker logs ${CONTAINER_NAME}"
    echo "Stop container: docker stop ${CONTAINER_NAME}"
fi

