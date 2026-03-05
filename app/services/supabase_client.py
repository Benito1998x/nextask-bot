"""
Cliente de Supabase para NexTask.

Encapsula las operaciones CRUD de tareas sobre la tabla 'tasks' en Supabase.
Usa el SDK síncrono de supabase-py (compatible con FastAPI via BackgroundTasks).
"""
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

TABLE_TASKS = "tasks"


class SupabaseOps:
    """
    Operaciones CRUD sobre la tabla de tareas en Supabase.

    Uso:
        from supabase import create_client
        client = create_client(settings.supabase_url, settings.supabase_key)
        ops = SupabaseOps(client)
        ops.create_task(titulo="Mi tarea", chat_id=12345)
    """

    def __init__(self, client: Any):
        self._client = client

    def create_task(
        self,
        titulo: str,
        chat_id: int,
        descripcion: str | None = None,
        prioridad: str = "media",
        fecha_limite: str | None = None,
        etiquetas: list[str] | None = None,
    ) -> dict | None:
        """Crea una nueva tarea y retorna la fila insertada."""
        row = {
            "titulo": titulo,
            "chat_id": chat_id,
            "status": "pendiente",
            "prioridad": prioridad,
        }
        if descripcion:
            row["descripcion"] = descripcion
        if fecha_limite:
            row["fecha_limite"] = fecha_limite
        if etiquetas:
            row["etiquetas"] = etiquetas

        try:
            response = self._client.table(TABLE_TASKS).insert(row).execute()
            if response.data:
                logger.info(f"Tarea creada: {response.data[0].get('id')}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error creando tarea: {e}", exc_info=True)
            return None

    def list_tasks(
        self,
        chat_id: int,
        status: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Lista las tareas de un usuario, opcionalmente filtradas por status."""
        try:
            query = self._client.table(TABLE_TASKS).select("*").eq("chat_id", chat_id)
            if status:
                query = query.eq("status", status)
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error listando tareas: {e}", exc_info=True)
            return []

    def update_task(
        self,
        task_id: str,
        **fields: Any,
    ) -> dict | None:
        """Actualiza campos de una tarea existente."""
        if not fields:
            return None

        try:
            response = (
                self._client.table(TABLE_TASKS)
                .update(fields)
                .eq("id", task_id)
                .execute()
            )
            if response.data:
                logger.info(f"Tarea actualizada: {task_id}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error actualizando tarea {task_id}: {e}", exc_info=True)
            return None

    def delete_task(self, task_id: str) -> bool:
        """Elimina una tarea por ID. Retorna True si se eliminó."""
        try:
            response = (
                self._client.table(TABLE_TASKS)
                .delete()
                .eq("id", task_id)
                .execute()
            )
            deleted = bool(response.data)
            if deleted:
                logger.info(f"Tarea eliminada: {task_id}")
            return deleted
        except Exception as e:
            logger.error(f"Error eliminando tarea {task_id}: {e}", exc_info=True)
            return False


def get_supabase_ops() -> SupabaseOps:
    """Factory: crea un SupabaseOps con las credenciales de settings."""
    from supabase import create_client
    client = create_client(settings.supabase_url, settings.supabase_key)
    return SupabaseOps(client)
