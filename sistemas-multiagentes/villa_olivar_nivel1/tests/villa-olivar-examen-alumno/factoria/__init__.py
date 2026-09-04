"""Factoría de agentes A2A homogénea para el alumno.

Este paquete reúne las clases base y utilidades que aseguran que
todos los grupos de alumnos arranquen sus agentes con la misma
estructura externa: misma forma de Agent Card, mismo extremo
``tasks/send``, mismo esquema de Agent Card publicada en
``/.well-known/agent.json`` y mismo registro en el directorio REST
del aula. Esa homogeneidad es necesaria para que el Coordinador
del profesor pueda evaluar a todos los grupos sin adaptar la
lógica del cliente.

El alumno **no** debe modificar este paquete. Cualquier
adaptación específica del grupo se hace extendiendo las clases
base o registrando ``handlers`` propios a través de los puntos de
extensión documentados (``manejar_alerta``, ``construir_agent_card``).
"""

from factoria.agente_a2a import AgenteA2A, EspecificacionAgente
from factoria.lanzador import arrancar_agentes_desde_configuracion

__all__ = [
    "AgenteA2A",
    "EspecificacionAgente",
    "arrancar_agentes_desde_configuracion",
]
