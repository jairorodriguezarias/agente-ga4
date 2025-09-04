import logging
from adk.agent import Agent
from adk.llm import Gemini

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# System prompt to define the agent's persona and constraints
SYSTEM_PROMPT = """
Eres un analista de marketing especializado en Google Analytics.
Tu única función es responder a preguntas sobre los datos de Google Analytics a los que tienes acceso a través de tus herramientas.
Eres claro y conciso en tus respuestas.
No puedes responder a ninguna otra pregunta que no esté relacionada con Google Analytics.
Si no puedes responder a una pregunta, simplemente di: 'No tengo acceso a esa información'.
"""

# The tools are defined in the mcp_toolbox/tools.yaml file and will be loaded by the ADK.
# No need to define them here.

# Create the agent
try:
    agent = Agent(
        llm=Gemini(),
        system_prompt=SYSTEM_PROMPT,
        # The ADK will automatically load the tools from the mcp_toolbox/tools.yaml file.
        # tools=[...],
    )
    logging.info("Agent created successfully.")
except Exception as e:
    logging.error(f"Failed to create agent: {e}")
    agent = None

if __name__ == '__main__':
    if agent:
        logging.info("Starting agent interaction.")
        # This is a placeholder for how you might interact with the agent.
        # For example, you could start a web server or a command-line interface.
        print("Agent is ready. You can now interact with it.")
    else:
        logging.error("Agent could not be initialized. Exiting.")