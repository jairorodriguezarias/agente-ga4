#!/bin/bash

# WARNING: This script is not guaranteed to work.
# It is based on a series of trial-and-error steps and the available documentation,
# but the registration process has been unreliable.

# Get an access token
TOKEN=$(gcloud auth print-access-token)

# Register the agent with Agentspace
curl -X PATCH \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-H "x-goog-user-project: agent-space-469714" \
"https://discoveryengine.googleapis.com/v1alpha/projects/323290918249/locations/global/collections/default_collection/engines/gemini-enterprise-17600951_1760095106457/assistants/default_assistant?updateMask=agent_configs" -d '{
    "name": "projects/323290918249/locations/global/collections/default_collection/engines/gemini-enterprise-17600951_1760095106457/assistants/default_assistant",
    "displayName": "Default Assistant",
    "agentConfigs": [{
      "displayName": "agente_ga4",
      "vertexAiSdkAgentConnectionInfo": {
        "reasoningEngine": "projects/agent-space-469714/locations/us-central1/reasoningEngines/7530533148405268480"
      },
      "toolDescription": "Agente GA4",
      "icon": {
        "uri": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/corporate_fare/default/24px.svg"
      },
      "id": "agente_ga4_agent"
    }]
  }'
