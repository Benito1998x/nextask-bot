"""
NexTask Agent — FastAPI Application

Endpoints:
- GET  /healthz           ← Health check para Cloud Run
- POST /webhook           ← Webhook de Telegram (mensajes entrantes)
- POST /scheduler/{event} ← Triggers de Cloud Scheduler
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings
from app.services.telegram_client import TelegramClient, parse_telegram_update
from app.services.redis_session import RedisSession

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

VALID_SCHEDULER_EVENTS = {"morning_checkin", "confrontacion", "weekly_report"}

from app.agent.core import NexTaskAgent
from app.tools.supabase_ops import SupabaseOpsTool
from app.tools.google_calendar import GoogleCalendarTool
from app.tools.notion_writer import NotionWriterTool
from app.services.audio_transcriber import get_audio_transcriber

# Singletons de servicios — se inicializan en lifespan
telegram_client: TelegramClient | None = None
redis_session: RedisSession | None = None
agent: NexTaskAgent | None = None
audio_transcriber = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: inicialización y cierre de recursos."""
    global telegram_client, redis_session, agent

    logger.info(f"🚀 NexTask iniciando — entorno: {settings.app_env}")

    # Inicializar cliente de Telegram
    telegram_client = TelegramClient(token=settings.telegram_bot_token)
    bot_info = await telegram_client.get_me()
    if bot_info:
        logger.info(f"🤖 Bot conectado: @{bot_info.get('username')}")
    else:
        logger.warning("⚠️ No se pudo verificar el token de Telegram")

    # Inicializar sesión Redis
    redis_session = RedisSession()
    
    # Inicializar Audio Transcriber
    global audio_transcriber
    audio_transcriber = get_audio_transcriber()

    # Inicializar NexTaskAgent (Sprint 4) con todas sus Tools
    global agent
    agent = NexTaskAgent(tools=[
        SupabaseOpsTool(),
        GoogleCalendarTool(),
        NotionWriterTool(),
        # telegram_client se maneja directamente aquí en main
        # audio_transcriber se maneja en pre-proceso aquí
    ])
    logger.info("🧠 NexTaskAgent online con todas las tools integradas")

    yield

    logger.info("🛑 NexTask apagando...")


app = FastAPI(
    title="NexTask Agent",
    description="Agente de IA en Telegram para gestión de tareas y agenda",
    version="0.1.0",
    lifespan=lifespan,
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/healthz", tags=["infra"])
async def health_check():
    """Health check para Cloud Run / load balancer."""
    return {"status": "ok", "service": "nextask", "env": settings.app_env}


# ============================================================
# TELEGRAM WEBHOOK
# ============================================================

async def _process_telegram_update(payload: dict) -> None:
    """
    BackgroundTask: procesa el update de Telegram de forma asíncrona.

    ADR-02: Respondemos HTTP 200 de inmediato a Telegram para evitar
    timeouts y reintentos. El procesamiento ocurre aquí, en background.
    """
    msg = parse_telegram_update(payload)
    if msg is None:
        logger.debug("Update ignorado — no es texto ni voz")
        return

    chat_id = msg.chat_id
    logger.info(f"Procesando mensaje | chat_id={chat_id} | voice={msg.is_voice}")

    # ── Mensaje de VOZ ──
    if msg.is_voice:
        logger.info(f"🎤 Procesando voz: file_id={msg.file_id}")
        if telegram_client:
            await telegram_client.send_message(
                chat_id=chat_id,
                text="🎧 _Descargando nota de voz..._"
            )
        
        # Extraer texto del audio
        transcription = await audio_transcriber.transcribe(msg.file_id) if audio_transcriber else ""
        if not transcription or "No pude" in transcription:
            if telegram_client:
                await telegram_client.send_message(
                    chat_id=chat_id, text=f"⚠️ Error de transcripción: {transcription}"
                )
            return

        # Modificamos el texto del mensaje para que el Agente lo procese
        msg.text = f"[Voz Transcrita]: {transcription}"
        
        if telegram_client:
            await telegram_client.send_message(
                chat_id=chat_id,
                text=f"🗣️ _{transcription}_"
            )

    # ── Mensaje Hacia el Agente ──
    if not agent:
        # Agent no inicializado, responder con placeholder
        if telegram_client:
            await telegram_client.send_message(
                chat_id=chat_id,
                text=f"✅ Recibí tu mensaje: _{msg.text}_\n\n⚙️ El agente está en configuración, pronto estará operativo.",
            )
        return

    # Con agent inicializado (Sprint 4+)
    try:
        history = await redis_session.get_history(chat_id) if redis_session else []
        response_text = await agent.process_message(
            chat_id=chat_id,
            text=msg.text,
            history=history,
        )
        # Guardar mensajes en historial
        if redis_session:
            await redis_session.append_message(chat_id, "user", msg.text)
            await redis_session.append_message(chat_id, "model", response_text)

        if telegram_client:
            await telegram_client.send_message(chat_id=chat_id, text=response_text)

    except Exception as e:
        logger.error(f"Error procesando mensaje de chat_id={chat_id}: {e}", exc_info=True)
        if telegram_client:
            await telegram_client.send_message(
                chat_id=chat_id,
                text="⚠️ Hubo un error procesando tu mensaje. Intenta de nuevo.",
            )


@app.post("/webhook", tags=["telegram"])
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Recibe updates de Telegram via Webhook.

    Retorna HTTP 200 OK inmediatamente (ADR-02).
    El procesamiento real ocurre en BackgroundTasks.
    """
    try:
        body = await request.json()
        logger.debug(f"Webhook recibido: update_id={body.get('update_id', 'unknown')}")
        background_tasks.add_task(_process_telegram_update, body)
        return {"ok": True}

    except Exception as e:
        logger.error(f"Error parseando webhook: {e}", exc_info=True)
        # Retornar 200 de todos modos — si retornamos 5xx, Telegram reintentará
        return {"ok": True}


# ============================================================
# CLOUD SCHEDULER
# ============================================================

@app.post("/scheduler/{event_type}", tags=["scheduler"])
async def scheduler_trigger(event_type: str, chat_id: int):
    """
    Recibe triggers proactivos de Cloud Scheduler.

    Eventos válidos:
    - morning_checkin: Resumen matutino de tareas
    - confrontacion:   Recordatorio de tareas pendientes
    - weekly_report:   Reporte semanal de progreso
    
    URL param: ?chat_id=123456
    """
    if event_type not in VALID_SCHEDULER_EVENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Evento inválido. Válidos: {VALID_SCHEDULER_EVENTS}"
        )

    logger.info(f"🕐 Scheduler trigger: {event_type} para chat_id: {chat_id}")

    if not agent:
        logger.warning("Agent no inicializado para scheduler")
        return {"ok": False, "error": "Agent not initialized"}

    try:
        response_text = await agent.process_scheduler_event(event_type, chat_id)
        
        # Enviar por Telegram de forma proactiva
        if telegram_client:
            await telegram_client.send_message(chat_id=chat_id, text=response_text)
            
        return {"ok": True, "event": event_type, "status": "processed"}
    except Exception as e:
        logger.error(f"Error en scheduler: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"}
    )
