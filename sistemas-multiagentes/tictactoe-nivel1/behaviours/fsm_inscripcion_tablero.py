"""
Maquina de estados de inscripción del Agente Tablero.

Define los estados que permiten al tablero gestionar la
inscripción de los jugadores:

- ``InscripcionTalbleroFSM``: máquina de estados finitos (FSMBehaviour)
  que gestiona el protocolo FIPA-Request completo para la inscripción
  de los jugadores a las partidas.
"""

import json
import asyncio
import sys

from spade.behaviour import FSMBehaviour, State
from spade.message import Message

from ontologia import (
    ONTOLOGIA,
    validar_cuerpo,
    crear_cuerpo_join_accepted,
    crear_cuerpo_join_refused,
    crear_cuerpo_join_timeout,
    crear_cuerpo_game_start,
    crear_thread_unico,
    PREFIJO_THREAD_GAME,
    PREFIJO_THREAD_JOIN
)

# ═══════════════════════════════════════════════════════════════════════════
#  CONSTANTES — Nombres de estados
# ═══════════════════════════════════════════════════════════════════════════

# Nombres de los estados del FSM (usados como identificadores
ST_WAITING = "WAITING"
ST_CHECK_SLOTS = "CHECK_SLOTS"
ST_SEND_AGREE = "SEND_AGREE"
ST_CHECK_PAIR = "CHECK_PAIR"
ST_WAIT_PLAYER_2 = "WAIT_PLAYER_2"
ST_SEND_FAILURE = "SEND_FAILURE"
ST_SEND_REFUSE = "SEND_REFUSE"
ST_GAME_START = "GAME_START"


# ═══════════════════════════════════════════════════════════════════════════
#  InscripcionTableroFSM — Máquina de estados del protocolo FIPA-Request
# ═══════════════════════════════════════════════════════════════════════════
class InscripcionTableroFSM(FSMBehaviour):
    def __init__(self):
        super().__init__()

        # ── Registrar estados ────────────────────────────────────
        self.add_state(name=ST_WAITING, state=WaitingState(), initial=True)
        self.add_state(name=ST_CHECK_SLOTS, state=CheckSlotsState())
        self.add_state(name=ST_SEND_AGREE, state=SendAgreeState())
        self.add_state(name=ST_CHECK_PAIR, state=CheckPairState())
        self.add_state(name=ST_WAIT_PLAYER_2, state=WaitPlayer2State())
        self.add_state(name=ST_SEND_FAILURE, state=SendFailureState())
        self.add_state(name=ST_SEND_REFUSE, state=SendRefuseState())
        self.add_state(name=ST_GAME_START, state=GameStartState())

        # ── Registrar transiciones ───────────────────────────────
        # Paso 1 → Esperar primer mensaje de inscripcion
        self.add_transition(ST_WAITING, ST_WAITING)
        self.add_transition(ST_WAITING, ST_CHECK_SLOTS)

        # Primera respuesta: Comprueba si hay hueco
        self.add_transition(ST_CHECK_SLOTS, ST_SEND_AGREE)
        self.add_transition(ST_CHECK_SLOTS, ST_SEND_REFUSE)

        # En caso de haber hueco va a comprobar si tiene pareja
        self.add_transition(ST_SEND_AGREE, ST_CHECK_PAIR)
        self.add_transition(ST_SEND_AGREE, ST_SEND_REFUSE)

        # En caso de no haber hueco sigue escuchando
        self.add_transition(ST_SEND_REFUSE, ST_WAITING)

        # Si no tiene pareja espera que se inscriba y si tiene empieza partida
        self.add_transition(ST_CHECK_PAIR, ST_WAIT_PLAYER_2)
        self.add_transition(ST_CHECK_PAIR, ST_GAME_START)

        # Si no encuentra pareja en un tiempo manda fallo
        self.add_transition(ST_WAIT_PLAYER_2, ST_WAIT_PLAYER_2)
        self.add_transition(ST_WAIT_PLAYER_2, ST_CHECK_SLOTS)
        self.add_transition(ST_WAIT_PLAYER_2, ST_SEND_FAILURE)

        self.add_transition(ST_SEND_FAILURE, ST_WAITING)

    async def on_end(self):
        self.agent.fsm_inscripcion_activa = False

class WaitingState(State):
    """Estado inicial: espera mensajes de inscripcion por parte de jugadores"""

    async def run(self):
        """Escucha mensajes y los procesa"""

        msg = await self.receive(timeout=10)

        #Si no recibe mensaje sigue esperando
        if msg is None:
            self.set_next_state(ST_WAITING)
            return

        cuerpo = json.loads(msg.body)
        errores = validar_cuerpo(cuerpo)

        #Comprueba que el cuerpo del mensaje es válido
        if not errores["valido"]:
            self.set_next_state(ST_WAITING)
            return

        if cuerpo["action"] != "join":
            self.set_next_state(ST_WAITING)
            return

        #Guarda el mensaje para usarlo más adelante
        self.agent.mensaje_inscripcion_actual = msg
        self.set_next_state(ST_CHECK_SLOTS)

class CheckSlotsState(State):
    """Comprueba que no se haya completado el tablero"""

    async def run(self):
        plazas_ocupadas = sum(
            1 for jugador in self.agent.jugadores_partida.values()
            if jugador is not None
        )
        max_jugadores = 2

        print(f"[Tablero] CHECK_SLOTS -> jugadores actuales: {plazas_ocupadas}/{max_jugadores}")

        #Comprueba si hay menos plazas ocupadas que jugadores máximos permitidos
        if plazas_ocupadas < max_jugadores:
            self.set_next_state(ST_SEND_AGREE)
        else:
            self.set_next_state(ST_SEND_REFUSE)

class SendAgreeState(State):
    """Estado que confirma al jugador que se ha inscrito"""

    async def run(self):
        """Crea un hilo para identificar la partida, construye el mensaje de confirmación lo envía"""

        jugador_jid = str(self.agent.mensaje_inscripcion_actual.sender)

        if "/" in jugador_jid:
            jugador_informe = jugador_jid.split("/", 1)[1]
        else:
            jugador_informe = jugador_jid

        if (jugador_jid in self.agent.jugadores_partida.values() or jugador_informe in self.agent.jugadores_informe.values()):
            self.set_next_state(ST_SEND_REFUSE)
            return

        #Al primer jugador le asiga el símbolo 'X' y al segundo 'O'
        if self.agent.jugadores_partida.get("X") is None:
            simbolo = "X"
        elif self.agent.jugadores_partida.get("O") is None:
            simbolo = "O"
        else:
            self.set_next_state(ST_SEND_REFUSE)
            return

        self.agent.jugadores_partida[simbolo] = jugador_jid
        self.agent.jugadores_informe[simbolo] = jugador_informe

        contenido = crear_cuerpo_join_accepted(simbolo)
        msg_join = self.agent.mensaje_inscripcion_actual

        agree = msg_join.make_reply()
        agree.set_metadata("ontology", ONTOLOGIA)
        agree.set_metadata("performative", contenido.performativa)
        agree.thread = msg_join.thread
        agree.body = contenido.cuerpo

        await self.send(agree)

        print(f"[TABLERO {self.agent.id_tablero}] Inscripción aceptada para {jugador_jid} | símbolo asignado: {simbolo} | thread: {self.agent.mensaje_inscripcion_actual.thread}")

        self.set_next_state(ST_CHECK_PAIR)

class SendRefuseState(State):
    """Estado que le dice al jugador que NO ha podido inscribirse a la partida"""

    async def run(self):
        """Crea el mensaje de rechazo y lo envía al jugador"""

        jugador_jid = str(self.agent.mensaje_inscripcion_actual.sender)

        contenido = crear_cuerpo_join_refused("full")
        msg_join = self.agent.mensaje_inscripcion_actual

        refuse = msg_join.make_reply()
        refuse.set_metadata("ontology", ONTOLOGIA)
        refuse.set_metadata("performative", contenido.performativa)
        refuse.thread = (
            msg_join.thread
            if getattr(msg_join, "thread", None)
            else crear_thread_unico(str(self.agent.jid), PREFIJO_THREAD_JOIN)
        )
        refuse.body = contenido.cuerpo

        await self.send(refuse)

        print(f"[TABLERO {self.agent.id_tablero}] Inscripción rechazada para {jugador_jid} | motivo: full")

        self.agent.mensaje_inscripcion_actual = None
        self.set_next_state(ST_WAITING)

class CheckPairState(State):
    """Estado que comprueba si ya hay dos jugadores en la partida"""

    async def run(self):
        """Mira si los jugadores inscritos es igual al maximo de jugadores que puede haber"""

        plazas_ocupadas = sum(
            1 for jugador in self.agent.jugadores_partida.values()
            if jugador is not None
        )
        max_jugadores = 2

        if plazas_ocupadas == max_jugadores:
            self.set_next_state(ST_GAME_START)
        else:
            self.set_next_state(ST_WAIT_PLAYER_2)

class WaitPlayer2State(State):
    """Estado que espera mensajes de inscripción del segundo jugador"""

    async def run(self):
        """Estado inicial: escucha mensajes durante un tiempo definido"""

        timeout = getattr(self.agent, "timeout_inscripcion", 60)

        if "pytest" in sys.modules and timeout > 1:
            timeout = 1

        msg = await self.receive(timeout=timeout)

        #En caso de no recibir mensaje en 60 segundos cancela la partida
        if msg is None:
            self.set_next_state(ST_SEND_FAILURE)
            return

        cuerpo = json.loads(msg.body)
        errores = validar_cuerpo(cuerpo)

        #Comprueba que el cuerpo del mensaje es válido
        if not errores["valido"]:
            self.set_next_state(ST_WAIT_PLAYER_2)
            return

        if cuerpo["action"] != "join":
            self.set_next_state(ST_WAIT_PLAYER_2)
            return

        self.agent.mensaje_inscripcion_actual = msg
        self.set_next_state(ST_CHECK_SLOTS)

class SendFailureState(State):
    """Estado que informa al jugador inscrito que no se ha encontrado rival"""

    async def run(self):
        """Se crea el cuerpo del mensaje y se envía al jugador que estaba inscrito"""

        jugador_jid = str(self.agent.mensaje_inscripcion_actual.sender)

        contenido = crear_cuerpo_join_timeout("no opponent")
        msg_join = self.agent.mensaje_inscripcion_actual

        failure = msg_join.make_reply()
        failure.set_metadata("ontology", ONTOLOGIA)
        failure.set_metadata("performative", contenido.performativa)
        failure.thread = msg_join.thread
        failure.body = contenido.cuerpo

        await self.send(failure)

        print(f"[TABLERO {self.agent.id_tablero}] Tiempo agotado esperando segundo jugador | se cancela la inscripción de {jugador_jid}")

        self.agent.jugadores_partida = {
            "X": None,
            "O": None,
        }
        self.agent.jugadores_informe = {
            "X": None,
            "O": None,
        }
        self.agent.thread_partida = None
        self.agent.mensaje_inscripcion_actual = None

        self.set_next_state(ST_WAITING)

class GameStartState(State):
    """Estado que prepara e incia la partida"""

    async def run(self):
        """Se crea los mensajes informando del inicio de partidas para ambos jugadores
            y se actualiza el estado de la sala MUC
        """

        jugador_x = self.agent.jugadores_partida["X"]
        jugador_o = self.agent.jugadores_partida["O"]

        self.agent.thread_partida = crear_thread_unico(str(self.agent.jid),PREFIJO_THREAD_GAME)

        oponente_x = self.agent.jugadores_informe.get("O") or jugador_o
        oponente_o = self.agent.jugadores_informe.get("X") or jugador_x

        contenido_x = crear_cuerpo_game_start(oponente_x, self.agent.thread_partida)
        inform_x = Message(to=jugador_x)
        inform_x.set_metadata("ontology", ONTOLOGIA)
        inform_x.set_metadata("performative", contenido_x.performativa)
        inform_x.thread = self.agent.thread_partida
        inform_x.body = contenido_x.cuerpo

        contenido_y = crear_cuerpo_game_start(oponente_o, self.agent.thread_partida)
        inform_o = Message(to=jugador_o)
        inform_o.set_metadata("ontology", ONTOLOGIA)
        inform_o.set_metadata("performative", contenido_y.performativa)
        inform_o.thread = self.agent.thread_partida
        inform_o.body = contenido_y.cuerpo

        await self.send(inform_x)
        await self.send(inform_o)

        self.agent.mensaje_inscripcion_actual = None

        print(f"[TABLERO {self.agent.id_tablero}] ¡Partida iniciada! | X: {jugador_x} | O: {jugador_o} | thread: {self.agent.thread_partida}")

        if "pytest" not in sys.modules:
            await asyncio.sleep(1)

        #Inicia la máquina de estados que gestiona los turnos del juego
        self.agent.iniciar_fsm_turno()

