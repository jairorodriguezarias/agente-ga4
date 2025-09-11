import asyncio
import os
import vertexai
from vertexai.preview import agent_engines
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# --- Configuración ---
# Se asegura de que las variables de entorno estén configuradas o usa valores predeterminados
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "agentemarketing")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# El ID del agente que desplegaste. Deberías actualizarlo si despliegas una nueva versión.
AGENT_ENGINE_ID = "8433487281507008512"

async def main():
    """
    Función principal asíncrona para conectarse a un agente desplegado y probarlo.
    """
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # Obtener el agente desplegado
    print(f"Conectando al agente: {AGENT_ENGINE_ID}...")
    try:
        remote_app = agent_engines.get(f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}")
    except Exception as e:
        print(f"Error: No se pudo encontrar el agente desplegado. Verifica el ID.")
        print(f"Detalles: {e}")
        return
    
    # Crear una sesión de forma asíncrona
    print("Creando sesión remota...")
    remote_session = await remote_app.async_create_session(user_id="u_789")
    print(f"Sesión creada: {remote_session.id}")

    # Enviar una consulta al agente desplegado
    print("Enviando consulta...")
    query = "cuál es el total de transacciones para el navegador Chrome en el mes 202405?"
    print(f">> {query}")
    response_stream = remote_app.stream_query(
        session_id=remote_session.id,
        message=query
    )

    print("\n--- Respuesta del Agente Remoto ---")
    for chunk in response_stream:
        if "text" in chunk.content.parts[0]:
            print(chunk.content.parts[0].text, end="")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
