from adk.agent import Agent
from adk.llm import Gemini

# Define your tools here

# Create the agent
agent = Agent(
    llm=Gemini(),
    # tools=[...]
)
