"""
Tests para Supabase Ops Tool — Ciclo TDD RED→GREEN→REFACTOR

Cubre CRUD completo de tareas usando mocks del cliente Supabase.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.models.schemas import TaskCreate, TaskUpdate, TaskStatus, TaskPriority


# ==============================================================
# FIXTURES
# ==============================================================

@pytest.fixture
def mock_supabase():
    """Mock del cliente Supabase con tabla 'tasks'."""
    client = MagicMock()
    table = MagicMock()
    client.table.return_value = table
    return client, table


@pytest.fixture
def sample_task_row():
    return {
        "id": "uuid-123",
        "titulo": "Revisar propuesta",
        "descripcion": "Revisar la propuesta del cliente",
        "status": "pendiente",
        "prioridad": "media",
        "fecha_limite": None,
        "etiquetas": ["trabajo"],
        "chat_id": 12345,
        "created_at": "2026-03-05T10:00:00",
        "updated_at": "2026-03-05T10:00:00",
    }


# ==============================================================
# Tests: SupabaseOps
# ==============================================================

class TestSupabaseOpsCreateTask:

    def test_crear_tarea_exitosamente(self, mock_supabase, sample_task_row):
        """
        Given datos válidos de tarea
        When se llama create_task
        Then inserta en la tabla 'tasks' y retorna la tarea creada
        """
        from app.services.supabase_client import SupabaseOps

        client, table = mock_supabase
        # Simular respuesta de Supabase
        table.insert.return_value.execute.return_value.data = [sample_task_row]

        ops = SupabaseOps(client)
        result = ops.create_task(
            titulo="Revisar propuesta",
            chat_id=12345,
            descripcion="Revisar la propuesta del cliente",
            prioridad="media",
        )

        assert result is not None
        assert result["titulo"] == "Revisar propuesta"
        assert result["chat_id"] == 12345
        table.insert.assert_called_once()


class TestSupabaseOpsListTasks:

    def test_listar_tareas_por_chat_id(self, mock_supabase, sample_task_row):
        """
        Given tareas existentes para un chat_id
        When se llama list_tasks
        Then retorna todas las tareas del usuario
        """
        from app.services.supabase_client import SupabaseOps

        client, table = mock_supabase
        table.select.return_value.eq.return_value.execute.return_value.data = [sample_task_row]

        ops = SupabaseOps(client)
        result = ops.list_tasks(chat_id=12345)

        assert len(result) == 1
        assert result[0]["titulo"] == "Revisar propuesta"

    def test_listar_tareas_filtradas_por_status(self, mock_supabase, sample_task_row):
        """
        Given un filtro de status
        When se llama list_tasks con status="pendiente"
        Then retorna solo las tareas con ese status
        """
        from app.services.supabase_client import SupabaseOps

        client, table = mock_supabase
        chain = table.select.return_value.eq.return_value.eq.return_value
        chain.execute.return_value.data = [sample_task_row]

        ops = SupabaseOps(client)
        result = ops.list_tasks(chat_id=12345, status="pendiente")

        assert len(result) == 1


class TestSupabaseOpsUpdateTask:

    def test_actualizar_tarea_exitosamente(self, mock_supabase, sample_task_row):
        """
        Given un task_id válido
        When se llama update_task con nuevos datos
        Then actualiza la fila en Supabase
        """
        from app.services.supabase_client import SupabaseOps

        client, table = mock_supabase
        updated = {**sample_task_row, "status": "completada"}
        table.update.return_value.eq.return_value.execute.return_value.data = [updated]

        ops = SupabaseOps(client)
        result = ops.update_task("uuid-123", status="completada")

        assert result is not None
        assert result["status"] == "completada"


class TestSupabaseOpsDeleteTask:

    def test_eliminar_tarea_exitosamente(self, mock_supabase):
        """
        Given un task_id válido
        When se llama delete_task
        Then elimina la fila de Supabase
        """
        from app.services.supabase_client import SupabaseOps

        client, table = mock_supabase
        table.delete.return_value.eq.return_value.execute.return_value.data = [{"id": "uuid-123"}]

        ops = SupabaseOps(client)
        result = ops.delete_task("uuid-123")

        assert result is True

    def test_eliminar_tarea_inexistente(self, mock_supabase):
        """
        Given un task_id que no existe
        When se llama delete_task
        Then retorna False
        """
        from app.services.supabase_client import SupabaseOps

        client, table = mock_supabase
        table.delete.return_value.eq.return_value.execute.return_value.data = []

        ops = SupabaseOps(client)
        result = ops.delete_task("uuid-inexistente")

        assert result is False
