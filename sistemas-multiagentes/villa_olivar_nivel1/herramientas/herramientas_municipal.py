"""
Herramientas ADK — Servicios Municipales Villa Olivar.

Envuelve las funciones puras de logica/logica_municipal.py como FunctionTool
de ADK. Estas herramientas permiten que el LLM del agente municipal procese
alertas y solicitudes de recursos de otros agentes.
"""

from google.adk.tools import FunctionTool

from logica.logica_municipal import (
    procesar_alerta_municipal,
    procesar_solicitud_municipal,
)


herramienta_procesar_alerta_municipal = FunctionTool(procesar_alerta_municipal)
herramienta_procesar_solicitud_municipal = FunctionTool(procesar_solicitud_municipal)


herramientas_municipal = [
    herramienta_procesar_alerta_municipal,
    herramienta_procesar_solicitud_municipal,
]