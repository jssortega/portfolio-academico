"""Modelos Pydantic que definen el contrato externo del sistema Villa Olivar.

Este paquete agrupa los esquemas que la Centralita 112 y los especialistas
deben respetar al intercambiar mensajes A2A. Forma parte del bloque del
25 % de la batería automática descrito en `doc/HITOS_EVALUACION.md` de la
rama `desarrollo-nivel3` y se publica en la rama `evaluacion-profesor`
para que los grupos lo integren mediante fusión.

Los grupos no deben modificar los modelos: si una aserción fundada en
ellos falla, la corrección debe aplicarse en la implementación, no en
el contrato.
"""

from contrato.agent_card import AgentCard, Capacidades, Habilidad
from contrato.alerta_emergencia import AlertaEmergencia, Ubicacion
from contrato.consulta_estado import ConsultaEstado
from contrato.estado_agente import EstadoAgente
from contrato.informe_actuacion import InformeActuacion
from contrato.informe_resolucion import InformeResolucion
from contrato.tipos import EstadoFinal, EstadoTask, Prioridad, RolEspecialista, TipoEmergencia
from contrato.traza import EventoTraza, RolAgente, VisibilidadAgente

__all__ = [
    "AgentCard",
    "AlertaEmergencia",
    "Capacidades",
    "ConsultaEstado",
    "EstadoAgente",
    "EstadoFinal",
    "EstadoTask",
    "EventoTraza",
    "Habilidad",
    "InformeActuacion",
    "InformeResolucion",
    "Prioridad",
    "RolAgente",
    "RolEspecialista",
    "TipoEmergencia",
    "Ubicacion",
    "VisibilidadAgente",
]
