> **Aviso:** Este documento corresponde a una versión de prueba (v0.1). La arquitectura y los componentes aquí descritos pueden estar sujetos a cambios.

---
**Autor:** Jairo Rodriguez Airas  
**Email:** jairorodriguez@google.com  
**Usuario:** @jairorodriguez
---

# Documentación de Arquitectura: Agente de Marketing para GA4

---

## 1. Introducción y Objetivo

Este documento describe la arquitectura, los componentes y el modelo de seguridad del **Agente de Marketing para Google Analytics 4 (GA4)**. El objetivo de esta prueba de concepto es ilustrar la creación de una interfaz conversacional inteligente que permita a los usuarios (como equipos de marketing o analistas de datos) realizar consultas en lenguaje natural sobre los datos de GA4 almacenados en BigQuery.

El agente está diseñado para ser seguro, escalable y fácil de usar, abstrayendo la complejidad de las consultas SQL y ofreciendo respuestas claras y directas.

---

## 2. Contexto y Motivación

Los datos de Google Analytics (para el Alta Online y la Banca Online) ya se están exportando a BigQuery, lo que permite consultar información relevante desde allí.

Se está considerando llevar información adicional, como la tabla de cookies generadas en el login de banca online, a BigQuery para poder identificar a qué cliente corresponde cada cookie. 

Actualmente, en Banca Online solo se dispone de datos de Page Views, aunque se prevé la inclusión de un etiquetado automático de páginas próximamente, lo que permitirá preguntas más detalladas sobre navegación. 

Está etiquetado el funnel de depósitos (Banca Online) y el funnel del Alta Online.

---

## 3. Arquitectura General

La solución se compone de varios servicios y componentes que trabajan en conjunto. La arquitectura ha sido diseñada siguiendo las mejores prácticas de Google Cloud, priorizando la seguridad y la separación de responsabilidades.

Los componentes principales son:

1.  **Agentspace**: La interfaz de usuario web donde los usuarios finales interactúan con el agente.
2.  **El Agente (Desarrollado con ADK y desplegado en Agent Engine)**: Es el cerebro de la operación. Procesa las peticiones del usuario y orquesta la interacción con las herramientas.
3.  **Servidor de Herramientas (MCP Toolbox)**: Un microservicio seguro que actúa como un puente controlado entre el Agente y la base de datos de BigQuery. Este servidor se despliega como un servicio contenedorizado independiente en **Google Cloud Run**.
4.  **Google BigQuery**: El almacén de datos donde residen los datos exportados de Google Analytics 4.
5.  **Servicios de Google Cloud**: Un conjunto de servicios en la nube que alojan y gestionan los componentes de la solución (Cloud Run, Secret Manager, IAM).

A continuación se presenta un diagrama que ilustra el flujo de componentes de la solución:

```
+---------------+      +----------------+      +-----------------------------+      +---------------------+ 
|               |      |                |      |  Agente (ADK + Gemini)      |      |                     | 
| Usuario Final |----->|   Agentspace   |----->| (Desplegado en Agent Engine)|----->|  Servidor MCP (Cloud| 
|               |      | (Interfaz Web) |      |                             |      |     Run)            | 
+---------------+      +----------------+      +---------------+-------------+      +----------+----------+ 
                                                              |                            | 
                                                              |                            | 
                                                              |                            |  1. Lee Secreto 
                                                              |                            | 
                                                              v                            v 
                                                      +-------+--------+         +---------+-----------+ 
                                                      |                |         |                       | 
                                                      |   (Lógica de   |         |   Secret Manager      | 
                                                      |  Conversación) |         | (contiene tools.yaml) | 
                                                      |                |         |                       | 
                                                      +----------------+         +---------------------+ 
                                                                                           | 
                                                                                           | 2. Ejecuta Query 
                                                                                           | 
                                                                                           v 
                                                                                 +---------+-----------+ 
                                                                                 |                     | 
                                                                                 |  Google BigQuery    | 
                                                                                 |  (Datos de GA4)     | 
                                                                                 |                     | 
                                                                                 +---------------------+ 
```

---

## 4. Flujo de una Consulta (Paso a Paso)

Para entender cómo funciona el sistema, a continuación se detalla el flujo de datos y acciones desde que el usuario realiza una pregunta hasta que recibe una respuesta:

1.  **Entrada del Usuario**: Un usuario inicia una conversación en la interfaz de **Agentspace** con una pregunta, por ejemplo: `"¿Cuántas visitas diarias tuvimos la semana pasada?"`.

2.  **Procesamiento del Agente (ADK + Gemini)**: El Agente, desplegado en **Agent Engine**, recibe la pregunta desde Agentspace. Impulsado por el modelo **Gemini 2.5 Flash**, analiza la intención del usuario y determina que para responder, necesita consultar datos. Identifica que la herramienta más adecuada es `get_daily_visits`.

3.  **Llamada Segura al Servidor de Herramientas**: El Agente no accede directamente a la base de datos. En su lugar, realiza una llamada HTTPS segura al **Servidor de Herramientas (MCP Toolbox)**.

4.  **Ejecución en el Servidor de Herramientas**: El servidor MCP, desplegado en **Google Cloud Run en la región `us-central1`**, recibe la petición. Su configuración (almacenada de forma segura en **Google Secret Manager**) contiene la consulta SQL predefinida asociada a la herramienta `get_daily_visits`.

5.  **Consulta a BigQuery**: El servidor MCP, utilizando su propia identidad de servicio, ejecuta la consulta SQL contra la tabla de datos de GA4 en **Google BigQuery**.

6.  **Respuesta de BigQuery**: BigQuery procesa la consulta y devuelve los resultados (una tabla con fechas y número de visitas) al servidor MCP.

7.  **Retorno al Agente**: El servidor MCP reenvía los datos obtenidos al Agente.

8.  **Formulación de la Respuesta Final**: El Agente recibe los datos en formato estructurado. Vuelve a utilizar el modelo Gemini para interpretar estos datos y generar una respuesta coherente y en lenguaje natural, como: `"La semana pasada, las visitas diarias fueron las siguientes: Lunes - 1,234, Martes - 1,567..."`.

9.  **Entrega al Usuario**: El Agente envía la respuesta final a **Agentspace**, donde se muestra al usuario en la interfaz de chat.

---

## 5. Personalidad y Directrices del Agente (System Prompt)

El comportamiento del agente, su personalidad y sus limitaciones están estrictamente definidos por un "prompt de sistema". Este prompt instruye al modelo de IA sobre cómo debe actuar en todo momento. El prompt configurado para este agente es el siguiente:

> ```
> Eres un analista de marketing especializado en Google Analytics.
> Tu única función es responder a preguntas sobre los datos de Google Analytics a los que tienes acceso a través de tus herramientas.
> Eres claro y conciso en tus respuestas.
> No puedes responder a ninguna otra pregunta que no esté relacionada con Google Analytics.
> Si no puedes responder a una pregunta, simplemente di: 'No tengo acceso a esa información'.
> ```

Este enfoque garantiza que el agente se mantenga enfocado en su tarea, sea seguro y no derive en conversaciones o acciones no deseadas.

---

## 6. Modelo de Seguridad y Permisos

La seguridad es un pilar fundamental de esta arquitectura. Se implementa a través de un modelo de **mínimo privilegio** y la delegación de responsabilidades.

*   **Identidad del Agente**: Cuando se ejecuta, el agente se autentica a través de las Credenciales Predeterminadas de la Aplicación (ADC). Esto significa que no almacena claves ni contraseñas. Al desplegarse en Agent Engine, utiliza la identidad del servicio gestionado.

*   **Identidad Dedicada para Herramientas**: El componente más crítico es el **Servidor MCP Toolbox**, que tiene su propia **Cuenta de Servicio** de Google Cloud (`toolbox-identity@...`). Esta es la única identidad que tiene permiso para interactuar con BigQuery.

*   **Principio de Mínimo Privilegio**: La cuenta de servicio `toolbox-identity` tiene un único rol de IAM asignado: `roles/bigquery.jobUser`. Esto le otorga permiso **únicamente para ejecutar consultas en BigQuery**. No puede leer datos de otros servicios, no puede modificar tablas, ni tiene acceso a ninguna otra parte del proyecto de Google Cloud. El agente, por su parte, no tiene **ningún acceso directo** a la base de datos.

*   **Gestión Segura de Secretos**: La configuración de las herramientas, incluyendo las consultas SQL, no está escrita en el código del agente. Reside en un archivo (`tools.yaml`) que se almacena de forma segura en **Google Secret Manager**. El servidor MCP es el único que tiene permisos para leer este secreto en el momento de la ejecución.

### El Archivo de Configuración de Herramientas (`tools.yaml`)

Un elemento central de la seguridad y la gestión es el archivo `tools.yaml`. Este archivo define, de forma declarativa, todas las herramientas que el agente puede utilizar. Su contenido es el siguiente:

```yaml
sources:
 my-bq-source:
   kind: bigquery
   project: agentemarketing

tools:
 get_daily_visits:
   kind: bigquery-sql
   source: my-bq-source
   statement: |
    SELECT *
    FROM `bigquery-public-data.google_analytics_sample.daily_visits`
    LIMIT 5
   description: |
    Use this tool to get information on daily website visits from Google Analytics.

toolsets:
 my_bq_toolset:
   - get_daily_visits
```

**Desglose del archivo:**

*   `sources`: Define el origen de los datos. En este caso, `my-bq-source` apunta al proyecto de BigQuery `agentemarketing`.
*   `tools`: Define cada herramienta individual. 
    *   `get_daily_visits`: Es el nombre de nuestra herramienta.
    *   `description`: Este es el texto que el modelo Gemini utiliza para decidir cuándo usar esta herramienta. Es fundamental que sea claro y descriptivo.
    *   `statement`: Aquí reside la consulta SQL exacta que se ejecutará. **Crucialmente, la lógica SQL está aquí, fuera del código del agente**, lo que permite modificarla sin redesplegar el agente y previene inyecciones de SQL.
*   `toolsets`: Agrupa un conjunto de herramientas (`get_daily_visits`) bajo un nombre (`my_bq_toolset`). El agente solicita este `toolset` al servidor MCP para cargar las herramientas que puede utilizar.

Este diseño desacopla completamente la lógica de acceso a datos de la lógica de conversación del agente.

---

## 7. Componentes y Tecnologías Utilizadas

A continuación se presenta una lista de las tecnologías y servicios clave que componen la solución:

*   **Lenguaje de Programación**: Python 3.11
*   **Framework del Agente**: Google Agent Development Kit (ADK)
*   **Modelo de IA Generativa**: Google Gemini 2.5 Flash
*   **Plataforma Cloud**: Google Cloud Platform (GCP)
*   **Servicios Clave de GCP**:
    *   **Agentspace**: La interfaz de usuario web para la interacción final con el agente.
    *   **Agent Engine**: Como plataforma gestionada para desplegar y escalar el agente final.
    *   **Cloud Run**: Para el despliegue del Servidor de Herramientas (MCP Toolbox) como un microservicio sin estado, escalable y seguro. El servicio está desplegado en la región `us-central1`.
    *   **BigQuery**: Como almacén de datos para la analítica de GA4.
    *   **IAM (Identity and Access Management)**: Para la gestión granular de permisos y cuentas de servicio.
    *   **Secret Manager**: Para el almacenamiento seguro de la configuración de las herramientas.
    *   **Cloud Storage**: Utilizado como área de staging durante el proceso de despliegie.

---

## 8. Evaluación y Calidad del Agente

Para garantizar que el agente funcione como se espera y mantenga un alto nivel de calidad, el proyecto incluye un sistema de evaluación. Este sistema utiliza el propio ADK para ejecutar un conjunto de pruebas predefinidas.

*   **Conjunto de Evaluaciones (`Evalset`)**: Se ha creado un archivo llamado `basico.evalset.json` que contiene una serie de conversaciones de ejemplo. Cada conversación incluye una pregunta del usuario y la respuesta ideal esperada por parte del agente.

*   **Proceso de Prueba Automatizado**: Mediante un comando (`adk eval`), se pueden lanzar estas conversaciones contra el agente de forma automática. El sistema compara la respuesta real del agente con la respuesta ideal definida en el `evalset`.

*   **Garantía de Calidad**: Este proceso permite verificar rápidamente que los cambios en el código, el prompt o la configuración no hayan afectado negativamente el comportamiento del agente. Sirve como una red de seguridad para asegurar que el agente sigue siendo preciso, conciso y se adhiere a sus directrices.

---

## 9. Despliegue y Acceso

El agente está diseñado para ser desplegado en **Agent Engine**, la plataforma gestionada de Google Cloud para agentes.

El proceso de despliegue se realiza con un único comando que empaqueta el código del agente, lo sube a un bucket de Cloud Storage, crea una imagen de contenedor y la despliega en el servicio.

**Comando de Despliegue:**
```bash
adk deploy agent_engine --project=agentemarketing --region=us-central1 --staging_bucket=gs://agentemarketing-agent-engine-bucket --display_name="Agente_Marketing" agente_ga4/
```

Este comando automatiza todo el ciclo de vida del despliegue, asegurando un proceso repetible y fiable.

Una vez desplegado, el agente estará disponible para los usuarios finales a través de **Agentspace**, la interfaz de usuario proporcionada por Google para interactuar con los agentes alojados en Agent Engine.