"""Comportamientos SPADE del supervisor del profesor.

Cada behaviour vive en su propio módulo para poder probarse de forma
aislada y para que la lectura del agente principal sea sencilla. Los
cuatro behaviours son:

- ``InyectorIncidentesBehaviour`` — Selecciona escenarios del catálogo
  y envía ``request`` con ``DatosEmergencia`` a la Centralita.
- ``ReceptorRespuestasBehaviour`` — Correlaciona las respuestas
  entrantes (``agree``, ``inform``, ``refuse``, ``not-understood``)
  con el seguimiento abierto y avanza el autómata.
- ``VigilanteTimeoutsBehaviour`` — Detecta seguimientos cuyo plazo
  ha caducado y los lleva a estado ``TIMEOUT``.
- ``SondeoEstadoBehaviour`` — Envía periódicamente ``query-ref`` a
  los agentes de cada grupo y registra los ``EstadoAgente``
  recibidos en la pestaña "Estados de agentes" del panel.
"""
from agente_profesor.comportamientos.inyector import (
    InyectorIncidentesBehaviour,
)
from agente_profesor.comportamientos.receptor import (
    ReceptorRespuestasBehaviour,
)
from agente_profesor.comportamientos.sondeo import (
    SondeoEstadoBehaviour,
)
from agente_profesor.comportamientos.vigilante import (
    VigilanteTimeoutsBehaviour,
)

__all__ = (
    "InyectorIncidentesBehaviour",
    "ReceptorRespuestasBehaviour",
    "SondeoEstadoBehaviour",
    "VigilanteTimeoutsBehaviour",
)
