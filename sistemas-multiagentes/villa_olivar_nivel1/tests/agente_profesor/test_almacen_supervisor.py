"""Tests de la capa de persistencia SQLite.

Verifican el ciclo de vida de las ejecuciones, el guardado y la
recuperación de seguimientos y eventos, el listado del histórico y
la idempotencia del sembrado del modo demo. Cada test trabaja sobre
un fichero SQLite temporal que se elimina al finalizar.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from agente_profesor.persistencia.almacen_supervisor import (
    AlmacenSupervisor,
)
from agente_profesor.persistencia.semilla_demo import (
    sembrar_demo_si_vacio,
)


# ─── Inicialización del almacén ────────────────────────────────────────────

class TestInicializacion:
    """El constructor del almacén crea el fichero y el esquema."""

    def test_constructor_crea_fichero_si_no_existe(self, db_temporal):
        assert not os.path.exists(db_temporal)
        almacen = AlmacenSupervisor(db_temporal)
        try:
            assert os.path.exists(db_temporal)
        finally:
            almacen.cerrar()

    def test_constructor_crea_directorio_padre(self, tmp_path):
        ruta = tmp_path / "nuevo_dir" / "supervisor.db"
        almacen = AlmacenSupervisor(str(ruta))
        try:
            assert ruta.parent.exists()
        finally:
            almacen.cerrar()

    def test_listar_ejecuciones_en_db_recien_creada_devuelve_vacio(
        self, almacen_temporal,
    ):
        assert almacen_temporal.listar_ejecuciones() == []

    def test_hay_ejecuciones_es_falso_en_db_recien_creada(
        self, almacen_temporal,
    ):
        assert almacen_temporal.hay_ejecuciones() is False


# ─── Crear ejecución ───────────────────────────────────────────────────────

class TestCrearEjecucion:
    """``crear_ejecucion`` inserta y devuelve un id incremental."""

    def test_devuelve_id_positivo(self, almacen_temporal):
        ejec_id = almacen_temporal.crear_ejecucion(
            modo="activo", grupos=[], descripcion="prueba",
        )
        assert ejec_id >= 1

    def test_ids_son_incrementales(self, almacen_temporal):
        a = almacen_temporal.crear_ejecucion("activo", [])
        b = almacen_temporal.crear_ejecucion("activo", [])
        assert b > a

    def test_grupos_se_persisten(self, almacen_temporal):
        grupos = [{
            "id": "fenix",
            "nombre": "Equipo Fénix",
            "jid_centralita": "centralita_fenix@localhost",
            "descripcion": "Test",
        }]
        ejec_id = almacen_temporal.crear_ejecucion("activo", grupos)
        datos = almacen_temporal.obtener_ejecucion(ejec_id)
        assert len(datos["grupos"]) == 1
        assert datos["grupos"][0]["id"] == "fenix"


# ─── Guardar y leer seguimientos ───────────────────────────────────────────

class TestGuardarSeguimiento:
    """Guardado y recuperación de seguimientos en una ejecución."""

    def _construir_dict(self, id_emergencia: str = "id-1") -> dict:
        return {
            "id_emergencia": id_emergencia,
            "grupo": "fenix",
            "jid_destino": "centralita_fenix@localhost",
            "tipo_emergencia": "incendio",
            "prioridad": "alta",
            "descripcion": "humo en planta",
            "estado": "RESUELTO",
            "instante_creacion": "2026-05-01T12:00:00",
            "instante_envio": "2026-05-01T12:00:01",
            "instante_agree": "2026-05-01T12:00:02",
            "instante_informe": "2026-05-01T12:00:30",
            "latencia_agree_ms": 1000,
            "latencia_informe_ms": 28000,
            "error": None,
            "informe": {"tipo_mensaje": "informe_resolucion"},
            "eventos": [{"tipo": "estado:RESUELTO", "detalle": "ok"}],
        }

    def test_seguimiento_se_recupera_con_los_mismos_datos(
        self, almacen_temporal,
    ):
        ejec_id = almacen_temporal.crear_ejecucion("activo", [])
        datos = self._construir_dict()
        almacen_temporal.guardar_seguimiento(datos)

        recuperada = almacen_temporal.obtener_ejecucion(ejec_id)
        assert len(recuperada["seguimientos"]) == 1
        seg = recuperada["seguimientos"][0]
        assert seg["id_emergencia"] == "id-1"
        assert seg["estado"] == "RESUELTO"
        assert seg["informe"] == {"tipo_mensaje": "informe_resolucion"}
        assert len(seg["eventos"]) == 1

    def test_actualizar_seguimiento_no_genera_duplicados(
        self, almacen_temporal,
    ):
        ejec_id = almacen_temporal.crear_ejecucion("activo", [])
        datos = self._construir_dict()
        almacen_temporal.guardar_seguimiento(datos)
        datos["estado"] = "TIMEOUT"
        almacen_temporal.guardar_seguimiento(datos)

        recuperada = almacen_temporal.obtener_ejecucion(ejec_id)
        assert len(recuperada["seguimientos"]) == 1
        assert recuperada["seguimientos"][0]["estado"] == "TIMEOUT"

    def test_guardar_sin_ejecucion_activa_no_falla(
        self, almacen_temporal,
    ):
        # No llamamos a crear_ejecucion previamente.
        almacen_temporal.guardar_seguimiento(self._construir_dict())
        # El listado sigue vacío.
        assert almacen_temporal.listar_ejecuciones() == []

    def test_seguimientos_de_distintas_ejecuciones_se_aislan(
        self, almacen_temporal,
    ):
        ejec_a = almacen_temporal.crear_ejecucion("activo", [])
        almacen_temporal.guardar_seguimiento(
            self._construir_dict("id-a"),
        )
        ejec_b = almacen_temporal.crear_ejecucion("activo", [])
        almacen_temporal.guardar_seguimiento(
            self._construir_dict("id-b"),
        )

        a = almacen_temporal.obtener_ejecucion(ejec_a)
        b = almacen_temporal.obtener_ejecucion(ejec_b)
        ids_a = [s["id_emergencia"] for s in a["seguimientos"]]
        ids_b = [s["id_emergencia"] for s in b["seguimientos"]]
        assert ids_a == ["id-a"]
        assert ids_b == ["id-b"]


# ─── Eventos del log ───────────────────────────────────────────────────────

class TestLogEventos:
    """Persistencia y orden cronológico inverso del log."""

    def test_evento_se_recupera(self, almacen_temporal):
        ejec_id = almacen_temporal.crear_ejecucion("activo", [])
        almacen_temporal.guardar_evento_log({
            "ts": "12:00:00", "tipo": "info",
            "de": "supervisor", "detalle": "arranque",
        })
        datos = almacen_temporal.obtener_ejecucion(ejec_id)
        assert len(datos["log"]) == 1
        assert datos["log"][0]["detalle"] == "arranque"

    def test_eventos_se_devuelven_de_mas_reciente_a_mas_antiguo(
        self, almacen_temporal,
    ):
        ejec_id = almacen_temporal.crear_ejecucion("activo", [])
        for indice in range(3):
            almacen_temporal.guardar_evento_log({
                "ts": f"12:00:0{indice}",
                "tipo": "info", "de": "x",
                "detalle": f"evento-{indice}",
            })
        datos = almacen_temporal.obtener_ejecucion(ejec_id)
        # Inserción 0,1,2 → orden descendente esperado: 2,1,0.
        detalles = [e["detalle"] for e in datos["log"]]
        assert detalles == ["evento-2", "evento-1", "evento-0"]


# ─── Finalización ──────────────────────────────────────────────────────────

class TestFinalizarEjecucion:
    """``finalizar_ejecucion`` rellena el campo ``fin``."""

    def test_finalizar_marca_fin_no_nulo(self, almacen_temporal):
        ejec_id = almacen_temporal.crear_ejecucion("activo", [])
        almacen_temporal.finalizar_ejecucion()
        datos = almacen_temporal.obtener_ejecucion(ejec_id)
        assert datos["metadatos"]["fin"] is not None

    def test_finalizar_sin_ejecucion_activa_no_lanza(
        self, almacen_temporal,
    ):
        # No debe lanzar excepciones aunque no haya ejecución.
        almacen_temporal.finalizar_ejecucion()


# ─── Listado de ejecuciones ────────────────────────────────────────────────

class TestListarEjecuciones:
    """El listado se ordena por id descendente."""

    def test_ejecuciones_se_ordenan_descendentemente(
        self, almacen_temporal,
    ):
        almacen_temporal.crear_ejecucion("activo", [], "primera")
        almacen_temporal.crear_ejecucion("activo", [], "segunda")
        almacen_temporal.crear_ejecucion("demo", [], "tercera")
        ids = [e["id"] for e in almacen_temporal.listar_ejecuciones()]
        assert ids == sorted(ids, reverse=True)

    def test_etiqueta_legible_incluye_id_y_modo(
        self, almacen_temporal,
    ):
        almacen_temporal.crear_ejecucion("activo", [], "una sesión")
        listado = almacen_temporal.listar_ejecuciones()
        etiqueta = listado[0]["etiqueta"]
        assert "#" in etiqueta
        assert "activo" in etiqueta
        assert "una sesión" in etiqueta


# ─── Sembrado demo ─────────────────────────────────────────────────────────

class TestSembradoDemo:
    """``sembrar_demo_si_vacio`` es idempotente."""

    def test_siembra_si_db_vacia(self, almacen_temporal):
        sembrada = sembrar_demo_si_vacio(almacen_temporal)
        assert sembrada is True
        assert almacen_temporal.hay_ejecuciones()

    def test_no_siembra_dos_veces(self, almacen_temporal):
        primera = sembrar_demo_si_vacio(almacen_temporal)
        segunda = sembrar_demo_si_vacio(almacen_temporal)
        assert primera is True
        assert segunda is False
        assert len(almacen_temporal.listar_ejecuciones()) == 1

    def test_demo_genera_seis_seguimientos(self, almacen_temporal):
        sembrar_demo_si_vacio(almacen_temporal)
        ejec_id = almacen_temporal.listar_ejecuciones()[0]["id"]
        datos = almacen_temporal.obtener_ejecucion(ejec_id)
        assert len(datos["seguimientos"]) == 6
