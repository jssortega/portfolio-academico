# -*- coding: utf-8 -*-
"""
Tests de las enumeraciones de la ontología compartida.

Verifican que los enums tienen los valores documentados en el contrato y
que cada miembro mantiene su valor de cadena exacto. Estas pruebas son
defensa frente a renombres accidentales: si alguien cambia
`TipoEmergencia.INCENDIO = "incendio"` por otra cadena, el supervisor
del profesor (que valida los mensajes con JSON-Schema) rechazará todos
los informes del grupo y la integración silenciosamente fallará.
"""
from __future__ import annotations

import pytest

from ontologia.modelos_compartidos import (
    EstadoActuacion,
    Prioridad,
    TipoEmergencia,
)


# Valores canónicos según docs/ontologia/propuesta_tests_unitarios.md §4.1.
TIPOS_EMERGENCIA_ESPERADOS: tuple[str, ...] = (
    "incendio", "derrame_quimico", "accidente_trafico",
    "inundacion", "derrumbe", "otro",
)
PRIORIDADES_ESPERADAS: tuple[str, ...] = ("baja", "media", "alta", "critica")
ESTADOS_ESPERADOS: tuple[str, ...] = (
    "recibido", "en_camino", "en_escena", "actuando",
    "finalizado", "requiere_apoyo",
)


# ─── Catálogos completos ────────────────────────────────────────────────────

def test_tipo_emergencia_contiene_seis_valores_canonicos() -> None:
    valores = {miembro.value for miembro in TipoEmergencia}
    assert valores == set(TIPOS_EMERGENCIA_ESPERADOS)


def test_prioridad_contiene_cuatro_niveles() -> None:
    valores = {miembro.value for miembro in Prioridad}
    assert valores == set(PRIORIDADES_ESPERADAS)


def test_estado_actuacion_contiene_seis_estados() -> None:
    valores = {miembro.value for miembro in EstadoActuacion}
    assert valores == set(ESTADOS_ESPERADOS)


# ─── Comportamiento como str (heredan de str, Enum) ─────────────────────────

@pytest.mark.parametrize("miembro", list(TipoEmergencia))
def test_tipo_emergencia_serializa_como_string(miembro: TipoEmergencia) -> None:
    """Cada miembro de TipoEmergencia se comporta como su valor de cadena."""
    assert str(miembro.value) == miembro.value
    assert isinstance(miembro.value, str)


@pytest.mark.parametrize("cadena", TIPOS_EMERGENCIA_ESPERADOS)
def test_tipo_emergencia_se_construye_desde_string(cadena: str) -> None:
    """TipoEmergencia(cadena) reconstruye el miembro correspondiente."""
    miembro = TipoEmergencia(cadena)
    assert miembro.value == cadena


def test_prioridad_se_construye_desde_string_valida() -> None:
    assert Prioridad("critica") is Prioridad.CRITICA


def test_prioridad_invalida_lanza_value_error() -> None:
    with pytest.raises(ValueError):
        Prioridad("urgentisima")


def test_estado_actuacion_se_construye_desde_string_valida() -> None:
    assert EstadoActuacion("en_escena") is EstadoActuacion.EN_ESCENA


# ─── Idempotencia: nada de duplicados ───────────────────────────────────────

@pytest.mark.parametrize(
    "tipo_enum",
    [TipoEmergencia, Prioridad, EstadoActuacion],
)
def test_enums_no_tienen_valores_duplicados(tipo_enum: type) -> None:
    """Si dos miembros comparten el mismo valor, Pydantic no podría
    distinguirlos al deserializar. Verificamos que el catálogo es disjunto."""
    valores = [miembro.value for miembro in tipo_enum]
    assert len(valores) == len(set(valores))
