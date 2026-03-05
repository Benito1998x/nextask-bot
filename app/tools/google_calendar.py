"""
Google Calendar Tool (Wrapper para el agente).
"""
from typing import Any
from app.tools.base import BaseTool
from app.services.google_calendar_client import get_google_calendar_ops


class GoogleCalendarTool(BaseTool):
    """Herramienta para administrar Google Calendar."""

    @property
    def name(self) -> str:
        return "google_calendar"

    @property
    def description(self) -> str:
        return (
            "Úsala para interactuar con Google Calendar. "
            "Acciones: 'list_today' (para ver la agenda del día), "
            "'create' (para agendar evento), 'delete' (para eliminar)."
        )

    def get_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "action": {
                        "type": "STRING",
                        "description": "Acción: 'list_today', 'create', 'delete'",
                    },
                    "summary": {
                        "type": "STRING",
                        "description": "Título del evento (para 'create')",
                    },
                    "start_time": {
                        "type": "STRING",
                        "description": "Inicio ISO 8601 (ej '2026-03-06T10:00:00') (para 'create')",
                    },
                    "end_time": {
                        "type": "STRING",
                        "description": "Fin ISO 8601 (para 'create')",
                    },
                    "event_id": {
                        "type": "STRING",
                        "description": "ID del evento (para 'delete')",
                    },
                },
                "required": ["action"],
            },
        }

    async def execute(self, **kwargs) -> Any:
        action = kwargs.get("action")
        try:
            ops = get_google_calendar_ops()
        except FileNotFoundError as e:
            return {"error": str(e)} # Token no existe

        if action == "list_today":
            return ops.list_today_events()

        elif action == "create":
            summary = kwargs.get("summary")
            start = kwargs.get("start_time")
            end = kwargs.get("end_time")
            if not all([summary, start, end]):
                return {"error": "summary, start_time y end_time requeridos para create"}
            return ops.create_event(summary=summary, start_time=start, end_time=end)

        elif action == "delete":
            event_id = kwargs.get("event_id")
            if not event_id:
                return {"error": "event_id requerido para delete"}
            return {"success": ops.delete_event(event_id)}

        else:
            return {"error": f"Acción desconocida: {action}"}
