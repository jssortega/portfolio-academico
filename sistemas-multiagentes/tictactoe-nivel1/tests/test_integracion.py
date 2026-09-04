import pytest
import asyncio
import json

from spade.agent import Agent
from spade.message import Message
from spade.behaviour import CyclicBehaviour

# Ajusta las importaciones a la estructura de tu proyecto si es necesario
from agentes.agente_tablero import AgenteTablero
from agentes.agente_jugador import AgenteJugador
from ontologia.ontologia import ONTOLOGIA, PERFORMATIVA_REQUEST, obtener_conversation_id

# =====================================================================
# CONSTANTES DE RED
# =====================================================================
XMPP_HOST = "localhost"
PASS = "secret"


def preparar_agente_para_test(agente, id_tablero="test"):
    """Inyecta las variables de entorno necesarias"""

    # Inyectamos diccionarios vacíos o con valores por defecto para evitar AttributeErrors
    agente.config_parametros = {"id_tablero": id_tablero, "puerto_web": 10000}
    agente.config_xmpp = {
        "servicio_muc": "conference.localhost",
        "sala_muc_completa": "tictactoe@conference.localhost"
    }


# =====================================================================
# AGENTE DUMMY PARA TESTEAR EL SUPERVISOR
# =====================================================================
class SupervisorDummy(Agent):
    """Agente espía que simula ser el supervisor para pedir el game-report."""

    async def setup(self):
        self.respuesta_recibida = None

        class EnviarYRecibir(CyclicBehaviour):
            async def on_start(self):
                msg = Message(to=f"tablero_test3@{XMPP_HOST}")
                msg.set_metadata("performative", PERFORMATIVA_REQUEST)
                msg.set_metadata("ontology", ONTOLOGIA)
                msg.set_metadata("conversation-id", obtener_conversation_id("game-report"))
                msg.body = json.dumps({"action": "game-report"})
                await self.send(msg)

            async def run(self):
                msg = await self.receive(timeout=2)
                if msg:
                    self.agent.respuesta_recibida = msg
                    self.kill()

        self.add_behaviour(EnviarYRecibir())


# =====================================================================
# TESTS DE INTEGRACIÓN
# =====================================================================

@pytest.mark.asyncio
async def test_descubrimiento_muc() -> None:
    """Test 1 y 2: Un Agente Tablero arranca y se une a la sala MUC. Un Agente Jugador lo descubre."""
    tablero = AgenteTablero(f"tablero_test1@{XMPP_HOST}", PASS, verify_security=False)
    jugador = AgenteJugador(f"jugador_test1@{XMPP_HOST}", PASS, verify_security=False)

    preparar_agente_para_test(tablero, "test1")
    preparar_agente_para_test(jugador, "test1")

    await tablero.start(auto_register=True)
    await asyncio.sleep(3)

    await jugador.start(auto_register=True)
    await asyncio.sleep(4)

    try:
        assert hasattr(jugador, "tableros_descubiertos")
        encontrado = any("tablero_test1" in jid for jid in jugador.tableros_descubiertos.keys())
        assert encontrado is True, "El jugador no descubrió al tablero en la sala MUC."
    finally:
        await jugador.stop()
        await tablero.stop()


@pytest.mark.asyncio
async def test_protocolo_inscripcion_y_turno() -> None:
    """Test 3 y 4: Protocolo de inscripción y ejecución de al menos un turno completo."""
    tablero = AgenteTablero(f"tablero_test2@{XMPP_HOST}", PASS, verify_security=False)
    preparar_agente_para_test(tablero, "test2")
    await tablero.start(auto_register=True)

    j1 = AgenteJugador(f"jugador_test2_a@{XMPP_HOST}", PASS, verify_security=False)
    j2 = AgenteJugador(f"jugador_test2_b@{XMPP_HOST}", PASS, verify_security=False)

    for j in [j1, j2]:
        j.nivel = 1
        j.limite_partidas_simultaneas = 1
        preparar_agente_para_test(j, "test2")

    await j1.start(auto_register=True)
    await j2.start(auto_register=True)

    try:
        await asyncio.sleep(7)

        partida_j1 = (
            len(j1.partidas_activas) > 0
            or len(j1.partidas_pendientes) > 0
        )
        partida_j2 = (
            len(j2.partidas_activas) > 0
            or len(j2.partidas_pendientes) > 0
        )

        # Si la partida ya terminó muy rápido, los jugadores limpian
        # partidas_activas, así que comprobamos también el informe final.
        partida_finalizada = tablero.ultimo_informe_partida is not None

        assert partida_j1 or partida_finalizada, ("El jugador 1 no tiene la partida activa ni existe informe final.")
        assert partida_j2 or partida_finalizada, ("El jugador 2 no tiene la partida activa ni existe informe final.")

        await asyncio.sleep(7)

        movimientos_registrados = len(tablero.historial)

        if movimientos_registrados == 0 and tablero.ultimo_informe_partida is not None:
            movimientos_registrados = len(tablero.ultimo_informe_partida.get("history", []))

        assert movimientos_registrados > 0, ("No se ha registrado ningún movimiento en el historial.")

    finally:
        await j1.stop()
        await j2.stop()
        await tablero.stop()


@pytest.mark.asyncio
async def test_respuesta_game_report() -> None:
    """Test 5: El Tablero responde a solicitudes game-report del agente observador."""
    tablero = AgenteTablero(f"tablero_test3@{XMPP_HOST}", PASS, verify_security=False)
    preparar_agente_para_test(tablero, "test3")
    await tablero.start(auto_register=True)
    await asyncio.sleep(2)

    supervisor = SupervisorDummy(f"supervisor_test@{XMPP_HOST}", PASS, verify_security=False)
    preparar_agente_para_test(supervisor, "test3")
    await supervisor.start(auto_register=True)

    try:
        await asyncio.sleep(4)
        respuesta = supervisor.respuesta_recibida
        assert respuesta is not None, "El tablero no envió ninguna respuesta al supervisor."
        assert respuesta.metadata.get("ontology") == ONTOLOGIA

        performativa = respuesta.metadata.get("performative")
        assert performativa in ["refuse", "inform"], f"Performativa inesperada: {performativa}"

    finally:
        await supervisor.stop()
        await tablero.stop()