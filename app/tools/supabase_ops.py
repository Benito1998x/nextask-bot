"""
Supabase Ops Tool (Wrapper para el agente).

Enruta las llamadas del LLM al cliente Supabase real.
"""
from typing import Any
from app.tools.base import BaseTool
from app.services.supabase_client import get_supabase_ops


class SupabaseOpsTool(BaseTool):
    """
    Herramienta para que el agente administre las tareas en Supabase.
    Soporta operaciones CRUD a través del parámetro 'action'.
    """

    @property
    def name(self) -> str:
        return "supabase_ops"

    @property
    def description(self) -> str:
        return (
            "Úsala para administrar la lista de tareas del usuario en la base de datos Supabase. "
            "Acciones disponibles: 'list' (listar tareas pendientes o completadas), "
            "'create' (crear nueva tarea), 'update' (actualizar estado/título), "
            "'delete' (eliminar tarea)."
        )

    def get_schema(self) -> dict[str, Any]:
        """Schema OpenAPI para function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "action": {
                        "type": "STRING",
                        "description": "Acción a realizar: 'list', 'create', 'update', 'delete'",
                    },
                    "chat_id": {
                        "type": "INTEGER",
                        "description": "ID del chat de Telegram (obligatorio para 'list' y 'create')",
                    },
                    "titulo": {
                        "type": "STRING",
                        "description": "Título de la tarea (usado en 'create' y 'update')",
                    },
                    "descripcion": {
                        "type": "STRING",
                        "description": "Descripción detallada (opcional en 'create')",
                    },
                    "status": {
                        "type": "STRING",
                        "description": "Estado de la tarea (ej: 'pendiente', 'completada'). Usado en 'list' y 'update'.",
                    },
                    "task_id": {
                        "type": "STRING",
                        "description": "ID de la tarea en la base de datos (obligatorio para 'update' y 'delete')",
                    },
                },
                "required": ["action"],
            },
        }

    async def execute(self, **kwargs) -> Any:
        """Enruta la acción al método correspondiente."""
        action = kwargs.get("action")
        ops = get_supabase_ops()

        try:
            if action == "list":
                chat_id = kwargs.get("chat_id")
                status = kwargs.get("status")
                if not chat_id:
                    return {"error": "Falta chat_id para iterar list_tasks"}
                return ops.list_tasks(chat_id=chat_id, status=status)

            elif action == "create":
                chat_id = kwargs.get("chat_id")
                titulo = kwargs.get("titulo")
                if not chat_id or not titulo:
                    return {"error": "Falta chat_id o titulo para create_task"}
                return ops.create_task(
                    titulo=titulo,
                    chat_id=chat_id,
                    descripcion=kwargs.get("descripcion")
                )

            elif action == "update":
                task_id = kwargs.get("task_id")
                if not task_id:
                    return {"error": "Falta task_id para update_task"}
                
                # Campos a actualizar
                fields = {}
                if "status" in kwargs: fields["status"] = kwargs["status"]
                if "titulo" in kwargs: fields["titulo"] = kwargs["titulo"]
                
                return ops.update_task(task_id=task_id, **fields)

            elif action == "delete":
                task_id = kwargs.get("task_id")
                if not task_id:
                    return {"error": "Falta task_id para delete_task"}
                success = ops.delete_task(task_id=task_id)
                return {"success": success, "task_id": task_id}

            else:
                return {"error": f"Acción desconocida: {action}"}

        except Exception as e:
            return {"error": str(e)}
