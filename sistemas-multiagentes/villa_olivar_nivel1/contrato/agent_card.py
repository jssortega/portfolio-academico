"""Modelo Pydantic de la Agent Card del protocolo A2A.

La Agent Card es un documento JSON que describe la identidad, las
capacidades y las habilidades de un agente. Se publica en la URL
estándar `/.well-known/agent.json` para que otros agentes puedan
descubrirlo. Este modelo recoge los campos que el contrato del
proyecto Villa Olivar considera obligatorios o relevantes; el campo
`extra="ignore"` permite que los agentes incluyan campos adicionales
del estándar A2A sin que la validación los rechace.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# Identificadores reconocibles en una habilidad: en el contrato del
# proyecto exigimos al menos un identificador y un nombre legible por
# habilidad para favorecer el descubrimiento por rol entre grupos.
LONGITUD_MINIMA_IDENTIFICADOR = 1
LONGITUD_MINIMA_NOMBRE = 1


class Capacidades(BaseModel):
    """Capacidades de transporte declaradas por el agente.

    El estándar A2A admite varias capacidades; en Villa Olivar la más
    relevante es `streaming`, que indica si el agente acepta el
    extremo `tasks/sendSubscribe` para entregar eventos intermedios.
    """

    model_config = ConfigDict(extra="ignore")

    streaming: bool = Field(
        default=False,
        description="Indica si el agente admite transmisión continua mediante SSE.",
    )
    pushNotifications: bool = Field(
        default=False,
        description="Indica si el agente puede emitir notificaciones empujadas.",
    )


class Habilidad(BaseModel):
    """Habilidad declarada por el agente en su Agent Card.

    Cada habilidad describe una capacidad concreta del agente con un
    identificador único, un nombre legible y una descripción. Las
    etiquetas (`tags`) permiten filtrar y agrupar habilidades durante
    el descubrimiento entre grupos.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(
        min_length=LONGITUD_MINIMA_IDENTIFICADOR,
        description="Identificador único de la habilidad dentro del agente.",
    )
    name: str = Field(
        min_length=LONGITUD_MINIMA_NOMBRE,
        description="Nombre legible para personas.",
    )
    description: str = Field(
        description="Descripción del propósito y alcance de la habilidad.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Etiquetas semánticas que facilitan el filtrado por rol.",
    )


class AgentCard(BaseModel):
    """Tarjeta de presentación del agente publicada en `/.well-known/agent.json`.

    Recoge los campos que cualquier agente del sistema Villa Olivar
    debe exponer para ser descubrible por la Centralita del propio
    grupo, por la Centralita de otros grupos y por el coordinador del
    profesor. La presencia de al menos una habilidad coherente con
    el rol del agente es condición necesaria para superar el Hito 1.
    """

    model_config = ConfigDict(extra="ignore")

    name: str = Field(
        min_length=1,
        description="Nombre identificativo del agente.",
    )
    description: str = Field(
        description="Descripción del propósito y alcance del agente.",
    )
    url: HttpUrl = Field(
        description="URL HTTP completa donde el agente atiende peticiones A2A.",
    )
    version: str = Field(
        min_length=1,
        description="Versión semántica del agente, por ejemplo `1.0.0`.",
    )
    capabilities: Capacidades = Field(
        default_factory=Capacidades,
        description="Capacidades de transporte declaradas por el agente.",
    )
    skills: list[Habilidad] = Field(
        min_length=1,
        description="Lista de habilidades del agente; debe contener al menos una.",
    )
    defaultInputModes: Optional[list[str]] = Field(
        default=None,
        description="Modos de entrada admitidos, por ejemplo `application/json`.",
    )
    defaultOutputModes: Optional[list[str]] = Field(
        default=None,
        description="Modos de salida admitidos.",
    )
