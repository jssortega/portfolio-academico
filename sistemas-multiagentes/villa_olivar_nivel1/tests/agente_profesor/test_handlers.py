"""Tests de los handlers HTTP del panel del supervisor.

Cubren tanto las funciones puras de transformación
(``_resumen_metricas``, ``_percentiles``, generadores CSV) como las
rutas HTTP completas con un cliente aiohttp de pruebas.

Para los tests HTTP no se arranca SPADE: se construye una aplicación
``aiohttp`` con las rutas registradas y un agente simulado inyectado
en ``app['agente']``. El plugin ``pytest-aiohttp`` proporciona la
fixture ``aiohttp_client`` que envía peticiones reales sin abrir un
puerto de red.
"""
from __future__ import annotations

import json

import pytest
from aiohttp import web

from agente_profesor.persistencia.almacen_supervisor import (
    AlmacenSupervisor,
)
from agente_profesor.seguimientos import (
    EstadoSeguimiento,
    Seguimiento,
)
from agente_profesor.web.handlers import (
    _almacen_lectura,
    _csv_log,
    _csv_resumen,
    _csv_seguimientos,
    _percentiles,
    _resumen_metricas,
    crear_middleware_auth,
    registrar_rutas,
)


# ─── Helpers ───────────────────────────────────────────────────────────────

def _seguimiento_resuelto(id_emergencia: str = "x") -> Seguimiento:
    seguimiento = Seguimiento(
        id_emergencia=id_emergencia,
        grupo="fenix",
        jid_destino="centralita_fenix@localhost",
        tipo_emergencia="incendio",
        prioridad="alta",
        descripcion="Calle Mayor 14",
    )
    seguimiento.registrar_envio()
    seguimiento.registrar_agree()
    seguimiento.registrar_informe({"tipo_mensaje": "informe_resolucion"})
    return seguimiento


def _seguimiento_timeout(id_emergencia: str = "y") -> Seguimiento:
    seguimiento = Seguimiento(
        id_emergencia=id_emergencia,
        grupo="olivar42",
        jid_destino="centralita_olivar42@localhost",
        tipo_emergencia="inundacion",
        prioridad="media",
        descripcion="Ribera del Olivar",
    )
    seguimiento.registrar_envio()
    seguimiento.registrar_error(
        EstadoSeguimiento.TIMEOUT, "No llegó agree",
    )
    return seguimiento


# ─── Funciones puras ───────────────────────────────────────────────────────

class TestResumenMetricas:
    """``_resumen_metricas`` agrega correctamente los seguimientos."""

    def test_lista_vacia_devuelve_ceros(self):
        resumen = _resumen_metricas([])
        assert resumen["total"] == 0
        assert resumen["ok"] == 0
        assert resumen["ko"] == 0
        assert resumen["por_estado"] == {}

    def test_cuenta_ok_y_ko(self):
        seguimientos = [
            _seguimiento_resuelto("a").a_dict(),
            _seguimiento_resuelto("b").a_dict(),
            _seguimiento_timeout("c").a_dict(),
        ]
        resumen = _resumen_metricas(seguimientos)
        assert resumen["total"] == 3
        assert resumen["ok"] == 2
        assert resumen["ko"] == 1

    def test_agrupa_por_grupo(self):
        seguimientos = [
            _seguimiento_resuelto("a").a_dict(),
            _seguimiento_timeout("b").a_dict(),
        ]
        resumen = _resumen_metricas(seguimientos)
        assert resumen["por_grupo"]["fenix"] == 1
        assert resumen["por_grupo"]["olivar42"] == 1


class TestPercentiles:
    """Cálculos puros de mediana, p95 y máximo."""

    def test_lista_vacia(self):
        resultado = _percentiles([])
        assert resultado == {"mediana": 0, "p95": 0, "maximo": 0}

    def test_un_unico_valor(self):
        resultado = _percentiles([100])
        assert resultado["mediana"] == 100
        assert resultado["maximo"] == 100

    def test_secuencia_creciente(self):
        valores = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        resultado = _percentiles(valores)
        # Mediana: posición 5 → 60.
        assert resultado["mediana"] == 60
        assert resultado["maximo"] == 100


class TestGeneradoresCSV:
    """Los CSV emitidos contienen cabeceras y filas correctas."""

    def test_csv_seguimientos_contiene_cabeceras(self):
        contenido = _csv_seguimientos([
            _seguimiento_resuelto().a_dict(),
        ])
        primera_linea = contenido.split("\n")[0]
        assert "id_emergencia" in primera_linea
        assert "grupo" in primera_linea
        assert "estado" in primera_linea

    def test_csv_resumen_contiene_categorias(self):
        contenido = _csv_resumen([
            _seguimiento_resuelto().a_dict(),
            _seguimiento_timeout().a_dict(),
        ])
        assert "totales" in contenido
        assert "por_estado" in contenido
        assert "por_grupo" in contenido

    def test_csv_log_contiene_cabeceras(self):
        eventos = [{
            "ts": "12:00:00", "tipo": "info",
            "de": "supervisor", "detalle": "arranque",
        }]
        contenido = _csv_log(eventos)
        primera_linea = contenido.split("\n")[0]
        assert "timestamp" in primera_linea
        assert "tipo" in primera_linea


# ─── Cliente aiohttp ───────────────────────────────────────────────────────

@pytest.fixture
async def cliente_panel(aiohttp_client, agente_simulado):
    """Devuelve un cliente HTTP de prueba con las rutas registradas."""
    # Incluimos un seguimiento resuelto y otro timeout para que las
    # respuestas tengan datos representativos.
    a = _seguimiento_resuelto("a")
    b = _seguimiento_timeout("b")
    agente_simulado.seguimientos = {
        "a": a, "b": b,
    }
    agente_simulado.log_eventos.appendleft({
        "ts": "12:00:00", "tipo": "info",
        "de": "supervisor", "detalle": "arranque",
    })

    app = web.Application()
    registrar_rutas(app)
    app["agente"] = agente_simulado
    app["modo"] = "activo"

    return await aiohttp_client(app)


@pytest.fixture
async def cliente_consulta(
    aiohttp_client, agente_simulado, almacen_temporal,
):
    """Cliente con un almacén en modo consulta y una ejecución pasada."""
    ejec_id = almacen_temporal.crear_ejecucion(
        modo="activo", grupos=agente_simulado.grupos,
        descripcion="prueba",
    )
    almacen_temporal.guardar_seguimiento(
        _seguimiento_resuelto("x").a_dict(),
    )
    almacen_temporal.guardar_evento_log({
        "ts": "12:00:00", "tipo": "info",
        "de": "supervisor", "detalle": "arranque",
    })
    almacen_temporal.finalizar_ejecucion()

    agente_simulado.almacen = almacen_temporal
    agente_simulado.modo = "consulta"
    agente_simulado.es_agente_vivo = False
    agente_simulado.seguimientos = {}

    app = web.Application()
    registrar_rutas(app)
    app["agente"] = agente_simulado
    app["modo"] = "consulta"

    # Inyectamos el id de la ejecución antes de arrancar la app para
    # evitar el DeprecationWarning de aiohttp (modificar la app tras
    # iniciarla está desaconsejado).
    app["__ejec_id__"] = ejec_id
    cliente = await aiohttp_client(app)
    return cliente


# ─── /supervisor (HTML) ────────────────────────────────────────────────────

class TestHandlerIndex:
    """``GET /supervisor`` sirve la plantilla HTML."""

    @pytest.mark.asyncio
    async def test_devuelve_html(self, cliente_panel):
        resp = await cliente_panel.get("/supervisor")
        assert resp.status == 200
        contenido = await resp.text()
        assert "<html" in contenido.lower() or "<!doctype" in contenido.lower()


# ─── /supervisor/api/state ─────────────────────────────────────────────────

class TestHandlerState:
    """Esquema estable de ``/api/state``."""

    @pytest.mark.asyncio
    async def test_contiene_claves_esperadas(self, cliente_panel):
        resp = await cliente_panel.get("/supervisor/api/state")
        assert resp.status == 200
        datos = await resp.json()
        for clave in (
            "supervisor", "grupos", "seguimientos",
            "resumen", "log", "timestamp",
        ):
            assert clave in datos

    @pytest.mark.asyncio
    async def test_seguimientos_se_serializan(self, cliente_panel):
        resp = await cliente_panel.get("/supervisor/api/state")
        datos = await resp.json()
        assert len(datos["seguimientos"]) == 2
        ids = {s["id_emergencia"] for s in datos["seguimientos"]}
        assert ids == {"a", "b"}


# ─── /supervisor/api/seguimientos[/{id}] ───────────────────────────────────

class TestHandlerSeguimientos:
    """Listado y detalle de seguimientos."""

    @pytest.mark.asyncio
    async def test_lista_devuelve_los_dos(self, cliente_panel):
        resp = await cliente_panel.get("/supervisor/api/seguimientos")
        datos = await resp.json()
        assert len(datos["seguimientos"]) == 2

    @pytest.mark.asyncio
    async def test_detalle_existente_devuelve_seguimiento(
        self, cliente_panel,
    ):
        resp = await cliente_panel.get("/supervisor/api/seguimientos/a")
        assert resp.status == 200
        datos = await resp.json()
        assert datos["id_emergencia"] == "a"

    @pytest.mark.asyncio
    async def test_detalle_inexistente_devuelve_404(self, cliente_panel):
        resp = await cliente_panel.get(
            "/supervisor/api/seguimientos/no-existe",
        )
        assert resp.status == 404


# ─── /supervisor/api/resumen ───────────────────────────────────────────────

class TestHandlerResumen:
    @pytest.mark.asyncio
    async def test_devuelve_metricas(self, cliente_panel):
        resp = await cliente_panel.get("/supervisor/api/resumen")
        datos = await resp.json()
        assert datos["total"] == 2
        assert datos["ok"] == 1
        assert datos["ko"] == 1


# ─── /supervisor/api/csv/{tipo} ────────────────────────────────────────────

class TestHandlerCSV:
    """Exportación CSV en vivo."""

    @pytest.mark.asyncio
    async def test_csv_seguimientos_se_descarga(self, cliente_panel):
        resp = await cliente_panel.get(
            "/supervisor/api/csv/seguimientos",
        )
        assert resp.status == 200
        assert resp.headers["Content-Type"].startswith("text/csv")
        contenido = await resp.text()
        assert "id_emergencia" in contenido

    @pytest.mark.asyncio
    async def test_csv_resumen_se_descarga(self, cliente_panel):
        resp = await cliente_panel.get("/supervisor/api/csv/resumen")
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_csv_log_se_descarga(self, cliente_panel):
        resp = await cliente_panel.get("/supervisor/api/csv/log")
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_tipo_invalido_devuelve_400(self, cliente_panel):
        resp = await cliente_panel.get("/supervisor/api/csv/invento")
        assert resp.status == 400


# ─── /supervisor/api/ejecuciones ───────────────────────────────────────────

class TestHandlerEjecuciones:
    """Endpoints de histórico (modo consulta con almacén persistido)."""

    @pytest.mark.asyncio
    async def test_listado_devuelve_la_ejecucion(self, cliente_consulta):
        resp = await cliente_consulta.get(
            "/supervisor/api/ejecuciones",
        )
        datos = await resp.json()
        assert len(datos["ejecuciones"]) == 1

    @pytest.mark.asyncio
    async def test_detalle_devuelve_seguimientos(self, cliente_consulta):
        ejec_id = cliente_consulta.app["__ejec_id__"]
        resp = await cliente_consulta.get(
            f"/supervisor/api/ejecuciones/{ejec_id}",
        )
        datos = await resp.json()
        assert len(datos["seguimientos"]) == 1

    @pytest.mark.asyncio
    async def test_detalle_inexistente_devuelve_404(
        self, cliente_consulta,
    ):
        resp = await cliente_consulta.get(
            "/supervisor/api/ejecuciones/9999",
        )
        assert resp.status == 404


# ─── /supervisor/api/escenarios ────────────────────────────────────────────

class TestHandlerEscenarios:
    """``GET /supervisor/api/escenarios`` lista el catálogo."""

    @pytest.mark.asyncio
    async def test_devuelve_lista_no_vacia(self, cliente_panel):
        resp = await cliente_panel.get("/supervisor/api/escenarios")
        assert resp.status == 200
        datos = await resp.json()
        assert "escenarios" in datos
        assert len(datos["escenarios"]) > 0

    @pytest.mark.asyncio
    async def test_cada_escenario_tiene_campos_completos(
        self, cliente_panel,
    ):
        resp = await cliente_panel.get("/supervisor/api/escenarios")
        datos = await resp.json()
        for esc in datos["escenarios"]:
            for clave in (
                "clave", "tipo_emergencia", "prioridad",
                "ubicacion", "descripcion",
            ):
                assert clave in esc


# ─── /supervisor/api/inyectar ──────────────────────────────────────────────

class TestHandlerInyectar:
    """``POST /supervisor/api/inyectar``."""

    @pytest.mark.asyncio
    async def test_falta_grupo_devuelve_400(self, cliente_panel):
        resp = await cliente_panel.post(
            "/supervisor/api/inyectar", json={},
        )
        assert resp.status == 400

    @pytest.mark.asyncio
    async def test_modo_consulta_devuelve_409(self, cliente_consulta):
        resp = await cliente_consulta.post(
            "/supervisor/api/inyectar", json={"grupo": "fenix"},
        )
        assert resp.status == 409


# ─── _almacen_lectura ──────────────────────────────────────────────────────

class TestAlmacenLectura:
    """Context manager que tolera el cierre del almacén principal.

    Comprueba que el histórico sigue siendo consultable cuando el
    almacén principal del supervisor se ha cerrado tras pulsar
    Finalizar pero el panel sigue abierto en el navegador.
    """

    def test_devuelve_almacen_vivo_si_existe(
        self, agente_simulado, almacen_temporal,
    ):
        agente_simulado.almacen = almacen_temporal
        with _almacen_lectura(agente_simulado) as almacen:
            assert almacen is almacen_temporal
        # No se cierra al salir del bloque.
        assert agente_simulado.almacen is almacen_temporal

    def test_abre_transitorio_si_almacen_cerrado(
        self, agente_simulado, db_temporal,
    ):
        # Sembramos primero el fichero a través de un almacén que
        # cerramos a continuación, simulando el escenario "post
        # finalizar".
        almacen_inicial = AlmacenSupervisor(db_temporal)
        almacen_inicial.crear_ejecucion("activo", [], "histórico")
        almacen_inicial.finalizar_ejecucion()
        almacen_inicial.cerrar()

        agente_simulado.almacen = None
        agente_simulado.ruta_db = db_temporal

        with _almacen_lectura(agente_simulado) as almacen:
            assert almacen is not None
            ejecuciones = almacen.listar_ejecuciones()
            assert len(ejecuciones) == 1

    def test_devuelve_none_si_no_hay_ruta(self, agente_simulado):
        agente_simulado.almacen = None
        agente_simulado.ruta_db = ""
        with _almacen_lectura(agente_simulado) as almacen:
            assert almacen is None


# ─── Middleware HTTP Basic ────────────────────────────────────────────────

class TestMiddlewareAuth:
    """``crear_middleware_auth`` exige cabecera Authorization."""

    @pytest.mark.asyncio
    async def test_sin_credenciales_devuelve_401(
        self, aiohttp_client, agente_simulado,
    ):
        app = web.Application()
        app.middlewares.append(
            crear_middleware_auth("admin", "secreto"),
        )
        registrar_rutas(app)
        app["agente"] = agente_simulado
        app["modo"] = "activo"
        cliente = await aiohttp_client(app)

        resp = await cliente.get("/supervisor/api/state")
        assert resp.status == 401
        assert "WWW-Authenticate" in resp.headers

    @pytest.mark.asyncio
    async def test_credenciales_validas_dejan_pasar(
        self, aiohttp_client, agente_simulado,
    ):
        import base64
        token = base64.b64encode(b"admin:secreto").decode()

        app = web.Application()
        app.middlewares.append(
            crear_middleware_auth("admin", "secreto"),
        )
        registrar_rutas(app)
        app["agente"] = agente_simulado
        app["modo"] = "activo"
        cliente = await aiohttp_client(app)

        resp = await cliente.get(
            "/supervisor/api/state",
            headers={"Authorization": f"Basic {token}"},
        )
        assert resp.status == 200
