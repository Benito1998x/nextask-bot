"""
Tests para Notion API Writer — Ciclo TDD RED→GREEN→REFACTOR

Cubre: creación de páginas en DB de tareas y hallazgos.
"""
import pytest
from unittest.mock import MagicMock


# ==============================================================
# FIXTURES
# ==============================================================

@pytest.fixture
def mock_notion_client():
    """Mock del cliente Notion."""
    client = MagicMock()
    return client


@pytest.fixture
def sample_page_response():
    return {
        "id": "page-uuid-123",
        "url": "https://notion.so/page-uuid-123",
        "properties": {
            "Titulo": {"title": [{"text": {"content": "Tarea de ejemplo"}}]}
        },
    }


# ==============================================================
# Tests: NotionWriter
# ==============================================================

class TestNotionWriterCreateTask:

    def test_crear_tarea_en_notion(self, mock_notion_client, sample_page_response):
        """
        Given datos de una tarea
        When se llama create_task_page
        Then crea una página en la DB de tareas de Notion
        """
        from app.services.notion_client import NotionWriter

        mock_notion_client.pages.create.return_value = sample_page_response

        writer = NotionWriter(mock_notion_client, db_tareas="db-tareas-id")
        result = writer.create_task_page(
            titulo="Tarea de ejemplo",
            status="pendiente",
            prioridad="media",
        )

        assert result is not None
        assert result["id"] == "page-uuid-123"
        mock_notion_client.pages.create.assert_called_once()

    def test_crear_tarea_con_error(self, mock_notion_client):
        """
        Given un error de la API de Notion
        When se llama create_task_page
        Then retorna None
        """
        from app.services.notion_client import NotionWriter

        mock_notion_client.pages.create.side_effect = Exception("API Error")

        writer = NotionWriter(mock_notion_client, db_tareas="db-tareas-id")
        result = writer.create_task_page(titulo="Falla", status="pendiente")

        assert result is None


class TestNotionWriterCreateHallazgo:

    def test_crear_hallazgo_en_notion(self, mock_notion_client, sample_page_response):
        """
        Given texto de un hallazgo
        When se llama create_hallazgo_page
        Then crea una página en la DB de hallazgos
        """
        from app.services.notion_client import NotionWriter

        mock_notion_client.pages.create.return_value = sample_page_response

        writer = NotionWriter(
            mock_notion_client,
            db_tareas="db-tareas-id",
            db_hallazgos="db-hallazgos-id",
        )
        result = writer.create_hallazgo_page(
            titulo="Hallazgo importante",
            contenido="Detalle del hallazgo",
        )

        assert result is not None
        mock_notion_client.pages.create.assert_called_once()
