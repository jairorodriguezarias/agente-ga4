import logging
from google.adk.agents import Agent
from toolbox_core import ToolboxSyncClient
from agente_ga4.prompts import SYSTEM_PROMPT
from agente_ga4.config import AGENT_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

 

# Define the remote tool for the MCP server
# This assumes the MCP server is running on localhost:8080
toolbox = ToolboxSyncClient("https://toolbox-170927488290.us-central1.run.app")
tools = toolbox.load_toolset('my_bq_toolset')


root_agent = Agent(
    model=AGENT_CONFIG['model'],
    name=AGENT_CONFIG['name'],
    description=AGENT_CONFIG['description'],
    instruction=SYSTEM_PROMPT,
    tools=tools,
)