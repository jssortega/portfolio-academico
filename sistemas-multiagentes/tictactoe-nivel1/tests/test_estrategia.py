import pytest
from typing import List

from estrategia.estrategia_nivel3 import elegir_movimiento


def test_tablero_vacio() -> None:
    """Verifica que ante un tablero vacío, devuelve una posición válida (0-8)."""
    tablero_vacio: List[str] = ["", "", "", "", "", "", "", "", ""]
    movimiento: int = elegir_movimiento(tablero_vacio, "X")

    es_valido: bool = 0 <= movimiento <= 8 and tablero_vacio[movimiento] == ""
    assert es_valido, "El movimiento en un tablero vacío debe ser válido y en una casilla libre."


def test_posicion_valida_casilla_libre() -> None:
    """Verifica que la función devuelve siempre una posición válida en una casilla libre."""
    tablero: List[str] = ["X", "O", "", "", "X", "", "O", "", ""]
    movimiento: int = elegir_movimiento(tablero, "O")

    es_valido: bool = 0 <= movimiento <= 8 and tablero[movimiento] == ""
    assert es_valido, "El movimiento debe realizarse obligatoriamente en una casilla libre."


def test_tablero_casi_lleno() -> None:
    """Ante un tablero con una sola casilla libre, devuelve exactamente esa casilla."""
    tablero: List[str] = ["X", "O", "X", "O", "O", "X", "X", "", "O"]
    movimiento: int = elegir_movimiento(tablero, "X")

    assert movimiento == 7, "Si solo hay una casilla libre, debe elegir esa forzosamente."


def test_aprovecha_oportunidad_ganar() -> None:
    """Si nivel >= 2: Ante una oportunidad inminente de ganar, la aprovecha."""
    # "X" tiene la oportunidad de ganar en la posición 2 (fila superior)
    tablero: List[str] = ["X", "X", "", "O", "O", "", "", "", ""]
    movimiento: int = elegir_movimiento(tablero, "X")

    assert movimiento == 2, "La estrategia debe aprovechar un movimiento ganador (nivel >= 2)."


def test_bloquea_amenaza_rival() -> None:
    """Si nivel >= 2: Ante una amenaza del rival, la bloquea."""
    # "X" amenaza con ganar en la posición 5 (fila central). "O" debe bloquear.
    tablero: List[str] = ["", "", "", "X", "X", "", "O", "", ""]
    movimiento: int = elegir_movimiento(tablero, "O")

    assert movimiento == 5, "La estrategia debe bloquear una victoria inminente del rival (nivel >= 2)."


def test_funcion_es_pura() -> None:
    """La función no modifica el tablero de entrada (es pura)."""
    tablero_original: List[str] = ["X", "", "O", "", "X", "", "", "", ""]
    # Hacemos una copia profunda manual para comparar después
    tablero_copia: List[str] = tablero_original.copy()

    _ = elegir_movimiento(tablero_original, "O")

    assert tablero_original == tablero_copia, "La función elegir_movimiento no debe mutar el tablero de entrada."


def test_funciona_para_ambos_simbolos() -> None:
    """La función trabaja correctamente tanto para el símbolo 'X' como para el 'O'."""
    tablero: List[str] = ["X", "O", "X", "", "", "", "O", "X", "O"]

    # Probamos jugando como "X"
    movimiento_x: int = elegir_movimiento(tablero, "X")
    es_valido_x: bool = tablero[movimiento_x] == ""

    # Probamos jugando como "O"
    movimiento_o: int = elegir_movimiento(tablero, "O")
    es_valido_o: bool = tablero[movimiento_o] == ""

    assert es_valido_x and es_valido_o, "La estrategia debe devolver posiciones libres independientemente del símbolo."