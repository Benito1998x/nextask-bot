from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """
    Interfaz base para todas las Tools del agente NexTask.

    Cada Tool representa una capacidad que Gemini puede invocar
    mediante function calling. Todas las Tools DEBEN heredar de esta clase.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre único que el LLM usa para identificar esta tool."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Descripción clara para el LLM: cuándo y cómo usar esta tool."""
        ...

    @abstractmethod
    def get_schema(self) -> dict[str, Any]:
        """
        Schema JSON de los parámetros para Gemini function calling.

        Returns:
            dict con estructura: { name, description, parameters }
        """
        ...
