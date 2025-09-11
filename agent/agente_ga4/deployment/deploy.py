import sys
import os

# Agrega el directorio raíz del proyecto a sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import vertexai
from agente_ga4.agent import root_agent, toolbox # 1. Importar toolbox
from dotenv import load_dotenv

load_dotenv()  # Carga las variables de entorno desde el archivo .env

# TODO: Fill in these values for your project
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")  # For other options, see https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview#supported-regions

if not PROJECT_ID:
    raise ValueError("La variable de entorno GOOGLE_CLOUD_PROJECT no está configurada.")

STAGING_BUCKET = f"gs://{PROJECT_ID}-agent-engine-bucket"

# Initialize the Vertex AI SDK
vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)
from vertexai.preview import reasoning_engines

# Wrap the agent in an AdkApp object
app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

# Create a local session to maintain conversation history
session = app.create_session(user_id="u_123")
print(session)

events = list(app.stream_query(
    user_id="u_123",
    session_id=session.id,
    message="whats the weather in new york",
))

# The full event stream shows the agent's thought process
print("--- Full Event Stream ---")
for event in events:
    print(event)

# For quick tests, you can extract just the final text response
final_text_responses = [
    e for e in events
    if e.get("content", {}).get("parts", [{}])[0].get("text")
    and not e.get("content", {}).get("parts", [{}])[0].get("function_call")
]
if final_text_responses:
    print("\n--- Final Response ---")
    print(final_text_responses[0]["content"]["parts"][0]["text"])


from vertexai import agent_engines

remote_app = agent_engines.create(
    agent_engine=app,
    requirements=[
        "google-cloud-aiplatform[adk,agent_engines]"   
    ]
)

print(f"Deployment finished!")
print(f"Resource Name: {remote_app.resource_name}")
# Resource Name: "projects/{PROJECT_NUMBER}/locations/{LOCATION}/reasoningEngines/{RESOURCE_ID}"


