from google.adk.tools import FunctionTool

from logica.logica_policia import (
    verificarAlerta,
    procesarAlertaAceptada,
    procesarAlertaRechazada,
    verificarPeticion,
    procesarPeticionAceptada,
    procesarPeticionRechazada,
)

herramientas_policia = [
    FunctionTool(verificarAlerta),
    FunctionTool(procesarAlertaAceptada),
    FunctionTool(procesarAlertaRechazada),
    FunctionTool(verificarPeticion),
    FunctionTool(procesarPeticionAceptada),
    FunctionTool(procesarPeticionRechazada),
]