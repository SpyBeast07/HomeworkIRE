#!/bin/bash
#
# A script to safely start the crawling_assignment container.
#
# 1. If 'crawling_server' is running, does nothing.
# 2. If 'crawling_server' is stopped, starts it.
# 3. If 'crawling_server' doesn't exist, it checks for the image.
# 4. If the image is missing, it loads it from the .tar file.
# 5. Finally, it runs a new container.
#

set -e # Exit immediately if any command fails

# --- Configuration ---
CONTAINER_NAME="crawling_server"
IMAGE_NAME="crawling_assignment:1.0"
TAR_FILE="crawling_assignment-1.0-amd64.tar"
CHECKSUM_FILE="${TAR_FILE}.sha256"

# 1. Check if container is running
if [ "$(docker ps -f "name=^/${CONTAINER_NAME}$" --format '{{.Names}}')" == "${CONTAINER_NAME}" ]; then
    echo "Container '${CONTAINER_NAME}' is already running."
    exit 0
fi

# 2. Check if container is stopped (but exists)
if [ "$(docker ps -a -f "name=^/${CONTAINER_NAME}$" --format '{{.Names}}')" == "${CONTAINER_NAME}" ]; then
    echo "Container '${CONTAINER_NAME}' is stopped. Starting..."
    docker start "${CONTAINER_NAME}"
    exit 0
fi

# 3. Container doesn't exist. Check for the image.
if [ -z "$(docker images -q ${IMAGE_NAME})" ]; then
    echo "Image '${IMAGE_NAME}' not found."
    
    if [ ! -f "${TAR_FILE}" ]; then
        echo "Error: ${TAR_FILE} not found. Cannot load image." >&2
        exit 1
    fi

    # 4. Verify and load the image
    if [ -f "${CHECKSUM_FILE}" ]; then
        echo "Verifying image from ${CHECKSUM_FILE}..."
        sha256sum -c "${CHECKSUM_FILE}"
    else
        echo "Warning: ${CHECKSUM_FILE} not found. Skipping verification."
    fi
    
    echo "Loading image from ${TAR_FILE}..."
    docker load -i "${TAR_FILE}"
fi

# 5. Image exists, container doesn't. Run a new one.
echo "Starting new container '${CONTAINER_NAME}'..."
docker run -d --name "${CONTAINER_NAME}" \
  -p 3000:3000 \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --pids-limit 128 \
  --memory 256m \
  "${IMAGE_NAME}"

echo "Container started successfully."