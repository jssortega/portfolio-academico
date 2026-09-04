import json
import os
import pytest
import jsonschema

DIRECTORIO_ACTUAL = os.path.dirname(__file__)
RUTA_ESQUEMA = os.path.join(
    DIRECTORIO_ACTUAL, "..", "ontologia", "esquema_emergencias.json"
)

ALERTA_VALIDA = {
    "tipo_mensaje": "alerta_emergencia",
    "id_emergencia": "INC-2026-042",
    "tipo_emergencia": "derrame_quimico",
    "ubicacion": {"direccion": "Av. Constitución 42"},
    "prioridad": "alta",
    "descripcion": "Derrame de amoniaco en la calzada",
    "marca_temporal": "2026-03-09T10:00:00Z",
}

INFORME_VALIDO = {
    "tipo_mensaje": "informe_actuacion",
    "id_emergencia": "INC-2026-042",
    "agente_origen": "bomberos",
    "estado": "en_camino",
    "detalle": "Desplazando dos unidades al lugar del incidente",
    "marca_temporal": "2026-03-09T10:05:00Z",
}


def test_esquema_es_json_valido():
    """
    El fichero esquema_emergencias.json se carga sin errores con json.load().
    """
    with open(RUTA_ESQUEMA, "r", encoding="utf-8") as f:
        esquema = json.load(f)

    assert isinstance(esquema, dict), (
        "El esquema debería ser un diccionario JSON válido."
    )


def test_esquema_tiene_definiciones_minimas():
    """
    El esquema contiene al menos las claves alerta_emergencia e informe_actuacion dentro de definitions.
    """
    with open(RUTA_ESQUEMA, "r", encoding="utf-8") as f:
        esquema = json.load(f)

    assert "definitions" in esquema, "El esquema debe tener una sección 'definitions'."
    assert "alerta_emergencia" in esquema["definitions"], (
        "Falta definir 'alerta_emergencia'."
    )
    assert "informe_actuacion" in esquema["definitions"], (
        "Falta definir 'informe_actuacion'."
    )


def test_esquema_tiene_seis_tipos():
    """El esquema debe contener al menos seis definiciones de tipos de mensaje."""
    with open(RUTA_ESQUEMA, "r", encoding="utf-8") as f:
        esquema = json.load(f)
    defs = esquema.get("definitions", {})
    assert len(defs) >= 6, (
        f"Se esperaban al menos 6 definiciones, pero hay {len(defs)}: {list(defs.keys())}"
    )


def test_todos_los_tipos_tienen_descripcion(esquema_emergencias):
    """Cada definición debe tener una descripción no vacía."""
    for name, defn in esquema_emergencias.get("definitions", {}).items():
        assert (
            "description" in defn
            and isinstance(defn["description"], str)
            and defn["description"].strip()
        ), f"La definición {name} no tiene description válida"


def test_todos_los_tipos_tienen_marca_temporal(esquema_emergencias):
    """Cada tipo debe tener marca_temporal en sus propiedades y en required."""
    for name, defn in esquema_emergencias.get("definitions", {}).items():
        props = defn.get("properties", {})
        req = defn.get("required", [])
        assert "marca_temporal" in props, f"{name} no tiene propiedad 'marca_temporal'"
        assert "marca_temporal" in req, (
            f"{name} no tiene 'marca_temporal' en 'required'"
        )


def test_alerta_valida_contra_esquema():
    """
    Un mensaje de ejemplo de tipo alerta_emergencia con todos los campos obligatorios
    se valida correctamente contra el esquema usando jsonschema.validate().
    """
    with open(RUTA_ESQUEMA, "r", encoding="utf-8") as f:
        esquema = json.load(f)

    esquema_validacion = {
        "definitions": esquema["definitions"],
        "$ref": "#/definitions/alerta_emergencia",
    }

    jsonschema.validate(instance=ALERTA_VALIDA, schema=esquema_validacion)


def test_alerta_sin_campo_obligatorio_falla():
    """
    Un mensaje de tipo alerta_emergencia al que le falta un campo obligatorio
    (por ejemplo, prioridad) produce un error de validación.
    """
    with open(RUTA_ESQUEMA, "r", encoding="utf-8") as f:
        esquema = json.load(f)

    esquema_validacion = {
        "definitions": esquema["definitions"],
        "$ref": "#/definitions/alerta_emergencia",
    }

    alerta_invalida = ALERTA_VALIDA.copy()
    del alerta_invalida["prioridad"]

    with pytest.raises(jsonschema.exceptions.ValidationError):
        jsonschema.validate(instance=alerta_invalida, schema=esquema_validacion)


def test_informe_valido_contra_esquema():
    """
    Un mensaje de ejemplo de tipo informe_actuacion con todos los campos obligatorios
    se valida correctamente.
    """
    with open(RUTA_ESQUEMA, "r", encoding="utf-8") as f:
        esquema = json.load(f)

    esquema_validacion = {
        "definitions": esquema["definitions"],
        "$ref": "#/definitions/informe_actuacion",
    }

    jsonschema.validate(instance=INFORME_VALIDO, schema=esquema_validacion)


@pytest.fixture
def esquema_emergencias():
    """Carga el esquema JSON de la ontología antes de ejecutar los tests."""
    with open("ontologia/esquema_emergencias.json", "r", encoding="utf-8") as f:
        return json.load(f)


def test_esquema_tiene_cuatro_tipos(esquema_emergencias):
    """El esquema JSON contiene al menos 4 definiciones de tipos de mensaje."""
    assert "definitions" in esquema_emergencias, (
        "El esquema debe tener una sección 'definitions'"
    )

    tipos = esquema_emergencias["definitions"].keys()
    assert len(tipos) >= 4, (
        f"Se esperaban al menos 4 tipos de mensaje, pero solo hay {len(tipos)}: {list(tipos)}"
    )


def test_solicitud_recurso_valida(esquema_emergencias):
    """Un mensaje de tipo solicitud_recurso con todos los campos obligatorios es válido."""

    subesquema = esquema_emergencias["definitions"]["solicitud_recurso"]
    mensaje_solicitud = {
        "tipo_mensaje": "solicitud_recurso",
        "id_emergencia": "INC-2026-001",
        "solicitante": "bomberos",
        "destinatario": "policia",
        "accion_solicitada": "establecer_perimetro",
        "marca_temporal": "2026-10-24T10:00:00Z",
    }

    try:
        jsonschema.validate(instance=mensaje_solicitud, schema=subesquema)
    except jsonschema.ValidationError as e:
        pytest.fail(
            f"El mensaje 'solicitud_recurso' falló la validación del esquema: {e.message}"
        )


def test_respuesta_recurso_valida(esquema_emergencias):
    """Un mensaje de tipo respuesta_recurso con todos los campos obligatorios es válido."""

    subesquema = esquema_emergencias["definitions"]["respuesta_recurso"]
    mensaje_respuesta = {
        "tipo_mensaje": "respuesta_recurso",
        "id_emergencia": "INC-2026-001",
        "solicitante_original": "bomberos",
        "accion_solicitada": "establecer_perimetro",
        "aceptada": True,
        "marca_temporal": "2026-10-24T10:05:00Z",
    }

    try:
        jsonschema.validate(instance=mensaje_respuesta, schema=subesquema)
    except jsonschema.ValidationError as e:
        pytest.fail(
            f"El mensaje 'respuesta_recurso' falló la validación del esquema: {e.message}"
        )
