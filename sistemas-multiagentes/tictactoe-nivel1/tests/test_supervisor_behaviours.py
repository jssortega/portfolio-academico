"""
Tests unitarios de las funciones auxiliares y los estados del FSM
del Agente Supervisor.

Se prueban de forma aislada, sin necesidad de SPADE ni servidor XMPP:
- Funciones puras: ``_determinar_rol``, ``_construir_detalle_informe``.
- Estados del FSM: cada estado se prueba con un agente simulado
  que expone los mismos atributos que ``AgenteSupervisor``.
"""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from behaviours.supervisor_behaviours import (
    TIMEOUT_RESPUESTA,
    ST_ENVIAR_REQUEST,
    ST_ESPERAR_RESPUESTA,
    ST_ESPERAR_INFORME,
    ST_PROCESAR_INFORME,
    ST_PROCESAR_RECHAZO,
    ST_REGISTRAR_TIMEOUT,
    EstadoEnviarRequest,
    EstadoEsperarRespuesta,
    EstadoEsperarInforme,
    EstadoProcesarInforme,
    EstadoProcesarRechazo,
    EstadoRegistrarTimeout,
    _construir_detalle_informe,
    _determinar_rol,
)


# ═══════════════════════════════════════════════════════════════════════════
#  Datos de prueba
# ═══════════════════════════════════════════════════════════════════════════

# Los informes de prueba deben cumplir el esquema de la ontología
# (additionalProperties: false), por lo que solo incluyen los campos
# definidos en MensajeGameReport del esquema JSON.

INFORME_VICTORIA = {
    "action": "game-report",
    "result": "win",
    "winner": "X",
    "players": {
        "X": "jugador_ana@localhost",
        "O": "jugador_luis@localhost",
    },
    "turns": 7,
    "board": ["X", "O", "X", "O", "X", "O", "", "", "X"],
}

INFORME_EMPATE = {
    "action": "game-report",
    "result": "draw",
    "winner": None,
    "players": {
        "X": "jugador_ana@localhost",
        "O": "jugador_luis@localhost",
    },
    "turns": 9,
    "board": ["X", "O", "X", "X", "O", "O", "O", "X", "X"],
}

INFORME_ABORTADA = {
    "action": "game-report",
    "result": "aborted",
    "winner": None,
    "reason": "both-timeout",
    "players": {
        "X": "jugador_ana@localhost",
        "O": "jugador_luis@localhost",
    },
    "turns": 2,
    "board": ["X", "", "", "", "O", "", "", "", ""],
}


# ═══════════════════════════════════════════════════════════════════════════
#  Utilidades para simular el agente y los mensajes
# ═══════════════════════════════════════════════════════════════════════════

def crear_agente_simulado():
    """Crea un objeto que imita los atributos de AgenteSupervisor
    necesarios para los tests de los estados del FSM."""
    agente = SimpleNamespace(
        informes_por_sala={"tictactoe": {}},
        tableros_consultados=set(),
        log_por_sala={"tictactoe": []},
        almacen=None,
        registrar_evento_log=MagicMock(),
    )
    return agente


def crear_mensaje_simulado(performativa, cuerpo_dict=None):
    """Crea un mensaje con los métodos mínimos que usan los estados."""
    msg = MagicMock()
    msg.get_metadata.return_value = performativa
    msg.sender = "tablero_mesa1@conference.localhost"
    msg.body = json.dumps(cuerpo_dict) if cuerpo_dict else "{}"
    return msg


def crear_estado_con_contexto(clase_estado, jid="tablero_mesa1@conference.localhost"):
    """Instancia un estado del FSM, le inyecta el contexto compartido
    y un agente simulado, y le asigna métodos send y receive simulados."""
    estado = clase_estado()
    estado.ctx = {
        "jid_tablero": jid,
        "sala_id": "tictactoe",
        "hilo": "report-test-12345",
        "mensaje": None,
    }
    estado.agent = crear_agente_simulado()
    estado.send = AsyncMock()
    estado.receive = AsyncMock(return_value=None)
    return estado


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de _determinar_rol
# ═══════════════════════════════════════════════════════════════════════════

class TestDeterminarRol:
    """Verifica que se clasifica correctamente el rol de un ocupante
    MUC a partir de su apodo."""

    def test_apodo_con_prefijo_tablero(self):
        """Un apodo que empiece por 'tablero_' debe clasificarse como
        tablero."""
        assert _determinar_rol("tablero_mesa1") == "tablero"

    def test_apodo_supervisor(self):
        """El apodo 'supervisor' debe clasificarse como supervisor."""
        assert _determinar_rol("supervisor") == "supervisor"

    def test_apodo_jugador(self):
        """Cualquier otro apodo debe clasificarse como jugador."""
        assert _determinar_rol("jugador_ana") == "jugador"

    def test_apodo_desconocido_es_jugador(self):
        """Un apodo que no empiece por 'tablero_' ni sea 'supervisor'
        se considera jugador por defecto."""
        assert _determinar_rol("observador_externo") == "jugador"


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de _construir_detalle_informe
# ═══════════════════════════════════════════════════════════════════════════

class TestConstruirDetalleInforme:
    """Verifica que se genera un texto descriptivo correcto para cada
    tipo de resultado de partida."""

    def test_detalle_victoria(self):
        """Una victoria debe indicar la ficha ganadora y los nombres
        de los jugadores."""
        detalle = _construir_detalle_informe(INFORME_VICTORIA)
        assert "Victoria" in detalle
        assert "ana" in detalle
        assert "luis" in detalle
        assert "7 turnos" in detalle

    def test_detalle_empate(self):
        """Un empate debe incluir la palabra 'Empate' y los nombres."""
        detalle = _construir_detalle_informe(INFORME_EMPATE)
        assert "Empate" in detalle
        assert "ana" in detalle
        assert "9 turnos" in detalle

    def test_detalle_abortada(self):
        """Una partida abortada debe incluir 'Abortada' y el motivo."""
        detalle = _construir_detalle_informe(INFORME_ABORTADA)
        assert "Abortada" in detalle
        assert "both-timeout" in detalle
        assert "2 turnos" in detalle

    def test_detalle_con_campos_vacios(self):
        """Con un diccionario mínimo no debe lanzar excepciones."""
        cuerpo_minimo = {"result": "?", "players": {}, "turns": 0}
        detalle = _construir_detalle_informe(cuerpo_minimo)
        assert isinstance(detalle, str)


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de EstadoEnviarRequest
# ═══════════════════════════════════════════════════════════════════════════

class TestEstadoEnviarRequest:
    """Verifica que el estado inicial envía el mensaje REQUEST,
    registra la solicitud en el log y transiciona correctamente."""

    @pytest.mark.asyncio
    async def test_envia_mensaje_al_tablero(self):
        """Debe llamar a send() con un mensaje dirigido al tablero."""
        estado = crear_estado_con_contexto(EstadoEnviarRequest)
        await estado.run()
        estado.send.assert_called_once()
        mensaje_enviado = estado.send.call_args[0][0]
        assert str(mensaje_enviado.to) == "tablero_mesa1@conference.localhost"

    @pytest.mark.asyncio
    async def test_transiciona_a_esperar_respuesta(self):
        """Tras enviar, debe establecer ESPERAR_RESPUESTA como
        siguiente estado."""
        estado = crear_estado_con_contexto(EstadoEnviarRequest)
        await estado.run()
        assert estado.next_state == ST_ESPERAR_RESPUESTA

    @pytest.mark.asyncio
    async def test_registra_solicitud_en_log(self):
        """Debe registrar un evento de tipo 'solicitud' en el log
        del dashboard al enviar el REQUEST."""
        estado = crear_estado_con_contexto(EstadoEnviarRequest)
        await estado.run()
        estado.agent.registrar_evento_log.assert_called_once()
        args = estado.agent.registrar_evento_log.call_args[0]
        assert args[0] == "solicitud"
        assert "game-report" in args[2]


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de EstadoEsperarRespuesta
# ═══════════════════════════════════════════════════════════════════════════

class TestEstadoEsperarRespuesta:
    """Verifica las transiciones del estado que espera la primera
    respuesta del tablero."""

    @pytest.mark.asyncio
    async def test_agree_transiciona_a_esperar_informe(self):
        """Si recibe AGREE, debe transicionar a ESPERAR_INFORME."""
        estado = crear_estado_con_contexto(EstadoEsperarRespuesta)
        estado.receive = AsyncMock(
            return_value=crear_mensaje_simulado("agree"),
        )
        await estado.run()
        assert estado.next_state == ST_ESPERAR_INFORME

    @pytest.mark.asyncio
    async def test_inform_transiciona_a_procesar_informe(self):
        """Si recibe INFORM directamente, debe transicionar a
        PROCESAR_INFORME y almacenar el mensaje en el contexto."""
        msg = crear_mensaje_simulado("inform", INFORME_VICTORIA)
        estado = crear_estado_con_contexto(EstadoEsperarRespuesta)
        estado.receive = AsyncMock(return_value=msg)
        await estado.run()
        assert estado.next_state == ST_PROCESAR_INFORME
        assert estado.ctx["mensaje"] is msg

    @pytest.mark.asyncio
    async def test_refuse_transiciona_a_procesar_rechazo(self):
        """Si recibe REFUSE, debe transicionar a PROCESAR_RECHAZO."""
        msg = crear_mensaje_simulado(
            "refuse", {"reason": "not-finished"},
        )
        estado = crear_estado_con_contexto(EstadoEsperarRespuesta)
        estado.receive = AsyncMock(return_value=msg)
        await estado.run()
        assert estado.next_state == ST_PROCESAR_RECHAZO
        assert estado.ctx["mensaje"] is msg

    @pytest.mark.asyncio
    async def test_timeout_transiciona_a_registrar_timeout(self):
        """Si no llega respuesta (None), debe transicionar a
        REGISTRAR_TIMEOUT."""
        estado = crear_estado_con_contexto(EstadoEsperarRespuesta)
        estado.receive = AsyncMock(return_value=None)
        await estado.run()
        assert estado.next_state == ST_REGISTRAR_TIMEOUT

    @pytest.mark.asyncio
    async def test_performativa_inesperada_transiciona_a_timeout(self):
        """Una performativa no reconocida debe transicionar a
        REGISTRAR_TIMEOUT como respuesta segura."""
        msg = crear_mensaje_simulado("propose")
        estado = crear_estado_con_contexto(EstadoEsperarRespuesta)
        estado.receive = AsyncMock(return_value=msg)
        await estado.run()
        assert estado.next_state == ST_REGISTRAR_TIMEOUT


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de EstadoEsperarInforme
# ═══════════════════════════════════════════════════════════════════════════

class TestEstadoEsperarInforme:
    """Verifica las transiciones del estado que espera el informe tras
    un AGREE. En este estado REFUSE no es una transición válida."""

    @pytest.mark.asyncio
    async def test_inform_transiciona_a_procesar_informe(self):
        """Si recibe INFORM, debe transicionar a PROCESAR_INFORME."""
        msg = crear_mensaje_simulado("inform", INFORME_VICTORIA)
        estado = crear_estado_con_contexto(EstadoEsperarInforme)
        estado.receive = AsyncMock(return_value=msg)
        await estado.run()
        assert estado.next_state == ST_PROCESAR_INFORME
        assert estado.ctx["mensaje"] is msg

    @pytest.mark.asyncio
    async def test_timeout_transiciona_a_registrar_timeout(self):
        """Si no llega respuesta, debe transicionar a
        REGISTRAR_TIMEOUT."""
        estado = crear_estado_con_contexto(EstadoEsperarInforme)
        estado.receive = AsyncMock(return_value=None)
        await estado.run()
        assert estado.next_state == ST_REGISTRAR_TIMEOUT

    @pytest.mark.asyncio
    async def test_refuse_no_transiciona_a_procesar_rechazo(self):
        """Tras AGREE, un REFUSE no debe transicionar a
        PROCESAR_RECHAZO (no es válido en este punto del protocolo).
        Se trata como performativa inesperada → REGISTRAR_TIMEOUT."""
        msg = crear_mensaje_simulado("refuse", {"reason": "not-finished"})
        estado = crear_estado_con_contexto(EstadoEsperarInforme)
        estado.receive = AsyncMock(return_value=msg)
        await estado.run()
        assert estado.next_state != ST_PROCESAR_RECHAZO
        assert estado.next_state == ST_REGISTRAR_TIMEOUT


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de EstadoProcesarInforme
# ═══════════════════════════════════════════════════════════════════════════

class TestEstadoProcesarInforme:
    """Verifica que el estado final procesa y almacena correctamente
    los informes recibidos."""

    @pytest.mark.asyncio
    async def test_almacena_informe_con_jid_tablero_del_contexto(self):
        """El informe debe almacenarse usando el jid_tablero del
        contexto del FSM (no el sender del mensaje), para que el
        nick del tablero sea legible en el dashboard."""
        msg = crear_mensaje_simulado("inform", INFORME_VICTORIA)
        # El sender es el JID real (con recurso aleatorio)
        msg.sender = "tablero_mesa1@localhost/recursoABC"
        estado = crear_estado_con_contexto(EstadoProcesarInforme)
        estado.ctx["mensaje"] = msg
        await estado.run()

        informes = estado.agent.informes_por_sala["tictactoe"]
        # La clave debe ser el jid_tablero del contexto, NO el sender
        jid_ctx = estado.ctx["jid_tablero"]
        assert jid_ctx in informes
        assert "tablero_mesa1@localhost/recursoABC" not in informes

    @pytest.mark.asyncio
    async def test_registra_evento_en_log(self):
        """Debe llamar a registrar_evento_log del agente."""
        msg = crear_mensaje_simulado("inform", INFORME_VICTORIA)
        estado = crear_estado_con_contexto(EstadoProcesarInforme)
        estado.ctx["mensaje"] = msg
        await estado.run()

        estado.agent.registrar_evento_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_persiste_en_almacen_con_jid_tablero(self):
        """Si el agente tiene almacén, debe llamar a guardar_informe
        con el jid_tablero del contexto del FSM."""
        msg = crear_mensaje_simulado("inform", INFORME_VICTORIA)
        estado = crear_estado_con_contexto(EstadoProcesarInforme)
        estado.ctx["mensaje"] = msg
        estado.agent.almacen = MagicMock()
        await estado.run()

        estado.agent.almacen.guardar_informe.assert_called_once()
        args = estado.agent.almacen.guardar_informe.call_args[0]
        # El segundo argumento debe ser el jid_tablero del contexto
        assert args[1] == estado.ctx["jid_tablero"]

    @pytest.mark.asyncio
    async def test_es_estado_final(self):
        """No debe establecer siguiente estado (el FSM termina)."""
        msg = crear_mensaje_simulado("inform", INFORME_VICTORIA)
        estado = crear_estado_con_contexto(EstadoProcesarInforme)
        estado.ctx["mensaje"] = msg
        await estado.run()
        assert estado.next_state is None

    @pytest.mark.asyncio
    async def test_json_invalido_no_lanza_excepcion(self):
        """Si el cuerpo del mensaje no es JSON válido, no debe lanzar
        excepciones (tablero que no usa la ontología correctamente)."""
        msg = MagicMock()
        msg.get_metadata.return_value = "inform"
        msg.sender = "tablero@localhost"
        msg.body = "esto no es json"
        estado = crear_estado_con_contexto(EstadoProcesarInforme)
        estado.ctx["mensaje"] = msg
        await estado.run()
        # No debe haber almacenado nada
        assert len(estado.agent.informes_por_sala["tictactoe"]) == 0

    @pytest.mark.asyncio
    async def test_informe_con_esquema_invalido_no_se_almacena(self):
        """Si el tablero envía un JSON válido pero que no cumple el
        esquema de la ontología (campos obligatorios ausentes), el
        informe no debe almacenarse."""
        # Falta 'players', 'turns' y 'board' que son obligatorios
        cuerpo_incompleto = {"action": "game-report", "result": "win"}
        msg = crear_mensaje_simulado("inform", cuerpo_incompleto)
        estado = crear_estado_con_contexto(EstadoProcesarInforme)
        estado.ctx["mensaje"] = msg
        await estado.run()
        assert len(estado.agent.informes_por_sala["tictactoe"]) == 0

    @pytest.mark.asyncio
    async def test_informe_victoria_sin_winner_no_se_almacena(self):
        """Si un tablero envía result='win' pero no incluye 'winner',
        la validación de la ontología debe rechazarlo."""
        cuerpo_sin_winner = {
            "action": "game-report",
            "result": "win",
            "players": {"X": "a@l", "O": "b@l"},
            "turns": 5,
            "board": ["X", "O", "X", "O", "X", "", "", "", ""],
        }
        msg = crear_mensaje_simulado("inform", cuerpo_sin_winner)
        estado = crear_estado_con_contexto(EstadoProcesarInforme)
        estado.ctx["mensaje"] = msg
        await estado.run()
        assert len(estado.agent.informes_por_sala["tictactoe"]) == 0


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de EstadoProcesarRechazo
# ═══════════════════════════════════════════════════════════════════════════

class TestEstadoProcesarRechazo:
    """Verifica que el estado final gestiona correctamente los
    rechazos de los tableros.

    El desbloqueo del tablero se realiza en el callback de presencia
    del agente (no en el FSM), por lo que estos tests solo verifican
    que el estado registra la razón y termina correctamente."""

    @pytest.mark.asyncio
    async def test_no_modifica_tableros_consultados(self):
        """El estado no debe tocar tableros_consultados (el
        desbloqueo se gestiona en el callback de presencia)."""
        msg = crear_mensaje_simulado(
            "refuse", {"reason": "not-finished"},
        )
        jid = "tablero_mesa1@conference.localhost"
        estado = crear_estado_con_contexto(EstadoProcesarRechazo, jid)
        estado.ctx["mensaje"] = msg
        estado.agent.tableros_consultados.add(jid)
        await estado.run()

        # El estado no debe haber modificado el conjunto
        assert jid in estado.agent.tableros_consultados

    @pytest.mark.asyncio
    async def test_es_estado_final(self):
        """No debe establecer siguiente estado."""
        msg = crear_mensaje_simulado(
            "refuse", {"reason": "not-finished"},
        )
        estado = crear_estado_con_contexto(EstadoProcesarRechazo)
        estado.ctx["mensaje"] = msg
        await estado.run()
        assert estado.next_state is None


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de EstadoRegistrarTimeout
# ═══════════════════════════════════════════════════════════════════════════

class TestEstadoRegistrarTimeout:
    """Verifica que el estado final registra la incidencia de tiempo
    agotado."""

    @pytest.mark.asyncio
    async def test_registra_evento_timeout(self):
        """Debe llamar a registrar_evento_log con tipo 'timeout'."""
        estado = crear_estado_con_contexto(EstadoRegistrarTimeout)
        await estado.run()

        estado.agent.registrar_evento_log.assert_called_once()
        args = estado.agent.registrar_evento_log.call_args[0]
        assert args[0] == "timeout"

    @pytest.mark.asyncio
    async def test_es_estado_final(self):
        """No debe establecer siguiente estado."""
        estado = crear_estado_con_contexto(EstadoRegistrarTimeout)
        await estado.run()
        assert estado.next_state is None
