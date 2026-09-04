"""Modelo Pydantic del estado de un agente público.

Cuerpo de la respuesta del Protocolo 2: cada agente público devuelve
su estado actual al coordinador del profesor cuando recibe una
`ConsultaEstado` (véase `contrato.consulta_estado`).

El modelo es deliberadamente sencillo y deja al grupo la libertad
de etiquetar el campo `estado` con su propia jerarquía interna
(`libre`, `ocupado`, `esperando_recurso`, etc.) mientras la cadena
sea estable a lo largo de la sesión y permita al coordinador
distinguir operatividad de degradación.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from contrato.traza import RolAgente


# Longitud mínima de los campos textuales identificadores.
LONGITUD_MINIMA_IDENTIFICADOR = 1
LONGITUD_MINIMA_ESTADO = 1


class EstadoAgente(BaseModel):
    """Estado actual de un agente público en respuesta a una `ConsultaEstado`.

    Los tres campos obligatorios (`agente_id`, `rol`, `estado`) son
    suficientes para alimentar la pestaña de estados del panel del
    supervisor. `emergencia_actual` y `detalle` enriquecen la
    respuesta cuando el agente está ocupado o quiere comunicar una
    advertencia.

    `momento` es opcional para tolerar respuestas de agentes que no
    rellenan ese campo; cuando está presente, debe ir en formato
    ISO 8601.
    """

    model_config = ConfigDict(extra="ignore")

    agente_id: str = Field(
        min_length=LONGITUD_MINIMA_IDENTIFICADOR,
        description="Identificador del agente que responde, idéntico al `agente_id` "
                    "con el que se registró en el directorio REST.",
    )
    rol: RolAgente = Field(
        description="Rol funcional del agente (incluye `centralita`).",
    )
    estado: str = Field(
        min_length=LONGITUD_MINIMA_ESTADO,
        description="Estado actual del agente (p. ej. `libre`, `ocupado`, "
                    "`esperando_recurso`, `degradado`). Cadena libre acordada "
                    "por el grupo, pero estable a lo largo de la sesión.",
    )
    emergencia_actual: Optional[UUID] = Field(
        default=None,
        description="`id_emergencia` que está atendiendo el agente en este "
                    "instante, si procede; ausente si está libre.",
    )
    detalle: Optional[str] = Field(
        default=None,
        description="Texto libre opcional con información adicional sobre el "
                    "estado (p. ej. unidad desplegada, ETA, motivo de degradación).",
    )
    momento: Optional[datetime] = Field(
        default=None,
        description="Instante en que se generó la respuesta, en formato ISO 8601.",
    )
