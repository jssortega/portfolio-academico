"""Handlers HTTP del dashboard del supervisor del profesor.

Replica los patrones del supervisor de TicTacToe (header sticky con
selector de ejecución y reloj, sidebar de unidades, panel central con
pestañas, exportación CSV, eventos SSE, almacén SQLite consultable)
adaptados al dominio Villa Olivar: en lugar de salas MUC se gestionan
grupos de alumnos y en lugar de partidas se gestionan seguimientos
de incidentes.

Endpoints:

- ``GET  /supervisor``                              Plantilla HTML.
- ``GET  /supervisor/api/state``                    Estado JSON en vivo.
- ``GET  /supervisor/api/seguimientos``             Lista de seguimientos.
- ``GET  /supervisor/api/seguimientos/{id}``        Detalle de uno.
- ``GET  /supervisor/api/resumen``                  Métricas agregadas.
- ``GET  /supervisor/api/ejecuciones``              Listado histórico.
- ``GET  /supervisor/api/ejecuciones/{id}``         Detalle histórico.
- ``GET  /supervisor/api/stream``                   SSE en tiempo real.
- ``GET  /supervisor/api/csv/{tipo}``               Exportación CSV en vivo.
- ``GET  /supervisor/api/ejecuciones/{id}/csv/{t}`` Exportación CSV histórica.
- ``POST /supervisor/api/inyectar``                 Inyección manual desde el panel.
- ``POST /supervisor/api/finalizar``                Cierre desde el panel.
- ``GET  /supervisor/static/<fichero>``             Estáticos (CSS/JS).

Los handlers acceden al supervisor mediante ``request.app["agente"]``,
que se inyecta al registrar las rutas.
"""
import asyncio
import base64
import contextlib
import csv
import io
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from aiohttp import web

from agente_profesor.persistencia.almacen_supervisor import (
    AlmacenSupervisor,
)

logger = logging.getLogger(__name__)


# ─── Constantes simbólicas ──────────────────────────────────────────────────

KEEPALIVE_SSE_SEGUNDOS = 15
TAMANO_COLA_SSE = 50
LIMITE_LOG_RECIENTES = 200

ESTADOS_OK = frozenset({"RESUELTO"})
ESTADOS_KO = frozenset({"RECHAZADO", "TIMEOUT", "FALLIDO"})

_TIPOS_CSV_VALIDOS = ("seguimientos", "resumen", "log")

# Subdirectorio (relativo a la carpeta de la BD SQLite) donde se vuelcan
# los CSV automáticos al pulsar Finalizar. Cada finalización crea su
# propia carpeta con marca temporal para no sobrescribir las anteriores.
NOMBRE_CARPETA_EXPORTACIONES = "exportaciones_csv"

# Formato de la marca temporal usada como nombre de la subcarpeta.
FORMATO_MARCA_CARPETA_EXPORT = "%Y%m%d-%H%M%S"

_DIR_WEB = os.path.dirname(os.path.abspath(__file__))
_DIR_TEMPLATES = os.path.join(_DIR_WEB, "templates")
_DIR_STATIC = os.path.join(_DIR_WEB, "static")


# ─── Suscriptores SSE (módulo) ──────────────────────────────────────────────

_suscriptores_sse: list[asyncio.Queue] = []


def notificar_sse(tipo: str, datos: dict) -> None:
    """Deposita un evento en todas las colas SSE activas."""
    evento = {"tipo": tipo, "datos": datos}
    for cola in list(_suscriptores_sse):
        try:
            cola.put_nowait(evento)
        except asyncio.QueueFull:
            # Si la cola está llena, descartamos el evento más reciente
            # antes que bloquear al supervisor. Es preferible perder un
            # tick a frenar la inyección.
            pass


def cerrar_todas_las_suscripciones_sse() -> None:
    """Manda un evento de cierre a todas las colas SSE.

    Permite al lanzador desbloquear los handlers SSE antes de hacer
    ``runner.cleanup()`` para evitar que el apagado se cuelgue
    esperando al keepalive.
    """
    for cola in list(_suscriptores_sse):
        try:
            cola.put_nowait({"tipo": "cierre", "datos": {}})
        except asyncio.QueueFull:
            pass


# ─── Autenticación HTTP Basic opcional ──────────────────────────────────────

def crear_middleware_auth(
    usuario: str, contrasena: str,
) -> web.middleware:
    """Devuelve un middleware aiohttp que exige HTTP Basic.

    Las rutas estáticas se sirven sin autenticación para que el
    navegador pueda cargar CSS y JS antes de mostrar el diálogo.
    """
    credenciales_esperadas = base64.b64encode(
        f"{usuario}:{contrasena}".encode(),
    ).decode()

    @web.middleware
    async def middleware_auth(request, handler):
        ruta = request.path
        es_estatico = ruta.startswith("/supervisor/static")
        autenticado = es_estatico

        if not autenticado:
            cabecera = request.headers.get("Authorization", "")
            if cabecera.startswith("Basic "):
                token = cabecera[6:]
                autenticado = token == credenciales_esperadas

        respuesta: web.StreamResponse
        if autenticado:
            respuesta = await handler(request)
        else:
            respuesta = web.Response(
                text="Autenticación requerida",
                status=401,
            )
            respuesta.headers["WWW-Authenticate"] = (
                'Basic realm="Supervisor Villa Olivar"'
            )

        return respuesta

    return middleware_auth


# ─── Construcción del estado público ────────────────────────────────────────

def _seguimientos_como_dicts(agente) -> list[dict]:
    """Devuelve los seguimientos del agente serializados a dict.

    Maneja los dos casos del proyecto: agente vivo (``Seguimiento``
    con método ``a_dict()``) y agente simulado (dicts directamente).
    """
    coleccion = getattr(agente, "seguimientos", {})
    if isinstance(coleccion, dict):
        valores = coleccion.values()
    else:
        valores = coleccion

    resultado = []
    for seguimiento in valores:
        if hasattr(seguimiento, "a_dict"):
            resultado.append(seguimiento.a_dict())
        else:
            resultado.append(seguimiento)
    return resultado


def _resumen_metricas(seguimientos: list[dict]) -> dict:
    """Calcula el resumen agregado a partir de seguimientos en dict."""
    total = len(seguimientos)
    por_estado: dict[str, int] = {}
    por_grupo: dict[str, int] = {}
    por_tipo: dict[str, int] = {}
    latencias_agree: list[int] = []
    latencias_informe: list[int] = []
    ok = 0
    ko = 0

    for seguimiento in seguimientos:
        estado = seguimiento.get("estado", "")
        grupo = seguimiento.get("grupo", "")
        tipo = seguimiento.get("tipo_emergencia", "")
        por_estado[estado] = por_estado.get(estado, 0) + 1
        por_grupo[grupo] = por_grupo.get(grupo, 0) + 1
        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
        if estado in ESTADOS_OK:
            ok += 1
        if estado in ESTADOS_KO:
            ko += 1
        lat_agree = seguimiento.get("latencia_agree_ms")
        lat_informe = seguimiento.get("latencia_informe_ms")
        if lat_agree is not None:
            latencias_agree.append(lat_agree)
        if lat_informe is not None:
            latencias_informe.append(lat_informe)

    resultado = {
        "total": total,
        "ok": ok,
        "ko": ko,
        "por_estado": por_estado,
        "por_grupo": por_grupo,
        "por_tipo": por_tipo,
        "latencia_agree_ms": _percentiles(latencias_agree),
        "latencia_informe_ms": _percentiles(latencias_informe),
    }
    return resultado


def _percentiles(valores: list[int]) -> dict:
    """Devuelve mediana, p95 y máximo de una lista de enteros."""
    resultado = {"mediana": 0, "p95": 0, "maximo": 0}
    if valores:
        ordenados = sorted(valores)
        cantidad = len(ordenados)
        indice_p50 = cantidad // 2
        indice_p95 = max(int(cantidad * 0.95) - 1, 0)
        resultado = {
            "mediana": ordenados[indice_p50],
            "p95": ordenados[indice_p95],
            "maximo": ordenados[-1],
        }
    return resultado


def _construir_estado(agente, modo_app: str = "") -> dict:
    """Construye el JSON de estado completo del supervisor en vivo."""
    seguimientos = _seguimientos_como_dicts(agente)
    grupos = list(getattr(agente, "grupos", []))
    log_eventos = list(getattr(agente, "log_eventos", []))[
        :LIMITE_LOG_RECIENTES
    ]
    modo_supervisor = getattr(agente, "modo", modo_app or "consulta")

    # En modo consulta no hay un agente vivo emitiendo eventos. El
    # frontend usa este flag para no quedarse esperando datos en
    # vivo y auto-seleccionar la ejecución más reciente del histórico.
    es_consulta = modo_app == "consulta" or not getattr(
        agente, "es_agente_vivo", True,
    )

    # Estados de los agentes (sondeo de telemetría). Lo aplanamos a
    # lista porque el frontend lo consume así.
    estados_agentes_dict = getattr(agente, "estados_agentes", {}) or {}
    estados_agentes = list(estados_agentes_dict.values())

    resultado = {
        "supervisor": {
            "jid": str(getattr(agente, "jid", "profesor_emergencias@—")),
            "modo": modo_supervisor,
            "es_vivo": not es_consulta,
        },
        "grupos": grupos,
        "seguimientos": seguimientos,
        "resumen": _resumen_metricas(seguimientos),
        "estados_agentes": estados_agentes,
        "log": log_eventos,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }
    return resultado


# ─── Handlers HTTP — estado en vivo ─────────────────────────────────────────

async def handler_index(request: web.Request) -> web.Response:
    """Sirve la plantilla HTML principal del dashboard."""
    ruta_html = os.path.join(_DIR_TEMPLATES, "supervisor.html")

    contenido = ""
    estado_http = 200
    try:
        with open(ruta_html, "r", encoding="utf-8") as fichero:
            contenido = fichero.read()
    except FileNotFoundError:
        logger.error("No se encontró la plantilla: %s", ruta_html)
        contenido = "Error: plantilla supervisor.html no encontrada"
        estado_http = 404

    respuesta = web.Response(
        text=contenido,
        status=estado_http,
        content_type="text/html",
    )
    return respuesta


async def handler_state(request: web.Request) -> web.Response:
    """Devuelve el estado completo del supervisor como JSON."""
    agente = request.app["agente"]
    modo_app = request.app.get("modo", "")
    estado = _construir_estado(agente, modo_app=modo_app)
    respuesta = web.json_response(estado)
    return respuesta


async def handler_lista_seguimientos(
    request: web.Request,
) -> web.Response:
    """Lista todos los seguimientos serializados en vivo."""
    agente = request.app["agente"]
    cuerpo = {"seguimientos": _seguimientos_como_dicts(agente)}
    respuesta = web.json_response(cuerpo)
    return respuesta


async def handler_detalle_seguimiento(
    request: web.Request,
) -> web.Response:
    """Devuelve un único seguimiento por ``id_emergencia``."""
    agente = request.app["agente"]
    id_emergencia = request.match_info.get("id", "")

    encontrado: Optional[dict] = None
    for seguimiento in _seguimientos_como_dicts(agente):
        if seguimiento.get("id_emergencia") == id_emergencia:
            encontrado = seguimiento

    respuesta: web.Response
    if encontrado is None:
        respuesta = web.json_response(
            {"error": f"Seguimiento '{id_emergencia}' no encontrado"},
            status=404,
        )
    else:
        respuesta = web.json_response(encontrado)
    return respuesta


async def handler_resumen(request: web.Request) -> web.Response:
    """Devuelve solo las métricas agregadas en vivo."""
    agente = request.app["agente"]
    seguimientos = _seguimientos_como_dicts(agente)
    respuesta = web.json_response(_resumen_metricas(seguimientos))
    return respuesta


# ─── Handlers HTTP — ejecuciones históricas ─────────────────────────────────

def _almacen_de(agente):
    """Devuelve el almacén SQLite del agente, o None si no hay."""
    resultado = getattr(agente, "almacen", None)
    return resultado


@contextlib.contextmanager
def _almacen_lectura(agente):
    """Devuelve un almacén apto para operaciones de solo lectura.

    Si el agente conserva un almacén abierto se reutiliza tal cual y
    no se cierra al salir del bloque ``with``. Si el almacén principal
    ya se ha cerrado (por ejemplo tras pulsar Finalizar pero el panel
    sigue abierto en el navegador), se abre una conexión transitoria
    contra ``agente.ruta_db`` que se cierra al finalizar el bloque.
    De este modo los endpoints de consulta histórica siguen
    funcionando sin alterar la semántica del apagado ordenado.

    Patrón tomado del supervisor de TicTacToe
    (``web/supervisor_handlers.py::_almacen_lectura``).
    """
    almacen_vivo = getattr(agente, "almacen", None)
    almacen_transitorio: Optional[AlmacenSupervisor] = None
    try:
        if almacen_vivo is not None:
            yield almacen_vivo
        else:
            ruta_db = getattr(agente, "ruta_db", "")
            if ruta_db and os.path.exists(ruta_db):
                almacen_transitorio = AlmacenSupervisor(ruta_db)
                yield almacen_transitorio
            else:
                yield None
    finally:
        if almacen_transitorio is not None:
            almacen_transitorio.cerrar()


async def handler_lista_ejecuciones(
    request: web.Request,
) -> web.Response:
    """Lista todas las ejecuciones almacenadas."""
    agente = request.app["agente"]

    cuerpo: dict
    with _almacen_lectura(agente) as almacen:
        if almacen is None:
            cuerpo = {"ejecuciones": []}
        else:
            cuerpo = {"ejecuciones": almacen.listar_ejecuciones()}

    respuesta = web.json_response(cuerpo)
    return respuesta


async def handler_detalle_ejecucion(
    request: web.Request,
) -> web.Response:
    """Devuelve el contenido completo de una ejecución pasada.

    El JSON tiene la misma forma que ``/api/state`` para que el
    frontend lo represente sin cambios.
    """
    agente = request.app["agente"]
    id_texto = request.match_info.get("id", "")

    respuesta: web.Response
    if not id_texto.isdigit():
        respuesta = web.json_response(
            {"error": "Ejecución no disponible"}, status=404,
        )
        return respuesta

    with _almacen_lectura(agente) as almacen:
        if almacen is None:
            respuesta = web.json_response(
                {"error": "Ejecución no disponible"}, status=404,
            )
        else:
            ejec_id = int(id_texto)
            datos = almacen.obtener_ejecucion(ejec_id)
            if not datos.get("metadatos"):
                respuesta = web.json_response(
                    {"error": f"Ejecución #{ejec_id} no encontrada"},
                    status=404,
                )
            else:
                cuerpo = {
                    "supervisor": {
                        "jid": "profesor_emergencias@(histórico)",
                        "modo": datos["metadatos"].get("modo", ""),
                        "es_vivo": False,
                        "ejecucion": datos["metadatos"],
                    },
                    "grupos": datos["grupos"],
                    "seguimientos": datos["seguimientos"],
                    "resumen": _resumen_metricas(datos["seguimientos"]),
                    "log": datos["log"],
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                }
                respuesta = web.json_response(cuerpo)
    return respuesta


# ─── Exportación CSV ────────────────────────────────────────────────────────

def _csv_seguimientos(seguimientos: list[dict]) -> str:
    """Genera el CSV de la tabla de seguimientos."""
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow([
        "id_emergencia", "grupo", "estado", "tipo_emergencia",
        "prioridad", "instante_envio", "instante_agree",
        "instante_informe", "latencia_agree_ms",
        "latencia_informe_ms", "error",
    ])
    for s in seguimientos:
        escritor.writerow([
            s.get("id_emergencia", ""),
            s.get("grupo", ""),
            s.get("estado", ""),
            s.get("tipo_emergencia", ""),
            s.get("prioridad", ""),
            s.get("instante_envio") or "",
            s.get("instante_agree") or "",
            s.get("instante_informe") or "",
            s.get("latencia_agree_ms") or "",
            s.get("latencia_informe_ms") or "",
            s.get("error") or "",
        ])
    resultado = salida.getvalue()
    return resultado


def _csv_resumen(seguimientos: list[dict]) -> str:
    """Genera un CSV con el reparto por estado, grupo y tipo."""
    metricas = _resumen_metricas(seguimientos)

    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(["categoria", "clave", "valor"])
    escritor.writerow(["totales", "total", metricas["total"]])
    escritor.writerow(["totales", "ok", metricas["ok"]])
    escritor.writerow(["totales", "ko", metricas["ko"]])
    for clave, valor in metricas["por_estado"].items():
        escritor.writerow(["por_estado", clave, valor])
    for clave, valor in metricas["por_grupo"].items():
        escritor.writerow(["por_grupo", clave, valor])
    for clave, valor in metricas["por_tipo"].items():
        escritor.writerow(["por_tipo", clave, valor])
    resultado = salida.getvalue()
    return resultado


def _csv_log(eventos: list[dict]) -> str:
    """Genera un CSV con el log cronológico."""
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(["timestamp", "tipo", "origen", "detalle"])
    for evento in eventos:
        escritor.writerow([
            evento.get("ts", ""),
            evento.get("tipo", ""),
            evento.get("de", ""),
            evento.get("detalle", ""),
        ])
    resultado = salida.getvalue()
    return resultado


def _respuesta_csv(contenido: str, nombre: str) -> web.Response:
    """Construye una respuesta CSV con cabeceras de descarga."""
    respuesta = web.Response(
        text=contenido,
        content_type="text/csv",
        charset="utf-8",
    )
    respuesta.headers["Content-Disposition"] = (
        f'attachment; filename="{nombre}"'
    )
    return respuesta


async def handler_csv(request: web.Request) -> web.Response:
    """Exporta seguimientos, resumen o log en vivo como CSV."""
    agente = request.app["agente"]
    tipo = request.match_info.get("tipo", "")

    respuesta: web.Response
    if tipo not in _TIPOS_CSV_VALIDOS:
        respuesta = web.Response(
            text=f"Tipo '{tipo}' no válido. "
            f"Tipos: {', '.join(_TIPOS_CSV_VALIDOS)}",
            status=400,
        )
    else:
        seguimientos = _seguimientos_como_dicts(agente)
        log_eventos = list(getattr(agente, "log_eventos", []))

        if tipo == "seguimientos":
            contenido = _csv_seguimientos(seguimientos)
        elif tipo == "resumen":
            contenido = _csv_resumen(seguimientos)
        else:
            contenido = _csv_log(log_eventos)

        respuesta = _respuesta_csv(
            contenido, f"supervisor_{tipo}.csv",
        )
    return respuesta


async def handler_csv_ejecucion(request: web.Request) -> web.Response:
    """Exporta seguimientos/resumen/log de una ejecución pasada."""
    agente = request.app["agente"]
    id_texto = request.match_info.get("id", "")
    tipo = request.match_info.get("tipo", "")

    respuesta: web.Response
    if tipo not in _TIPOS_CSV_VALIDOS:
        respuesta = web.Response(
            text=f"Tipo '{tipo}' no válido", status=400,
        )
        return respuesta
    if not id_texto.isdigit():
        respuesta = web.Response(
            text="Ejecución no disponible", status=404,
        )
        return respuesta

    with _almacen_lectura(agente) as almacen:
        if almacen is None:
            respuesta = web.Response(
                text="Ejecución no disponible", status=404,
            )
        else:
            ejec_id = int(id_texto)
            datos = almacen.obtener_ejecucion(ejec_id)
            if not datos.get("metadatos"):
                respuesta = web.Response(
                    text=f"Ejecución #{ejec_id} no encontrada",
                    status=404,
                )
            else:
                seguimientos = datos["seguimientos"]
                log_eventos = datos["log"]

                if tipo == "seguimientos":
                    contenido = _csv_seguimientos(seguimientos)
                elif tipo == "resumen":
                    contenido = _csv_resumen(seguimientos)
                else:
                    contenido = _csv_log(log_eventos)

                respuesta = _respuesta_csv(
                    contenido,
                    f"supervisor_ejec{ejec_id}_{tipo}.csv",
                )
    return respuesta


# ─── Server-Sent Events ─────────────────────────────────────────────────────

async def handler_sse(request: web.Request) -> web.StreamResponse:
    """Mantiene una conexión SSE con el dashboard.

    El primer evento es el estado completo. A partir de ahí, cada vez
    que el supervisor llama a ``notificar_sse`` el evento se reenvía
    por aquí. Si pasan más de ``KEEPALIVE_SSE_SEGUNDOS`` sin tráfico,
    se envía un comentario de keepalive para que los proxies no
    cierren la conexión.
    """
    respuesta = web.StreamResponse()
    respuesta.content_type = "text/event-stream"
    respuesta.headers["Cache-Control"] = "no-cache"
    respuesta.headers["X-Accel-Buffering"] = "no"
    await respuesta.prepare(request)

    cola: asyncio.Queue = asyncio.Queue(maxsize=TAMANO_COLA_SSE)
    _suscriptores_sse.append(cola)

    agente = request.app["agente"]
    modo_app = request.app.get("modo", "")
    estado_inicial = json.dumps(
        _construir_estado(agente, modo_app=modo_app),
        ensure_ascii=False,
    )
    try:
        await respuesta.write(
            f"event: state\ndata: {estado_inicial}\n\n".encode("utf-8"),
        )
    except (ConnectionResetError, ConnectionError):
        # El cliente cerró la conexión mientras enviábamos el primer
        # evento; no hay nada que hacer salvo limpiar la cola.
        if cola in _suscriptores_sse:
            _suscriptores_sse.remove(cola)
        return respuesta

    try:
        activo = True
        while activo:
            try:
                evento = await asyncio.wait_for(
                    cola.get(), timeout=KEEPALIVE_SSE_SEGUNDOS,
                )
                tipo = evento.get("tipo", "state")
                if tipo == "cierre":
                    activo = False
                else:
                    datos = json.dumps(
                        evento.get("datos", {}),
                        ensure_ascii=False,
                    )
                    linea = f"event: {tipo}\ndata: {datos}\n\n"
                    await respuesta.write(linea.encode("utf-8"))
            except asyncio.TimeoutError:
                await respuesta.write(b": keepalive\n\n")
            except (ConnectionResetError, ConnectionError):
                activo = False
    finally:
        if cola in _suscriptores_sse:
            _suscriptores_sse.remove(cola)

    return respuesta


# ─── Inyección manual desde el panel ────────────────────────────────────────

async def handler_escenarios(request: web.Request) -> web.Response:
    """Lista las claves del catálogo de escenarios.

    El panel usa esta lista para alimentar el selector del mini
    formulario que aparece al pulsar "Inyectar incidente". Vive como
    endpoint independiente porque el catálogo es estático en
    ejecución y así evitamos enviarlo en cada ``/api/state``.
    """
    # Importación local: el catálogo se construye al importar
    # agente_profesor.escenarios; mantener el import a nivel de
    # función evita arrastrar la dependencia en tests que no la
    # necesitan (los handlers se importan desde varios sitios).
    from agente_profesor.escenarios import _DEFINICIONES_ESCENARIOS

    cuerpo = {
        "escenarios": [
            {
                "clave": clave,
                "tipo_emergencia": tipo,
                "prioridad": prioridad,
                "ubicacion": ubicacion,
                "descripcion": descripcion,
            }
            for (clave, tipo, prioridad, ubicacion, descripcion)
            in _DEFINICIONES_ESCENARIOS
        ],
    }
    respuesta = web.json_response(cuerpo)
    return respuesta


async def handler_inyectar(request: web.Request) -> web.Response:
    """Dispara una inyección manual a un grupo desde el botón del panel.

    Cuerpo JSON esperado::

        {
          "grupo": "fenix",                  // obligatorio: id del grupo
          "clave_escenario": "incendio_alta" // opcional; si falta, aleatorio
        }
    """
    agente = request.app["agente"]

    if getattr(agente, "modo", "") != "activo":
        respuesta = web.json_response(
            {
                "error": "El supervisor está en modo consulta; "
                         "no se pueden inyectar incidentes.",
            },
            status=409,
        )
        return respuesta

    try:
        cuerpo = await request.json()
    except json.JSONDecodeError:
        cuerpo = {}

    id_grupo = cuerpo.get("grupo", "")
    clave_escenario = cuerpo.get("clave_escenario") or None
    if not id_grupo:
        respuesta = web.json_response(
            {"error": "Falta el campo 'grupo' en el cuerpo JSON."},
            status=400,
        )
        return respuesta

    seguimiento = await agente.inyectar_manualmente(
        id_grupo=id_grupo, clave_escenario=clave_escenario,
    )
    if seguimiento is None:
        respuesta = web.json_response(
            {
                "error": "No se ha podido inyectar (grupo o "
                         "escenario desconocido).",
            },
            status=400,
        )
    else:
        respuesta = web.json_response({
            "estado": "inyectado",
            "id_emergencia": seguimiento.id_emergencia,
            "grupo": seguimiento.grupo,
            "tipo_emergencia": seguimiento.tipo_emergencia,
            "prioridad": seguimiento.prioridad,
        })
    return respuesta


# ─── Finalización desde el panel ────────────────────────────────────────────

def _volcar_csvs_a_disco(agente) -> Optional[Path]:
    """Guarda los tres CSV en disco junto al archivo SQLite.

    Crea una subcarpeta con marca temporal dentro de
    ``<dir_db>/exportaciones_csv/`` y escribe en ella tres ficheros:
    ``seguimientos.csv``, ``resumen.csv`` y ``log.csv``. Devuelve la
    ruta absoluta de la carpeta creada, o ``None`` si el agente no
    tiene una BD configurada (caso defensivo: en operación normal
    siempre la tiene).
    """
    ruta_db = getattr(agente, "ruta_db", "")
    if not ruta_db:
        return None

    seguimientos = _seguimientos_como_dicts(agente)
    log_eventos = list(getattr(agente, "log_eventos", []))

    marca = datetime.now().strftime(FORMATO_MARCA_CARPETA_EXPORT)
    carpeta_destino = (
        Path(ruta_db).resolve().parent
        / NOMBRE_CARPETA_EXPORTACIONES
        / marca
    )
    carpeta_destino.mkdir(parents=True, exist_ok=True)

    contenidos = {
        "seguimientos.csv": _csv_seguimientos(seguimientos),
        "resumen.csv":      _csv_resumen(seguimientos),
        "log.csv":          _csv_log(log_eventos),
    }
    for nombre, texto in contenidos.items():
        (carpeta_destino / nombre).write_text(texto, encoding="utf-8")

    return carpeta_destino


async def handler_finalizar(request: web.Request) -> web.Response:
    """Cierra el supervisor de forma ordenada desde el panel.

    Antes de detener el bucle principal, vuelca a disco los tres CSV
    (seguimientos, resumen, registro) en una subcarpeta junto al
    archivo SQLite, para que la sesión quede archivada aunque el
    profesor no haya descargado los CSV manualmente desde el panel.
    """
    agente = request.app["agente"]
    evento_parada = request.app.get("evento_parada", None)
    ts = datetime.now().strftime("%H:%M:%S")

    carpeta_export: Optional[Path] = None
    try:
        carpeta_export = _volcar_csvs_a_disco(agente)
    except OSError as err:
        # No bloqueamos el cierre por un error de E/S al exportar:
        # registramos la incidencia y seguimos finalizando.
        logger.error(
            "No se pudieron volcar los CSV automáticos: %s", err,
        )

    cerrar_todas_las_suscripciones_sse()

    # El retardo cortísimo es suficiente para que la respuesta llegue
    # al navegador antes de que el bucle principal active el apagado.
    if evento_parada is not None:
        loop = asyncio.get_event_loop()
        loop.call_later(0.3, evento_parada.set)

    cuerpo = {
        "estado": "finalizando",
        "timestamp": ts,
        "csv_exportados": carpeta_export is not None,
        "csv_carpeta": str(carpeta_export) if carpeta_export else "",
    }
    if carpeta_export is not None:
        logger.info(
            "CSV automáticos guardados en %s al finalizar el supervisor.",
            carpeta_export,
        )
    respuesta = web.json_response(cuerpo)
    return respuesta


# ─── Registro de rutas ──────────────────────────────────────────────────────

def registrar_rutas(app: web.Application) -> None:
    """Registra todas las rutas del dashboard en una aiohttp app."""
    app.router.add_get("/supervisor", handler_index)
    app.router.add_get("/supervisor/", handler_index)
    app.router.add_get("/supervisor/api/state", handler_state)
    app.router.add_get(
        "/supervisor/api/seguimientos", handler_lista_seguimientos,
    )
    app.router.add_get(
        "/supervisor/api/seguimientos/{id}", handler_detalle_seguimiento,
    )
    app.router.add_get("/supervisor/api/resumen", handler_resumen)
    app.router.add_get(
        "/supervisor/api/ejecuciones", handler_lista_ejecuciones,
    )
    app.router.add_get(
        "/supervisor/api/ejecuciones/{id}", handler_detalle_ejecucion,
    )
    app.router.add_get("/supervisor/api/stream", handler_sse)
    app.router.add_get("/supervisor/api/csv/{tipo}", handler_csv)
    app.router.add_get(
        "/supervisor/api/ejecuciones/{id}/csv/{tipo}",
        handler_csv_ejecucion,
    )
    app.router.add_get(
        "/supervisor/api/escenarios", handler_escenarios,
    )
    app.router.add_post(
        "/supervisor/api/inyectar", handler_inyectar,
    )
    app.router.add_post(
        "/supervisor/api/finalizar", handler_finalizar,
    )
    app.router.add_static("/supervisor/static", _DIR_STATIC)

    logger.info(
        "Rutas del supervisor registradas en /supervisor* "
        "(estado, seguimientos, resumen, ejecuciones, stream, "
        "csv, finalizar)",
    )
