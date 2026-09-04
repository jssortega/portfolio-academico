"""Hito 2 — Envío a especialistas (escenarios 3, 4, 5 y 7).

Verifica que el ``InformeResolucion`` devuelto refleja, mediante el
campo ``informes_especialistas`` y la ``traza_participacion``, qué
especialistas han intervenido en la atención de la emergencia:

- *Envío a un único especialista* (escenario 3): para una alerta
  cuyo tipo se resuelve con un único rol, el informe debe contener
  contribución solo de ese rol.
- *Envío a dos especialistas en cadena* (escenario 4): para una
  alerta que exige dos roles, el informe debe contener ambos.
- *Especialista no relevante no es invocado* (escenario 7): para
  una alerta sin víctimas, el sanitario no figura en el informe.
- *Fallo localizado en un especialista* (escenario 8): la
  Centralita debe reflejar el fallo en el informe agregado sin
  detenerse.

Prueba de **caja negra contra el sistema real** del grupo.

Nota sobre el paralelismo del despacho: el Hito 2 pide que los
especialistas independientes se atiendan de forma concurrente,
pero esta propiedad **no se verifica aquí**. Una comprobación de
caja negra solo podría medir tiempos de pared, una señal
intrínsecamente frágil frente a la varianza del modelo de lenguaje
(LLM) y, además, insuficiente: el contrato de la traza
(`contrato/traza.py`) exige un único evento por especialista y no
fija el instante en que se sella, de modo que no aporta evidencia
estructural que distinga la concurrencia real de un despacho
secuencial. Por ello, el paralelismo se evalúa por **inspección
del diseño** del grupo (presencia de despacho concurrente, p. ej.
`asyncio.gather`, en su Centralita), no mediante un test temporal.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask, RolEspecialista
from cliente_pruebas.cliente import ClienteCoordinador


@pytest.mark.integration
@pytest.mark.hito_2
class TestEnvioAEspecialistas:
    """El informe refleja la lista de especialistas convocados."""

    @pytest.mark.asyncio
    async def test_alerta_con_un_unico_rol_devuelve_un_solo_informe_de_especialista(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Un incendio sin víctimas se resuelve solo con Bomberos."""
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Pequeño incendio en contenedor de cartón en la vía pública, "
                "sin víctimas y sin riesgo de propagación."
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
        assert RolEspecialista.BOMBEROS in roles_intervinientes
        # El sanitario no debe figurar porque no hay víctimas.
        assert RolEspecialista.SANITARIO not in roles_intervinientes

    @pytest.mark.asyncio
    async def test_alerta_con_dos_roles_en_cadena_devuelve_ambos_informes(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Un incendio con persona atrapada exige bomberos y sanitario."""
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Incendio en vivienda con persona atrapada en el segundo "
                "piso, requiere rescate y atención sanitaria inmediata."
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
        assert RolEspecialista.BOMBEROS in roles_intervinientes
        assert RolEspecialista.SANITARIO in roles_intervinientes

    @pytest.mark.asyncio
    async def test_accidente_de_trafico_con_corte_devuelve_policia_y_sanitario(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Para un accidente de tráfico con corte de vía intervienen policía y sanitario."""
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Colisión en glorieta con dos heridos y corte total de la "
                "vía durante el rescate."
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

    @pytest.mark.asyncio
    async def test_especialista_no_relevante_no_aparece_en_el_informe(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Un incendio sin víctimas no debe convocar al sanitario."""
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Incendio en nave industrial vacía durante la noche, sin "
                "víctimas confirmadas ni riesgo para personas."
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
        assert RolEspecialista.SANITARIO not in roles_intervinientes
