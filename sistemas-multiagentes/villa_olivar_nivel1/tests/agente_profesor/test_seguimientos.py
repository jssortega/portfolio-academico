"""Tests del autómata ``Seguimiento``.

Verifican las transiciones permitidas, las que deben rechazarse
(estado terminal o transición no contemplada por el grafo), las
métricas de latencia y la serialización a dict que consume el
dashboard.

Son tests puros: no requieren SPADE, ni red, ni servidor XMPP.
"""
from datetime import datetime, timedelta

import pytest

from agente_profesor.seguimientos import (
    ESTADOS_OK,
    ESTADOS_TERMINALES,
    EstadoSeguimiento,
    Seguimiento,
)


# ─── Helper de fabricación ─────────────────────────────────────────────────

def _construir_seguimiento(**overrides) -> Seguimiento:
    """Devuelve un Seguimiento con valores por defecto coherentes."""
    base = {
        "id_emergencia": "test-id-123",
        "grupo": "fenix",
        "jid_destino": "centralita_fenix@localhost",
        "tipo_emergencia": "incendio",
        "prioridad": "alta",
        "descripcion": "Calle Mayor 14 — humo denso",
    }
    base.update(overrides)
    return Seguimiento(**base)


# ─── Estado inicial ────────────────────────────────────────────────────────

class TestEstadoInicial:
    """El seguimiento se construye en estado PREPARADO."""

    def test_estado_inicial_es_preparado(self):
        seguimiento = _construir_seguimiento()
        assert seguimiento.estado == EstadoSeguimiento.PREPARADO

    def test_eventos_iniciales_estan_vacios(self):
        seguimiento = _construir_seguimiento()
        assert seguimiento.eventos == []

    def test_instantes_arranque_son_none(self):
        seguimiento = _construir_seguimiento()
        assert seguimiento.instante_envio is None
        assert seguimiento.instante_agree is None
        assert seguimiento.instante_informe is None

    def test_no_es_terminal_al_inicio(self):
        seguimiento = _construir_seguimiento()
        assert not seguimiento.es_terminal()


# ─── Transiciones positivas ────────────────────────────────────────────────

class TestTransicionesValidas:
    """Cada transición permitida del autómata."""

    def test_preparado_a_enviado(self):
        seguimiento = _construir_seguimiento()
        seguimiento.registrar_envio()
        assert seguimiento.estado == EstadoSeguimiento.ENVIADO
        assert seguimiento.instante_envio is not None

    def test_enviado_a_aceptado(self):
        seguimiento = _construir_seguimiento()
        seguimiento.registrar_envio()
        seguimiento.registrar_agree()
        assert seguimiento.estado == EstadoSeguimiento.ACEPTADO
        assert seguimiento.instante_agree is not None

    def test_aceptado_a_resuelto(self):
        seguimiento = _construir_seguimiento()
        seguimiento.registrar_envio()
        seguimiento.registrar_agree()
        seguimiento.registrar_informe({"tipo_mensaje": "informe_resolucion"})
        assert seguimiento.estado == EstadoSeguimiento.RESUELTO
        assert seguimiento.informe is not None

    def test_secuencia_completa_genera_eventos_timeline(self):
        seguimiento = _construir_seguimiento()
        seguimiento.registrar_envio()
        seguimiento.registrar_agree()
        seguimiento.registrar_informe({"k": "v"})
        # Tres transiciones registradas en la línea de tiempo.
        tipos = [e.tipo for e in seguimiento.eventos]
        assert tipos == [
            "estado:ENVIADO",
            "estado:ACEPTADO",
            "estado:RESUELTO",
        ]


# ─── Transiciones a estados terminales de error ─────────────────────────────

class TestTransicionesAError:
    """Desde cualquier estado transitorio se puede ir a un terminal KO."""

    @pytest.mark.parametrize("destino_error", [
        EstadoSeguimiento.TIMEOUT,
        EstadoSeguimiento.RECHAZADO,
        EstadoSeguimiento.FALLIDO,
    ])
    def test_desde_preparado_a_error(self, destino_error):
        seguimiento = _construir_seguimiento()
        seguimiento.registrar_error(destino_error, "motivo de prueba")
        assert seguimiento.estado == destino_error
        assert seguimiento.error == "motivo de prueba"

    @pytest.mark.parametrize("destino_error", [
        EstadoSeguimiento.TIMEOUT,
        EstadoSeguimiento.RECHAZADO,
        EstadoSeguimiento.FALLIDO,
    ])
    def test_desde_enviado_a_error(self, destino_error):
        seguimiento = _construir_seguimiento()
        seguimiento.registrar_envio()
        seguimiento.registrar_error(destino_error, "fallo")
        assert seguimiento.estado == destino_error

    @pytest.mark.parametrize("destino_error", [
        EstadoSeguimiento.TIMEOUT,
        EstadoSeguimiento.RECHAZADO,
        EstadoSeguimiento.FALLIDO,
    ])
    def test_desde_aceptado_a_error(self, destino_error):
        seguimiento = _construir_seguimiento()
        seguimiento.registrar_envio()
        seguimiento.registrar_agree()
        seguimiento.registrar_error(destino_error, "fallo")
        assert seguimiento.estado == destino_error


# ─── Transiciones inválidas ────────────────────────────────────────────────

class TestTransicionesInvalidas:
    """El autómata rechaza saltos no contemplados por el grafo."""

    def test_estado_terminal_no_admite_transicion(self):
        seguimiento = _construir_seguimiento()
        seguimiento.registrar_error(
            EstadoSeguimiento.TIMEOUT, "sin agree",
        )
        ok = seguimiento.transicionar(EstadoSeguimiento.RESUELTO)
        assert ok is False
        assert seguimiento.estado == EstadoSeguimiento.TIMEOUT

    def test_no_se_puede_saltar_de_preparado_a_resuelto(self):
        seguimiento = _construir_seguimiento()
        ok = seguimiento.transicionar(EstadoSeguimiento.RESUELTO)
        assert ok is False
        assert seguimiento.estado == EstadoSeguimiento.PREPARADO

    def test_no_se_puede_saltar_de_preparado_a_aceptado(self):
        seguimiento = _construir_seguimiento()
        ok = seguimiento.transicionar(EstadoSeguimiento.ACEPTADO)
        assert ok is False

    def test_no_se_puede_saltar_de_enviado_a_resuelto(self):
        seguimiento = _construir_seguimiento()
        seguimiento.registrar_envio()
        ok = seguimiento.transicionar(EstadoSeguimiento.RESUELTO)
        assert ok is False
        assert seguimiento.estado == EstadoSeguimiento.ENVIADO


# ─── Métricas de latencia ──────────────────────────────────────────────────

class TestLatencias:
    """Cálculo de latencias en milisegundos."""

    def test_latencia_agree_es_none_sin_agree(self):
        seguimiento = _construir_seguimiento()
        seguimiento.registrar_envio()
        assert seguimiento.latencia_agree_ms() is None

    def test_latencia_agree_se_calcula_correctamente(self):
        seguimiento = _construir_seguimiento()
        seguimiento.instante_envio = datetime(2026, 5, 1, 12, 0, 0)
        seguimiento.instante_agree = (
            seguimiento.instante_envio + timedelta(milliseconds=350)
        )
        assert seguimiento.latencia_agree_ms() == 350

    def test_latencia_informe_es_none_sin_informe(self):
        seguimiento = _construir_seguimiento()
        seguimiento.registrar_envio()
        seguimiento.registrar_agree()
        assert seguimiento.latencia_informe_ms() is None

    def test_latencia_informe_se_calcula_desde_agree(self):
        seguimiento = _construir_seguimiento()
        seguimiento.instante_agree = datetime(2026, 5, 1, 12, 0, 0)
        seguimiento.instante_informe = (
            seguimiento.instante_agree + timedelta(seconds=12)
        )
        assert seguimiento.latencia_informe_ms() == 12_000


# ─── Conjuntos de estados ──────────────────────────────────────────────────

class TestConjuntosEstados:
    """Los conjuntos exportados son coherentes con el grafo."""

    def test_terminales_incluyen_los_cuatro_finales(self):
        assert ESTADOS_TERMINALES == frozenset({
            EstadoSeguimiento.RESUELTO,
            EstadoSeguimiento.RECHAZADO,
            EstadoSeguimiento.TIMEOUT,
            EstadoSeguimiento.FALLIDO,
        })

    def test_estados_ok_solo_contiene_resuelto(self):
        assert ESTADOS_OK == frozenset({EstadoSeguimiento.RESUELTO})

    def test_es_terminal_marca_correctamente_los_estados_finales(self):
        for estado in ESTADOS_TERMINALES:
            seguimiento = _construir_seguimiento(estado=estado)
            assert seguimiento.es_terminal()


# ─── Serialización a dict ──────────────────────────────────────────────────

class TestSerializacion:
    """``a_dict()`` produce el esquema documentado del dashboard."""

    def test_a_dict_contiene_campos_obligatorios(self):
        seguimiento = _construir_seguimiento()
        datos = seguimiento.a_dict()
        for clave in (
            "id_emergencia", "grupo", "jid_destino", "estado",
            "tipo_emergencia", "prioridad", "descripcion",
            "instante_creacion", "instante_envio", "instante_agree",
            "instante_informe", "latencia_agree_ms",
            "latencia_informe_ms", "informe", "error", "eventos",
        ):
            assert clave in datos, f"Falta el campo '{clave}'"

    def test_estado_se_serializa_como_string(self):
        seguimiento = _construir_seguimiento()
        seguimiento.registrar_envio()
        datos = seguimiento.a_dict()
        assert datos["estado"] == "ENVIADO"

    def test_eventos_se_serializan_como_lista(self):
        seguimiento = _construir_seguimiento()
        seguimiento.registrar_envio()
        datos = seguimiento.a_dict()
        assert isinstance(datos["eventos"], list)
        assert len(datos["eventos"]) == 1
        assert datos["eventos"][0]["tipo"] == "estado:ENVIADO"

    def test_a_dict_serializa_instantes_como_iso(self):
        seguimiento = _construir_seguimiento()
        seguimiento.registrar_envio()
        datos = seguimiento.a_dict()
        # ISO 8601 contiene 'T' como separador entre fecha y hora.
        assert "T" in datos["instante_envio"]
        assert "T" in datos["instante_creacion"]
