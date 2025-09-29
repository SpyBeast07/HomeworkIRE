# Start docker container for Elasticsearch
# Check if container is running, if not start it
# If container does not exist, create and start it
import subprocess
import time
import requests

CONTAINER_NAME = "es-container"
IMAGE_NAME = "docker.elastic.co/elasticsearch/elasticsearch:8.15.0"
ES_PORT = 9200

def run_command(cmd):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error running command '{cmd}': {e}")
        return None

def container_exists(name):
    """Check if a container with given name exists."""
    output = run_command(f"docker ps -a --filter 'name={name}' --format '{{{{.Names}}}}'")
    return name in output.splitlines()

def container_running(name):
    """Check if the container is currently running."""
    output = run_command(f"docker ps --filter 'name={name}' --format '{{{{.Names}}}}'")
    return name in output.splitlines()

def start_container():
    """Start Elasticsearch container if not exists, else restart it."""
    if container_exists(CONTAINER_NAME):
        if container_running(CONTAINER_NAME):
            print(f"{CONTAINER_NAME} is already running. Restarting...")
            run_command(f"docker restart {CONTAINER_NAME}")
        else:
            print(f"{CONTAINER_NAME} exists but is stopped. Starting...")
            run_command(f"docker start {CONTAINER_NAME}")
    else:
        print(f"{CONTAINER_NAME} does not exist. Creating and starting container...")
        run_command(
            f"docker run -d --name {CONTAINER_NAME} "
            f"-p {ES_PORT}:{ES_PORT} "
            f"-e 'discovery.type=single-node' "
            f"-e 'xpack.security.enabled=false' "
            f"{IMAGE_NAME}"
        )

def check_status():
    """Print container status and test if Elasticsearch is responding."""
    if container_running(CONTAINER_NAME):
        print(f"{CONTAINER_NAME} is running ✅")
    else:
        print(f"{CONTAINER_NAME} is NOT running ❌")
        return

    # Wait a few seconds for ES to start
    time.sleep(5)

    try:
        response = requests.get(f"http://localhost:{ES_PORT}", verify=False, timeout=5)
        if response.status_code == 200:
            print("Elasticsearch is responding at http://localhost:9200 ✅")
        else:
            print(f"Elasticsearch responded with status code: {response.status_code} ❌")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to Elasticsearch: {e} ❌")

def wait_for_es(port=9200, retries=10, delay=3):
    """Wait until Elasticsearch is ready."""
    url = f"http://localhost:{port}"
    for i in range(retries):
        try:
            response = requests.get(url, verify=False, timeout=5)
            if response.status_code == 200:
                print("Elasticsearch is responding ✅")
                return True
        except requests.exceptions.RequestException:
            print(f"Waiting for Elasticsearch... ({i+1}/{retries})")
            time.sleep(delay)
    print("Failed to connect to Elasticsearch after retries ❌")
    return False

if __name__ == "__main__":
    start_container()
    wait_for_es()
    check_status()


# # To start the container manually, run:
# # Start Elasticsearch:
# docker run -d \
#   --name es-container \
#   -p 9200:9200 \
#   -e "discovery.type=single-node" \
#   -e "xpack.security.enabled=false" \
#   docker.elastic.co/elasticsearch/elasticsearch:8.15.0

# # Check:
# docker ps

# # Test:
# curl -k http://localhost:9200
