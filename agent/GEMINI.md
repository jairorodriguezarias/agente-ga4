# ADK Agent Project

This file describes the structure and usage of this ADK agent project, with specific information for the Gemini model.

## Project Structure

The project follows this structure:

```
agente_ga4/
├── venv/
├── agente_ga4/
│   ├── __init__.py
│   ├── agent.py
│   ├── config.py
│   ├── prompts.py
│   └── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
├── GEMINI.md
├── requirements.txt (moved to agente_ga4/requirements.txt)
├── setup_gcloud.sh
└── mcp_toolbox/
    ├── toolbox
    └── tools.yaml
```

## Getting Started (for Gemini)

To run the agent or perform development tasks:

1.  **Activate the virtual environment**:
    ```bash
    source venv/bin/activate
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r agente_ga4/requirements.txt
    ```

3.  **Authentication**:
    This project uses Application Default Credentials (ADC) for authentication with Google Cloud. Make sure you are logged in with:
    ```bash
    gcloud auth application-default login
    ```

4.  **Run the agent (locally)**:
    ```bash
    adk web --agent_path=agente_ga4/agent.py
    ```

## Toolbox Setup (for Gemini)

To use the tools for this agent, you need to download the `toolbox` executable and configure the MCP server:

1.  **Download the `toolbox` executable**:
    ```bash
    cd mcp_toolbox
    export VERSION=0.7.0
    curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/darwin/amd64/toolbox # For macOS
    # curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox # For Linux
    chmod +x toolbox
    cd ..
    ```

2.  **Configure the `tools` secret in Secret Manager**:
    ```bash
    gcloud secrets create tools --data-file=mcp_toolbox/tools.yaml # First time only
    gcloud secrets versions add tools --data-file=mcp_toolbox/tools.yaml # To update
    ```

3.  **Deploy the MCP server on Cloud Run**:
    ```bash
    export IMAGE=us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest
    gcloud run deploy toolbox \
        --image $IMAGE \
        --service-account toolbox-identity \
        --region us-central1 \
        --set-secrets "/app/tools.yaml=tools:latest" \
        --args="--tools-file=/app/tools.yaml","--address=0.0.0.0","--port=8080" \
        --allow-unauthenticated \
        --timeout=600
    ```

## Important Information (for Gemini)

-   **Google Cloud Project ID**: `YOUR_PROJECT_ID`
-   **Admin User**: `YOUR_ADMIN_USER_EMAIL`
-   **Authentication**: Uses Application Default Credentials (ADC) via `gcloud auth application-default login`. It is not necessary to use a `.env` file for credentials.
-   **Dependencies**: The main dependency is `google-adk`, installed with `pip install -r requirements.txt`.

## Additional Configuration (for Gemini)

### Fix for SSL Certificate Error on macOS

**Problem:** `aiohttp.client_exceptions.ClientConnectorCertificateError` with `[SSL: CERTIFICATE_VERIFY_FAILED]`.

**Solution:** The `venv/bin/activate` script has been modified to export `SSL_CERT_FILE` pointing to `certifi` certificates. It is activated automatically with `source venv/bin/activate`.

### BigQuery Permissions

**Problem:** `Error 403: Access Denied` related to `bigquery.jobs.create`.

**Solution:** Grant the `roles/bigquery.jobUser` role to the `toolbox-identity@YOUR_PROJECT_ID.iam.gserviceaccount.com` service account.
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member serviceAccount:toolbox-identity@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --role roles/bigquery.jobUser
```

## Deployment on Agent Engine (for Gemini)

To deploy the agent to Google Cloud Agent Engine:

1.  **Ensure the GCS bucket exists**:
    ```bash
    gcloud storage buckets create gs://YOUR_PROJECT_ID-agent-engine-bucket --project=YOUR_PROJECT_ID --location=us-central1
    ```

2.  **Deploy the agent to Agent Engine**:
    ```bash
    adk deploy agent_engine \
        --project=YOUR_PROJECT_ID \
        --region=us-central1 \
        --staging_bucket=gs://YOUR_PROJECT_ID-agent-engine-bucket \
        --display_name="Agente_Marketing"
    ```

## Publishing ADK Agents to Agentspace

This section is based on the document "Publishing agents built on ADK to Agentspace".

### Prerequisites

-   **Project on Allowlist**: Your Google Cloud project must be on the Agentspace allowlist.
-   **Cross-Project Registration**: If the agent (deployed in Project A) and Agentspace (in Project B) are in different projects, an additional *allowlisting* process is needed.
-   **Service Account Permissions**: The `service-PROJECTNUMBER@gcp-sa-discoveryengine.iam.gserviceaccount.com` service account needs the following roles:
    -   `Discovery Engine Service Agent`
    -   `Editor`
    -   `Vertex AI User`
    -   `Vertex AI Viewer`
    *(Note: To find this service account in IAM, make sure to check the "Include Google-provided role grants" box)*.

### 1. Deploy to Agent Engine

Make sure your `requirements.txt` contains `google-cloud-aiplatform[agent_engines,adk]`.

```bash
adk deploy agent_engine \
    --project=YOUR_PROJECT_ID \
    --region=us-central1 \
    --staging_bucket=gs://YOUR_DEPLOYMENT_BUCKET \
    --display_name="YOUR_AGENT_NAME"
```

#### Important notes on deployment:

-   The `adk deploy` command creates a **new** agent each time. There is currently no functionality to update an existing one (it is a pending feature request).
-   To **delete an agent**, you can use the Agent Engine UI in the Cloud Console or the [agent registration tool](https://github.com/VeerMuchandi/agent_registration_tool).
-   Currently, you cannot view **deployment logs** in real-time (also a pending feature request).
-   It is crucial to **note the `reasoning-engine id`** displayed at the end of the deployment to register the agent.

### 2. Test the Deployed Agent

You can use a Python script to verify that the agent works on Agent Engine.

```python
import vertexai
from vertexai.preview import reasoning_engines

# Initial Configuration
PROJECT_ID = "YOUR_PROJECT_ID"
LOCATION = "us-central1"
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Find the Reasoning Engine
engines = reasoning_engines.ReasoningEngine.list(
    filter='display_name="YOUR_AGENT_NAME"'
)

if not engines:
    print(f"Reasoning Engine with name YOUR_AGENT_NAME not found")
else:
    engine = engines[0]
    print(f"Reasoning Engine found: {engine.resource_name}")

    # Create a session
    session = engine.create_session()
    print(f"Session created: {session.name}")

    # Run the agent
    output = engine.agent_run(
        session_id=session.name.split('/')[-1],
        message="Type your prompt here"
    )
    print(f"Agent response: {output}")
```

### 3. Register in Agentspace (Alternative Method)

There is a CLI tool to simplify agent registration and management.

-   **Repository**: [https://github.com/VeerMuchandi/agent_registration_tool](https://github.com/VeerMuchandi/agent_registration_tool)
-   **Usage**:
    ```bash
    python as_registry_client.py --config config.txt
    ```
    The tool allows actions like `register_agent`, `update_agent`, `list_registry`, etc.

### Known Issues

-   **`Malformed Function Call` Error** (Bug ID: `b/409316706`): Can occur in long-running transactions and causes the agent to not execute completely.
-   **Output Formatting**: Sometimes, the agent's output format can be random and display raw markdown or HTML.