"""Pruebas unitarias del modelo `EventoTraza` y sus enumerados.

La traza de participación es el principal artefacto de evidencia
que el coordinador del profesor cruza con los criterios de
`doc/HITOS_EVALUACION.md` para decidir si una inyección supera o
no el hito asociado. Estas pruebas verifican que el modelo
Pydantic admite los eventos válidos y rechaza los malformados.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from contrato.traza import EventoTraza, RolAgente, VisibilidadAgente


INSTANTE_FIJO = datetime(2026, 5, 30, 17, 32, 12, 450000, tzinfo=timezone.utc)


@pytest.mark.hito_3
class TestEventoTraza:
    """Pruebas del modelo `EventoTraza`."""

    def test_admite_un_evento_completo_de_un_publico(self) -> None:
        """Un evento intra-grupo con los seis campos obligatorios es válido."""
        evento = EventoTraza(
            instante=INSTANTE_FIJO,
            agente_id="centralita_fenix",
            rol=RolAgente.CENTRALITA,
            visibilidad=VisibilidadAgente.PUBLICO,
            accion="recibir_alerta",
            detalle="AlertaEmergencia recibida vía A2A; id_emergencia=2efae4fb",
        )
        assert evento.rol is RolAgente.CENTRALITA
        assert evento.visibilidad is VisibilidadAgente.PUBLICO
        assert evento.grupo_externo is None

    def test_admite_un_evento_de_un_privado(self) -> None:
        """Un evento con `visibilidad = privado` es válido y documentable."""
        evento = EventoTraza(
            instante=INSTANTE_FIJO,
            agente_id="policia_fenix",
            rol=RolAgente.POLICIA,
            visibilidad=VisibilidadAgente.PRIVADO,
            accion="establecer_perimetro",
            detalle="Calle Mayor cortada al tráfico en ambos sentidos",
        )
        assert evento.visibilidad is VisibilidadAgente.PRIVADO

    def test_admite_grupo_externo_en_escenarios_colaborativos(self) -> None:
        """Un evento de coordinación inter-grupo lleva `grupo_externo`."""
        evento = EventoTraza(
            instante=INSTANTE_FIJO,
            agente_id="centralita_fenix",
            rol=RolAgente.CENTRALITA,
            visibilidad=VisibilidadAgente.PUBLICO,
            accion="coordinar_con_grupo",
            detalle="Solicita refuerzos a centralita_quercus",
            grupo_externo="g3-quercus",
        )
        assert evento.grupo_externo == "g3-quercus"

    def test_rechaza_accion_con_mayusculas(self) -> None:
        """El identificador de la acción debe ir en `snake_case` para permitir agregación."""
        with pytest.raises(ValidationError):
            EventoTraza(
                instante=INSTANTE_FIJO,
                agente_id="centralita_fenix",
                rol=RolAgente.CENTRALITA,
                visibilidad=VisibilidadAgente.PUBLICO,
                accion="RecibirAlerta",
                detalle="ok",
            )

    def test_rechaza_accion_con_espacios(self) -> None:
        """El identificador de la acción no admite espacios."""
        with pytest.raises(ValidationError):
            EventoTraza(
                instante=INSTANTE_FIJO,
                agente_id="centralita_fenix",
                rol=RolAgente.CENTRALITA,
                visibilidad=VisibilidadAgente.PUBLICO,
                accion="recibir alerta",
                detalle="ok",
            )

    def test_rechaza_detalle_vacio(self) -> None:
        """El detalle textual no puede ser una cadena vacía."""
        with pytest.raises(ValidationError):
            EventoTraza(
                instante=INSTANTE_FIJO,
                agente_id="centralita_fenix",
                rol=RolAgente.CENTRALITA,
                visibilidad=VisibilidadAgente.PUBLICO,
                accion="recibir_alerta",
                detalle="",
            )

    def test_rechaza_visibilidad_inventada(self) -> None:
        """Un valor de visibilidad fuera de `publico` o `privado` debe rechazarse."""
        with pytest.raises(ValidationError):
            EventoTraza.model_validate(
                {
                    "instante": INSTANTE_FIJO.isoformat(),
                    "agente_id": "centralita_fenix",
                    "rol": "centralita",
                    "visibilidad": "semipublico",
                    "accion": "recibir_alerta",
                    "detalle": "ok",
                },
            )


@pytest.mark.hito_3
class TestRolAgente:
    """Pruebas del enumerado `RolAgente`."""

    def test_incluye_centralita_y_los_cuatro_especialistas(self) -> None:
        """`RolAgente` extiende a `RolEspecialista` añadiendo la Centralita."""
        valores = {rol.value for rol in RolAgente}
        assert valores == {
            "centralita",
            "bomberos",
            "sanitario",
            "policia",
            "municipal",
        }


@pytest.mark.hito_3
class TestVisibilidadAgente:
    """Pruebas del enumerado `VisibilidadAgente`."""

    def test_contiene_solo_publico_y_privado(self) -> None:
        """El eje de visibilidad es binario."""
        valores = {visibilidad.value for visibilidad in VisibilidadAgente}
        assert valores == {"publico", "privado"}
