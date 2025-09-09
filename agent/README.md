# GA4 Agent

This project is an agent created with the Google Agent Development Kit (ADK), specializing in the analysis of Google Analytics data.

## Table of Contents
- [Initial Setup](#initial-setup)
  - [Prerequisites](#prerequisites)
  - [Automated Setup with Script](#automated-setup-with-script)
  - [Manual Setup](#manual-setup)
- [Tool Description (`tools.yaml`)](#tool-description-toolsyaml)
- [Agent Usage](#agent-usage)
- [Agent Evaluation with ADK](#agent-evaluation-with-adk)
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

### Local Environment Setup

1.  **Activate the virtual environment**:
    ```bash
    source venv/bin/activate
    ```
    *Note: If the virtual environment does not exist or is corrupted, it will be created automatically with Python 3.11.6 when installing dependencies.*

2.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Authenticate with Google Cloud**:
    Make sure you are logged in with your Application Default Credentials (ADC). This is crucial for the agent and tools to interact with Google Cloud services.
    ```bash
    gcloud auth application-default login
    ```

### Google Cloud Setup

1.  **Enable Google Cloud services**:
    Make sure the following services are enabled in your Google Cloud project (`YOUR_PROJECT_ID`):
    ```bash
    gcloud services enable cloudresourcemanager.googleapis.com \
                           servicenetworking.googleapis.com \
                           run.googleapis.com \
                           cloudbuild.googleapis.com \
                           cloudfunctions.googleapis.com \
                           aiplatform.googleapis.com \
                           sqladmin.googleapis.com \
                           compute.googleapis.com
    ```

2.  **Configure BigQuery permissions**:
    If you get an `Access Denied` error related to `bigquery.jobs.create` when running the agent, it means the `toolbox-identity` service account does not have the necessary permissions to interact with BigQuery.
    **Solution:** Grant the `roles/bigquery.jobUser` role to the `toolbox-identity@YOUR_PROJECT_ID.iam.gserviceaccount.com` service account in your project.
    ```bash
    gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
        --member serviceAccount:toolbox-identity@YOUR_PROJECT_ID.iam.gserviceaccount.com \
        --role roles/bigquery.jobUser
    ```

### MCP Server (Toolbox) Setup

The agent uses a tool server (MCP Toolbox) to interact with BigQuery. This server can be run locally or deployed on Cloud Run.

For a detailed example of MCP setup for BigQuery, you can consult the [official quickstart guide](https://googleapis.github.io/genai-toolbox/samples/bigquery/mcp_quickstart/).

1.  **Download the `toolbox` executable**:
    **Note:** The following command is for `darwin` systems (macOS). If you use a different operating system, please adjust the download URL to your architecture.
    ```bash
    cd mcp_toolbox
    export VERSION=0.7.0
    # For darwin systems (macOS)
    curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/darwin/amd64/toolbox
    # For linux systems
    # curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox
    chmod +x toolbox
    cd .. # Return to the project root directory
    ```

2.  **Configure `tools.yaml`**:
    The `mcp_toolbox/tools.yaml` file defines the tools available to the MCP server. Ensure that the configuration of the tools and `toolsets` is correct.
    *   The initial query for `search_release_notes_bq` was changed to a `daily_visits` query from Google Analytics.
    *   The tool name and its description were updated to reflect this change (`get_daily_visits`).

3.  **Update the `tools` secret in Secret Manager**:
    If you have modified `mcp_toolbox/tools.yaml` and the MCP server is deployed on Cloud Run, you need to update the secret in Secret Manager for the changes to take effect.
    ```bash
    gcloud secrets versions add tools --data-file="mcp_toolbox/tools.yaml"
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

## Agent Evaluation with ADK

The project uses "evalsets" to perform regression testing and ensure the agent behaves as expected.

- **What is an `evalset`?**: It is a JSON file containing one or more sample conversations, each with a user input and the ideal response the agent should produce.
- **Existing files**:
    - `basico.evalset.json`: Contains general questions to validate the agent's personality and basic capabilities.
    - `transacciones_mensuales.evalset.json`: Contains specific tests for the monthly transactions tool.

**How to run the evaluation?**

```bash
# Run the basic test set
adk eval --agent_path=agente_ga4/agent.py --eval_set_path=agente_ga4/basico.evalset.json
```

**How to create a new `evalset`?**
The easiest way is to interact with the agent via `adk web` and, once a satisfactory conversation is obtained, save it as a new JSON `evalset` file for future tests.

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