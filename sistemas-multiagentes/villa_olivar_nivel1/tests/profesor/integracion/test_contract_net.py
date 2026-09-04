"""Hito 4 — *Trazabilidad de la cadena Contract Net* (escenario 11).

El protocolo Contract Net (CNP, *Contract Net Protocol*) que el
grupo emplea para asignar internamente subtareas a los
especialistas no forma parte del contrato externo: ni el CFP
(*Call For Proposals*) ni las propuestas individuales se exponen
al coordinador del profesor. Lo que sí se expone, y por tanto
puede verificarse en caja negra, es la **evidencia agregada** de
que se ha producido una negociación.

Esta evidencia se materializa en la ``traza_participacion`` del
``InformeResolucion``: cuando el grupo organiza la asignación
mediante CNP, la traza debe incluir, además de los eventos
``intervenir_*`` de los especialistas seleccionados, eventos
intermedios que documenten la convocatoria (``convocar_cnp``),
la recepción de propuestas (``recibir_propuesta``) y la
asignación (``asignar_subtarea``).

Prueba de **caja negra contra el sistema real** del grupo.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask
from cliente_pruebas.cliente import ClienteCoordinador


# Acciones que evidencian la negociación CNP en la traza.
ACCIONES_CNP_REQUERIDAS = {
    "convocar_cnp",
    "asignar_subtarea",
}


@pytest.mark.integration
@pytest.mark.hito_4
class TestContractNet:
    """La traza del informe documenta la cadena CFP-propuesta-asignación."""

    @pytest.mark.asyncio
    async def test_traza_incluye_eventos_de_convocatoria_y_asignacion_cnp(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Una alerta resuelta mediante CNP deja eventos de convocatoria y asignación.

        El texto describe un escenario en el que el rol de bomberos
        admite varias dotaciones candidatas, lo que justifica una
        convocatoria CNP entre ellas.
        """
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Incendio extenso en almacén que requiere coordinación entre "
                "varias dotaciones de bomberos; debe seleccionarse la más "
                "adecuada en función de capacidad y proximidad."
            ),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.estado is EstadoTask.COMPLETED
        assert respuesta.informe is not None
        acciones = {evento.accion for evento in respuesta.informe.traza_participacion}
        acciones_faltantes = ACCIONES_CNP_REQUERIDAS - acciones
        assert not acciones_faltantes, (
            "La traza no documenta la negociación CNP. "
            f"Acciones esperadas no encontradas: {sorted(acciones_faltantes)}. "
            f"Acciones observadas: {sorted(acciones)}."
        )

    @pytest.mark.asyncio
    async def test_la_traza_se_mantiene_ordenada_cronologicamente(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Los instantes de los eventos de la traza son monótonamente crecientes."""
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto="Incendio en almacén con dotación única.",
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.informe is not None
        instantes = [evento.instante for evento in respuesta.informe.traza_participacion]
        instantes_ordenados = sorted(instantes)
        assert instantes == instantes_ordenados, (
            "La traza de participación debe respetar el orden cronológico."
        )
