"""
Cliente Notion para NexTask.

Escribe tareas y hallazgos en las bases de datos de Notion del usuario.
Usa la API oficial de Notion (notion-client).
"""
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class NotionWriter:
    """
    Escritor de páginas en Notion.

    Uso:
        from notion_client import Client
        client = Client(auth=settings.notion_api_key)
        writer = NotionWriter(client, db_tareas="...", db_hallazgos="...")
    """

    def __init__(
        self,
        client: Any,
        db_tareas: str = "",
        db_hallazgos: str = "",
    ):
        self._client = client
        self._db_tareas = db_tareas
        self._db_hallazgos = db_hallazgos

    def create_task_page(
        self,
        titulo: str,
        status: str = "pendiente",
        prioridad: str | None = None,
        descripcion: str | None = None,
    ) -> dict | None:
        """Crea una página de tarea en la DB de tareas de Notion."""
        properties: dict[str, Any] = {
            "Titulo": {"title": [{"text": {"content": titulo}}]},
            "Status": {"select": {"name": status}},
        }
        if prioridad:
            properties["Prioridad"] = {"select": {"name": prioridad}}

        children = []
        if descripcion:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": descripcion}}]
                },
            })

        try:
            page = self._client.pages.create(
                parent={"database_id": self._db_tareas},
                properties=properties,
                children=children,
            )
            logger.info(f"Página Notion creada: {page.get('id')}")
            return page
        except Exception as e:
            logger.error(f"Error creando página en Notion: {e}", exc_info=True)
            return None

    def create_hallazgo_page(
        self,
        titulo: str,
        contenido: str,
    ) -> dict | None:
        """Crea una página de hallazgo/descubrimiento en la DB de hallazgos."""
        properties: dict[str, Any] = {
            "Titulo": {"title": [{"text": {"content": titulo}}]},
        }
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": contenido}}]
                },
            }
        ]

        try:
            page = self._client.pages.create(
                parent={"database_id": self._db_hallazgos},
                properties=properties,
                children=children,
            )
            logger.info(f"Hallazgo Notion creado: {page.get('id')}")
            return page
        except Exception as e:
            logger.error(f"Error creando hallazgo en Notion: {e}", exc_info=True)
            return None


def get_notion_writer() -> NotionWriter:
    """Factory: crea NotionWriter con credenciales de settings."""
    from notion_client import Client
    client = Client(auth=settings.notion_api_key)
    return NotionWriter(
        client,
        db_tareas=settings.notion_db_tareas,
        db_hallazgos=settings.notion_db_hallazgos,
    )
