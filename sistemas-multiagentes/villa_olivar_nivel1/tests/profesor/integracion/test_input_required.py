"""Hito 4 — *Estado ``input-required`` ante datos incompletos* (escenario 7).

Verifica el flujo de petición de datos faltantes definido por el
protocolo A2A: una alerta sin información esencial provoca que la
Centralita devuelva la Task en estado ``input-required`` con un
mensaje que solicita el dato; un segundo ``tasks/send`` que aporta
el complemento devuelve la Task ya ``completed``.

Prueba de **caja negra contra el sistema real** del grupo. La
alerta inicial omite la ``ubicacion``, un dato considerado
esencial por el contrato del Hito 4 cuando el escenario lo
requiere para el envío de unidades. Si la implementación del
grupo decide no exigir ubicación, la prueba puede fallar: en ese
caso, el grupo debe documentar su criterio y la prueba puede
omitirse según política docente.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from contrato.alerta_emergencia import AlertaEmergencia, Ubicacion
from contrato.tipos import EstadoTask
from cliente_pruebas.cliente import ClienteCoordinador


@pytest.mark.integration
@pytest.mark.hito_4
class TestInputRequired:
    """La Task pide datos faltantes y los acepta en una segunda llamada."""

    @pytest.mark.asyncio
    async def test_alerta_sin_ubicacion_obtiene_input_required_y_luego_completa(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Sin ubicación, la Task pide el dato; con la ubicación, completa."""
        alerta_incompleta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Necesario despliegue de bomberos en lugar no especificado "
                "para incendio sin más datos."
            ),
        )
        respuesta_inicial = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta_incompleta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta_inicial.estado is EstadoTask.INPUT_REQUIRED, (
            "Una alerta sin ubicación cuando se requiere despliegue debería "
            "obtener input-required, no "
            f"{respuesta_inicial.estado.value}."
        )

        # Reenviar la Task con la ubicación añadida.
        alerta_completa = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=alerta_incompleta.texto,
            ubicacion=Ubicacion(direccion="C/ Mayor 12, Jaén"),
        )
        respuesta_final = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta_completa,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta_final.estado is EstadoTask.COMPLETED, (
            "Tras aportar la ubicación, la Task debe completar; "
            f"estado obtenido: {respuesta_final.estado.value}."
        )
        assert respuesta_final.informe is not None
