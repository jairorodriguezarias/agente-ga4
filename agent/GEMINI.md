# Proyecto de Agente con ADK

Este archivo describe la estructura y el uso de este proyecto de agente de ADK.

## Estructura del Proyecto

El proyecto sigue la siguiente estructura:

```
agente_ga4/
├── venv/
├── agente_ga4/
│   ├── __init__.py
│   └── agent.py
├── .env
├── README.md
└── GEMINI.md
```

- **agente_ga4/**: El directorio raíz de su proyecto.
- **venv/**: El entorno virtual de Python.
- **agente_ga4/**: Un paquete de Python para su agente.
- **__init__.py**: Hace que el directorio `agente_ga4` sea un paquete de Python.
- **agent.py**: Este es el archivo principal donde se define la lógica de su agente.
- **.env**: Archivo para variables de entorno (no se usa para credenciales en este proyecto).
- **README.md**: Archivo de descripción del proyecto.
- **GEMINI.md**: Archivo con información para Gemini.

## Cómo Empezar

1.  **Activar el entorno virtual**:
    ```bash
    source venv/bin/activate
    ```

2.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Autenticación**:
    Este proyecto utiliza las Credenciales Predeterminadas de la Aplicación (Application Default Credentials - ADC) para la autenticación con Google Cloud. Asegúrate de haber iniciado sesión con:
    ```bash
    gcloud auth application-default login
    ```

4.  **Ejecutar el agente**:
    ```bash
    adk web --agent_path=agente_ga4/agent.py
    ```

## Toolbox Setup

Para poder utilizar las herramientas de este agente, es necesario descargar el ejecutable `toolbox`:

**Nota:** El siguiente comando es para sistemas `darwin` (macOS). Si usas un sistema operativo diferente, por favor, ajusta la URL de descarga a tu arquitectura.

```bash
cd agent/mcp_toolbox
export VERSION=0.7.0
# Para sistemas darwin (macOS)
curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/darwin/amd64/toolbox
# Para sistemas linux
# curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox
chmod +x toolbox
```

## Información Importante

- **ID del Proyecto de Google Cloud**: `agentemarketing`
- **Usuario Administrador**: `admin@jairorodriguez.altostrat.com`
- **Autenticación**: Se utilizan las Credenciales Predeterminadas de la Aplicación (ADC) a través de `gcloud auth application-default login`. No es necesario utilizar un archivo `.env` para las credenciales.
- **Dependencias**: La principal dependencia es `google-adk`, que se instala con `pip install google-adk`.
- **Ejecución**: El agente se ejecuta con el comando `adk web --agent_path=agente_ga4/agent.py`.

## Configuración Adicional

### Arreglo para error de Certificado SSL en macOS

Al intentar cargar herramientas de `toolbox` de forma remota, puede surgir un error de `CERTIFICATE_VERIFY_FAILED`.

Para solucionarlo de forma permanente dentro del entorno virtual, el script `venv/bin/activate` ha sido modificado para exportar la variable de entorno `SSL_CERT_FILE` apuntando a los certificados del paquete `certifi`. Esta solución se activa automáticamente al usar `source venv/bin/activate`.

### Permisos de BigQuery

Para que el agente pueda interactuar con BigQuery, la cuenta de servicio `toolbox-identity` necesita el rol `roles/bigquery.jobUser`. Este rol se otorga con el siguiente comando:

```bash
gcloud projects add-iam-policy-binding agentemarketing \
    --member serviceAccount:toolbox-identity@agentemarketing.iam.gserviceaccount.com \
    --role roles/bigquery.jobUser
```
