# -*- coding: utf-8 -*-
"""
Tests de los cinco modelos Pydantic de la ontología compartida.

Cobertura mínima por modelo (según docs/ontologia/propuesta_tests_unitarios.md §4):
  - Construcción válida con los campos requeridos.
  - Defaults aplicados cuando se omite un campo opcional.
  - Validación rechaza la ausencia de un campo `required`.
  - Round-trip JSON: serializar + deserializar conserva el contenido.

Estos modelos son el contrato de interfaz con el agente supervisor del
profesor; cualquier cambio incompatible aquí rompe la corrección
automática. Por eso los tests son intencionalmente defensivos.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from ontologia.modelos_compartidos import (
    ConsultaEstado,
    Coordenadas,
    DatosEmergencia,
    EstadoActuacion,
    EstadoAgente,
    InformeResolucion,
    Prioridad,
    RespuestaAgente,
    TipoEmergencia,
    Ubicacion,
)


# ─── Helpers para construir modelos con valores canónicos ───────────────────

def _construir_datos_emergencia(**overrides) -> DatosEmergencia:
    valores_base = {
        "id_emergencia": "EM-001",
        "tipo_emergencia": TipoEmergencia.INCENDIO,
        "ubicacion": Ubicacion(direccion="C/ Real 12, Villa Olivar"),
        "prioridad": Prioridad.ALTA,
        "descripcion": "Humo visible en planta segunda.",
    }
    valores_base.update(overrides)
    return DatosEmergencia(**valores_base)


def _construir_respuesta_agente(**overrides) -> RespuestaAgente:
    valores_base = {
        "id_emergencia": "EM-001",
        "agente_origen": "g1.bomberos",
        "estado": EstadoActuacion.EN_CAMINO,
        "detalle": "Saliendo del parque hacia el incidente.",
    }
    valores_base.update(overrides)
    return RespuestaAgente(**valores_base)


def _construir_informe_resolucion(**overrides) -> InformeResolucion:
    valores_base = {
        "id_emergencia": "EM-001",
        "tipo_emergencia": TipoEmergencia.INCENDIO,
        "prioridad": Prioridad.ALTA,
        "estado_final": "resuelto",
        "resumen": "Incendio extinguido sin víctimas.",
    }
    valores_base.update(overrides)
    return InformeResolucion(**valores_base)


# ─── DatosEmergencia ────────────────────────────────────────────────────────

def test_datos_emergencia_construccion_valida() -> None:
    de = _construir_datos_emergencia()
    assert de.id_emergencia == "EM-001"
    assert de.tipo_emergencia is TipoEmergencia.INCENDIO
    assert de.tipo_mensaje == "alerta_emergencia"


def test_datos_emergencia_marca_temporal_default_es_reciente() -> None:
    """marca_temporal usa default_factory; debe estar dentro de 5 s del 'now'."""
    antes = datetime.now()
    de = _construir_datos_emergencia()
    despues = datetime.now()
    assert antes - timedelta(seconds=1) <= de.marca_temporal <= despues + timedelta(seconds=1)


def test_datos_emergencia_falta_id_lanza() -> None:
    with pytest.raises(ValidationError):
        DatosEmergencia(
            tipo_emergencia=TipoEmergencia.INCENDIO,
            ubicacion=Ubicacion(direccion="X"),
            prioridad=Prioridad.ALTA, descripcion="Y",
        )


def test_datos_emergencia_tipo_emergencia_invalido_lanza() -> None:
    with pytest.raises(ValidationError):
        _construir_datos_emergencia(tipo_emergencia="categoria_inventada")


def test_datos_emergencia_round_trip_json() -> None:
    """JSON → modelo → JSON conserva el contenido."""
    de = _construir_datos_emergencia()
    json_a = de.model_dump_json()
    reconstruido = DatosEmergencia.model_validate_json(json_a)
    assert reconstruido.model_dump() == de.model_dump()


# ─── RespuestaAgente ────────────────────────────────────────────────────────

def test_respuesta_agente_construccion_valida() -> None:
    ra = _construir_respuesta_agente()
    assert ra.tipo_mensaje == "informe_actuacion"
    assert ra.recursos_desplegados == []


def test_respuesta_agente_con_recursos_desplegados() -> None:
    ra = _construir_respuesta_agente(recursos_desplegados=["B-12", "B-15"])
    assert ra.recursos_desplegados == ["B-12", "B-15"]


def test_respuesta_agente_estado_invalido_lanza() -> None:
    with pytest.raises(ValidationError):
        _construir_respuesta_agente(estado="esperando_callback")


def test_respuesta_agente_round_trip_json() -> None:
    ra = _construir_respuesta_agente(estado=EstadoActuacion.ACTUANDO)
    rec = RespuestaAgente.model_validate_json(ra.model_dump_json())
    assert rec.estado is EstadoActuacion.ACTUANDO


# ─── InformeResolucion ──────────────────────────────────────────────────────

def test_informe_resolucion_construccion_valida() -> None:
    ir = _construir_informe_resolucion()
    assert ir.tipo_mensaje == "informe_resolucion"
    assert ir.agentes_participantes == []
    assert ir.acciones_realizadas == []


def test_informe_resolucion_con_listas_pobladas() -> None:
    ir = _construir_informe_resolucion(
        agentes_participantes=["g1.centralita", "g1.bomberos"],
        acciones_realizadas=["enfriamiento", "ventilación"],
    )
    assert "g1.centralita" in ir.agentes_participantes
    assert len(ir.acciones_realizadas) == 2


def test_informe_resolucion_falta_resumen_lanza() -> None:
    with pytest.raises(ValidationError):
        InformeResolucion(
            id_emergencia="EM-001",
            tipo_emergencia=TipoEmergencia.INCENDIO,
            prioridad=Prioridad.ALTA,
            estado_final="resuelto",
        )


def test_informe_resolucion_round_trip_json_preserva_listas() -> None:
    ir = _construir_informe_resolucion(
        agentes_participantes=["g1.centralita"],
        acciones_realizadas=["enfriamiento"],
    )
    rec = InformeResolucion.model_validate_json(ir.model_dump_json())
    assert rec.agentes_participantes == ir.agentes_participantes
    assert rec.acciones_realizadas == ir.acciones_realizadas


# ─── ConsultaEstado ─────────────────────────────────────────────────────────

def test_consulta_estado_construccion_valida() -> None:
    ce = ConsultaEstado(agente_destino="g1.centralita")
    assert ce.tipo_mensaje == "consulta_estado"


def test_consulta_estado_falta_destino_lanza() -> None:
    with pytest.raises(ValidationError):
        ConsultaEstado()


# ─── EstadoAgente ───────────────────────────────────────────────────────────

def test_estado_agente_construccion_valida_minima() -> None:
    ea = EstadoAgente(agente="g1.centralita", estado="libre")
    assert ea.tipo_mensaje == "estado_agente"
    assert ea.emergencia_actual is None
    assert ea.detalle == ""


def test_estado_agente_con_emergencia_actual() -> None:
    ea = EstadoAgente(
        agente="g1.centralita",
        estado="ocupado",
        emergencia_actual="EM-001",
        detalle="Coordinando intervención.",
    )
    assert ea.emergencia_actual == "EM-001"


def test_estado_agente_falta_estado_lanza() -> None:
    with pytest.raises(ValidationError):
        EstadoAgente(agente="g1.centralita")


def test_estado_agente_round_trip_json() -> None:
    ea = EstadoAgente(agente="g1.bomberos", estado="en_escena", emergencia_actual="EM-099")
    rec = EstadoAgente.model_validate_json(ea.model_dump_json())
    assert rec.emergencia_actual == "EM-099"


# ─── Discriminadores tipo_mensaje ──────────────────────────────────────────

def test_cada_modelo_tiene_su_tipo_mensaje_distintivo() -> None:
    """El campo tipo_mensaje debe ser único por modelo, para que el
    receptor (supervisor o agente del grupo) pueda discriminar el tipo
    sin recurrir a heurísticas."""
    discriminadores = {
        DatosEmergencia: "alerta_emergencia",
        RespuestaAgente: "informe_actuacion",
        InformeResolucion: "informe_resolucion",
        ConsultaEstado: "consulta_estado",
        EstadoAgente: "estado_agente",
    }
    valores_vistos = list(discriminadores.values())
    assert len(set(valores_vistos)) == len(valores_vistos)


# ─── Marca temporal con tz-naive y tz-aware ────────────────────────────────

def test_marca_temporal_acepta_datetime_con_zona_horaria() -> None:
    momento = datetime(2026, 5, 6, 17, 30, tzinfo=timezone.utc)
    de = _construir_datos_emergencia(marca_temporal=momento)
    assert de.marca_temporal == momento


# ─── Ubicación: estructura objeto y coordenadas opcionales ─────────────────

def test_ubicacion_acepta_solo_direccion() -> None:
    """`coordenadas` es opcional; el supervisor puede omitirlo."""
    de = _construir_datos_emergencia(
        ubicacion=Ubicacion(direccion="Plaza Mayor 1"),
    )
    assert de.ubicacion.direccion == "Plaza Mayor 1"
    assert de.ubicacion.coordenadas is None


def test_ubicacion_acepta_coordenadas_opcionales() -> None:
    de = _construir_datos_emergencia(
        ubicacion=Ubicacion(
            direccion="Plaza Mayor 1",
            coordenadas=Coordenadas(latitud=37.78, longitud=-3.79),
        ),
    )
    assert de.ubicacion.coordenadas is not None
    assert de.ubicacion.coordenadas.latitud == pytest.approx(37.78)


def test_ubicacion_string_plano_es_rechazada() -> None:
    """Garantiza que ya no se acepta un string plano para `ubicacion`,
    como exigía el contrato anterior. Si esta prueba se rompe, los
    grupos están enviando el formato antiguo."""
    with pytest.raises(ValidationError):
        DatosEmergencia(
            id_emergencia="EM-001",
            tipo_emergencia=TipoEmergencia.INCENDIO,
            ubicacion="C/ Real 12",
            prioridad=Prioridad.ALTA,
            descripcion="Humo",
        )
