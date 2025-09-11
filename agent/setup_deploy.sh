#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Check if PROJECT_ID is set
if [ -z "$1" ]; then
    echo "Usage: $0 <PROJECT_ID>"
    exit 1
fi

PROJECT_ID=$1

echo "--- Starting MCP/Toolbox Server Setup for project: $PROJECT_ID ---"

# 1. Create the toolbox-identity service account
SERVICE_ACCOUNT_EMAIL="toolbox-identity@$PROJECT_ID.iam.gserviceaccount.com"
echo "Checking for existing service account 'toolbox-identity'"...
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "Service account 'toolbox-identity' already exists."
else
    echo "Creating service account 'toolbox-identity'"...
    gcloud iam service-accounts create toolbox-identity --project=$PROJECT_ID --display-name="Toolbox Identity"
fi

# Add a delay to allow for propagation
echo "Waiting for 10 seconds for the service account to propagate..."
sleep 10

# 2. Grant IAM roles to the service account
echo "Granting IAM roles to 'toolbox-identity'"...
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:toolbox-identity@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:toolbox-identity@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:toolbox-identity@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"

# 3. Create the 'tools' secret in Secret Manager
# This assumes a file named 'mcp_toolbox/tools.yaml' exists in the current directory.

echo "Creating 'tools' secret from 'mcp_toolbox/tools.yaml'"...
if [ -f "mcp_toolbox/tools.yaml" ]; then
    if gcloud secrets describe tools --project=$PROJECT_ID > /dev/null 2>&1; then
        echo "Secret 'tools' already exists. Adding a new version."
        gcloud secrets versions add tools --data-file=mcp_toolbox/tools.yaml --project=$PROJECT_ID
    else
        echo "Creating new secret 'tools'."
        gcloud secrets create tools --data-file=mcp_toolbox/tools.yaml --project=$PROJECT_ID
    fi
else
    echo "Warning: mcp_toolbox/tools.yaml not found. Skipping secret creation."
    echo "Please create the secret manually."
fi

# 4. Deploy the MCP server to Cloud Run
echo "Deploying MCP server to Cloud Run"...
IMAGE=us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest
gcloud run deploy toolbox \
    --image=$IMAGE \
    --service-account="toolbox-identity@$PROJECT_ID.iam.gserviceaccount.com" \
    --region=us-central1 \
    --set-secrets="/app/tools.yaml=tools:latest" \
    --args="--tools-file=/app/tools.yaml,--address=0.0.0.0,--port=8080" \
    --allow-unauthenticated \
    --timeout=600 \
    --project=$PROJECT_ID

echo "--- MCP/Toolbox Server Setup Finished ---"

# Deploy the Agent to Agent Engine
echo "--- Deploying the Agent to Agent Engine ---"
echo "This step can take several minutes."
cd agent && source venv/bin/activate && adk deploy agent_engine agente_ga4 --project=$(grep GOOGLE_CLOUD_PROJECT .env | cut -d '=' -f2) --region=$(grep GOOGLE_CLOUD_LOCATION .env | cut -d '=' -f2) --staging_bucket=gs://$(grep GOOGLE_CLOUD_PROJECT .env | cut -d '=' -f2)-agent-engine-bucket --display_name=$(grep AGENT_DISPLAY_NAME .env | cut -d '=' -f2)