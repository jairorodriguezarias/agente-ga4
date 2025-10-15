import logging
import os
from typing import Optional

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.sessions import InMemorySessionService
from google.cloud import modelarmor_v1
from google.genai import types
from toolbox_core import ToolboxSyncClient

from .config import AGENT_CONFIG
from .prompts import SYSTEM_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# --- Client Initializations ---
project = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("GOOGLE_CLOUD_LOCATION")
template_model_id = os.getenv("TEMPLATE_MODEL_ARMOR_ID")
TOOLBOX_URL = os.getenv("TOOLBOX_URL")

# Initialize Model Armor Client
if not all([project, location, template_model_id]):
    raise ValueError("Asegúrate de que las variables de entorno GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, y TEMPLATE_MODEL_ARMOR_ID estén configuradas.")
model_armor_client = modelarmor_v1.ModelArmorClient(transport="rest", client_options={"api_endpoint": f"modelarmor.{location}.rep.googleapis.com"})

# Initialize Toolbox Client
if not TOOLBOX_URL:
    raise ValueError("La variable de entorno TOOLBOX_URL no está configurada.")
toolbox = ToolboxSyncClient(TOOLBOX_URL)
tools = toolbox.load_toolset('my_bq_toolset')


# --- Model Armor Guardrail Functions ---
def model_armor_analyze(prompt: str):
    user_prompt_data = modelarmor_v1.DataItem()
    user_prompt_data.text = prompt

    request = modelarmor_v1.SanitizeUserPromptRequest(
        name=f"projects/{project}/locations/{location}/templates/{template_model_id}",
        user_prompt_data=user_prompt_data,
    )
    response = model_armor_client.sanitize_user_prompt(request=request)
    print(f"[Model Armor Response]: {response}")
    jailbreak = response.sanitization_result.filter_results.get("pi_and_jailbreak")
    sensitive_data = response.sanitization_result.filter_results.get("sdp")

    return jailbreak, sensitive_data

def guardrail_function(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    agent_name = callback_context.agent_name
    print(f"[Callback] Before model call for agent: {agent_name}")

    pii_found = callback_context.state.get("PII", False)

    last_user_message = ""
    if llm_request.contents and llm_request.contents[-1].role == 'user':
        if llm_request.contents[-1].parts:
            last_user_message = llm_request.contents[-1].parts[0].text
    print(f"[Callback] Inspecting last user message: '{last_user_message}'")

    if pii_found and last_user_message.lower() != "yes":
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="Please respond Yes/No to continue")]
            )
        )
    elif pii_found and last_user_message.lower() == "yes":
        callback_context.state["PII"] = False
        return None

    try:
        jailbreak, sensitive_data = model_armor_analyze(last_user_message)
        if sensitive_data and sensitive_data.sdp_filter_result and sensitive_data.sdp_filter_result.deidentify_result:
            if sensitive_data.sdp_filter_result.deidentify_result.match_state.name == "MATCH_FOUND":
                pii_found = True
                callback_context.state["PII"] = True
                if pii_found and last_user_message.lower() != "no":
                    return LlmResponse(
                        content=types.Content(
                            role="model",
                            parts=[types.Part(text=
                                              f"""
                                              Your query has identify the following personal information:
                                              {sensitive_data.sdp_filter_result.deidentify_result.info_types}
                                              
                                              Would you like to continue? (Yes/No)
                                              """
                                              )],
                        )
                    )
                elif pii_found and last_user_message.lower() == "yes":
                    callback_context.state["PII"] = False
                    return None

        elif jailbreak and jailbreak.pi_and_jailbreak_filter_result:
            if jailbreak.pi_and_jailbreak_filter_result.match_state.name == "MATCH_FOUND":
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text="Break Reason: Jailbreak")]
                    )
                )
    except Exception as e:
        print(f"[Model Armor Error] Failed to analyze prompt: {e}")
        # Decide if you want to block the request or allow it if Model Armor fails.
        # Returning None allows the request to proceed to the LLM.
        return None

    return None


# --- Session Management ---
session_service = InMemorySessionService()

# --- Agent Definition ---
generate_content_config_1 = types.GenerateContentConfig(
    temperature=0.2,  # More deterministic output
    max_output_tokens=1000,
)

root_agent = Agent(
    model=AGENT_CONFIG['model'],
    name=AGENT_CONFIG['name'],
    description=AGENT_CONFIG['description'],
    instruction=SYSTEM_PROMPT,
    generate_content_config=generate_content_config_1,
    tools=tools,
    before_model_callback=guardrail_function,
)