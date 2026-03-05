"""
Tests para Audio Transcription Tool — Ciclo TDD RED→GREEN→REFACTOR

Cubre: descarga de archivo de voz de Telegram, muestra de transcripción mock.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ==============================================================
# FIXTURES
# ==============================================================

@pytest.fixture
def mock_telegram_client():
    """Mock del TelegramClient para descargar archivos."""
    client = MagicMock()
    return client


# ==============================================================
# Tests: AudioTranscriber
# ==============================================================

class TestAudioTranscriberGetFileUrl:

    @pytest.mark.asyncio
    async def test_obtener_url_de_archivo(self):
        """
        Given un file_id válido de Telegram
        When se llama get_file_url
        Then retorna la URL de descarga del archivo
        """
        from app.services.audio_transcriber import AudioTranscriber

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={
                    "ok": True,
                    "result": {"file_path": "voice/file_123.ogg"}
                })
            )

            transcriber = AudioTranscriber(telegram_token="fake-token")
            url = await transcriber.get_file_url("file-id-123")

        assert url is not None
        assert "voice/file_123.ogg" in url


class TestAudioTranscriberTranscribe:

    @pytest.mark.asyncio
    async def test_transcribir_placeholder(self):
        """
        Given un file_id de voz
        When se llama transcribe (placeholder)
        Then retorna un mensaje indicando que la transcripción se procesó
        """
        from app.services.audio_transcriber import AudioTranscriber

        transcriber = AudioTranscriber(telegram_token="fake-token")

        with patch.object(transcriber, "get_file_url", new_callable=AsyncMock) as mock_url, \
             patch.object(transcriber, "_download_and_transcribe", new_callable=AsyncMock) as mock_transcribe:

            mock_url.return_value = "https://api.telegram.org/file/bot.../voice.ogg"
            mock_transcribe.return_value = "Hola, esto es una prueba de voz"

            result = await transcriber.transcribe("file-id-123")

        assert result == "Hola, esto es una prueba de voz"

    @pytest.mark.asyncio
    async def test_transcribir_error_retorna_mensaje_amigable(self):
        """
        Given un error al descargar el archivo
        When se llama transcribe
        Then retorna un mensaje de error amigable
        """
        from app.services.audio_transcriber import AudioTranscriber

        transcriber = AudioTranscriber(telegram_token="fake-token")

        with patch.object(transcriber, "get_file_url", new_callable=AsyncMock) as mock_url:
            mock_url.return_value = None

            result = await transcriber.transcribe("bad-file-id")

        assert "error" in result.lower() or "no pude" in result.lower()
