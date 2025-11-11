import sys
import os

# Agrega el directorio raíz del proyecto a sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import vertexai
from agente_ga4.agent import root_agent, toolbox # 1. Importar toolbox
from dotenv import load_dotenv

load_dotenv()  # Carga las variables de entorno desde el archivo .env

# Carga las variables de entorno para pruebas
TEST_USER_ID = os.getenv("TEST_USER_ID", "user_test_001")
# TEST_MESSAGE = os.getenv("TEST_MESSAGE", "what is the total revenue for the month of May 2024?") # Comentado para usar prompts de archivo


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

# --- Ejecución de la Prueba ---
def main():
    """Función principal para probar el agente con múltiples prompts."""
    # Wrap the agent in an AdkApp object
    app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )

    # Lee los prompts desde el archivo
    prompts_file = os.path.join(os.path.dirname(__file__), "prompts.txt")
    try:
        with open(prompts_file, "r", encoding="utf-8") as f:
            prompts = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: El archivo de prompts no se encontró en {prompts_file}")
        return

    print(f"--- Iniciando prueba con {len(prompts)} prompts ---")

    # Itera sobre cada prompt
    for i, prompt in enumerate(prompts):
        print(f"\n==================================================")
        print(f"  PROMPT {i + 1}/{len(prompts)}: {prompt}")
        print(f"==================================================")

        # Crea una nueva sesión para cada prompt para mantener las conversaciones aisladas
        session = app.create_session(user_id=TEST_USER_ID)
        print(f"Sesión creada: {session.id}")

        try:
            events = list(app.stream_query(
                user_id=TEST_USER_ID,
                session_id=session.id,
                message=prompt,
            ))

            # Extrae y muestra solo la respuesta final de texto
            final_text_responses = [
                e for e in events
                if e.get("content", {}).get("parts", [{}])[0].get("text")
                and not e.get("content", {}).get("parts", [{}])[0].get("function_call")
            ]
            if final_text_responses:
                print("\n--- Respuesta Final del Agente ---")
                print(final_text_responses[-1]["content"]["parts"][0]["text"])
            else:
                print("\n--- No se recibió una respuesta de texto final ---")

        except Exception as e:
            print(f"\n--- Ocurrió un error al procesar el prompt ---")
            print(e)

    print("\n--- Prueba Finalizada ---")


 
