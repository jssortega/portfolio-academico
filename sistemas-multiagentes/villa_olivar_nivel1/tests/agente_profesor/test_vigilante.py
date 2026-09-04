"""Tests del ``VigilanteTimeoutsBehaviour``.

El vigilante caduca seguimientos cuyos plazos han expirado. Los tests
manipulan los instantes (``instante_envio`` / ``instante_agree``) hacia
atrás en el tiempo para forzar la transición sin tener que esperar
realmente al timeout.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from agente_profesor.comportamientos.vigilante import (
    VigilanteTimeoutsBehaviour,
)
from agente_profesor.seguimientos import (
    EstadoSeguimiento,
    Seguimiento,
)


# ─── Helpers ───────────────────────────────────────────────────────────────

def _construir_vigilante(agente):
    behaviour = VigilanteTimeoutsBehaviour(period=1.0)
    behaviour.agent = agente
    return behaviour


def _seguimiento_en_envio(
    instante_envio: datetime, id_emergencia: str = "id-1",
) -> Seguimiento:
    """Construye un seguimiento en ENVIADO con ``instante_envio`` dado."""
    seguimiento = Seguimiento(
        id_emergencia=id_emergencia,
        grupo="fenix",
        jid_destino="centralita_fenix@localhost",
        tipo_emergencia="incendio",
        prioridad="alta",
        descripcion="prueba",
    )
    seguimiento.registrar_envio()
    seguimiento.instante_envio = instante_envio
    return seguimiento


def _seguimiento_en_aceptado(
    instante_agree: datetime, id_emergencia: str = "id-2",
) -> Seguimiento:
    seguimiento = _seguimiento_en_envio(
        datetime.now() - timedelta(seconds=10),
        id_emergencia=id_emergencia,
    )
    seguimiento.registrar_agree()
    seguimiento.instante_agree = instante_agree
    return seguimiento


# ─── Timeout de agree ──────────────────────────────────────────────────────

class TestTimeoutAgree:
    """Si ``agree_segundos`` se supera, el seguimiento va a TIMEOUT."""

    @pytest.mark.asyncio
    async def test_envio_caducado_va_a_timeout(self, agente_simulado):
        # Plazo: 5 s. Forzamos un envío hace 10 s.
        antiguo = datetime.now() - timedelta(seconds=10)
        seguimiento = _seguimiento_en_envio(antiguo)
        agente_simulado.seguimientos[seguimiento.id_emergencia] = seguimiento

        vigilante = _construir_vigilante(agente_simulado)
        await vigilante.run()

        assert seguimiento.estado == EstadoSeguimiento.TIMEOUT
        assert "agree" in (seguimiento.error or "").lower()

    @pytest.mark.asyncio
    async def test_envio_dentro_de_plazo_no_caduca(self, agente_simulado):
        reciente = datetime.now() - timedelta(seconds=1)
        seguimiento = _seguimiento_en_envio(reciente)
        agente_simulado.seguimientos[seguimiento.id_emergencia] = seguimiento

        vigilante = _construir_vigilante(agente_simulado)
        await vigilante.run()

        assert seguimiento.estado == EstadoSeguimiento.ENVIADO


# ─── Timeout de informe ────────────────────────────────────────────────────

class TestTimeoutInforme:
    """Si ``informe_segundos`` se supera, ACEPTADO va a TIMEOUT."""

    @pytest.mark.asyncio
    async def test_aceptado_caducado_va_a_timeout(self, agente_simulado):
        # Plazo informe: 180 s. Forzamos un agree hace 200 s.
        antiguo_agree = datetime.now() - timedelta(seconds=200)
        seguimiento = _seguimiento_en_aceptado(antiguo_agree)
        agente_simulado.seguimientos[seguimiento.id_emergencia] = seguimiento

        vigilante = _construir_vigilante(agente_simulado)
        await vigilante.run()

        assert seguimiento.estado == EstadoSeguimiento.TIMEOUT
        assert "informe" in (seguimiento.error or "").lower() or \
               "informeresolucion" in (seguimiento.error or "").lower()

    @pytest.mark.asyncio
    async def test_aceptado_dentro_de_plazo_no_caduca(
        self, agente_simulado,
    ):
        reciente_agree = datetime.now() - timedelta(seconds=10)
        seguimiento = _seguimiento_en_aceptado(reciente_agree)
        agente_simulado.seguimientos[seguimiento.id_emergencia] = seguimiento

        vigilante = _construir_vigilante(agente_simulado)
        await vigilante.run()

        assert seguimiento.estado == EstadoSeguimiento.ACEPTADO


# ─── Estado terminal ───────────────────────────────────────────────────────

class TestEstadoTerminal:
    """El vigilante ignora seguimientos en estado terminal."""

    @pytest.mark.asyncio
    async def test_no_modifica_resueltos(self, agente_simulado):
        seguimiento = _seguimiento_en_aceptado(datetime.now())
        seguimiento.registrar_informe({"tipo_mensaje": "informe_resolucion"})
        # Ahora está en RESUELTO.
        assert seguimiento.estado == EstadoSeguimiento.RESUELTO
        agente_simulado.seguimientos[seguimiento.id_emergencia] = seguimiento

        vigilante = _construir_vigilante(agente_simulado)
        await vigilante.run()

        assert seguimiento.estado == EstadoSeguimiento.RESUELTO

    @pytest.mark.asyncio
    async def test_diccionario_vacio_no_falla(self, agente_simulado):
        vigilante = _construir_vigilante(agente_simulado)
        await vigilante.run()
        assert agente_simulado.llamadas_eventos == []
