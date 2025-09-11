
#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Set the project ID from the argument or use the default
PROJECT_ID="${1:-YOUR_PROJECT_ID}"

echo "Configuring Google Cloud project: $PROJECT_ID"

# Set the project ID for gcloud
gcloud config set project $PROJECT_ID

# Enable the required APIs
echo "Enabling APIs (Vertex AI, Cloud Run, Secret Manager)..."
gcloud services enable aiplatform.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com

# Create a service account
SERVICE_ACCOUNT_NAME="agent-runner"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Checking for existing service account..."
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL >/dev/null 2>&1; then
    echo "Service account '$SERVICE_ACCOUNT_NAME' already exists."
else
    echo "Creating service account '$SERVICE_ACCOUNT_NAME'..."
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="Agent Runner"
fi

# Grant permissions to the service account
echo "Granting Vertex AI User role to the service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/aiplatform.user"

# Authentication for local development
echo "Service account key creation is disabled in your organization."
echo "For local development, you will use Application Default Credentials (ADC) with your own user account."
echo "Please run 'gcloud auth application-default login' after this script completes."

# Create an API key as an alternative
echo "Creating an API key as an alternative..."
# The command to create an API key is `gcloud alpha services api-keys create`
# but it's an alpha command and might not be available or could change.
# Instead, we will just provide the instruction to the user.
echo "To create an API key, go to the Google Cloud Console:"
echo "https://console.cloud.google.com/apis/credentials"
echo "Then, you can add the key to your .env file:"
echo "GOOGLE_API_KEY=\"your_api_key\""

echo "Configuration script finished."
