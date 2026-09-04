# -*- coding: utf-8 -*-
"""
Tests de interoperabilidad entre los modelos Pydantic y los JSON-Schemas.

`ontologia/esquema_supervisor.json` es la versión "exterior" del contrato
supervisor↔grupo: describe en JSON-Schema los cuatro mensajes que cruzan
la frontera. La fuente de verdad son los modelos Pydantic; el JSON-Schema
los duplica para que cualquier herramienta (no necesariamente Python)
pueda validar mensajes.

Estos tests verifican que las dos representaciones siguen alineadas:
si alguien cambia un Pydantic sin actualizar el JSON-Schema (o al revés),
los tests deben fallar para que el desfase no llegue a producción.

Dependencia: jsonschema. Si no está instalado, los tests se saltan con
un mensaje que indica cómo instalarlo.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from ontologia.modelos_compartidos import (
    ConsultaEstado,
    Coordenadas,
    DatosEmergencia,
    EstadoActuacion,
    EstadoAgente,
    InformeResolucion,
    Prioridad,
    TipoEmergencia,
    Ubicacion,
)


jsonschema = pytest.importorskip(
    "jsonschema",
    reason="instala jsonschema para los tests de interop: pip install jsonschema",
)


RUTA_ESQUEMA_SUPERVISOR: Path = (
    Path(__file__).resolve().parents[2]
    / "ontologia"
    / "esquema_supervisor.json"
)


@pytest.fixture(scope="module")
def esquema_supervisor() -> dict:
    """Carga el JSON-Schema una vez por módulo."""
    with open(RUTA_ESQUEMA_SUPERVISOR, "r", encoding="utf-8") as fichero:
        return json.load(fichero)


def _validar_contra_definicion(
    esquema: dict, definicion: str, instancia: dict
) -> None:
    """
    Valida `instancia` contra `esquema_supervisor.json#/definitions/{definicion}`.

    Las definiciones del JSON-Schema están bajo el bloque `definitions`;
    aquí construimos un sub-esquema que apunta a la rama concreta para
    validar sólo ese tipo de mensaje.
    """
    sub_esquema = {
        "$ref": "#/definitions/" + definicion,
        "definitions": esquema["definitions"],
    }
    jsonschema.validate(instance=instancia, schema=sub_esquema)


# ─── DatosEmergencia ↔ datos_emergencia ─────────────────────────────────────

def test_datos_emergencia_validan_contra_esquema(esquema_supervisor: dict) -> None:
    de = DatosEmergencia(
        id_emergencia="EM-001",
        tipo_emergencia=TipoEmergencia.INCENDIO,
        ubicacion=Ubicacion(direccion="C/ Real 12"),
        prioridad=Prioridad.ALTA,
        descripcion="Humo visible en planta segunda.",
    )
    instancia = json.loads(de.model_dump_json())
    _validar_contra_definicion(esquema_supervisor, "datos_emergencia", instancia)


def test_datos_emergencia_con_coordenadas_validan_contra_esquema(
    esquema_supervisor: dict,
) -> None:
    """`coordenadas` es opcional; cuando viaja debe validarse igualmente."""
    de = DatosEmergencia(
        id_emergencia="EM-002",
        tipo_emergencia=TipoEmergencia.INCENDIO,
        ubicacion=Ubicacion(
            direccion="Plaza Mayor 1",
            coordenadas=Coordenadas(latitud=37.78, longitud=-3.79),
        ),
        prioridad=Prioridad.ALTA,
        descripcion="Humo visible.",
    )
    instancia = json.loads(de.model_dump_json())
    _validar_contra_definicion(esquema_supervisor, "datos_emergencia", instancia)


def test_datos_emergencia_falta_required_falla_en_esquema(
    esquema_supervisor: dict,
) -> None:
    """Si quitamos un campo `required`, jsonschema debe rechazar."""
    instancia = {
        # falta id_emergencia
        "tipo_emergencia": "incendio",
        "ubicacion": {"direccion": "C/ X"},
        "prioridad": "alta",
        "descripcion": "Y",
    }
    with pytest.raises(jsonschema.ValidationError):
        _validar_contra_definicion(esquema_supervisor, "datos_emergencia", instancia)


# ─── InformeResolucion ↔ informe_resolucion ────────────────────────────────

def test_informe_resolucion_valida_contra_esquema(esquema_supervisor: dict) -> None:
    ir = InformeResolucion(
        id_emergencia="EM-001",
        tipo_emergencia=TipoEmergencia.INCENDIO,
        prioridad=Prioridad.ALTA,
        estado_final="resuelto",
        resumen="Incendio extinguido.",
        agentes_participantes=["g1.centralita", "g1.bomberos"],
        acciones_realizadas=["evaluar_riesgo", "enfriamiento"],
    )
    instancia = json.loads(ir.model_dump_json())
    _validar_contra_definicion(
        esquema_supervisor, "informe_resolucion", instancia
    )


def test_informe_resolucion_acepta_listas_vacias_aunque_se_penalice(
    esquema_supervisor: dict,
) -> None:
    """
    El schema acepta listas vacías; la penalización de corrección por
    estar vacías la aplica el supervisor del profesor (no el schema).
    """
    instancia = {
        "tipo_mensaje": "informe_resolucion",
        "id_emergencia": "EM-001",
        "tipo_emergencia": "incendio",
        "prioridad": "alta",
        "estado_final": "resuelto",
        "resumen": "Resolución mínima.",
        "agentes_participantes": [],
        "acciones_realizadas": [],
        "marca_temporal": "2026-05-06T17:00:00Z",
    }
    _validar_contra_definicion(
        esquema_supervisor, "informe_resolucion", instancia
    )


# ─── ConsultaEstado ↔ consulta_estado ──────────────────────────────────────

def test_consulta_estado_valida_contra_esquema(esquema_supervisor: dict) -> None:
    ce = ConsultaEstado(agente_destino="g1.centralita")
    instancia = json.loads(ce.model_dump_json())
    _validar_contra_definicion(
        esquema_supervisor, "consulta_estado", instancia
    )


# ─── EstadoAgente ↔ estado_agente ──────────────────────────────────────────

def test_estado_agente_minimo_valida_contra_esquema(
    esquema_supervisor: dict,
) -> None:
    ea = EstadoAgente(agente="g1.bomberos", estado="libre")
    instancia = json.loads(ea.model_dump_json())
    _validar_contra_definicion(esquema_supervisor, "estado_agente", instancia)


def test_estado_agente_con_emergencia_actual_valida(
    esquema_supervisor: dict,
) -> None:
    ea = EstadoAgente(
        agente="g1.bomberos",
        estado="actuando",
        emergencia_actual="EM-001",
        detalle="Aplicando enfriamiento.",
    )
    instancia = json.loads(ea.model_dump_json())
    _validar_contra_definicion(esquema_supervisor, "estado_agente", instancia)


# ─── Coherencia de los Enums entre Pydantic y JSON-Schema ───────────────────

def test_tipos_emergencia_pydantic_y_jsonschema_coinciden(
    esquema_supervisor: dict,
) -> None:
    """Los seis valores de TipoEmergencia están en el schema de datos_emergencia."""
    valores_pydantic = {miembro.value for miembro in TipoEmergencia}
    valores_schema = set(
        esquema_supervisor["definitions"]["datos_emergencia"]
        ["properties"]["tipo_emergencia"]["enum"]
    )
    assert valores_pydantic == valores_schema


def test_prioridades_pydantic_y_jsonschema_coinciden(
    esquema_supervisor: dict,
) -> None:
    valores_pydantic = {miembro.value for miembro in Prioridad}
    valores_schema = set(
        esquema_supervisor["definitions"]["datos_emergencia"]
        ["properties"]["prioridad"]["enum"]
    )
    assert valores_pydantic == valores_schema
