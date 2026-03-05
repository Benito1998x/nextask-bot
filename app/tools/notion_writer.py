"""
Notion Writer Tool (Wrapper para el agente).
"""
from typing import Any
from app.tools.base import BaseTool
from app.services.notion_client import get_notion_writer


class NotionWriterTool(BaseTool):
    """Herramienta para documentar en Notion."""

    @property
    def name(self) -> str:
        return "notion_writer"

    @property
    def description(self) -> str:
        return (
            "Úsala para escribir páginas en Notion. "
            "Acciones: 'create_task' (para tareas de largo plazo en la DB de proyectos), "
            "'create_hallazgo' (para anotar un hallazgo técnico, aprendizaje o nota importante)."
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
                        "description": "Acción: 'create_task' o 'create_hallazgo'",
                    },
                    "titulo": {
                        "type": "STRING",
                        "description": "Título de la página",
                    },
                    "contenido": {
                        "type": "STRING",
                        "description": "Descripción o contenido detallado",
                    },
                    "status": {
                        "type": "STRING",
                        "description": "Estado (solo para 'create_task')",
                    },
                },
                "required": ["action", "titulo", "contenido"],
            },
        }

    async def execute(self, **kwargs) -> Any:
        action = kwargs.get("action")
        titulo = kwargs.get("titulo")
        contenido = kwargs.get("contenido")

        if not titulo or not contenido:
             return {"error": "titulo y contenido son requeridos"}

        try:
            writer = get_notion_writer()
            if action == "create_task":
                page = writer.create_task_page(
                    titulo=titulo,
                    descripcion=contenido,
                    status=kwargs.get("status", "pendiente")
                )
                return {"success": True, "page_id": page.get("id") if page else None}

            elif action == "create_hallazgo":
                page = writer.create_hallazgo_page(
                    titulo=titulo,
                    contenido=contenido
                )
                return {"success": True, "page_id": page.get("id") if page else None}

            else:
                return {"error": f"Acción desconocida: {action}"}
        except Exception as e:
            return {"error": str(e)}
