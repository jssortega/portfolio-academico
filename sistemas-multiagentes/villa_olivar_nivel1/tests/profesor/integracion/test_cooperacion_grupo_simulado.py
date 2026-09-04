"""Hito 5 — *Cooperación con un grupo simulado y respaldo* (escenarios 8 y 9).

Estos tests arrancan **dobles A2A reales** del lado del coordinador
del profesor para fingir que existe un grupo vecino al que el
sistema del grupo evaluado puede delegar. La cooperación entre
grupos del Hito 5 se verifica en dos variantes:

- **E8 — Cooperación con grupo simulado**: el coordinador levanta un
  doble que finge ser un bomberos público de otro grupo. La
  Centralita del grupo evaluado, ante un escenario que requiere
  bomberos (su rol privado, supongamos), debe descubrir el doble
  y delegar la subtarea.
- **E9 — Indisponibilidad transitoria de la pareja externa**: el
  doble devuelve siempre ``500``; el sistema evaluado debe
  registrar el fallo, conmutar al respaldo o consignar la
  incidencia en el informe.

Las dos pruebas dependen de una **manipulación del registro REST**
del aula que el coordinador no puede ejecutar sin permisos. Por
eso se omiten salvo que el grupo evaluado haya arrancado su
sistema apuntando al doble del registro (variable
``REGISTRO_REST_URL`` apuntando al doble) y, dentro del doble, se
haya insertado el descriptor del grupo simulado. Para no
inflar la fixture con esa orquestación, las pruebas comprueban el
comportamiento observable suponiendo que el grupo ha configurado
correctamente el descubrimiento.

Prueba de **caja negra contra el sistema real** del grupo.
"""

from __future__ import annotations

import os
from uuid import UUID

import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask
from cliente_pruebas.cliente import ClienteCoordinador
from tests.profesor.integracion.conftest import DobleServicio


# Nombre de la variable de entorno que el grupo debe exportar antes
# de arrancar para apuntar al doble del registro proporcionado por
# el coordinador.
NOMBRE_VARIABLE_REGISTRO_DOBLADO = "URL_REGISTRO_DOBLADO_EN_GRUPO"


def _omitir_si_no_hay_registro_doblado() -> None:
    """Omite la prueba si el grupo no apunta al registro instrumentado."""
    if not os.environ.get(NOMBRE_VARIABLE_REGISTRO_DOBLADO):
        pytest.skip(
            f"Para ejercer la cooperación con grupo simulado, el grupo debe "
            f"arrancar su sistema apuntando al doble del registro y exportar "
            f"{NOMBRE_VARIABLE_REGISTRO_DOBLADO}=true para confirmar la "
            "configuración.",
        )


@pytest.mark.integration
@pytest.mark.hito_5
class TestCooperacionGrupoSimulado:
    """El sistema del grupo descubre y delega en un grupo externo simulado."""

    @pytest.mark.asyncio
    async def test_delegacion_efectiva_en_doble_de_grupo_externo(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        grupo_externo_simulado: DobleServicio,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Una alerta que necesita un rol externo se atiende a través del doble."""
        _omitir_si_no_hay_registro_doblado()
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Incendio extenso que excede la capacidad propia; se "
                "requiere apoyo del rol bomberos a través de otro grupo."
            ),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.estado is EstadoTask.COMPLETED
        assert respuesta.informe is not None
        eventos_externos = [
            evento for evento in respuesta.informe.traza_participacion
            if evento.grupo_externo is not None
        ]
        assert len(eventos_externos) >= 1, (
            "La traza debe contener al menos un evento con grupo_externo "
            "indicado, evidenciando la delegación al doble del grupo "
            f"simulado en {grupo_externo_simulado.url}."
        )

    @pytest.mark.asyncio
    async def test_indisponibilidad_de_la_pareja_externa_se_documenta_o_se_conmuta(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        grupo_externo_caido: DobleServicio,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Si el grupo externo elegido falla, el informe registra la incidencia (E9)."""
        _omitir_si_no_hay_registro_doblado()
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Escenario que requiere apoyo externo; el grupo "
                "candidato deliberadamente no responderá."
            ),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        estados_terminales = {EstadoTask.COMPLETED, EstadoTask.FAILED, EstadoTask.CANCELED}
        assert respuesta.estado in estados_terminales, (
            "La Task debe terminar en un estado terminal pese al fallo del "
            f"grupo externo; obtenido: {respuesta.estado.value}."
        )
        if respuesta.estado is EstadoTask.COMPLETED:
            assert respuesta.informe is not None
            acciones = {
                evento.accion for evento in respuesta.informe.traza_participacion
            }
            indicadores_de_incidencia = {
                "registrar_incidencia_externa",
                "conmutar_a_respaldo",
                "fallo_grupo_externo",
            }
            assert indicadores_de_incidencia & acciones, (
                "La traza debe documentar el fallo del grupo externo con "
                "alguna de las acciones convencionales "
                f"{indicadores_de_incidencia}; acciones observadas: {acciones}."
            )
