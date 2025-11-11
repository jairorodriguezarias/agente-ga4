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
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
AGENT_NAME = os.getenv("AGENT_DISPLAY_NAME")
# SESSION_ID = os.getenv("TEST_SESSION_ID", "session_test_abc") # Comentado para crear una sesión por prompt
# prompt_text = os.getenv("TEST_PROMPT_AAPL", "AAPL") # Comentado para usar prompts de archivo

def main():
    """
    Script principal para encontrar un agente, crear/obtener una sesión y ejecutar múltiples consultas.
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

    # Lee los prompts desde el archivo
    prompts_file = os.path.join(os.path.dirname(__file__), "prompts.txt")
    try:
        with open(prompts_file, "r", encoding="utf-8") as f:
            prompts = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: El archivo de prompts no se encontró en {prompts_file}")
        sys.exit(1)

    print(f"--- Iniciando prueba con {len(prompts)} prompts ---")

    # Itera sobre cada prompt
    for i, prompt_text in enumerate(prompts):
        print(f"\n==================================================")
        print(f"  PROMPT {i + 1}/{len(prompts)}: {prompt_text}")
        print(f"==================================================")

        # Crea una nueva sesión para cada prompt para mantener las conversaciones aisladas
        # Esta lógica es más robusta: intenta obtener la sesión y si no existe, la crea.
        try:
            print(f"Intentando obtener la sesión: 'session_test_{i}'...")
            session = engine.get_session(session_id=f"session_test_{i}")
            print("Sesión existente encontrada.")
        except Exception:
            print("No se encontró la sesión. Creando una nueva...")
            session = engine.create_session(session_id=f"session_test_{i}")
            print("Nueva sesión creada.")
        
        print(f"ID de Sesión: {session.id}")

        # --- 3. Ejecutar el Agente ---
        print("\nEnviando consulta al agente...")
        print(f">> {prompt_text}")

        output = engine.agent_run(
            session_id=session.id,
            message=types.Content(
                parts=[types.Part(text=prompt_text)],
                role="user",
            ).model_dump_json(),
        )

        print("\n--- Respuesta del Agente ---")
        print(output)

if __name__ == "__main__":
    main()