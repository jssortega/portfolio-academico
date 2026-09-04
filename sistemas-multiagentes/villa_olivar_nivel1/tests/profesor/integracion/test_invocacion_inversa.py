"""Hito 5 — *Invocación inversa entrante* (escenario 12).

En modalidad B (cooperación entre grupos), el sistema del grupo
evaluado expone sus especialistas públicos para que cualquier
otro grupo del aula pueda invocarlos a través del protocolo A2A.
La prueba verifica el caso simétrico al envío habitual: el
coordinador del profesor actúa como si fuera **un grupo externo**
e invoca directamente al especialista público del grupo evaluado
(no a la Centralita), comprobando que el especialista atiende la
petición con normalidad y devuelve un informe ajustado al
contrato.

La URL del especialista la aporta el grupo mediante la variable
de entorno ``URL_BOMBEROS_PUBLICOS``. Sin ella, la prueba se
omite porque no toda configuración expone bomberos como público y
forzar su existencia condicionaría las decisiones de diseño del
grupo.

Prueba de **caja negra contra el sistema real** del grupo.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask, RolEspecialista
from cliente_pruebas.cliente import ClienteCoordinador


# Identificador del "grupo externo" que el coordinador simula. El
# grupo evaluado debe registrarlo en el campo ``grupo_externo`` de
# al menos un ``EventoTraza`` para evidenciar que ha reconocido la
# procedencia externa de la petición.
ID_GRUPO_EXTERNO_SIMULADO = "grupo-externo-prueba"


@pytest.mark.integration
@pytest.mark.hito_5
class TestInvocacionInversa:
    """Un especialista público del grupo atiende peticiones de un grupo externo."""

    @pytest.mark.asyncio
    async def test_especialista_publico_responde_a_peticion_de_grupo_externo(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_especialista_publico_bomberos: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """El bomberos público acepta una alerta directa y devuelve su informe."""
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Apoyo requerido para incendio que excede la capacidad del "
                "grupo solicitante; se requiere intervención de bomberos "
                "del grupo externo."
            ),
            coordinacion=[ID_GRUPO_EXTERNO_SIMULADO],
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_especialista_publico_bomberos,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.estado is EstadoTask.COMPLETED
        assert respuesta.informe is not None
        roles_intervinientes = {
            item.rol for item in respuesta.informe.informes_especialistas
        }
        assert RolEspecialista.BOMBEROS in roles_intervinientes

    @pytest.mark.asyncio
    async def test_la_traza_documenta_la_procedencia_externa_de_la_peticion(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_especialista_publico_bomberos: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Al menos un evento de la traza debe marcar el ``grupo_externo``."""
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Solicitud de apoyo entre grupos vecinos para incendio "
                "extenso que supera capacidad propia."
            ),
            coordinacion=[ID_GRUPO_EXTERNO_SIMULADO],
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_especialista_publico_bomberos,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.informe is not None
        eventos_con_grupo_externo = [
            evento for evento in respuesta.informe.traza_participacion
            if evento.grupo_externo == ID_GRUPO_EXTERNO_SIMULADO
        ]
        assert len(eventos_con_grupo_externo) >= 1, (
            f"La traza debe contener al menos un evento con "
            f"grupo_externo={ID_GRUPO_EXTERNO_SIMULADO!r} para evidenciar "
            "que el grupo ha reconocido la procedencia externa."
        )
