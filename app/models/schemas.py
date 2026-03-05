"""
Schemas Pydantic de NexTask.

Todos los modelos de datos del proyecto.
Se irán agregando a medida que se implementan las Tools.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ============================================================
# ENUMS
# ============================================================

class TaskStatus(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


class TaskPriority(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"


# ============================================================
# TASK MODELS
# ============================================================

class TaskCreate(BaseModel):
    """Datos para crear una nueva tarea."""
    titulo: str = Field(..., min_length=1, max_length=500)
    descripcion: str | None = Field(None, max_length=2000)
    fecha_limite: datetime | None = None
    prioridad: TaskPriority = TaskPriority.MEDIA
    etiquetas: list[str] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Datos para actualizar una tarea existente (todos opcionales)."""
    titulo: str | None = Field(None, min_length=1, max_length=500)
    descripcion: str | None = None
    status: TaskStatus | None = None
    fecha_limite: datetime | None = None
    prioridad: TaskPriority | None = None
    etiquetas: list[str] | None = None


class Task(BaseModel):
    """Tarea completa tal como se almacena en Supabase."""
    id: str
    titulo: str
    descripcion: str | None = None
    status: TaskStatus = TaskStatus.PENDIENTE
    prioridad: TaskPriority = TaskPriority.MEDIA
    fecha_limite: datetime | None = None
    etiquetas: list[str] = Field(default_factory=list)
    chat_id: int | None = None  # ID del chat de Telegram
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ============================================================
# AGENT / WEBHOOK MODELS
# ============================================================

class AgentMessage(BaseModel):
    """Mensaje procesado del agente."""
    chat_id: int
    text: str
    message_id: int | None = None
    is_voice: bool = False
    file_id: str | None = None  # Para mensajes de voz


class AgentResponse(BaseModel):
    """Respuesta que el agente enviará al usuario."""
    text: str
    chat_id: int
    parse_mode: str = "Markdown"


# ============================================================
# SCHEDULER MODELS
# ============================================================

class SchedulerEvent(BaseModel):
    """Evento proveniente de Cloud Scheduler."""
    event_type: str  # morning_checkin | confrontacion | weekly_report
    timestamp: datetime | None = None
