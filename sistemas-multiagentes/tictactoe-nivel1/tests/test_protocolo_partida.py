"""Pruebas del protocolo de JUEGO de las partidas.

Una vez completado el registro, el tablero arbitra la partida y
los jugadores proponen sus jugadas. Estas pruebas verifican ese
protocolo con la técnica de **caja negra**: montan el agente real
del alumno sobre la sala MUC simulada, lo enfrentan a simuladores
del agente contrario y comprueban la conformidad de los mensajes.

Mensajes verificados:

* ``game-start`` — INFORM          Tablero → cada jugador.
* ``turn``       — CFP             Tablero → ambos jugadores.
* ``move``       — PROPOSE         Jugador → Tablero (propuesta).
* ``move``       — ACCEPT_PROPOSAL Tablero → sala (confirmación).
* ``turn-result``— INFORM          Jugador → Tablero (acuse).
* ``game-over``  — REJECT_PROPOSAL Tablero → sala (partida abortada).
"""
import pytest

from agentes.agente_jugador import AgenteJugador
from agentes.agente_tablero import AgenteTablero
from ontologia.ontologia import (
    PERFORMATIVA_ACCEPT_PROPOSAL,
    PERFORMATIVA_CFP,
    PERFORMATIVA_INFORM,
    PERFORMATIVA_PROPOSE,
    PERFORMATIVA_REJECT_PROPOSAL,
)
from tests.simuladores import (
    SALA_DE_PRUEBA,
    JugadorSimulado,
    SalaSimulada,
    TableroSimulado,
    acelerar_tiempos,
    anunciar_tablero_descubierto,
    ejecutar_escenario,
    montar_agente,
    perfil_xmpp_de_prueba,
)


@pytest.fixture(autouse=True)
def _acelerar(monkeypatch):
    """Acorta los plazos de espera de los agentes en cada prueba."""
    acelerar_tiempos(monkeypatch)


async def _montar_jugador(
    sala: SalaSimulada, nombre: str, nick: str,
) -> object:
    """Monta un agente jugador del alumno sobre la sala simulada."""
    return await montar_agente(
        AgenteJugador, nombre,
        perfil_xmpp_de_prueba(), {"nick_muc": nick}, sala,
    )


async def _montar_tablero(
    sala: SalaSimulada, nick: str = "tablero_sim",
) -> object:
    """Monta un agente tablero del alumno sobre la sala simulada."""
    return await montar_agente(
        AgenteTablero, "tablero_demo_01",
        perfil_xmpp_de_prueba(), {"nick_muc": nick}, sala,
    )


# ══════════════════════════════════════════════════════════════
#  El tablero del alumno arbitrando la partida
# ══════════════════════════════════════════════════════════════

class TestPartidaTablero:
    """Verifica el agente TABLERO del alumno durante la partida."""

    @pytest.mark.asyncio
    async def test_tablero_anuncia_game_start_a_ambos_jugadores(self):
        """El tablero abre la partida con un ``game-start`` por jugador.

        Cada ``game-start`` es un INFORM con el rival y el ``thread``
        de la partida, dirigido en privado a un jugador.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        jugador_x = JugadorSimulado(sala, "Jug-X", retardo_inicial=0.0)
        jugador_o = JugadorSimulado(sala, "Jug-O", retardo_inicial=0.3)

        await ejecutar_escenario(
            tablero.correr_unica(),
            jugador_x.ejecutar(), jugador_o.ejecutar(),
        )

        anuncios = sala.buscar(accion="game-start", emisor=tablero.nick)
        assert len(anuncios) == 2
        for anuncio in anuncios:
            assert anuncio.performativa == PERFORMATIVA_INFORM
            assert anuncio.cuerpo.get("opponent")
            assert anuncio.cuerpo.get("thread")
            assert anuncio.valido, anuncio.errores
        assert {a.destino for a in anuncios} == {"Jug-X", "Jug-O"}

    @pytest.mark.asyncio
    async def test_tablero_convoca_los_turnos_con_cfp(self):
        """El tablero convoca cada turno con un ``turn`` (CFP).

        El protocolo de partida circula en privado: el Tablero
        emite el ``CFP turn`` como mensaje dirigido al JID privado
        de cada jugador (``sala/nick``), no por difusión. Cada turno
        produce, por tanto, **dos** CFP —uno para cada jugador—.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        jugador_x = JugadorSimulado(sala, "Jug-X", retardo_inicial=0.0)
        jugador_o = JugadorSimulado(sala, "Jug-O", retardo_inicial=0.3)

        await ejecutar_escenario(
            tablero.correr_unica(),
            jugador_x.ejecutar(), jugador_o.ejecutar(),
        )

        turnos = sala.buscar(accion="turn", emisor=tablero.nick)
        assert len(turnos) >= 2
        destinos = {t.destino for t in turnos}
        assert "Jug-X" in destinos and "Jug-O" in destinos
        for turno in turnos:
            assert turno.performativa == PERFORMATIVA_CFP
            assert turno.cuerpo.get("active_symbol") in ("X", "O")
            assert turno.destino != "difusion"
            assert turno.valido, turno.errores

    @pytest.mark.asyncio
    async def test_tablero_confirma_las_jugadas_con_accept_proposal(self):
        """El tablero confirma las jugadas válidas con un ``move``.

        Verifica que el tablero emite **al menos una** confirmación
        durante la partida. Cada confirmación es un ACCEPT_PROPOSAL
        que lleva la casilla y el símbolo del jugador que movió.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        jugador_x = JugadorSimulado(sala, "Jug-X", retardo_inicial=0.0)
        jugador_o = JugadorSimulado(sala, "Jug-O", retardo_inicial=0.3)

        await ejecutar_escenario(
            tablero.correr_unica(),
            jugador_x.ejecutar(), jugador_o.ejecutar(),
        )

        confirmaciones = sala.buscar(
            accion="move",
            emisor=tablero.nick,
            performativa=PERFORMATIVA_ACCEPT_PROPOSAL,
        )
        assert len(confirmaciones) >= 1
        for confirmacion in confirmaciones:
            assert isinstance(confirmacion.cuerpo.get("position"), int)
            assert confirmacion.cuerpo.get("symbol") in ("X", "O")
            assert confirmacion.valido, confirmacion.errores

    @pytest.mark.asyncio
    async def test_tablero_aborta_si_la_jugada_es_invalida(self):
        """El tablero aborta con ``game-over`` ante una jugada ilegal.

        Si un jugador propone una casilla ocupada, el tablero
        notifica el aborto a **ambos** jugadores con sendos
        ``REJECT_PROPOSAL game-over`` privados (``make_reply`` del
        PROPOSE entrante de cada jugador) y registra la partida
        como abortada con ``reason=invalid``.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        jugador_x = JugadorSimulado(sala, "Jug-X", retardo_inicial=0.0)
        jugador_o = JugadorSimulado(
            sala, "Jug-O", modo="jugada_invalida", retardo_inicial=0.3,
        )

        await ejecutar_escenario(
            tablero.correr_unica(),
            jugador_x.ejecutar(), jugador_o.ejecutar(),
        )

        finales = sala.buscar(accion="game-over", emisor=tablero.nick)
        # Dos game-over: uno por jugador, ambos privados.
        assert len(finales) == 2
        for final in finales:
            assert final.performativa == PERFORMATIVA_REJECT_PROPOSAL
            assert final.cuerpo.get("reason") == "invalid"
            assert final.destino != "difusion"
            assert final.valido, final.errores
        destinos = {f.destino for f in finales}
        assert destinos == {"Jug-X", "Jug-O"}

    @pytest.mark.asyncio
    async def test_tablero_aborta_si_un_jugador_no_responde(self):
        """El tablero aborta con ``game-over`` ante un turno sin jugada.

        Si el jugador de turno no envía su ``move``, el tablero
        notifica el aborto a **ambos** jugadores con sendos
        ``REJECT_PROPOSAL game-over`` privados (construidos desde
        cero contra los JID conservados en el registro, porque en
        esta rama no hay mensaje al que responder) con la razón
        ``timeout``.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        jugador_x = JugadorSimulado(sala, "Jug-X", retardo_inicial=0.0)
        jugador_o = JugadorSimulado(
            sala, "Jug-O", modo="sin_jugada", retardo_inicial=0.3,
        )

        await ejecutar_escenario(
            tablero.correr_unica(),
            jugador_x.ejecutar(), jugador_o.ejecutar(),
        )

        finales = sala.buscar(accion="game-over", emisor=tablero.nick)
        assert len(finales) == 2
        for final in finales:
            assert final.cuerpo.get("reason") == "timeout"
            assert final.destino != "difusion"
            assert final.valido, final.errores
        destinos = {f.destino for f in finales}
        assert destinos == {"Jug-X", "Jug-O"}

    @pytest.mark.asyncio
    async def test_tablero_reintenta_el_primer_cfp_si_ambos_jugadores_tardan(self):
        """El Tablero reenvía el primer ``CFP turn`` ante carrera de
        arranque que afecta a los dos jugadores.

        Verifica la cortesía descrita en
        ``doc/GUIA_THREAD_Y_GAME_START.md`` §5.3: si **ninguno**
        de los dos jugadores atiende el primer ``CFP`` —típicamente
        porque sus comportamientos de partida aún se están
        registrando tras procesar el ``game-start``—, el Tablero
        **no** aborta tras el plazo corto del primer ``CFP``;
        reenvía el mismo ``CFP`` una segunda vez y la partida
        continúa.

        Importante: la cortesía solo es procedente cuando **no ha
        llegado ningún ``PROPOSE``** en el plazo corto del primer
        ``CFP``. Si uno de los dos jugadores hubiera respondido a
        tiempo, el canal estaría demostradamente operativo y la
        cortesía **no** se aplicaría: el Tablero solo esperaría al
        rival durante el ``timeout_turno`` normal. Reenviar un
        ``CFP`` cuando uno ya respondió confundiría al respondedor
        (que está en ``ESPERAR_CONFIRMACION``) con un acuse de
        jugada malformado y cerraría la partida prematuramente.
        Por eso este test desactiva expresamente a los **dos**
        jugadores durante la ventana inicial.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        # Ambos jugadores se quedan «sordos» durante el plazo del
        # primer ``CFP``: es la única situación en la que la
        # cortesía debe dispararse.
        jugador_x = JugadorSimulado(
            sala, "Jug-X", retardo_inicial=0.0,
            retardo_partida_inicial=0.45,
        )
        jugador_o = JugadorSimulado(
            sala, "Jug-O", retardo_inicial=0.3,
            retardo_partida_inicial=0.45,
        )

        await ejecutar_escenario(
            tablero.correr_unica(),
            jugador_x.ejecutar(), jugador_o.ejecutar(),
        )

        cfps = sala.buscar(accion="turn", emisor=tablero.nick)
        cfps_iniciales = [
            registro for registro in cfps
            if registro.cuerpo.get("active_symbol") == "X"
        ]
        # Al menos dos CFP iniciales: el primero (que ambos
        # jugadores se perdieron por la carrera de arranque) más
        # el reintento del protocolo de cortesía.
        assert len(cfps_iniciales) >= 2
        # El Tablero no abortó: no hubo ``game-over``.
        abortos = sala.buscar(accion="game-over", emisor=tablero.nick)
        assert abortos == []

    @pytest.mark.asyncio
    async def test_partida_completa_entre_agentes_reales(self):
        """Un tablero y dos jugadores reales completan una partida.

        Es la prueba de integración del protocolo de juego: los tres
        agentes del alumno juegan entre sí y la partida termina en
        un resultado regular (victoria o empate), con todos los
        mensajes conformes a la ontología. Se ejecuta en memoria
        (``SalaSimulada``): el ``game-start`` viaja en el thread de la
        inscripción y el jugador lo capta por su propio thread, sin
        depender de resolver el apodo MUC del tablero.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        jugador_uno = await _montar_jugador(
            sala, "jugador_demo_n1_01", "Jug-01",
        )
        jugador_dos = await _montar_jugador(
            sala, "jugador_demo_n1_02", "Jug-02",
        )
        # El descubrimiento reactivo no se simula en SalaSimulada:
        # se inyecta manualmente el nick del Tablero en cada Jugador.
        anunciar_tablero_descubierto(jugador_uno, tablero.nick)
        anunciar_tablero_descubierto(jugador_dos, tablero.nick)

        await ejecutar_escenario(
            tablero.correr_unica(),
            jugador_uno.correr_unica(), jugador_dos.correr_unica(),
        )

        # El cierre regular de la partida es observable en la sala
        # por el último mensaje de ``turn-result`` con ``result`` en
        # ``{"win", "draw"}``: ese es el contrato fijado por el
        # diagrama de secuencia. No se consulta ningún atributo
        # interno del agente del alumno.
        veredictos = [
            registro for registro in sala.buscar(accion="turn-result")
            if registro.cuerpo.get("result") in ("win", "draw")
        ]
        assert len(veredictos) >= 1, (
            "Ningún jugador anunció el cierre regular con turn-result"
        )
        assert all(registro.valido for registro in sala.historico), [
            registro.errores
            for registro in sala.historico if not registro.valido
        ]


# ══════════════════════════════════════════════════════════════
#  El jugador del alumno durante la partida
# ══════════════════════════════════════════════════════════════

class TestPartidaJugador:
    """Verifica el agente JUGADOR del alumno durante la partida."""

    @pytest.mark.asyncio
    async def test_jugador_propone_su_jugada_con_move(self):
        """El jugador propone su jugada con un ``move`` (PROPOSE).

        El mensaje lleva la casilla en ``position`` y se dirige en
        privado al tablero.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        jugador = await _montar_jugador(
            sala, "jugador_demo_n1_01", "Jug-real",
        )
        tablero = TableroSimulado(sala, modo="normal")
        anunciar_tablero_descubierto(jugador, tablero.nick)
        rival = JugadorSimulado(sala, "Rival-01", retardo_inicial=0.3)

        await ejecutar_escenario(
            jugador.correr_unica(), tablero.ejecutar(), rival.ejecutar(),
        )

        jugadas = sala.buscar(
            accion="move", emisor=jugador.nick,
            performativa=PERFORMATIVA_PROPOSE,
        )
        assert len(jugadas) >= 1
        for jugada in jugadas:
            assert isinstance(jugada.cuerpo.get("position"), int)
            assert jugada.destino != "difusion"
            assert jugada.valido, jugada.errores

    @pytest.mark.asyncio
    async def test_jugador_informa_el_resultado_del_turno(self):
        """El jugador comunica el desenlace de su turno.

        Tras mover, envía un ``turn-result`` (INFORM) con el campo
        ``result`` dentro del vocabulario de la ontología.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        jugador = await _montar_jugador(
            sala, "jugador_demo_n1_01", "Jug-real",
        )
        tablero = TableroSimulado(sala, modo="normal")
        anunciar_tablero_descubierto(jugador, tablero.nick)
        rival = JugadorSimulado(sala, "Rival-01", retardo_inicial=0.3)

        await ejecutar_escenario(
            jugador.correr_unica(), tablero.ejecutar(), rival.ejecutar(),
        )

        acuses = sala.buscar(accion="turn-result", emisor=jugador.nick)
        assert len(acuses) >= 1
        for acuse in acuses:
            assert acuse.performativa == PERFORMATIVA_INFORM
            assert acuse.cuerpo.get("result") in (
                "continue", "win", "draw",
            )
            assert acuse.valido, acuse.errores

    @pytest.mark.asyncio
    async def test_la_partida_del_jugador_no_termina_en_aborto(self):
        """La partida del jugador termina en un resultado regular.

        Esta prueba no inspecciona las jugadas del jugador una a una:
        comprueba el desenlace observable. Si el jugador propusiera
        una casilla ocupada, el tablero abortaría con ``game-over``;
        al exigir que la partida cierre en victoria o empate se
        verifica **indirectamente** que el jugador no provocó ese
        aborto con una jugada ilegal.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        jugador = await _montar_jugador(
            sala, "jugador_demo_n1_01", "Jug-real",
        )
        tablero = TableroSimulado(sala, modo="normal")
        anunciar_tablero_descubierto(jugador, tablero.nick)
        rival = JugadorSimulado(sala, "Rival-01", retardo_inicial=0.3)

        await ejecutar_escenario(
            jugador.correr_unica(), tablero.ejecutar(), rival.ejecutar(),
        )

        assert tablero.informe is not None
        assert tablero.informe["result"] in ("win", "draw")

