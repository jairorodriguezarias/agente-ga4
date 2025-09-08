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
    source venv/bin/activate
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
        agente_ga4/
    ```