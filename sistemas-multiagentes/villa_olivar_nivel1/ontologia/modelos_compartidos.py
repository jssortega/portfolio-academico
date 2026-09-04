"""
Modelos Pydantic compartidos — Ontología Villa Olivar (Nivel 2).

Este fichero es de SOLO LECTURA. Contiene los modelos Pydantic que
constituyen el contrato de interfaz entre los agentes del grupo y el
agente supervisor del profesor.

Los grupos pueden extender estos modelos por herencia para añadir
campos internos, pero los campos base son obligatorios y no deben
modificarse.

Autor: Profesor de la asignatura
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ─── Enumeraciones compartidas ──────────────────────────────────────────────

class TipoEmergencia(str, Enum):
    """Tipos de emergencia reconocidos por el sistema."""
    INCENDIO = "incendio"
    DERRAME_QUIMICO = "derrame_quimico"
    ACCIDENTE_TRAFICO = "accidente_trafico"
    INUNDACION = "inundacion"
    DERRUMBE = "derrumbe"
    OTRO = "otro"


class Prioridad(str, Enum):
    """Niveles de prioridad de una emergencia."""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class EstadoActuacion(str, Enum):
    """Estados posibles de la actuación de un agente."""
    RECIBIDO = "recibido"
    EN_CAMINO = "en_camino"
    EN_ESCENA = "en_escena"
    ACTUANDO = "actuando"
    FINALIZADO = "finalizado"
    REQUIERE_APOYO = "requiere_apoyo"


# ─── Modelos Pydantic ───────────────────────────────────────────────────────

class Coordenadas(BaseModel):
    """Coordenadas geográficas (latitud, longitud) en grados decimales."""
    latitud: float = Field(description="Latitud en grados decimales (WGS84)")
    longitud: float = Field(description="Longitud en grados decimales (WGS84)")


class Ubicacion(BaseModel):
    """Ubicación de un incidente.

    Siempre lleva `direccion` (texto libre). Las `coordenadas` son
    opcionales: el supervisor las omite si el escenario del catálogo
    no las define.
    """
    direccion: str = Field(description="Dirección en texto libre")
    coordenadas: Optional[Coordenadas] = Field(
        default=None,
        description="Coordenadas geográficas, si se conocen.",
    )


class DatosEmergencia(BaseModel):
    """Datos de una emergencia inyectada por el supervisor.

    El supervisor envía este modelo a la Centralita del grupo mediante
    un mensaje FIPA-ACL con performativa 'request'.
    """
    tipo_mensaje: str = Field(default="alerta_emergencia")
    id_emergencia: str = Field(description="Identificador único del incidente")
    tipo_emergencia: TipoEmergencia
    ubicacion: Ubicacion = Field(description="Ubicación del incidente")
    prioridad: Prioridad
    descripcion: str = Field(description="Descripción en lenguaje natural")
    marca_temporal: datetime = Field(default_factory=datetime.now)


class RespuestaAgente(BaseModel):
    """Respuesta de un agente especialista al procesar una alerta.

    Los especialistas envían este modelo para informar de su estado
    y las acciones realizadas.
    """
    tipo_mensaje: str = Field(default="informe_actuacion")
    id_emergencia: str
    agente_origen: str = Field(description="JID o rol del agente que responde")
    estado: EstadoActuacion
    detalle: str = Field(description="Descripción de las acciones realizadas")
    recursos_desplegados: list[str] = Field(default_factory=list)
    marca_temporal: datetime = Field(default_factory=datetime.now)


class InformeResolucion(BaseModel):
    """Informe final que la Centralita envía al supervisor.

    Se envía con performativa 'inform' cuando el incidente se ha
    resuelto o se ha alcanzado un estado estable.
    """
    tipo_mensaje: str = Field(default="informe_resolucion")
    id_emergencia: str
    tipo_emergencia: TipoEmergencia
    prioridad: Prioridad
    estado_final: str = Field(description="Estado de cierre del incidente")
    resumen: str = Field(description="Resumen de la resolución")
    agentes_participantes: list[str] = Field(default_factory=list)
    acciones_realizadas: list[str] = Field(default_factory=list)
    marca_temporal: datetime = Field(default_factory=datetime.now)


class ConsultaEstado(BaseModel):
    """Consulta de estado que el supervisor envía a cualquier agente.

    Se envía con performativa 'query-ref'. El agente debe responder
    con un EstadoAgente.
    """
    tipo_mensaje: str = Field(default="consulta_estado")
    agente_destino: str = Field(description="JID o rol del agente consultado")
    marca_temporal: datetime = Field(default_factory=datetime.now)


class EstadoAgente(BaseModel):
    """Estado actual de un agente, en respuesta a una ConsultaEstado.

    Se envía con performativa 'inform' como respuesta a 'query-ref'.
    """
    tipo_mensaje: str = Field(default="estado_agente")
    agente: str = Field(description="JID o rol del agente")
    estado: str = Field(description="Estado actual (libre, ocupado, etc.)")
    emergencia_actual: Optional[str] = Field(
        default=None,
        description="ID de la emergencia que está gestionando, si aplica"
    )
    detalle: str = Field(
        default="",
        description="Información adicional sobre el estado"
    )
    marca_temporal: datetime = Field(default_factory=datetime.now)
