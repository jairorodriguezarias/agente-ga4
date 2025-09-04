# Agente GA4

Este proyecto es un agente creado con el Kit de Desarrollo de Agentes (ADK) de Google, especializado en el análisis de datos de Google Analytics.

## Tabla de Contenidos
- [Setup Inicial](#setup-inicial)
  - [Requisitos Previos](#requisitos-previos)
  - [Configuración del Entorno Local](#configuración-del-entorno-local)
  - [Configuración de Google Cloud](#configuración-de-google-cloud)
  - [Configuración del Servidor MCP (Toolbox)](#configuración-del-servidor-mcp-toolbox)
- [Uso del Agente](#uso-del-agente)
- [Refactorización del Código](#refactorización-del-código)
- [Solución de Problemas Comunes](#solución-de-problemas-comunes)
  - [Error de Certificado SSL (macOS)](#error-de-certificado-ssl-macos)
  - [Error 404 (Toolset no encontrado)](#error-404-toolset-no-encontrado)
  - [Error 403 (Permisos de BigQuery)](#error-403-permisos-de-bigquery)
  - [Error de Importación (asyncio.tools)](#error-de-importación-asyncio.tools)
  - [Error 404 (Región de Gemini API)](#error-404-región-de-gemini-api)
- [Limpieza del Proyecto](#limpieza-del-proyecto)
- [Despliegue en Cloud Run](#despliegue-en-cloud-run)

---

## Setup Inicial

### Requisitos Previos
Asegúrate de tener instalado:
- Python 3.11 o superior
- `gcloud CLI` (Google Cloud SDK)
- `docker` (si planeas ejecutar el servidor MCP localmente)

### Configuración del Entorno Local

1.  **Activar el entorno virtual**:
    ```bash
    source venv/bin/activate
    ```
    *Nota: Si el entorno virtual no existe o está dañado, se creará automáticamente con Python 3.11.6 al instalar las dependencias.*

2.  **Instalar dependencias de Python**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Autenticación con Google Cloud**:
Asegúrate de haber iniciado sesión con tus Credenciales Predeterminadas de la Aplicación (ADC). Esto es crucial para que el agente y las herramientas interactúen con los servicios de Google Cloud.
    ```bash
    gcloud auth application-default login
    ```

### Configuración de Google Cloud

1.  **Habilitar servicios de Google Cloud**:
Asegúrate de que los siguientes servicios estén habilitados en tu proyecto de Google Cloud (`YOUR_PROJECT_ID`):
    ```bash
    gcloud services enable cloudresourcemanager.googleapis.com \
                           servicenetworking.googleapis.com \
                           run.googleapis.com \
                           cloudbuild.googleapis.com \
                           cloudfunctions.googleapis.com \
                           aiplatform.googleapis.com \
                           sqladmin.googleapis.com \
                           compute.googleapis.com
    ```

2.  **Configurar permisos de BigQuery**:
Si al ejecutar el agente obtienes un error de `Access Denied` relacionado con `bigquery.jobs.create`, significa que la cuenta de servicio `toolbox-identity` no tiene los permisos necesarios para interactuar con BigQuery.
**Solución:** Otorga el rol `roles/bigquery.jobUser` a la cuenta de servicio `toolbox-identity@YOUR_PROJECT_ID.iam.gserviceaccount.com` en tu proyecto.
    ```bash
    gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
        --member serviceAccount:toolbox-identity@YOUR_PROJECT_ID.iam.gserviceaccount.com \
        --role roles/bigquery.jobUser
    ```

### Configuración del Servidor MCP (Toolbox)

El agente utiliza un servidor de herramientas (MCP Toolbox) para interactuar con BigQuery. Este servidor puede ejecutarse localmente o desplegarse en Cloud Run.

1.  **Descargar el ejecutable `toolbox`**:
    **Nota:** El siguiente comando es para sistemas `darwin` (macOS). Si usas un sistema operativo diferente, por favor, ajusta la URL de descarga a tu arquitectura.
    ```bash
    cd mcp_toolbox
    export VERSION=0.7.0
    # Para sistemas darwin (macOS)
    curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/darwin/amd64/toolbox
    # Para sistemas linux
    # curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox
    chmod +x toolbox
    cd .. # Volver al directorio raíz del proyecto
    ```

2.  **Configurar `tools.yaml`**:
El archivo `mcp_toolbox/tools.yaml` define las herramientas disponibles para el servidor MCP. Asegúrate de que la configuración de las herramientas y los `toolsets` sea correcta.
    *   La consulta inicial para `search_release_notes_bq` fue cambiada a una consulta de `daily_visits` de Google Analytics.
    *   El nombre de la herramienta y su descripción fueron actualizados para reflejar este cambio (`get_daily_visits`).

3.  **Actualizar el secreto `tools` en Secret Manager**:
Si has modificado `mcp_toolbox/tools.yaml` y el servidor MCP está desplegado en Cloud Run, necesitas actualizar el secreto en Secret Manager para que los cambios surtan efecto.
    ```bash
    gcloud secrets versions add tools --data-file="mcp_toolbox/tools.yaml"
    ```

## Uso del Agente

Una vez configurado el entorno local y el servidor MCP, puedes ejecutar el agente:

```bash
adk web --agent_path=agente_ga4/agent.py
```
Luego, puedes interactuar con el agente en tu terminal.

## Refactorización del Código

Para una mejor organización y mantenibilidad, el código del agente ha sido refactorizado:
- El `SYSTEM_PROMPT` ha sido movido a `agente_ga4/prompts.py`.
- La configuración del agente (modelo, nombre, descripción) ha sido movida a `agente_ga4/config.py`.
- El archivo `agente_ga4/agent.py` ahora importa estas configuraciones y las utiliza para inicializar el agente.

## Solución de Problemas Comunes

### Error de Certificado SSL (macOS)

**Problema:** Al ejecutar el agente en macOS, es posible que te encuentres con un error `aiohttp.client_exceptions.ClientConnectorCertificateError` que indica `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate`. Esto ocurre porque el entorno de Python no puede encontrar los certificados raíz del sistema.

**Solución:** El entorno virtual de este proyecto ha sido configurado para solucionar este problema automáticamente. El script `venv/bin/activate` ha sido modificado para establecer la variable de entorno `SSL_CERT_FILE` para que apunte a los certificados proporcionados por el paquete `certifi`. Esta solución se activa automáticamente al usar `source venv/bin/activate`.

### Error 404 (Toolset no encontrado)

**Problema:** Si el agente falla con un `RuntimeError` indicando `toolset 