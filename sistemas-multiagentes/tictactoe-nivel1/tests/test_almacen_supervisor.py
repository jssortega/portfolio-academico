"""
Tests unitarios del almacén de persistencia SQLite del supervisor.

Verifica que la clase ``AlmacenSupervisor`` gestiona correctamente
las operaciones de creación, lectura y cierre sobre la base de datos
SQLite, sin dependencia de SPADE ni del servidor XMPP.

Cada test utiliza una base de datos temporal que se elimina al
finalizar, de modo que los tests son independientes entre sí.
"""

import json
import os
import tempfile

import pytest

from persistencia.almacen_supervisor import AlmacenSupervisor


# ═══════════════════════════════════════════════════════════════════════════
#  Datos de prueba
# ═══════════════════════════════════════════════════════════════════════════

SALAS_EJEMPLO = [
    {"id": "tictactoe", "jid": "tictactoe@conference.localhost"},
    {"id": "torneo", "jid": "torneo@conference.localhost"},
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
    "ts": "09:28:30",
}

INFORME_EMPATE = {
    "action": "game-report",
    "result": "draw",
    "winner": None,
    "players": {
        "X": "jugador_ana@localhost",
        "O": "jugador_luis@localhost",
    },
    "turns": 9,
    "board": ["X", "O", "X", "X", "O", "O", "O", "X", "X"],
    "ts": "09:35:12",
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
    "ts": "10:12:45",
}


# ═══════════════════════════════════════════════════════════════════════════
#  Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def ruta_db_temporal():
    """Crea un fichero temporal para la base de datos y lo elimina
    al finalizar el test."""
    fd, ruta = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield ruta
    if os.path.exists(ruta):
        os.unlink(ruta)


@pytest.fixture
def almacen(ruta_db_temporal):
    """Crea un almacén conectado a una base de datos temporal."""
    alm = AlmacenSupervisor(ruta_db_temporal)
    yield alm
    alm.cerrar()


@pytest.fixture
def almacen_con_ejecucion(almacen):
    """Crea un almacén con una ejecución ya registrada."""
    almacen.crear_ejecucion(SALAS_EJEMPLO)
    return almacen


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de inicialización
# ═══════════════════════════════════════════════════════════════════════════

class TestInicializacion:
    """Verifica que el almacén se inicializa correctamente."""

    def test_crear_almacen_genera_fichero(self, ruta_db_temporal):
        """El constructor debe crear el fichero de la base de datos."""
        alm = AlmacenSupervisor(ruta_db_temporal)
        existe = os.path.exists(ruta_db_temporal)
        alm.cerrar()
        assert existe

    def test_crear_almacen_crea_directorios_intermedios(self):
        """Si la ruta contiene directorios que no existen, los crea."""
        with tempfile.TemporaryDirectory() as directorio:
            ruta = os.path.join(directorio, "sub", "dir", "test.db")
            alm = AlmacenSupervisor(ruta)
            existe = os.path.exists(ruta)
            alm.cerrar()
            assert existe

    def test_ejecucion_id_inicial_es_none(self, almacen):
        """Antes de llamar a crear_ejecucion, el id debe ser None."""
        assert almacen.ejecucion_id is None


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de gestión de ejecuciones
# ═══════════════════════════════════════════════════════════════════════════

class TestCrearEjecucion:
    """Verifica la creación de ejecuciones."""

    def test_crear_ejecucion_devuelve_id_positivo(self, almacen):
        """El identificador de la ejecución debe ser un entero positivo."""
        id_ejec = almacen.crear_ejecucion(SALAS_EJEMPLO)
        assert id_ejec > 0

    def test_crear_ejecucion_asigna_ejecucion_id(self, almacen):
        """Tras crear la ejecución, el atributo ejecucion_id debe
        coincidir con el valor devuelto."""
        id_ejec = almacen.crear_ejecucion(SALAS_EJEMPLO)
        assert almacen.ejecucion_id == id_ejec

    def test_crear_varias_ejecuciones_ids_distintos(self, almacen):
        """Cada ejecución debe recibir un identificador diferente."""
        id1 = almacen.crear_ejecucion(SALAS_EJEMPLO)
        almacen.finalizar_ejecucion()
        id2 = almacen.crear_ejecucion(SALAS_EJEMPLO)
        assert id1 != id2

    def test_crear_ejecucion_almacena_salas(self, almacen):
        """Las salas pasadas deben poder recuperarse."""
        almacen.crear_ejecucion(SALAS_EJEMPLO)
        salas = almacen.obtener_salas_ejecucion(almacen.ejecucion_id)
        assert len(salas) == len(SALAS_EJEMPLO)
        assert salas[0]["id"] == "tictactoe"
        assert salas[1]["id"] == "torneo"


class TestFinalizarEjecucion:
    """Verifica la finalización de ejecuciones."""

    def test_finalizar_establece_fecha_fin(self, almacen_con_ejecucion):
        """Tras finalizar, la ejecución debe tener fecha de fin."""
        almacen_con_ejecucion.finalizar_ejecucion()
        ejecuciones = almacen_con_ejecucion.listar_ejecuciones()
        assert ejecuciones[0]["fin"] is not None

    def test_ejecucion_activa_tiene_fin_nulo(self, almacen_con_ejecucion):
        """Una ejecución no finalizada debe tener fin como None."""
        ejecuciones = almacen_con_ejecucion.listar_ejecuciones()
        assert ejecuciones[0]["fin"] is None

    def test_finalizar_sin_ejecucion_no_falla(self, almacen):
        """Llamar a finalizar sin haber creado ejecución no debe
        lanzar ninguna excepción."""
        almacen.finalizar_ejecucion()


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de guardado de informes
# ═══════════════════════════════════════════════════════════════════════════

class TestGuardarInforme:
    """Verifica el almacenamiento de informes de partida."""

    def test_guardar_informe_se_puede_recuperar(self, almacen_con_ejecucion):
        """Un informe guardado debe poder leerse con los mismos datos."""
        almacen_con_ejecucion.guardar_informe(
            "tictactoe", "tablero_mesa1@localhost", INFORME_VICTORIA,
        )
        informes = almacen_con_ejecucion.obtener_informes_ejecucion(
            almacen_con_ejecucion.ejecucion_id,
        )
        assert "tictactoe" in informes
        assert "tablero_mesa1@localhost" in informes["tictactoe"]
        cuerpo = informes["tictactoe"]["tablero_mesa1@localhost"]
        assert cuerpo["result"] == "win"
        assert cuerpo["winner"] == "X"
        assert cuerpo["turns"] == 7

    def test_guardar_varios_informes_misma_sala(self, almacen_con_ejecucion):
        """Se pueden guardar informes de distintos tableros en la misma
        sala."""
        almacen_con_ejecucion.guardar_informe(
            "tictactoe", "tablero_mesa1@localhost", INFORME_VICTORIA,
        )
        almacen_con_ejecucion.guardar_informe(
            "tictactoe", "tablero_mesa2@localhost", INFORME_EMPATE,
        )
        informes = almacen_con_ejecucion.obtener_informes_ejecucion(
            almacen_con_ejecucion.ejecucion_id,
        )
        assert len(informes["tictactoe"]) == 2

    def test_guardar_informes_en_salas_distintas(self, almacen_con_ejecucion):
        """Los informes de salas diferentes se separan correctamente."""
        almacen_con_ejecucion.guardar_informe(
            "tictactoe", "tablero_mesa1@localhost", INFORME_VICTORIA,
        )
        almacen_con_ejecucion.guardar_informe(
            "torneo", "tablero_t1@localhost", INFORME_ABORTADA,
        )
        informes = almacen_con_ejecucion.obtener_informes_ejecucion(
            almacen_con_ejecucion.ejecucion_id,
        )
        assert "tictactoe" in informes
        assert "torneo" in informes
        assert informes["torneo"]["tablero_t1@localhost"]["result"] == "aborted"

    def test_guardar_informe_sin_ejecucion_no_falla(self, almacen):
        """Si no se ha creado ejecución, guardar_informe no debe
        lanzar excepciones (simplemente no hace nada)."""
        almacen.guardar_informe(
            "tictactoe", "tablero@localhost", INFORME_VICTORIA,
        )

    def test_informes_ejecucion_inexistente_devuelve_vacio(
        self, almacen_con_ejecucion,
    ):
        """Consultar informes de una ejecución que no existe debe
        devolver un diccionario vacío."""
        informes = almacen_con_ejecucion.obtener_informes_ejecucion(9999)
        assert informes == {}


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de guardado de eventos
# ═══════════════════════════════════════════════════════════════════════════

class TestGuardarEvento:
    """Verifica el almacenamiento de eventos del registro."""

    def test_guardar_evento_se_puede_recuperar(self, almacen_con_ejecucion):
        """Un evento guardado debe poder leerse con los mismos campos."""
        almacen_con_ejecucion.guardar_evento(
            "tictactoe", "informe", "tablero_mesa1", "Victoria X", "09:28:30",
        )
        eventos = almacen_con_ejecucion.obtener_eventos_ejecucion(
            almacen_con_ejecucion.ejecucion_id,
        )
        assert "tictactoe" in eventos
        assert len(eventos["tictactoe"]) == 1
        ev = eventos["tictactoe"][0]
        assert ev["tipo"] == "informe"
        assert ev["de"] == "tablero_mesa1"
        assert ev["detalle"] == "Victoria X"
        assert ev["ts"] == "09:28:30"

    def test_eventos_se_devuelven_en_orden_inverso(
        self, almacen_con_ejecucion,
    ):
        """Los eventos más recientes deben aparecer primero (orden
        cronológico inverso)."""
        almacen_con_ejecucion.guardar_evento(
            "tictactoe", "presencia", "ana", "Se une", "09:00:00",
        )
        almacen_con_ejecucion.guardar_evento(
            "tictactoe", "informe", "tablero", "Victoria", "09:05:00",
        )
        eventos = almacen_con_ejecucion.obtener_eventos_ejecucion(
            almacen_con_ejecucion.ejecucion_id,
        )
        primero = eventos["tictactoe"][0]
        assert primero["tipo"] == "informe"

    def test_guardar_evento_sin_ejecucion_no_falla(self, almacen):
        """Si no hay ejecución activa, guardar_evento no debe lanzar
        excepciones."""
        almacen.guardar_evento(
            "tictactoe", "presencia", "ana", "Se une", "09:00:00",
        )

    def test_eventos_en_salas_distintas_se_separan(
        self, almacen_con_ejecucion,
    ):
        """Los eventos de salas diferentes deben estar separados."""
        almacen_con_ejecucion.guardar_evento(
            "tictactoe", "presencia", "ana", "Entra", "09:00:00",
        )
        almacen_con_ejecucion.guardar_evento(
            "torneo", "presencia", "luis", "Entra", "09:01:00",
        )
        eventos = almacen_con_ejecucion.obtener_eventos_ejecucion(
            almacen_con_ejecucion.ejecucion_id,
        )
        assert len(eventos["tictactoe"]) == 1
        assert len(eventos["torneo"]) == 1


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de listado de ejecuciones
# ═══════════════════════════════════════════════════════════════════════════

class TestListarEjecuciones:
    """Verifica la consulta del historial de ejecuciones."""

    def test_listar_sin_ejecuciones_devuelve_lista_vacia(self, almacen):
        """Si no se ha creado ninguna ejecución, la lista está vacía."""
        resultado = almacen.listar_ejecuciones()
        assert resultado == []

    def test_listar_una_ejecucion(self, almacen_con_ejecucion):
        """Con una ejecución activa, la lista debe contener un
        elemento."""
        resultado = almacen_con_ejecucion.listar_ejecuciones()
        assert len(resultado) == 1
        assert resultado[0]["id"] == almacen_con_ejecucion.ejecucion_id
        assert resultado[0]["num_salas"] == 2

    def test_listar_varias_ejecuciones_orden_descendente(self, almacen):
        """Las ejecuciones deben aparecer ordenadas de más reciente
        a más antigua."""
        almacen.crear_ejecucion([SALAS_EJEMPLO[0]])
        almacen.finalizar_ejecucion()
        almacen.crear_ejecucion(SALAS_EJEMPLO)
        resultado = almacen.listar_ejecuciones()
        assert len(resultado) == 2
        # La más reciente (2 salas) debe estar primero
        assert resultado[0]["num_salas"] == 2
        assert resultado[1]["num_salas"] == 1

    def test_listar_incluye_campos_esperados(self, almacen_con_ejecucion):
        """Cada ejecución listada debe contener id, inicio, fin y
        num_salas."""
        resultado = almacen_con_ejecucion.listar_ejecuciones()
        ejec = resultado[0]
        assert "id" in ejec
        assert "inicio" in ejec
        assert "fin" in ejec
        assert "num_salas" in ejec


# ═══════════════════════════════════════════════════════════════════════════
#  Tests de aislamiento entre ejecuciones
# ═══════════════════════════════════════════════════════════════════════════

class TestAislamientoEjecuciones:
    """Verifica que los datos de una ejecución no se mezclan con los
    de otra."""

    def test_informes_de_ejecucion_anterior_no_aparecen_en_la_nueva(
        self, almacen,
    ):
        """Los informes guardados en una ejecución no deben aparecer
        al consultar otra ejecución diferente."""
        almacen.crear_ejecucion(SALAS_EJEMPLO)
        id1 = almacen.ejecucion_id
        almacen.guardar_informe(
            "tictactoe", "tablero@localhost", INFORME_VICTORIA,
        )
        almacen.finalizar_ejecucion()

        almacen.crear_ejecucion(SALAS_EJEMPLO)
        id2 = almacen.ejecucion_id

        informes_1 = almacen.obtener_informes_ejecucion(id1)
        informes_2 = almacen.obtener_informes_ejecucion(id2)

        assert len(informes_1.get("tictactoe", {})) == 1
        assert len(informes_2.get("tictactoe", {})) == 0

    def test_eventos_de_ejecucion_anterior_no_aparecen_en_la_nueva(
        self, almacen,
    ):
        """Los eventos guardados en una ejecución no deben aparecer
        al consultar otra ejecución diferente."""
        almacen.crear_ejecucion(SALAS_EJEMPLO)
        id1 = almacen.ejecucion_id
        almacen.guardar_evento(
            "tictactoe", "presencia", "ana", "Entra", "09:00:00",
        )
        almacen.finalizar_ejecucion()

        almacen.crear_ejecucion(SALAS_EJEMPLO)
        id2 = almacen.ejecucion_id

        eventos_1 = almacen.obtener_eventos_ejecucion(id1)
        eventos_2 = almacen.obtener_eventos_ejecucion(id2)

        assert len(eventos_1.get("tictactoe", [])) == 1
        assert len(eventos_2.get("tictactoe", [])) == 0
