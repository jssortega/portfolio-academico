"""
Lanzador del Agente Supervisor para la prueba de examen.

Esta rama prepara el Agente Supervisor del profesor exclusivamente
para el día del examen. El supervisor se ejecuta **siempre** en modo
examen; no admite otros modos. Lo único que el profesor decide al
arrancarlo es la submodalidad del examen, con ``--submodo``:

- **grupo** (valor por defecto): sala MUC única
  ``examen@examen.<dominio>``, compartida por todos los alumnos.
  Cada alumno aporta un único tablero y un único jugador.
  Configuración del supervisor en ``config/sala_examen.yaml``.

- **individual**: 30 salas MUC, una por puesto del aula
  (``PC-01@examen.<dominio>`` … ``PC-30@examen.<dominio>``). El
  supervisor pre-crea las 30 al arrancar. Cada alumno se une a la
  sala asociada al puesto físico donde se ha sentado y aporta 3
  tableros y 12 jugadores. Configuración del supervisor en
  ``config/sala_examen_individual.yaml``.

En las dos submodalidades el componente MUC dedicado al examen
(``examen.<dominio>``) tiene la directiva
``restrict_room_creation = "admin"``: ningún alumno puede crear salas
allí. Si el supervisor del profesor no las pre-crea, los agentes
alumno son rechazados y no se pueden generar partidas, lo que evita
perder informes (game-report) por agentes que arrancan en vacío.
Detalle en ``doc/MODO_EXAMEN.md``.

El supervisor admite dos perfiles XMPP, que se eligen en
``config/config.yaml`` con ``xmpp.perfil_activo``:

- **local**: Prosody local del repositorio de infraestructura de la
  asignatura. Permite a los alumnos **simular** en su propio equipo el
  funcionamiento que se reproduce en el laboratorio. La contraseña del
  supervisor es la ``password_defecto`` del YAML.
- **servidor**: Prosody oficial de la asignatura (sinbad2.ujaen.es),
  donde el profesor realiza la **evaluación definitiva** de los
  proyectos. Exige la contraseña fuerte del supervisor en la variable
  de entorno ``SSMMAA_SUPERVISOR_PASSWORD``.

El lanzador aborta si el perfil activo no es ninguno de esos dos.

Además del arranque normal, el lanzador admite un **modo consulta**
(``--consulta``) que abre únicamente el panel web sobre un fichero de
persistencia ya existente, sin conectarse al servidor XMPP. Sirve para
revisar las ejecuciones pasadas (informes, registro y clasificación)
una vez terminada la prueba. En este modo basta con ``--consulta``:
el lanzador localiza automáticamente el fichero ``.db`` más reciente
bajo ``data/`` (recorriendo todo el árbol de subdirectorios) y el
profesor puede cambiar a cualquier otro desde el selector del panel.

Uso::

    export SSMMAA_SUPERVISOR_PASSWORD='clave_fuerte_del_profesor'
    python supervisor_main.py                       # grupo (default)
    python supervisor_main.py --submodo grupo       # explícito
    python supervisor_main.py --submodo individual  # 30 salas PC-NN
    python supervisor_main.py --consulta            # último .db de data/
    python supervisor_main.py --consulta --db data/examen.db
"""

import argparse
import asyncio
import logging
import os
import signal
import socket
import sys
import webbrowser
from types import SimpleNamespace
from typing import Any

from aiohttp import web

from agentes.agente_supervisor import AgenteSupervisor
from persistencia.almacen_supervisor import AlmacenSupervisor
from utils import (
    aplicar_servicio_muc_segun_modo,
    arrancar_agente,
    cargar_configuracion,
    cargar_torneos,
    crear_agente,
    crear_salas_torneos,
)
from web.supervisor_handlers import registrar_rutas_supervisor

# ── Configuración global del logging ───────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("supervisor_main")

# ── Valores por defecto ──────────────────────────────────────
# Segundos entre cada consulta del supervisor a las salas MUC.
INTERVALO_POLL_MUC_DEFECTO = 10

# Segundos de espera al comprobar la accesibilidad TCP del servidor
# XMPP antes de arrancar. Es una comprobación rápida que evita que el
# supervisor se quede esperando un timeout largo de SPADE si el
# servidor no está accesible.
TIMEOUT_COMPROBACION_XMPP = 5

# Puerto del panel web del supervisor. Es solo el valor de respaldo:
# el puerto se lee de 'sistema.puerto_web' de config.yaml y, si se
# indica, '--puerto' tiene prioridad sobre ambos.
#
# Reparto de puertos en el rango 80xx, coherente con los puertos del
# servidor de la asignatura abiertos al exterior:
#   8000         Panel web del supervisor (este lanzador).
#   8001-8005    Scripts de verificación del supervisor.
#   8009         Panel web de los tests de integración.
# Los agentes Tablero del alumno usan otro rango (10080-10089 en la
# rama examen-alumno), de modo que un alumno puede arrancar a la vez
# sus agentes y el supervisor en modo simulación 'local' sin que los
# puertos web se solapen.
PUERTO_WEB_DEFECTO = 8000

# El modo de ejecución es siempre 'examen' en esta rama. Se mantiene
# como constante para los puntos del código y de la configuración que
# todavía lo necesitan (inyección en el agente, redirección del
# componente MUC, etiquetas de log).
MODO_EXAMEN = "examen"

# Submodalidades válidas del examen. Es la única elección del profesor
# al arrancar el supervisor.
SUBMODO_GRUPO = "grupo"
SUBMODO_INDIVIDUAL = "individual"
SUBMODOS_EXAMEN = (SUBMODO_GRUPO, SUBMODO_INDIVIDUAL)
SUBMODO_EXAMEN_POR_DEFECTO = SUBMODO_GRUPO


def _resolver_clave_examen(submodo: str) -> str:
    """Devuelve la clave interna que identifica la submodalidad.

    El supervisor se ejecuta siempre en modo examen, así que la clave
    interna solo depende del submodo:

        grupo       →  examen_grupo
        individual  →  examen_individual

    Esta clave indexa ``FICHERO_SALAS`` y ``RUTA_DB_POR_SUBMODO``.

    Args:
        submodo: Valor de ``--submodo`` (``"grupo"`` o
            ``"individual"``).

    Returns:
        Clave interna (``"examen_grupo"`` o ``"examen_individual"``).
    """
    clave = f"{MODO_EXAMEN}_{submodo}"
    return clave


# Ficheros de salas asociados a cada submodalidad del examen: la sala
# única para 'grupo' y las 30 salas PC-NN para 'individual'.
FICHERO_SALAS = {
    "examen_grupo": "config/sala_examen.yaml",
    "examen_individual": "config/sala_examen_individual.yaml",
}

# Base de datos SQLite por defecto de cada submodalidad. Las dos van a
# ficheros distintos para que la trazabilidad por puesto del submodo
# 'individual' no se mezcle con la de la sala compartida del submodo
# 'grupo'. Si el profesor indica '--db' explícitamente, este valor se
# ignora.
RUTA_DB_POR_SUBMODO = {
    "examen_grupo": "data/examen.db",
    "examen_individual": "data/examen_individual.db",
}

# Directorio raíz donde se almacenan los ficheros SQLite del
# supervisor. En modo consulta el lanzador lo recorre recursivamente
# para localizar el último fichero `.db` modificado. Es el mismo
# directorio que utiliza el selector de bases de datos del panel web,
# que también explora todo el árbol (`web/supervisor_handlers.py`).
DIRECTORIO_RAIZ_DATOS = "data"
EXTENSION_BD = ".db"

# Variable de entorno con la contraseña del supervisor en el servidor
# XMPP. Se exige siempre que el perfil XMPP activo sea 'servidor'
# (sinbad2.ujaen.es), porque en ese servidor el JID supervisor es el
# del profesor y debe estar protegido frente a alumnos que conocen
# 'password_defecto' del config.yaml público.
#
# En el perfil 'local' la contraseña sigue siendo 'password_defecto'
# del YAML, para que el supervisor pueda arrancarse contra un Prosody
# local en pruebas sin ningún requisito adicional.
#
# Operativa del día del examen (servidor del profesor):
#     export SSMMAA_SUPERVISOR_PASSWORD='clave_fuerte_del_profesor'
#     python supervisor_main.py --submodo individual
# Si todavía no se ha fijado la contraseña fuerte en el servidor:
# ejecutar 'prosodyctl passwd supervisor@<dominio>' dentro del
# contenedor Prosody (ver el repositorio público de infraestructura
# de la asignatura para los detalles del despliegue:
# https://gitlab.com/ssmmaa/infraestructurassmmaa/ssmmaa-infraestructura).
VARIABLE_PASSWORD_SUPERVISOR = "SSMMAA_SUPERVISOR_PASSWORD"

# Perfiles XMPP en los que la contraseña del supervisor DEBE venir de
# la variable de entorno (no se permite caer al YAML público). El
# servidor oficial de la asignatura tiene una clave fuerte fijada con
# 'prosodyctl passwd' y NO publicada en config.yaml.
PERFILES_REQUIEREN_PASSWORD_FUERTE = frozenset({"servidor"})

# El supervisor admite dos perfiles XMPP:
#   - 'local'    → simulación: el alumno reproduce en su equipo el
#                  funcionamiento del laboratorio.
#   - 'servidor' → evaluación definitiva del profesor en el Prosody
#                  oficial de la asignatura (sinbad2.ujaen.es).
# Cualquier otro valor de 'perfil_activo' es un error de configuración
# y aborta el lanzador.
PERFILES_XMPP_ACEPTADOS = frozenset({"local", "servidor"})

# Perfil contra el que se realiza la evaluación oficial del examen.
PERFIL_XMPP_SERVIDOR_OFICIAL = "servidor"


# Códigos de salida usados al abortar el lanzador por errores
# tratables (sin traza Python visible). Cada código identifica un
# tipo de fallo para que el operador pueda relacionarlo con la
# tabla de resolución de problemas del README.
COD_SALIDA_PASSWORD_AUSENTE = 2          # SSMMAA_SUPERVISOR_PASSWORD ausente
COD_SALIDA_PERFIL_NO_PERMITIDO = 3        # Perfil XMPP no admitido (S-X)
COD_SALIDA_BD_NO_EXISTE = 4               # Fichero --db inexistente
COD_SALIDA_XMPP_INALCANZABLE = 5          # TCP del servidor no responde
COD_SALIDA_CONFIG_INVALIDA = 6            # config.yaml malformado/incompleto


def _abortar_por_configuracion_invalida(
    error: Exception, ruta_config: str,
) -> None:
    """Aborta con un mensaje limpio cuando ``cargar_configuracion``
    falla por un fichero ausente o por un perfil activo inválido.

    El objetivo es que el profesor vea **solo** la causa y la ayuda
    para corregirla, sin la traza Python que aparecería por defecto
    al propagarse el ``FileNotFoundError``/``ValueError`` hasta el
    intérprete.

    Args:
        error: Excepción capturada al leer la configuración.
        ruta_config: Ruta del fichero de configuración intentado.

    Raises:
        SystemExit: Siempre, con ``COD_SALIDA_CONFIG_INVALIDA``.
    """
    logger.critical(
        "No se pudo cargar la configuración de %s.\n"
        "  Causa: %s\n"
        "  Revisa que el fichero existe, que es YAML válido y que\n"
        "  'xmpp.perfil_activo' apunta a uno de los perfiles definidos\n"
        "  en 'xmpp.perfiles' (típicamente 'local' o 'servidor').\n"
        "  Si tu fichero está correcto y aun así falla, compara con\n"
        "  el ejemplo de config/config.yaml en el repositorio.",
        ruta_config, error,
    )
    sys.exit(COD_SALIDA_CONFIG_INVALIDA)


def _leer_puerto_web_modo_consulta(ruta_config: str) -> int:
    """Devuelve el ``sistema.puerto_web`` del YAML para el modo
    consulta, tolerando que el bloque ``xmpp`` esté mal configurado.

    El modo consulta abre solo el panel web sobre un fichero SQLite
    y nunca se conecta al servidor XMPP, así que un
    ``xmpp.perfil_activo`` inválido o ausente no debe impedir su
    arranque. Esta función lee el YAML en crudo y devuelve el
    puerto definido en ``sistema.puerto_web`` (o el valor de
    respaldo si la clave no existe, el fichero no se puede leer o
    el contenido no es un YAML válido).

    Args:
        ruta_config: Ruta del fichero de configuración a leer.

    Returns:
        Puerto del panel web que el modo consulta debe usar.
    """
    import yaml  # local: el módulo `yaml` se carga ya por dependencias

    puerto = PUERTO_WEB_DEFECTO
    try:
        with open(ruta_config, "r", encoding="utf-8") as fichero:
            crudo = yaml.safe_load(fichero) or {}
        valor = crudo.get("sistema", {}).get(
            "puerto_web", PUERTO_WEB_DEFECTO,
        )
        puerto = int(valor)
    except (FileNotFoundError, yaml.YAMLError, ValueError, TypeError):
        # En modo consulta cualquier problema con el YAML cae al
        # puerto de respaldo: no hay XMPP ni dependencias del
        # bloque 'xmpp', así que el panel siempre puede arrancar.
        puerto = PUERTO_WEB_DEFECTO
    return puerto


def _localizar_bd_consulta_por_defecto(
    directorio_raiz: str = DIRECTORIO_RAIZ_DATOS,
) -> str | None:
    """Devuelve el fichero ``.db`` más reciente bajo ``directorio_raiz``.

    Recorre recursivamente todo el árbol del directorio indicado y
    selecciona el fichero con extensión ``.db`` cuya marca de tiempo de
    modificación es la más reciente. Sirve para que el modo consulta
    arranque con un valor por defecto razonable cuando el profesor no
    indica ``--db``: lo habitual es querer revisar la última ejecución,
    y el selector del panel web permite cambiar luego a cualquier otra
    base de datos del árbol sin reiniciar el proceso.

    Args:
        directorio_raiz: Ruta del directorio que se va a explorar.
            Por defecto ``data/``, el mismo que utiliza el selector
            del panel web.

    Returns:
        Ruta relativa al fichero ``.db`` más reciente, o ``None`` si
        el directorio no existe o no contiene ningún fichero ``.db``.
    """
    ruta_seleccionada: str | None = None
    if os.path.isdir(directorio_raiz):
        mtime_mejor = float("-inf")
        for directorio_actual, _subdirs, ficheros in os.walk(
            directorio_raiz,
        ):
            for nombre_fichero in ficheros:
                if not nombre_fichero.lower().endswith(EXTENSION_BD):
                    continue
                ruta_absoluta = os.path.join(
                    directorio_actual, nombre_fichero,
                )
                try:
                    mtime = os.path.getmtime(ruta_absoluta)
                except OSError:
                    continue
                if mtime > mtime_mejor:
                    mtime_mejor = mtime
                    ruta_seleccionada = os.path.relpath(ruta_absoluta)
    return ruta_seleccionada


def _validar_perfil_xmpp(config_xmpp: dict) -> None:
    """Valida el perfil XMPP activo y registra el modo de ejecución.

    El supervisor admite dos perfiles, con propósitos distintos:

    * ``local``    → modo de **simulación**: los alumnos reproducen en
      su propio equipo el funcionamiento del laboratorio. Las partidas
      no computan en la evaluación oficial.
    * ``servidor`` → **evaluación definitiva** en el Prosody oficial de
      la asignatura (sinbad2.ujaen.es).

    Cualquier otro valor es un error de configuración y aborta el
    lanzador, para no arrancar el supervisor contra un servidor no
    previsto.

    Args:
        config_xmpp: Diccionario con el perfil XMPP resuelto.

    Raises:
        SystemExit: Si el perfil activo no es ``local`` ni
            ``servidor``.
    """
    perfil = config_xmpp.get("perfil", "?")
    if perfil not in PERFILES_XMPP_ACEPTADOS:
        logger.critical(
            "El perfil XMPP activo es '%s' (%s:%d), que no es válido "
            "para el supervisor.\n"
            "  Edita config/config.yaml y deja 'xmpp.perfil_activo' "
            "con uno de estos valores: %s.\n"
            "  Detalles operativos en doc/MODO_EXAMEN.md.",
            perfil,
            config_xmpp.get("host", "?"),
            int(config_xmpp.get("puerto", 0) or 0),
            ", ".join(sorted(PERFILES_XMPP_ACEPTADOS)),
        )
        sys.exit(3)
    elif perfil == PERFIL_XMPP_SERVIDOR_OFICIAL:
        logger.info(
            "Perfil XMPP 'servidor': evaluación definitiva contra el "
            "Prosody oficial de la asignatura (%s).",
            config_xmpp.get("host", "?"),
        )
    else:
        logger.info(
            "Perfil XMPP 'local': modo de simulación contra un Prosody "
            "local (%s). Las partidas no computan en la evaluación "
            "oficial del examen.",
            config_xmpp.get("host", "?"),
        )


def _validar_xmpp_alcanzable(config_xmpp: dict) -> None:
    """Comprueba que el servidor XMPP del perfil activo acepta
    conexiones TCP antes de arrancar el supervisor.

    Sin esta comprobación, si el servidor no es accesible (VPN caída,
    Prosody local sin arrancar, host o puerto mal configurados), SPADE
    intentaría conectar y el supervisor se quedaría esperando un
    timeout largo y poco informativo. Esta función detecta el problema
    de inmediato y aborta con un mensaje que indica cómo resolverlo.

    Args:
        config_xmpp: Diccionario con el perfil XMPP resuelto.

    Raises:
        SystemExit: Si el ``host:puerto`` del perfil no acepta
            conexiones TCP.
    """
    host = config_xmpp.get("host", "localhost")
    puerto = int(config_xmpp.get("puerto", 5222) or 5222)
    perfil = config_xmpp.get("perfil", "?")

    alcanzable = False
    try:
        conexion = socket.create_connection(
            (host, puerto), timeout=TIMEOUT_COMPROBACION_XMPP,
        )
        conexion.close()
        alcanzable = True
    except (OSError, ValueError):
        alcanzable = False

    if not alcanzable:
        if perfil == PERFIL_XMPP_SERVIDOR_OFICIAL:
            ayuda = (
                "  El perfil 'servidor' apunta al Prosody de la "
                "asignatura: comprueba que estás en la red de la UJA "
                "o conectado por VPN.\n"
                f"      nc -zv {host} {puerto}"
            )
        else:
            ayuda = (
                "  El perfil 'local' necesita el Prosody local del "
                "repositorio de infraestructura de la asignatura: "
                "arráncalo antes de lanzar el supervisor.\n"
                "      docker compose up -d   (en ese repositorio)"
            )
        logger.critical(
            "El servidor XMPP del perfil '%s' no es accesible en "
            "%s:%d.\n"
            "%s\n"
            "  Revisa también 'xmpp.perfil_activo' y el host/puerto "
            "del perfil en config/config.yaml.",
            perfil, host, puerto, ayuda,
        )
        sys.exit(5)
    logger.info(
        "Servidor XMPP accesible en %s:%d.", host, puerto,
    )


def _obtener_password_supervisor(config_xmpp: dict) -> str | None:
    """Devuelve la contraseña que debe usar el supervisor según el
    perfil XMPP activo.

    Cuando el perfil activo es ``servidor`` (sinbad2.ujaen.es) la
    contraseña se lee de la variable de entorno
    ``SSMMAA_SUPERVISOR_PASSWORD`` y el script aborta si no está
    definida. En el perfil ``local`` se devuelve ``None`` para que
    ``crear_agente`` use ``password_defecto`` del YAML, lo que permite
    arrancar el supervisor contra un Prosody local en pruebas sin
    requisitos adicionales y, al mismo tiempo, blinda la cuenta
    supervisor del servidor oficial frente a la contraseña pública del
    repositorio.

    Args:
        config_xmpp: Perfil XMPP resuelto. La condición decisiva es
            ``config_xmpp["perfil"]``.

    Returns:
        ``str`` con la contraseña fuerte si el perfil la exige,
        ``None`` si el perfil permite caer al ``password_defecto``.

    Raises:
        SystemExit: En un perfil que requiere contraseña fuerte y la
            variable de entorno no está definida o está vacía.
    """
    perfil = config_xmpp.get("perfil", "local")
    password_resultado = None

    if perfil in PERFILES_REQUIEREN_PASSWORD_FUERTE:
        password = os.environ.get(
            VARIABLE_PASSWORD_SUPERVISOR, "",
        ).strip()
        if not password:
            logger.critical(
                "El perfil XMPP '%s' requiere la variable de entorno "
                "%s, pero no está definida o está vacía.\n"
                "  El supervisor del servidor de la asignatura NO "
                "debe usar la 'password_defecto' del config.yaml: ese "
                "fichero es público y un alumno podría suplantarlo. "
                "Define la contraseña fuerte antes de arrancar:\n"
                "      export %s='clave_fuerte_del_profesor'\n"
                "      python supervisor_main.py\n"
                "  Si todavía no has fijado la contraseña en el "
                "servidor:\n"
                "      ejecuta 'prosodyctl passwd supervisor@<dominio>'\n"
                "      dentro del contenedor Prosody (ver el repositorio\n"
                "      de infraestructura de la asignatura\n"
                "      https://gitlab.com/ssmmaa/infraestructurassmmaa/ssmmaa-infraestructura).",
                perfil, VARIABLE_PASSWORD_SUPERVISOR,
                VARIABLE_PASSWORD_SUPERVISOR,
            )
            sys.exit(2)
        password_resultado = password

    return password_resultado


def _registrar_senales_parada(
    bucle: asyncio.AbstractEventLoop,
    evento_parada: asyncio.Event,
    mensaje: str,
) -> None:
    """Registra manejadores de SIGINT/SIGTERM de forma multiplataforma.

    En Unix/macOS se usa ``loop.add_signal_handler``, que permite
    gestionar señales directamente dentro del bucle asyncio.
    En Windows esa API no está disponible, por lo que se recurre a
    ``signal.signal`` con ``call_soon_threadsafe`` para activar el
    evento de parada de forma segura desde el hilo de la señal.

    Args:
        bucle: Bucle de eventos asyncio en ejecución.
        evento_parada: Evento que se activará al recibir la señal.
        mensaje: Texto descriptivo para el log al recibir la señal.
    """
    if sys.platform != "win32":
        # Unix/macOS — add_signal_handler es la forma recomendada
        def _senal_unix() -> None:
            logger.info("Señal de parada recibida. %s", mensaje)
            evento_parada.set()

        bucle.add_signal_handler(signal.SIGINT, _senal_unix)
        bucle.add_signal_handler(signal.SIGTERM, _senal_unix)
    else:
        # Windows — signal.signal como alternativa; se usa
        # call_soon_threadsafe porque el handler se ejecuta en el
        # hilo principal, fuera del bucle asyncio.
        def _senal_windows(_signum: int, _frame: Any) -> None:
            logger.info("Señal de parada recibida. %s", mensaje)
            bucle.call_soon_threadsafe(evento_parada.set)

        signal.signal(signal.SIGINT, _senal_windows)


def parsear_argumentos() -> argparse.Namespace:
    """Parsea los argumentos de línea de órdenes.

    El supervisor de esta rama se ejecuta siempre en modo examen, por
    lo que no hay argumento ``--modo``: la decisión del profesor es la
    submodalidad (``--submodo``). Adicionalmente, ``--consulta`` abre
    solo el panel web sobre un fichero de persistencia existente, sin
    conectar con XMPP.

    Returns:
        Namespace con los argumentos: submodo, consulta, config,
        intervalo, db, puerto.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Lanzador del Agente Supervisor para la prueba de examen"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Submodalidades del examen (--submodo):\n"
            "  grupo       (default) sala MUC única\n"
            "              examen@examen.<dominio>\n"
            "              (config/sala_examen.yaml)\n"
            "  individual  30 salas PC-01..PC-30 en examen.<dominio>\n"
            "              (config/sala_examen_individual.yaml)\n"
            "\n"
            "Modo consulta (--consulta):\n"
            "  Abre solo el panel web sobre un fichero de persistencia\n"
            "  ya existente, sin conectar con XMPP. Si no se indica\n"
            "  --db, se auto-selecciona el .db más reciente bajo data/\n"
            "  (recursivo). El selector del panel permite cambiar a\n"
            "  cualquier otro fichero del árbol sin reiniciar.\n"
            "\n"
            "El servidor garantiza la prelación del supervisor con\n"
            'restrict_room_creation="admin" sobre el componente del\n'
            "examen. La evaluación oficial se ejecuta contra el\n"
            "servidor de la asignatura (sinbad2.ujaen.es); el perfil\n"
            "'local' permite simular el laboratorio."
        ),
    )
    parser.add_argument(
        "--submodo",
        choices=list(SUBMODOS_EXAMEN),
        default=SUBMODO_EXAMEN_POR_DEFECTO,
        help=(
            "Submodalidad del examen. "
            f"Valores: {', '.join(SUBMODOS_EXAMEN)} "
            f"(default: {SUBMODO_EXAMEN_POR_DEFECTO})."
        ),
    )
    parser.add_argument(
        "--consulta",
        action="store_true",
        help=(
            "Abre solo el panel web para revisar un fichero de "
            "persistencia existente, sin conectar con el servidor "
            "XMPP. Si no se indica --db, el lanzador selecciona "
            "automáticamente el fichero .db más reciente bajo "
            "data/ (recorriendo todo el árbol). El selector del "
            "panel permite luego cambiar a cualquier otro fichero."
        ),
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Ruta al fichero de configuración (default: config/config.yaml)",
    )
    parser.add_argument(
        "--intervalo",
        type=int,
        default=INTERVALO_POLL_MUC_DEFECTO,
        help=(
            "Intervalo en segundos entre consultas a las salas MUC "
            f"(default: {INTERVALO_POLL_MUC_DEFECTO})"
        ),
    )
    parser.add_argument(
        "--db",
        default=None,
        help=(
            "Ruta al fichero SQLite de persistencia. En modo en "
            "directo, si no se indica, se elige automáticamente "
            "según el submodo: 'data/examen.db' para 'grupo' y "
            "'data/examen_individual.db' para 'individual'. En "
            "modo consulta, si no se indica, se selecciona el "
            "fichero .db más reciente bajo data/ (recursivo)."
        ),
    )
    parser.add_argument(
        "--puerto",
        type=int,
        default=None,
        help=(
            "Puerto del panel web. Si no se indica, se usa "
            "'sistema.puerto_web' de config.yaml "
            f"(valor de respaldo: {PUERTO_WEB_DEFECTO})."
        ),
    )
    parser.add_argument(
        "--fichero-salas",
        default=None,
        help=(
            "Ruta al fichero YAML con las salas que el supervisor debe "
            "pre-crear. Si no se indica, se usa el fichero oficial "
            "asociado al submodo ('config/sala_examen.yaml' para "
            "'grupo', 'config/sala_examen_individual.yaml' para "
            "'individual'). Útil para herramientas de evaluación que "
            "necesitan suministrar una lista reducida de salas (por "
            "ejemplo, una única sala 'PC-NN' por alumno en lugar de "
            "las 30 del aula)."
        ),
    )
    argumentos = parser.parse_args()
    return argumentos


# ══════════════════════════════════════════════════════════════════
#  Modo consulta — solo panel web sobre datos históricos
# ══════════════════════════════════════════════════════════════════

async def ejecutar_modo_consulta(
    ruta_db: str,
    puerto: int,
    evento_parada: asyncio.Event | None = None,
) -> None:
    """Abre el panel web sobre un fichero de persistencia existente.

    El modo consulta no conecta con el servidor XMPP ni crea ninguna
    sala ni behaviour: se limita a abrir el almacén SQLite en modo de
    lectura y a exponer el panel web para revisar las ejecuciones
    pasadas (informes, registro de eventos y clasificación). Es la
    contrapartida, en esta rama de examen, del modo consulta del
    Agente Supervisor de la rama ``feature/agente-supervisor``.

    Args:
        ruta_db: Ruta al fichero SQLite con los datos a revisar.
        puerto: Puerto en el que escuchará el panel web.
        evento_parada: Evento que detiene el panel cuando se activa.
            En la ejecución normal no se indica y la función crea uno
            propio, gobernado por las señales SIGINT/SIGTERM. Los tests
            inyectan su propio evento para poder cerrar el panel de
            forma ordenada sin enviar señales al proceso.
    """
    logger.info("Modo CONSULTA — solo panel web (sin conexión XMPP)")
    logger.info("Fichero de persistencia: %s", ruta_db)

    if not os.path.exists(ruta_db):
        logger.critical(
            "El fichero de persistencia '%s' no existe. Indica una "
            "ruta válida con --db o ejecuta antes el supervisor para "
            "generar la base de datos del submodo correspondiente.",
            ruta_db,
        )
        sys.exit(4)

    # Almacén de solo lectura: no crea una ejecución nueva.
    almacen = AlmacenSupervisor(ruta_db)
    ejecuciones = almacen.listar_ejecuciones()
    logger.info(
        "Ejecuciones encontradas en la base de datos: %d",
        len(ejecuciones),
    )

    # Objeto ligero que el panel consulta en lugar del agente real.
    # En modo consulta solo se usan los endpoints de ejecuciones
    # pasadas, no el estado en directo, así que basta con exponer
    # estructuras vacías y el almacén. El atributo ``ruta_db`` se
    # mantiene actualizado por el handler de cambio de BD, que el
    # panel del profesor invoca para revisar otro fichero sin tener
    # que relanzar el supervisor.
    agente_consulta = SimpleNamespace(
        salas_muc=[],
        informes_por_sala={},
        ocupantes_por_sala={},
        log_por_sala={},
        almacen=almacen,
        ruta_db=ruta_db,
    )

    # Si el llamador no aporta su propio evento de parada, se crea uno
    # gobernado por las señales del sistema operativo (Ctrl+C).
    if evento_parada is None:
        evento_parada = asyncio.Event()

    # Panel web independiente, sin SPADE ni XMPP. Todas las claves de
    # la aplicación (incluido el evento de parada) se fijan ANTES de
    # arrancar el runner: aiohttp desaconseja modificar el estado de
    # una aplicación ya iniciada.
    app = web.Application()
    registrar_rutas_supervisor(app)
    app["agente"] = agente_consulta
    app["modo"] = "consulta"
    app["evento_parada"] = evento_parada

    runner = web.AppRunner(app)
    await runner.setup()
    sitio = web.TCPSite(runner, "0.0.0.0", puerto)
    await sitio.start()

    url_panel = f"http://localhost:{puerto}/supervisor"
    logger.info("Panel web disponible en %s", url_panel)
    logger.info(
        "Modo consulta: selecciona una ejecución pasada en el "
        "desplegable del panel. Pulsa Ctrl+C para salir.",
    )
    webbrowser.open(url_panel)

    # Mantener en ejecución hasta la señal de parada.
    bucle = asyncio.get_running_loop()
    _registrar_senales_parada(bucle, evento_parada, "Cerrando el panel...")

    await evento_parada.wait()

    # El handler de cambio de BD puede haber sustituido el almacén
    # original por uno nuevo; al cerrar, se libera el que esté
    # activo en ese momento, no la referencia inicial.
    almacen_activo = getattr(agente_consulta, "almacen", almacen)
    if almacen_activo is not None:
        almacen_activo.cerrar()
    await runner.shutdown()
    await runner.cleanup()
    logger.info("Modo consulta finalizado.")


# ══════════════════════════════════════════════════════════════════
#  Ejecución del supervisor del examen
# ══════════════════════════════════════════════════════════════════

async def ejecutar_supervisor(
    submodo: str,
    ruta_config: str,
    intervalo: int,
    ruta_db: str,
    puerto: int,
    ruta_fichero_salas: str | None = None,
) -> None:
    """Crea las salas MUC del examen, arranca el supervisor XMPP
    completo y monitoriza las partidas en tiempo real.

    Args:
        submodo: Submodalidad del examen (``"grupo"`` o
            ``"individual"``).
        ruta_config: Ruta al fichero config.yaml.
        ruta_fichero_salas: Ruta opcional a un YAML con la lista de
            salas a pre-crear. Si es ``None`` se usa el oficial del
            submodo. Permite que herramientas externas suministren
            una lista reducida (por ejemplo, una única sala por
            alumno en evaluaciones individuales).
        intervalo: Segundos entre cada consulta a las salas MUC.
        ruta_db: Ruta al fichero SQLite de persistencia.
        puerto: Puerto del dashboard web.
    """
    clave_modo = _resolver_clave_examen(submodo)
    etiqueta_modo = clave_modo.upper()
    ruta_salas = ruta_fichero_salas or FICHERO_SALAS[clave_modo]

    logger.info("Modo %s — fichero de salas: %s", etiqueta_modo, ruta_salas)

    # ── Cargar configuración ───────────────────────────────────
    logger.info("Cargando configuración desde: %s", ruta_config)
    config = cargar_configuracion(ruta_config)
    config_xmpp = config["xmpp"]

    # Validar que el perfil XMPP activo es uno de los admitidos
    # ('local' o 'servidor') y registrar el modo de ejecución.
    _validar_perfil_xmpp(config_xmpp)

    # Comprobar que el servidor XMPP responde antes de seguir. Evita
    # que el supervisor se quede esperando un timeout largo de SPADE
    # si el servidor no es accesible (VPN caída, Prosody local sin
    # arrancar, host/puerto mal configurados).
    _validar_xmpp_alcanzable(config_xmpp)

    # Redirigir el componente MUC al dedicado del examen
    # ('examen.<dominio>') si el perfil lo define. Detalle:
    # doc/CONFIGURACION_SINBAD2_MUC_DEDICADO.md.
    aplicar_servicio_muc_segun_modo(MODO_EXAMEN, config_xmpp)

    # Ajustar nivel de logging según configuración del sistema
    config_sistema = config.get("sistema", {})
    nivel_log = config_sistema.get("nivel_log", "INFO")
    logging.getLogger().setLevel(getattr(logging, nivel_log, logging.INFO))

    # ── Crear salas MUC desde el fichero correspondiente ────────
    torneos = cargar_torneos(ruta_salas)
    if torneos:
        await crear_salas_torneos(torneos, config_xmpp)
    else:
        logger.warning(
            "No se encontraron salas en %s. El supervisor usará "
            "el descubrimiento automático.",
            ruta_salas,
        )

    # ── Extraer los nombres de las salas del fichero de torneos ──
    # Cada entrada del fichero tiene una clave "sala" con el nombre
    # de la sala MUC. Se pasan al agente para que se una directamente
    # a ellas, sin depender del descubrimiento automático XEP-0030
    # (que puede no encontrarlas si acaban de ser creadas).
    salas_del_modo = [t["sala"] for t in torneos if "sala" in t]

    if salas_del_modo:
        logger.info(
            "Salas del modo %s: %s",
            etiqueta_modo, ", ".join(salas_del_modo),
        )

    # ── Crear el agente con la factoría ────────────────────────
    # Cuando el perfil XMPP activo es 'servidor' (sinbad2), la
    # contraseña se toma de la variable de entorno
    # SSMMAA_SUPERVISOR_PASSWORD para que el JID supervisor no pueda
    # ser suplantado por un alumno que conoce 'password_defecto' del
    # YAML público. En el perfil 'local' se devuelve None y
    # crear_agente cae al 'password_defecto' del perfil.
    password_supervisor = _obtener_password_supervisor(config_xmpp)
    logger.info("Creando Agente Supervisor...")
    agente = crear_agente(
        AgenteSupervisor, "supervisor", config_xmpp,
        contrasena=password_supervisor,
    )

    # Inyectar los atributos que setup() espera encontrar.
    # Se usa descubrimiento "manual" con la lista explícita de salas
    # extraída del fichero del submodo, para que el supervisor se una
    # exactamente a las salas correctas.
    agente.config_xmpp = config_xmpp
    agente.config_parametros = {
        "intervalo_consulta": intervalo,
        "ruta_db": ruta_db,
        "puerto_web": puerto,
        "descubrimiento_salas": "manual",
        "salas_muc": salas_del_modo,
    }
    agente.config_llm = None

    # Inyectar el modo y el submodo de ejecución para que el agente
    # pueda condicionar su comportamiento sin depender de este
    # lanzador. En esta rama el modo es siempre 'examen'; el submodo
    # distingue entre la sala única (grupo) y las 30 salas PC-NN
    # (individual).
    agente.modo = MODO_EXAMEN
    agente.submodo = submodo

    # ── Arrancar el agente con la factoría ─────────────────────
    await arrancar_agente(agente, config_xmpp)
    logger.info(
        "Supervisor arrancado en modo %s (JID: %s, intervalo: %d s)",
        etiqueta_modo, agente.jid, intervalo,
    )

    # ── Mantener en ejecución hasta señal de parada ────────────
    evento_parada = asyncio.Event()
    bucle = asyncio.get_running_loop()
    _registrar_senales_parada(
        bucle, evento_parada, "Deteniendo supervisor...",
    )

    # Exponer el evento de parada en la app web para que el
    # manejador de finalización del torneo (P-09) pueda activarlo
    # desde el panel sin depender de señales del sistema operativo.
    if hasattr(agente, "web") and hasattr(agente.web, "app"):
        agente.web.app["evento_parada"] = evento_parada
        agente.web.app["modo"] = MODO_EXAMEN

    # Abrir el panel web automáticamente en el navegador del profesor.
    url_panel = f"http://localhost:{puerto}/supervisor"
    logger.info("Panel web disponible en %s", url_panel)
    webbrowser.open(url_panel)

    logger.info("Supervisor en ejecución. Pulsa Ctrl+C para detener.")
    await evento_parada.wait()

    # ── Detener el agente de forma ordenada ────────────────────
    # El apagado sigue una secuencia deliberada:
    #   1. Cerrar la persistencia: los datos de la sesión quedan
    #      guardados ANTES de cualquier tarea de limpieza.
    #   2. Expulsar a los ocupantes que aún estén en las salas, para
    #      que sus agentes finalicen de forma limpia.
    #   3. Destruir las salas del examen: la siguiente ejecución del
    #      supervisor las creará de cero, sin estado residual.
    # Los pasos 2 y 3 necesitan el cliente XMPP todavía conectado, así
    # que van antes de stop(); se protegen con try/except para que un
    # fallo de limpieza nunca impida el apagado ordenado.
    await agente.detener_persistencia()
    try:
        await agente.expulsar_ocupantes_salas()
        await agente.eliminar_salas_examen()
    except Exception as error:  # noqa: BLE001
        logger.warning(
            "No se pudo completar la limpieza de las salas MUC al "
            "apagar el supervisor: %s", error,
        )
    await agente.stop()
    logger.info("Supervisor detenido correctamente.")


# ══════════════════════════════════════════════════════════════════
#  Punto de entrada
# ══════════════════════════════════════════════════════════════════

def main() -> None:
    """Punto de entrada principal del lanzador del supervisor.

    Parsea argumentos, resuelve el fichero de persistencia según la
    submodalidad y arranca el supervisor del examen o, si se indica
    ``--consulta``, abre el panel web sobre los datos históricos.

    Los errores tratables (fichero de configuración ausente, perfil
    XMPP mal escrito, etc.) se reportan como un único mensaje
    ``critical`` con ayuda y se abandona la ejecución con un código
    de salida específico, sin traza Python.
    """
    argumentos = parsear_argumentos()

    # Validación de la configuración: solo es necesaria cuando el
    # supervisor va a conectarse al servidor XMPP. El modo consulta
    # (``--consulta``) abre únicamente el panel web sobre un fichero
    # SQLite y nunca se conecta a XMPP, así que un perfil mal
    # configurado o ausente NO debe abortar su arranque. Para los
    # arranques de directo, se carga aquí la configuración una sola
    # vez y se reaprovecha al leer el puerto.
    config_inicial: dict | None = None
    if not argumentos.consulta:
        try:
            config_inicial = cargar_configuracion(argumentos.config)
        except (FileNotFoundError, ValueError) as error:
            _abortar_por_configuracion_invalida(
                error, argumentos.config,
            )
            return  # noqa: type-narrowing — sys.exit ya no vuelve

    # Resolución del fichero de persistencia. La política depende del
    # modo de ejecución:
    #
    #   * Modo en directo: si el profesor no ha pasado --db, se usa la
    #     ruta asociada a la submodalidad. Las dos submodalidades
    #     tienen BD separadas ('data/examen.db' para 'grupo' y
    #     'data/examen_individual.db' para 'individual') para que la
    #     trazabilidad por submodalidad quede aislada.
    #
    #   * Modo consulta: la submodalidad es irrelevante (no se crean
    #     salas ni se conecta a XMPP), así que el lanzador localiza
    #     automáticamente el fichero `.db` más reciente bajo `data/`,
    #     recorriendo todo el árbol de subdirectorios. El selector
    #     del panel permite cambiar a cualquier otro fichero del
    #     árbol sin reiniciar el proceso.
    #
    # Cualquier --db explícito prevalece sobre el valor por defecto.
    if argumentos.consulta:
        if argumentos.db is None:
            ruta_bd_reciente = _localizar_bd_consulta_por_defecto()
            if ruta_bd_reciente is None:
                logger.critical(
                    "No se encontró ningún fichero '.db' bajo el "
                    "directorio '%s/'. Ejecuta antes el supervisor "
                    "para generar una base de datos, o indica una "
                    "ruta explícita con --db.",
                    DIRECTORIO_RAIZ_DATOS,
                )
                sys.exit(COD_SALIDA_BD_NO_EXISTE)
            argumentos.db = ruta_bd_reciente
            logger.info(
                "Base de datos auto-seleccionada para el modo "
                "consulta (la más reciente bajo '%s/'): %s",
                DIRECTORIO_RAIZ_DATOS, argumentos.db,
            )
    else:
        clave_modo = _resolver_clave_examen(argumentos.submodo)
        if argumentos.db is None:
            argumentos.db = RUTA_DB_POR_SUBMODO[clave_modo]
            logger.info(
                "Base de datos SQLite resuelta automáticamente para "
                "el submodo '%s': %s",
                argumentos.submodo, argumentos.db,
            )

    # Resolución del puerto del panel web: se prefiere --puerto sobre
    # 'sistema.puerto_web' del config.yaml, y a falta de ambos el
    # valor de respaldo. En el modo en directo la configuración ya
    # está cargada y validada; en el modo consulta se lee solo la
    # clave 'sistema.puerto_web', tolerando errores en el bloque
    # 'xmpp' que aquí no se usa.
    if argumentos.puerto is None:
        if config_inicial is not None:
            argumentos.puerto = int(
                config_inicial.get("sistema", {}).get(
                    "puerto_web", PUERTO_WEB_DEFECTO,
                ),
            )
        else:
            argumentos.puerto = _leer_puerto_web_modo_consulta(
                argumentos.config,
            )
        logger.info(
            "Puerto del panel web resuelto: %d", argumentos.puerto,
        )

    try:
        if argumentos.consulta:
            asyncio.run(
                ejecutar_modo_consulta(argumentos.db, argumentos.puerto),
            )
        else:
            asyncio.run(
                ejecutar_supervisor(
                    argumentos.submodo, argumentos.config,
                    argumentos.intervalo, argumentos.db, argumentos.puerto,
                    argumentos.fichero_salas,
                ),
            )
    except KeyboardInterrupt:
        logger.info("Ejecución interrumpida por el usuario.")
    except (FileNotFoundError, ValueError) as error:
        # Salvaguarda para el modo en directo: si la configuración
        # cambia entre la validación temprana y la lectura
        # definitiva (p. ej., el profesor edita el fichero a mitad
        # de arranque), se reporta también limpio. El modo consulta
        # ya tolera estos errores internamente y no debería caer
        # aquí.
        _abortar_por_configuracion_invalida(error, argumentos.config)


if __name__ == "__main__":
    main()
