"""Accesorios (*fixtures*) compartidos por las pruebas de integración.

Estas pruebas son **de caja negra contra el sistema real** del grupo:
cada test envía Tasks A2A reales por HTTP a la Centralita del grupo
y, cuando procede, directamente a los especialistas públicos. La
implementación interna del grupo se trata como opaca; solo se
observa el contrato externo: estructura del ``InformeResolucion``,
ciclo de vida de las Tasks y respuestas a peticiones JSON-RPC.

Mientras el grupo no haya arrancado su sistema, las pruebas
**fallan** con un error de conexión (``httpx.ConnectError``) o
expiran por tiempo de espera. Esto es deliberado: las pruebas
sirven como guía iterativa de avance (véase
el plan de pruebas mantenido en la rama del profesor) y el primer hito que el grupo
debe alcanzar es justamente que estas pruebas dejen de fallar por
falta de servicio.

Configuración por fichero del grupo
-----------------------------------

Como la elección de qué especialistas son públicos y cuáles privados
es decisión de cada grupo, las pruebas no pueden fijar literalmente
en el código las URL del grupo. El grupo declara su mapeo en el
**bloque ``evaluacion:`` de ``config/config.yaml``** (la plantilla
de este bloque viene comentada en el propio fichero para que el
alumno la descomente y la ajuste).

La URL del registro REST se reaprovecha del bloque ``red`` ya
existente (``red.perfiles[<perfil_activo>].registro_central``),
de modo que no hay que duplicarla en el bloque ``evaluacion``.

Las pruebas leen el ``config.yaml`` a través de la fixture
:func:`configuracion_grupo`. Las variables de entorno
``CENTRALITA_URL``, ``REGISTRO_REST_URL`` y similares siguen
aceptándose como sustitución puntual para entornos de integración
continua: si están definidas, prevalecen sobre el contenido del
fichero.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Optional
from uuid import UUID, uuid4

import httpx
import pytest
import pytest_asyncio
import yaml
from aiohttp import web

from cliente_pruebas.cliente import ClienteCoordinador
from contrato.tipos import EstadoTask, RolEspecialista


# Tiempo de espera generoso para las llamadas HTTP. El sistema del
# grupo invoca a un LLM remoto (Gemini u Ollama) durante el
# procesamiento de la alerta; el valor debe absorber ese retardo
# sin enmascarar caídas reales del servicio.
TIEMPO_ESPERA_SEGUNDOS = 60.0

# URL por defecto cuando ni el fichero de configuración ni la
# variable de entorno aportan un valor. Coincide con el puerto
# convencional de la Centralita en el arranque local descrito en
# ``doc/AGENTES_A2A.md``.
URL_CENTRALITA_POR_DEFECTO = "http://localhost:8110"

# URL por defecto del registro REST del aula.
URL_REGISTRO_POR_DEFECTO = "http://sinbad2.ujaen.es:8020"

# Ruta relativa del fichero de configuración único del alumno
# dentro del proyecto. Toda la configuración vive en
# ``config/config.yaml``; el bloque ``evaluacion`` de ese fichero
# es el que las pruebas del profesor leen.
RUTA_RELATIVA_FICHERO_CONFIGURACION = Path("config") / "config.yaml"


@dataclass
class ConfiguracionGrupo:
    """Vista estructurada del bloque ``evaluacion`` de ``config/config.yaml``.

    Reúne en un único objeto las URL declaradas por el grupo y las
    expone con accesores tipados. Los campos opcionales toman valores
    seguros (``dict`` vacío) cuando el grupo no declara un bloque,
    de modo que las pruebas que los necesitan puedan omitirse con
    ``pytest.skip`` sin propagar ``AttributeError``.
    """

    url_centralita: str
    publicos_por_rol: dict[RolEspecialista, str] = field(default_factory=dict)
    privados_por_rol: dict[RolEspecialista, str] = field(default_factory=dict)
    url_registro_central: str = URL_REGISTRO_POR_DEFECTO

    def url_publico(self, rol: RolEspecialista) -> Optional[str]:
        """URL declarada por el grupo para el especialista público del rol."""
        url = self.publicos_por_rol.get(rol)
        return url

    def url_privado(self, rol: RolEspecialista) -> Optional[str]:
        """URL local declarada por el grupo para el especialista privado del rol."""
        url = self.privados_por_rol.get(rol)
        return url

    def primer_publico_disponible(self) -> Optional[tuple[RolEspecialista, str]]:
        """Devuelve cualquier especialista público declarado, si lo hay."""
        candidato = next(iter(self.publicos_por_rol.items()), None)
        return candidato

    def primer_privado_disponible(self) -> Optional[tuple[RolEspecialista, str]]:
        """Devuelve cualquier especialista privado declarado, si lo hay."""
        candidato = next(iter(self.privados_por_rol.items()), None)
        return candidato


def _ruta_fichero_configuracion() -> Path:
    """Localiza el ``config/config.yaml`` del grupo.

    Busca la ruta relativa ``config/config.yaml`` desde el
    directorio actual hacia arriba, lo que permite ejecutar las
    pruebas desde cualquier subdirectorio del proyecto.
    """
    directorio = Path.cwd()
    candidatos = [directorio, *directorio.parents]
    ruta = next(
        (candidato / RUTA_RELATIVA_FICHERO_CONFIGURACION
         for candidato in candidatos
         if (candidato / RUTA_RELATIVA_FICHERO_CONFIGURACION).is_file()),
        directorio / RUTA_RELATIVA_FICHERO_CONFIGURACION,
    )
    return ruta


def _extraer_url_registro_del_bloque_red(datos: dict) -> Optional[str]:
    """Devuelve ``red.perfiles[<perfil_activo>].registro_central`` si existe."""
    bloque_red = datos.get("red") or {}
    perfil_activo = bloque_red.get("perfil_activo")
    perfiles = bloque_red.get("perfiles") or {}
    if not isinstance(perfil_activo, str) or perfil_activo not in perfiles:
        return None
    perfil = perfiles[perfil_activo] or {}
    url = perfil.get("registro_central")
    if isinstance(url, str) and url:
        return url
    return None


def _cargar_diccionario_yaml(ruta: Path) -> dict:
    """Lee el YAML como diccionario; devuelve dict vacío si el fichero no existe."""
    contenido: dict = {}
    if ruta.is_file():
        with ruta.open(encoding="utf-8") as origen:
            cargado = yaml.safe_load(origen)
            if isinstance(cargado, dict):
                contenido = cargado
    return contenido


def _convertir_a_rol_o_omitir(clave: str) -> Optional[RolEspecialista]:
    """Convierte una clave textual al enumerado ``RolEspecialista`` si encaja."""
    try:
        rol = RolEspecialista(clave)
    except ValueError:
        rol = None
    return rol


def _extraer_urls_por_rol(seccion: Optional[dict]) -> dict[RolEspecialista, str]:
    """Filtra las claves de la sección que se corresponden con roles válidos."""
    if not isinstance(seccion, dict):
        seccion = {}
    urls_por_rol: dict[RolEspecialista, str] = {}
    for clave, valor in seccion.items():
        rol = _convertir_a_rol_o_omitir(str(clave))
        if rol is not None and isinstance(valor, str) and valor:
            urls_por_rol[rol] = valor
    return urls_por_rol


@pytest.fixture(scope="session")
def configuracion_grupo() -> ConfiguracionGrupo:
    """Carga el bloque ``evaluacion`` de ``config/config.yaml``.

    El alumno declara el reparto de visibilidad en ese bloque (ver
    plantilla comentada al final de ``config/config.yaml``). La URL
    del registro REST se reaprovecha del bloque ``red`` ya existente.

    Las variables de entorno tienen precedencia sobre el contenido
    del fichero para facilitar la integración continua:

    - ``CENTRALITA_URL`` reemplaza la URL de la Centralita.
    - ``REGISTRO_REST_URL`` reemplaza la URL del registro central.
    - ``URL_BOMBEROS_PUBLICOS`` inscribe a bomberos como público con
      esa URL aunque el fichero diga otra cosa.
    - ``URL_PRIVADO_PROHIBIDO`` declara una URL como privada (rol
      ``policia`` por convención) cuando el bloque ``evaluacion``
      no aporta privados.
    """
    ruta = _ruta_fichero_configuracion()
    datos = _cargar_diccionario_yaml(ruta)
    bloque_evaluacion = datos.get("evaluacion") or {}

    url_centralita = (
        os.environ.get("CENTRALITA_URL")
        or (bloque_evaluacion.get("centralita") or {}).get("url")
        or URL_CENTRALITA_POR_DEFECTO
    )
    url_registro = (
        os.environ.get("REGISTRO_REST_URL")
        or _extraer_url_registro_del_bloque_red(datos)
        or URL_REGISTRO_POR_DEFECTO
    )
    publicos = _extraer_urls_por_rol(bloque_evaluacion.get("publicos"))
    privados = _extraer_urls_por_rol(bloque_evaluacion.get("privados"))

    # Compatibilidad hacia atrás con las dos variables de entorno
    # documentadas en la versión anterior del conftest.
    url_bomberos_entorno = os.environ.get("URL_BOMBEROS_PUBLICOS")
    if url_bomberos_entorno:
        publicos[RolEspecialista.BOMBEROS] = url_bomberos_entorno
    url_privado_entorno = os.environ.get("URL_PRIVADO_PROHIBIDO")
    if url_privado_entorno and not privados:
        privados[RolEspecialista.POLICIA] = url_privado_entorno

    configuracion = ConfiguracionGrupo(
        url_centralita=url_centralita,
        publicos_por_rol=publicos,
        privados_por_rol=privados,
        url_registro_central=url_registro,
    )
    return configuracion


@pytest.fixture
def url_centralita(configuracion_grupo: ConfiguracionGrupo) -> str:
    """URL base de la Centralita 112 del grupo evaluado."""
    return configuracion_grupo.url_centralita


@pytest.fixture
def url_registro_central(configuracion_grupo: ConfiguracionGrupo) -> str:
    """URL del registro REST del aula."""
    return configuracion_grupo.url_registro_central


@pytest.fixture
def url_especialista_publico_bomberos(
    configuracion_grupo: ConfiguracionGrupo,
) -> str:
    """URL del especialista de bomberos público (Hito 5).

    Si el grupo no ha declarado bomberos como público en el
    bloque ``evaluacion`` de ``config/config.yaml``, omite la
    prueba: no toda configuración expone bomberos como público y
    forzar su existencia condicionaría las decisiones de diseño.
    """
    url = configuracion_grupo.url_publico(RolEspecialista.BOMBEROS)
    if url is None:
        pytest.skip(
            "El grupo no declara bomberos como público en el bloque "
            "`evaluacion` de `config/config.yaml`; la prueba se omite.",
        )
    return url


@pytest.fixture
def url_agente_privado_prohibido(
    configuracion_grupo: ConfiguracionGrupo,
) -> str:
    """URL local declarada por el grupo para un agente privado.

    Devuelve la URL del primer privado declarado en el bloque
    ``evaluacion`` de ``config/config.yaml``. Sin declaración no
    se puede comprobar el aislamiento sin acceder al código fuente,
    así que la prueba se omite.
    """
    candidato = configuracion_grupo.primer_privado_disponible()
    if candidato is None:
        pytest.skip(
            "El grupo no declara ninguna URL de agente privado en el "
            "bloque `evaluacion` de `config/config.yaml`; la prueba se omite.",
        )
    _, url = candidato
    return url


@pytest_asyncio.fixture
async def cliente_coordinador(
    url_registro_central: str,
) -> AsyncIterator[ClienteCoordinador]:
    """Cliente A2A asíncrono del coordinador con tiempo de espera real.

    Se construye con un ``httpx.AsyncClient`` real (sin transporte
    inyectado), de modo que las llamadas viajan por la red hasta
    el sistema del grupo.
    """
    async with httpx.AsyncClient(timeout=TIEMPO_ESPERA_SEGUNDOS) as cliente_http:
        cliente = ClienteCoordinador(
            cliente_http=cliente_http,
            url_registro=url_registro_central,
        )
        yield cliente


@pytest.fixture
def nuevo_identificador_emergencia() -> UUID:
    """Genera un UUID v4 nuevo por test."""
    identificador = uuid4()
    return identificador


@pytest.fixture
def identificador_task_prefijado(request: pytest.FixtureRequest) -> str:
    """Identificador de Task derivado del nombre del test, único por ejecución."""
    sufijo = uuid4().hex[:8]
    identificador = f"{request.node.name}-{sufijo}"
    return identificador


# ---------------------------------------------------------------------------
# Dobles A2A externos para los escenarios de cooperación entre grupos (H5).
#
# La cooperación cruzada del Hito 5 obliga al sistema del grupo a invocar a
# agentes públicos de **otros grupos**. Como en el banco de pruebas del
# coordinador no se puede dar por hecho que esos otros grupos estén
# arrancados, el conftest ofrece dobles A2A en proceso: pequeños servidores
# ``aiohttp`` que se levantan en puertos efímeros, se dan de alta en el
# registro REST si está accesible y responden a peticiones JSON-RPC con
# respuestas grabadas. Los tests los usan como **proveedores externos
# falsos** que el sistema del grupo evaluado debe descubrir y consumir.
# ---------------------------------------------------------------------------


# Direccionamiento por defecto del servidor doble. La IP ``127.0.0.1``
# (en lugar de ``0.0.0.0``) evita conflictos con cortafuegos cuando el
# desarrollador ejecuta las pruebas en su portátil.
HOST_DOBLE = "127.0.0.1"


@dataclass
class RegistroDeAccesos:
    """Contador de accesos al doble del registro REST.

    Permite a las pruebas verificar si el sistema del grupo consultó al
    registro durante la atención de una alerta determinada. El plan del
    Hito 5 exige que los escenarios intra-grupo (modalidad A) no generen
    tráfico al registro central.
    """

    consultas_get_agentes: int = 0
    altas: int = 0
    bajas: int = 0
    senales_vida: int = 0


@dataclass
class DobleServicio:
    """Representa un doble HTTP arrancado y su URL pública.

    Devuelve la URL en la forma ``http://127.0.0.1:<puerto>`` para que
    los tests puedan insertarla en la configuración del grupo evaluado
    (típicamente exportando ``URL_BOMBEROS_PUBLICOS`` o equivalente).
    """

    url: str
    runner: web.AppRunner


async def _crear_servidor_aiohttp(handlers: list[tuple[str, str, Callable]]) -> DobleServicio:
    """Crea y arranca un servidor aiohttp en un puerto efímero.

    Args:
        handlers: lista de tuplas (método HTTP, ruta, handler) a registrar.

    Returns:
        Una instancia de :class:`DobleServicio` con la URL y el runner.
    """
    aplicacion = web.Application()
    for metodo, ruta, handler in handlers:
        aplicacion.router.add_route(metodo, ruta, handler)
    runner = web.AppRunner(aplicacion)
    await runner.setup()
    sitio = web.TCPSite(runner, host=HOST_DOBLE, port=0)
    await sitio.start()
    socket_servidor = sitio._server.sockets[0]
    puerto_efimero = socket_servidor.getsockname()[1]
    url = f"http://{HOST_DOBLE}:{puerto_efimero}"
    doble = DobleServicio(url=url, runner=runner)
    return doble


@pytest_asyncio.fixture
async def grupo_externo_simulado(
    nuevo_identificador_emergencia: UUID,
) -> AsyncIterator[DobleServicio]:
    """Doble A2A de un especialista público "de otro grupo".

    Levanta un servidor que responde con:

    - ``/.well-known/agent.json``: Agent Card mínima con habilidades de
      bomberos público.
    - ``POST /``: cualquier petición JSON-RPC ``tasks/send`` se contesta
      con una Task ``completed`` que incluye un ``InformeResolucion`` con
      un evento ``apoyo_externo`` en la traza y ``grupo_externo``
      apuntando al identificador del grupo simulado.

    El test usa este doble para simular un grupo vecino al que el
    sistema del grupo evaluado debe delegar (escenario 8 del Hito 5).
    """
    identificador_grupo = "grupo-externo-simulado"

    async def manejar_agent_card(_: web.Request) -> web.Response:
        cuerpo = {
            "name": "bomberos_grupo_externo_simulado",
            "description": "Doble de bomberos público de un grupo externo.",
            "url": "<sustituido-en-fixture>",
            "version": "1.0.0",
            "skills": [
                {
                    "id": "extincion_apoyo",
                    "name": "Apoyo a extinción",
                    "description": "Apoyo entre grupos en escenarios de cascada.",
                    "tags": ["bomberos", "apoyo", "publico"],
                },
            ],
        }
        return web.json_response(cuerpo)

    async def manejar_tasks(peticion: web.Request) -> web.Response:
        cuerpo_peticion = await peticion.json()
        identificador_task = cuerpo_peticion.get("id", "task-doble")
        respuesta = {
            "jsonrpc": "2.0",
            "id": identificador_task,
            "result": {
                "id": identificador_task,
                "status": {"state": EstadoTask.COMPLETED.value},
                "history": [
                    {"state": EstadoTask.SUBMITTED.value},
                    {"state": EstadoTask.WORKING.value},
                    {"state": EstadoTask.COMPLETED.value},
                ],
                "artifacts": [
                    {
                        "parts": [
                            {
                                "type": "data",
                                "data": {
                                    "id_emergencia": str(nuevo_identificador_emergencia),
                                    "tipo_emergencia": "incendio",
                                    "prioridad": "alta",
                                    "estado_final": "resuelta",
                                    "informes_especialistas": [
                                        {
                                            "rol": "bomberos",
                                            "completado": True,
                                            "acciones_realizadas": ["apoyo_externo"],
                                            "recursos_empleados": ["dotacion_externa_01"],
                                            "observaciones": (
                                                f"Apoyo prestado por {identificador_grupo}"
                                            ),
                                        },
                                    ],
                                    "traza_participacion": [
                                        {
                                            "instante": "2026-05-16T17:32:11Z",
                                            "agente_id": "bomberos-externo",
                                            "rol": "bomberos",
                                            "visibilidad": "publico",
                                            "accion": "apoyo_externo",
                                            "detalle": "apoyo a extinción entre grupos",
                                            "grupo_externo": identificador_grupo,
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                ],
            },
        }
        return web.json_response(respuesta)

    doble = await _crear_servidor_aiohttp(
        handlers=[
            ("GET", "/.well-known/agent.json", manejar_agent_card),
            ("POST", "/", manejar_tasks),
        ],
    )
    try:
        yield doble
    finally:
        await doble.runner.cleanup()


@pytest_asyncio.fixture
async def grupo_externo_caido() -> AsyncIterator[DobleServicio]:
    """Doble que devuelve siempre ``500`` para simular un grupo caído.

    Útil para el escenario 9 del Hito 5 (indisponibilidad transitoria
    de la pareja externa): el sistema del grupo evaluado debe detectar
    el fallo y conmutar al respaldo o registrar la incidencia.
    """

    async def manejar(_: web.Request) -> web.Response:
        return web.Response(status=500, text="grupo simulado caído")

    doble = await _crear_servidor_aiohttp(
        handlers=[
            ("GET", "/.well-known/agent.json", manejar),
            ("POST", "/", manejar),
        ],
    )
    try:
        yield doble
    finally:
        await doble.runner.cleanup()


@pytest_asyncio.fixture
async def registro_central_instrumentado() -> AsyncIterator[tuple[DobleServicio, RegistroDeAccesos]]:
    """Doble del registro REST que cuenta los accesos recibidos.

    Permite verificar el escenario 10 del Hito 5: los escenarios A
    no deben generar tráfico al registro central. El test exporta la
    URL del doble como ``REGISTRO_REST_URL`` antes de invocar al
    sistema del grupo evaluado y, tras la ejecución, comprueba que
    el contador permanece en cero.

    Responde con la lista vacía a ``GET /agentes`` y acepta altas y
    bajas con respuesta 200 sin almacenar estado.
    """
    accesos = RegistroDeAccesos()

    async def manejar_get_agentes(_: web.Request) -> web.Response:
        accesos.consultas_get_agentes += 1
        return web.json_response([])

    async def manejar_alta(_: web.Request) -> web.Response:
        accesos.altas += 1
        return web.json_response({"resultado": "alta_ok"})

    async def manejar_baja(_: web.Request) -> web.Response:
        accesos.bajas += 1
        return web.json_response({"resultado": "baja_ok"})

    async def manejar_senal_vida(_: web.Request) -> web.Response:
        accesos.senales_vida += 1
        return web.json_response({"resultado": "ok"})

    doble = await _crear_servidor_aiohttp(
        handlers=[
            ("GET", "/agentes", manejar_get_agentes),
            ("POST", "/agentes", manejar_alta),
            ("DELETE", "/agentes/{id}", manejar_baja),
            ("POST", "/agentes/{id}/senal_vida", manejar_senal_vida),
        ],
    )
    try:
        yield doble, accesos
    finally:
        await doble.runner.cleanup()
