from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Configuración central de NexTask.
    Todos los valores se leen desde .env automáticamente.
    """

    # Google AI
    gemini_api_key: str = Field(..., description="API key de Google Gemini")
    gemini_model: str = Field("gemini-2.5-flash", description="Modelo Gemini a usar")

    # Telegram
    telegram_bot_token: str = Field(..., description="Token del bot de Telegram")

    # Supabase
    supabase_url: str = Field(..., description="URL del proyecto Supabase")
    supabase_key: str = Field(..., description="Anon key de Supabase")

    # Notion
    notion_api_key: str = Field(..., description="Integration token de Notion")
    notion_db_tareas: str = Field("", description="ID de la DB de tareas en Notion")
    notion_db_hallazgos: str = Field("", description="ID de la DB de hallazgos")
    notion_db_config: str = Field("", description="ID de la DB de configuración")
    notion_db_agenda: str = Field("", description="ID de la DB de agenda")

    # Google Calendar
    gcal_calendar_id: str = Field("", description="ID del calendario de Google")

    # Redis
    redis_url: str = Field("redis://localhost:6379", description="URL de Redis")
    session_ttl_seconds: int = Field(86400, description="TTL de sesión en segundos (24h)")

    # App
    app_env: str = Field("development", description="Entorno: development | production")
    log_level: str = Field("INFO", description="Nivel de logs")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Instancia singleton — importar desde aquí en todo el proyecto
settings = Settings()
