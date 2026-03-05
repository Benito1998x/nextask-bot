# 🧠 NexTask AI Agent

**Documentación Técnica Definitiva — Marzo 2026**
*Desarrollado para: Asistente Bot Multi-Herramientas en Telegram.*

NexTask es un agente conversacional avanzado impulsado por **Gemini 2.5 Flash** diseñado para orquestar flujos de trabajo personales e integrarse de manera autónoma con ecosistemas de productividad clave (Supabase, Notion, Google Calendar) mediante el uso de la API de Telegram como interfaz (Front-End). 

El sistema utiliza *Function Calling* (Tool Use) para ejecutar operaciones de bases de datos, administración de agendamientos y gestión del conocimiento desde comandos de lenguaje natural o notas de voz transcritas en español neutro.

---

## 🏗️ Arquitectura del Sistema (Design)

La solución está construida sobre un patrón *Serverless Event-Driven* usando FastAPI (Asíncrono).

### 1. Capa de Recepción (Webhooks)
- **Telegram Bot API**: Actúa como el cliente/interfaz. Envía payloads JSON (updates) directamente a `/webhook` del servidor.
- **Transcriptor de Audio**: Si el payload contiene un archivo de tipo `voice`, el interceptor local descarga la nota de voz en formato OGG, la procesa (vía Simulación Whisper/Google Speech), transforma el audio a texto y transfiere el flujo a la capa del Agente.

### 2. Capa del Agente (Orquestador Core)
- **Google GenAI SDK**: Actualizado a la última biblioteca oficial (`google-genai` v1+).
- Se inyecta un System Prompt robusto con el rol estructurado de un asistente estoico y experto en finanzas y sistemas.
- El agente mantiene contexto ("memoria") obteniendo de **Redis** la conversación reciente del `chat_id`. Si Redis falla (TimeOut), el agente opera de forma *Stateless* con degradación elegante.

### 3. Capa de Tools (Function Calling)
El LLM tiene a disposición un esquema estricto (OpenAPI `FunctionDeclarations`). Cuando decide interactuar con alguna herramienta externa, invoca lógicamente los wrappers y el código Python se encarga de las ejecuciones HTTP Asíncronas:

| Tool Wrapper | Capacidad / Skill | Backend Operativo |
| --- | --- | --- |
| `SupabaseOpsTool` | Creación y actualización de tareas tipo Kanban. | **PostgreSQL** vía Supabase REST (`supabase-py`). |
| `GoogleCalendarTool` | Consultar agenda del día, crear/eliminar eventos. | Google Identity OAuth2 y Calendar v3 REST. |
| `NotionWriterTool` | Crear páginas con formato en múltiples bases y wikis. | Document Object Model de Notion (`notion-client`). |

---

## 🛠️ Stack Tecnológico (Vital Tools)

1. **Python 3.12+ (Backend Core):** Usado para asincronismo nativo (`asyncio`).
2. **FastAPI & Uvicorn:** Framework ligero para exponer el Endpoint del Webhook HTTP.
3. **Pydantic:** Validación estricta de esquemas de datos entrantes de Telegram y de las firmas de funciones de Gemini.
4. **Redis:** (Opcional en dev / OBLIGATORIO en Prod serverless). Capa de caché ultrarrápida para contexto de los chats (Chat History).
5. **Docker:** Motor de virtualización usado para empaquetar el ambiente en un OS `slim` predecible y mandarlo a la Nube.

---

## ⚙️ Skills (Capacidades del Sistema)

Como analista de ingeniería, se integraron estas *skills* autónomas:
- **Zero-Shot Task Translation:** Capacidad de entender que *"Recuérdame en media hora"* implica un cálculo matemático temporal para crear un evento en Google Calendar y no una insersión en Supabase.
- **Fail-Safe Processing:** El sistema no se traba si un servicio cae. (ej. Manejo de `ConnectionError` en `redis_session.py`).
- **Data Engineering (Mapeo O-R):** Traducción del esquema JSON del usuario a propiedades específicas de las bases de datos altamente estructuradas de Notion.

---

## 📝 Notas y Observaciones de Data Science / Ingeniería

### Observaciones Críticas del Entorno (Marzo 2026)
1. **Gemini SDK Deprecation:** Google deprecó la biblioteca antigua `google.generativeai` y restringió el modelo `gemini-2.0-flash` para nuevos "Free Tiers". El sistema reaccionó mudando toda la infraestructura a `google-genai` para habilitar **Gemini 2.5 Flash**, que ofrece latencias más bajas y capacidades de *tooling* nativas.
2. **Seguridad de Secretos (CI/CD):** Se implementó *Push Protection*. GitHub prohibió intentos de subir repositorios donde existían filtraciones pasivas en archivos `.env.example`. El sistema maneja variables ambientales limpias.

### Oportunidades de Mejora / Siguientes Pasos (Technical Debt)
1. **Reconocimiento de Audio Original:** Actualmente el sistema simula transcripciones si la API de reconocimiento falla. Conectarlo definitivamente a Whisper de OpenAI o Speech-to-Text integrado de Gemini Multimodal mejoraría la eficiencia del análisis de voz de los usuarios al 100%.
2. **Latencia del Cold-Start:** Si se despliega en Cloud Run / Render, la primera interacción tras horas de inactividad tardará ~20 segundos en "despertar" el contenedor local y reconstruir el cliente Redis.
3. **Observabilidad (Logging Nube):** Conectar los logs actuales de Python a Google Cloud Logging, Datadog o Sentry para medir la tasa de éxito de las "infracciones de System Prompt" (alucinaciones del Agente).
