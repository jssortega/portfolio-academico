"""Hito 1 — *Procesado de una alerta sencilla* (escenario 2).

Verifica el camino más básico del contrato externo: la Centralita
del grupo acepta una ``AlertaEmergencia`` enviada por el
coordinador del profesor mediante ``tasks/send`` y devuelve una
Task en estado ``completed`` con un ``InformeResolucion`` coherente.

Prueba de **caja negra contra el sistema real** del grupo: las
peticiones viajan por HTTP a la URL declarada en la variable de
entorno ``CENTRALITA_URL``. Mientras el grupo no haya arrancado
su sistema, la prueba fallará con ``httpx.ConnectError`` o
expirará por tiempo de espera. Ese fallo es la señal esperada
antes de tener una primera implementación funcional.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from contrato.alerta_emergencia import AlertaEmergencia, Ubicacion
from contrato.tipos import EstadoTask, TipoEmergencia
from cliente_pruebas.cliente import ClienteCoordinador


@pytest.mark.integration
@pytest.mark.hito_1
class TestCentralitaResponde:
    """La Centralita acepta una alerta básica y devuelve un informe."""

    @pytest.mark.asyncio
    async def test_envio_simple_completa_la_task_con_informe(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Envía un texto de incendio simple y verifica `Task.completed`.

        El informe devuelto debe correlacionarse con la alerta
        original (mismo ``id_emergencia``) y contener al menos un
        evento en la traza de participación.
        """
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto="Incendio en almacén de la calle Mayor con humo denso.",
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.estado is EstadoTask.COMPLETED, (
            f"La Task no completó: estado={respuesta.estado}, "
            f"mensaje={respuesta.mensaje_error!r}"
        )
        assert respuesta.task_id == identificador_task_prefijado
        assert respuesta.informe is not None, (
            "La Task terminó completed pero no se localizó el InformeResolucion "
            "en la respuesta."
        )
        assert respuesta.informe.id_emergencia == nuevo_identificador_emergencia
        assert len(respuesta.informe.traza_participacion) >= 1

    @pytest.mark.asyncio
    async def test_alerta_con_ubicacion_completa_la_task(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Una alerta con ubicación textual mínima también se procesa."""
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto="Incendio en cocina con propagación al salón.",
            ubicacion=Ubicacion(direccion="C/ Mayor 12, Jaén"),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.estado is EstadoTask.COMPLETED
        assert respuesta.informe is not None
        assert respuesta.informe.tipo_emergencia is TipoEmergencia.INCENDIO
