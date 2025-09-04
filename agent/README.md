# Agente GA4

Este proyecto es un agente creado con el Kit de Desarrollo de Agentes (ADK) de Google.

## Setup

1.  **Instalar dependencias de Python**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Autenticación con Google Cloud**:
    Asegúrate de haber iniciado sesión con tus Credenciales Predeterminadas de la Aplicación (ADC):
    ```bash
    gcloud auth application-default login
    ```

gcloud services enable cloudresourcemanager.googleapis.com \
                       servicenetworking.googleapis.com \
                       run.googleapis.com \
                       cloudbuild.googleapis.com \
                       cloudfunctions.googleapis.com \
                       aiplatform.googleapis.com \
                       sqladmin.googleapis.com \
                       compute.googleapis.com 

                       
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


# Para agregar una nueva versión del secreto 'tools' con el contenido de tu archivo
gcloud secrets create tools --data-file=tools.yaml
gcloud secrets versions add tools --data-file="tools.yaml"

export IMAGE=us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest

gcloud run deploy toolbox \
--image $IMAGE \
--service-account toolbox-identity \
--region us-central1 \
--set-secrets "/app/tools.yaml=tools:latest" \
--args="--tools-file=/app/tools.yaml","--address=0.0.0.0","--port=8080" \
--allow-unauthenticated

## Troubleshooting

### SSL: CERTIFICATE_VERIFY_FAILED

Al ejecutar el agente en macOS, es posible que te encuentres con un error `aiohttp.client_exceptions.ClientConnectorCertificateError` que indica `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate`.

Esto ocurre porque el entorno de Python no puede encontrar los certificados raíz del sistema.

**Solución:**

El entorno virtual de este proyecto ha sido configurado para solucionar este problema automáticamente. El script `venv/bin/activate` ha sido modificado para establecer la variable de entorno `SSL_CERT_FILE` para que apunte a los certificados proporcionados por el paquete `certifi`.

Cada vez que actives el entorno con `source venv/bin/activate`, la solución se aplicará.

### Permisos de BigQuery

Si al ejecutar el agente obtienes un error de `Access Denied` relacionado con `bigquery.jobs.create`, significa que la cuenta de servicio `toolbox-identity` no tiene los permisos necesarios para interactuar con BigQuery.

**Solución:**

Otorga el rol `roles/bigquery.jobUser` a la cuenta de servicio `toolbox-identity` en tu proyecto. Puedes hacerlo con el siguiente comando:

```bash
gcloud projects add-iam-policy-binding agentemarketing \
    --member serviceAccount:toolbox-identity@agentemarketing.iam.gserviceaccount.com \
    --role roles/bigquery.jobUser
```

