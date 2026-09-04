"""Pruebas del protocolo de INFORME de las partidas.

Cuando una partida termina, el supervisor del profesor pide al
tablero el informe del resultado. Estas pruebas verifican ese
protocolo con la técnica de **caja negra**: montan el agente
tablero real del alumno, lo hacen jugar una partida con jugadores
simulados y, después, un supervisor simulado le solicita el
informe.

Mensajes verificados:

* ``game-report`` — REQUEST Supervisor → Tablero (solicitud).
* ``game-report`` — INFORM  Tablero → Supervisor (informe completo).
* ``game-report`` — REFUSE  Tablero → Supervisor (partida en curso).
"""
import pytest

from agentes.agente_tablero import AgenteTablero
from ontologia.ontologia import PERFORMATIVA_INFORM, PERFORMATIVA_REFUSE
from tests.simuladores import (
    SALA_DE_PRUEBA,
    JugadorSimulado,
    SalaSimulada,
    SupervisorSimulado,
    acelerar_tiempos,
    detener_tareas,
    ejecutar_escenario,
    montar_agente,
    perfil_xmpp_de_prueba,
)


@pytest.fixture(autouse=True)
def _acelerar(monkeypatch):
    """Acorta los plazos de espera de los agentes en cada prueba."""
    acelerar_tiempos(monkeypatch)


async def _montar_tablero(
    sala: SalaSimulada, nick: str = "tablero_sim",
) -> object:
    """Monta un agente tablero del alumno sobre la sala simulada.

    El ``nick`` por defecto sigue el estilo de la factoría
    (``construir_nick_tablero`` exige el prefijo ``tablero_``); los
    jugadores filtran los participantes de la sala por ese
    prefijo en :mod:`agentes.utilidades.descubrimiento`, así que
    cualquier otra forma haría que los jugadores no descubrieran
    el Tablero y la partida no llegase a arrancar.
    """
    return await montar_agente(
        AgenteTablero, "tablero_demo_01",
        perfil_xmpp_de_prueba(), {"nick_muc": nick}, sala,
    )


async def _jugar_partida(
    sala: SalaSimulada, tablero: object, modo_segundo: str = "normal",
) -> list:
    """Disputa una partida completa y deja activo el informe.

    Arranca el comportamiento cíclico de informe del tablero, juega
    una partida con dos jugadores simulados y devuelve las tareas
    cíclicas para que la prueba las detenga al terminar.

    Los nicks de los jugadores simulados llevan el prefijo
    ``jugador_`` de la factoría y los plazos de inscripción se
    espacian (``0.0`` y ``0.3``) para evitar que las dos
    solicitudes caigan en la misma ventana del gestor de equidad
    (sección 4.6 del documento de diseño de la Fase 1).

    Args:
        sala: Sala MUC simulada.
        tablero: Tablero del alumno ya montado.
        modo_segundo: Modo del segundo jugador simulado; con
            ``"jugada_invalida"`` la partida acaba abortada.

    Returns:
        Las tareas cíclicas en segundo plano del tablero.
    """
    tareas = tablero.iniciar_ciclicos()
    jugador_x = JugadorSimulado(
        sala, "jugador_x_sim", retardo_inicial=0.0,
    )
    jugador_o = JugadorSimulado(
        sala, "jugador_o_sim", modo=modo_segundo, retardo_inicial=0.3,
    )
    await ejecutar_escenario(
        tablero.correr_unica(),
        jugador_x.ejecutar(), jugador_o.ejecutar(),
    )
    return tareas


class TestInformeTablero:
    """Verifica el agente TABLERO del alumno en el protocolo de informe."""

    @pytest.mark.asyncio
    async def test_tablero_responde_con_inform_tras_la_partida(self):
        """Terminada la partida, el tablero entrega el informe.

        La respuesta al ``game-report`` del supervisor debe ser un
        INFORM con un cuerpo conforme a la ontología.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        tareas = await _jugar_partida(sala, tablero)

        supervisor = SupervisorSimulado(sala, "supervisor_sim")
        respuesta = await supervisor.solicitar_informe(tablero.nick)
        await detener_tareas(tareas)

        assert respuesta is not None
        assert respuesta.get_metadata("performative") == PERFORMATIVA_INFORM
        informes = sala.buscar(accion="game-report", emisor=tablero.nick)
        assert len(informes) == 1
        assert informes[0].performativa == PERFORMATIVA_INFORM
        assert informes[0].valido, informes[0].errores

    @pytest.mark.asyncio
    async def test_informe_es_conforme_a_la_ontologia(self):
        """El informe tiene la estructura de un resultado válido.

        La prueba comprueba la **conformidad estructural** del cuerpo
        del informe con la ontología (``MensajeGameReport``): el
        ``result`` pertenece al vocabulario, el ``winner`` es
        coherente con él, ``turns`` es un entero dentro de rango y el
        ``board`` y los ``players`` tienen la forma esperada. No se
        compara el contenido con la partida concreta arbitrada, solo
        que el informe está bien formado y es autoconsistente.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        tareas = await _jugar_partida(sala, tablero)

        supervisor = SupervisorSimulado(sala, "supervisor_sim")
        await supervisor.solicitar_informe(tablero.nick)
        await detener_tareas(tareas)

        informe = sala.buscar(
            accion="game-report", emisor=tablero.nick,
        )[0]
        # El informe se valida contra el contrato observable de la
        # ontología (cuerpo conforme a ``MensajeGameReport``), sin
        # leer ningún atributo interno del agente del alumno: el
        # protocolo de informe queda cerrado por el ``INFORM
        # game-report`` que circula por la sala, único punto que el
        # supervisor del profesor consulta en producción.
        assert informe.cuerpo["result"] in ("win", "draw", "aborted")
        if informe.cuerpo["result"] == "win":
            assert informe.cuerpo["winner"] in ("X", "O")
        else:
            assert informe.cuerpo["winner"] is None
        assert isinstance(informe.cuerpo["turns"], int)
        assert 0 <= informe.cuerpo["turns"] <= 9
        assert isinstance(informe.cuerpo["board"], list)
        assert len(informe.cuerpo["board"]) == 9
        assert set(informe.cuerpo["players"].keys()) == {"X", "O"}

    @pytest.mark.asyncio
    async def test_tablero_rechaza_el_informe_si_la_partida_sigue(self):
        """Con la partida en curso, el tablero rechaza la solicitud.

        Si el supervisor pide el informe antes de que la partida
        termine, el tablero responde con un REFUSE y la razón
        ``not-finished``.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        # No se juega la partida: el comportamiento de informe es lo
        # único que se arranca, así que 'informe_final' sigue vacío.
        tareas = tablero.iniciar_ciclicos()

        supervisor = SupervisorSimulado(sala, "supervisor_sim")
        respuesta = await supervisor.solicitar_informe(tablero.nick)
        await detener_tareas(tareas)

        assert respuesta is not None
        informe = sala.buscar(
            accion="game-report", emisor=tablero.nick,
        )[0]
        assert informe.performativa == PERFORMATIVA_REFUSE
        assert informe.cuerpo.get("reason") == "not-finished"
        assert informe.valido, informe.errores

    @pytest.mark.asyncio
    async def test_informe_de_una_partida_abortada(self):
        """El informe de una partida abortada indica la causa.

        Cuando la partida acaba por una jugada inválida, el informe
        es un INFORM con ``result`` ``aborted`` y una ``reason``.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        tareas = await _jugar_partida(
            sala, tablero, modo_segundo="jugada_invalida",
        )

        supervisor = SupervisorSimulado(sala, "supervisor_sim")
        await supervisor.solicitar_informe(tablero.nick)
        await detener_tareas(tareas)

        informe = sala.buscar(
            accion="game-report", emisor=tablero.nick,
        )[0]
        assert informe.performativa == PERFORMATIVA_INFORM
        assert informe.cuerpo["result"] == "aborted"
        assert informe.cuerpo.get("reason") in (
            "invalid", "timeout", "both-timeout",
        )
        assert informe.valido, informe.errores

    @pytest.mark.asyncio
    async def test_informe_conserva_el_hilo_de_la_solicitud(self):
        """El informe se correlaciona con la solicitud por el hilo.

        El tablero debe responder con el mismo ``thread`` que traía
        la solicitud del supervisor, para que este empareje la
        respuesta con su petición.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        tareas = await _jugar_partida(sala, tablero)

        supervisor = SupervisorSimulado(sala, "supervisor_sim")
        await supervisor.solicitar_informe(tablero.nick)
        await detener_tareas(tareas)

        solicitud = sala.buscar(
            accion="game-report", emisor="supervisor_sim",
        )[0]
        respuesta = sala.buscar(
            accion="game-report", emisor=tablero.nick,
        )[0]
        assert respuesta.thread == solicitud.thread
        assert respuesta.thread

    @pytest.mark.asyncio
    async def test_supervisor_aplica_cortesia_de_reintento(self):
        """El supervisor reenvía el ``REQUEST`` si el primero no obtiene respuesta.

        Verifica la cortesía §5.4 de
        ``doc/GUIA_THREAD_Y_GAME_START.md`` desde el lado del
        **iniciador**: si la primera solicitud agota su plazo —porque
        el Tablero no está escuchando (aquí no se monta ningún
        ComportamientoInformeTablero)—, el supervisor debe reenviar
        exactamente el mismo mensaje una segunda vez antes de dar
        el informe por no entregado. La sala debe acabar con dos
        ``REQUEST game-report`` del supervisor con idéntico
        ``thread``.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        supervisor = SupervisorSimulado(sala, "supervisor_sim")

        # Sin tablero montado: nadie atiende el REQUEST. El
        # simulador agota su plazo dos veces y devuelve None tras
        # consumir la cortesía.
        respuesta = await supervisor.solicitar_informe(
            "tablero_inexistente",
        )

        assert respuesta is None
        assert supervisor.reintentos_realizados == 1

        solicitudes = sala.buscar(
            accion="game-report", emisor=supervisor.nick,
        )
        # Dos REQUEST: envío inicial + reintento de cortesía.
        assert len(solicitudes) == 2
        # Las dos solicitudes comparten thread y cuerpo (la cortesía
        # reenvía exactamente el mismo mensaje, no uno nuevo).
        assert solicitudes[0].thread == solicitudes[1].thread
        assert solicitudes[0].cuerpo == solicitudes[1].cuerpo
        assert solicitudes[0].thread.startswith("report-")
