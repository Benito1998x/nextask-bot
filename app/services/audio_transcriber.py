"""
Servicio de transcripción de audio para NexTask.

Descarga notas de voz de Telegram y las transcribe usando
el modelo Whisper de OpenAI (o un placeholder hasta que esté integrado).
"""
import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class AudioTranscriber:
    """
    Transcribe notas de voz de Telegram.

    Flujo:
    1. Obtiene la URL del archivo via Telegram getFile API.
    2. Descarga el archivo .ogg.
    3. Transcribe con Whisper (o placeholder).
    """

    def __init__(self, telegram_token: str):
        self._token = telegram_token
        self._api_base = f"https://api.telegram.org/bot{telegram_token}"

    async def get_file_url(self, file_id: str) -> str | None:
        """
        Obtiene la URL de descarga de un archivo de Telegram.

        Args:
            file_id: file_id del mensaje de voz

        Returns:
            URL completa para descargar el archivo, o None si falla
        """
        url = f"{self._api_base}/getFile"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params={"file_id": file_id})
                data = response.json()

            if data.get("ok") and data.get("result", {}).get("file_path"):
                file_path = data["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{self._token}/{file_path}"
                logger.info(f"URL de archivo obtenida: {file_path}")
                return download_url

            logger.warning(f"No se pudo obtener file_path para file_id={file_id}")
            return None

        except Exception as e:
            logger.error(f"Error obteniendo URL de archivo: {e}", exc_info=True)
            return None

    async def _download_and_transcribe(self, file_url: str) -> str:
        """
        Descarga el archivo de audio y lo transcribe.

        Este método será expandido cuando se integre Whisper completo.
        Por ahora usa un placeholder funcional.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(file_url)
                audio_bytes = response.content

            # TODO: Integrar Whisper para transcripción real
            # import whisper
            # model = whisper.load_model("base")
            # result = model.transcribe(audio_bytes)
            # return result["text"]

            logger.info(f"Audio descargado: {len(audio_bytes)} bytes")
            return f"[Transcripción pendiente — audio de {len(audio_bytes)} bytes recibido]"

        except Exception as e:
            logger.error(f"Error descargando/transcribiendo audio: {e}", exc_info=True)
            return "No pude procesar el audio. Intenta de nuevo."

    async def transcribe(self, file_id: str) -> str:
        """
        Método principal: obtiene URL, descarga y transcribe.

        Args:
            file_id: file_id del mensaje de voz de Telegram

        Returns:
            Texto transcrito del audio, o mensaje de error amigable
        """
        file_url = await self.get_file_url(file_id)
        if not file_url:
            return "No pude obtener el archivo de audio. Verifica que el mensaje de voz fue enviado correctamente."

        return await self._download_and_transcribe(file_url)


def get_audio_transcriber() -> AudioTranscriber:
    """Factory: crea AudioTranscriber con token de Telegram."""
    return AudioTranscriber(telegram_token=settings.telegram_bot_token)
