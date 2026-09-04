"""Tests del agente ``SupervisorEmergencias``.

Verifican los métodos del agente que pueden probarse sin arrancar
SPADE: ``registrar_seguimiento``, ``registrar_evento`` y la
delegación de ``inyectar_manualmente`` al inyector. Se evita pasar
por ``setup()`` de SPADE creando la instancia con ``object.__new__``
e inyectando manualmente los atributos que el método bajo prueba
necesita (patrón usado en ``TicTacToe — test_agente_supervisor.py``).
"""
from __future__ import annotations

from collections import deque
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from agente_profesor.agente_supervisor import SupervisorEmergencias
from agente_profesor.persistencia.almacen_supervisor import (
    AlmacenSupervisor,
)
from agente_profesor.seguimientos import (
    EstadoSeguimiento,
    Seguimiento,
)


# ─── Helper de instanciación sin SPADE ─────────────────────────────────────

def _construir_supervisor_vacio(modo: str = "activo") -> SupervisorEmergencias:
    """Crea un ``SupervisorEmergencias`` saltándose ``__init__``.

    Inyecta los atributos imprescindibles para que los métodos bajo
    prueba se ejecuten sin tocar XMPP.
    """
    agente = object.__new__(SupervisorEmergencias)
    agente.modo = modo
    agente.es_agente_vivo = True
    agente.grupos = []
    agente.timeouts = {}
    agente.seguimientos = {}
    agente.log_eventos = deque(maxlen=500)
    agente.estados_agentes = {}
    agente.consultas_en_curso = {}
    agente.almacen = None
    agente.ruta_db = ""
    agente.inyector = None
    return agente


# ─── registrar_seguimiento ─────────────────────────────────────────────────

class TestRegistrarSeguimiento:
    """``registrar_seguimiento`` actualiza el dict, persiste y notifica."""

    def test_inserta_en_diccionario(self):
        agente = _construir_supervisor_vacio()
        seguimiento = Seguimiento(
            id_emergencia="abc",
            grupo="fenix",
            jid_destino="centralita_fenix@localhost",
            tipo_emergencia="incendio",
            prioridad="alta",
            descripcion="x",
        )
        agente.registrar_seguimiento(seguimiento)
        assert agente.seguimientos["abc"] is seguimiento

    def test_actualiza_si_ya_existe(self):
        agente = _construir_supervisor_vacio()
        seguimiento = Seguimiento(
            id_emergencia="abc", grupo="fenix",
            jid_destino="centralita_fenix@localhost",
            tipo_emergencia="incendio", prioridad="alta",
            descripcion="x",
        )
        agente.registrar_seguimiento(seguimiento)
        seguimiento.registrar_envio()
        agente.registrar_seguimiento(seguimiento)
        # Sigue siendo el mismo objeto y con estado actualizado.
        assert agente.seguimientos["abc"].estado == EstadoSeguimiento.ENVIADO

    def test_persiste_en_almacen_si_disponible(self, almacen_temporal):
        agente = _construir_supervisor_vacio()
        agente.almacen = almacen_temporal
        almacen_temporal.crear_ejecucion("activo", [])

        seguimiento = Seguimiento(
            id_emergencia="abc", grupo="fenix",
            jid_destino="centralita_fenix@localhost",
            tipo_emergencia="incendio", prioridad="alta",
            descripcion="x",
        )
        agente.registrar_seguimiento(seguimiento)
        listado = almacen_temporal.listar_ejecuciones()
        ejec_id = listado[0]["id"]
        datos = almacen_temporal.obtener_ejecucion(ejec_id)
        assert len(datos["seguimientos"]) == 1


# ─── registrar_evento ──────────────────────────────────────────────────────

class TestRegistrarEvento:
    """``registrar_evento`` añade el evento al log con marca temporal."""

    def test_evento_se_inserta_al_principio(self):
        agente = _construir_supervisor_vacio()
        agente.registrar_evento("info", "supervisor", "primer evento")
        agente.registrar_evento("info", "supervisor", "segundo evento")
        # El más reciente es el primero (deque.appendleft).
        eventos = list(agente.log_eventos)
        assert eventos[0]["detalle"] == "segundo evento"
        assert eventos[1]["detalle"] == "primer evento"

    def test_evento_incluye_marca_temporal(self):
        agente = _construir_supervisor_vacio()
        agente.registrar_evento("info", "supervisor", "x")
        evento = agente.log_eventos[0]
        # Formato HH:MM:SS: 8 caracteres con dos ':'.
        assert len(evento["ts"]) == 8
        assert evento["ts"].count(":") == 2

    def test_evento_persiste_si_almacen_disponible(self, almacen_temporal):
        agente = _construir_supervisor_vacio()
        agente.almacen = almacen_temporal
        ejec_id = almacen_temporal.crear_ejecucion("activo", [])
        agente.registrar_evento("info", "supervisor", "evento test")

        datos = almacen_temporal.obtener_ejecucion(ejec_id)
        assert any(
            e["detalle"] == "evento test" for e in datos["log"]
        )


# ─── inyectar_manualmente ──────────────────────────────────────────────────

class TestInyectarManualmente:
    """Delegación al inyector según el modo de operación."""

    @pytest.mark.asyncio
    async def test_modo_consulta_devuelve_none(self):
        agente = _construir_supervisor_vacio(modo="consulta")
        agente.inyector = None
        resultado = await agente.inyectar_manualmente(id_grupo="fenix")
        assert resultado is None

    @pytest.mark.asyncio
    async def test_sin_inyector_devuelve_none(self):
        agente = _construir_supervisor_vacio(modo="activo")
        agente.inyector = None
        resultado = await agente.inyectar_manualmente(id_grupo="fenix")
        assert resultado is None

    @pytest.mark.asyncio
    async def test_delega_en_inyector_si_modo_activo(self):
        agente = _construir_supervisor_vacio(modo="activo")

        seguimiento_falso = Seguimiento(
            id_emergencia="abc", grupo="fenix",
            jid_destino="centralita_fenix@localhost",
            tipo_emergencia="incendio", prioridad="alta",
            descripcion="x",
        )
        # Inyector simulado con inyectar_a_grupo asíncrono.
        class _InyectorSimulado:
            def __init__(self):
                self.llamadas = []

            async def inyectar_a_grupo(self, id_grupo, clave_escenario):
                self.llamadas.append((id_grupo, clave_escenario))
                return seguimiento_falso

        inyector = _InyectorSimulado()
        agente.inyector = inyector

        resultado = await agente.inyectar_manualmente(
            id_grupo="fenix", clave_escenario="incendio_alta",
        )
        assert resultado is seguimiento_falso
        assert inyector.llamadas == [("fenix", "incendio_alta")]
