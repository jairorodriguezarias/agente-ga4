import logging
import asyncio
import os
from typing import Optional
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from toolbox_core import ToolboxSyncClient
from .prompts import SYSTEM_PROMPT
from .config import AGENT_CONFIG
from google.adk.tools.tool_context import ToolContext
from google.adk.models.lite_llm import LiteLlm # For multi-model support
from google.adk.runners import Runner
from google.genai import types # For creating message Content/Parts
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get the specific logger used by ADK.
adk_logger = logging.getLogger("google_adk")

# Set its level to DEBUG to ensure you capture ALL messages from the SDK,
# even if the general level is higher (like INFO).
adk_logger.setLevel(logging.DEBUG)

# Load environment variables
load_dotenv()

# Define the remote tool for the MCP server
TOOLBOX_URL = os.getenv("TOOLBOX_URL")
if not TOOLBOX_URL:
    raise ValueError("La variable de entorno TOOLBOX_URL no está configurada.")

toolbox = ToolboxSyncClient(TOOLBOX_URL)
tools = toolbox.load_toolset('my_bq_toolset')

# --- Session Management ---
# Key Concept: SessionService stores conversation history & state.

# InMemorySessionService is simple, non-persistent storage
session_service = InMemorySessionService()

generate_content_config_1=types.GenerateContentConfig(
        temperature=0.2, # More deterministic output
        max_output_tokens=1000,
    )

root_agent = Agent(
    model=AGENT_CONFIG['model'],
    name=AGENT_CONFIG['name'],
    description=AGENT_CONFIG['description'],
    instruction=SYSTEM_PROMPT,
    generate_content_config=generate_content_config_1,
    tools=tools,
 )