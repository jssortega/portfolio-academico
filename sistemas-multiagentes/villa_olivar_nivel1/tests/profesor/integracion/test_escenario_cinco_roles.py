"""Hito 3 — *Escenario integral de los cinco roles* (escenario 3).

Verifica el caso más exigente del Hito 3: una alerta compuesta que
obliga a la Centralita a coordinar a los cuatro especialistas y
devolver un ``InformeResolucion`` con presencia de cada uno de
ellos en ``informes_especialistas`` y, complementariamente, de la
Centralita en la ``traza_participacion``.

Complementariamente cubre el escenario 4 del Hito 3 (sólo dos
roles cuando la alerta no requiere los cuatro) y el escenario 7
(coherencia entre clasificación y envío).

Prueba de **caja negra contra el sistema real** del grupo.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask, RolEspecialista
from contrato.traza import RolAgente
from cliente_pruebas.cliente import ClienteCoordinador


@pytest.mark.integration
@pytest.mark.hito_3
class TestEscenarioCincoRoles:
    """El informe documenta a los cinco roles cuando la alerta lo exige."""

    @pytest.mark.asyncio
    async def test_alerta_integral_devuelve_los_cuatro_especialistas_y_la_centralita(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Un escenario compuesto activa los cuatro especialistas.

        El texto describe simultáneamente derrumbe, incendio, fuga
        química, heridos y necesidad de corte de tráfico, de modo
        que cualquier criterio razonable de la Centralita debe
        convocar a los cuatro roles.
        """
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Derrumbe parcial de un edificio en el casco histórico con "
                "personas atrapadas y heridos, incendio activo en planta baja, "
                "fuga química procedente del cuadro eléctrico, y necesidad "
                "inmediata de corte de tráfico y acordonamiento del entorno."
            ),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.estado is EstadoTask.COMPLETED
        assert respuesta.informe is not None
        roles_intervinientes = {
            item.rol for item in respuesta.informe.informes_especialistas
        }
        cuatro_roles_esperados = {
            RolEspecialista.BOMBEROS,
            RolEspecialista.SANITARIO,
            RolEspecialista.POLICIA,
            RolEspecialista.MUNICIPAL,
        }
        assert roles_intervinientes == cuatro_roles_esperados, (
            f"El escenario compuesto debe convocar a los cuatro especialistas; "
            f"se obtuvieron {sorted(rol.value for rol in roles_intervinientes)}."
        )
        # La Centralita debe figurar al menos una vez en la traza.
        roles_en_traza = {evento.rol for evento in respuesta.informe.traza_participacion}
        assert RolAgente.CENTRALITA in roles_en_traza

    @pytest.mark.asyncio
    async def test_alerta_con_dos_roles_no_invoca_a_los_otros_dos(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Un robo con herido debe convocar sanitario y policía, no bomberos ni municipal."""
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Robo violento en establecimiento con un dependiente herido "
                "leve por un objeto contundente. Sin fuego, sin riesgo "
                "estructural y sin necesidad de actuación municipal."
            ),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.estado is EstadoTask.COMPLETED
        assert respuesta.informe is not None
        roles_intervinientes = {
            item.rol for item in respuesta.informe.informes_especialistas
        }
        assert RolEspecialista.POLICIA in roles_intervinientes
        assert RolEspecialista.SANITARIO in roles_intervinientes
        assert RolEspecialista.BOMBEROS not in roles_intervinientes
        assert RolEspecialista.MUNICIPAL not in roles_intervinientes
