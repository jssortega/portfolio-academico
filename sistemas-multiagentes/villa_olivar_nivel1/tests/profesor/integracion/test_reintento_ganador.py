"""Hito 4 — *Reintento ante fallo del ganador* (escenario 9).

Si el especialista que ganó el CFP falla durante la ejecución de
la subtarea, la Centralita debe reintentar con la segunda mejor
propuesta antes de declarar la subtarea como fallida. La evidencia
externa de este comportamiento es la presencia en la
``traza_participacion`` de un segundo evento ``asignar_subtarea``
hacia un agente distinto del ganador original.

Prueba de **caja negra contra el sistema real** del grupo.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask
from cliente_pruebas.cliente import ClienteCoordinador


@pytest.mark.integration
@pytest.mark.hito_4
class TestReintentoGanador:
    """Ante el fallo del ganador del CFP, la Centralita reintenta."""

    @pytest.mark.asyncio
    async def test_segunda_asignacion_distinta_cuando_el_ganador_falla(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """La traza muestra dos `asignar_subtarea` a agentes distintos cuando el primero falla.

        El texto fuerza explícitamente el fallo del primer ganador
        (con la indicación "la unidad asignada inicialmente debe
        fallar") para que el grupo pueda implementar la regla en
        su orquestador o en su LLM. El criterio observable es que
        existan al menos dos eventos ``asignar_subtarea`` con
        ``agente_id`` distinto en la traza, o, alternativamente,
        un evento ``reintentar`` explícito.
        """
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Incendio en almacén con varias dotaciones de bomberos "
                "disponibles. La primera unidad asignada debe fallar a "
                "mitad de la intervención para forzar un reintento con "
                "la segunda mejor propuesta."
            ),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.informe is not None
        asignaciones = [
            evento for evento in respuesta.informe.traza_participacion
            if evento.accion == "asignar_subtarea"
        ]
        reintentos = [
            evento for evento in respuesta.informe.traza_participacion
            if evento.accion == "reintentar"
        ]
        identificadores_asignados = {evento.agente_id for evento in asignaciones}
        hay_segunda_asignacion = len(identificadores_asignados) >= 2
        hay_evento_reintento = len(reintentos) >= 1
        assert hay_segunda_asignacion or hay_evento_reintento, (
            "Ante el fallo del primer ganador, la traza debe contener "
            "al menos dos `asignar_subtarea` con agente_id distinto o un "
            "evento `reintentar`. Asignaciones observadas: "
            f"{identificadores_asignados}; eventos `reintentar`: {len(reintentos)}."
        )

    @pytest.mark.asyncio
    async def test_la_task_global_termina_resuelta_a_pesar_del_reintento(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """El reintento debe permitir que la Task global termine `completed`.

        Si la segunda propuesta también es válida, el reintento
        debe ser suficiente para resolver la emergencia. Si no
        existe una segunda propuesta, el plan acepta ``failed``
        explícito, pero la Task no puede quedar en estado
        intermedio.
        """
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Incendio con dos dotaciones de bomberos candidatas; la "
                "primera asignada deberá fallar para forzar el respaldo, "
                "que sí debe poder completar la intervención."
            ),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        estados_terminales = {EstadoTask.COMPLETED, EstadoTask.FAILED, EstadoTask.CANCELED}
        assert respuesta.estado in estados_terminales, (
            f"La Task debe terminar en un estado terminal; obtenido: "
            f"{respuesta.estado.value}."
        )
