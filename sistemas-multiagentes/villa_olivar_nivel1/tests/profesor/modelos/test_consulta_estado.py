"""Pruebas unitarias de `ConsultaEstado`.

Modelo del cuerpo del Protocolo 2 (sondeo de estado) que el
coordinador del profesor envía a cualquiera de los tres agentes
públicos del grupo.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from contrato.consulta_estado import OPERACION_CONSULTAR_ESTADO, ConsultaEstado


@pytest.mark.hito_2
class TestConsultaEstado:
    """Pruebas del modelo `ConsultaEstado`."""

    def test_admite_un_cuerpo_practicamente_vacio(self) -> None:
        """Un cuerpo sin campos toma el valor por defecto de `operacion`."""
        consulta = ConsultaEstado()
        assert consulta.operacion == OPERACION_CONSULTAR_ESTADO
        assert consulta.rol_destino is None
        assert consulta.momento is None

    def test_acepta_rol_destino_y_momento(self) -> None:
        """Los campos opcionales se conservan tras la validación."""
        consulta = ConsultaEstado(
            rol_destino="bomberos",
            momento=datetime(2026, 5, 30, 17, 32, 50, tzinfo=timezone.utc),
        )
        assert consulta.rol_destino == "bomberos"
        assert consulta.momento is not None

    def test_ignora_silenciosamente_los_campos_extra(self) -> None:
        """Los campos no contemplados se descartan sin error."""
        consulta = ConsultaEstado.model_validate(
            {
                "operacion": OPERACION_CONSULTAR_ESTADO,
                "campo_no_contemplado": "valor cualquiera",
            },
        )
        assert consulta.operacion == OPERACION_CONSULTAR_ESTADO

    def test_rechaza_momento_invalido(self) -> None:
        """Una marca temporal mal formada debe rechazarse."""
        with pytest.raises(ValidationError):
            ConsultaEstado.model_validate({"momento": "no-es-una-fecha"})
