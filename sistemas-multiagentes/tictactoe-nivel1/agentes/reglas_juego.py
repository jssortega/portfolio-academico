"""Reglas del tres en raya — lógica pura, sin SPADE ni red.

Este módulo reúne las funciones con las que tanto el agente
tablero como el agente jugador razonan sobre el estado de una
partida: validar una posición, aplicar un movimiento, detectar
una línea ganadora y decidir el resultado de un turno.

Se mantiene **separado de los agentes** por dos motivos
didácticos:

1. La lógica del juego puede probarse de forma aislada, sin
   levantar ningún agente ni servidor XMPP.
2. Ningún agente duplica las reglas: el tablero y el jugador
   comparten exactamente la misma definición de victoria y
   empate, de modo que sus evaluaciones nunca discrepan.

El vocabulario de los resultados (``continue``, ``win``,
``draw``) y la representación del tablero (lista de nueve
cadenas, con ``""`` para la casilla vacía) coinciden con los
campos de la ontología, para que el valor calculado aquí pueda
incorporarse directamente a un mensaje ``turn-result`` o
``game-report`` sin conversiones.
"""
from typing import Optional

# ── Representación del tablero ─────────────────────────────────
# El tablero es una lista de nueve posiciones (índices 0-8), leída
# de izquierda a derecha y de arriba abajo:
#       0 | 1 | 2
#       3 | 4 | 5
#       6 | 7 | 8
NUM_CASILLAS = 9

# Marca de una casilla todavía sin ocupar. Es la cadena vacía para
# que coincida con el campo 'board' del informe de la ontología.
CASILLA_VACIA = ""

# Símbolos (fichas) válidos de los dos jugadores.
SIMBOLO_X = "X"
SIMBOLO_O = "O"

# Las ocho líneas que producen una victoria: tres filas, tres
# columnas y dos diagonales.
LINEAS_GANADORAS = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),   # filas
    (0, 3, 6), (1, 4, 7), (2, 5, 8),   # columnas
    (0, 4, 8), (2, 4, 6),              # diagonales
)

# ── Vocabulario de resultados (campo 'result' de la ontología) ──
RESULTADO_CONTINUA = "continue"
RESULTADO_VICTORIA = "win"
RESULTADO_EMPATE = "draw"

# Orden de preferencia de la estrategia posicional (nivel 1): se
# ocupa primero el centro, después las esquinas y por último los
# lados. Es una heurística sencilla y reproducible que el alumno
# sustituye por su estrategia real en los niveles 2, 3 y 4.
_PREFERENCIA_POSICIONAL = (4, 0, 2, 6, 8, 1, 3, 5, 7)


def crear_tablero_vacio() -> list[str]:
    """Devuelve un tablero nuevo con las nueve casillas vacías."""
    return [CASILLA_VACIA] * NUM_CASILLAS


def posicion_en_rango(posicion: int) -> bool:
    """Indica si ``posicion`` es un índice de casilla válido (0-8)."""
    return 0 <= posicion < NUM_CASILLAS


def posicion_libre(tablero: list[str], posicion: int) -> bool:
    """Indica si la casilla ``posicion`` existe y está sin ocupar.

    Args:
        tablero: Lista de nueve cadenas con el estado del tablero.
        posicion: Índice de casilla que se quiere comprobar.

    Returns:
        ``True`` solo si el índice está en rango y la casilla
        correspondiente está vacía.
    """
    es_libre = posicion_en_rango(posicion) and (
        tablero[posicion] == CASILLA_VACIA
    )
    return es_libre


def aplicar_movimiento(
    tablero: list[str], posicion: int, simbolo: str,
) -> list[str]:
    """Devuelve una copia del tablero con ``simbolo`` en ``posicion``.

    No modifica el tablero recibido: trabajar sobre una copia evita
    efectos colaterales cuando varios fragmentos del código
    comparten la misma lista.

    Args:
        tablero: Estado de partida antes del movimiento.
        posicion: Casilla donde se coloca la ficha (debe estar
            libre; el llamador lo verifica con
            :func:`posicion_libre`).
        simbolo: Ficha que se coloca (``"X"`` u ``"O"``).

    Returns:
        Un tablero nuevo con el movimiento ya aplicado.
    """
    nuevo_tablero = list(tablero)
    nuevo_tablero[posicion] = simbolo
    return nuevo_tablero


def hay_linea(tablero: list[str], simbolo: str) -> bool:
    """Indica si ``simbolo`` completa alguna de las ocho líneas."""
    completada = False
    for linea in LINEAS_GANADORAS:
        if all(tablero[casilla] == simbolo for casilla in linea):
            completada = True
    return completada


def tablero_completo(tablero: list[str]) -> bool:
    """Indica si no queda ninguna casilla vacía en el tablero."""
    return all(casilla != CASILLA_VACIA for casilla in tablero)


def contar_fichas(tablero: list[str]) -> int:
    """Devuelve cuántas casillas del tablero están ocupadas."""
    return sum(1 for casilla in tablero if casilla != CASILLA_VACIA)


def evaluar_resultado(
    tablero: list[str], simbolo: str,
) -> tuple[str, Optional[str]]:
    """Evalúa el tablero tras un movimiento del jugador ``simbolo``.

    Es la función que el jugador activo usa para construir el
    mensaje ``turn-result`` de la ontología, y que el tablero usa
    para decidir si la partida termina.

    Args:
        tablero: Estado del tablero ya con el último movimiento
            aplicado.
        simbolo: Ficha del jugador que acaba de mover.

    Returns:
        Una tupla ``(resultado, ganador)``:

        * ``("win", simbolo)`` si ``simbolo`` ha completado línea.
        * ``("draw", None)`` si el tablero está lleno sin línea.
        * ``("continue", None)`` si la partida debe continuar.

        El vocabulario coincide con el campo ``result`` de la
        acción ``turn-result`` de la ontología.
    """
    if hay_linea(tablero, simbolo):
        resultado: tuple[str, Optional[str]] = (RESULTADO_VICTORIA, simbolo)
    elif tablero_completo(tablero):
        resultado = (RESULTADO_EMPATE, None)
    else:
        resultado = (RESULTADO_CONTINUA, None)
    return resultado


def elegir_posicion(tablero: list[str]) -> int:
    """Elige una casilla libre con la estrategia posicional (nivel 1).

    Recorre las casillas en el orden de preferencia centro →
    esquinas → lados y devuelve la primera que esté libre. Es una
    estrategia deliberadamente simple: garantiza un movimiento
    legal y reproducible. El alumno la sustituye por su estrategia
    real (reglas, minimax o LLM) en su agente jugador.

    Args:
        tablero: Estado actual del tablero.

    Returns:
        Índice de la casilla elegida, o ``-1`` si el tablero está
        completo (situación que el llamador debe haber descartado
        antes comprobando el resultado del turno anterior).
    """
    eleccion = -1
    for posicion in _PREFERENCIA_POSICIONAL:
        if eleccion == -1 and posicion_libre(tablero, posicion):
            eleccion = posicion
    return eleccion
