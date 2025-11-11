import asyncio
import os
import vertexai
from vertexai import agent_engines
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# --- Configuración ---
# Se asegura de que las variables de entorno estén configuradas
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")

# Obtiene el resource name del agente desde las variables de entorno
AGENT_ENGINE_RESOURCE_NAME = os.getenv("AGENT_ENGINE_RESOURCE_NAME")
TEST_USER_ID = os.getenv("TEST_USER_ID", "user_test_001")
# TEST_QUERY_ES = os.getenv("TEST_QUERY_ES", "cuál es el total de transacciones para el navegador Chrome en el mes 202405?") # Comentado para usar prompts de archivo

def main():
    """
    Función principal para conectarse a un agente desplegado y probarlo con múltiples prompts.
    """
    if not all([PROJECT_ID, LOCATION, AGENT_ENGINE_RESOURCE_NAME]):
        print("Error: Asegúrate de que las variables de entorno GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, y AGENT_ENGINE_RESOURCE_NAME estén configuradas.")
        return

    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # Obtener el agente desplegado
    print(f"Conectando al agente: {AGENT_ENGINE_RESOURCE_NAME}...")
    try:
        remote_app = agent_engines.get(AGENT_ENGINE_RESOURCE_NAME)
    except Exception as e:
        print(f"Error: No se pudo encontrar el agente desplegado. Verifica el resource name.")
        print(f"Detalles: {e}")
        return
    
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
    for i, query in enumerate(prompts):
        print(f"\n==================================================")
        print(f"  PROMPT {i + 1}/{len(prompts)}: {query}")
        print(f"==================================================")

        # Crear una sesión de forma síncrona para cada prompt
        print("Creando sesión remota...")
        remote_session = remote_app.create_session(user_id=TEST_USER_ID)
        print(f"Sesión creada: {remote_session}")

        # Enviar una consulta al agente desplegado
        print("Enviando consulta...")
        print(f">> {query}")
        response_stream = remote_app.stream_query(
            user_id=TEST_USER_ID,
            session_id=remote_session['id'],
            message=query
        )

        print("\n--- Respuesta del Agente Remoto ---")
        for chunk in response_stream:
            if "text" in chunk['content']['parts'][0]:
                print(chunk['content']['parts'][0]['text'], end="")
        print("\n")

if __name__ == "__main__":
    main()
