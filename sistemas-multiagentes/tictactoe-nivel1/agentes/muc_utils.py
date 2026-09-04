from xml.etree.ElementTree import SubElement


def obtener_sala_muc(agent):
    parametros = getattr(agent, "config_parametros", {}) or {}
    config_xmpp = getattr(agent, "config_xmpp", {}) or {}

    sala_asignada = parametros.get("sala_asignada")
    if sala_asignada:
        if "@" in sala_asignada:
            return sala_asignada

        servicio_muc = config_xmpp.get("servicio_muc", "conference.localhost")
        return f"{sala_asignada}@{servicio_muc}"

    sala_completa = config_xmpp.get("sala_muc_completa")
    if sala_completa:
        return sala_completa

    sala = config_xmpp.get("sala_tictactoe", "tictactoe")
    servicio_muc = config_xmpp.get("servicio_muc", "conference.localhost")
    return f"{sala}@{servicio_muc}"


def setup_muc(agent, apodo):
    client = agent.client
    sala_muc = obtener_sala_muc(agent)

    agent.muc_room = sala_muc

    if "xep_0045" not in client.plugin:
        client.register_plugin("xep_0045")

    client.plugin["xep_0045"].join_muc(
        sala_muc,
        nick=apodo,
    )

    return sala_muc

def actualizar_estado_muc(agent, sala_muc, apodo, estado):
    stanza = agent.client.make_presence(
        pto=f"{sala_muc}/{apodo}",
        pstatus=estado,
    )
    stanza.send()