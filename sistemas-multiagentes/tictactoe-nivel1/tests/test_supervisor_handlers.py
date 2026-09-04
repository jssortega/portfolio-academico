"""
Tests unitarios de los manejadores HTTP y funciones de conversión
del panel web del Agente Supervisor.

Se prueban dos categorías:
- **Funciones puras** (``_mapear_resultado``, ``_nombre_legible_sala``,
  ``_convertir_informes``): sin necesidad de servidor HTTP.
- **Manejadores HTTP** (las cuatro rutas del supervisor): mediante
  el cliente de pruebas de ``pytest-aiohttp``, con un agente simulado
  inyectado en la aplicación.
"""

import os
import tempfile
from types import SimpleNamespace

import pytest
from aiohttp import web

from persistencia.almacen_supervisor import AlmacenSupervisor
from web.supervisor_handlers import (
    _convertir_informes,
    _mapear_resultado,
    _nombre_legible_sala,
    registrar_rutas_supervisor,
)


# ═══════════════════════════════════════════════════════════════════════════
#  Datos de prueba
# ═══════════════════════════════════════════════════════════════════════════

SALAS_EJEMPLO = [
    {"id": "tictactoe", "jid": "tictactoe@conference.localhost"},
]

INFORME_VICTORIA = {
    "action": "game-report",
    "result": "win",
    "winner": "X",
    "players": {
        "X": "jugador_ana@localhost",
        "O": "jugador_luis@localhost",
    },
    "turns": 7,
    "board": ["X", "O", "X", "O", "X", "O", "", "", "X"],
}

INFORME_ABORTADA = {
    "action": "game-report",
    "result": "aborted",
    "winner": None,
    "reason": "both-timeout",
    "players": {
        "X": "jugador_ana@localhost",
        "O": "jugador_luis@localhost",
    },
    "turns": 2,
    "board": ["X", "", "", "", "O", "", "", "", ""],
}

OCUPANTES_EJEMPLO = [
    {"nick": "supervisor", "jid": "supervisor@localhost",
     "rol": "supervisor", "estado": "online"},
    {"nick": "tablero_mesa1", "jid": "tablero_mesa1@localhost",
     "rol": "tablero", "estado": "online"},
]


# ═══════════════════════════════════════════════════════════════════════════
#  Utilidades
# ═══════════════════════════════════════════════════════════════════════════

def crear_agente_simulado(salas=None, informes=None, eventos=None,
                          ocupantes=None, almacen=None):
    """Crea un objeto que imita los atributos que los manejadores
    HTTP leen de ``request.app["agente"]``."""
    salas_cfg = salas if salas is not None else list(SALAS_EJEMPLO)
    agente = SimpleNamespace(
        salas_muc=salas_cfg,
        informes_por_sala=informes if informes is not None else {
            s["id"]: {} for s in salas_cfg
        },
        ocupantes_por_sala=ocupantes if ocupantes is not None else {
            s["id"]: [] for s in salas_cfg
        },
        log_por_sala=eventos if eventos is not None else {
            s["id"]: [] for s in salas_cfg
        },
        almacen=almacen,
    )
    return agente


def crear_app_con_agente(agente):
    """Crea una aplicación aiohttp con las rutas del supervisor y el
    agente simulado inyectado."""
    app = web.Application()
    registrar_rutas_supervisor(app)
    app["agente"] = agente
    return app


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de _mapear_resultado
# ═══════════════════════════════════════════════════════════════════════════

class TestMapearResultado:
    """Verifica la traducción de resultados de la ontología al formato
    del panel web."""

    def test_win_a_victoria(self):
        assert _mapear_resultado("win") == "victoria"

    def test_draw_a_empate(self):
        assert _mapear_resultado("draw") == "empate"

    def test_aborted_a_abortada(self):
        assert _mapear_resultado("aborted") == "abortada"

    def test_valor_ya_en_espanol_se_mantiene(self):
        assert _mapear_resultado("victoria") == "victoria"
        assert _mapear_resultado("empate") == "empate"

    def test_valor_desconocido_pasa_sin_cambios(self):
        assert _mapear_resultado("otro") == "otro"


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de _nombre_legible_sala
# ═══════════════════════════════════════════════════════════════════════════

class TestNombreLegibleSala:
    """Verifica la generación de nombres legibles para las salas."""

    def test_nombre_simple_devuelve_sala_principal(self):
        assert _nombre_legible_sala("tictactoe") == "Sala principal"

    def test_nombre_con_guion_bajo_se_capitaliza(self):
        resultado = _nombre_legible_sala("practica_grupo_a")
        assert "Sala" in resultado
        assert "Practica" in resultado
        assert "Grupo" in resultado


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de _convertir_informes
# ═══════════════════════════════════════════════════════════════════════════

class TestConvertirInformes:
    """Verifica la conversión de informes del formato interno al
    formato del panel web."""

    def test_diccionario_vacio_devuelve_lista_vacia(self):
        resultado = _convertir_informes({})
        assert resultado == []

    def test_convierte_un_informe_de_victoria(self):
        informes_raw = {
            "tablero_mesa1@localhost": INFORME_VICTORIA,
        }
        resultado = _convertir_informes(informes_raw)
        assert len(resultado) == 1
        inf = resultado[0]
        assert inf["resultado"] == "victoria"
        assert inf["ficha_ganadora"] == "X"
        assert inf["turnos"] == 7
        assert inf["tablero"] == "tablero_mesa1"

    def test_convierte_informe_abortada_con_motivo(self):
        informes_raw = {
            "tablero_mesa1@localhost": INFORME_ABORTADA,
        }
        resultado = _convertir_informes(informes_raw)
        assert len(resultado) == 1
        inf = resultado[0]
        assert inf["resultado"] == "abortada"
        assert inf["reason"] == "both-timeout"

    def test_id_secuencial(self):
        """Cada informe convertido debe tener un id secuencial."""
        informes_raw = {
            "tablero_1@localhost": INFORME_VICTORIA,
            "tablero_2@localhost": INFORME_ABORTADA,
        }
        resultado = _convertir_informes(informes_raw)
        assert resultado[0]["id"] == "informe_001"
        assert resultado[1]["id"] == "informe_002"

    def test_tablero_final_es_lista_de_9(self):
        """El tablero final debe ser una lista de 9 elementos."""
        informes_raw = {
            "tablero@localhost": INFORME_VICTORIA,
        }
        resultado = _convertir_informes(informes_raw)
        assert len(resultado[0]["tablero_final"]) == 9

    def test_jid_muc_extrae_nick_del_recurso(self):
        """Si el JID es de una sala MUC (contiene 'conference'), el
        nick del tablero debe extraerse del recurso del JID."""
        informes_raw = {
            "sala_pc04@conference.localhost/tablero_mesa1_rfr": (
                INFORME_VICTORIA
            ),
        }
        resultado = _convertir_informes(informes_raw)
        assert resultado[0]["tablero"] == "tablero_mesa1_rfr"

    def test_jid_real_extrae_nick_de_parte_local(self):
        """Si el JID es real (no MUC), el nick debe extraerse de la
        parte local (antes de @), no del recurso aleatorio."""
        informes_raw = {
            "tablero_mesa2@sinbad2.ujaen.es": INFORME_VICTORIA,
        }
        resultado = _convertir_informes(informes_raw)
        assert resultado[0]["tablero"] == "tablero_mesa2"


# ═══════════════════════════════════════════════════════════════════════════
#  Fixtures para tests HTTP
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
async def cliente_basico(aiohttp_client):
    """Cliente HTTP con un agente vacío."""
    agente = crear_agente_simulado()
    app = crear_app_con_agente(agente)
    cliente = await aiohttp_client(app)
    return cliente


@pytest.fixture
async def cliente_con_datos(aiohttp_client):
    """Cliente HTTP con un agente que tiene informes y ocupantes."""
    informes = {
        "tictactoe": {
            "tablero_mesa1@localhost": INFORME_VICTORIA,
        },
    }
    ocupantes = {"tictactoe": OCUPANTES_EJEMPLO}
    agente = crear_agente_simulado(
        informes=informes, ocupantes=ocupantes,
    )
    app = crear_app_con_agente(agente)
    cliente = await aiohttp_client(app)
    return cliente


@pytest.fixture
async def cliente_con_almacen(aiohttp_client):
    """Cliente HTTP con un agente que tiene un almacén SQLite con
    una ejecución finalizada."""
    fd, ruta_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    almacen = AlmacenSupervisor(ruta_db)
    almacen.crear_ejecucion(SALAS_EJEMPLO)
    almacen.guardar_informe(
        "tictactoe", "tablero_mesa1@localhost", INFORME_VICTORIA,
    )
    almacen.guardar_evento(
        "tictactoe", "informe", "tablero_mesa1",
        "Victoria X", "09:28:30",
    )
    almacen.finalizar_ejecucion()
    id_ejec = almacen.ejecucion_id

    agente = crear_agente_simulado(almacen=almacen)
    app = crear_app_con_agente(agente)
    cliente = await aiohttp_client(app)

    # Exponer datos para que los tests los usen
    cliente._almacen = almacen
    cliente._ruta_db = ruta_db
    cliente._id_ejec = id_ejec

    yield cliente

    almacen.cerrar()
    if os.path.exists(ruta_db):
        os.unlink(ruta_db)


# ═══════════════════════════════════════════════════════════════════════════
#  Tests HTTP: página principal
# ═══════════════════════════════════════════════════════════════════════════

class TestHandlerIndex:
    """Verifica que la ruta raíz sirve la página HTML del panel."""

    @pytest.mark.asyncio
    async def test_index_devuelve_html(self, cliente_basico):
        """GET /supervisor debe devolver contenido HTML con código 200."""
        resp = await cliente_basico.get("/supervisor")
        assert resp.status == 200
        texto = await resp.text()
        assert "<!DOCTYPE html>" in texto

    @pytest.mark.asyncio
    async def test_index_con_barra_final(self, cliente_basico):
        """GET /supervisor/ también debe funcionar."""
        resp = await cliente_basico.get("/supervisor/")
        assert resp.status == 200


# ═══════════════════════════════════════════════════════════════════════════
#  Tests HTTP: estado en vivo
# ═══════════════════════════════════════════════════════════════════════════

class TestHandlerState:
    """Verifica que la ruta de estado en vivo devuelve el JSON
    esperado."""

    @pytest.mark.asyncio
    async def test_devuelve_json_con_salas(self, cliente_con_datos):
        """La respuesta debe ser JSON con una clave 'salas'."""
        resp = await cliente_con_datos.get("/supervisor/api/state")
        assert resp.status == 200
        datos = await resp.json()
        assert "salas" in datos
        assert "timestamp" in datos
        assert len(datos["salas"]) == 1

    @pytest.mark.asyncio
    async def test_sala_contiene_informes(self, cliente_con_datos):
        """La sala debe incluir los informes convertidos."""
        resp = await cliente_con_datos.get("/supervisor/api/state")
        datos = await resp.json()
        sala = datos["salas"][0]
        assert len(sala["informes"]) == 1
        assert sala["informes"][0]["resultado"] == "victoria"

    @pytest.mark.asyncio
    async def test_sala_contiene_ocupantes(self, cliente_con_datos):
        """La sala debe incluir la lista de ocupantes."""
        resp = await cliente_con_datos.get("/supervisor/api/state")
        datos = await resp.json()
        sala = datos["salas"][0]
        assert len(sala["ocupantes"]) == 2


# ═══════════════════════════════════════════════════════════════════════════
#  Tests HTTP: historial de ejecuciones
# ═══════════════════════════════════════════════════════════════════════════

class TestHandlerListarEjecuciones:
    """Verifica que la ruta de listado de ejecuciones devuelve datos
    del almacén SQLite."""

    @pytest.mark.asyncio
    async def test_devuelve_lista_de_ejecuciones(
        self, cliente_con_almacen,
    ):
        """La respuesta debe contener una clave 'ejecuciones' con al
        menos un elemento."""
        resp = await cliente_con_almacen.get(
            "/supervisor/api/ejecuciones",
        )
        assert resp.status == 200
        datos = await resp.json()
        assert "ejecuciones" in datos
        assert len(datos["ejecuciones"]) >= 1

    @pytest.mark.asyncio
    async def test_ejecucion_tiene_campos_esperados(
        self, cliente_con_almacen,
    ):
        """Cada ejecución debe tener id, inicio, fin y num_salas."""
        resp = await cliente_con_almacen.get(
            "/supervisor/api/ejecuciones",
        )
        datos = await resp.json()
        ejec = datos["ejecuciones"][0]
        assert "id" in ejec
        assert "inicio" in ejec
        assert "fin" in ejec
        assert "num_salas" in ejec


class TestHandlerDatosEjecucion:
    """Verifica que la ruta de datos de una ejecución pasada devuelve
    el mismo formato que la ruta de estado en vivo."""

    @pytest.mark.asyncio
    async def test_devuelve_salas_con_informes(
        self, cliente_con_almacen,
    ):
        """La ejecución pasada debe contener las salas con sus
        informes y eventos."""
        id_ejec = cliente_con_almacen._id_ejec
        url = f"/supervisor/api/ejecuciones/{id_ejec}"
        resp = await cliente_con_almacen.get(url)
        assert resp.status == 200
        datos = await resp.json()
        assert "salas" in datos
        assert len(datos["salas"]) == 1
        sala = datos["salas"][0]
        assert sala["id"] == "tictactoe"
        assert len(sala["informes"]) == 1
        assert len(sala["log"]) == 1

    @pytest.mark.asyncio
    async def test_ocupantes_vacios_en_ejecucion_pasada(
        self, cliente_con_almacen,
    ):
        """Las ejecuciones pasadas no tienen datos de presencia."""
        id_ejec = cliente_con_almacen._id_ejec
        url = f"/supervisor/api/ejecuciones/{id_ejec}"
        resp = await cliente_con_almacen.get(url)
        datos = await resp.json()
        sala = datos["salas"][0]
        assert sala["ocupantes"] == []

    @pytest.mark.asyncio
    async def test_ejecucion_inexistente_devuelve_vacio(
        self, cliente_con_almacen,
    ):
        """Una ejecución que no existe debe devolver salas vacías."""
        resp = await cliente_con_almacen.get(
            "/supervisor/api/ejecuciones/9999",
        )
        assert resp.status == 200
        datos = await resp.json()
        assert datos["salas"] == []

    @pytest.mark.asyncio
    async def test_id_no_numerico_devuelve_vacio(
        self, cliente_con_almacen,
    ):
        """Un id no numérico debe devolver salas vacías."""
        resp = await cliente_con_almacen.get(
            "/supervisor/api/ejecuciones/abc",
        )
        assert resp.status == 200
        datos = await resp.json()
        assert datos["salas"] == []
