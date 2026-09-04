"""
Agente Jugador del sistema Tic-Tac-Toe Multiagente.

Se una a la sala MUC en busca de tableros disponibles,
solicita unirse a las partidas, una vez se una envía movimientos
válidos según su nivel de estrategia para ganar la partida.
"""

from spade.agent import Agent
from spade.template import Template

from agentes.muc_utils import setup_muc, obtener_sala_muc

from ontologia import (
    ONTOLOGIA, PERFORMATIVA_AGREE,
    PERFORMATIVA_REFUSE, PERFORMATIVA_FAILURE,
    PERFORMATIVA_INFORM
)

from behaviours.busqueda_tablero import BuscarPartida, RecibirRespuesta

from estrategia.estrategia_nivel1 import elegir_movimiento as elegir_movimiento_nivel1
from estrategia.estrategia_nivel3 import elegir_movimiento as elegir_movimiento_nivel3

class AgenteJugador(Agent):
    """Agente que se une a tableros disponibles que encuentra en la sala MUC y juega las partidas"""

    async def setup(self):
        """Inicializa el jugador: estado interno, salas MUC y behaviours.

            Inicializa las variables del agente, se une a la sala
            MUC, y comienza el proceso de inscripción a los tableros disponibles.
        """

        nombre_agente = str(self.jid).split("@")[0]
        self.player_name = nombre_agente.removeprefix("jugador_")
        parametros = getattr(self, "config_parametros", {}) or {}
        nick_base = str(parametros.get("nick_muc", self.player_name))

        if nick_base.startswith("jugador_"):
            self.muc_nick = nick_base
        else:
            self.muc_nick = f"jugador_{nick_base}"

        #Variables del agente que gestiona los tableros que descubre y los que se conecta
        self.tableros_descubiertos = {}
        self.tableros_contactados = set()
        self.partidas_pendientes = {}
        self.partidas_activas = {}
        self.indice_busqueda_tablero = sum(ord(c) for c in self.muc_nick)
        self.max_partidas = self.config_parametros.get("max_partidas", 3)

        #Lee el nivel de estrategia desde la configuración del agente
        self.nivel_estrategia = self.config_parametros.get("nivel_estrategia", 1)

        # Elige un nivel de estrategia según el valor de la configuracion
        if self.nivel_estrategia == 3:
            self.elegir_movimiento = elegir_movimiento_nivel3
        else:
            self.elegir_movimiento = elegir_movimiento_nivel1

        #Se une a la sala MUC
        self.muc_room = obtener_sala_muc(self)

        self.client.add_event_handler(
            f"muc::{self.muc_room}::got_online",
            self.on_presencia_muc
        )

        self.client.add_event_handler(
            f"muc::{self.muc_room}::got_offline",
            self.on_presencia_muc
        )

        setup_muc(self, apodo=self.muc_nick)

        template_agree = Template()
        template_agree.set_metadata("ontology", ONTOLOGIA)
        template_agree.set_metadata("performative", PERFORMATIVA_AGREE)

        template_refuse = Template()
        template_refuse.set_metadata("ontology", ONTOLOGIA)
        template_refuse.set_metadata("performative", PERFORMATIVA_REFUSE)

        template_failure = Template()
        template_failure.set_metadata("ontology", ONTOLOGIA)
        template_failure.set_metadata("performative", PERFORMATIVA_FAILURE)

        template_inform = Template()
        template_inform.set_metadata("ontology", ONTOLOGIA)
        template_inform.set_metadata("performative", PERFORMATIVA_INFORM)

        template_respuesta_tablero = (template_agree | template_refuse | template_failure | template_inform)

        #Comportamientos para buscar partida y recibir las respuestas del agente con
        #sus correspondientes performativas
        self.add_behaviour(BuscarPartida(period=5))
        self.add_behaviour(RecibirRespuesta(), template_respuesta_tablero)

    def on_presencia_muc(self, presencia):
        """Metodo auxiliar que hace la busqueda de talberos en la sala MUC"""

        jid_from = presencia["from"]

        if hasattr(jid_from, "bare"):
            sala_jid = str(jid_from.bare)
            nick = str(jid_from.resource) if jid_from.resource else ""
        else:
            jid_str = str(jid_from)
            if "/" in jid_str:
                sala_jid, nick = jid_str.split("/", 1)
            else:
                sala_jid = jid_str
                nick = ""

        tipo = presencia["type"]

        if sala_jid.lower() != str(self.muc_room).lower():
            return

        #Filtra solo nicknames que empiecen por tablero_
        if not nick.startswith("tablero_"):
            return

        tablero_jid = nick

        if tipo == "unavailable":
            self.tableros_descubiertos.pop(tablero_jid, None)
            return

        status = str(presencia["status"] or "").strip().lower()

        if not status:
            status = "waiting"

        #Añade el tablero descubierto al map
        self.tableros_descubiertos[tablero_jid] = {
            "nick": nick,
            "status": status,
        }

        print(f"[JUGADOR {self.player_name}] Tablero detectado: {nick} -> {tablero_jid} [{status}]")

    def es_tablero_valido(self, nick: str) -> bool:
        """
        Comprueba si el nick extraído de la sala MUC pertenece a un tablero.
        """
        return nick.startswith("tablero_")

    def puede_jugar_nueva_partida(self) -> bool:
        """
        Comprueba si la suma de partidas activas y pendientes es menor que el límite.
        """
        total_partidas = len(self.partidas_activas) + len(self.partidas_pendientes)
        return total_partidas < self.limite_partidas_simultaneas
