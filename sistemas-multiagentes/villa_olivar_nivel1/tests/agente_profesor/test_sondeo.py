"""Tests del ``SondeoEstadoBehaviour``.

Verifican que cada disparo emite un mensaje ``query-ref`` por cada
combinación (grupo, rol) y que ``procesar_estado_agente_recibido``
asienta en ``estados_agentes`` los datos del rol consultado.
"""
from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from agente_profesor.comportamientos.sondeo import (
    ROLES_POR_DEFECTO,
    SondeoEstadoBehaviour,
    procesar_estado_agente_recibido,
)


def _construir_sondeo(agente, period: float = 15.0) -> SondeoEstadoBehaviour:
    behaviour = SondeoEstadoBehaviour(period=period)
    behaviour.agent = agente
    behaviour.send = AsyncMock()
    return behaviour


# ─── Disparo periódico ─────────────────────────────────────────────────────

class TestDisparoPeriodico:
    """Cada disparo emite un mensaje por (grupo, rol)."""

    @pytest.mark.asyncio
    async def test_envia_un_mensaje_por_rol_y_grupo(
        self, agente_simulado,
    ):
        sondeo = _construir_sondeo(agente_simulado)
        await sondeo.on_start()
        await sondeo.run()

        # 2 grupos × 5 roles por defecto = 10 mensajes.
        esperados = len(agente_simulado.grupos) * len(ROLES_POR_DEFECTO)
        assert sondeo.send.await_count == esperados

    @pytest.mark.asyncio
    async def test_jid_destino_sigue_la_convencion(
        self, agente_simulado,
    ):
        sondeo = _construir_sondeo(agente_simulado)
        await sondeo.on_start()
        await sondeo.run()

        destinatarios = {
            llamada.args[0].to
            for llamada in sondeo.send.await_args_list
        }
        # bomberos_fenix@localhost, sanitario_fenix@localhost, etc.
        assert "bomberos_fenix@localhost" in destinatarios
        assert "centralita_olivar42@localhost" in destinatarios

    @pytest.mark.asyncio
    async def test_consulta_se_registra_en_consultas_en_curso(
        self, agente_simulado,
    ):
        sondeo = _construir_sondeo(agente_simulado)
        await sondeo.on_start()
        await sondeo.run()

        assert len(agente_simulado.consultas_en_curso) > 0
        # Cada consulta tiene rol, grupo y jid_destino.
        primera = next(iter(agente_simulado.consultas_en_curso.values()))
        assert "rol" in primera
        assert "grupo" in primera
        assert "jid_destino" in primera


# ─── Procesado de respuestas ──────────────────────────────────────────────

class TestProcesarEstado:
    """``procesar_estado_agente_recibido`` actualiza la tabla."""

    def test_estado_valido_se_almacena(self, agente_simulado):
        # Inserta una consulta abierta como si el sondeo la hubiera
        # disparado.
        agente_simulado.consultas_en_curso["sondeo-123"] = {
            "rol": "bomberos",
            "grupo": "fenix",
            "jid_destino": "bomberos_fenix@localhost",
            "instante_envio": datetime.now(),
        }
        cuerpo = json.dumps({
            "tipo_mensaje": "estado_agente",
            "agente": "bomberos_fenix@localhost",
            "estado": "ocupado",
            "emergencia_actual": "id-99",
            "detalle": "Camión en escena",
        })
        consumido = procesar_estado_agente_recibido(
            agente_simulado, "sondeo-123", cuerpo,
        )
        assert consumido is True
        clave = ("fenix", "bomberos")
        assert clave in agente_simulado.estados_agentes
        registro = agente_simulado.estados_agentes[clave]
        assert registro["estado"] == "ocupado"
        assert registro["latencia_ms"] >= 0

    def test_conversation_id_no_abierto_devuelve_falso(
        self, agente_simulado,
    ):
        consumido = procesar_estado_agente_recibido(
            agente_simulado, "no-existe", "{}",
        )
        assert consumido is False

    def test_estado_invalido_consume_pero_no_almacena(
        self, agente_simulado,
    ):
        agente_simulado.consultas_en_curso["sondeo-x"] = {
            "rol": "bomberos",
            "grupo": "fenix",
            "jid_destino": "bomberos_fenix@localhost",
            "instante_envio": datetime.now(),
        }
        consumido = procesar_estado_agente_recibido(
            agente_simulado, "sondeo-x", "{esto no es json válido",
        )
        # La consulta se consumió (era nuestra) pero el estado es
        # inválido → no se asienta.
        assert consumido is True
        assert ("fenix", "bomberos") not in agente_simulado.estados_agentes
