#!/bin/bash
#
# Updated script to safely start the crawling_assignment 1.2 server.
#
# - Automatically loads crawling_assignment-1.2-amd64.tar if image not found.
# - Verifies checksum.
# - Runs container with required security flags & data volume.
# - Reuses running/stopped containers named 'crawling_server'.
#

set -e  # Exit on any error

# --- Configuration ---
CONTAINER_NAME="crawling_server"
IMAGE_NAME="crawling_assignment:1.2"
TAR_FILE="crawling_assignment-1.2-amd64.tar"
CHECKSUM_FILE="${TAR_FILE}.sha256"

# Make sure the data folder exists
mkdir -p data
chmod 777 data

echo "=== Starting Crawling Assignment Server (v1.2) ==="

# 1. Check if container is already running
if [ "$(docker ps -f "name=^/${CONTAINER_NAME}$" --format '{{.Names}}')" == "${CONTAINER_NAME}" ]; then
    echo "Container '${CONTAINER_NAME}' is already running."
    exit 0
fi

# 2. If container exists but is stopped → start it
if [ "$(docker ps -a -f "name=^/${CONTAINER_NAME}$" --format '{{.Names}}')" == "${CONTAINER_NAME}" ]; then
    echo "Container '${CONTAINER_NAME}' exists but is stopped. Starting..."
    docker start "${CONTAINER_NAME}"
    exit 0
fi

# 3. No container exists → check if image exists
if [ -z "$(docker images -q ${IMAGE_NAME})" ]; then
    echo "Image '${IMAGE_NAME}' not found."

    # Ensure tar file exists
    if [ ! -f "${TAR_FILE}" ]; then
        echo "ERROR: ${TAR_FILE} not found. Cannot load Docker image."
        exit 1
    fi

    # Verify checksum if available
    if [ -f "${CHECKSUM_FILE}" ]; then
        echo "Verifying image checksum..."
        sha256sum -c "${CHECKSUM_FILE}"
    else
        echo "WARNING: ${CHECKSUM_FILE} missing. Skipping checksum verification."
    fi

    # Load image
    echo "Loading image from ${TAR_FILE}..."
    docker load -i "${TAR_FILE}"
fi

# 4. Run new container
echo "Running a new container '${CONTAINER_NAME}'..."

docker run -d \
  --name "${CONTAINER_NAME}" \
  --rm \
  -p 3000:3000 \
  -v "$(pwd)/data:/data" \
  --tmpfs /tmp:rw,noexec,nosuid \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --pids-limit 128 \
  --memory 256m \
  "${IMAGE_NAME}"

echo "Container '${CONTAINER_NAME}' started successfully!"
echo "Server running at: http://localhost:3000"