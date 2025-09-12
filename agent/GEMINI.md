# ADK Agent Project (Gemini)

This file describes the structure and usage of this ADK agent project, with specific information for the Gemini model.

## Full Setup from Scratch

This guide will take you from a new Google Cloud project to a fully deployed Agent and MCP/Toolbox server.

### Step 1: Initial Google Cloud Project Setup

This step configures your Google Cloud project, enables necessary APIs, and creates a service account for the agent to run.

1.  **Navigate to the `agent` directory:**
    ```bash
    cd agent
    ```
2.  **Run the setup script:**
    Provide your Google Cloud Project ID as an argument.
    ```bash
    ./setup_gcloud.sh YOUR_PROJECT_ID
    ```
3.  **Configure Authentication:**
    The script will create a `gcloud-sa-key.json` file. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to it as instructed by the script output.

### Step 2: Deploy the MCP/Toolbox Server

This step deploys the MCP/Toolbox server, which the agent uses to execute tools.

1.  **Navigate to the project root directory.**
2.  **Run the deployment script:**
    Provide your Google Cloud Project ID as an argument.
    ```bash
    agent/setup_deploy.sh YOUR_PROJECT_ID
    ```
    This script handles the creation of the `toolbox-identity` service account, sets its permissions, and deploys the server to Cloud Run.

### Step 3: Deploy the Agent to Agent Engine

This final step deploys your agent code to the Agent Engine. It's recommended to do this from the project root.

1.  **Activate the virtual environment**:
    ```bash
    source agent/venv/bin/activate
    ```

2.  **Run the deployment command**:
    The following command will deploy the agent. It leverages the `.env` file inside the `agent` directory.
    ```bash
    cd agent && adk deploy agent_engine agente_ga4 --project=$(grep GOOGLE_CLOUD_PROJECT .env | cut -d '=' -f2) --region=$(grep GOOGLE_CLOUD_LOCATION .env | cut -d '=' -f2) --staging_bucket=gs://$(grep GOOGLE_CLOUD_PROJECT .env | cut -d '=' -f2)-agent-engine-bucket --display_name=$(grep AGENT_DISPLAY_NAME .env | cut -d '=' -f2)
    ```

3.  **Save the Resource Name**:
    After a successful deployment, add the output `Resource name` to your `agent/.env` file:
    ```
    AGENT_ENGINE_RESOURCE_NAME=projects/your-project-number/locations/us-central1/reasoningEngines/your-engine-id
    ```

---

## Manual Setup & Technical Details

This section provides more details on the components and manual steps for developers.

### Local Development

To run the agent locally for development or testing:

1.  **Activate the virtual environment**:
    ```bash
    source venv/bin/activate
    ```
2.  **Install dependencies**:
    ```bash
    pip install -r agente_ga4/requirements.txt
    ```
3.  **Authentication**:
    Ensure you are authenticated. For a new project, follow Step 1.3 from the "Full Setup" guide. For existing setups, ensure `gcloud auth application-default login` is active or `GOOGLE_APPLICATION_CREDENTIALS` is set.
4.  **Run the agent (locally)**:
    ```bash
    adk web --agent_path=agente_ga4/agent.py
    ```

### MCP/Toolbox Server Details

The `setup_deploy.sh` script automates the MCP setup. This section provides details on what the script does.

**Important:** The `agent/mcp_toolbox/tools.yaml` file has a hardcoded BigQuery project ID (`agentemarketing`). You must change this to your own project ID before deploying.

1.  **`toolbox-identity` Service Account:** A dedicated service account is created for the MCP server.
2.  **Permissions:** The service account is granted the following roles:
    *   `roles/secretmanager.secretAccessor`: To read the `tools.yaml` configuration from Secret Manager.
    *   `roles/cloudsql.client`: To connect to Cloud SQL databases.
    *   `roles/bigquery.jobUser`: To run BigQuery jobs.
3.  **Secret Configuration:** The `mcp_toolbox/tools.yaml` file is uploaded to Secret Manager as a secret named `tools`.
4.  **Cloud Run Deployment:** The public `toolbox` image (`us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest`) is deployed to Cloud Run, configured to use the `toolbox-identity` service account and the `tools` secret.

### Additional Configuration

#### Fix for SSL Certificate Error on macOS

**Problem:** `aiohttp.client_exceptions.ClientConnectorCertificateError` with `[SSL: CERTIFICATE_VERIFY_FAILED]`.

**Solution:** The `venv/bin/activate` script has been modified to export `SSL_CERT_FILE` pointing to `certifi` certificates. It is activated automatically with `source venv/bin/activate`.

#### BigQuery Permissions

The `setup_deploy.sh` script already grants the `roles/bigquery.jobUser` to the `toolbox-identity` service account. This section is for reference.

**Problem:** `Error 403: Access Denied` related to `bigquery.jobs.create`.

**Solution:** Ensure the `toolbox-identity@YOUR_PROJECT_ID.iam.gserviceaccount.com` service account has the `roles/bigquery.jobUser` role.
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member serviceAccount:toolbox-identity@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --role roles/bigquery.jobUser
```
```