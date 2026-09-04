"""
Comportamientos de partida del Agente Jugador.

Define los behaviours y metodos auxiliares que permiten al jugador
intercambiar mensajes con el tablero sobre los movimientos de
la partida y analizar el estado del tablero:

- ``BuscarPartida``: cíclico, está a la escucha de mensajes del tablero
y actúa en función de estos enviando movimientos válidos al tablero
"""

import json

from spade.behaviour import CyclicBehaviour
from spade.message import Message

from ontologia import (
    ONTOLOGIA,
    PERFORMATIVA_ACCEPT_PROPOSAL,
    PERFORMATIVA_INFORM,
    PERFORMATIVA_CFP,
    PERFORMATIVA_REJECT_PROPOSAL,
    crear_cuerpo_move,
    crear_cuerpo_ok,
    crear_cuerpo_turn_result,
    validar_cuerpo,
)


def comprobar_ganador(tablero: list[str]) -> str | None:
    """Devuelve 'X', 'O' o None."""
    lineas = [
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6),
    ]

    ganador = None

    for a, b, c in lineas:
        if tablero[a] != "" and tablero[a] == tablero[b] and tablero[b] == tablero[c]:
            ganador = tablero[a]

    return ganador


def evaluar_tablero(tablero: list[str]) -> tuple[str, str | None]:
    """Metodo auxiliar que evalua el tablero para ver si tiene un ganador, un empate o la partida sigue"""
    ganador = comprobar_ganador(tablero)

    if ganador is not None:
        return "win", ganador

    if "" not in tablero:
        return "draw", None

    return "continue", None

# ═══════════════════════════════════════════════════════════════════════════
#  ComportamientoPartida
# ═══════════════════════════════════════════════════════════════════════════
class ComportamientoPartida(CyclicBehaviour):
    """Escucha constantemente mensajes del tablero y actúa en función de como vaya la partida.

        Tiene distintos métodos auxiliares para realizar las distintas acciones, y así seguir
        una lógica totalmente desacoplada y más fácil de entender
    """

    def __init__(self, tablero_jid: str, mi_simbolo: str, thread_partida: str):
        super().__init__()
        self.tablero_jid = tablero_jid
        self.mi_simbolo = mi_simbolo
        self.thread_partida = thread_partida

        self.oponente = None
        self.partida_iniciada = False
        self.tablero_local = [""] * 9

    async def enviar_movimiento(self, posicion: int, msg_original):
        """Crea el mensaje con el movimiento que va ha realizar y se lo envía al tablero"""

        contenido = crear_cuerpo_move(posicion)
        msg = msg_original.make_reply()
        msg.thread = self.thread_partida
        msg.set_metadata("ontology", ONTOLOGIA)
        msg.set_metadata("performative", contenido.performativa)
        msg.body = contenido.cuerpo

        await self.send(msg)

        print(f"[JUGADOR {self.agent.player_name}] Movimiento enviado a {self.tablero_jid} | posición: {posicion} | thread: {self.thread_partida}")

    async def enviar_ok(self, msg_original):
        """Si no es su turno envía el mensaje de "ok" al tablero
            para indicar que sigue en la partida.
        """

        contenido = crear_cuerpo_ok()

        msg = msg_original.make_reply()
        msg.thread = self.thread_partida
        msg.set_metadata("ontology", ONTOLOGIA)
        msg.set_metadata("performative", contenido.performativa)
        msg.body = contenido.cuerpo

        await self.send(msg)

        print(
            f"[JUGADOR {self.agent.player_name}] OK enviado a {self.tablero_jid} "
            f"| thread: {self.thread_partida}"
        )

    async def enviar_resultado_turno(self, resultado: str, ganador: str | None = None, msg_original=None):
        contenido = crear_cuerpo_turn_result(resultado, ganador)

        msg = msg_original.make_reply()
        msg.thread = self.thread_partida
        msg.set_metadata("ontology", ONTOLOGIA)
        msg.set_metadata("performative", contenido.performativa)
        msg.body = contenido.cuerpo

        await self.send(msg)

        print(
            f"[JUGADOR {self.agent.player_name}] Resultado de turno enviado a {self.tablero_jid} "
            f"| resultado: {resultado} | ganador: {ganador} | thread: {self.thread_partida}"
        )

    def actualizar_tablero_local(self, posicion: int, simbolo: str):
        """Actualiza el tablero local para ir evaluandolo"""

        if 0 <= posicion <= 8 and self.tablero_local[posicion] == "":
            self.tablero_local[posicion] = simbolo

    def limpiar_partida(self):
        """Reinicia la partida"""

        if self.thread_partida in self.agent.partidas_activas:
            del self.agent.partidas_activas[self.thread_partida]

        if self.tablero_jid in self.agent.tableros_contactados:
            self.agent.tableros_contactados.discard(self.tablero_jid)

    async def run(self):
        msg = await self.receive(timeout=30)

        #Si no ha recibido mensajes del tablero en el tiempo
        #límite reinicia la partida
        if msg is None:
            self.limpiar_partida()

            print(f"[JUGADOR {self.agent.player_name}] Timeout esperando mensajes del tablero | tablero: {self.tablero_jid} | thread: {self.thread_partida}")

            self.kill()
            return

        cuerpo = json.loads(msg.body)
        errores = validar_cuerpo(cuerpo)

        #Comprueba que el cuerpo del mensaje es válido
        if not errores["valido"]:
            return

        performativa = msg.get_metadata("performative")
        accion = cuerpo.get("action")

        # Si es el mensaje de comienzo partida guarda todos los datos
        if performativa == PERFORMATIVA_INFORM and accion == "game-start":
            self.agent.partidas_pendientes.pop(self.thread_partida, None)

            self.oponente = cuerpo["opponent"]
            self.partida_iniciada = True

            self.agent.partidas_activas[self.thread_partida] = {
                "tablero": self.tablero_jid,
                "mi_simbolo": self.mi_simbolo,
                "oponente": self.oponente,
            }

            print(
                f"[JUGADOR {self.agent.player_name}] ¡Partida iniciada! "
                f"| tablero: {self.tablero_jid} | símbolo: {self.mi_simbolo} "
                f"| rival: {self.oponente} | thread: {self.thread_partida}"
            )

        # Si es el mensaje de turno analiza la partida y envía el movimiento
        elif performativa == PERFORMATIVA_CFP and accion == "turn":
            #Aquí hace una comprobación por si ha recibido el
            #mensaje de turno antes que el de comienzo de partida
            if not self.partida_iniciada:
                self.partida_iniciada = True

                if self.thread_partida not in self.agent.partidas_activas:
                    self.agent.partidas_activas[self.thread_partida] = {
                        "tablero": self.tablero_jid,
                        "mi_simbolo": self.mi_simbolo,
                        "oponente": self.oponente,
                    }

                print(
                    f"[JUGADOR {self.agent.player_name}] CFP recibido antes que game-start "
                    f"| tablero: {self.tablero_jid} | thread: {self.thread_partida}"
                )

            simbolo_activo = cuerpo["active_symbol"]

            #Antes de enviar el movimiento comprueba que efectivamente es su turno
            if simbolo_activo == self.mi_simbolo:
                posicion = self.agent.elegir_movimiento(self.tablero_local, self.mi_simbolo)
                await self.enviar_movimiento(posicion, msg)
            else:
                await self.enviar_ok(msg)

        # Una vez el movimiento es aceptado actualiza el tablero local
        # y evalúa si la partida sigue o ha terminado
        elif performativa == PERFORMATIVA_ACCEPT_PROPOSAL and accion == "move":
            posicion = cuerpo["position"]
            simbolo = cuerpo["symbol"]

            self.actualizar_tablero_local(posicion, simbolo)

            resultado, ganador = evaluar_tablero(self.tablero_local)

            if simbolo == self.mi_simbolo:
                await self.enviar_resultado_turno(resultado, ganador, msg)

            if resultado in ("win", "draw"):
                print(
                    f"[JUGADOR {self.agent.player_name}] Partida finalizada "
                    f"| tablero: {self.tablero_jid} | resultado: {resultado} "
                    f"| ganador: {ganador} | thread: {self.thread_partida}"
                )

                self.limpiar_partida()
                self.kill()

        elif performativa == PERFORMATIVA_REJECT_PROPOSAL and accion == "game-over":
            razon = cuerpo["reason"]
            ganador = cuerpo.get("winner")

            print(
                f"[JUGADOR {self.agent.player_name}] Partida finalizada "
                f"| tablero: {self.tablero_jid} | motivo: {razon} "
                f"| ganador: {ganador} | thread: {self.thread_partida}"
            )

            self.limpiar_partida()
            self.kill()