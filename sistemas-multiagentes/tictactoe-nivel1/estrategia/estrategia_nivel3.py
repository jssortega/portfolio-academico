"""
Estrategia para elegir movimiento de nivel 3
"""

def elegir_movimiento(tablero: list[str], mi_simbolo: str) -> int:
    """
    Metodo que elige el mejor movimiento usando Minimax poda alfa-beta
    """

    simbolo_rival = "O" if mi_simbolo == "X" else "X"

    def comprobar_ganador(tablero: list[str], simbolo: str) -> bool:
        filas = [
            [tablero[0], tablero[1], tablero[2]],
            [tablero[3], tablero[4], tablero[5]],
            [tablero[6], tablero[7], tablero[8]],
        ]
        columnas = [
            [tablero[0], tablero[3], tablero[6]],
            [tablero[1], tablero[4], tablero[7]],
            [tablero[2], tablero[5], tablero[8]],
        ]
        diagonales = [
            [tablero[0], tablero[4], tablero[8]],
            [tablero[2], tablero[4], tablero[6]],
        ]
        lineas = filas + columnas + diagonales
        for linea in lineas:
            if linea == [simbolo, simbolo, simbolo]:
                return True
        return False

    def hay_empate(tab: list[str]) -> bool:
        return all(casilla != "" for casilla in tab)

    def minimax(tab: list[str], profundidad: int, es_maximizador: bool, alfa: int, beta: int) -> int:
        if comprobar_ganador(tab, mi_simbolo):
            return 10 - profundidad
        if comprobar_ganador(tab, simbolo_rival):
            return profundidad - 10
        if hay_empate(tab):
            return 0

        if es_maximizador:
            mejor_valor = -1000
            for i in range(9):
                if tab[i] == "":
                    tab[i] = mi_simbolo
                    valor = minimax(tab, profundidad + 1, False, alfa, beta)
                    tab[i] = ""
                    mejor_valor = max(mejor_valor, valor)
                    alfa = max(alfa, mejor_valor)
                    if beta <= alfa:
                        break
            return mejor_valor
        else:
            mejor_valor = 1000
            for i in range(9):
                # CORRECCIÓN: Usamos ""[cite: 6]
                if tab[i] == "":
                    tab[i] = simbolo_rival
                    valor = minimax(tab, profundidad + 1, True, alfa, beta)
                    tab[i] = ""
                    mejor_valor = min(mejor_valor, valor)
                    beta = min(beta, mejor_valor)
                    if beta <= alfa:
                        break
            return mejor_valor

    mejor_movimiento = -1
    mejor_valor = -1000

    for i in range(9):
        if tablero[i] == "":
            tablero[i] = mi_simbolo
            valor = minimax(tablero, 0, False, -1000, 1000)
            tablero[i] = ""

            if valor > mejor_valor:
                mejor_valor = valor
                mejor_movimiento = i

    return mejor_movimiento