"""
Agente Tablero del sistema Tic-Tac-Toe Multiagente.

Publica su estado en las salas MUC, escucha inscripciones de
jugadores, gestiona los turnos de la partida e informa al
supervisor con el curso de la partida producida.

Además, expone una web accesible en el puerto configurado
que permite visualizar en tiempo real las partidas que se
están produciendo simultáneamente.
"""

from spade.agent import Agent
from spade.template import Template

from agentes.muc_utils import setup_muc, actualizar_estado_muc

from ontologia.ontologia import (
    ONTOLOGIA,
    PERFORMATIVA_REQUEST,
    obtener_conversation_id
)
from behaviours.fsm_inscripcion_tablero import InscripcionTableroFSM
from behaviours.fsm_turno_tablero import TurnoTableroFSM
from behaviours.responder_informe_supervisor import ResponderInformeSupervisor

from web.tablero_handlers import game_state_handler, game_page_handler
import pathlib


class AgenteTablero(Agent):
    """Agente que crea el tablero y se hace visible a través de la sala MUC"""

    async def setup(self):
        """Inicializa el tablero: estado interno, salas MUC, behaviours y web.

                Inicializa las variables del agente, publica su estado en la sala
                MUC, y comienza el proceso de inscripción con los jugadores a
                través de una máquina de estados.
        """

        nombre_agente = str(self.jid).split("@")[0]

        parametros = getattr(self, "config_parametros", {}) or {}

        self.timeout_inscripcion = parametros.get("timeout_inscripcion", 60)

        self.id_tablero = parametros.get(
            "id_tablero",
            nombre_agente.removeprefix("tablero_")
        )
        nick_base = str(parametros.get("nick_muc", self.id_tablero))

        if nick_base.startswith("tablero_"):
            self.muc_nick = nick_base
        else:
            self.muc_nick = f"tablero_{nick_base}"

        self.muc_room = setup_muc(self, apodo=self.muc_nick)

        #Variables para la configuración web
        self.puerto_web = parametros.get("puerto_web", 8081)

        self.reiniciar_estado_partida()
        self.activar_respuesta_informe_supervisor()

        self.web.app["agent"] = self
        self.web.app.router.add_get("/game/state", game_state_handler)
        self.web.app.router.add_get("/game", game_page_handler)

        static_path = pathlib.Path("web/static").resolve()
        self.web.app.router.add_static("/static/", path=str(static_path))

        await self.web.start(hostname="0.0.0.0", port=self.puerto_web)

        #En primer lugar publica el estado como "waiting" en la sala MUC
        actualizar_estado_muc(self, self.muc_room, self.muc_nick, "waiting")
        print(f"[TABLERO] Conectado a {self.muc_room} como {self.muc_nick}")

        #Comienza el protocolo de inscripción para escuchar mensajes de inscripción de los jugadores
        self.activar_fsm_inscripcion()

    def publicar_estado(self, estado: str):
        """Metodo auxiliar que recibe el estado del tablero en la sala MUC y lo publica"""

        actualizar_estado_muc(self, self.muc_room, self.muc_nick, estado)

    def reiniciar_estado_partida(self):
        """Metodo auxiliar para inicializar todas las variables necessarias
            del agente para el desarrollo de la partida.
        """

        self.jugadores_partida = {
            "X": None,
            "O": None,
        }
        self.jugadores_informe = {
            "X": None,
            "O": None,
        }
        self.thread_partida = None
        self.mensaje_inscripcion_actual = None

        self.tablero = [""] * 9
        self.turno_actual = None
        self.estado_partida = "waiting"

        self.posicion_turno = None
        self.propuesta_turno = None
        self.ok_turno = None

        self.resultado_turno = None

        self.motivo_rechazo = None
        self.ganador_rechazo = None

        self.resultado_final = None
        self.ganador_final = None
        self.razon_final = None

        self.historial = []
        self.turnos_jugados = 0

        # No borra el último informe
        if not hasattr(self, "ultimo_informe_partida"):
            self.ultimo_informe_partida = None

        if not hasattr(self, "ultimo_estado_final_web"):
            self.ultimo_estado_final_web = None

    def activar_fsm_inscripcion(self):
        """Metodo que crea el template para filtrar mensajes de inscripcion por parte
            de los jugadores y arranca el FSM
        """

        if getattr(self, "fsm_inscripcion_activa", False):
            return

        template_inscripcion = Template()
        template_inscripcion.set_metadata("ontology", ONTOLOGIA)
        template_inscripcion.set_metadata("performative", PERFORMATIVA_REQUEST)
        template_inscripcion.set_metadata("conversation-id", obtener_conversation_id("join"))

        self.fsm_inscripcion_activa = True
        self.add_behaviour(InscripcionTableroFSM(), template_inscripcion)

    def activar_respuesta_informe_supervisor(self):
        """Crea el template del protocolo de informe y arranca el behaviour."""

        template_informe = Template()
        template_informe.set_metadata("ontology", ONTOLOGIA)
        template_informe.set_metadata("performative", PERFORMATIVA_REQUEST)
        template_informe.set_metadata("conversation-id", obtener_conversation_id("game-report"))

        self.add_behaviour(ResponderInformeSupervisor(),template_informe)

    def iniciar_fsm_turno(self):
        """Metodo que crea el template para filtrar mensajes de turno según el hilo para
            diferenciar entre partidas, también inicia el comportamiento de partida
            del tablero y publica en la sala MUC que se encuentra jugando.
        """

        template_turno = Template()
        template_turno.set_metadata("ontology", ONTOLOGIA)
        template_turno.thread = self.thread_partida

        self.turno_actual = "X"
        self.estado_partida = "playing"

        self.add_behaviour(TurnoTableroFSM(), template_turno)
        self.publicar_estado("playing")

    def reactivar_para_nueva_partida(self):
        """Metodo que se usa para reiniciar todas las variables por defecto, publicar
            el estado en la sala MUC como "waiting" para que se puedan unir nuevos
            jugadores y volver al estado de inscripción.
        """

        self.reiniciar_estado_partida()
        self.publicar_estado("waiting")
        self.activar_fsm_inscripcion()

    def obtener_estado_web(self):
        """Devuelve el estado actual del tablero en formato listo para /game/state."""
        return {
            "board": self.tablero.copy(),
            "players": {
                "X": self.jugadores_partida.get("X"),
                "O": self.jugadores_partida.get("O"),
            },
            "current_turn": self.turno_actual,
            "status": self.estado_partida,
            "result": self.resultado_final,
            "winner": self.ganador_final,
            "history": [
                {
                    "turn": item["turn"],
                    "symbol": item["symbol"],
                    "position": item["position"],
                    "board_snapshot": item.get("board_snapshot", []).copy()
                    if item.get("board_snapshot") is not None else None,
                }
                for item in self.historial
            ],
        }

    def obtener_estado_web_publico(self):
        """Devuelve el estado que debe mostrar la web."""
        estado_actual = self.obtener_estado_web()

        hay_partida_activa = (
                estado_actual["players"]["X"] is not None
                or estado_actual["players"]["O"] is not None
                or len(estado_actual["history"]) > 0
        )

        if hay_partida_activa:
            return estado_actual

        if self.ultimo_estado_final_web is not None:
            return self.ultimo_estado_final_web

        return estado_actual

    def registrar_jugador(self, jid: str) -> str:
        """Gestiona la entrada de jugadores y devuelve el símbolo asignado o 'full'."""
        if self.jugadores_partida["X"] is None:
            self.jugadores_partida["X"] = jid
            return "X"
        elif self.jugadores_partida["O"] is None:
            self.jugadores_partida["O"] = jid
            return "O"
        return "full"

    def es_movimiento_valido(self, posicion: int) -> bool:
        """Verifica si una posición está dentro de rango y libre."""
        if not (0 <= posicion <= 8):
            return False
        return self.tablero[posicion] == ""

    def hay_empate(self) -> bool:
        """Comprueba si el tablero está lleno."""
        return "" not in self.tablero