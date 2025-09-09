import asyncio
import os
import vertexai
from vertexai.preview import agent_engines
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# --- Configuration ---
# Ensures that environment variables are configured or uses default values
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "agentemarketing")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# The ID of the agent you deployed. You should update this if you deploy a new version.
AGENT_ENGINE_ID = "8433487281507008512"

async def main():
    """
    Main asynchronous function to connect to a deployed agent and test it.
    """
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # Get the deployed agent
    print(f"Connecting to agent: {AGENT_ENGINE_ID}...")
    try:
        remote_app = agent_engines.get(f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}")
    except Exception as e:
        print(f"Error: Could not find the deployed agent. Verify the ID.")
        print(f"Details: {e}")
        return
    
    # Create a session asynchronously
    print("Creating remote session...")
    remote_session = await remote_app.async_create_session(user_id="u_789")
    print(f"Session created: {remote_session.id}")

    # Send a query to the deployed agent
    print("Sending query...")
    query = "what is the total number of transactions for the Chrome browser in the month 202405?" # Example question
    print(f">> {query}")
    response_stream = remote_app.stream_query(
        session_id=remote_session.id,
        message=query
    )

    print("\n--- Remote Agent Response ---")
    for chunk in response_stream:
        if "text" in chunk.content.parts[0]:
            print(chunk.content.parts[0].text, end="")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
