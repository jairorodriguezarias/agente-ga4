# Agente GA4

Este proyecto es un agente creado con el Kit de Desarrollo de Agentes (ADK) de Google, especializado en el análisis de datos de Google Analytics.

## Tabla de Contenidos
- [Setup Inicial](#setup-inicial)
  - [Requisitos Previos](#requisitos-previos)
  - [Configuración Automatizada con Script](#configuración-automatizada-con-script)
  - [Configuración Manual](#configuración-manual)
- [Descripción de Herramientas (`tools.yaml`)](#descripción-de-herramientas-toolsyaml)
- [Uso del Agente](#uso-del-agente)
- [Evaluación del Agente con ADK](#evaluación-del-agente-con-adk)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Solución de Problemas Comunes](#solución-de-problemas-comunes)

---

## Setup Inicial

### Requisitos Previos
Asegúrate de tener instalado:
- Python 3.11 o superior
- `gcloud CLI` (Google Cloud SDK)
- `docker` (si planeas ejecutar el servidor MCP localmente)

### Configuración Automatizada con Script (`setup_gcloud.sh`)

El proyecto incluye un script para automatizar la configuración inicial de Google Cloud.

**¿Qué hace el script?**
-   Configura el ID del proyecto en `gcloud`.
-   Activa las APIs necesarias (Vertex AI, Cloud Run, Secret Manager).
-   Crea una cuenta de servicio (`agent-runner`) con los permisos necesarios (`roles/vertexai.user`).
-   Crea y descarga una clave JSON (`gcloud-sa-key.json`) para esa cuenta de servicio.

**¿Cómo usarlo?**
```bash
bash setup_gcloud.sh TU_ID_DE_PROYECTO
```
Tras ejecutarlo, el script te indicará cómo configurar la variable de entorno `GOOGLE_APPLICATION_CREDENTIALS` para usar la clave JSON generada, que es el método de autenticación recomendado.

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

Para un ejemplo detallado de la configuración de MCP para BigQuery, puedes consultar la [guía de inicio rápido oficial](https://googleapis.github.io/genai-toolbox/samples/bigquery/mcp_quickstart/).

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

---

## Descripción de Herramientas (`tools.yaml`)

El agente no tiene consultas SQL en su código. En su lugar, utiliza herramientas definidas en `mcp_toolbox/tools.yaml`. Estas herramientas son servidas por el servidor MCP.

A continuación se describen las herramientas implementadas:

- **`get_daily_visits`**
  - **Descripción**: Obtiene una lista de las visitas diarias al sitio web desde Google Analytics.
  - **Parámetros**: Ninguno.

- **`get_daily_transactions_by_browser`**
  - **Descripción**: Devuelve el número total de transacciones agrupadas por navegador para un día específico.
  - **Parámetros**: `TABLE_SUFFIX` (string, formato `YYYYMMDD`).

- **`get_monthly_visits`**
  - **Descripción**: Devuelve el número total de visitas únicas para un mes específico.
  - **Parámetros**: `YEAR_MONTH` (string, formato `YYYYMM`).

- **`get_monthly_transactions_by_browser`**
  - **Descripción**: Devuelve el número total de transacciones agrupadas por navegador para un mes específico.
  - **Parámetros**: `YEAR_MONTH` (string, formato `YYYYMM`).

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

**Problema:** Si el agente falla con un `RuntimeError` indicando `toolset`

### Error de Importación (`ModuleNotFoundError`)

**Problema:** Al ejecutar un script como `python agente_ga4/deploy.py` desde el directorio raíz del proyecto, puedes encontrar un `ModuleNotFoundError`, indicando que un paquete como `agente_ga4` no se puede encontrar.

**Causa:** Esto ocurre porque Python, por defecto, agrega el directorio del script (`agente_ga4/`) a su ruta de búsqueda, en lugar del directorio de trabajo actual (`agent/`). Cuando el script intenta importar `from agente_ga4...`, Python no puede encontrar el paquete porque no está buscando en el directorio correcto.

**Solución:** La solución implementada en `deploy.py` es agregar manualmente el directorio raíz del proyecto a la ruta de búsqueda de Python al inicio del script. Esto asegura que los módulos del paquete siempre se puedan encontrar, independientemente de cómo se ejecute el script.
```python
# deploy.py
import sys
import os

# Agrega el directorio raíz del proyecto a sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ... el resto del script
```

### Error de Sesión no Cerrada (`Unclosed client session`)

**Problema:** Después de que un script se ejecuta y finaliza, pueden aparecer errores como `Unclosed client session` o `Unclosed connector`.

**Causa:** Esto sucede porque un cliente de red (en este caso, `ToolboxSyncClient`) abrió conexiones pero no las cerró explícitamente antes de que el programa terminara.

**Solución:** Se implementó un bloque `try...finally` en `deploy.py` para garantizar que el método `toolbox.close()` se llame siempre al final de la ejecución. Esto libera los recursos de red de manera ordenada y elimina los mensajes de error.

```python
# deploy.py
from agente_ga4.agent import toolbox

try:
    # Lógica principal de la aplicación
    ...
finally:
    # Este bloque se ejecuta siempre al final
    print("\nCerrando la conexión del toolbox...")
    toolbox.close()
```

## Evaluación del Agente con ADK

El proyecto utiliza "evalsets" para realizar pruebas de regresión y asegurar que el agente se comporta como se espera.

- **¿Qué es un `evalset`?**: Es un archivo JSON que contiene una o más conversaciones de ejemplo, cada una con una entrada de usuario y la respuesta ideal que el agente debería producir.
- **Archivos existentes**:
    - `basico.evalset.json`: Contiene preguntas generales para validar la personalidad y las capacidades básicas del agente.
    - `transacciones_mensuales.evalset.json`: Contiene pruebas específicas para la herramienta de transacciones mensuales.

**¿Cómo ejecutar la evaluación?**

```bash
# Ejecutar el set de pruebas básico
adk eval --agent_path=agente_ga4/agent.py --eval_set_path=agente_ga4/basico.evalset.json
```

**¿Cómo crear un nuevo `evalset`?**
La forma más sencilla es interactuar con el agente vía `adk web` y, una vez que se obtiene una conversación satisfactoria, guardarla como un nuevo archivo JSON de `evalset` para futuras pruebas.

## Despliegue en Agent Engine

Para desplegar el agente en Google Cloud Agent Engine, sigue estos pasos. Los valores de configuración (`project`, `region`, etc.) se toman del archivo `.env`.

1.  **Asegúrate de que el bucket de GCS exista:** Agent Engine necesita un bucket de GCS para el staging. Si aún no existe, créalo con este comando:
    ```bash
    gcloud storage buckets create gs://agentemarketing-agent-engine-bucket --project=agentemarketing --location=us-central1
    ```

2.  **Verifica las dependencias:** Asegúrate de que tu archivo `agente_ga4/requirements.txt` contenga `google-adk` y `google-cloud-aiplatform[agent_engines]`.

3.  **Despliega el agente:** Ejecuta el siguiente comando en tu terminal desde el directorio raíz del proyecto.
    ```bash
    adk deploy agent_engine --project=agentemarketing --region=us-central1 --staging_bucket=gs://agentemarketing-agent-engine-bucket --display_name="Agente_Marketing" agente_ga4/
    ```
    Este comando empaquetará tu código, lo subirá al bucket de staging, creará una imagen de contenedor y la desplegará en el servicio gestionado de Agent Engine. El proceso puede tardar varios minutos.

## Modelo de Seguridad y Permisos

El acceso a los recursos de Google Cloud, como BigQuery, se gestiona a través de un modelo de autenticación y autorización robusto. Es fundamental entender cómo el agente interactúa con estos servicios de forma segura.

### Autenticación del Agente

El agente utiliza las **Credenciales Predeterminadas de la Aplicación (ADC)** para autenticarse con los servicios de Google Cloud. Esto significa que el agente se autentica como la identidad que ha iniciado sesión en `gcloud CLI` en tu entorno local (`gcloud auth application-default login`).

### Autorización para BigQuery (a través del Servidor MCP)

Cuando el agente necesita acceder a BigQuery, lo hace a través del **Servidor MCP (Toolbox)**. Este servidor, cuando se despliega en Cloud Run, utiliza su propia **Cuenta de Servicio** para la autorización.

-   **Cuenta de Servicio del Servidor MCP**: `toolbox-identity@YOUR_PROJECT_ID.iam.gserviceaccount.com`
    Esta cuenta de servicio es la identidad que el servidor MCP asume para interactuar con los servicios de Google Cloud, incluyendo BigQuery.

-   **Permisos Necesarios**: Para que el servidor MCP pueda ejecutar consultas en BigQuery, su cuenta de servicio (`toolbox-identity`) debe tener los roles de IAM adecuados. El rol mínimo necesario para ejecutar trabajos de BigQuery es `roles/bigquery.jobUser`. Este rol incluye el permiso `bigquery.jobs.create` que fue necesario otorgar previamente.

    **Esquema de Flujo de Permisos:**
    1.  **Usuario Local** (`gcloud auth application-default login`)
    2.  **Agente Local** (se autentica como el usuario local vía ADC)
    3.  **Llamada al Servidor MCP** (el agente se comunica con la URL pública del servidor MCP)
    4.  **Servidor MCP en Cloud Run** (se autentica con su Cuenta de Servicio `toolbox-identity`)
    5.  **Acceso a BigQuery** (la Cuenta de Servicio `toolbox-identity` ejecuta la consulta en BigQuery, siempre que tenga el rol `roles/bigquery.queryUser` o `roles/bigquery.jobUser`)

Este modelo asegura que el agente local no necesita directamente los permisos de BigQuery, sino que delega esa responsabilidad al servidor MCP, que opera con un conjunto de permisos más restringido y específico para su función.
