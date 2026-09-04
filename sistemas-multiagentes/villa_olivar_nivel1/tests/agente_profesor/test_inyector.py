"""Tests del ``InyectorIncidentesBehaviour``.

Verifican el flujo de inyección manual y el round-robin del modo
automático sin arrancar SPADE: se construye una instancia del
behaviour, se le asigna el agente simulado y se sustituye el método
``send`` por una corrutina que captura los mensajes enviados.
"""
from __future__ import annotations

import json
from typing import List
from unittest.mock import AsyncMock

import pytest

from agente_profesor.comportamientos.inyector import (
    ONTOLOGIA_EMERGENCIAS,
    PROTOCOLO_INYECCION,
    TIPO_MENSAJE_INYECCION,
    InyectorIncidentesBehaviour,
)
from agente_profesor.escenarios import (
    claves_escenarios,
    construir_id_emergencia,
)
from agente_profesor.seguimientos import EstadoSeguimiento


# ─── Helper de instanciación ───────────────────────────────────────────────

def _construir_behaviour(agente, period: float = 30.0) -> InyectorIncidentesBehaviour:
    """Construye el behaviour y le asigna el agente simulado.

    Replica el patrón usado en TicTacToe (``test_supervisor_behaviours.py``):
    se llama a ``on_start`` manualmente para inicializar el estado
    interno y se reemplaza ``send`` por un ``AsyncMock``.
    """
    behaviour = InyectorIncidentesBehaviour(period=period)
    behaviour.agent = agente
    behaviour.send = AsyncMock()
    return behaviour


# ─── Inyección manual a un grupo conocido ──────────────────────────────────

class TestInyeccionManual:
    """``inyectar_a_grupo`` envía un request y crea un seguimiento."""

    @pytest.mark.asyncio
    async def test_envia_request_al_jid_de_la_centralita(
        self, agente_simulado,
    ):
        behaviour = _construir_behaviour(agente_simulado)
        await behaviour.on_start()

        seguimiento = await behaviour.inyectar_a_grupo(
            id_grupo="fenix", clave_escenario="incendio_alta",
        )
        assert seguimiento is not None
        # Comprobar que se ha llamado a send con un mensaje cuyo
        # destinatario es el jid_centralita del grupo.
        assert behaviour.send.await_count == 1
        mensaje_enviado = behaviour.send.await_args.args[0]
        assert mensaje_enviado.to == "centralita_fenix@localhost"

    @pytest.mark.asyncio
    async def test_metadatos_fipa_acl_son_los_esperados(
        self, agente_simulado,
    ):
        behaviour = _construir_behaviour(agente_simulado)
        await behaviour.on_start()

        await behaviour.inyectar_a_grupo(
            id_grupo="fenix", clave_escenario="incendio_alta",
        )
        mensaje = behaviour.send.await_args.args[0]
        # SPADE almacena las metadatas con set_metadata; las
        # recuperamos accediendo al diccionario interno (`metadata`).
        meta = mensaje.metadata
        assert meta["performative"] == "request"
        assert meta["protocol"] == PROTOCOLO_INYECCION
        assert meta["ontology"] == ONTOLOGIA_EMERGENCIAS
        assert meta["language"] == "json-pydantic"

    @pytest.mark.asyncio
    async def test_conversation_id_es_el_id_emergencia(
        self, agente_simulado,
    ):
        behaviour = _construir_behaviour(agente_simulado)
        await behaviour.on_start()

        seguimiento = await behaviour.inyectar_a_grupo(
            id_grupo="fenix", clave_escenario="incendio_alta",
        )
        mensaje = behaviour.send.await_args.args[0]
        assert mensaje.metadata["conversation_id"] == seguimiento.id_emergencia

    @pytest.mark.asyncio
    async def test_cuerpo_del_request_es_json_valido(
        self, agente_simulado,
    ):
        behaviour = _construir_behaviour(agente_simulado)
        await behaviour.on_start()

        await behaviour.inyectar_a_grupo(
            id_grupo="fenix", clave_escenario="incendio_alta",
        )
        mensaje = behaviour.send.await_args.args[0]
        cuerpo = json.loads(mensaje.body)
        assert cuerpo["tipo_mensaje"] == TIPO_MENSAJE_INYECCION
        assert cuerpo["tipo_emergencia"] == "incendio"
        assert cuerpo["prioridad"] == "alta"
        assert cuerpo["id_emergencia"] == construir_id_emergencia(
            "incendio_alta",
        )

    @pytest.mark.asyncio
    async def test_seguimiento_creado_queda_en_envio(
        self, agente_simulado,
    ):
        behaviour = _construir_behaviour(agente_simulado)
        await behaviour.on_start()

        seguimiento = await behaviour.inyectar_a_grupo(
            id_grupo="fenix", clave_escenario="incendio_alta",
        )
        assert seguimiento.estado == EstadoSeguimiento.ENVIADO
        # El supervisor recibió la transición PREPARADO + ENVIADO.
        assert seguimiento in agente_simulado.llamadas_seguimientos

    @pytest.mark.asyncio
    async def test_evento_request_se_registra_en_log(
        self, agente_simulado,
    ):
        behaviour = _construir_behaviour(agente_simulado)
        await behaviour.on_start()

        await behaviour.inyectar_a_grupo(
            id_grupo="fenix", clave_escenario="incendio_alta",
        )
        tipos = [e["tipo"] for e in agente_simulado.llamadas_eventos]
        assert "request" in tipos


# ─── Validaciones de error ─────────────────────────────────────────────────

class TestValidacionesError:
    """``inyectar_a_grupo`` rechaza grupos y escenarios desconocidos."""

    @pytest.mark.asyncio
    async def test_grupo_desconocido_devuelve_none(
        self, agente_simulado,
    ):
        behaviour = _construir_behaviour(agente_simulado)
        await behaviour.on_start()

        resultado = await behaviour.inyectar_a_grupo(
            id_grupo="grupo_que_no_existe",
        )
        assert resultado is None
        assert behaviour.send.await_count == 0

    @pytest.mark.asyncio
    async def test_escenario_desconocido_devuelve_none(
        self, agente_simulado,
    ):
        behaviour = _construir_behaviour(agente_simulado)
        await behaviour.on_start()

        resultado = await behaviour.inyectar_a_grupo(
            id_grupo="fenix",
            clave_escenario="incendio_imposible_999",
        )
        assert resultado is None
        assert behaviour.send.await_count == 0


# ─── Modo automático y round-robin ─────────────────────────────────────────

class TestModoAutomatico:
    """En modo automático, cada disparo elige un grupo distinto."""

    @pytest.mark.asyncio
    async def test_run_en_modo_manual_no_inyecta(
        self, agente_simulado,
    ):
        # Por defecto el agente_simulado tiene automatica=False.
        behaviour = _construir_behaviour(agente_simulado)
        await behaviour.on_start()
        await behaviour.run()
        assert behaviour.send.await_count == 0

    @pytest.mark.asyncio
    async def test_round_robin_recorre_los_grupos(
        self, agente_simulado,
    ):
        # Activar modo automático y reducir el catálogo a una clave
        # para que el escenario sea predecible.
        agente_simulado.config_supervisor["inyeccion"]["automatica"] = True
        behaviour = _construir_behaviour(agente_simulado)
        await behaviour.on_start()

        await behaviour.run()
        await behaviour.run()
        # Dos disparos: dos mensajes, uno a cada grupo.
        destinatarios = [
            llamada.args[0].to
            for llamada in behaviour.send.await_args_list
        ]
        assert set(destinatarios) == {
            "centralita_fenix@localhost",
            "centralita_olivar42@localhost",
        }

    @pytest.mark.asyncio
    async def test_run_sin_grupos_no_inyecta(
        self, agente_simulado,
    ):
        agente_simulado.grupos = []
        agente_simulado.config_supervisor["inyeccion"]["automatica"] = True
        behaviour = _construir_behaviour(agente_simulado)
        await behaviour.on_start()
        await behaviour.run()
        assert behaviour.send.await_count == 0
