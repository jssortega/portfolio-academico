"""Verificación visual de la configuración del alumno.

Este script no conecta con el servidor XMPP ni arranca ningún agente:
lee ``config/config.yaml`` y ``config/agents.yaml``, aplica la misma
normalización que usa el lanzador (``main.py``) y muestra por
pantalla:

1. La sala MUC destino, con el nombre ya canonizado a la forma
   común (``pc-NN`` para el submodo individual del examen,
   ``examen`` para el submodo grupo, etc.).
2. La lista de agentes que se generarán a partir de la
   configuración actual, indicando para cada uno su nombre, su rol
   (tablero o jugador) y el nick MUC único que la utilidad
   asignará en la sala.

Sirve para que el alumno compruebe, antes del día del examen, que
los campos ``alumno.pc``, ``alumno.nick_tablero`` y
``alumno.nick_jugador`` producen exactamente los nicks que espera
ver en el panel del supervisor.

Uso desde la raíz del proyecto::

    python scripts/verificar_configuracion.py
    python scripts/verificar_configuracion.py --config config/config.yaml

El script no requiere conectividad con la UJA: todo se calcula a
partir de los ficheros locales.
"""
import argparse
import logging
import sys
from pathlib import Path

# Permite ejecutar el script tanto con ``python
# scripts/verificar_configuracion.py`` como con ``python -m
# scripts.verificar_configuracion``, asegurando que la raíz del
# proyecto está en sys.path antes de importar los módulos del
# alumno.
_RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
if str(_RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROYECTO))

from config.configuracion import (   # noqa: E402
    cargar_configuracion,
    cargar_plantillas,
    generar_agentes,
)

# ── Constantes de formato del informe ───────────────────────────
# Anchura de las columnas de la tabla que se imprime por consola.
# Se eligen valores cómodos para nicks de hasta ~24 caracteres y
# nombres JID locales de longitud típica (tablero_alumno_NN).
_ANCHO_NOMBRE = 36
_ANCHO_ROL = 8
_ANCHO_NICK = 28

# Cabecera de la tabla (en español). El separador se construye
# dinámicamente con la suma de las anchuras + los espacios entre
# columnas para mantener la coherencia si se ajusta alguna.
_CABECERA_TABLA = (
    f"{'Nombre del agente':<{_ANCHO_NOMBRE}}"
    f"  {'Rol':<{_ANCHO_ROL}}"
    f"  {'Nick MUC':<{_ANCHO_NICK}}"
)


def _parsear_argumentos() -> argparse.Namespace:
    """Analiza los argumentos de la línea de órdenes del script.

    Returns:
        Namespace con la ruta al config.yaml y al agents.yaml.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Imprime la sala MUC destino y los nicks que la "
            "utilidad asignará a los agentes del alumno a partir "
            "de la configuración actual, sin conectar con el "
            "servidor XMPP."
        ),
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Ruta al fichero de configuración del alumno.",
    )
    parser.add_argument(
        "--agents",
        default="config/agents.yaml",
        help="Ruta al fichero de plantillas de agentes.",
    )
    return parser.parse_args()


def _clasificar_rol(nombre_agente: str) -> str:
    """Determina si un agente generado es un tablero o un jugador.

    La función se apoya en el patrón de nombres que produce
    ``generar_agentes``: ``tablero_<usuario>_NN`` y
    ``jugador_<usuario>_n<L>_NN``. No se importan constantes del
    módulo de configuración para mantener el script independiente
    de cambios menores en el formato.

    Args:
        nombre_agente: Parte local del JID del agente.

    Returns:
        ``"Tablero"``, ``"Jugador"`` o ``"-"`` si no encaja.
    """
    if nombre_agente.startswith("tablero_"):
        return "Tablero"
    elif nombre_agente.startswith("jugador_"):
        return "Jugador"
    else:
        return "-"


def _imprimir_resumen_sala(config_xmpp: dict, seccion_alumno: dict) -> None:
    """Imprime el bloque cabecera con la sala MUC destino y los datos
    del alumno relevantes para el modo examen.

    Args:
        config_xmpp: Perfil XMPP resuelto.
        seccion_alumno: Bloque ``alumno`` del config.yaml.
    """
    modalidad = seccion_alumno.get("modalidad", "?")
    submodo = seccion_alumno.get("submodo", "")
    usuario = seccion_alumno.get("usuario_uja", "?")
    pc_original = seccion_alumno.get("pc", "")

    sala_muc = config_xmpp.get("sala_muc_completa", "?")
    servicio_muc = config_xmpp.get("servicio_muc", "?")
    sala_local = config_xmpp.get("sala_tictactoe", "?")

    print("═" * 78)
    print("  Verificación de la configuración del alumno")
    print("═" * 78)
    print(f"  Usuario UJA          : {usuario}")
    print(f"  Modalidad            : {modalidad}")
    if modalidad == "examen":
        print(f"  Submodalidad         : {submodo or '(no indicada)'}")
        if submodo == "individual":
            print(
                f"  Puesto escrito       : '{pc_original}'  "
                f"→  normalizado: '{sala_local}'"
            )
    print(f"  Componente MUC       : {servicio_muc}")
    print(f"  Sala MUC destino     : {sala_muc}")
    print("─" * 78)


def _imprimir_tabla_agentes(agentes: list[dict]) -> None:
    """Imprime la tabla de agentes generados con su nick MUC.

    Args:
        agentes: Lista de definiciones tal como devuelve
            ``generar_agentes``.
    """
    print(_CABECERA_TABLA)
    print("─" * len(_CABECERA_TABLA))

    contador_tableros = 0
    contador_jugadores = 0
    nicks_vistos: set[str] = set()
    nicks_duplicados: set[str] = set()

    for agente in agentes:
        nombre = agente.get("nombre", "")
        parametros = agente.get("parametros", {})
        nick = parametros.get("nick_muc", "—")
        rol = _clasificar_rol(nombre)

        if rol == "Tablero":
            contador_tableros += 1
        elif rol == "Jugador":
            contador_jugadores += 1

        if nick in nicks_vistos:
            nicks_duplicados.add(nick)
        else:
            nicks_vistos.add(nick)

        print(
            f"{nombre:<{_ANCHO_NOMBRE}}  "
            f"{rol:<{_ANCHO_ROL}}  "
            f"{nick:<{_ANCHO_NICK}}"
        )

    print("─" * len(_CABECERA_TABLA))
    print(
        f"  Total: {len(agentes)} agentes "
        f"({contador_tableros} tableros, {contador_jugadores} jugadores)"
    )

    if nicks_duplicados:
        print(
            "  ⚠ ATENCIÓN: hay nicks duplicados → "
            + ", ".join(sorted(nicks_duplicados))
        )
    else:
        print("  ✓ Todos los nicks son únicos.")
    print("═" * 78)


def main() -> None:
    """Punto de entrada del script."""
    # El script imprime su propia salida tabulada por consola; el
    # logging de los módulos importados se limita a WARNING para
    # que no se mezcle con la tabla.
    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    argumentos = _parsear_argumentos()

    config = cargar_configuracion(argumentos.config)
    plantillas = cargar_plantillas(argumentos.agents)
    agentes = generar_agentes(config, plantillas)

    _imprimir_resumen_sala(config["xmpp"], config.get("alumno", {}))
    _imprimir_tabla_agentes(agentes)


if __name__ == "__main__":
    main()
