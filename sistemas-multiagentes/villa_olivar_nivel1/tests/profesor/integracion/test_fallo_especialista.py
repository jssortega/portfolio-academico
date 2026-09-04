"""Hito 2 / Hito 4 — *Fallo localizado de un especialista* (H2 E8, H4 E8).

Cuando un especialista convocado por la Centralita devuelve la
subtarea como ``failed``, la Centralita debe reflejarlo en el
``InformeResolucion`` (a través del campo ``completado: false`` del
``InformeActuacion`` del especialista y/o del ``estado_final:
"parcial"`` agregado) y continuar la atención con el resto, sin
quedar atrapada en un estado intermedio.

La prueba envía una alerta cuyo texto incluye una condición
deliberadamente conflictiva para uno de los roles (por ejemplo,
"sin recursos disponibles" o "fuera de cobertura"). El grupo es
libre de implementar el mecanismo concreto que provoque el fallo
del especialista (excepción simulada, regla en el LLM, etc.); el
contrato observable es: la Task global no se cuelga, el informe
documenta el fallo y la operación sigue.

Prueba de **caja negra contra el sistema real** del grupo.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoFinal, EstadoTask, RolEspecialista
from cliente_pruebas.cliente import ClienteCoordinador


@pytest.mark.integration
@pytest.mark.hito_2
@pytest.mark.hito_4
class TestFalloEspecialista:
    """La Centralita refleja el fallo de un especialista sin colgarse."""

    @pytest.mark.asyncio
    async def test_fallo_de_un_especialista_no_bloquea_la_task_global(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """La Task global termina en `completed` o `failed`, nunca en estado intermedio.

        El texto de la alerta exige a varios especialistas e incluye
        una condición que típicamente provocará el fallo de uno de
        ellos (recurso no disponible). Cualquier desenlace
        terminal del protocolo es válido; lo inaceptable es que la
        Task quede en estado ``working`` indefinidamente.
        """
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Incendio extenso con varios heridos graves; la unidad "
                "sanitaria más próxima está fuera de servicio y "
                "explícitamente NO debe poder responder. Las demás "
                "unidades sí actúan con normalidad."
            ),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        estados_terminales = {EstadoTask.COMPLETED, EstadoTask.FAILED, EstadoTask.CANCELED}
        assert respuesta.estado in estados_terminales, (
            f"La Task quedó en estado intermedio {respuesta.estado.value}; "
            "debería resolverse en un estado terminal."
        )

    @pytest.mark.asyncio
    async def test_informe_documenta_el_fallo_del_especialista_afectado(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """El informe agregado registra el fallo (`estado_final=parcial` o `completado=false`).

        Si la Task termina ``completed``, el informe debe declarar
        explícitamente el fallo del especialista afectado mediante
        uno de los dos mecanismos siguientes:

        1. ``estado_final = parcial``: el resultado agregado señala
           que no todos los especialistas pudieron completar.
        2. ``InformeActuacion.completado = false`` del especialista
           afectado: el especialista refleja su propia incidencia.

        Si la Task termina ``failed``, basta con que haya un mensaje
        de error descriptivo.
        """
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Accidente de tráfico con heridos graves; "
                "deliberadamente no hay unidad sanitaria disponible "
                "para forzar el fallo de su subtarea."
            ),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        if respuesta.estado is EstadoTask.COMPLETED:
            assert respuesta.informe is not None
            es_parcial = respuesta.informe.estado_final is EstadoFinal.PARCIAL
            hay_especialista_no_completado = any(
                informe.completado is False
                for informe in respuesta.informe.informes_especialistas
            )
            assert es_parcial or hay_especialista_no_completado, (
                "La Task terminó completed pero el informe no documenta el fallo "
                "ni con estado_final=parcial ni con InformeActuacion.completado=False."
            )
        else:
            # Task `failed` o `canceled`: basta con que haya un mensaje informativo.
            assert respuesta.mensaje_error is not None
            assert len(respuesta.mensaje_error) > 0
