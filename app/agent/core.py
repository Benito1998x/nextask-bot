"""
Motor del agente NexTask.

Conecta Gemini 2.5 Flash con las Tools del proyecto.
Implementa el loop de function calling usando el nuevo SDK `google-genai`.

Modelo: Gemini 2.5 Flash (function calling nativo)
"""
import logging
from typing import Any

from google import genai
from google.genai import types

from app.config import settings
from app.agent.prompts import SYSTEM_PROMPT
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)


class NexTaskAgent:
    """
    Agente principal que orquesta las herramientas de NexTask.

    Uso:
        agent = NexTaskAgent(tools=[SupabaseTool(), CalendarTool(), ...])
        response = await agent.process_message(chat_id=123, text="Crea una tarea...")
    """

    def __init__(self, tools: list[BaseTool] | None = None):
        self._tools: dict[str, BaseTool] = {}
        self._tool_declarations: list[dict[str, Any]] = []

        # Registrar tools
        if tools:
            for tool in tools:
                self.register_tool(tool)

        # Crear cliente asíncrono
        self._client = genai.Client(api_key=settings.gemini_api_key)
        
        # Convertir los schemas en un objeto Tool de genai
        genai_tools = None
        if self._tool_declarations:
            function_declarations = []
            for schema in self._tool_declarations:
                function_declarations.append(
                    types.FunctionDeclaration(
                        name=schema.get("name"),
                        description=schema.get("description"),
                        # GenAI a veces prefiere que parameters sea dict
                        parameters=schema.get("parameters")
                    )
                )
            genai_tools = [types.Tool(function_declarations=function_declarations)]

        # Configurar el chat base
        self._config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
            tools=genai_tools,
        )

        logger.info(
            f"NexTaskAgent inicializado | modelo={settings.gemini_model} | "
            f"tools={list(self._tools.keys())}"
        )

    def register_tool(self, tool: BaseTool) -> None:
        """Registra una nueva Tool en el agente."""
        self._tools[tool.name] = tool
        self._tool_declarations.append(tool.get_schema())
        logger.info(f"Tool registrada: {tool.name}")

    async def process_message(
        self,
        chat_id: int,
        text: str,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Procesa un mensaje del usuario y retorna la respuesta del agente.
        """
        logger.info(f"Procesando mensaje | chat_id={chat_id} | text={text[:80]}")

        try:
            # Transformar `history` (nuestro formato dict simple) 
            # a `types.Content` de google-genai
            curated_history = []
            if history:
                for msg in history:
                    # Formato esperado: [{"role": "user", "parts": [{"text": "..."}]}]
                    role = msg.get("role", "user")
                    text_content = msg.get("parts", [{}])[0].get("text", "")
                    curated_history.append(
                        types.Content(role=role, parts=[types.Part.from_text(text_content)])
                    )

            # Iniciar chat asíncrono
            chat = self._client.aio.chats.create(
                model=settings.gemini_model,
                config=self._config,
                history=curated_history if curated_history else None
            )

            # Enviar mensaje al modelo
            response = await chat.send_message(text)

            # Loop de function calling
            response = await self._handle_function_calls(chat, response)

            # Extraer texto de la respuesta final
            response_text = response.text or "✅ Tarea procesada (sin comentario final)."
            logger.info(f"Respuesta generada | chat_id={chat_id} | len={len(response_text)}")
            return response_text

        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}", exc_info=True)
            return "⚠️ Hubo un error procesando tu mensaje. Intenta de nuevo en un momento."

    async def _handle_function_calls(self, chat, response) -> Any:
        """
        Loop de function calling adaptado al SDK google-genai.
        """
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            if not response.function_calls:
                break

            function_responses = []
            for fc in response.function_calls:
                # fc.args es un dict proveniente del nuevo SDK
                args = fc.args if fc.args else {}
                result = await self._execute_tool(fc.name, args)
                
                # Crear la respuesta de la función para el modelo
                function_responses.append(
                    types.Part.from_function_response(
                        name=fc.name,
                        response={"result": result}
                    )
                )

            # Enviar resultados de vuelta a Gemini (pasamos la lista de Parts)
            response = await chat.send_message(function_responses)
            iteration += 1

        if iteration >= max_iterations:
            logger.warning("Se alcanzó el límite de iteraciones de function calling")

        return response

    async def _execute_tool(self, tool_name: str, args: dict[str, Any]) -> Any:
        """
        Ejecuta una Tool registrada y retorna el resultado.
        """
        logger.info(f"Ejecutando tool: {tool_name} | args={args}")

        tool = self._tools.get(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' no encontrada"
            logger.error(error_msg)
            return {"error": error_msg}

        try:
            # Nuestro estándar: ejecutar acción específica o execute()
            action = args.pop("action", None)
            if action and hasattr(tool, action):
                method = getattr(tool, action)
                result = await method(**args) if args else await method()
            else:
                result = await tool.execute(**args) if hasattr(tool, "execute") else {"error": "No action specified"}

            if hasattr(result, "model_dump"):
                return result.model_dump()
            return result

        except Exception as e:
            logger.error(f"Error ejecutando {tool_name}: {e}", exc_info=True)
            return {"error": str(e)}

    async def process_scheduler_event(
        self, event_type: str, chat_id: int
    ) -> str:
        """Procesa un evento del Cloud Scheduler."""
        prompts_by_event = {
            "morning_checkin": (
                "Es hora del checkin matutino. "
                "Usa supabase_ops para obtener las tareas pendientes de hoy "
                "y genera el resumen matutino."
            ),
            "confrontacion": (
                "Es hora de la confrontación de la tarde. "
                "Revisa las tareas del día y genera el recordatorio."
            ),
            "weekly_report": (
                "Es el reporte semanal. Obtén todas las tareas de la semana y genera el resumen."
            ),
        }

        prompt = prompts_by_event.get(event_type)
        if not prompt:
            return f"⚠️ Evento desconocido: {event_type}"

        return await self.process_message(chat_id=chat_id, text=prompt)
