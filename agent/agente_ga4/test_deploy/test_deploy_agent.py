import os
import sys
import json
import vertexai
from vertexai.preview import reasoning_engines
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Loads configuration from environment variables for greater flexibility
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "agentspace-demo-1145-b")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
AGENT_NAME = os.getenv("AGENT_DISPLAY_NAME", "Corporate Analyst")
SESSION_ID = "test-session-01"

def main():
    """
    Main script to find an agent, create/get a session, and execute a query.
    """
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # --- 1. Find the Reasoning Engine ---
    print(f"Searching for agent with name: '{AGENT_NAME}'...")
    engines = reasoning_engines.ReasoningEngine.list(filter=f'display_name="{AGENT_NAME}"')

    if not engines:
        print(f"Error: No agent found with the name '{AGENT_NAME}'.")
        sys.exit(1)

    engine = engines[0]
    print(f"Agent found: {engine.resource_name}")

    # --- 2. Get or Create the Session ---
    # This logic is more robust: it tries to get the session, and if it doesn't exist, it creates it.
    try:
        print(f"Attempting to get session: '{SESSION_ID}'...")
        session = engine.get_session(session_id=SESSION_ID)
        print("Existing session found.")
    except Exception:
        print("Session not found. Creating a new one...")
        session = engine.create_session(session_id=SESSION_ID)
        print("New session created.")
    
    print(f"Session ID: {session.id}")

    # --- 3. Execute the Agent ---
    print("\nSending query to the agent...")
    prompt_text = "AAPL"
    print(f">> {prompt_text}")

    output = engine.agent_run(
        session_id=SESSION_ID,
        message=types.Content(
            parts=[types.Part(text=prompt_text)],
            role="user",
        ).model_dump_json(),
    )

    print("\n--- Agent Response ---")
    print(output)

if __name__ == "__main__":
    main()
