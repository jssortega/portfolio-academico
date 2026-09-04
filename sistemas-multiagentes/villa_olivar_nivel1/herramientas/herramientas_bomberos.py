"""
Herramientas ADK — Bomberos Villa Olivar.

Envuelve las funciones puras de logica/logica_bomberos.py como FunctionTool
de ADK. Estas herramientas permiten que el LLM del agente Bomberos evalúe
riesgos químicos, incendios, procese alertas y finalice intervenciones.

Autor: Jesús Ortega Castillo (joc00023@ujaen.es)
Grupo: multi007s
"""

from google.adk.tools import FunctionTool

from logica.logica_bomberos import (
    evaluar_riesgo_quimico,
    evaluar_incendio,
    procesar_alerta,
    finalizar_intervencion,
)


# Herramienta para evaluar derrames químicos.
# El LLM debe invocarla cuando la alerta describa sustancias como
# amoniaco, cloro o gasolina. Devuelve sustancia detectada, nivel de riesgo,
# radio de seguridad y si es necesario solicitar corte de gas.
herramienta_evaluar_riesgo_quimico = FunctionTool(evaluar_riesgo_quimico)


# Herramienta para evaluar incendios.
# El LLM debe invocarla cuando la alerta sea de tipo incendio o la descripción
# mencione fuego en casa, bosque, fábrica u otro entorno. Devuelve tipo/lugar
# afectado, nivel de riesgo, radio de seguridad y necesidad de corte de gas.
herramienta_evaluar_incendio = FunctionTool(evaluar_incendio)


# Herramienta principal de procesamiento de alertas.
# El LLM debe invocarla cuando reciba una alerta_emergencia completa.
# Devuelve la evaluación del riesgo, el informe para Centralita, la solicitud
# de perímetro para Policía y, si procede, la solicitud de corte de gas para
# Servicios Municipales.
herramienta_procesar_alerta_bomberos = FunctionTool(procesar_alerta)


# Herramienta para cerrar la intervención de Bomberos.
# El LLM debe invocarla cuando el peligro haya sido neutralizado y la zona
# pueda considerarse segura. Devuelve un informe_actuacion con estado finalizado.
herramienta_finalizar_intervencion_bomberos = FunctionTool(finalizar_intervencion)


# Lista de FunctionTool que se pasa a AgenteVillaOlivarLLM.registrar_herramientas_adk().
# La clase base las convierte a LLMTool y las registra en el LLMAgent de SPADE-LLM.
herramientas_bomberos = [
    herramienta_evaluar_riesgo_quimico,
    herramienta_evaluar_incendio,
    herramienta_procesar_alerta_bomberos,
    herramienta_finalizar_intervencion_bomberos,
]