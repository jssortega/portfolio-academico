"""Modelo Pydantic de la consulta de estado del Protocolo 2.

Cuerpo que el coordinador del profesor envía a cualquiera de los
tres agentes públicos del grupo (Centralita y los dos especialistas
elegidos como públicos) para sondear su estado actual. La respuesta
del agente viene en un `EstadoAgente` (véase
`contrato.estado_agente`).

El sondeo es independiente del protocolo de inyección de alertas
(`AlertaEmergencia`): se ejecuta periódicamente durante toda la
sesión para alimentar la vista de *Estados de agentes* del panel
del supervisor.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# Valor canónico de la operación: en esta versión del contrato solo
# existe `consultar_estado`. Mantener el campo explícito facilita
# extender el protocolo en iteraciones futuras sin romper la
# compatibilidad hacia atrás.
OPERACION_CONSULTAR_ESTADO = "consultar_estado"


class ConsultaEstado(BaseModel):
    """Cuerpo de la consulta de estado dirigida a un agente público.

    Los tres campos son opcionales para que el sondeo más simple
    consista en una llamada A2A con un cuerpo prácticamente vacío.
    El campo `operacion` se conserva con un valor por defecto para
    permitir extender el protocolo en el futuro (p. ej. añadir un
    `consultar_capacidades`) sin alterar las pruebas existentes.

    La identificación del destinatario real la determina la URL a
    la que el coordinador envía la consulta; `rol_destino` es solo
    una verificación de coherencia opcional.
    """

    model_config = ConfigDict(extra="ignore")

    operacion: str = Field(
        default=OPERACION_CONSULTAR_ESTADO,
        description="Identificador de la operación; en esta versión del contrato "
                    "el único valor admitido es `consultar_estado`.",
    )
    rol_destino: Optional[str] = Field(
        default=None,
        description="Rol esperado del agente al que se dirige la consulta. "
                    "Permite al agente comprobar que la URL invocada coincide "
                    "con su propio rol.",
    )
    momento: Optional[datetime] = Field(
        default=None,
        description="Instante en que se emite la consulta, en formato ISO 8601.",
    )
