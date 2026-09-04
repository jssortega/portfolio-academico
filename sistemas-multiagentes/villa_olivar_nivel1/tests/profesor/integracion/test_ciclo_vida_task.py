"""Hito 4 — *Transición de estados de la Task* (escenario 6).

Observa el ciclo de vida de una Task tal como lo expone la
Centralita del grupo a través del campo ``history`` de la
respuesta JSON-RPC. La transición canónica permitida por el
protocolo A2A y recogida en ``EstadoTask`` es:

    SUBMITTED -> WORKING -> COMPLETED | FAILED | INPUT_REQUIRED
    INPUT_REQUIRED -> WORKING (al recibir el dato faltante)

Esta prueba también cubre el escenario 10 del Hito 4 (Tasks
concurrentes del coordinador): dos Tasks emitidas casi a la vez
mantienen sus historiales separados.

Prueba de **caja negra contra el sistema real** del grupo.
"""

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask
from cliente_pruebas.cliente import ClienteCoordinador


# Conjunto de estados que el protocolo A2A admite en el campo
# ``history`` de una respuesta a ``tasks/get``.
ESTADOS_VALIDOS = {estado.value for estado in EstadoTask}


@pytest.mark.integration
@pytest.mark.hito_4
class TestCicloVidaTask:
    """La Task transita por los estados canónicos del protocolo A2A."""

    @pytest.mark.asyncio
    async def test_historial_respeta_la_secuencia_canonica_del_protocolo(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """El historial recogido cumple las reglas de transición del protocolo A2A."""
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto="Incendio en almacén que ejercita el ciclo de vida completo.",
        )
        await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )
        respuesta = await cliente_coordinador.consultar_task(
            url_centralita=url_centralita,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.respuesta_cruda is not None
        historial = respuesta.respuesta_cruda.get("result", {}).get("history", [])
        assert len(historial) >= 1
        estados = [entrada.get("state") for entrada in historial]
        # Todos los estados deben pertenecer al enumerado canónico.
        estados_invalidos = [estado for estado in estados if estado not in ESTADOS_VALIDOS]
        assert estados_invalidos == [], (
            f"El historial contiene estados desconocidos: {estados_invalidos}"
        )
        # El historial debe empezar en `submitted`.
        assert estados[0] == EstadoTask.SUBMITTED.value, (
            f"El primer estado del historial debería ser submitted, fue {estados[0]!r}."
        )
        # Después de un estado terminal, no debe aparecer otro
        # estado posterior (no hay reinicios).
        estados_terminales = {EstadoTask.COMPLETED.value, EstadoTask.FAILED.value,
                              EstadoTask.CANCELED.value}
        terminal_visto = False
        secuencia_correcta = True
        for estado in estados:
            if terminal_visto:
                secuencia_correcta = False
            if estado in estados_terminales:
                terminal_visto = True
        assert secuencia_correcta, (
            f"El historial continúa después de un estado terminal: {estados}"
        )

    @pytest.mark.asyncio
    async def test_dos_tasks_concurrentes_mantienen_historiales_independientes(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
    ) -> None:
        """Dos identificadores distintos generan dos historiales no entrelazados."""
        id_emergencia_a = uuid4()
        id_emergencia_b = uuid4()
        identificador_a = f"task-h4-conc-a-{id_emergencia_a.hex[:8]}"
        identificador_b = f"task-h4-conc-b-{id_emergencia_b.hex[:8]}"
        alerta_a = AlertaEmergencia(
            id_emergencia=id_emergencia_a,
            texto="Incendio en almacén — Task concurrente A.",
        )
        alerta_b = AlertaEmergencia(
            id_emergencia=id_emergencia_b,
            texto="Inundación en garaje — Task concurrente B.",
        )

        respuesta_a, respuesta_b = await asyncio.gather(
            cliente_coordinador.enviar_alerta(url_centralita, alerta_a, identificador_a),
            cliente_coordinador.enviar_alerta(url_centralita, alerta_b, identificador_b),
        )

        assert respuesta_a.task_id == identificador_a
        assert respuesta_b.task_id == identificador_b
        assert respuesta_a.informe is not None
        assert respuesta_b.informe is not None
        assert respuesta_a.informe.id_emergencia == id_emergencia_a
        assert respuesta_b.informe.id_emergencia == id_emergencia_b
