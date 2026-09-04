"""
Utilidades DF — Villa Olivar.

Primero intenta usar el DF real XMPP.
Si no hay DF arrancado, usa un registro local en memoria.
"""

import json
from spade.message import Message

DF_JID = "df_multi007s@localhost"

# Registro local de respaldo:
# tipo_servicio -> [jid_agente]
_DIRECTORIO_LOCAL = {}


def _bare_jid(jid) -> str:
    return str(jid).split("/")[0]


def _respuesta_local(performative: str, body: dict) -> Message:
    msg = Message(to=DF_JID)
    msg.sender = DF_JID
    msg.set_metadata("performative", performative)
    msg.set_metadata("ontology", "fipa-df")
    msg.set_metadata("protocol", "fipa-request")
    msg.set_metadata("language", "application/json")
    msg.body = json.dumps(body)
    return msg


def crear_mensaje_df(tipo, ontologia):
    """Construye un mensaje de petición al DF real."""
    msg = Message(to=DF_JID)
    msg.set_metadata("performative", "request")
    msg.set_metadata("ontology", ontologia)
    msg.body = json.dumps(tipo)
    return msg


async def registrar_servicio(behaviour, tipo_servicio):
    """
    Registra un servicio.

    Si existe el DF real, usa su respuesta.
    Si no existe o no responde, registra localmente al agente.
    """
    jid_agente = _bare_jid(behaviour.agent.jid)

    msg = crear_mensaje_df({"tipo": tipo_servicio}, "df-register")
    await behaviour.send(msg)

    resp = None
    tiempo_limite = 3

    while tiempo_limite > 0:
        candidato = await behaviour.receive(timeout=1)

        if candidato is None:
            tiempo_limite -= 1
            continue

        if (
            _bare_jid(candidato.sender) == _bare_jid(DF_JID)
            and candidato.get_metadata("ontology") == "fipa-df"
        ):
            resp = candidato
            break

        tiempo_limite -= 1

    if resp and resp.get_metadata("performative") == "inform":
        return resp

    # Fallback local si no hay DF real
    if tipo_servicio not in _DIRECTORIO_LOCAL:
        _DIRECTORIO_LOCAL[tipo_servicio] = []

    if jid_agente not in _DIRECTORIO_LOCAL[tipo_servicio]:
        _DIRECTORIO_LOCAL[tipo_servicio].append(jid_agente)

    print(f"[DF-LOCAL] Registrado servicio '{tipo_servicio}': {jid_agente}")

    return _respuesta_local(
        "inform",
        {
            "status": "ok-local",
            "tipo": tipo_servicio,
            "jid": jid_agente,
        },
    )


async def buscar_servicio(behaviour, tipo=""):
    """
    Busca servicios.

    Si existe el DF real, usa su respuesta.
    Si no existe o no responde, busca en el registro local.
    """
    msg = crear_mensaje_df({"tipo": tipo}, "df-search")
    await behaviour.send(msg)

    resp = None
    tiempo_limite = 3

    while tiempo_limite > 0:
        candidato = await behaviour.receive(timeout=1)

        if candidato is None:
            tiempo_limite -= 1
            continue

        if (
            _bare_jid(candidato.sender) == _bare_jid(DF_JID)
            and candidato.get_metadata("performative") == "inform"
            and candidato.get_metadata("ontology") == "fipa-df"
        ):
            try:
                datos = json.loads(candidato.body)
            except Exception:
                tiempo_limite -= 1
                continue

            if datos.get("tipo") == tipo:
                resp = candidato
                break

        tiempo_limite -= 1

    if resp:
        return resp

    # Fallback local si no hay DF real
    jids = _DIRECTORIO_LOCAL.get(tipo, [])

    print(f"[DF-LOCAL] Busqueda servicio '{tipo}': {jids}")

    return _respuesta_local(
        "inform",
        {
            "tipo": tipo,
            "jids": jids,
        },
    )