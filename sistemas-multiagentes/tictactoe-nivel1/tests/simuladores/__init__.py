"""Arnés de simulación para las pruebas de protocolo del alumno.

Este paquete reúne todo lo necesario para verificar los agentes
del alumno **sin** un servidor XMPP real:

* :class:`SalaSimulada` — una sala MUC en memoria.
* :func:`montar_agente` — crea el agente del alumno con la
  factoría y lo conecta a la sala simulada.
* :class:`TableroSimulado`, :class:`JugadorSimulado` y
  :class:`SupervisorSimulado` — oráculos del comportamiento
  esperado del agente contrario.

Uso típico desde un fichero de prueba::

    from tests.simuladores import (
        SalaSimulada, montar_agente, TableroSimulado,
        ejecutar_escenario, acelerar_tiempos,
    )
"""
from tests.simuladores.arnes import (
    SALA_DE_PRUEBA,
    AgenteMontado,
    acelerar_tiempos,
    anunciar_tablero_descubierto,
    detener_tareas,
    ejecutar_escenario,
    montar_agente,
    perfil_xmpp_de_prueba,
)
from tests.simuladores.jugador_simulado import JugadorSimulado
from tests.simuladores.sala_simulada import (
    MensajeEntrante,
    RegistroMensaje,
    SalaSimulada,
)
from tests.simuladores.supervisor_simulado import SupervisorSimulado
from tests.simuladores.tablero_simulado import TableroSimulado

__all__ = [
    "SALA_DE_PRUEBA",
    "AgenteMontado",
    "JugadorSimulado",
    "MensajeEntrante",
    "RegistroMensaje",
    "SalaSimulada",
    "SupervisorSimulado",
    "TableroSimulado",
    "acelerar_tiempos",
    "anunciar_tablero_descubierto",
    "detener_tareas",
    "ejecutar_escenario",
    "montar_agente",
    "perfil_xmpp_de_prueba",
]