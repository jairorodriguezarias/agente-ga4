# Proyecto de Agente con ADK

Este archivo describe la estructura y el uso de este proyecto de agente de ADK, con información específica para el modelo Gemini.

## Estructura del Proyecto

El proyecto sigue la siguiente estructura:

```
agente_ga4/
├── venv/
├── agente_ga4/
│   ├── __init__.py
│   ├── agent.py
│   ├── config.py
│   ├── prompts.py
│   └── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
├── GEMINI.md
├── requirements.txt (moved to agente_ga4/requirements.txt)
├── setup_gcloud.sh
└── mcp_toolbox/
    ├── toolbox
    └── tools.yaml
```

## Cómo Empezar (para Gemini)

Para ejecutar el agente o realizar tareas de desarrollo:

1.  **Activar el entorno virtual**:
    ```bash
    source v/bin/activate
    ```

2.  **Instalar dependencias**:
    ```bash
    pip install -r agente_ga4/requirements.txt
    ```

3.  **Autenticación**:
    Este proyecto utiliza las Credenciales Predeterminadas de la Aplicación (Application Default Credentials - ADC) para la autenticación con Google Cloud. Asegúrate de haber iniciado sesión con:
    ```bash
    gcloud auth application-default login
    ```

4.  **Ejecutar el agente (localmente)**:
    ```bash
    adk web --agent_path=agente_ga4/agent.py
    ```

## Toolbox Setup (para Gemini)

Para poder utilizar las herramientas de este agente, es necesario descargar el ejecutable `toolbox` y configurar el servidor MCP:

1.  **Descargar el ejecutable `toolbox`**:
    ```bash
    cd mcp_toolbox
    export VERSION=0.7.0
    curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/darwin/amd64/toolbox # Para macOS
    # curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox # Para Linux
    chmod +x toolbox
    cd ..
    ```

2.  **Configurar el secreto `tools` en Secret Manager**:
    ```bash
    gcloud secrets create tools --data-file=mcp_toolbox/tools.yaml # Solo la primera vez
    gcloud secrets versions add tools --data-file=mcp_toolbox/tools.yaml # Para actualizar
    ```

3.  **Desplegar el servidor MCP en Cloud Run**:
    ```bash
    export IMAGE=us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest
    gcloud run deploy toolbox \
        --image $IMAGE \
        --service-account toolbox-identity \
        --region us-central1 \
        --set-secrets "/app/tools.yaml=tools:latest" \
        --args="--tools-file=/app/tools.yaml","--address=0.0.0.0","--port=8080" \
        --allow-unauthenticated \
        --timeout=600
    ```

## Información Importante (para Gemini)

-   **ID del Proyecto de Google Cloud**: `YOUR_PROJECT_ID`
-   **Usuario Administrador**: `YOUR_ADMIN_USER_EMAIL`
-   **Autenticación**: Se utilizan las Credenciales Predeterminadas de la Aplicación (ADC) a través de `gcloud auth application-default login`. No es necesario utilizar un archivo `.env` para las credenciales.
-   **Dependencias**: La principal dependencia es `google-adk`, que se instala con `pip install -r requirements.txt`.

## Configuración Adicional (para Gemini)

### Arreglo para error de Certificado SSL en macOS

**Problema:** `aiohttp.client_exceptions.ClientConnectorCertificateError` con `[SSL: CERTIFICATE_VERIFY_FAILED]`.

**Solución:** El script `venv/bin/activate` ha sido modificado para exportar `SSL_CERT_FILE` apuntando a los certificados de `certifi`. Se activa automáticamente con `source venv/bin/activate`.

### Permisos de BigQuery

**Problema:** `Error 403: Access Denied` relacionado con `bigquery.jobs.create`.

**Solución:** Otorgar el rol `roles/bigquery.jobUser` a la cuenta de servicio `toolbox-identity@YOUR_PROJECT_ID.iam.gserviceaccount.com`.
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member serviceAccount:toolbox-identity@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --role roles/bigquery.jobUser
```

## Despliegue en Agent Engine (para Gemini)

Para desplegar el agente en Google Cloud Agent Engine:

1.  **Asegúrate de que el bucket de GCS exista:**
    ```bash
    gcloud storage buckets create gs://YOUR_PROJECT_ID-agent-engine-bucket --project=YOUR_PROJECT_ID --location=us-central1
    ```

2.  **Despliega el agente en Agent Engine:**
    ```bash
    adk deploy agent_engine \
        --project=YOUR_PROJECT_ID \
        --region=us-central1 \
        --staging_bucket=gs://YOUR_PROJECT_ID-agent-engine-bucket \
        --display_name="Agente_Marketing"
    ```

## Publicar Agentes de ADK en Agentspace

Esta sección se basa en el documento "Publishing agents built on ADK to Agentspace".

### Prerrequisitos

-   **Proyecto en Allowlist**: Tu proyecto de Google Cloud debe estar en la lista de permitidos de Agentspace.
-   **Registro Cross-Project**: Si el agente (desplegado en Proyecto A) y Agentspace (en Proyecto B) están en proyectos distintos, se necesita un proceso de *allowlisting* adicional.
-   **Permisos de Cuenta de Servicio**: La cuenta de servicio `service-PROJECTNUMBER@gcp-sa-discoveryengine.iam.gserviceaccount.com` necesita los siguientes roles:
    -   `Discovery Engine Service Agent`
    -   `Editor`
    -   `Vertex AI User`
    -   `Vertex AI Viewer`
    *(Nota: Para encontrar esta cuenta de servicio en IAM, asegúrate de marcar la casilla "Incluir concesiones de roles proporcionadas por Google")*.

### 1. Despliegue en Agent Engine

Asegúrate de que tu `requirements.txt` contiene `google-cloud-aiplatform[agent_engines,adk]`.

```bash
adk deploy agent_engine \
    --project=YOUR_PROJECT_ID \
    --region=us-central1 \
    --staging_bucket=gs://YOUR_DEPLOYMENT_BUCKET \
    --display_name="YOUR_AGENT_NAME"
```

#### Notas importantes sobre el despliegue:

-   El comando `adk deploy` crea un agente **nuevo** cada vez. Actualmente no hay funcionalidad para actualizar uno existente (es una feature request pendiente).
-   Para **eliminar un agente**, se puede usar la UI de Agent Engine en la consola de Cloud o la [herramienta de registro de agentes](https://github.com/VeerMuchandi/agent_registration_tool).
-   Actualmente no se pueden ver los **logs de despliegue** en tiempo real (también es una feature request pendiente).
-   Es crucial **anotar el `reasoning-engine id`** que se muestra al final del despliegue para poder registrar el agente en Agentspace.

### 2. Probar el Agente Desplegado

Puedes usar un script de Python para verificar que el agente funciona en Agent Engine.

```python
import vertexai
from vertexai.preview import reasoning_engines

# Configuración inicial
PROJECT_ID = "YOUR_PROJECT_ID"
LOCATION = "us-central1"
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Buscar el Reasoning Engine
engines = reasoning_engines.ReasoningEngine.list(
    filter='display_name="YOUR_AGENT_NAME"'
)

if not engines:
    print(f"No se encontró el Reasoning Engine con el nombre: YOUR_AGENT_NAME")
else:
    engine = engines[0]
    print(f"Reasoning Engine encontrado: {engine.resource_name}")

    # Crear una sesión
    session = engine.create_session()
    print(f"Sesión creada: {session.name}")

    # Ejecutar el agente
    output = engine.agent_run(
        session_id=session.name.split('/')[-1],
        message="Escribe tu prompt aquí"
    )
    print(f"Respuesta del agente: {output}")
```

### 3. Registrar en Agentspace (Método Alternativo)

Existe una herramienta CLI para simplificar el registro y la gestión de agentes.

-   **Repositorio**: [https://github.com/VeerMuchandi/agent_registration_tool](https://github.com/VeerMuchandi/agent_registration_tool)
-   **Uso**:
    ```bash
    python as_registry_client.py --config config.txt
    ```
    La herramienta permite acciones como `register_agent`, `update_agent`, `list_registry`, etc.

### Problemas Conocidos

-   **Error de `Malformed Function Call`** (ID de bug: `b/409316706`): Puede ocurrir en transacciones largas y causa que el agente no se ejecute completamente.
-   **Formato de Salida**: A veces, el formato de la salida del agente puede ser aleatorio y mostrar markdown o HTML crudo.
