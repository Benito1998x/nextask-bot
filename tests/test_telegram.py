"""
Tests para la integración de Telegram — Ciclo TDD Red→Green→Refactor

Cubre:
- T-01: Parseo de TelegramUpdate JSON a AgentMessage
- T-02: TelegramClient.send_message
- T-05: Webhook endpoint integration
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.schemas import AgentMessage
from app.services.telegram_client import TelegramClient, parse_telegram_update


# ==============================================================
# FIXTURES
# ==============================================================

@pytest.fixture
def telegram_text_update() -> dict:
    """Payload real de Telegram para un mensaje de texto."""
    return {
        "update_id": 123456789,
        "message": {
            "message_id": 42,
            "from": {"id": 99, "is_bot": False, "first_name": "Ricardo"},
            "chat": {"id": 12345, "type": "private"},
            "date": 1700000000,
            "text": "Hola agente"
        }
    }


@pytest.fixture
def telegram_voice_update() -> dict:
    """Payload real de Telegram para un mensaje de voz."""
    return {
        "update_id": 123456790,
        "message": {
            "message_id": 43,
            "from": {"id": 99, "is_bot": False, "first_name": "Ricardo"},
            "chat": {"id": 12345, "type": "private"},
            "date": 1700000001,
            "voice": {
                "file_id": "AwACAgIAAxkBAAI_FAKE_FILE_ID",
                "duration": 3,
                "mime_type": "audio/ogg"
            }
        }
    }


@pytest.fixture
def malformed_update() -> dict:
    """Payload sin campo 'message'."""
    return {"update_id": 123456791}


@pytest.fixture
def telegram_client() -> TelegramClient:
    """Instancia del cliente con token falso."""
    return TelegramClient(token="1234567890:AAFakeToken")


# ==============================================================
# T-01: Parseo de TelegramUpdate
# ==============================================================

class TestParseTelegramUpdate:

    def test_parseo_mensaje_texto_exitosamente(self, telegram_text_update):
        """
        Escenario 1: Happy Path — mensaje de texto.
        Given un Update JSON de Telegram con campo 'message.text'
        When se llama a parse_telegram_update
        Then retorna AgentMessage con chat_id, text y is_voice=False
        """
        result = parse_telegram_update(telegram_text_update)

        assert result is not None
        assert isinstance(result, AgentMessage)
        assert result.chat_id == 12345
        assert result.text == "Hola agente"
        assert result.message_id == 42
        assert result.is_voice is False
        assert result.file_id is None

    def test_parseo_mensaje_voz_correctamente(self, telegram_voice_update):
        """
        Escenario 2: Edge Case — mensaje de voz.
        Given un Update JSON de Telegram con campo 'message.voice'
        When se llama a parse_telegram_update
        Then retorna AgentMessage con is_voice=True y file_id
        """
        result = parse_telegram_update(telegram_voice_update)

        assert result is not None
        assert isinstance(result, AgentMessage)
        assert result.chat_id == 12345
        assert result.is_voice is True
        assert result.file_id == "AwACAgIAAxkBAAI_FAKE_FILE_ID"
        assert result.text == ""  # Los mensajes de voz no tienen texto

    def test_parseo_retorna_none_si_payload_malformado(self, malformed_update):
        """
        Escenario 4: Error Case — payload sin 'message'.
        Given un Update JSON sin campo 'message'
        When se llama a parse_telegram_update
        Then retorna None
        """
        result = parse_telegram_update(malformed_update)
        assert result is None

    def test_parseo_retorna_none_si_message_sin_texto_ni_voz(self):
        """
        Edge Case — mensaje que no es texto ni voz (ej. sticker).
        """
        update = {
            "update_id": 999,
            "message": {
                "message_id": 44,
                "chat": {"id": 12345, "type": "private"},
                "sticker": {"file_id": "sticker_id"}
            }
        }
        result = parse_telegram_update(update)
        assert result is None


# ==============================================================
# T-02: TelegramClient.send_message
# ==============================================================

class TestTelegramClientSendMessage:

    @pytest.mark.asyncio
    async def test_send_message_exitoso(self, telegram_client):
        """
        Escenario 1: Happy Path — envío exitoso.
        Given un token válido y un chat_id válido
        When se llama a send_message
        Then realiza POST a la API y retorna True
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await telegram_client.send_message(
                chat_id=12345,
                text="Hola desde NexTask"
            )

        assert result is True
        mock_post.assert_called_once()

        # Verificar que se enviaron los parámetros correctos
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["json"]["chat_id"] == 12345
        assert call_kwargs["json"]["text"] == "Hola desde NexTask"
        assert call_kwargs["json"]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_telegram_client_maneja_token_invalido(self, telegram_client):
        """
        Escenario 3: Error Case — token inválido (HTTP 401).
        Given un token de Telegram inválido
        When send_message hace POST a la API
        Then retorna False sin lanzar excepción al exterior
        """
        import httpx

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "Unauthorized",
                request=MagicMock(),
                response=MagicMock(status_code=401)
            )
            result = await telegram_client.send_message(
                chat_id=12345,
                text="Test"
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_red_de_error_de_red(self, telegram_client):
        """
        Edge Case — fallo de red (timeout).
        Given un error de red
        When send_message intenta conectarse
        Then retorna False sin lanzar excepción al exterior
        """
        import httpx

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")
            result = await telegram_client.send_message(
                chat_id=12345,
                text="Test timeout"
            )

        assert result is False


# ==============================================================
# T-05: Webhook Endpoint integration
# ==============================================================

class TestWebhookEndpoint:

    @pytest.mark.asyncio
    async def test_webhook_procesa_mensaje_texto_exitosamente(self):
        """
        Escenario 1: Happy Path — webhook recibe texto y responde 200 inmediatamente.
        """
        from fastapi.testclient import TestClient
        from unittest.mock import patch

        update_payload = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "chat": {"id": 12345, "type": "private"},
                "text": "hola"
            }
        }

        with patch("app.main.agent") as mock_agent, \
             patch("app.main.telegram_client") as mock_tg, \
             patch("app.main.redis_session"):

            mock_agent.process_message = AsyncMock(return_value="ok")
            mock_tg.send_message = AsyncMock(return_value=True)

            from app.main import app
            client = TestClient(app)
            response = client.post("/webhook", json=update_payload)

        assert response.status_code == 200
        assert response.json() == {"ok": True}

    @pytest.mark.asyncio
    async def test_webhook_ignora_payload_malformado(self):
        """
        Escenario 4: Error Case — payload sin 'message', debe retornar 200 de todas formas.
        """
        from fastapi.testclient import TestClient

        with patch("app.main.agent"), \
             patch("app.main.telegram_client"), \
             patch("app.main.redis_session"):

            from app.main import app
            client = TestClient(app)
            response = client.post("/webhook", json={"update_id": 999})

        assert response.status_code == 200
