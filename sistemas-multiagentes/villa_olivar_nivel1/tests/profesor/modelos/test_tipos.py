"""Pruebas unitarias de los tipos enumerados del contrato.

Verifican que los conjuntos cerrados de valores admitidos por el
contrato son los esperados y que las representaciones textuales
coinciden con las que se publicarán en el `InformeResolucion` y en
las habilidades de las Agent Cards.

Estas pruebas son íntegramente de caja blanca sobre el código del
profesor: validan los valores del propio contrato, no la
implementación de ningún grupo.
"""

import pytest

from contrato.tipos import (
    EstadoFinal,
    EstadoTask,
    Prioridad,
    RolEspecialista,
    TipoEmergencia,
)


@pytest.mark.hito_1
class TestTipoEmergencia:
    """Pruebas del enumerado `TipoEmergencia`."""

    def test_contiene_las_cinco_categorias_principales_y_otro(self) -> None:
        """El conjunto cerrado debe incluir las cinco categorías principales y `OTRO`."""
        valores_esperados = {
            "incendio",
            "accidente_trafico",
            "derrame_quimico",
            "inundacion",
            "derrumbe",
            "otro",
        }
        valores_encontrados = {tipo.value for tipo in TipoEmergencia}
        assert valores_encontrados == valores_esperados

    def test_acepta_la_representacion_textual_canonica(self) -> None:
        """`TipoEmergencia("incendio")` debe devolver el valor enumerado correspondiente."""
        tipo = TipoEmergencia("incendio")
        assert tipo is TipoEmergencia.INCENDIO

    def test_rechaza_un_valor_no_listado(self) -> None:
        """Un valor textual no contemplado debe lanzar `ValueError`."""
        with pytest.raises(ValueError):
            TipoEmergencia("terremoto")


@pytest.mark.hito_1
class TestPrioridad:
    """Pruebas del enumerado `Prioridad`."""

    def test_contiene_los_cuatro_niveles(self) -> None:
        """El contrato fija exactamente cuatro niveles de prioridad."""
        valores_encontrados = {nivel.value for nivel in Prioridad}
        assert valores_encontrados == {"baja", "media", "alta", "critica"}


@pytest.mark.hito_2
class TestRolEspecialista:
    """Pruebas del enumerado `RolEspecialista`."""

    def test_contiene_los_cuatro_roles_funcionales(self) -> None:
        """El sistema reconoce cuatro roles especialistas, sin contar la Centralita.

        Los valores textuales coinciden con el catálogo del registro REST
        (`doc/registro_rest_para_clientes.md`): en particular `municipal`
        es el identificador canónico del rol de Servicios Municipales.
        """
        valores_encontrados = {rol.value for rol in RolEspecialista}
        assert valores_encontrados == {
            "bomberos",
            "sanitario",
            "policia",
            "municipal",
        }


@pytest.mark.hito_4
class TestEstadoTask:
    """Pruebas del enumerado `EstadoTask`."""

    def test_admite_el_guion_en_input_required(self) -> None:
        """El estado `input-required` se representa con guion conforme al protocolo A2A."""
        estado = EstadoTask("input-required")
        assert estado is EstadoTask.INPUT_REQUIRED

    def test_contiene_todos_los_estados_del_ciclo_de_vida(self) -> None:
        """El conjunto cerrado contempla los seis estados posibles del ciclo A2A."""
        valores_encontrados = {estado.value for estado in EstadoTask}
        assert valores_encontrados == {
            "submitted",
            "working",
            "input-required",
            "completed",
            "failed",
            "canceled",
        }


@pytest.mark.hito_3
class TestEstadoFinal:
    """Pruebas del enumerado `EstadoFinal`."""

    def test_distingue_resolucion_completa_parcial_y_no_resuelta(self) -> None:
        """El desenlace agregado tiene tres categorías diferenciadas."""
        valores_encontrados = {estado.value for estado in EstadoFinal}
        assert valores_encontrados == {"resuelta", "parcial", "no_resuelta"}
