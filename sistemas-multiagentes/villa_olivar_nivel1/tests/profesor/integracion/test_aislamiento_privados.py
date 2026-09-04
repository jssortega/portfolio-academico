"""Hito 3 — *Aislamiento de los agentes privados* (escenario 2).

Verifica dos propiedades complementarias del aislamiento de los
agentes con rol privado:

1. **No alcanzabilidad directa**: una petición A2A dirigida a una
   URL que el grupo declara como privada debe fallar (404, 403,
   conexión rechazada o tiempo de espera agotado). La URL la
   aporta el grupo a través de la variable de entorno
   ``URL_PRIVADO_PROHIBIDO``; sin ella, esta verificación se
   omite porque no se puede comprobar sin acceder al código del
   grupo.

2. **Evidencia en la traza**: cuando una alerta canalizada por la
   Centralita pública requiere a un agente privado, el
   ``InformeResolucion`` debe contener al menos un evento con
   ``visibilidad: "privado"`` en la traza de participación. Esta
   es la única forma en que un privado deja constancia frente al
   coordinador externo.

Prueba de **caja negra contra el sistema real** del grupo.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import httpx
import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.traza import VisibilidadAgente
from cliente_pruebas.cliente import ClienteCoordinador


@pytest.mark.integration
@pytest.mark.hito_3
class TestAislamientoPrivados:
    """Los privados no son alcanzables desde fuera del grupo."""

    @pytest.mark.asyncio
    async def test_invocacion_directa_a_privado_no_es_alcanzable(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_agente_privado_prohibido: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """La URL declarada como privada debe rechazar peticiones externas.

        Se considera aislamiento correcto cualquiera de los
        siguientes: 404 (no encontrada), 403 (prohibida), conexión
        rechazada o tiempo de espera agotado.
        """
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto="Alerta de prueba dirigida directamente a un privado.",
        )
        with pytest.raises((httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException)):
            respuesta = await cliente_coordinador.enviar_alerta(
                url_centralita=url_agente_privado_prohibido,
                alerta=alerta,
                identificador_task=identificador_task_prefijado,
            )
            # Si la petición no lanzó, exigimos al menos que el
            # estado devuelto no sea completed (el privado nunca
            # debería atender una invocación externa con éxito).
            from contrato.tipos import EstadoTask
            assert respuesta.estado is not EstadoTask.COMPLETED, (
                "El privado completó una petición externa: aislamiento incorrecto."
            )

    @pytest.mark.asyncio
    async def test_traza_documenta_la_intervencion_privada_a_traves_de_la_centralita(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
    ) -> None:
        """Una alerta que requiere a un privado deja un evento `privado` en la traza.

        El grupo debe declarar al menos un agente privado en su
        ``AGENTES_A2A.md``. La prueba envía una alerta cuya
        atención típicamente requiere a uno de los privados
        (servicios municipales) y verifica que el informe contiene
        al menos un evento con visibilidad privada. Si el grupo
        decide hacer públicos a los cuatro especialistas, esta
        prueba fallará: el contrato del Hito 3 exige exactamente
        dos privados.
        """
        id_emergencia = uuid4()
        identificador_task = f"task-h3-privado-{id_emergencia.hex[:8]}"
        alerta = AlertaEmergencia(
            id_emergencia=id_emergencia,
            texto=(
                "Inundación en bajos del polígono que requiere coordinación "
                "con servicios municipales para retirada de mobiliario urbano "
                "y restitución del alumbrado público."
            ),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task,
        )

        assert respuesta.informe is not None, (
            f"La Task no devolvió informe; estado={respuesta.estado}."
        )
        visibilidades = {evento.visibilidad for evento in respuesta.informe.traza_participacion}
        assert VisibilidadAgente.PRIVADO in visibilidades, (
            "La traza no contiene ningún evento con visibilidad privada. "
            "El grupo debe declarar al menos dos especialistas privados (Hito 3)."
        )
