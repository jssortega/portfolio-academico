"""Tests del catálogo de escenarios.

El catálogo es la fuente de verdad para la inyección de incidentes
y para el modo demo. Los tests verifican:

- Que los UUIDs son **deterministas**: la misma clave produce siempre
  el mismo ``id_emergencia`` (propiedad sobre la que se apoya la
  parametrización de los tests del grupo).
- Que la colección demo es **reproducible** (mismas claves, mismos
  identificadores entre invocaciones).
- Que las claves del catálogo están bien formadas (snake_case y
  únicas) y existen las claves que el modo demo necesita.
"""
from __future__ import annotations

import pytest

from agente_profesor.escenarios import (
    GRUPO_DEMO_PRIMERO,
    GRUPO_DEMO_SEGUNDO,
    _DEFINICIONES_ESCENARIOS,
    claves_escenarios,
    construir_id_emergencia,
    construir_seguimientos_demo,
    grupos_demo,
)
from agente_profesor.seguimientos import EstadoSeguimiento


# ─── Determinismo de los identificadores ───────────────────────────────────

class TestUUIDsDeterministas:
    """``construir_id_emergencia`` produce identificadores reproducibles."""

    def test_misma_clave_produce_mismo_uuid(self):
        a = construir_id_emergencia("incendio_alta")
        b = construir_id_emergencia("incendio_alta")
        assert a == b

    def test_claves_distintas_producen_uuids_distintos(self):
        a = construir_id_emergencia("incendio_alta")
        b = construir_id_emergencia("incendio_critica")
        assert a != b

    def test_uuid_v5_tiene_36_caracteres(self):
        uuid_str = construir_id_emergencia("incendio_alta")
        # Formato canónico UUID: 8-4-4-4-12.
        assert len(uuid_str) == 36
        assert uuid_str.count("-") == 4


# ─── Forma del catálogo ────────────────────────────────────────────────────

class TestCatalogo:
    """Verifica las invariantes estructurales del catálogo."""

    def test_catalogo_no_esta_vacio(self):
        assert len(_DEFINICIONES_ESCENARIOS) > 0

    def test_claves_son_unicas(self):
        claves = [d[0] for d in _DEFINICIONES_ESCENARIOS]
        assert len(claves) == len(set(claves))

    def test_claves_estan_en_snake_case(self):
        for clave in claves_escenarios():
            assert clave == clave.lower(), (
                f"Clave '{clave}' no está en minúsculas"
            )
            assert " " not in clave, f"Clave '{clave}' contiene espacios"

    def test_orden_de_claves_es_estable_entre_llamadas(self):
        primera = claves_escenarios()
        segunda = claves_escenarios()
        assert primera == segunda

    def test_definiciones_tienen_5_campos(self):
        for definicion in _DEFINICIONES_ESCENARIOS:
            assert len(definicion) == 5


# ─── Modo demo ─────────────────────────────────────────────────────────────

class TestSeguimientosDemo:
    """``construir_seguimientos_demo`` produce datos reproducibles."""

    def test_demo_es_reproducible(self):
        a = construir_seguimientos_demo()
        b = construir_seguimientos_demo()
        ids_a = [s.id_emergencia for s in a]
        ids_b = [s.id_emergencia for s in b]
        assert ids_a == ids_b

    def test_demo_genera_seis_seguimientos(self):
        seguimientos = construir_seguimientos_demo()
        assert len(seguimientos) == 6

    def test_demo_incluye_dos_grupos_distintos(self):
        seguimientos = construir_seguimientos_demo()
        grupos = {s.grupo for s in seguimientos}
        assert grupos == {GRUPO_DEMO_PRIMERO, GRUPO_DEMO_SEGUNDO}

    def test_demo_incluye_estados_terminales_variados(self):
        seguimientos = construir_seguimientos_demo()
        estados = {s.estado for s in seguimientos}
        # El demo debe enseñar al menos un OK y al menos un KO.
        assert EstadoSeguimiento.RESUELTO in estados
        ko_presentes = estados & {
            EstadoSeguimiento.TIMEOUT,
            EstadoSeguimiento.FALLIDO,
            EstadoSeguimiento.RECHAZADO,
        }
        assert ko_presentes, "El demo debería incluir un estado KO"

    def test_seguimientos_resueltos_tienen_informe(self):
        seguimientos = construir_seguimientos_demo()
        for seguimiento in seguimientos:
            if seguimiento.estado == EstadoSeguimiento.RESUELTO:
                assert seguimiento.informe is not None

    def test_seguimientos_ko_tienen_mensaje_de_error(self):
        seguimientos = construir_seguimientos_demo()
        ko_estados = {
            EstadoSeguimiento.TIMEOUT,
            EstadoSeguimiento.FALLIDO,
            EstadoSeguimiento.RECHAZADO,
        }
        for seguimiento in seguimientos:
            if seguimiento.estado in ko_estados:
                assert seguimiento.error, (
                    f"El seguimiento {seguimiento.id_emergencia} no "
                    "tiene mensaje de error a pesar de estado KO."
                )


# ─── Grupos demo ───────────────────────────────────────────────────────────

class TestGruposDemo:
    """``grupos_demo`` devuelve los grupos del modo demo."""

    def test_grupos_demo_son_dos(self):
        grupos = grupos_demo()
        assert len(grupos) == 2

    def test_grupos_demo_tienen_jid_centralita(self):
        grupos = grupos_demo()
        for grupo in grupos:
            assert "@" in grupo["jid_centralita"]

    def test_ids_grupos_demo_son_los_constantes(self):
        ids = {g["id"] for g in grupos_demo()}
        assert ids == {GRUPO_DEMO_PRIMERO, GRUPO_DEMO_SEGUNDO}
