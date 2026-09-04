"""Pruebas unitarias del modelo `InformeActuacion`.

Cubren la validación del informe parcial que cada especialista
devuelve a la Centralita. Se asocian al Hito 2 (despacho a un
especialista) y al Hito 4 (compatibilidad con el coordinador del
profesor) según `doc/HITOS_EVALUACION.md`.
"""

import pytest
from pydantic import ValidationError

from contrato.informe_actuacion import InformeActuacion
from contrato.tipos import RolEspecialista


@pytest.mark.hito_2
class TestInformeActuacion:
    """Pruebas del modelo `InformeActuacion`."""

    def test_admite_un_informe_minimo_con_solo_rol_y_completado(self) -> None:
        """Un informe sin acciones ni recursos sigue siendo válido."""
        informe = InformeActuacion(rol=RolEspecialista.BOMBEROS, completado=True)
        assert informe.rol is RolEspecialista.BOMBEROS
        assert informe.acciones_realizadas == []
        assert informe.recursos_empleados == []

    def test_admite_listas_completas_de_acciones_y_recursos(self) -> None:
        """Un informe enriquecido se valida y conserva el orden original."""
        informe = InformeActuacion(
            rol=RolEspecialista.SANITARIO,
            completado=True,
            acciones_realizadas=["triage", "estabilización", "traslado"],
            recursos_empleados=["uvi_movil_1", "ambulancia_2"],
            observaciones="Dos heridos leves trasladados al hospital comarcal.",
        )
        assert informe.acciones_realizadas == ["triage", "estabilización", "traslado"]
        assert informe.recursos_empleados[0] == "uvi_movil_1"

    def test_rechaza_un_rol_que_no_pertenece_al_conjunto_cerrado(self) -> None:
        """Un rol inventado debe ser rechazado por la validación."""
        with pytest.raises(ValidationError):
            InformeActuacion.model_validate(
                {"rol": "guardia_civil", "completado": True},
            )

    def test_admite_un_informe_con_acciones_pero_no_completado(self) -> None:
        """Un especialista puede informar de acciones parciales con `completado=False`."""
        informe = InformeActuacion(
            rol=RolEspecialista.POLICIA,
            completado=False,
            acciones_realizadas=["perímetro establecido"],
            observaciones="A la espera de refuerzos antes de continuar.",
        )
        assert informe.completado is False
        assert informe.observaciones is not None

    def test_ignora_silenciosamente_los_campos_extra(self) -> None:
        """Un informe con campos no contemplados se valida sin error."""
        informe = InformeActuacion.model_validate(
            {
                "rol": "municipal",
                "completado": True,
                "campo_extra_grupo": "información interna del grupo",
            },
        )
        assert informe.rol is RolEspecialista.MUNICIPAL
