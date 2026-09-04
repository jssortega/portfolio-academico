"""Pruebas del uso de la FACTORÍA y de los JID.

Para que los agentes del alumno superen las pruebas de protocolo
(registro, partida e informe) necesitan integrarse correctamente
en la infraestructura de la rama. Estas pruebas comprueban los
dos puntos donde más a menudo falla esa integración, descritos en
``doc/PROBLEMAS_FRECUENTES_EXAMEN.md``:

1. **La factoría** ``utils.crear_agente`` debe poder construir el
   agente del alumno y darle el JID que corresponde al perfil XMPP
   activo, sin que el alumno fije ningún JID literal.
2. **El JID y el nick** dentro de la sala MUC: cada agente se une
   con el nick de su configuración y se dirige a los demás por su
   **nick** de sala, nunca por el JID del agente.

Si estas pruebas fallan, las de protocolo también fallarán: por
eso conviene revisarlas primero.
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from agentes.agente_jugador import AgenteJugador
from agentes.agente_tablero import AgenteTablero
from tests.simuladores import (
    SALA_DE_PRUEBA,
    JugadorSimulado,
    SalaSimulada,
    TableroSimulado,
    acelerar_tiempos,
    ejecutar_escenario,
    montar_agente,
    perfil_xmpp_de_prueba,
)
from tests.simuladores.arnes import anunciar_tablero_descubierto
from utils import arrancar_agente, construir_jid, crear_agente


@pytest.fixture(autouse=True)
def _acelerar(monkeypatch):
    """Acorta los plazos de espera de los agentes en cada prueba."""
    acelerar_tiempos(monkeypatch)


# ══════════════════════════════════════════════════════════════
#  Uso de la factoría de agentes
# ══════════════════════════════════════════════════════════════

class TestFactoria:
    """Verifica que los agentes del alumno usan bien la factoría."""

    def test_construir_jid_usa_el_dominio_del_perfil(self):
        """``construir_jid`` forma el JID como ``nombre@dominio``."""
        jid = construir_jid(
            "tablero_demo_01", {"dominio": "sinbad2.ujaen.es"},
        )
        assert jid == "tablero_demo_01@sinbad2.ujaen.es"

    def test_crear_agente_construye_el_jid_desde_la_config(self):
        """La factoría da al agente el JID del perfil XMPP activo.

        El nombre del agente y el dominio del perfil deben aparecer
        en el JID del agente creado.
        """
        perfil = perfil_xmpp_de_prueba(dominio="sinbad2.ujaen.es")
        agente = crear_agente(AgenteTablero, "tablero_demo_01", perfil)
        jid = str(agente.jid)
        assert "tablero_demo_01" in jid
        assert "sinbad2.ujaen.es" in jid

    def test_crear_agente_no_fija_ningun_jid_literal(self):
        """El JID del agente cambia con el dominio del perfil.

        Si el agente fijara un JID literal en su código, el JID no
        dependería del perfil; comprobamos que sí depende.
        """
        agente_local = crear_agente(
            AgenteTablero, "tablero_demo_01",
            perfil_xmpp_de_prueba(dominio="localhost"),
        )
        agente_uja = crear_agente(
            AgenteTablero, "tablero_demo_01",
            perfil_xmpp_de_prueba(dominio="sinbad2.ujaen.es"),
        )
        assert str(agente_local.jid) != str(agente_uja.jid)
        assert "localhost" in str(agente_local.jid)
        assert "sinbad2.ujaen.es" in str(agente_uja.jid)

    def test_crear_agente_admite_las_clases_del_alumno(self):
        """La factoría puede instanciar el tablero y el jugador.

        Si el alumno cambiara la firma del constructor de sus
        agentes, la factoría no podría crearlos y esta prueba lo
        delataría.
        """
        perfil = perfil_xmpp_de_prueba()
        tablero = crear_agente(AgenteTablero, "tablero_demo_01", perfil)
        jugador = crear_agente(
            AgenteJugador, "jugador_demo_n1_01", perfil,
        )
        assert isinstance(tablero, AgenteTablero)
        assert isinstance(jugador, AgenteJugador)

    @pytest.mark.asyncio
    async def test_arrancar_agente_propaga_auto_register(self):
        """``arrancar_agente`` pasa ``auto_register`` a ``start``.

        El registro automático de la cuenta XMPP es un parámetro de
        ``start()`` en SPADE 4.x; la factoría debe tomarlo del
        perfil y propagarlo.
        """
        agente_sin_registro = SimpleNamespace(start=AsyncMock())
        await arrancar_agente(agente_sin_registro, {"auto_register": False})
        agente_sin_registro.start.assert_awaited_once_with(
            auto_register=False,
        )

        agente_con_registro = SimpleNamespace(start=AsyncMock())
        await arrancar_agente(agente_con_registro, {"auto_register": True})
        agente_con_registro.start.assert_awaited_once_with(
            auto_register=True,
        )


# ══════════════════════════════════════════════════════════════
#  Uso del JID y del nick dentro de la sala MUC
# ══════════════════════════════════════════════════════════════

class TestNickEnLaSala:
    """Verifica que los agentes usan bien el nick dentro de la sala."""

    @pytest.mark.asyncio
    async def test_agente_se_une_a_la_sala_con_el_nick_de_la_config(self):
        """El agente entra en la sala con el nick de su configuración.

        ``generar_agentes`` asigna a cada agente un nick único en
        ``config_parametros["nick_muc"]``; el agente debe usar ese
        valor al unirse, no un nick fijo.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        montado = await montar_agente(
            AgenteTablero, "tablero_demo_01",
            perfil_xmpp_de_prueba(),
            {"nick_muc": "tablero_demo-07"}, sala,
        )
        union_muc = montado.agente.client.plugin["xep_0045"].join_muc
        union_muc.assert_called_once()
        _, argumentos = union_muc.call_args
        assert argumentos.get("nick") == "tablero_demo-07"

    @pytest.mark.asyncio
    async def test_tablero_dirige_sus_respuestas_por_nick(self):
        """El tablero responde a cada jugador por su nick de sala.

        Si comparase ``msg.sender`` con un JID ``nombre@dominio``,
        la respuesta privada no llegaría. La comprobación: la
        ``join-accepted`` se dirige al nick del jugador.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        nick_tablero = "tablero_demo-01"
        nick_jugador = "jugador_ana-n1-01"
        tablero = await montar_agente(
            AgenteTablero, "tablero_demo_01",
            perfil_xmpp_de_prueba(), {"nick_muc": nick_tablero}, sala,
        )
        # El jugador descubre al Tablero por el nick que ocupa la
        # sala y le dirige el REQUEST en privado a ese nick.
        jugador = JugadorSimulado(
            sala, nick_jugador, modo="solo_inscripcion",
            nick_tablero=nick_tablero,
        )

        await ejecutar_escenario(
            tablero.correr_unica(), jugador.ejecutar(),
        )

        aceptaciones = sala.buscar(
            accion="join-accepted", emisor=nick_tablero,
        )
        assert len(aceptaciones) == 1
        assert aceptaciones[0].destino == nick_jugador

    @pytest.mark.asyncio
    async def test_jugador_dirige_sus_jugadas_al_nick_del_tablero(self):
        """El jugador envía sus jugadas al nick del tablero.

        El jugador conoce al tablero solo por el nick que aparece
        como remitente de la ``join-accepted``; debe usar ese nick
        —y no un JID inventado— para enviarle sus ``move``.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        nick_tablero_simulado = "tablero_sim-01"
        nick_jugador = "jugador_demo-n1-01"
        nick_rival = "jugador_rival-n1-01"
        jugador = await montar_agente(
            AgenteJugador, "jugador_demo_n1_01",
            perfil_xmpp_de_prueba(), {"nick_muc": nick_jugador}, sala,
        )
        tablero = TableroSimulado(
            sala, nick=nick_tablero_simulado, modo="normal",
        )
        # El jugador real debe conocer el nick del Tablero antes de
        # poder dirigirle ningún mensaje. La utilidad de
        # descubrimiento (verificada aparte) lo poblaría con la
        # presencia MUC; aquí se inyecta directamente.
        anunciar_tablero_descubierto(jugador, nick_tablero_simulado)
        rival = JugadorSimulado(
            sala, nick_rival, retardo_inicial=0.05,
            nick_tablero=nick_tablero_simulado,
        )

        await ejecutar_escenario(
            jugador.correr_unica(), tablero.ejecutar(), rival.ejecutar(),
        )

        jugadas = sala.buscar(accion="move", emisor=nick_jugador)
        assert len(jugadas) >= 1
        assert all(
            jugada.destino == nick_tablero_simulado for jugada in jugadas
        )
