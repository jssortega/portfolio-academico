from google.adk.tools import FunctionTool

from logica.logica_sanitario import (
    verificarAlerta,
    procesarAlertaAceptada,
    procesarAlertaRechazada,
    atenderHeridos,
)


herramienta_verificar_alerta = FunctionTool(verificarAlerta)
herramienta_procesar_alerta_aceptada = FunctionTool(procesarAlertaAceptada)
herramienta_procesar_alerta_rechazada = FunctionTool(procesarAlertaRechazada)
herramienta_atender_heridos = FunctionTool(atenderHeridos)


herramientas_sanitario = [
    herramienta_verificar_alerta,
    herramienta_procesar_alerta_aceptada,
    herramienta_procesar_alerta_rechazada,
    herramienta_atender_heridos,
]