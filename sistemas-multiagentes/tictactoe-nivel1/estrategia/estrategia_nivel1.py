"""
Estrategia para elegir movimiento de nivel 1
"""

def elegir_movimiento(tablero: list[str], mi_simbolo: str) -> int:
    """
    Metodo que elige el mejor movimiento asignadole valores a las zonas del tablero
    """

    #Aqui se asigna los valores a las posiciones, el centro por ejemplo es la que mayor valor tiene
    puntuaciones = {
        0: 3, 1: 1, 2: 3,
        3: 1, 4: 4, 5: 1,
        6: 3, 7: 1, 8: 3,
    }

    mejor_posicion = -1
    mejor_puntuacion = -1

    #Mira las posiciones libres y se queda con la de mejor puntuacion
    for i in range(len(tablero)):
        if tablero[i] == "":
            if puntuaciones[i] > mejor_puntuacion:
                mejor_puntuacion = puntuaciones[i]
                mejor_posicion = i

    return mejor_posicion