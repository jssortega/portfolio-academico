"""Hito 1 — *Disponibilidad continuada* (escenario 8).

Tras un lote de 10 peticiones secuenciales, la Centralita debe
seguir respondiendo con normalidad y sin degradación apreciable
de latencia atribuible a fugas de recursos. El plan
(plan de pruebas de la rama del profesor) clasifica este escenario
como de integración: aunque está en la frontera con despliegue,
puede ejecutarse contra cualquier sistema arrancado.

Prueba de **caja negra contra el sistema real** del grupo.
"""

from __future__ import annotations

import time
from uuid import uuid4

import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask
from cliente_pruebas.cliente import ClienteCoordinador


# Número de peticiones del lote. El plan exige al menos 10.
NUMERO_PETICIONES = 10

# Factor de degradación tolerable entre la primera y la última
# petición. Un valor 3.0 admite que la décima tarde hasta el triple
# que la primera (margen amplio porque el LLM introduce variabilidad
# natural). Si la implementación tiene una fuga de recursos clara,
# la última petición será sustancialmente más lenta y se superará
# este margen.
FACTOR_DEGRADACION_MAXIMA = 3.0


@pytest.mark.integration
@pytest.mark.hito_1
class TestDisponibilidadContinuada:
    """Un lote de peticiones secuenciales no degrada al servicio."""

    @pytest.mark.asyncio
    async def test_diez_peticiones_secuenciales_completan_sin_caida(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
    ) -> None:
        """Las diez peticiones del lote terminan en `completed`."""
        estados: list[EstadoTask] = []
        for indice in range(NUMERO_PETICIONES):
            id_emergencia = uuid4()
            identificador_task = f"task-h1-lote-{indice:02d}-{id_emergencia.hex[:8]}"
            alerta = AlertaEmergencia(
                id_emergencia=id_emergencia,
                texto=f"Incendio número {indice} en almacén con humo denso.",
            )
            respuesta = await cliente_coordinador.enviar_alerta(
                url_centralita=url_centralita,
                alerta=alerta,
                identificador_task=identificador_task,
            )
            estados.append(respuesta.estado)

        completadas = sum(1 for estado in estados if estado is EstadoTask.COMPLETED)
        assert completadas == NUMERO_PETICIONES, (
            f"Solo {completadas}/{NUMERO_PETICIONES} peticiones terminaron en completed: "
            f"{[estado.value for estado in estados]}"
        )

    @pytest.mark.asyncio
    async def test_la_latencia_no_se_degrada_de_forma_notable_a_lo_largo_del_lote(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
    ) -> None:
        """La última petición no debe tardar más de tres veces que la primera."""
        latencias_segundos: list[float] = []
        for indice in range(NUMERO_PETICIONES):
            id_emergencia = uuid4()
            identificador_task = f"task-h1-degr-{indice:02d}-{id_emergencia.hex[:8]}"
            alerta = AlertaEmergencia(
                id_emergencia=id_emergencia,
                texto=f"Incendio número {indice} con clasificación trivial.",
            )
            instante_inicio = time.monotonic()
            respuesta = await cliente_coordinador.enviar_alerta(
                url_centralita=url_centralita,
                alerta=alerta,
                identificador_task=identificador_task,
            )
            instante_fin = time.monotonic()
            assert respuesta.estado is EstadoTask.COMPLETED
            latencias_segundos.append(instante_fin - instante_inicio)

        primera = latencias_segundos[0]
        ultima = latencias_segundos[-1]
        # Solo aplicamos la cota si la primera latencia es
        # significativa (≥ 100 ms); si fue casi instantánea, la
        # comparación relativa sería ruido puro.
        if primera >= 0.1:
            cota = primera * FACTOR_DEGRADACION_MAXIMA
            assert ultima <= cota, (
                f"Degradación de latencia atribuible a posible fuga: "
                f"primera={primera:.3f}s, última={ultima:.3f}s, "
                f"cota tolerada={cota:.3f}s, lote completo="
                f"{[round(valor, 3) for valor in latencias_segundos]}"
            )
