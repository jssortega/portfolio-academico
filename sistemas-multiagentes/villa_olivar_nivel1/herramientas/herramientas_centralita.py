"""
Herramientas ADK para el agente Centralita — Villa Olivar (Nivel 2).

Envuelve las funciones puras de logica/logica_centralita.py como
FunctionTool de Google ADK, que la clase base AgenteVillaOlivarLLM
convierte internamente a LLMTool de SPADE-LLM.

El LLM lee el nombre, la descripción (docstring) y los type hints
de cada función para decidir cuándo y cómo invocarla. Por eso los
docstrings de las funciones envueltas son descriptivos y precisos:
son información operativa para el LLM, no solo documentación interna.

Autor(es): Cristina Silva (csu0002@ujaen.es), Jesús Ortega Castillo (joc00023@ujaen.es)
Grupo: multi007s
"""

from google.adk.tools import FunctionTool

from logica.logica_centralita import (
    clasificar_emergencia,
    determinar_destinatarios,
    generar_id_emergencia,
)


def _crear_herramientas_centralita() -> list[FunctionTool]:
    """Construye y devuelve la lista de FunctionTool para la Centralita.

    Cada FunctionTool envuelve una función pura de logica_centralita.py.
    El LLM usa el docstring y los type hints de la función envuelta para
    decidir cuándo invocarla y con qué parámetros.

    Returns:
        Lista de FunctionTool lista para pasar a registrar_herramientas_adk().
    """
    return [
        FunctionTool(clasificar_emergencia),
        FunctionTool(determinar_destinatarios),
        FunctionTool(generar_id_emergencia),
    ]


# Lista de herramientas que se pasa a AgenteVillaOlivarLLM.registrar_herramientas_adk().
# La clase base las convierte a LLMTool y las registra en el LLMAgent de SPADE-LLM.
herramientas_centralita: list[FunctionTool] = _crear_herramientas_centralita()

# Alias individuales para tests y uso directo
herramienta_clasificar: FunctionTool = herramientas_centralita[0]
herramienta_destinatarios: FunctionTool = herramientas_centralita[1]
herramienta_generar_id: FunctionTool = herramientas_centralita[2]