"""Hito 1 — *Variedad de tipos de emergencia* (escenario 3).

Repite el flujo ``tasks/send`` con alertas cuyo texto contiene
indicios inequívocos del tipo de emergencia y verifica que la
Centralita las clasifica en la categoría esperada.

Prueba de **caja negra contra el sistema real**. La parametrización
usa textos suficientemente explícitos como para que un clasificador
basado en LLM razonable acierte: si el grupo falla aquí, su
clasificador necesita revisión.

También cubre el escenario 6 del Hito 1 (entradas degeneradas):
una alerta con texto ilegible debe terminar la Task en estado
``failed`` con un mensaje descriptivo, sin que la Centralita
quede en un estado intermedio.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask, TipoEmergencia
from cliente_pruebas.cliente import ClienteCoordinador


# Catálogo de pares (texto, tipo_esperado) que se inyectan en la
# prueba parametrizada. Cada texto es deliberadamente unívoco para
# que cualquier clasificador razonable acierte.
CASOS_CLASIFICACION: list[tuple[str, TipoEmergencia]] = [
    ("Incendio en almacén con humo denso y llamas visibles.", TipoEmergencia.INCENDIO),
    (
        "Colisión múltiple en la A-44 con heridos atrapados en los vehículos.",
        TipoEmergencia.ACCIDENTE_TRAFICO,
    ),
    (
        "Derrame de hidrocarburos en zona industrial sur con vapores tóxicos.",
        TipoEmergencia.DERRAME_QUIMICO,
    ),
    (
        "Inundación severa en bajos del polígono tras tormenta torrencial.",
        TipoEmergencia.INUNDACION,
    ),
    (
        "Derrumbe parcial de edificación abandonada en el casco antiguo.",
        TipoEmergencia.DERRUMBE,
    ),
]


@pytest.mark.integration
@pytest.mark.hito_1
class TestClasificacionEmergencias:
    """La Centralita clasifica cada alerta en su categoría esperada."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("texto", "tipo_esperado"), CASOS_CLASIFICACION)
    async def test_clasificacion_devuelta_coincide_con_la_categoria_esperada(
        self,
        texto: str,
        tipo_esperado: TipoEmergencia,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
    ) -> None:
        """Para cada texto, el informe llega con el tipo esperado."""
        id_emergencia = uuid4()
        identificador_task = f"task-h1-clasif-{tipo_esperado.value}-{id_emergencia.hex[:8]}"
        alerta = AlertaEmergencia(id_emergencia=id_emergencia, texto=texto)

        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task,
        )

        assert respuesta.estado is EstadoTask.COMPLETED, (
            f"La Task no completó: estado={respuesta.estado}, "
            f"mensaje={respuesta.mensaje_error!r}"
        )
        assert respuesta.informe is not None
        assert respuesta.informe.tipo_emergencia is tipo_esperado, (
            f"Clasificación incorrecta: texto={texto!r}, "
            f"esperado={tipo_esperado.value}, "
            f"obtenido={respuesta.informe.tipo_emergencia.value}"
        )

    @pytest.mark.asyncio
    async def test_entrada_degenerada_produce_task_failed_con_mensaje(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Un texto que la Centralita no consigue interpretar se cierra como `failed`.

        Tras el fallo, la Centralita debe quedar en estado operativo
        para atender peticiones posteriores. La presente prueba se
        limita a verificar la primera mitad de la propiedad
        (estado ``failed`` con mensaje no vacío); la disponibilidad
        continuada se verifica en pruebas separadas.
        """
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto="???",
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.estado is EstadoTask.FAILED, (
            "Una alerta ilegible debería cerrar la Task como failed, "
            f"no como {respuesta.estado}."
        )
        assert respuesta.informe is None
        assert respuesta.mensaje_error is not None
        assert len(respuesta.mensaje_error) > 0
