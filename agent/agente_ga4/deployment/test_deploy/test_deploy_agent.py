import os
import sys
import json
import vertexai
from vertexai.preview import reasoning_engines
from google.genai import types
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# --- Configuración ---
# Carga la configuración desde variables de entorno para mayor flexibilidad
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "agentemarketing")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
AGENT_NAME = os.getenv("AGENT_DISPLAY_NAME", "Agente_Marketing")
SESSION_ID = "u_123"

def main():
    """
    Script principal para encontrar un agente, crear/obtener una sesión y ejecutar una consulta.
    """
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # --- 1. Encontrar el Reasoning Engine ---
    print(f"Buscando el agente con el nombre: '{AGENT_NAME}'...")
    engines = reasoning_engines.ReasoningEngine.list(filter=f'display_name="{AGENT_NAME}"')

    if not engines:
        print(f"Error: No se encontró ningún agente con el nombre '{AGENT_NAME}'.")
        sys.exit(1)

    engine = engines[0]
    print(f"Agente encontrado: {engine.resource_name}")

    # --- 2. Obtener o Crear la Sesión ---
    # Esta lógica es más robusta: intenta obtener la sesión y si no existe, la crea.
    try:
        print(f"Intentando obtener la sesión: '{SESSION_ID}'...")
        session = engine.get_session(session_id=SESSION_ID)
        print("Sesión existente encontrada.")
    except Exception:
        print("No se encontró la sesión. Creando una nueva...")
        session = engine.create_session(session_id=SESSION_ID)
        print("Nueva sesión creada.")
    
    print(f"ID de Sesión: {session.id}")

    # --- 3. Ejecutar el Agente ---
    print("\nEnviando consulta al agente...")
    prompt_text = "AAPL"
    print(f">> {prompt_text}")

    output = engine.agent_run(
        session_id=SESSION_ID,
        message=types.Content(
            parts=[types.Part(text=prompt_text)],
            role="user",
        ).model_dump_json(),
    )

    print("\n--- Respuesta del Agente ---")
    print(output)

if __name__ == "__main__":
    main()