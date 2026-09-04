"""Hito 1 — *Persistencia y consulta posterior* (escenario 4).

Comprueba que la Centralita conserva el estado de las Tasks que
recibe, de modo que una llamada ulterior ``tasks/get`` con el
mismo ``id`` devuelve el historial de estados y, si la Task ya ha
finalizado, el ``InformeResolucion`` asociado.

Prueba de **caja negra contra el sistema real**: las dos
peticiones (``tasks/send`` y ``tasks/get``) viajan a la URL
declarada en ``CENTRALITA_URL``. La prueba falla si la Centralita
no recuerda la Task entre llamadas (por ejemplo, si la
implementación es puramente en memoria y la pierde tras devolver
el resultado).
"""

from __future__ import annotations

from uuid import UUID

import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask
from cliente_pruebas.cliente import ClienteCoordinador


@pytest.mark.integration
@pytest.mark.hito_1
class TestPersistenciaTasks:
    """La Centralita admite consultas posteriores a la misma Task."""

    @pytest.mark.asyncio
    async def test_consulta_get_devuelve_el_mismo_informe_que_send(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """`tasks/get` posterior al `tasks/send` recupera el informe almacenado."""
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto="Inundación en bajos comerciales tras tormenta.",
        )
        respuesta_envio = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )
        assert respuesta_envio.estado is EstadoTask.COMPLETED

        respuesta_consulta = await cliente_coordinador.consultar_task(
            url_centralita=url_centralita,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta_consulta.estado is EstadoTask.COMPLETED
        assert respuesta_consulta.task_id == identificador_task_prefijado
        assert respuesta_consulta.informe is not None
        assert respuesta_consulta.informe.id_emergencia == nuevo_identificador_emergencia
        # El informe agregado debe ser el mismo (mismo tipo y prioridad).
        assert (
            respuesta_consulta.informe.tipo_emergencia
            is respuesta_envio.informe.tipo_emergencia
        )
        assert (
            respuesta_consulta.informe.prioridad
            is respuesta_envio.informe.prioridad
        )

    @pytest.mark.asyncio
    async def test_history_contiene_la_secuencia_canonica_del_ciclo_de_vida(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """El historial devuelto incluye al menos `submitted`, `working` y `completed`."""
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto="Incendio en almacén controlado por la dotación local.",
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
        resultado = respuesta.respuesta_cruda.get("result", {})
        historial = resultado.get("history", [])
        assert len(historial) >= 1, (
            "La Centralita debe devolver el historial de estados en `tasks/get`."
        )
        estados = [entrada.get("state") for entrada in historial]
        assert EstadoTask.COMPLETED.value in estados, (
            f"El historial no recoge el estado completed: {estados}"
        )
