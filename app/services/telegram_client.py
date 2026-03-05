"""
Cliente de Telegram para NexTask.

Responsabilidades:
1. parse_telegram_update(): parsear el JSON entrante de Telegram → AgentMessage
2. TelegramClient: encapsular el envío de mensajes via httpx AsyncClient

ADR-01: Usamos httpx puro (no python-telegram-bot) para máximo control y rendimiento.
"""
import logging
from typing import Any

import httpx

from app.models.schemas import AgentMessage

logger = logging.getLogger(__name__)


# ============================================================
# FUNCIONES DE PARSEO
# ============================================================

def parse_telegram_update(payload: dict[str, Any]) -> AgentMessage | None:
    """
    Parsea un Telegram Update JSON y retorna un AgentMessage normalizado.

    Soporta:
    - Mensajes de texto (message.text)
    - Mensajes de voz (message.voice)

    Retorna None para updates sin mensaje o con tipos no soportados
    (stickers, imágenes, etc.).
    """
    message = payload.get("message") or payload.get("edited_message")
    if not message:
        logger.debug(f"Update sin 'message': update_id={payload.get('update_id')}")
        return None

    chat_id: int = message.get("chat", {}).get("id")
    message_id: int = message.get("message_id")

    if not chat_id:
        logger.warning("Update sin chat_id, ignorando")
        return None

    # ── Mensaje de TEXTO ──────────────────────────────────
    if text := message.get("text"):
        return AgentMessage(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            is_voice=False,
        )

    # ── Mensaje de VOZ ────────────────────────────────────
    if voice := message.get("voice"):
        file_id = voice.get("file_id", "")
        return AgentMessage(
            chat_id=chat_id,
            message_id=message_id,
            text="",  # Se llenará con la transcripción
            is_voice=True,
            file_id=file_id,
        )

    # Tipo no soportado (sticker, imagen, etc.)
    logger.debug(f"Tipo de mensaje no soportado en chat={chat_id}")
    return None


# ============================================================
# CLIENTE HTTP
# ============================================================

class TelegramClient:
    """
    Cliente asíncrono para la API de Telegram.

    Uso:
        client = TelegramClient(token=settings.telegram_bot_token)
        await client.send_message(chat_id=123, text="Hola!")
    """

    def __init__(self, token: str):
        self._token = token
        self._api_base = f"https://api.telegram.org/bot{token}"

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "Markdown",
    ) -> bool:
        """
        Envía un mensaje de texto al usuario.

        Args:
            chat_id: ID del chat de Telegram
            text: Texto a enviar (soporta Markdown)
            parse_mode: "Markdown" o "HTML"

        Returns:
            True si el mensaje fue enviado correctamente, False si hubo un error.
        """
        url = f"{self._api_base}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

            logger.info(f"Mensaje enviado a chat_id={chat_id}")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Error HTTP al enviar mensaje a chat_id={chat_id}: "
                f"status={e.response.status_code}"
            )
            return False

        except httpx.ConnectError as e:
            logger.error(f"Error de red al enviar mensaje a chat_id={chat_id}: {e}")
            return False

        except Exception as e:
            logger.error(f"Error inesperado al enviar mensaje: {e}", exc_info=True)
            return False

    async def set_webhook(self, webhook_url: str) -> bool:
        """
        Registra la URL del webhook en Telegram.

        Args:
            webhook_url: URL pública del servidor (ej. https://xxx.ngrok.io/webhook)

        Returns:
            True si el webhook fue configurado correctamente.
        """
        url = f"{self._api_base}/setWebhook"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json={"url": webhook_url})
                response.raise_for_status()
                data = response.json()

            if data.get("ok"):
                logger.info(f"Webhook configurado: {webhook_url}")
                return True
            else:
                logger.error(f"Telegram rechazó el webhook: {data}")
                return False

        except Exception as e:
            logger.error(f"Error configurando webhook: {e}", exc_info=True)
            return False

    async def get_me(self) -> dict | None:
        """
        Obtiene información del bot (para verificar que el token es válido).
        """
        url = f"{self._api_base}/getMe"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json().get("result")
        except Exception as e:
            logger.error(f"Error en getMe: {e}")
            return None
