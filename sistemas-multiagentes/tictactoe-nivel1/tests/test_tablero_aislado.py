import pytest
from agentes.agente_tablero import AgenteTablero
from behaviours.fsm_turno_tablero import comprobar_ganador


@pytest.fixture
def agente_tablero():
    """Crea una instancia del agente sin arrancarlo para probar su lógica."""
    # Usamos un JID y password ficticios porque no vamos a conectar a XMPP
    agente = AgenteTablero("tablero@test", "secret")
    # Inicializamos manualmente lo que normalmente haría el setup()
    agente.tablero = [""] * 9
    agente.jugadores_partida = {"X": None, "O": None}
    agente.estado_partida = "waiting"
    return agente


def test_estado_inicial_correcto(agente_tablero):
    """El estado inicial del tablero es correcto."""
    assert agente_tablero.tablero == [""] * 9
    assert agente_tablero.estado_partida == "waiting"


def test_gestion_plazas_jugadores(agente_tablero):
    """Verifica la asignación de X, O y el rechazo por lleno."""
    assert agente_tablero.registrar_jugador("jugador1@hub") == "X"
    assert agente_tablero.registrar_jugador("jugador2@hub") == "O"
    assert agente_tablero.registrar_jugador("jugador3@hub") == "full"


def test_validacion_movimiento(agente_tablero):
    """Acepta libres y rechaza ocupadas."""
    assert agente_tablero.es_movimiento_valido(4) is True
    agente_tablero.tablero[4] = "X"
    assert agente_tablero.es_movimiento_valido(4) is False


def test_deteccion_victoria_lineas(agente_tablero):
    """Verifica que la función detecta las 8 posibles líneas ganadoras."""
    lineas = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Filas
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columnas
        [0, 4, 8], [2, 4, 6]  # Diagonales
    ]

    for linea in lineas:
        # Creamos un tablero vacío
        tablero = [""] * 9
        # Rellenamos la línea ganadora con "X"
        for pos in linea:
            tablero[pos] = "X"

        assert comprobar_ganador(tablero) == "X", f"Falló al detectar la victoria en la línea {linea}"


def test_deteccion_empate(agente_tablero):
    """Verifica que detecta empate cuando no hay huecos."""
    agente_tablero.tablero = ["X", "O", "X", "X", "O", "O", "O", "X", "X"]

    # 1. Comprobamos que el tablero detecta que está lleno
    assert agente_tablero.hay_empate() is True

    # 2. Comprobamos que no hay ningún ganador en ese tablero
    assert comprobar_ganador(agente_tablero.tablero) is None