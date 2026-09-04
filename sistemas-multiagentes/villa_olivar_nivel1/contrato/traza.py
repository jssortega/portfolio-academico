"""Modelo Pydantic de la traza de participación.

Cada `InformeResolucion` que la Centralita devuelve al coordinador
del profesor lleva, como evidencia obligatoria, una lista ordenada
de eventos del tipo `EventoTraza` que documenta paso a paso qué
agente del grupo intervino, en qué instante, con qué visibilidad y
qué hizo. Esta lista es el principal artefacto que el coordinador
cruza con los criterios de cada hito (descritos en
`doc/HITOS_EVALUACION.md`) para decidir si una inyección supera o
no el hito asociado.

La traza es también la única manera en que un agente **privado**
deja constancia de su intervención frente al coordinador externo:
los privados no se exponen en la red del aula ni se registran en
el directorio público, así que su existencia y participación solo
se pueden inferir a partir de los eventos `visibilidad = "privado"`
que la Centralita incluya en la traza.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# Patrón al que debe ajustarse el campo `accion`: identificador
# estable en `snake_case` para que el coordinador pueda agregar
# por tipo de acción al evaluar los hitos.
PATRON_ACCION = r"^[a-z_][a-z0-9_]*$"

# Longitud mínima del campo `detalle` (texto libre legible).
LONGITUD_MINIMA_DETALLE = 1

# Longitud mínima de `agente_id` y `grupo_externo`.
LONGITUD_MINIMA_IDENTIFICADOR = 1


class VisibilidadAgente(str, Enum):
    """Visibilidad de un agente desde la perspectiva del coordinador.

    Coincide con el modelo de visibilidad del Nivel 3
    (`doc/AGENTES_A2A.md`): los agentes **públicos** se registran en
    el directorio REST y son alcanzables por el coordinador; los
    **privados** solo son alcanzables a través de la Centralita
    propia del grupo, por el mecanismo que el grupo elija.
    """

    PUBLICO = "publico"
    PRIVADO = "privado"


class RolAgente(str, Enum):
    """Roles posibles de un agente en la traza de participación.

    Es una extensión de `RolEspecialista` (de `contrato.tipos`) que
    incorpora el rol implícito `centralita`. Los valores textuales
    coinciden con el catálogo del registro REST
    (`doc/registro_rest_para_clientes.md`) para evitar divergencia
    entre los modelos Pydantic y la inscripción de los agentes
    públicos en el directorio del aula.
    """

    CENTRALITA = "centralita"
    BOMBEROS = "bomberos"
    SANITARIO = "sanitario"
    POLICIA = "policia"
    MUNICIPAL = "municipal"


class EventoTraza(BaseModel):
    """Una entrada de la traza de participación del `InformeResolucion`.

    Cada evento documenta una acción concreta de un agente del grupo
    durante la resolución de la emergencia. La secuencia de eventos
    debe permitir al coordinador reconstruir, en orden temporal, qué
    roles intervinieron, con qué visibilidad y qué hicieron.

    En **escenarios colaborativos** (cuando la `AlertaEmergencia`
    original llega a varias Centralitas, véase
    `AlertaEmergencia.coordinacion`), los eventos relacionados con
    la coordinación con otros grupos deben llevar el campo opcional
    `grupo_externo` para que el coordinador pueda cruzar las trazas
    de los grupos participantes y validar la coherencia
    colaborativa.
    """

    model_config = ConfigDict(extra="ignore")

    instante: datetime = Field(
        description="Instante en que ocurre el evento, en formato ISO 8601 "
                    "(idealmente con milisegundos y zona UTC). Los eventos de la "
                    "traza deben ir en orden monótonamente creciente.",
    )
    agente_id: str = Field(
        min_length=LONGITUD_MINIMA_IDENTIFICADOR,
        description="Identificador único del agente que ejecuta la acción. Para "
                    "los públicos coincide con el `agente_id` registrado en el "
                    "directorio REST; para los privados es un identificador "
                    "interno del grupo, decidido por el propio grupo.",
    )
    rol: RolAgente = Field(
        description="Rol funcional del agente (incluye `centralita`).",
    )
    visibilidad: VisibilidadAgente = Field(
        description="Visibilidad del agente: `publico` si está registrado en el "
                    "directorio REST; `privado` si solo es accesible a través de "
                    "la Centralita propia del grupo.",
    )
    accion: str = Field(
        pattern=PATRON_ACCION,
        description="Identificador semántico de la acción en `snake_case` "
                    "(p. ej. `recibir_alerta`, `evaluar_situacion`, "
                    "`coordinar_con_grupo`). Debe ser un valor estable para "
                    "permitir agregación por tipo de acción al evaluar el hito.",
    )
    detalle: str = Field(
        min_length=LONGITUD_MINIMA_DETALLE,
        description="Descripción legible de la acción (p. ej. mensaje al LLM, "
                    "decisión tomada, recurso desplegado).",
    )
    grupo_externo: Optional[str] = Field(
        default=None,
        min_length=LONGITUD_MINIMA_IDENTIFICADOR,
        description="En escenarios colaborativos, identifica al grupo externo "
                    "(`id_grupo`) con el que se ha intercambiado información "
                    "en esta acción. Ausente en eventos intra-grupo.",
    )
