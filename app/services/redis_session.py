"""
Servicio de sesión Redis para NexTask.

Gestiona el historial de conversación por chat_id en Redis,
con TTL configurable (default 24h).

Cada chat de Telegram tiene su propia sesión con historial.
"""
import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisSession:
    """
    Gestiona el historial de conversación en Redis.
    
    Cada sesión se almacena como una lista JSON en Redis con clave:
        nextask:session:{chat_id}
    
    TTL por defecto: 24 horas (configurable en .env).
    """

    def __init__(self):
        self._redis: aioredis.Redis | None = None

    async def connect(self) -> None:
        """Conectar a Redis."""
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=1, # Timeout rápido para no bloquear
            )
            # Verificar conexión rápida
            try:
                await self._redis.ping()
                logger.debug(f"Conectado a Redis: {settings.redis_url}")
            except Exception as e:
                logger.warning(f"No se pudo conectar a Redis. Operando sin memoria de sesión. Error: {e}")
                self._redis = None

    async def disconnect(self) -> None:
        """Cerrar conexión a Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.debug("Redis desconectado")

    def _key(self, chat_id: int) -> str:
        """Genera la clave de Redis para un chat."""
        return f"nextask:session:{chat_id}"

    async def get_history(self, chat_id: int) -> list[dict[str, str]]:
        """
        Obtiene el historial de conversación de un chat.
        """
        await self.connect()
        if not self._redis:
            return [] # Fail gracefully si redis está caído
            
        key = self._key(chat_id)
        
        try:
            raw = await self._redis.get(key)
            if not raw:
                return []
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"Error obteniendo historial para chat={chat_id}: {e}")
            return []

    async def append_message(
        self, chat_id: int, role: str, text: str
    ) -> None:
        """Agrega un mensaje al historial."""
        await self.connect()
        if not self._redis:
            return # No hacer nada si redis no está disponible
            
        key = self._key(chat_id)
        
        # history se obtiene seguro gracias al try-except en get_history
        history = await self.get_history(chat_id)
        history.append({
            "role": role,
            "parts": [text],
        })

        if len(history) > 20:
            history = history[-20:]

        try:
            await self._redis.set(
                key,
                json.dumps(history, ensure_ascii=False),
                ex=settings.session_ttl_seconds,
            )
        except Exception as e:
            logger.warning(f"Error guardando historial para chat={chat_id}: {e}")

    async def clear_session(self, chat_id: int) -> None:
        """Elimina el historial de un chat."""
        await self.connect()
        if self._redis:
            try:
                await self._redis.delete(self._key(chat_id))
                logger.info(f"Sesión limpiada para chat={chat_id}")
            except Exception:
                pass

    async def session_exists(self, chat_id: int) -> bool:
        """Verifica si un chat tiene sesión activa."""
        await self.connect()
        if not self._redis:
            return False
            
        try:
            return await self._redis.exists(self._key(chat_id)) > 0
        except Exception:
            return False


# Instancia singleton
redis_session = RedisSession()
