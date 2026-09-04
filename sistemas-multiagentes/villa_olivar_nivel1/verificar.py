# Verificar que LLMProvider puede conectar con el Ollama local
import asyncio
from spade_llm import LLMProvider, ContextManager
from spade_llm.context._types import UserMessage

async def verificar():
    proveedor = LLMProvider.create_ollama(model="gemma3:4b")
    contexto = ContextManager(system_prompt="Responde en espanol, brevemente.")
    mensaje = UserMessage(role="user", content="Hola, que tiempo hace en Jaén.")
    contexto.add_message_dict(mensaje, conversation_id="verificacion")
    contexto.set_current_conversation("verificacion")
    respuesta = await proveedor.get_response(contexto)
    print(respuesta)

asyncio.run(verificar())

