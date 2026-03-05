"""
Tests para Google Calendar Sync Tool — Ciclo TDD RED→GREEN→REFACTOR

Cubre: listar eventos, crear evento, eliminar evento, manejo de errores.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


# ==============================================================
# FIXTURES
# ==============================================================

@pytest.fixture
def mock_gcal_service():
    """Mock del servicio Google Calendar API."""
    service = MagicMock()
    return service


@pytest.fixture
def sample_event():
    return {
        "id": "event-123",
        "summary": "Reunión con cliente",
        "start": {"dateTime": "2026-03-06T10:00:00-04:00"},
        "end": {"dateTime": "2026-03-06T11:00:00-04:00"},
        "status": "confirmed",
    }


# ==============================================================
# Tests: GoogleCalendarOps
# ==============================================================

class TestGoogleCalendarListEvents:

    def test_listar_eventos_del_dia(self, mock_gcal_service, sample_event):
        """
        Given un calendario con eventos
        When se llama list_today_events
        Then retorna los eventos del día formateados
        """
        from app.services.google_calendar_client import GoogleCalendarOps

        events_resource = mock_gcal_service.events.return_value
        events_resource.list.return_value.execute.return_value = {
            "items": [sample_event]
        }

        ops = GoogleCalendarOps(mock_gcal_service, calendar_id="test@gmail.com")
        result = ops.list_today_events()

        assert len(result) == 1
        assert result[0]["summary"] == "Reunión con cliente"

    def test_listar_sin_eventos(self, mock_gcal_service):
        """
        Given un calendario sin eventos
        When se llama list_today_events
        Then retorna lista vacía
        """
        from app.services.google_calendar_client import GoogleCalendarOps

        events_resource = mock_gcal_service.events.return_value
        events_resource.list.return_value.execute.return_value = {"items": []}

        ops = GoogleCalendarOps(mock_gcal_service, calendar_id="test@gmail.com")
        result = ops.list_today_events()

        assert result == []


class TestGoogleCalendarCreateEvent:

    def test_crear_evento_exitosamente(self, mock_gcal_service):
        """
        Given datos válidos de evento
        When se llama create_event
        Then inserta en el calendario y retorna el evento creado
        """
        from app.services.google_calendar_client import GoogleCalendarOps

        created = {
            "id": "new-event",
            "summary": "Nueva reunión",
            "htmlLink": "https://calendar.google.com/event?id=new-event",
        }
        events_resource = mock_gcal_service.events.return_value
        events_resource.insert.return_value.execute.return_value = created

        ops = GoogleCalendarOps(mock_gcal_service, calendar_id="test@gmail.com")
        result = ops.create_event(
            summary="Nueva reunión",
            start_time="2026-03-06T10:00:00",
            end_time="2026-03-06T11:00:00",
        )

        assert result is not None
        assert result["id"] == "new-event"


class TestGoogleCalendarDeleteEvent:

    def test_eliminar_evento_exitosamente(self, mock_gcal_service):
        """
        Given un event_id válido
        When se llama delete_event
        Then elimina el evento
        """
        from app.services.google_calendar_client import GoogleCalendarOps

        events_resource = mock_gcal_service.events.return_value
        events_resource.delete.return_value.execute.return_value = {}

        ops = GoogleCalendarOps(mock_gcal_service, calendar_id="test@gmail.com")
        result = ops.delete_event("event-123")

        assert result is True

    def test_eliminar_evento_error(self, mock_gcal_service):
        """
        Given un event_id inválido
        When se llama delete_event
        Then retorna False
        """
        from app.services.google_calendar_client import GoogleCalendarOps

        events_resource = mock_gcal_service.events.return_value
        events_resource.delete.return_value.execute.side_effect = Exception("Not found")

        ops = GoogleCalendarOps(mock_gcal_service, calendar_id="test@gmail.com")
        result = ops.delete_event("invalid-id")

        assert result is False
