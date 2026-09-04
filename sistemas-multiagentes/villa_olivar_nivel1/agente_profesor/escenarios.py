"""Catálogo de escenarios deterministas del supervisor.

El supervisor inyecta escenarios tomados de un catálogo cerrado y
reproducible. Esta misma colección se usa para alimentar el modo
demo de la interfaz cuando se arranca sin XMPP, de manera que el
profesor pueda explorar el panel sin necesidad de un grupo vivo.

Cada escenario reutiliza un UUID v5 con un *espacio de nombres*
fijo, de modo que la clave del catálogo determina el
``id_emergencia`` resultante: dos arranques producen exactamente
los mismos identificadores y la batería de pruebas del grupo puede
usarlos con ``pytest.mark.parametrize`` sin sorpresas temporales.

El catálogo se carga desde ``dataset_incidencias.yaml`` (situado en
la carpeta del agente del profesor), que es la fuente de verdad
externa: añadir o ampliar incidencias se hace editando ese fichero,
sin tocar código Python.
"""
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from agente_profesor.seguimientos import (
    EstadoSeguimiento,
    EventoTimeline,
    Seguimiento,
)

# ─── Constantes simbólicas ──────────────────────────────────────────────────

# Espacio de nombres UUID v5 para generar id_emergencia reproducibles
# a partir de la clave del catálogo. No tiene significado externo:
# solo asegura que dos invocaciones produzcan el mismo identificador.
NAMESPACE_ESCENARIOS_VILLAOLIVAR = uuid.UUID(
    "ec7d1f3a-2c4f-5e6a-9b8c-0d1e2f3a4b5c",
)

GRUPO_DEMO_PRIMERO = "g04-fenix"
GRUPO_DEMO_SEGUNDO = "g11-olivar42"

# Ruta al fichero del catálogo de incidencias. Vive junto a este módulo
# para que el catálogo viaje con el código del supervisor del profesor.
RUTA_CATALOGO_INCIDENCIAS = (
    Path(__file__).resolve().parent / "dataset_incidencias.yaml"
)

# Campos obligatorios que cada incidencia del catálogo debe declarar.
CAMPOS_OBLIGATORIOS_INCIDENCIA = (
    "clave", "tipo_emergencia", "prioridad", "ubicacion", "descripcion",
)


# ─── Carga del catálogo desde el fichero YAML ───────────────────────────────

def _cargar_definiciones_escenarios() -> list[tuple[str, str, str, str, str]]:
    """Lee el catálogo de incidencias y devuelve la lista de tuplas.

    Validamos cada entrada para que un catálogo mal formado falle
    pronto y con un mensaje claro, en vez de propagar el error a la
    inyección del supervisor.
    """
    contenido = RUTA_CATALOGO_INCIDENCIAS.read_text(encoding="utf-8")
    datos = yaml.safe_load(contenido) or {}
    incidencias_brutas = datos.get("incidencias", [])

    definiciones: list[tuple[str, str, str, str, str]] = []
    claves_vistas: set[str] = set()
    for indice, entrada in enumerate(incidencias_brutas):
        for campo in CAMPOS_OBLIGATORIOS_INCIDENCIA:
            if campo not in entrada:
                raise ValueError(
                    f"Catálogo {RUTA_CATALOGO_INCIDENCIAS.name}: la "
                    f"incidencia #{indice} no declara el campo "
                    f"obligatorio '{campo}'.",
                )
        clave = entrada["clave"]
        if clave in claves_vistas:
            raise ValueError(
                f"Catálogo {RUTA_CATALOGO_INCIDENCIAS.name}: la clave "
                f"'{clave}' está duplicada. Las claves deben ser "
                "únicas porque alimentan el UUID v5 del id_emergencia.",
            )
        claves_vistas.add(clave)
        definiciones.append((
            clave,
            entrada["tipo_emergencia"],
            entrada["prioridad"],
            entrada["ubicacion"],
            entrada["descripcion"],
        ))

    if not definiciones:
        raise ValueError(
            f"Catálogo {RUTA_CATALOGO_INCIDENCIAS.name}: el catálogo "
            "está vacío. Define al menos una incidencia.",
        )
    return definiciones


# Cada entrada es (clave, tipo_emergencia, prioridad, ubicacion, descripcion).
# El orden y las claves se consideran parte del contrato público del
# supervisor (ver caracteristicas_para_tests_grupo.md §6). La fuente
# de verdad es el fichero YAML del catálogo; aquí guardamos la carga
# en caché al importar el módulo.
_DEFINICIONES_ESCENARIOS: list[tuple[str, str, str, str, str]] = (
    _cargar_definiciones_escenarios()
)


def construir_id_emergencia(clave: str) -> str:
    """Devuelve un ``id_emergencia`` reproducible a partir de la clave.

    Se usa UUID v5 con un namespace fijo para que dos llamadas con la
    misma clave produzcan el mismo identificador.
    """
    resultado = str(uuid.uuid5(
        NAMESPACE_ESCENARIOS_VILLAOLIVAR, clave,
    ))
    return resultado


def claves_escenarios() -> list[str]:
    """Lista de claves del catálogo en orden de declaración."""
    resultado = [definicion[0] for definicion in _DEFINICIONES_ESCENARIOS]
    return resultado


# ─── Datos demo para arranque sin XMPP ──────────────────────────────────────

def _seguimiento_demo(
    clave: str, grupo: str, estado: EstadoSeguimiento,
    minutos_atras: float, latencia_agree_ms: int,
    latencia_informe_ms: int = 0, error: str = "",
) -> Seguimiento:
    """Construye un seguimiento demo con marcas temporales coherentes.

    Las marcas temporales están desplazadas hacia atrás respecto al
    instante actual para que la línea de tiempo se vea natural en la
    interfaz incluso sin grupos vivos.
    """
    definicion = next(
        (d for d in _DEFINICIONES_ESCENARIOS if d[0] == clave),
        _DEFINICIONES_ESCENARIOS[0],
    )
    _, tipo_emergencia, prioridad, ubicacion, descripcion = definicion

    ahora = datetime.now()
    instante_creacion = ahora - timedelta(minutes=minutos_atras)
    instante_envio = instante_creacion + timedelta(milliseconds=50)
    instante_agree = instante_envio + timedelta(
        milliseconds=latencia_agree_ms,
    )
    instante_informe = None
    if latencia_informe_ms > 0:
        instante_informe = instante_agree + timedelta(
            milliseconds=latencia_informe_ms,
        )

    seguimiento = Seguimiento(
        id_emergencia=construir_id_emergencia(clave),
        grupo=grupo,
        jid_destino=f"centralita@{grupo}.localhost",
        tipo_emergencia=tipo_emergencia,
        prioridad=prioridad,
        descripcion=f"{ubicacion} — {descripcion}",
        estado=estado,
        instante_creacion=instante_creacion,
        instante_envio=instante_envio,
        instante_agree=instante_agree,
        instante_informe=instante_informe,
    )

    # Eventos coherentes con las marcas temporales de arriba
    seguimiento.eventos.append(EventoTimeline(
        instante=instante_creacion,
        tipo="estado:PREPARADO",
        detalle="Escenario seleccionado del catálogo",
    ))
    seguimiento.eventos.append(EventoTimeline(
        instante=instante_envio,
        tipo="estado:ENVIADO",
        detalle="Petición (request) enviada a la Centralita",
    ))
    seguimiento.eventos.append(EventoTimeline(
        instante=instante_agree,
        tipo="estado:ACEPTADO",
        detalle=f"Aceptación (agree) recibida en {latencia_agree_ms} ms",
    ))
    if estado == EstadoSeguimiento.RESUELTO:
        seguimiento.eventos.append(EventoTimeline(
            instante=instante_informe,
            tipo="estado:RESUELTO",
            detalle="InformeResolucion válido recibido",
        ))
        seguimiento.informe = {
            "tipo_mensaje": "informe_resolucion",
            "id_emergencia": seguimiento.id_emergencia,
            "tipo_emergencia": tipo_emergencia,
            "prioridad": prioridad,
            "estado_final": "resuelto",
            "resumen": (
                f"Datos de muestra: respuesta coordinada para "
                f"{tipo_emergencia}."
            ),
            "agentes_participantes": [
                f"bomberos@{grupo}.localhost",
                f"sanitario@{grupo}.localhost",
            ],
            "acciones_realizadas": [
                "Despliegue de unidad operativa",
                "Comunicación a la Centralita",
                "Cierre coordinado del incidente",
            ],
            "marca_temporal": instante_informe.isoformat(),
        }
    elif error:
        seguimiento.error = error
        seguimiento.eventos.append(EventoTimeline(
            instante=instante_agree + timedelta(seconds=2),
            tipo=f"estado:{estado.value}",
            detalle=error,
        ))

    return seguimiento


def construir_seguimientos_demo() -> list[Seguimiento]:
    """Genera una colección de seguimientos demo para el arranque.

    El objetivo es que el profesor vea el panel "vivo" desde el
    primer segundo, con incidentes en distintos estados terminales y
    de varios grupos. Los datos son deterministas: la misma invocación
    produce siempre la misma colección.
    """
    aleatorio = random.Random(42)

    resultado = [
        _seguimiento_demo(
            "incendio_alta", GRUPO_DEMO_PRIMERO,
            EstadoSeguimiento.RESUELTO,
            minutos_atras=12.0,
            latencia_agree_ms=380,
            latencia_informe_ms=23_500,
        ),
        _seguimiento_demo(
            "derrame_quimico_media", GRUPO_DEMO_PRIMERO,
            EstadoSeguimiento.RESUELTO,
            minutos_atras=8.0,
            latencia_agree_ms=420,
            latencia_informe_ms=18_200,
        ),
        _seguimiento_demo(
            "accidente_trafico_alta", GRUPO_DEMO_PRIMERO,
            EstadoSeguimiento.TIMEOUT,
            minutos_atras=5.5,
            latencia_agree_ms=510,
            error="No llegó InformeResolucion en 180 s",
        ),
        _seguimiento_demo(
            "incendio_critica", GRUPO_DEMO_SEGUNDO,
            EstadoSeguimiento.RESUELTO,
            minutos_atras=4.0,
            latencia_agree_ms=295,
            latencia_informe_ms=31_700,
        ),
        _seguimiento_demo(
            "inundacion_alta", GRUPO_DEMO_SEGUNDO,
            EstadoSeguimiento.FALLIDO,
            minutos_atras=2.5,
            latencia_agree_ms=470,
            error=(
                "El cuerpo del mensaje no se puede interpretar "
                "como InformeResolucion."
            ),
        ),
        _seguimiento_demo(
            "otro_baja", GRUPO_DEMO_SEGUNDO,
            EstadoSeguimiento.ACEPTADO,
            minutos_atras=0.4,
            latencia_agree_ms=aleatorio.randint(250, 600),
        ),
    ]

    return resultado


def grupos_demo() -> list[dict]:
    """Lista de grupos demo presentes en los seguimientos de muestra.

    Cada entrada incluye el JID supuesto de la Centralita para que la
    barra lateral del panel muestre la información completa.
    """
    resultado = [
        {
            "id": GRUPO_DEMO_PRIMERO,
            "nombre": GRUPO_DEMO_PRIMERO,
            "jid_centralita": f"centralita@{GRUPO_DEMO_PRIMERO}.localhost",
            "descripcion": "Grupo de muestra del banco de pruebas.",
        },
        {
            "id": GRUPO_DEMO_SEGUNDO,
            "nombre": GRUPO_DEMO_SEGUNDO,
            "jid_centralita": f"centralita@{GRUPO_DEMO_SEGUNDO}.localhost",
            "descripcion": "Segundo grupo de muestra.",
        },
    ]
    return resultado
