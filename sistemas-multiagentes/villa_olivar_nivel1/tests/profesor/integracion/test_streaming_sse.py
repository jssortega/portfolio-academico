"""Hito 6 — *Transmisión continua SSE en Tasks largas* (escenario 3).

Una Task abierta con ``tasks/sendSubscribe`` debe emitir eventos
intermedios (``working`` con artefactos parciales) durante el
procesado, no solo el evento final ``completed``. La prueba abre
la suscripción, recolecta los eventos recibidos y verifica que:

1. Aparece al menos un evento intermedio con estado ``working``
   antes del cierre.
2. La transmisión termina con un evento ``completed`` (o ``failed``
   si la Task no puede resolverse).
3. Cada evento intermedio cumple el esquema mínimo: incluye un
   campo ``status.state`` con un valor del enumerado
   ``EstadoTask``.

La transmisión continua es una capacidad **opcional** del Hito 6: si
el sistema no implementa ``tasks/sendSubscribe``, el servidor A2A
responde con un error JSON-RPC ``-32601`` y código HTTP 404. En ese
caso la prueba se **omite**, porque no es obligatoria para aprobar; no
se trata como un fallo.

Prueba de **caja negra contra el sistema real** del grupo.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask
from cliente_pruebas.cliente import ClienteCoordinador


# Estados que el plan considera intermedios (no terminales) dentro
# de una transmisión continua.
ESTADOS_INTERMEDIOS = {EstadoTask.WORKING.value, EstadoTask.INPUT_REQUIRED.value}

# Estados que dan por cerrada la transmisión continua.
ESTADOS_TERMINALES = {
    EstadoTask.COMPLETED.value,
    EstadoTask.FAILED.value,
    EstadoTask.CANCELED.value,
}

# Código HTTP con el que el servidor A2A señala que un método JSON-RPC
# no está soportado. La factoría lo emite, junto al error ``-32601``,
# cuando el grupo no implementa ``tasks/sendSubscribe`` (capacidad
# opcional del Hito 6).
CODIGO_HTTP_METODO_NO_SOPORTADO = 404


async def _recolectar_eventos_hasta_terminal(
    cliente_coordinador: ClienteCoordinador,
    url_centralita: str,
    alerta: AlertaEmergencia,
    identificador_task: str,
) -> list[dict[str, Any]]:
    """Abre la transmisión continua y devuelve sus eventos hasta el terminal.

    Los eventos se acumulan hasta el primer estado terminal inclusive; una vez
    alcanzado, se cierra la transmisión sin consumir el resto (sin recurrir a
    ``break``, mediante una variable de control booleana).

    Si el sistema no implementa ``tasks/sendSubscribe``, el servidor responde
    con código HTTP 404 (error JSON-RPC ``-32601``) y la prueba se **omite**:
    la transmisión continua es opcional en el Hito 6. Cualquier otro error HTTP
    se propaga como fallo real.
    """
    eventos: list[dict[str, Any]] = []
    transmision = cliente_coordinador.enviar_alerta_streaming(
        url_centralita=url_centralita,
        alerta=alerta,
        identificador_task=identificador_task,
    )
    iterador = transmision.__aiter__()
    try:
        terminal_alcanzado = False
        while not terminal_alcanzado:
            try:
                evento = await iterador.__anext__()
            except StopAsyncIteration:
                # La transmisión se cerró sin más eventos: fin natural.
                terminal_alcanzado = True
            else:
                eventos.append(evento)
                estado = evento.get("result", {}).get("status", {}).get("state")
                terminal_alcanzado = estado in ESTADOS_TERMINALES
    except httpx.HTTPStatusError as error:
        if error.response.status_code == CODIGO_HTTP_METODO_NO_SOPORTADO:
            pytest.skip(
                "El sistema no implementa `tasks/sendSubscribe` (transmisión "
                "continua SSE), capacidad opcional del Hito 6; la prueba se omite."
            )
        raise
    finally:
        await transmision.aclose()
    return eventos


@pytest.mark.integration
@pytest.mark.hito_6
class TestStreamingSse:
    """`tasks/sendSubscribe` emite eventos intermedios y un evento terminal."""

    @pytest.mark.asyncio
    async def test_aparece_al_menos_un_evento_working_antes_del_terminal(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """La transmisión incluye eventos `working` durante la atención."""
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Escenario integral de varios especialistas que tarda "
                "lo bastante como para emitir varios eventos intermedios "
                "de progreso."
            ),
        )
        eventos = await _recolectar_eventos_hasta_terminal(
            cliente_coordinador=cliente_coordinador,
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )
        estados_observados = [
            evento.get("result", {}).get("status", {}).get("state")
            for evento in eventos
            if evento.get("result", {}).get("status", {}).get("state") is not None
        ]
        intermedios = [estado for estado in estados_observados if estado in ESTADOS_INTERMEDIOS]
        terminales = [estado for estado in estados_observados if estado in ESTADOS_TERMINALES]
        assert len(intermedios) >= 1, (
            "La transmisión continua no entregó ningún evento intermedio "
            f"(working / input-required); estados observados: {estados_observados}."
        )
        assert len(terminales) >= 1, (
            "La transmisión continua no entregó un evento terminal; "
            f"estados observados: {estados_observados}."
        )

    @pytest.mark.asyncio
    async def test_los_eventos_intermedios_cumplen_el_esquema_minimo(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Cada evento intermedio lleva `status.state` con un valor válido del enumerado."""
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto="Escenario para verificar el esquema de los eventos SSE intermedios.",
        )
        valores_validos = {estado.value for estado in EstadoTask}
        eventos = await _recolectar_eventos_hasta_terminal(
            cliente_coordinador=cliente_coordinador,
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )
        for evento in eventos:
            estado = evento.get("result", {}).get("status", {}).get("state")
            assert estado in valores_validos, (
                f"Evento SSE con estado desconocido: {estado!r}; "
                f"valores admitidos: {valores_validos}."
            )
