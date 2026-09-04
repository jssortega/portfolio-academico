"""Pruebas unitarias de `EstadoAgente`.

Modelo del cuerpo de la respuesta del Protocolo 2: cada agente
público devuelve su estado actual al coordinador del profesor
cuando recibe una `ConsultaEstado`.
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from contrato.estado_agente import EstadoAgente
from contrato.traza import RolAgente


@pytest.mark.hito_2
class TestEstadoAgente:
    """Pruebas del modelo `EstadoAgente`."""

    def test_admite_un_estado_minimo_con_solo_los_obligatorios(self) -> None:
        """Los tres campos obligatorios son suficientes para un estado válido."""
        estado = EstadoAgente(
            agente_id="bomberos_fenix",
            rol=RolAgente.BOMBEROS,
            estado="libre",
        )
        assert estado.agente_id == "bomberos_fenix"
        assert estado.emergencia_actual is None
        assert estado.detalle is None

    def test_admite_un_estado_ocupado_con_emergencia_actual(self) -> None:
        """Un estado `ocupado` puede llevar el id de la emergencia que atiende."""
        emergencia = UUID("2efae4fb-ef5e-5920-989d-957b9a511bff")
        estado = EstadoAgente(
            agente_id="bomberos_fenix",
            rol=RolAgente.BOMBEROS,
            estado="ocupado",
            emergencia_actual=emergencia,
            detalle="Unidad 2 desplazada al lugar del incendio.",
            momento=datetime.now(timezone.utc),
        )
        assert estado.emergencia_actual == emergencia
        assert estado.detalle is not None

    def test_admite_centralita_como_rol(self) -> None:
        """La Centralita también responde al sondeo y se identifica con su rol."""
        estado = EstadoAgente(
            agente_id="centralita_fenix",
            rol=RolAgente.CENTRALITA,
            estado="operativa",
        )
        assert estado.rol is RolAgente.CENTRALITA

    def test_rechaza_un_estado_vacio(self) -> None:
        """La cadena de `estado` no puede ser vacía."""
        with pytest.raises(ValidationError):
            EstadoAgente(
                agente_id="bomberos_fenix",
                rol=RolAgente.BOMBEROS,
                estado="",
            )

    def test_rechaza_emergencia_actual_no_uuid(self) -> None:
        """`emergencia_actual` debe ser un UUID válido."""
        with pytest.raises(ValidationError):
            EstadoAgente.model_validate(
                {
                    "agente_id": "bomberos_fenix",
                    "rol": "bomberos",
                    "estado": "ocupado",
                    "emergencia_actual": "no-es-uuid",
                },
            )

    def test_se_serializa_y_se_recompone_sin_perdida(self) -> None:
        """La conversión a JSON y la validación inversa son idempotentes."""
        original = EstadoAgente(
            agente_id="sanitario_fenix",
            rol=RolAgente.SANITARIO,
            estado="esperando_recurso",
            detalle="Esperando ambulancia de refuerzo (ETA 5 min)",
        )
        recompuesto = EstadoAgente.model_validate(original.model_dump(mode="json"))
        assert recompuesto == original
