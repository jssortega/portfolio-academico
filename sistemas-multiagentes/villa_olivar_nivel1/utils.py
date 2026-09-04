"""
Módulo de utilidades para el Sistema de Emergencias — Villa Olivar.

Centraliza funciones comunes (carga de configuración, construcción de JID
y creación/arranque de agentes SPADE) para evitar duplicación entre
main.py y los tests.

En SPADE 4.x los parámetros de conexión se reparten entre el constructor
del agente (port, verify_security) y el método start() (auto_register).
Las funciones factoría de este módulo encapsulan esa separación para que
el código cliente no tenga que recordar estos detalles.

Compatibilidad llm_chat():
    La versión actual de spade-llm no expone un método ``llm_chat()`` en
    ``LLMAgent``. Este módulo lo inyecta automáticamente al importarse,
    encapsulando la API real (ContextManager + get_llm_response) con el
    ciclo completo de tool calling. Si una versión futura de spade-llm
    añade ``llm_chat()`` de forma nativa, la inyección se desactiva
    automáticamente (comprobación ``hasattr``). Patrón idéntico al del
    Guión 7 (``configuracion.py``).

Autor(es): [Nombre del grupo]
Grupo: <denominación del grupo>
"""
import json
import logging
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml
from spade.agent import Agent

logger = logging.getLogger(__name__)


# ─── Carga de configuración ──────────────────────────────────────────────────

def cargar_configuracion(ruta: str = "config.yaml") -> dict[str, Any]:
    """Carga la configuración completa desde el fichero YAML.

    Args:
        ruta: Ruta al fichero de configuración.

    Returns:
        Diccionario con toda la configuración del sistema.
    """
    ruta_config = Path(ruta)
    resultado = {}
    try:
        with open(ruta_config, "r", encoding="utf-8") as fichero:
            resultado = yaml.safe_load(fichero)
        logger.info("Configuración cargada desde %s", ruta_config)
    except FileNotFoundError:
        logger.error(
            "No se encontró el fichero de configuración: %s", ruta_config
        )
        sys.exit(1)
    except yaml.YAMLError as error:
        logger.error("Error al parsear %s: %s", ruta_config, error)
        sys.exit(1)
    return resultado


# ─── Construcción de JID ─────────────────────────────────────────────────────

def construir_jid(usuario: str, config_xmpp: dict[str, Any]) -> str:
    """Construye el JID completo a partir del nombre de usuario y el perfil.

    Args:
        usuario: Nombre de usuario del agente.
        config_xmpp: Diccionario con la configuración del perfil XMPP activo.

    Returns:
        JID completo en formato 'usuario@servidor'.
    """
    resultado = f"{usuario}@{config_xmpp['servidor']}"
    return resultado


# ─── Funciones factoría para agentes SPADE ───────────────────────────────────

def crear_agente(
    clase_agente: type[Agent],
    usuario: str,
    contrasena: str,
    config_xmpp: dict[str, Any],
) -> Agent:
    """Crea una instancia de agente SPADE con los parámetros de conexión.

    Construye el JID y pasa al constructor únicamente los parámetros que
    este acepta (port y verify_security).  El parámetro auto_register
    se gestiona aparte en arrancar_agente(), ya que pertenece a start().

    Args:
        clase_agente: Clase (o subclase) de spade.agent.Agent a instanciar.
        usuario: Nombre de usuario del agente (sin dominio).
        contrasena: Contraseña del agente en el servidor XMPP.
        config_xmpp: Diccionario con la configuración del perfil XMPP activo.

    Returns:
        Instancia del agente, lista para ser arrancada con arrancar_agente().
    """
    jid = construir_jid(usuario, config_xmpp)
    resultado = clase_agente(
        jid,
        contrasena,
        port=config_xmpp.get("puerto", 5222),
        verify_security=config_xmpp.get("verificar_seguridad", False),
    )
    return resultado


async def arrancar_agente(
    agente: Agent,
    config_xmpp: dict[str, Any],
) -> None:
    """Arranca un agente SPADE pasando auto_register a start().

    En SPADE 4.x, auto_register es parámetro de start(), no del
    constructor.  Esta función encapsula esa particularidad.

    Args:
        agente: Instancia del agente ya creada con crear_agente().
        config_xmpp: Diccionario con la configuración del perfil XMPP activo.
    """
    auto_registro = config_xmpp.get("registro_automatico", True)
    await agente.start(auto_register=auto_registro)


# =============================================================================
# Compatibilidad llm_chat() para SPADE-LLM
# =============================================================================
# La versión actual de spade-llm no expone un método llm_chat() en LLMAgent.
# Los behaviours del proyecto usan ``await self.agent.llm_chat(consulta)``
# como interfaz simple ("una línea para preguntar al cerebro"). Este bloque
# inyecta ese método si la biblioteca no lo proporciona, usando internamente
# la API real: ContextManager + LLMProvider.get_llm_response() con el ciclo
# completo de tool calling (necesario para las herramientas ADK adaptadas).
#
# Si una versión futura de spade-llm añade llm_chat() de forma nativa,
# la comprobación ``hasattr`` evita el conflicto y esta adaptación queda
# inactiva automáticamente.
#
# Patrón idéntico al del Guión 7 (configuracion.py).

_logger_compat = logging.getLogger("utils.llm_chat")

# Límite de iteraciones del ciclo de tool calling para evitar
# bucles infinitos si el LLM solicita herramientas indefinidamente.
_MAX_ITERACIONES_TOOLS: int = 10


def _inyectar_llm_chat() -> None:
    """Inyecta ``llm_chat()`` en ``LLMAgent`` si no existe.

    El método inyectado:
        1. Crea un ``UserMessage`` con la consulta recibida.
        2. Lo añade al ``ContextManager`` del agente con un
           ``conversation_id`` único (para que cada consulta sea
           independiente y no acumule historial).
        3. Gestiona el ciclo completo de tool calling: si el LLM
           solicita herramientas, las ejecuta y vuelve a consultar
           al LLM hasta obtener una respuesta de texto.
        4. Si el agente tiene servidores MCP configurados y las
           herramientas aún no se han cargado, las inicializa de
           forma perezosa en la primera llamada.

    Esta función se ejecuta una sola vez al importar el módulo.
    """
    from spade_llm import LLMAgent

    if hasattr(LLMAgent, "llm_chat"):
        _logger_compat.debug(
            "LLMAgent ya tiene llm_chat() nativo — no se inyecta."
        )
        return

    from spade_llm.context._types import UserMessage

    async def llm_chat(self, consulta: str) -> str:
        """Envía una consulta al LLM y devuelve la respuesta como texto.

        Método de compatibilidad inyectado por ``utils.py``.
        Encapsula la API de SPADE-LLM (ContextManager + get_llm_response)
        en una llamada simple para los behaviours del proyecto.

        Si el agente tiene herramientas registradas (ADK adaptadas o MCP),
        gestiona el ciclo completo de tool calling.

        Args:
            consulta: Texto de la pregunta para el LLM.

        Returns:
            Respuesta del LLM como cadena de texto.
        """
        # Inicialización perezosa de herramientas MCP (solo la primera vez)
        if self.mcp_servers and not self.tools:
            await self._setup_mcp_tools()

        # Cada consulta usa un conversation_id único para que no se
        # acumule historial entre mensajes FIPA independientes.
        id_conversacion = uuid.uuid4().hex
        mensaje = UserMessage(role="user", content=consulta)
        self.context.add_message_dict(mensaje, conversation_id=id_conversacion)
        self.context.set_current_conversation(id_conversacion)

        herramientas = self.tools if self.tools else None

        # --- Ciclo de tool calling -----------------------------------------
        respuesta_final = None
        iteracion = 0

        while respuesta_final is None and iteracion < _MAX_ITERACIONES_TOOLS:
            iteracion += 1

            respuesta_llm = await self.provider.get_llm_response(
                self.context, herramientas, id_conversacion
            )

            tool_calls = respuesta_llm.get("tool_calls", [])
            texto = respuesta_llm.get("text")

            if not tool_calls:
                respuesta_final = texto
            else:
                # Registrar la petición del asistente en el contexto
                llamadas_formateadas = []
                for tc in tool_calls:
                    args = tc.get("arguments", {})
                    args_str = json.dumps(args) if isinstance(args, dict) else args
                    llamadas_formateadas.append({
                        "id": tc.get("id"),
                        "type": "function",
                        "function": {
                            "name": tc.get("name"),
                            "arguments": args_str,
                        },
                    })
                msg_asistente = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": llamadas_formateadas,
                }
                self.context.add_message_dict(msg_asistente, id_conversacion)

                # Ejecutar cada herramienta
                for tc in tool_calls:
                    nombre = tc.get("name")
                    argumentos = tc.get("arguments", {})
                    id_llamada = tc.get("id", f"call_{nombre}_{iteracion}")
                    herramienta = next(
                        (h for h in self.tools if h.name == nombre), None
                    )
                    resultado_tool = {
                        "error": f"Herramienta {nombre} no encontrada"
                    }
                    if herramienta is not None:
                        try:
                            resultado_tool = await herramienta.execute(
                                **argumentos
                            )
                        except Exception as e:
                            resultado_tool = {"error": str(e)}
                    self.context.add_tool_result(
                        nombre, resultado_tool, id_llamada, id_conversacion
                    )

        resultado: str = respuesta_final if respuesta_final is not None else ""
        return resultado

    LLMAgent.llm_chat = llm_chat
    _logger_compat.info(
        "Método llm_chat() inyectado en LLMAgent (compatibilidad)."
    )


# Ejecutar la inyección al importar este módulo.
_inyectar_llm_chat()
