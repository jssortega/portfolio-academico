"""Tests del ``ReceptorRespuestasBehaviour``.

El receptor avanza el autómata del seguimiento al recibir mensajes
FIPA-ACL. Los tests construyen mensajes simulados, los entregan al
behaviour mediante ``receive`` (sustituido por un AsyncMock) y
comprueban que el seguimiento queda en el estado esperado.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from agente_profesor.comportamientos.receptor import (
    ReceptorRespuestasBehaviour,
)
from agente_profesor.seguimientos import (
    EstadoSeguimiento,
    Seguimiento,
)
from tests.agente_profesor.conftest import MensajeSimulado


# ─── Helpers ───────────────────────────────────────────────────────────────

def _seguimiento_en_estado(
    estado: EstadoSeguimiento,
    id_emergencia: str = "id-1",
) -> Seguimiento:
    """Devuelve un seguimiento ya en el estado solicitado.

    Replica la secuencia de transiciones internas para que los
    instantes (envío/agree) estén correctamente rellenados.
    """
    seguimiento = Seguimiento(
        id_emergencia=id_emergencia,
        grupo="fenix",
        jid_destino="centralita_fenix@localhost",
        tipo_emergencia="incendio",
        prioridad="alta",
        descripcion="Calle Mayor 14 — humo denso",
    )
    if estado == EstadoSeguimiento.PREPARADO:
        return seguimiento
    seguimiento.registrar_envio()
    if estado == EstadoSeguimiento.ENVIADO:
        return seguimiento
    seguimiento.registrar_agree()
    return seguimiento


def _construir_receptor(agente, mensaje=None):
    """Crea el receptor con ``receive`` devolviendo ``mensaje``."""
    behaviour = ReceptorRespuestasBehaviour()
    behaviour.agent = agente
    behaviour.receive = AsyncMock(return_value=mensaje)
    return behaviour


# ─── Performativa agree ────────────────────────────────────────────────────

class TestAgree:
    """Un ``agree`` lleva el seguimiento de ENVIADO a ACEPTADO."""

    @pytest.mark.asyncio
    async def test_agree_transiciona_a_aceptado(self, agente_simulado):
        seguimiento = _seguimiento_en_estado(
            EstadoSeguimiento.ENVIADO, id_emergencia="abc",
        )
        agente_simulado.seguimientos[seguimiento.id_emergencia] = seguimiento
        mensaje = MensajeSimulado(
            performativa="agree", conversation_id="abc",
        )
        receptor = _construir_receptor(agente_simulado, mensaje)
        await receptor.run()
        assert seguimiento.estado == EstadoSeguimiento.ACEPTADO


# ─── Performativa inform (RESUELTO) ────────────────────────────────────────

class TestInformValido:
    """Un ``inform`` con InformeResolucion válido lleva a RESUELTO."""

    def _cuerpo_informe_valido(self, seguimiento):
        return json.dumps({
            "tipo_mensaje": "informe_resolucion",
            "id_emergencia": seguimiento.id_emergencia,
            "tipo_emergencia": seguimiento.tipo_emergencia,
            "prioridad": seguimiento.prioridad,
            "estado_final": "resuelto",
            "resumen": "Cierre coordinado",
            "agentes_participantes": [],
            "acciones_realizadas": [],
        })

    @pytest.mark.asyncio
    async def test_inform_valido_transiciona_a_resuelto(
        self, agente_simulado,
    ):
        seguimiento = _seguimiento_en_estado(
            EstadoSeguimiento.ACEPTADO, id_emergencia="def",
        )
        agente_simulado.seguimientos[seguimiento.id_emergencia] = seguimiento
        mensaje = MensajeSimulado(
            performativa="inform",
            conversation_id="def",
            cuerpo=self._cuerpo_informe_valido(seguimiento),
        )
        receptor = _construir_receptor(agente_simulado, mensaje)
        await receptor.run()
        assert seguimiento.estado == EstadoSeguimiento.RESUELTO
        assert seguimiento.informe is not None


# ─── Performativa inform (FALLIDO) ─────────────────────────────────────────

class TestInformInvalido:
    """``inform`` con cuerpo no válido lleva a FALLIDO."""

    @pytest.mark.asyncio
    async def test_json_no_parseable_lleva_a_fallido(
        self, agente_simulado,
    ):
        seguimiento = _seguimiento_en_estado(
            EstadoSeguimiento.ACEPTADO, id_emergencia="ghi",
        )
        agente_simulado.seguimientos[seguimiento.id_emergencia] = seguimiento
        mensaje = MensajeSimulado(
            performativa="inform",
            conversation_id="ghi",
            cuerpo="{esto no es json",
        )
        receptor = _construir_receptor(agente_simulado, mensaje)
        await receptor.run()
        assert seguimiento.estado == EstadoSeguimiento.FALLIDO
        assert seguimiento.error is not None

    @pytest.mark.asyncio
    async def test_informe_incoherente_lleva_a_fallido(
        self, agente_simulado,
    ):
        seguimiento = _seguimiento_en_estado(
            EstadoSeguimiento.ACEPTADO, id_emergencia="jkl",
        )
        agente_simulado.seguimientos[seguimiento.id_emergencia] = seguimiento
        # tipo_emergencia distinto del original (incendio vs inundacion).
        cuerpo = json.dumps({
            "tipo_mensaje": "informe_resolucion",
            "id_emergencia": "jkl",
            "tipo_emergencia": "inundacion",
            "prioridad": "alta",
            "estado_final": "resuelto",
            "resumen": "Cierre incoherente",
            "agentes_participantes": [],
            "acciones_realizadas": [],
        })
        mensaje = MensajeSimulado(
            performativa="inform",
            conversation_id="jkl",
            cuerpo=cuerpo,
        )
        receptor = _construir_receptor(agente_simulado, mensaje)
        await receptor.run()
        assert seguimiento.estado == EstadoSeguimiento.FALLIDO


# ─── Performativas de rechazo ──────────────────────────────────────────────

class TestRechazo:
    """``refuse`` y ``not-understood`` llevan a RECHAZADO."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("performativa", ["refuse", "not-understood"])
    async def test_rechazo_lleva_a_rechazado(
        self, agente_simulado, performativa,
    ):
        seguimiento = _seguimiento_en_estado(
            EstadoSeguimiento.ENVIADO, id_emergencia="mno",
        )
        agente_simulado.seguimientos[seguimiento.id_emergencia] = seguimiento
        mensaje = MensajeSimulado(
            performativa=performativa,
            conversation_id="mno",
        )
        receptor = _construir_receptor(agente_simulado, mensaje)
        await receptor.run()
        assert seguimiento.estado == EstadoSeguimiento.RECHAZADO


# ─── Mensajes que se ignoran ───────────────────────────────────────────────

class TestMensajesIgnorados:
    """Los mensajes sin seguimiento o con performativa rara se loguean."""

    @pytest.mark.asyncio
    async def test_sin_mensaje_no_falla(self, agente_simulado):
        receptor = _construir_receptor(agente_simulado, mensaje=None)
        await receptor.run()
        # No se registró ningún evento.
        assert agente_simulado.llamadas_eventos == []

    @pytest.mark.asyncio
    async def test_conversation_id_desconocido_genera_warn(
        self, agente_simulado,
    ):
        mensaje = MensajeSimulado(
            performativa="agree", conversation_id="no-existe",
        )
        receptor = _construir_receptor(agente_simulado, mensaje)
        await receptor.run()
        tipos = [e["tipo"] for e in agente_simulado.llamadas_eventos]
        assert "warn" in tipos

    @pytest.mark.asyncio
    async def test_performativa_extranya_genera_warn(
        self, agente_simulado,
    ):
        seguimiento = _seguimiento_en_estado(
            EstadoSeguimiento.ENVIADO, id_emergencia="pqr",
        )
        agente_simulado.seguimientos[seguimiento.id_emergencia] = seguimiento
        mensaje = MensajeSimulado(
            performativa="propose", conversation_id="pqr",
        )
        receptor = _construir_receptor(agente_simulado, mensaje)
        await receptor.run()
        # El estado del seguimiento no cambia.
        assert seguimiento.estado == EstadoSeguimiento.ENVIADO
