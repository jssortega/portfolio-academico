"""Hito 5 — *Sin cooperación cuando no hace falta* (escenario 10).

Un escenario íntegramente resoluble con agentes del propio grupo
(modalidad A) no debe generar tráfico al registro central. La
prueba arranca un **doble del registro REST** que cuenta accesos
y exige al grupo evaluado apuntar a ese doble; tras una alerta
intra-grupo, el contador del doble debe permanecer en cero.

Como en ``test_cooperacion_grupo_simulado.py``, la verificación
exige que el grupo arranque su sistema apuntando al doble del
registro (no se puede hacer desde el coordinador sin permisos
sobre el proceso del grupo). Por eso la prueba se omite salvo
que el grupo confirme la configuración exportando la variable
``URL_REGISTRO_DOBLADO_EN_GRUPO``.

Prueba de **caja negra contra el sistema real** del grupo.
"""

from __future__ import annotations

import os
from uuid import UUID

import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask
from cliente_pruebas.cliente import ClienteCoordinador
from tests.profesor.integracion.conftest import DobleServicio, RegistroDeAccesos


NOMBRE_VARIABLE_REGISTRO_DOBLADO = "URL_REGISTRO_DOBLADO_EN_GRUPO"


def _omitir_si_no_hay_registro_doblado() -> None:
    if not os.environ.get(NOMBRE_VARIABLE_REGISTRO_DOBLADO):
        pytest.skip(
            f"Para verificar la ausencia de tráfico al registro el grupo "
            f"debe arrancar apuntando al doble y exportar "
            f"{NOMBRE_VARIABLE_REGISTRO_DOBLADO}=true.",
        )


@pytest.mark.integration
@pytest.mark.hito_5
class TestModalidadASinTraficoRegistro:
    """Un escenario intra-grupo no genera tráfico al registro central."""

    @pytest.mark.asyncio
    async def test_alerta_intragrupo_no_consulta_get_agentes(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        registro_central_instrumentado: tuple[DobleServicio, RegistroDeAccesos],
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Tras resolver un escenario A, el contador del doble no registra consultas."""
        _omitir_si_no_hay_registro_doblado()
        _, accesos = registro_central_instrumentado

        # Captura del contador previo para descontar el ruido del
        # alta/señales de vida que el sistema pudiera estar
        # emitiendo periódicamente.
        consultas_previas = accesos.consultas_get_agentes

        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Pequeño incendio en contenedor sin víctimas, resoluble "
                "íntegramente con los recursos del propio grupo."
            ),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )
        assert respuesta.estado is EstadoTask.COMPLETED

        consultas_durante = accesos.consultas_get_agentes - consultas_previas
        assert consultas_durante == 0, (
            "Un escenario intra-grupo no debe generar consultas al "
            f"registro central; se observaron {consultas_durante}."
        )
