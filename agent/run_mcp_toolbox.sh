#!/bin/bash

# Set the project ID and other variables
PROJECT_ID="agentemarketing"
SERVICE_NAME="mcp-toolbox"
VERSION="0.13.0"
IMAGE="us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:${VERSION}"
ADC_FILE_HOST="${HOME}/.config/gcloud/application_default_credentials.json"
ADC_FILE_CONTAINER="/tmp/adc.json"

# Pull the Docker image
echo "Pulling the genai-toolbox container image..."
docker pull $IMAGE

# Run the Docker container
echo "Running the mcp-toolbox container..."
docker run --rm -p 8080:8080 \
    -v "$(pwd)/mcp_toolbox/tools.yaml:/tools.yaml" \
    -v "${ADC_FILE_HOST}:${ADC_FILE_CONTAINER}" \
    -e "GOOGLE_APPLICATION_CREDENTIALS=${ADC_FILE_CONTAINER}" \
    $IMAGE --tools-file /tools.yaml
