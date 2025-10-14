# GA4 Agent

This project is an agent created with the Google Agent Development Kit (ADK), specializing in the analysis of Google Analytics data.

## Table of Contents
- [Initial Setup](#initial-setup)
  - [Prerequisites](#prerequisites)
  - [Automated Setup with Script](#automated-setup-with-script)
  - [Manual Setup](#manual-setup)
- [Tool Description (`tools.yaml`)](#tool-description-toolsyaml)
- [Agent Usage](#agent-usage)
- [Agent Evaluation](#agent-evaluation)
- [Project Structure](#project-structure)
- [Troubleshooting Common Issues](#troubleshooting-common-issues)

---

## Initial Setup

### Prerequisites
Make sure you have installed:
- Python 3.11 or higher
- `gcloud CLI` (Google Cloud SDK)
- `docker` (if you plan to run the MCP server locally)

### Automated Setup with Script (`setup_gcloud.sh`)

The project includes a script to automate the initial Google Cloud setup.

**What does the script do?**
-   Sets the project ID in `gcloud`.
-   Enables the necessary APIs (Vertex AI, Cloud Run, Secret Manager).
-   Creates a service account (`agent-runner`) with the necessary permissions (`roles/vertexai.user`).
-   Creates and downloads a JSON key (`gcloud-sa-key.json`) for that service account.

**How to use it?**
```bash
bash setup_gcloud.sh YOUR_PROJECT_ID
```
After running, the script will instruct you on how to set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to use the generated JSON key, which is the recommended authentication method.

### Manual Setup & Technical Details

This section provides more details on the components and manual steps for developers.

#### Local Development

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

#### MCP/Toolbox Server Details

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

---

## Tool Description (`tools.yaml`)

The agent does not have SQL queries in its code. Instead, it uses tools defined in `mcp_toolbox/tools.yaml`. These tools are served by the MCP server.

The implemented tools are described below:

- **`get_daily_visits`**
  - **Description**: Gets a list of daily website visits from Google Analytics.
  - **Parameters**: None.

- **`get_daily_transactions_by_browser`**
  - **Description**: Returns the total number of transactions grouped by browser for a specific day.
  - **Parameters**: `TABLE_SUFFIX` (string, format `YYYYMMDD`).

- **`get_monthly_visits`**
  - **Description**: Returns the total number of unique visits for a specific month.
  - **Parameters**: `YEAR_MONTH` (string, format `YYYYMM`).

- **`get_monthly_transactions_by_browser`**
  - **Description**: Returns the total number of transactions grouped by browser for a specific month.
  - **Parameters**: `YEAR_MONTH` (string, format `YYYYMM`).

## Agent Usage

Once the local environment and the MCP server are configured, you can run the agent:

```bash
adk web --agent_path=agente_ga4/agent.py
```
Then, you can interact with the agent in your terminal.

## Agent Evaluation

This project includes a script to evaluate the agent's performance using a predefined evaluation set.

**How to run the evaluation?**

```bash
./evaluate_agent.sh --eval_dataset=agente_ga4/evaluation/basico.evalset.json
```

This will run the evaluation using the `basico.evalset.json` dataset and print the results to the console.

## Code Refactoring

For better organization and maintainability, the agent's code has been refactored:
- The `SYSTEM_PROMPT` has been moved to `agente_ga4/prompts.py`.
- The agent's configuration (model, name, description) has been moved to `agente_ga4/config.py`.
- The `agente_ga4/agent.py` file now imports these configurations and uses them to initialize the agent.

## Troubleshooting Common Issues

### SSL Certificate Error (macOS)

**Problem:** When running the agent on macOS, you might encounter an `aiohttp.client_exceptions.ClientConnectorCertificateError` stating `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate`. This occurs because the Python environment cannot find the system's root certificates.

**Solution:** This project's virtual environment has been configured to solve this problem automatically. The `venv/bin/activate` script has been modified to set the `SSL_CERT_FILE` environment variable to point to the certificates provided by the `certifi` package. This solution is activated automatically when using `source venv/bin/activate`.

### Error 404 (Toolset not found)

**Problem:** If the agent fails with a `RuntimeError` indicating `toolset`

### Import Error (`ModuleNotFoundError`)

**Problem:** When running a script like `python agente_ga4/deploy.py` from the project's root directory, you might encounter a `ModuleNotFoundError`, indicating that a package like `agente_ga4` cannot be found.

**Cause:** This happens because Python, by default, adds the script's directory (`agente_ga4/`) to its search path, instead of the current working directory (`agent/`). When the script tries to import `from agente_ga4...`, Python cannot find the package because it is not looking in the correct directory.

**Solution:** The solution implemented in `deploy.py` is to manually add the project's root directory to Python's search path at the beginning of the script. This ensures that the package's modules can always be found, regardless of how the script is executed.
```python
# deploy.py
import sys
import os

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ... rest of the script
```

### Unclosed Client Session Error (`Unclosed client session`)

**Problem:** After a script runs and finishes, errors like `Unclosed client session` or `Unclosed connector` may appear.

**Cause:** This happens because a network client (in this case, `ToolboxSyncClient`) opened connections but did not explicitly close them before the program terminated.

**Solution:** A `try...finally` block was implemented in `deploy.py` to ensure that the `toolbox.close()` method is always called at the end of execution. This releases network resources gracefully and eliminates the error messages.

```python
# deploy.py
from agente_ga4.agent import toolbox

try:
    # Main application logic
    ...
finally:
    # This block always executes at the end
    print("\nClosing the toolbox connection...")
    toolbox.close()
```

## Architecture

```
+----------------+      +-----------------------------+      +--------------------------------+
|      User      |----->|   ADK Agent (Agent Engine)  |----->|  Toolbox Server (Cloud Run)    |
+----------------+      +-----------------------------+      +--------------------------------+
                                                                           |
                                                                           |
                                          +--------------------------------+--------------------------------+
                                          |                                                                 |
                                          v                                                                 v
                               +---------------------+                                     +--------------------------+
                               |      BigQuery       |                                     |      Secret Manager      |
                               |   (Data Platform)   |                                     |  (stores tools.yaml)     |
                               +---------------------+                                     +--------------------------+
```

## Deployment on Agent Engine

To deploy the agent to Google Cloud Agent Engine, follow these steps. The configuration values (`project`, `region`, etc.) are taken from the `.env` file.

1.  **Ensure the GCS bucket exists:** Agent Engine needs a GCS bucket for staging. If it doesn't exist yet, create it with this command:
    ```bash
    gcloud storage buckets create gs://agentemarketing-agent-engine-bucket --project=agentemarketing --location=us-central1
    ```

2.  **Check dependencies:** Make sure your `agente_ga4/requirements.txt` file contains `google-adk` and `google-cloud-aiplatform[agent_engines]`.

3.  **Deploy the agent:** Run the following command in your terminal from the project's root directory.
    ```bash
    adk deploy agent_engine --project=agentemarketing --region=us-central1 --staging_bucket=gs://agentemarketing-agent-engine-bucket --display_name="Agente_Marketing" agente_ga4/
    ```
    This command will package your code, upload it to the staging bucket, create a container image, and deploy it to the managed Agent Engine service. The process can take several minutes.

## Security and Permissions Model

Access to Google Cloud resources, such as BigQuery, is managed through a robust authentication and authorization model. It is essential to understand how the agent interacts with these services securely.

### Agent Authentication

The agent uses **Application Default Credentials (ADC)** to authenticate with Google Cloud services. This means the agent authenticates as the identity that is logged into the `gcloud CLI` in your local environment (`gcloud auth application-default login`).

### Authorization for BigQuery (via MCP Server)

When the agent needs to access BigQuery, it does so through the **MCP Server (Toolbox)**. This server, when deployed on Cloud Run, uses its own **Service Account** for authorization.

-   **MCP Server Service Account**: `toolbox-identity@YOUR_PROJECT_ID.iam.gserviceaccount.com`
    This service account is the identity that the MCP server assumes to interact with Google Cloud services, including BigQuery.

-   **Required Permissions**: For the MCP server to be able to run queries in BigQuery, its service account (`toolbox-identity`) must have the appropriate IAM roles. The minimum role required to run BigQuery jobs is `roles/bigquery.jobUser`. This role includes the `bigquery.jobs.create` permission that was previously required to be granted.

    **Permissions Flow Diagram:**
    1.  **Local User** (`gcloud auth application-default login`)
    2.  **Local Agent** (authenticates as the local user via ADC)
    3.  **Call to MCP Server** (the agent communicates with the public URL of the MCP server)
    4.  **MCP Server on Cloud Run** (authenticates with its `toolbox-identity` Service Account)
    5.  **Access to BigQuery** (the `toolbox-identity` Service Account runs the query in BigQuery, provided it has the `roles/bigquery.queryUser` or `roles/bigquery.jobUser` role)

This model ensures that the local agent does not directly need BigQuery permissions, but instead delegates that responsibility to the MCP server, which operates with a more restricted and specific set of permissions for its function.