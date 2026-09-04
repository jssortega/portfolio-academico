"""Modelo Pydantic del informe de actuación de un especialista.

Este es el cuerpo que un especialista (Bomberos, Sanitario, Policía,
Servicios Municipales) devuelve a la Centralita tras atender la
subtarea que le ha sido encomendada. La Centralita lo agrega junto
con los informes del resto de especialistas para componer el
`InformeResolucion` final.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from contrato.tipos import RolEspecialista


# Cota inferior del número de acciones que puede registrar un
# especialista. Cero acciones es un valor válido cuando el
# especialista determina que no hay nada que hacer en su ámbito.
NUMERO_MINIMO_ACCIONES = 0


class InformeActuacion(BaseModel):
    """Informe que un especialista devuelve a la Centralita.

    El conjunto de campos refleja la información mínima que la
    Centralita necesita para agregar la respuesta: quién ha actuado,
    si la actuación se ha completado o no, qué acciones se han
    realizado y qué recursos se han empleado. El campo
    `observaciones` permite al especialista añadir comentarios
    relevantes para el coordinador externo o para los grupos vecinos.

    El modelo admite campos extra silenciosamente, lo que permite a
    los grupos enriquecer su informe interno sin romper el contrato.
    """

    model_config = ConfigDict(extra="ignore")

    rol: RolEspecialista = Field(
        description="Rol del especialista que emite el informe.",
    )
    completado: bool = Field(
        description="Indica si la actuación del especialista ha terminado correctamente.",
    )
    acciones_realizadas: list[str] = Field(
        default_factory=list,
        description="Lista de acciones concretas ejecutadas por el especialista.",
    )
    recursos_empleados: list[str] = Field(
        default_factory=list,
        description="Lista de recursos humanos o materiales movilizados.",
    )
    observaciones: Optional[str] = Field(
        default=None,
        description="Texto libre con comentarios o advertencias relevantes.",
    )
