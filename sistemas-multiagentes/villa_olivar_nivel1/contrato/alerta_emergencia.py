"""Modelo Pydantic de la alerta de emergencia entrante.

Este es el cuerpo de la petición que el coordinador del profesor envía
a la Centralita 112 del grupo a través del extremo A2A `tasks/send`.
La Centralita debe procesarlo, clasificar la emergencia y orquestar
la respuesta de los especialistas.

El contrato es deliberadamente sencillo en los campos obligatorios
para que la Centralita pueda atender alertas con información mínima.
Los campos opcionales permiten enriquecer la alerta cuando el
informador dispone de más datos.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Longitud mínima del texto de la alerta. Una cadena vacía o un único
# carácter no se considera una alerta procesable.
LONGITUD_MINIMA_TEXTO = 3

# Longitud mínima de un identificador de grupo en `coordinacion`.
LONGITUD_MINIMA_ID_GRUPO = 1

# Longitud mínima del código de hito en `hito_evaluado`.
LONGITUD_MINIMA_HITO = 1

# Rangos válidos para coordenadas geográficas en grados decimales.
LATITUD_MINIMA = -90.0
LATITUD_MAXIMA = 90.0
LONGITUD_MINIMA_GRADOS = -180.0
LONGITUD_MAXIMA_GRADOS = 180.0


class Ubicacion(BaseModel):
    """Localización de la emergencia.

    Compuesta por una dirección textual y, opcionalmente, coordenadas
    geográficas. La dirección textual es siempre obligatoria porque
    representa la información que el informador típicamente
    proporciona al servicio de emergencias.

    El modelo admite campos extra silenciosamente (`extra="ignore"`)
    para favorecer la tolerancia a la entrada conforme al principio
    de robustez.
    """

    model_config = ConfigDict(extra="ignore")

    direccion: str = Field(min_length=1, description="Dirección textual de la emergencia.")
    latitud: Optional[float] = Field(
        default=None,
        ge=LATITUD_MINIMA,
        le=LATITUD_MAXIMA,
        description="Latitud en grados decimales, si está disponible.",
    )
    longitud: Optional[float] = Field(
        default=None,
        ge=LONGITUD_MINIMA_GRADOS,
        le=LONGITUD_MAXIMA_GRADOS,
        description="Longitud en grados decimales, si está disponible.",
    )


class AlertaEmergencia(BaseModel):
    """Alerta de emergencia que llega a la Centralita 112.

    Los campos obligatorios son `id_emergencia` (correlador único
    generado por el coordinador externo) y `texto` (descripción
    libre redactada por quien reporta la emergencia). El resto son
    opcionales y aportan contexto adicional. La Centralita debe ser
    capaz de procesar la alerta aunque solo reciba `id_emergencia`
    y `texto`; la **clasificación** (`tipo_emergencia`, `prioridad`)
    es responsabilidad de la Centralita y aparece en el
    `InformeResolucion` resultante.

    Los campos `hito_evaluado` y `coordinacion` los aporta el
    coordinador del profesor para que la Centralita pueda dejar
    constancia del hito al que se dirige la inyección y reconocer
    los escenarios colaborativos (cuando `coordinacion` contiene
    más de un `id_grupo`).

    Los campos no contemplados en este modelo se ignoran
    silenciosamente, conforme al principio de tolerancia en la
    entrada: un cliente puede enviar campos adicionales sin que la
    petición sea rechazada.
    """

    model_config = ConfigDict(extra="ignore")

    id_emergencia: UUID = Field(
        description="Identificador único de la emergencia (UUID v4) generado por "
                    "el coordinador externo. Sirve como correlador entre la alerta "
                    "y el InformeResolucion que la Centralita devolverá.",
    )
    texto: str = Field(
        min_length=LONGITUD_MINIMA_TEXTO,
        description="Descripción libre de la emergencia tal como la reporta el informador.",
    )
    ubicacion: Optional[Ubicacion] = Field(
        default=None,
        description="Localización de la emergencia, si se conoce.",
    )
    momento: Optional[datetime] = Field(
        default=None,
        description="Instante en que se notifica la alerta, en formato ISO 8601.",
    )
    informador: Optional[str] = Field(
        default=None,
        description="Identificador opcional de quien reporta la emergencia.",
    )
    hito_evaluado: Optional[str] = Field(
        default=None,
        min_length=LONGITUD_MINIMA_HITO,
        description="Código del hito de evaluación al que va dirigida esta inyección "
                    "(p. ej. 'H3-E5'). La Centralita debe dejar constancia de él "
                    "en la traza de participación del informe resultante; no necesita "
                    "interpretarlo para decidir cómo resolver la emergencia.",
    )
    coordinacion: list[str] = Field(
        default_factory=list,
        description="Lista de identificadores de grupo (`id_grupo`) involucrados en el escenario. "
                    "Cuando contiene un único elemento, el escenario es individual: solo el "
                    "grupo listado debe atender la emergencia. Cuando contiene dos o más, el "
                    "escenario es colaborativo: la misma alerta llega a las Centralitas de "
                    "todos los grupos listados dentro de una ventana corta, y la resolución "
                    "requiere cooperación entre ellos. Una lista vacía equivale a la lista "
                    "que contiene solo el id del grupo destinatario.",
    )
