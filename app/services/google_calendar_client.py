"""
Cliente de Google Calendar para NexTask.

Usa la API REST de Google Calendar (google-api-python-client) para
listar, crear y eliminar eventos del calendario del usuario.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class GoogleCalendarOps:
    """
    Operaciones sobre Google Calendar.

    Uso:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file("token.json")
        service = build("calendar", "v3", credentials=creds)
        ops = GoogleCalendarOps(service, calendar_id="primary")
    """

    def __init__(self, service: Any, calendar_id: str):
        self._service = service
        self._calendar_id = calendar_id

    def list_today_events(self) -> list[dict]:
        """Lista los eventos del día de hoy."""
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        try:
            result = (
                self._service.events()
                .list(
                    calendarId=self._calendar_id,
                    timeMin=start_of_day.isoformat(),
                    timeMax=end_of_day.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = result.get("items", [])
            logger.info(f"Encontrados {len(events)} eventos hoy")
            return events
        except Exception as e:
            logger.error(f"Error listando eventos: {e}", exc_info=True)
            return []

    def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: str | None = None,
    ) -> dict | None:
        """
        Crea un evento en el calendario.

        Args:
            summary: Título del evento
            start_time: ISO 8601 (ej: 2026-03-06T10:00:00)
            end_time: ISO 8601
            description: Descripción opcional
        """
        event_body = {
            "summary": summary,
            "start": {"dateTime": start_time, "timeZone": "America/Caracas"},
            "end": {"dateTime": end_time, "timeZone": "America/Caracas"},
        }
        if description:
            event_body["description"] = description

        try:
            event = (
                self._service.events()
                .insert(calendarId=self._calendar_id, body=event_body)
                .execute()
            )
            logger.info(f"Evento creado: {event.get('id')} — {summary}")
            return event
        except Exception as e:
            logger.error(f"Error creando evento: {e}", exc_info=True)
            return None

    def delete_event(self, event_id: str) -> bool:
        """Elimina un evento por ID."""
        try:
            self._service.events().delete(
                calendarId=self._calendar_id, eventId=event_id
            ).execute()
            logger.info(f"Evento eliminado: {event_id}")
            return True
        except Exception as e:
            logger.error(f"Error eliminando evento {event_id}: {e}", exc_info=True)
            return False


def get_google_calendar_ops() -> GoogleCalendarOps:
    """Factory: crea GoogleCalendarOps con credenciales del token.json."""
    import json
    from pathlib import Path
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    token_path = Path(__file__).parent.parent.parent / "token.json"

    if not token_path.exists():
        raise FileNotFoundError(
            f"token.json no encontrado en {token_path}. "
            "Ejecuta: python scripts/google_auth.py"
        )

    creds = Credentials.from_authorized_user_file(
        str(token_path),
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    service = build("calendar", "v3", credentials=creds)
    return GoogleCalendarOps(service, calendar_id=settings.gcal_calendar_id)
