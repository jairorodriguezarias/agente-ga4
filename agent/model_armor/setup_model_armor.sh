#!/bin/bash

# This script configures Vertex AI Model Armor integration.

# Exit immediately if a command exits with a non-zero status.
set -e

# Get the Google Cloud project ID and project number.
PROJECT_ID=$(grep GOOGLE_CLOUD_PROJECT .env | cut -d '=' -f2)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

if [ -z "$PROJECT_ID" ] || [ -z "$PROJECT_NUMBER" ]; then
  echo "Error: Could not retrieve PROJECT_ID or PROJECT_NUMBER. Make sure you are authenticated with gcloud and a project is set."
  exit 1
fi

echo "Project ID: $PROJECT_ID"
echo "Project Number: $PROJECT_NUMBER"

# --- 1. Grant Model Armor User permission to the Vertex AI service account ---
echo "\nGranting Model Armor User role to the Vertex AI service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-aiplatform.iam.gserviceaccount.com" \
    --role="roles/modelarmor.user"

echo "Permissions granted successfully."

# --- 2. Configure Model Armor Floor Settings ---
echo "\nConfiguring Model Armor floor settings for the project..."
curl -X PATCH \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -d '''{
      "filterConfig": {
        "rai_settings": {
          "rai_filters": [
            {"filter_type": "DANGEROUS", "confidence_level": "LOW_AND_ABOVE"},
            {"filter_type": "HARASSMENT", "confidence_level": "LOW_AND_ABOVE"},
            {"filter_type": "SEXUALLY_EXPLICIT", "confidence_level": "LOW_AND_ABOVE"},
            {"filter_type": "HATE_SPEECH", "confidence_level": "LOW_AND_ABOVE"}
          ]
        },
        "sdp_settings": {
          "basic_config": {
            "filter_enforcement": "ENABLED"
          }
        },
        "pi_and_jailbreak_filter_settings": {
          "filter_enforcement": "ENABLED",
          "confidence_level": "LOW_AND_ABOVE"
        },
        "malicious_uri_filter_settings": {
          "filter_enforcement": "ENABLED"
        }
      },
      "enableFloorSettingEnforcement": true,
      "integratedServices": "AI_PLATFORM",
      "aiPlatformFloorSetting": {
        "inspect_only":false,
        "enableCloudLogging": true
      }
    }''' \
    "https://modelarmor.googleapis.com/v1/projects/$PROJECT_ID/locations/global/floorSetting" 
echo "\n\nModel Armor has been configured for project $PROJECT_ID."
echo "All 'generateContent' API calls to Gemini models in this project will now be inspected."
echo "Results will be available in Cloud Logging."
