"""Modelo Pydantic del informe de resolución agregado.

Este es el cuerpo que la Centralita 112 devuelve al coordinador del
profesor al cierre de la atención de una emergencia. Agrega la
clasificación inicial, los informes parciales de cada especialista
interviniente y el desenlace final.

El `InformeResolucion` es el principal artefacto observable del
contrato externo: las pruebas del profesor lo validan tanto en su
estructura (con este modelo Pydantic) como en su contenido
(comprobando coherencia con la alerta original y con los
especialistas esperados según el tipo de emergencia).
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from contrato.alerta_emergencia import Ubicacion
from contrato.informe_actuacion import InformeActuacion
from contrato.tipos import EstadoFinal, Prioridad, TipoEmergencia
from contrato.traza import EventoTraza


# La traza de participación debe contener al menos un evento
# (típicamente el de recepción de la alerta por la Centralita) para
# que el coordinador pueda validar el hito asociado a la inyección.
LONGITUD_MINIMA_TRAZA = 1


class InformeResolucion(BaseModel):
    """Informe agregado que devuelve la Centralita al coordinador.

    Reúne en un único documento la **clasificación final** de la
    emergencia (decidida por la Centralita a partir del `texto` de
    la `AlertaEmergencia`), los informes parciales de los
    especialistas que han intervenido, el resultado agregado y la
    **traza de participación** que sirve como evidencia para
    validar los hitos.

    El campo `id_emergencia` correlaciona el informe con la
    `AlertaEmergencia` original; el campo `traza_participacion`
    (obligatorio, no vacío) documenta, paso a paso, qué agente
    intervino, cuándo, con qué visibilidad y qué hizo.

    El campo `resumen` aporta una descripción legible para personas
    que no consumen el modelo programáticamente.
    """

    model_config = ConfigDict(extra="ignore")

    id_emergencia: UUID = Field(
        description="Identificador (UUID) de la AlertaEmergencia original con la "
                    "que se correlaciona este informe.",
    )
    tipo_emergencia: TipoEmergencia = Field(
        description="Clasificación final de la emergencia decidida por la Centralita.",
    )
    prioridad: Prioridad = Field(
        description="Prioridad asignada por la Centralita tras la coordinación.",
    )
    ubicacion: Optional[Ubicacion] = Field(
        default=None,
        description="Localización confirmada o inferida durante la atención.",
    )
    informes_especialistas: list[InformeActuacion] = Field(
        default_factory=list,
        description="Lista de informes parciales emitidos por los especialistas convocados.",
    )
    estado_final: EstadoFinal = Field(
        description="Resultado agregado de la atención de la emergencia.",
    )
    resumen: Optional[str] = Field(
        default=None,
        description="Descripción legible que resume la atención prestada.",
    )
    traza_participacion: list[EventoTraza] = Field(
        min_length=LONGITUD_MINIMA_TRAZA,
        description="Lista cronológicamente ordenada de eventos que documenta la "
                    "participación de cada agente del grupo durante la resolución. "
                    "Es la evidencia obligatoria que el coordinador externo usa "
                    "para validar el cumplimiento de los hitos descritos en "
                    "`doc/HITOS_EVALUACION.md`. Debe contener al menos un "
                    "evento; en la práctica, al menos uno por cada agente que "
                    "haya intervenido (público o privado) y, en escenarios "
                    "colaborativos, al menos uno por cada interacción con un "
                    "grupo externo.",
    )
