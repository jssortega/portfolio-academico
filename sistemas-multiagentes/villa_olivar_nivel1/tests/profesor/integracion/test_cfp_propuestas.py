"""Hito 4 — *Contract Net: propuestas y notificación* (escenarios 1, 3 y 4).

Verifica la evidencia agregada de una convocatoria CNP completa
en la ``traza_participacion`` del ``InformeResolucion``:

- **E1**: para una subtarea con varias unidades posibles, la
  Centralita emite un CFP y recibe al menos dos propuestas. Cada
  propuesta deja un evento ``recibir_propuesta`` en la traza con
  un identificador distinto en ``agente_id``.
- **E3**: el especialista ganador recibe la subtarea
  (``intervenir_*``) y el perdedor recibe una notificación de no
  asignación (``notificar_no_asignacion``).
- **E4**: para escenarios donde dos roles distintos pueden cubrir
  la misma subtarea, las propuestas comparables proceden de
  agentes con ``rol`` distinto y la asignación final escoge solo
  uno de los dos.

Prueba de **caja negra contra el sistema real** del grupo.
"""

from __future__ import annotations

from collections import Counter
from uuid import UUID

import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask
from cliente_pruebas.cliente import ClienteCoordinador


@pytest.mark.integration
@pytest.mark.hito_4
class TestCfpPropuestas:
    """La traza recoge propuestas y notificaciones del Contract Net."""

    @pytest.mark.asyncio
    async def test_cfp_recibe_al_menos_dos_propuestas_distintas(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """La Centralita recibe al menos dos propuestas para la misma subtarea (E1).

        El texto describe una intervención donde, según el plan de
        evaluación, varias unidades del mismo rol podrían
        responder; el evento ``recibir_propuesta`` debe aparecer
        al menos dos veces con ``agente_id`` distinto.
        """
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Incendio extenso en almacén que puede asignarse a "
                "cualquiera de las dotaciones de bomberos disponibles. "
                "Se requiere selección por capacidad."
            ),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.estado is EstadoTask.COMPLETED
        assert respuesta.informe is not None
        propuestas = [
            evento for evento in respuesta.informe.traza_participacion
            if evento.accion == "recibir_propuesta"
        ]
        assert len(propuestas) >= 2, (
            "La traza debe documentar al menos dos propuestas (`recibir_propuesta`) "
            f"para una subtarea con varias unidades posibles; se observaron "
            f"{len(propuestas)}."
        )
        identificadores_proponentes = {evento.agente_id for evento in propuestas}
        assert len(identificadores_proponentes) >= 2, (
            "Las propuestas deben proceder de agentes distintos: "
            f"observados {identificadores_proponentes}."
        )

    @pytest.mark.asyncio
    async def test_asignacion_y_notificacion_al_perdedor(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """El ganador recibe la subtarea y el perdedor recibe `notificar_no_asignacion` (E3)."""
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Intervención sanitaria asignable entre varias unidades "
                "disponibles; se requiere selección por proximidad."
            ),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.informe is not None
        acciones_contadas = Counter(
            evento.accion for evento in respuesta.informe.traza_participacion
        )
        assert acciones_contadas.get("asignar_subtarea", 0) >= 1, (
            f"La traza no contiene `asignar_subtarea`: {dict(acciones_contadas)}"
        )
        assert acciones_contadas.get("notificar_no_asignacion", 0) >= 1, (
            "La traza no contiene `notificar_no_asignacion` para los proponentes "
            f"no seleccionados: {dict(acciones_contadas)}"
        )

    @pytest.mark.asyncio
    async def test_cfp_entre_roles_distintos_escoge_solo_uno(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Cuando dos roles distintos podrían cubrir una subtarea, solo uno la asume (E4).

        Escenario inspirado en el plan: una víctima leve podría
        atenderla Sanitario o Servicios Municipales si hay médico
        de apoyo. La traza debe mostrar propuestas de roles
        distintos y una única asignación efectiva.
        """
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Víctima con malestar leve en evento municipal con "
                "personal sanitario de apoyo presente; la atención "
                "puede asumirla el especialista sanitario o los "
                "servicios municipales con apoyo médico."
            ),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.informe is not None
        propuestas = [
            evento for evento in respuesta.informe.traza_participacion
            if evento.accion == "recibir_propuesta"
        ]
        roles_proponentes = {evento.rol for evento in propuestas}
        assert len(roles_proponentes) >= 2, (
            "Las propuestas deben proceder de al menos dos roles distintos; "
            f"observados: {[rol.value for rol in roles_proponentes]}."
        )
        asignaciones = [
            evento for evento in respuesta.informe.traza_participacion
            if evento.accion == "asignar_subtarea"
        ]
        assert len(asignaciones) == 1, (
            "Cuando dos roles podían cubrir la misma subtarea, debe haber "
            f"exactamente una asignación efectiva; se observaron {len(asignaciones)}."
        )
