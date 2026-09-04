"""Conjuntos cerrados de valores admitidos por el contrato externo.

Estos tipos enumerados acotan los valores que pueden aparecer en los
campos categóricos de los mensajes A2A intercambiados entre la
Centralita y los especialistas. Cualquier valor fuera de estos
conjuntos se considera una violación del contrato y debe ser
detectada por las pruebas.

El uso de `str` como clase base permite que los modelos Pydantic
acepten tanto el valor enumerado (`TipoEmergencia.INCENDIO`) como su
representación textual (`"incendio"`) sin pérdida de información.
"""

from enum import Enum


class TipoEmergencia(str, Enum):
    """Categorías de emergencias atendidas por el sistema.

    El conjunto se mantiene cerrado de forma deliberada para que la
    clasificación sea verificable. La categoría `OTRO` actúa como
    válvula de escape para alertas que no encajan en ninguna de las
    cinco categorías principales.
    """

    INCENDIO = "incendio"
    ACCIDENTE_TRAFICO = "accidente_trafico"
    DERRAME_QUIMICO = "derrame_quimico"
    INUNDACION = "inundacion"
    DERRUMBE = "derrumbe"
    OTRO = "otro"


class Prioridad(str, Enum):
    """Niveles de prioridad asignables a una emergencia.

    El orden semántico es `BAJA < MEDIA < ALTA < CRITICA`. La
    Centralita asigna la prioridad inicial y, en ocasiones, los
    especialistas pueden recomendar elevarla durante la atención.
    """

    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class RolEspecialista(str, Enum):
    """Roles de los cuatro especialistas del sistema.

    Cada grupo expone exactamente dos de estos roles como agentes
    públicos y mantiene los otros dos como privados. La Centralita
    es siempre pública y no figura en este conjunto: tiene su propio
    rol implícito `centralita` (véase `RolAgente` en
    `contrato.traza` para el enumerado que incluye también la
    Centralita y se usa en `EventoTraza`).

    Los valores textuales (`bomberos`, `sanitario`, `policia`,
    `municipal`) coinciden con el catálogo del registro REST
    declarado en `doc/registro_rest_para_clientes.md` para evitar
    divergencia entre los modelos Pydantic del contrato y la
    inscripción de los agentes públicos en el directorio del aula.
    """

    BOMBEROS = "bomberos"
    SANITARIO = "sanitario"
    POLICIA = "policia"
    MUNICIPAL = "municipal"


class EstadoTask(str, Enum):
    """Estados del ciclo de vida de una Task A2A.

    Los nombres conservan la grafía original del protocolo A2A para
    facilitar la correspondencia con la especificación. La transición
    permitida es:

        SUBMITTED -> WORKING -> COMPLETED | FAILED | INPUT_REQUIRED
        INPUT_REQUIRED -> WORKING (al recibir el dato faltante)
        cualquiera -> CANCELED (al recibir cancelación)
    """

    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class EstadoFinal(str, Enum):
    """Resultado final de la atención de una emergencia.

    Resume el desenlace agregado tras la coordinación con todos los
    especialistas. No coincide necesariamente con `EstadoTask`: una
    Task puede terminar en `COMPLETED` con un `EstadoFinal.PARCIAL`
    si parte de los especialistas no pudieron intervenir.
    """

    RESUELTA = "resuelta"
    PARCIAL = "parcial"
    NO_RESUELTA = "no_resuelta"
