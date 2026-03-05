"""
Fixtures compartidas para los tests de NexTask.
Todas las fixtures aquí se reutilizan en múltiples archivos de test.
"""
import os
import pytest
from unittest.mock import patch


# ============================================================
# ENVIRONMENT MOCK — siempre activo (autouse)
# ============================================================
@pytest.fixture(autouse=True)
def mock_env_vars():
    """
    Sobreescribe variables de entorno en TODOS los tests.
    Garantiza que nunca se usen credenciales reales en tests.
    """
    env_overrides = {
        "GEMINI_API_KEY": "test-gemini-key-fake",
        "GEMINI_MODEL": "gemini-2.0-flash",
        "TELEGRAM_BOT_TOKEN": "1234567890:AAFake-Test-Token",
        "SUPABASE_URL": "https://test-project.supabase.co",
        "SUPABASE_KEY": "test-supabase-anon-key-fake",
        "NOTION_API_KEY": "secret_test_notion_key_fake",
        "NOTION_DB_TAREAS": "test-db-tareas-id",
        "NOTION_DB_HALLAZGOS": "test-db-hallazgos-id",
        "NOTION_DB_CONFIG": "test-db-config-id",
        "NOTION_DB_AGENDA": "test-db-agenda-id",
        "GCAL_CALENDAR_ID": "test@group.calendar.google.com",
        "REDIS_URL": "redis://localhost:6379",
        "SESSION_TTL_SECONDS": "86400",
        "APP_ENV": "test",
        "LOG_LEVEL": "ERROR",  # Silenciar logs en tests
    }
    with patch.dict(os.environ, env_overrides, clear=False):
        yield
