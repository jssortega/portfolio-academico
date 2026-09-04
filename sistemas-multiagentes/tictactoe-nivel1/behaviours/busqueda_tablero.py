"""
Comportamientos de búsqueda del Agente Jugador.

Define los behaviours que permiten al jugador intercambiar mensajes
con los tableros para la inscripción:

- ``BuscarPartida``: periódico, consulta los tableros de la sala MUC
si encuentra alguno disponible le envía un mensaje de inscripción.
- ``RecicibirRespuesta``: cíclico, escucha las respuestas por parte del
tablero y en función de la respuesta pasa al siguiente punto
"""

import json

from spade.agent import Agent
from spade.message import Message
from spade.template import Template

from spade.behaviour import PeriodicBehaviour, CyclicBehaviour

from behaviours.partida_jugador import ComportamientoPartida

from ontologia.ontologia import (
    ONTOLOGIA,
    PERFORMATIVA_AGREE,
    PERFORMATIVA_INFORM,
    PERFORMATIVA_REFUSE,
    PERFORMATIVA_FAILURE,
    validar_cuerpo,
    crear_mensaje_join
)

# ═══════════════════════════════════════════════════════════════════════════
#  BuscarPartida
# ═══════════════════════════════════════════════════════════════════════════
class BuscarPartida(PeriodicBehaviour):
    """Busca periódicamente tableros disponibles en las salas MUC.

        En cuanto encuentra un tablero disponible crea el mensaje de
        inscripción correspondiente y lo envía al tablero.
    """

    async def run(self):

        # Comprueba que no ha superado el maximo de partidas permitidas por jugador antes de seguir
        max_partidas = getattr(self.agent, "max_partidas", 1)

        ocupadas = (
                len(self.agent.partidas_activas)
                + len(self.agent.partidas_pendientes)
                + len(self.agent.tableros_contactados)
        )

        if ocupadas >= max_partidas:
            return

        tableros = list(self.agent.tableros_descubiertos.items())

        if not tableros:
            return

        inicio = getattr(self.agent, "indice_busqueda_tablero", 0) % len(tableros)

        for desplazamiento in range(len(tableros)):
            indice = (inicio + desplazamiento) % len(tableros)
            jid, info = tableros[indice]

            if info.get("status") != "waiting":
                continue

            destino_tablero = jid

            # En tests simulados se usa solo el nick.
            # En ejecución real XMPP se usa sala/nick.
            if "/" not in destino_tablero and not hasattr(self.agent, "_sala"):
                destino_tablero = f"{self.agent.muc_room}/{jid}"

            if jid in self.agent.tableros_contactados:
                continue

            if destino_tablero in self.agent.tableros_contactados:
                continue

            msg = crear_mensaje_join(destino_tablero, str(self.agent.jid))

            print(
                f"[JUGADOR {self.agent.player_name}] Solicitando inscripción en "
                f"{info['nick']} ({destino_tablero})"
            )

            await self.send(msg)

            self.agent.tableros_contactados.add(destino_tablero)
            self.agent.indice_busqueda_tablero = (indice + 1) % len(tableros)

            return

# ═══════════════════════════════════════════════════════════════════════════
#  RecibirRespuesta
# ═══════════════════════════════════════════════════════════════════════════
class RecibirRespuesta(CyclicBehaviour):
    """Escucha mensajes cíclicamente de respuesta de los tableros

        Procesa los mensajes de respuesta de los tableros y actúa en consecuencia
    """

    async def run(self):
        msg = await self.receive(timeout=10)

        if msg is None:
            if not self.agent.partidas_pendientes and not self.agent.partidas_activas:
                self.agent.tableros_contactados.clear()
            return

        cuerpo = json.loads(msg.body)
        errores = validar_cuerpo(cuerpo)

        #Comprueba que el cuerpo del mensaje es válido
        if not errores["valido"]:
            return

        performativa = msg.get_metadata("performative")
        accion = cuerpo.get("action")
        thread = msg.thread
        tablero_jid = str(msg.sender)

        #Si el mensaje es de "agree" guarda el simbolo que va a tener en la partida
        if performativa == PERFORMATIVA_AGREE and accion == "join-accepted":
            simbolo = cuerpo["symbol"]

            if tablero_jid in self.agent.tableros_contactados:
                self.agent.tableros_contactados.remove(tablero_jid)

            self.agent.partidas_pendientes[tablero_jid] = {
                "thread_join": thread,
                "tablero": tablero_jid,
                "mi_simbolo": simbolo,
            }

            print(f"[JUGADOR {self.agent.player_name}] Inscripción aceptada por {tablero_jid} | símbolo asignado: {simbolo} | thread join: {thread}")

        #Si la respuesta es "refuse" o "failure" elimina el tablero de la lista
        elif performativa == PERFORMATIVA_REFUSE and accion == "join-refused":
            razon = cuerpo["reason"]

            if tablero_jid in self.agent.tableros_contactados:
                self.agent.tableros_contactados.remove(tablero_jid)

            print(f"[JUGADOR {self.agent.player_name}] Inscripción rechazada por {tablero_jid} | motivo: {razon}")

        elif performativa == PERFORMATIVA_FAILURE and accion == "join-timeout":
            razon = cuerpo["reason"]

            if tablero_jid in self.agent.tableros_contactados:
                self.agent.tableros_contactados.remove(tablero_jid)

            print(f"[JUGADOR {self.agent.player_name}] Inscripción expirada en {tablero_jid} | motivo: {razon}")

        elif performativa == PERFORMATIVA_INFORM and accion == "game-start":
            thread_partida = cuerpo["thread"]
            oponente = cuerpo["opponent"]

            datos = self.agent.partidas_pendientes.pop(tablero_jid, None)

            if datos is None:
                print(
                    f"[JUGADOR {self.agent.player_name}] Game-start recibido de "
                    f"{tablero_jid}, pero no había inscripción pendiente"
                )
                return

            simbolo = datos["mi_simbolo"]

            template_partida = Template()
            template_partida.set_metadata("ontology", ONTOLOGIA)
            template_partida.thread = thread_partida

            comportamiento_partida = ComportamientoPartida(
                tablero_jid=tablero_jid,
                mi_simbolo=simbolo,
                thread_partida=thread_partida,
            )

            comportamiento_partida.oponente = oponente
            comportamiento_partida.partida_iniciada = True

            self.agent.partidas_activas[thread_partida] = {
                "tablero": tablero_jid,
                "mi_simbolo": simbolo,
                "oponente": oponente,
            }

            self.agent.add_behaviour(comportamiento_partida, template_partida)

            print(f"[JUGADOR {self.agent.player_name}] Partida iniciada | tablero: {tablero_jid} | símbolo: {simbolo} | rival: {oponente} | thread partida: {thread_partida}")
