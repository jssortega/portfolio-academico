"""
Maquina de estados de turnos del Agente Tablero.

Define los estados que permiten al tablero gestionar los
turnos de la partida:

- ``TurnoTableroFSM``: máquina de estados finitos (FSMBehaviour)
  que gestiona el protocolo FIPA Contract Net completo para el
  desarrollo de los turnos de cada partida.
"""

import json
import time

from spade.behaviour import FSMBehaviour, State
from spade.message import Message

from ontologia import (
    ONTOLOGIA, validar_cuerpo,
    crear_cuerpo_turn, crear_cuerpo_move_confirmado,
    crear_cuerpo_game_over
)

ST_SEND_CFP = "SEND_CFP"
ST_WAIT_PROPOSALS = "WAIT_PROPOSALS"
ST_CHECK_MOVIMIENTO = "CHECK_MOVIMIENTO"
ST_SEND_ACCEPT = "SEND_ACCEPT"
ST_WAIT_RESULT = "WAIT_RESULT"
ST_CHECK_RESULT = "CHECK_RESULT"
ST_NEXT_TURN = "NEXT_TURN"
ST_SEND_REJECT = "SEND_REJECT"
ST_FIN_PARTIDA = "FIN_PARTIDA"

TIMEOUT_TURNO = 1.2
TIMEOUT_CORTESIA_PRIMER_CFP = 0.55


def comprobar_ganador(tablero: list[str]) -> str | None:
    lineas = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Filas
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columnas
        (0, 4, 8), (2, 4, 6)  # Diagonales
    ]

    for a, b, c in lineas:
        if tablero[a] == tablero[b] == tablero[c] and tablero[a] != "":
            return tablero[a]

    return None

def evaluar_tablero(tablero: list[str]) -> tuple[str, str | None]:
    ganador = comprobar_ganador(tablero)

    if ganador is not None:
        return "win", ganador

    if "" not in tablero:
        return "draw", None

    return "continue", None


class TurnoTableroFSM(FSMBehaviour):
    def __init__(self):
        super().__init__()

        self.add_state(name=ST_SEND_CFP, state=SendCFPState(), initial=True)
        self.add_state(name=ST_WAIT_PROPOSALS, state=WaitProposalsState())
        self.add_state(name=ST_CHECK_MOVIMIENTO, state=CheckMovimientoState())
        self.add_state(name=ST_SEND_ACCEPT, state=SendAcceptState())
        self.add_state(name=ST_WAIT_RESULT, state=WaitResultState())
        self.add_state(name=ST_CHECK_RESULT, state=CheckResultState())
        self.add_state(name=ST_NEXT_TURN, state=NextTurnState())
        self.add_state(name=ST_SEND_REJECT, state=SendRejectState())
        self.add_state(name=ST_FIN_PARTIDA, state=FinPartidaState())

        self.add_transition(ST_SEND_CFP, ST_WAIT_PROPOSALS)

        self.add_transition(ST_WAIT_PROPOSALS, ST_SEND_REJECT)
        self.add_transition(ST_WAIT_PROPOSALS, ST_CHECK_MOVIMIENTO)

        self.add_transition(ST_CHECK_MOVIMIENTO, ST_SEND_ACCEPT)
        self.add_transition(ST_CHECK_MOVIMIENTO, ST_SEND_REJECT)

        self.add_transition(ST_SEND_ACCEPT, ST_WAIT_RESULT)

        self.add_transition(ST_WAIT_RESULT, ST_CHECK_RESULT)
        self.add_transition(ST_WAIT_RESULT, ST_SEND_REJECT)

        self.add_transition(ST_CHECK_RESULT, ST_NEXT_TURN)
        self.add_transition(ST_CHECK_RESULT, ST_FIN_PARTIDA)
        self.add_transition(ST_CHECK_RESULT, ST_SEND_REJECT)

        self.add_transition(ST_NEXT_TURN, ST_SEND_CFP)

        self.add_transition(ST_SEND_REJECT, ST_FIN_PARTIDA)

class SendCFPState(State):
    async def run(self):
        jugador_x = self.agent.jugadores_partida["X"]
        jugador_o = self.agent.jugadores_partida["O"]

        simbolo_activo = self.agent.turno_actual

        self.agent.propuesta_turno = None
        self.agent.ok_turno = None
        self.agent.timeout_turno = False
        self.agent.inicio_turno = time.time()

        if len(getattr(self.agent, "historial", [])) == 0:
            self.agent.reintento_cfp_inicial_usado = False

        contenido = crear_cuerpo_turn(simbolo_activo)
        turno_x = Message(to=jugador_x)
        turno_x.set_metadata("ontology", ONTOLOGIA)
        turno_x.set_metadata("performative", contenido.performativa)
        turno_x.thread = self.agent.thread_partida
        turno_x.body = contenido.cuerpo

        turno_o = Message(to=jugador_o)
        turno_o.set_metadata("ontology", ONTOLOGIA)
        turno_o.set_metadata("performative", contenido.performativa)
        turno_o.thread = self.agent.thread_partida
        turno_o.body = contenido.cuerpo

        await self.send(turno_x)
        await self.send(turno_o)

        self.set_next_state(ST_WAIT_PROPOSALS)

class WaitProposalsState(State):
    async def run(self):
        simbolo_activo = self.agent.turno_actual
        simbolo_rival = "O" if simbolo_activo == "X" else "X"

        jid_activo = self.agent.jugadores_partida[simbolo_activo]
        jid_rival = self.agent.jugadores_partida[simbolo_rival]

        self.agent.propuesta_turno = None
        self.agent.ok_turno = None

        self.agent.motivo_rechazo = None
        self.agent.ganador_rechazo = None

        reintento_disponible = (
            len(getattr(self.agent, "historial", [])) == 0
            and not getattr(self.agent, "reintento_cfp_inicial_usado", False)
        )

        timeout_actual = (
            TIMEOUT_CORTESIA_PRIMER_CFP
            if reintento_disponible
            else TIMEOUT_TURNO
        )
        tiempo_total = time.monotonic() + timeout_actual

        while True:
            if self.agent.propuesta_turno is not None and self.agent.ok_turno is not None:
                self.set_next_state(ST_CHECK_MOVIMIENTO)
                return

            restante = tiempo_total - time.monotonic()

            if restante <= 0:
                if (
                    reintento_disponible
                    and self.agent.propuesta_turno is None
                    and self.agent.ok_turno is None
                ):
                    contenido = crear_cuerpo_turn(simbolo_activo)

                    turno_x = Message(to=self.agent.jugadores_partida["X"])
                    turno_x.set_metadata("ontology", ONTOLOGIA)
                    turno_x.set_metadata("performative", contenido.performativa)
                    turno_x.thread = self.agent.thread_partida
                    turno_x.body = contenido.cuerpo

                    turno_o = Message(to=self.agent.jugadores_partida["O"])
                    turno_o.set_metadata("ontology", ONTOLOGIA)
                    turno_o.set_metadata("performative", contenido.performativa)
                    turno_o.thread = self.agent.thread_partida
                    turno_o.body = contenido.cuerpo

                    await self.send(turno_x)
                    await self.send(turno_o)

                    self.agent.reintento_cfp_inicial_usado = True
                    reintento_disponible = False
                    tiempo_total = time.monotonic() + TIMEOUT_TURNO
                    continue

                break

            msg = await self.receive(timeout=restante)

            if msg is None:
                if (
                    reintento_disponible
                    and self.agent.propuesta_turno is None
                    and self.agent.ok_turno is None
                ):
                    contenido = crear_cuerpo_turn(simbolo_activo)

                    turno_x = Message(to=self.agent.jugadores_partida["X"])
                    turno_x.set_metadata("ontology", ONTOLOGIA)
                    turno_x.set_metadata("performative", contenido.performativa)
                    turno_x.thread = self.agent.thread_partida
                    turno_x.body = contenido.cuerpo

                    turno_o = Message(to=self.agent.jugadores_partida["O"])
                    turno_o.set_metadata("ontology", ONTOLOGIA)
                    turno_o.set_metadata("performative", contenido.performativa)
                    turno_o.thread = self.agent.thread_partida
                    turno_o.body = contenido.cuerpo

                    await self.send(turno_x)
                    await self.send(turno_o)

                    self.agent.reintento_cfp_inicial_usado = True
                    reintento_disponible = False
                    tiempo_total = time.monotonic() + TIMEOUT_TURNO
                    continue

                break

            if msg.thread != self.agent.thread_partida:
                continue

            remitente = str(msg.sender)
            cuerpo = json.loads(msg.body)

            errores = validar_cuerpo(cuerpo)
            if not errores["valido"]:
                self.agent.motivo_rechazo = "invalid"
                self.agent.ganador_rechazo = (
                    simbolo_rival if remitente == jid_activo else simbolo_activo
                )
                self.set_next_state(ST_SEND_REJECT)
                return

            if remitente == jid_activo:
                if cuerpo.get("action") != "move":
                    continue

                self.agent.propuesta_turno = msg

            elif remitente == jid_rival:
                if cuerpo.get("action") != "ok":
                    continue

                self.agent.ok_turno = msg

        if self.agent.propuesta_turno is None and self.agent.ok_turno is None:
            self.agent.motivo_rechazo = "both-timeout"
            self.agent.ganador_rechazo = None
        elif self.agent.propuesta_turno is not None:
            self.agent.motivo_rechazo = "timeout"
            self.agent.ganador_rechazo = simbolo_activo
        else:
            self.agent.motivo_rechazo = "timeout"
            self.agent.ganador_rechazo = simbolo_rival

        self.set_next_state(ST_SEND_REJECT)

class CheckMovimientoState(State):
    async def run(self):
        msg = self.agent.propuesta_turno

        if msg is None:
            self.agent.motivo_rechazo = "invalid"
            self.agent.ganador_rechazo = "O" if self.agent.turno_actual == "X" else "X"
            self.set_next_state(ST_SEND_REJECT)
            return

        cuerpo = json.loads(msg.body)
        posicion = cuerpo["position"]

        self.agent.posicion_turno = posicion

        if self.agent.tablero[posicion] == "":
            self.agent.posicion_turno = posicion
            self.set_next_state(ST_SEND_ACCEPT)
        else:
            self.agent.motivo_rechazo = "invalid"
            self.agent.ganador_rechazo = "O" if self.agent.turno_actual == "X" else "X"
            self.set_next_state(ST_SEND_REJECT)

class SendAcceptState(State):
    async def run(self):
        jugador_x = self.agent.jugadores_partida["X"]
        jugador_o = self.agent.jugadores_partida["O"]

        simbolo_activo = self.agent.turno_actual
        posicion = self.agent.posicion_turno

        self.agent.tablero[posicion] = simbolo_activo

        self.agent.historial.append({
            "turn": len(self.agent.historial) + 1,
            "symbol": simbolo_activo,
            "position": posicion,
            "board_snapshot": self.agent.tablero.copy(),
        })

        self.agent.turnos_jugados = len(self.agent.historial)

        contenido = crear_cuerpo_move_confirmado(posicion, simbolo_activo)
        accept_x = Message(to=jugador_x)
        accept_x.set_metadata("ontology", ONTOLOGIA)
        accept_x.set_metadata("performative", contenido.performativa)
        accept_x.thread = self.agent.thread_partida
        accept_x.body = contenido.cuerpo

        accept_o = Message(to=jugador_o)
        accept_o.set_metadata("ontology", ONTOLOGIA)
        accept_o.set_metadata("performative", contenido.performativa)
        accept_o.thread = self.agent.thread_partida
        accept_o.body = contenido.cuerpo

        await self.send(accept_x)
        await self.send(accept_o)

        self.set_next_state(ST_WAIT_RESULT)

class WaitResultState(State):
    async def run(self):
        simbolo_activo = self.agent.turno_actual
        simbolo_rival = "O" if simbolo_activo == "X" else "X"

        jid_activo = self.agent.jugadores_partida[simbolo_activo]

        self.agent.resultado_turno = None
        self.agent.motivo_rechazo = None
        self.agent.ganador_rechazo = None

        tiempo_total = time.monotonic() + TIMEOUT_TURNO

        while True:
            restante = tiempo_total - time.monotonic()

            if restante <= 0:
                self.agent.motivo_rechazo = "timeout"
                self.agent.ganador_rechazo = simbolo_rival
                self.set_next_state(ST_SEND_REJECT)
                return

            msg = await self.receive(timeout=restante)

            if msg is None:
                self.agent.motivo_rechazo = "timeout"
                self.agent.ganador_rechazo = simbolo_rival
                self.set_next_state(ST_SEND_REJECT)
                return

            if msg.thread != self.agent.thread_partida:
                continue

            remitente = str(msg.sender)

            # Puede quedar algún OK tardío del jugador no activo.
            # No debe abortar como invalid: simplemente no es el turn-result esperado.
            if remitente != jid_activo:
                continue

            cuerpo = json.loads(msg.body)

            errores = validar_cuerpo(cuerpo)
            if not errores["valido"]:
                self.agent.motivo_rechazo = "invalid"
                self.agent.ganador_rechazo = None
                self.set_next_state(ST_SEND_REJECT)
                return

            if cuerpo.get("action") != "turn-result":
                continue

            resultado = cuerpo.get("result")
            winner = cuerpo.get("winner", None)

            if resultado not in ("continue", "win", "draw"):
                self.agent.motivo_rechazo = "invalid"
                self.agent.ganador_rechazo = None
                self.set_next_state(ST_SEND_REJECT)
                return

            if resultado == "win" and winner not in ("X", "O"):
                self.agent.motivo_rechazo = "invalid"
                self.agent.ganador_rechazo = None
                self.set_next_state(ST_SEND_REJECT)
                return

            if resultado == "win" and winner != simbolo_activo:
                self.agent.motivo_rechazo = "invalid"
                self.agent.ganador_rechazo = simbolo_rival
                self.set_next_state(ST_SEND_REJECT)
                return

            if resultado in ("continue", "draw") and winner is not None:
                self.agent.motivo_rechazo = "invalid"
                self.agent.ganador_rechazo = None
                self.set_next_state(ST_SEND_REJECT)
                return

            self.agent.resultado_turno = {
                "result": resultado,
                "winner": winner,
                "sender": remitente,
                "symbol": simbolo_activo,
            }

            self.set_next_state(ST_CHECK_RESULT)
            return

class CheckResultState(State):
    async def run(self):
        resultado_turno = self.agent.resultado_turno

        if resultado_turno is None:
            self.agent.motivo_rechazo = "invalid"
            self.agent.ganador_rechazo = None
            self.set_next_state(ST_SEND_REJECT)
            return

        resultado = resultado_turno["result"]
        winner = resultado_turno.get("winner")

        #El tablero comprueba los resultados también para asegurar
        resultado_real, winner_real = evaluar_tablero(self.agent.tablero)

        if resultado != resultado_real:
            self.agent.motivo_rechazo = "invalid"
            self.agent.ganador_rechazo = ("O" if self.agent.turno_actual == "X" else "X")
            self.set_next_state(ST_SEND_REJECT)
            return

        if winner != winner_real:
            self.agent.motivo_rechazo = "invalid"
            self.agent.ganador_rechazo = (
                "O" if self.agent.turno_actual == "X" else "X"
            )
            self.set_next_state(ST_SEND_REJECT)
            return

        if resultado == "continue":
            self.set_next_state(ST_NEXT_TURN)
            return

        if resultado == "draw":
            self.agent.resultado_final = "draw"
            self.agent.ganador_final = None
            self.agent.razon_final = None
            self.set_next_state(ST_FIN_PARTIDA)
            return

        if resultado == "win":
            self.agent.resultado_final = "win"
            self.agent.ganador_final = winner
            self.agent.razon_final = None
            self.set_next_state(ST_FIN_PARTIDA)
            return

        self.agent.motivo_rechazo = "invalid"
        self.agent.ganador_rechazo = None
        self.set_next_state(ST_SEND_REJECT)

class NextTurnState(State):
    async def run(self):
        if self.agent.turno_actual == "X":
            self.agent.turno_actual = "O"
        else:
            self.agent.turno_actual = "X"

        self.agent.propuesta_turno = None
        self.agent.ok_turno = None
        self.agent.posicion_turno = None
        self.agent.resultado_turno = None
        self.agent.motivo_rechazo = None
        self.agent.ganador_rechazo = None

        self.set_next_state(ST_SEND_CFP)

class SendRejectState(State):
    async def run(self):
        jugador_x = self.agent.jugadores_partida["X"]
        jugador_o = self.agent.jugadores_partida["O"]

        razon = self.agent.motivo_rechazo
        ganador = self.agent.ganador_rechazo

        contenido = crear_cuerpo_game_over(razon, ganador)
        reject_x = Message(to=jugador_x)
        reject_x.set_metadata("ontology", ONTOLOGIA)
        reject_x.set_metadata("performative", contenido.performativa)
        reject_x.thread = self.agent.thread_partida
        reject_x.body = contenido.cuerpo

        reject_o = Message(to=jugador_o)
        reject_o.set_metadata("ontology", ONTOLOGIA)
        reject_o.set_metadata("performative", contenido.performativa)
        reject_o.thread = self.agent.thread_partida
        reject_o.body = contenido.cuerpo

        self.agent.resultado_final = "aborted"
        self.agent.ganador_final = ganador
        self.agent.razon_final = razon

        await self.send(reject_x)
        await self.send(reject_o)

        self.set_next_state(ST_FIN_PARTIDA)

class FinPartidaState(State):
    async def run(self):
        self.agent.estado_partida = "finished"
        self.agent.publicar_estado("finished")

        if not hasattr(self.agent, "historial"):
            self.agent.historial = []

        if not hasattr(self.agent, "turnos_jugados"):
            self.agent.turnos_jugados = len(self.agent.historial)

        self.agent.turno_actual = None
        self.agent.ultimo_estado_final_web = self.agent.obtener_estado_web()

        self.agent.ultimo_informe_partida = {
            "result": self.agent.resultado_final,
            "winner": self.agent.ganador_final if self.agent.resultado_final == "win" else None,
            "players": {
                "X": self.agent.jugadores_informe.get("X") or self.agent.jugadores_partida.get("X"),
                "O": self.agent.jugadores_informe.get("O") or self.agent.jugadores_partida.get("O"),
            },
            "turns": self.agent.turnos_jugados,
            "board": self.agent.tablero.copy(),
            "reason": getattr(self.agent, "razon_final", None),
            "history": self.agent.historial.copy(),
            "thread": self.agent.thread_partida,
        }

        print(
            f"[TABLERO {self.agent.id_tablero}] Partida finalizada: "
            f"resultado={self.agent.resultado_final}, "
            f"ganador={self.agent.ganador_final}, "
            f"razon={getattr(self.agent, 'razon_final', None)}"
        )

        self.kill()



