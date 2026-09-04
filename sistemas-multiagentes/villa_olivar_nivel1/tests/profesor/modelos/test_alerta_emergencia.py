"""Pruebas unitarias del modelo `AlertaEmergencia`.

Cubren los escenarios 1, 2, 3 y 6 del Hito 1 descritos en
`doc/HITOS_EVALUACION.md`, así como los casos no triviales 2 y 5
del inventario de `doc/PLAN_PRUEBAS.md` § 3.7.2 (caracteres
especiales y campos extra ignorados silenciosamente). Incluyen
también las pruebas de los campos `id_emergencia`, `hito_evaluado`
y `coordinacion` que el coordinador del profesor utiliza para
correlacionar la inyección con un hito y para señalar los
escenarios colaborativos.

Son pruebas de caja blanca sobre el código del profesor: validan el
modelo Pydantic propio, no la implementación de ningún grupo.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from contrato.alerta_emergencia import AlertaEmergencia, Ubicacion


# Identificador estable para usar en varias pruebas. Cuando una prueba
# necesite varios ids distintos, los genera con `uuid4()`.
ID_EMERGENCIA_FIJO = UUID("2efae4fb-ef5e-5920-989d-957b9a511bff")


@pytest.mark.hito_1
class TestAlertaEmergencia:
    """Pruebas del modelo `AlertaEmergencia`."""

    def test_admite_id_y_texto_como_unicos_campos_obligatorios(self) -> None:
        """Una alerta minimalista es válida con `id_emergencia` y `texto` suficiente."""
        alerta = AlertaEmergencia(
            id_emergencia=ID_EMERGENCIA_FIJO,
            texto="Incendio detectado en la calle Olivos 12",
        )
        assert alerta.id_emergencia == ID_EMERGENCIA_FIJO
        assert alerta.texto.startswith("Incendio")
        assert alerta.ubicacion is None
        assert alerta.momento is None
        assert alerta.hito_evaluado is None
        assert alerta.coordinacion == []

    def test_acepta_todos_los_campos_opcionales_juntos(self) -> None:
        """Una alerta enriquecida con todos los campos opcionales es válida."""
        alerta = AlertaEmergencia(
            id_emergencia=uuid4(),
            texto="Accidente de tráfico con dos heridos",
            ubicacion=Ubicacion(
                direccion="Avenida Principal, 5",
                latitud=37.78,
                longitud=-3.78,
            ),
            momento=datetime(2026, 5, 10, 12, 30, tzinfo=timezone.utc),
            informador="vecino_anonimo",
            hito_evaluado="H3-E5",
            coordinacion=["g1-fenix", "g3-quercus"],
        )
        assert alerta.ubicacion is not None
        assert alerta.ubicacion.latitud == pytest.approx(37.78)
        assert alerta.informador == "vecino_anonimo"
        assert alerta.hito_evaluado == "H3-E5"
        assert alerta.coordinacion == ["g1-fenix", "g3-quercus"]

    def test_rechaza_alerta_sin_id_de_emergencia(self) -> None:
        """`id_emergencia` es obligatorio: el correlador no puede faltar."""
        with pytest.raises(ValidationError):
            AlertaEmergencia.model_validate({"texto": "Inundación en el sótano"})

    def test_rechaza_id_de_emergencia_que_no_es_uuid(self) -> None:
        """Una cadena cualquiera no es un UUID válido."""
        with pytest.raises(ValidationError):
            AlertaEmergencia.model_validate(
                {
                    "id_emergencia": "no-es-un-uuid",
                    "texto": "Incidente con humo en el portal",
                }
            )

    def test_rechaza_texto_demasiado_corto(self) -> None:
        """Un texto vacío o de un único carácter no es procesable."""
        with pytest.raises(ValidationError):
            AlertaEmergencia(id_emergencia=ID_EMERGENCIA_FIJO, texto="")

    def test_ignora_silenciosamente_los_campos_extra(self) -> None:
        """Los campos no contemplados en el contrato se descartan sin error."""
        alerta = AlertaEmergencia.model_validate(
            {
                "id_emergencia": str(ID_EMERGENCIA_FIJO),
                "texto": "Inundación en el sótano del edificio municipal",
                "campo_no_contemplado": "valor cualquiera",
                "otro_extra": 42,
            }
        )
        assert alerta.texto.startswith("Inundación")
        assert not hasattr(alerta, "campo_no_contemplado")

    def test_admite_texto_con_caracteres_especiales(self) -> None:
        """Emojis, comillas tipográficas y tildes se procesan como texto literal."""
        texto = "Incidente «grave» con humo 🔥 en la planta n.º 3"
        alerta = AlertaEmergencia(id_emergencia=ID_EMERGENCIA_FIJO, texto=texto)
        assert alerta.texto == texto

    def test_rechaza_latitud_fuera_de_rango(self) -> None:
        """Una latitud por encima de 90 grados no es geográficamente válida."""
        with pytest.raises(ValidationError):
            Ubicacion(direccion="Ubicación inventada", latitud=120.0)

    def test_rechaza_longitud_fuera_de_rango(self) -> None:
        """Una longitud por debajo de -180 grados no es geográficamente válida."""
        with pytest.raises(ValidationError):
            Ubicacion(direccion="Ubicación inventada", longitud=-200.0)

    def test_se_serializa_y_se_recompone_sin_perdida(self) -> None:
        """La conversión a JSON y la validación inversa son idempotentes."""
        alerta_original = AlertaEmergencia(
            id_emergencia=ID_EMERGENCIA_FIJO,
            texto="Derrame químico en la calzada",
            ubicacion=Ubicacion(direccion="Polígono Industrial, nave 7"),
            hito_evaluado="H1-E2",
            coordinacion=["g4-laurel"],
        )
        cuerpo_json = alerta_original.model_dump(mode="json")
        alerta_recompuesta = AlertaEmergencia.model_validate(cuerpo_json)
        assert alerta_recompuesta == alerta_original

    def test_coordinacion_admite_varios_grupos_para_escenarios_colaborativos(self) -> None:
        """Un escenario colaborativo se reconoce por `coordinacion` con > 1 elemento."""
        alerta = AlertaEmergencia(
            id_emergencia=ID_EMERGENCIA_FIJO,
            texto="Incendio forestal extendido entre dos términos municipales",
            coordinacion=["g1-fenix", "g3-quercus", "g7-olivar"],
        )
        assert len(alerta.coordinacion) == 3
        assert "g1-fenix" in alerta.coordinacion

    def test_rechaza_hito_evaluado_vacio(self) -> None:
        """El código del hito, si se proporciona, no puede ser una cadena vacía."""
        with pytest.raises(ValidationError):
            AlertaEmergencia(
                id_emergencia=ID_EMERGENCIA_FIJO,
                texto="Inundación en el sótano",
                hito_evaluado="",
            )
