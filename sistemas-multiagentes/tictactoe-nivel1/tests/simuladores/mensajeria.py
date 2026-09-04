"""Utilidades de mensajería compartidas por los simuladores.

Los simuladores (tablero, jugador y supervisor) construyen y leen
mensajes de la ontología igual que lo haría un agente real. Estas
funciones centralizan esa tarea para que cada simulador quede
breve y se concentre en su lógica de protocolo.
"""
import json
from typing import Any, Optional

from spade.message import Message

from ontologia.ontologia import CONVERSATION_ID_POR_ACCION, ONTOLOGIA


def construir_mensaje(
    destino: str,
    contenido: Any,
    *,
    thread: Optional[str] = None,
    conversation_id: Optional[str] = None,
    groupchat: bool = False,
) -> Message:
    """Construye un ``Message`` SPADE con la metadata FIPA-ACL.

    Si ``conversation_id`` no se indica explícitamente, se intenta
    derivar a partir del ``action`` del cuerpo y del diccionario
    ``CONVERSATION_ID_POR_ACCION`` de la ontología. De ese modo, los
    simuladores emiten los mismos metadatos que los agentes reales
    sin necesidad de repetir el valor en cada llamada.

    Args:
        destino: JID de destino (sala para difusión, ``sala/nick``
            para mensaje privado).
        contenido: ``ContenidoMensaje`` de un constructor
            ``crear_cuerpo_*`` de la ontología.
        thread: Hilo de correlación. Opcional.
        conversation_id: Identificador del protocolo. Si es ``None``,
            se intenta derivar del ``action`` del cuerpo.
        groupchat: Si es ``True``, marca el mensaje como difusión.

    Returns:
        El mensaje listo para entregar a la sala simulada.
    """
    mensaje = Message(to=destino)
    mensaje.set_metadata("ontology", ONTOLOGIA)
    mensaje.set_metadata("performative", contenido.performativa)
    cid = conversation_id
    if cid is None:
        try:
            cuerpo = json.loads(contenido.cuerpo)
        except (json.JSONDecodeError, TypeError, AttributeError):
            cuerpo = {}
        accion = cuerpo.get("action") if isinstance(cuerpo, dict) else None
        cid = CONVERSATION_ID_POR_ACCION.get(accion)
    if cid is not None:
        mensaje.set_metadata("conversation-id", cid)
    if groupchat:
        mensaje.set_metadata("type", "groupchat")
    if thread is not None:
        mensaje.thread = thread
    mensaje.body = contenido.cuerpo
    return mensaje


def leer_cuerpo(mensaje: Any) -> dict[str, Any]:
    """Interpreta el cuerpo de un mensaje como diccionario JSON."""
    cuerpo: dict[str, Any] = {}
    texto = getattr(mensaje, "body", None)
    if texto:
        try:
            datos = json.loads(texto)
        except (json.JSONDecodeError, TypeError):
            datos = None
        if isinstance(datos, dict):
            cuerpo = datos
    return cuerpo


def extraer_nick(jid_origen: str) -> str:
    """Obtiene el nick (recurso) de un JID MUC ``sala@servicio/nick``."""
    nick = ""
    if "/" in jid_origen:
        nick = jid_origen.split("/", 1)[1]
    return nick


def privado(sala: str, nick: str) -> str:
    """Compone el JID de ocupante para un mensaje privado MUC."""
    return f"{sala}/{nick}"
