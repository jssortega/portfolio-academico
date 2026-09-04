"""Lanzador principal del sistema Tic-Tac-Toe Multiagente.

Lee la configuración de config.yaml y agents.yaml, construye los JIDs
de cada agente a partir del perfil XMPP activo, importa dinámicamente
las clases con importlib y arranca todos los agentes en orden ALEATORIO.

El orden aleatorio es deliberado: fuerza que el diseño de los agentes
tolere la ausencia temporal de otros agentes. Si el sistema solo funciona
cuando los agentes arrancan en un orden determinado (por ejemplo, primero
los tableros y luego los jugadores), eso indica un defecto de diseño.

Uso:
    python main.py
    python main.py --config config/config.yaml --agents config/agents.yaml
"""

import argparse
import asyncio
import importlib
import logging
import random
import signal
import sys
from typing import Any

from spade.agent import Agent

from config.configuracion import (
    cargar_configuracion,
    cargar_plantillas,
    cargar_torneos,
    generar_agentes,
    normalizar_nombre_sala,
)
from utils import (
    arrancar_agente,
    comprobar_supervisor_activo,
    crear_agente,
)

# ── Códigos de salida ──────────────────────────────────────────
# Código devuelto por main() cuando la sonda detecta que el
# supervisor del examen NO está activo (la sala MUC no existe en
# el servidor). Es distinto de los códigos de error genéricos (1)
# para que un script externo pueda diferenciar "el alumno arrancó
# antes que el profesor" de un error de configuración cualquiera.
CODIGO_SALIDA_SUPERVISOR_INACTIVO = 7

# Modalidad que exige que el supervisor del profesor haya creado
# previamente la sala MUC. Solo en este caso tiene sentido lanzar
# la sonda al servidor.
MODALIDAD_REQUIERE_SUPERVISOR = "examen"

# ── Configuración global del logging ───────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


def parsear_argumentos() -> argparse.Namespace:
    """Analiza los argumentos de la línea de órdenes.

    Returns:
        Namespace con los argumentos: config (ruta a config.yaml)
        y agents (ruta a agents.yaml).
    """
    parser = argparse.ArgumentParser(
        description="Lanzador del sistema Tic-Tac-Toe Multiagente",
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Ruta al fichero de configuración (default: config/config.yaml)",
    )
    parser.add_argument(
        "--agents",
        default="config/agents.yaml",
        help="Ruta al fichero de agentes (default: config/agents.yaml)",
    )
    parser.add_argument(
        "--torneos",
        default="config/torneos.yaml",
        help="Ruta al fichero de torneos (default: config/torneos.yaml)",
    )
    argumentos = parser.parse_args()
    return argumentos


def importar_clase_agente(modulo_ruta: str, clase_nombre: str) -> type:
    """Importa dinámicamente una clase de agente usando importlib.

    Permite que los agentes se definan en agents.yaml sin que main.py
    tenga que conocer de antemano las clases concretas. Esto facilita
    añadir nuevos tipos de agentes sin modificar el lanzador.

    Args:
        modulo_ruta: Ruta del módulo en notación de puntos
            (ej: "agentes.agente_tablero").
        clase_nombre: Nombre de la clase dentro del módulo
            (ej: "AgenteTablero").

    Returns:
        La clase Python del agente, lista para instanciar.

    Raises:
        ImportError: Si el módulo no se puede importar.
        AttributeError: Si la clase no existe en el módulo.
    """
    clase_resultado = None

    try:
        modulo = importlib.import_module(modulo_ruta)
        clase_resultado = getattr(modulo, clase_nombre)
        logger.debug("Importado: %s.%s", modulo_ruta, clase_nombre)
    except ImportError as error:
        logger.error(
            "No se pudo importar el módulo '%s': %s", modulo_ruta, error
        )
        raise
    except AttributeError as error:
        logger.error(
            "Clase '%s' no encontrada en módulo '%s': %s",
            clase_nombre,
            modulo_ruta,
            error,
        )
        raise

    return clase_resultado


def crear_instancia_agente(
    definicion: dict[str, Any],
    config_xmpp: dict[str, Any],
    config_llm: dict[str, Any] | None,
) -> Agent:
    """Crea una instancia de agente SPADE a partir de su definición YAML.

    Construye el JID del agente, importa su clase dinámicamente y
    la instancia con los parámetros de configuración. Si el agente
    necesita configuración LLM (estrategia nivel 4), se inyecta como
    parte de los parámetros.

    Args:
        definicion: Diccionario con la definición del agente leída
            de agents.yaml (nombre, clase, modulo, parametros, etc.).
        config_xmpp: Configuración XMPP resuelta (perfil activo).
        config_llm: Configuración LLM resuelta (perfil activo) o None.

    Returns:
        Instancia del agente SPADE, sin arrancar.
    """
    # Importar la clase del agente dinámicamente
    clase_agente = importar_clase_agente(
        definicion["modulo"], definicion["clase"]
    )

    # Instanciar el agente con la factoría crear_agente. La factoría
    # lee del perfil XMPP TODOS los datos de conexión (dominio para
    # construir el JID, puerto, verify_security y contraseña) y los
    # pasa al constructor de SPADE. De este modo los valores de
    # conexión al servidor viven exclusivamente en config.yaml: main.py
    # no los reconstruye ni los manipula. Así se evita la
    # inconsistencia de instanciar el agente sin el puerto del perfil
    # (SPADE asumiría el 5222 por defecto) cuando el servidor de la
    # asignatura escucha en otro puerto, como el 8022 de sinbad2.
    agente = crear_agente(
        clase_agente, definicion["nombre"], config_xmpp,
    )

    # Inyectar parámetros específicos del agente (id_tablero, puerto_web,
    # nivel_estrategia, etc.) como atributos accesibles desde setup()
    parametros = definicion.get("parametros", {})
    agente.config_parametros = parametros

    # Inyectar configuración de infraestructura para que el agente
    # pueda acceder a la sala MUC, a los tiempos de espera, etc. sin
    # codificar esos valores directamente en el código fuente.
    agente.config_xmpp = config_xmpp
    agente.config_llm = config_llm

    nick_muc = parametros.get("nick_muc", "—")
    logger.info(
        "Agente creado: %s (%s.%s) — nick MUC: '%s' — parámetros: %s",
        agente.jid,
        definicion["modulo"],
        definicion["clase"],
        nick_muc,
        parametros,
    )

    instancia_resultado = agente
    return instancia_resultado


async def crear_salas_torneos(
    torneos: list[dict[str, Any]],
    config_xmpp: dict[str, Any],
) -> dict[str, str]:
    """Crea las salas MUC necesarias para los torneos definidos.

    En XMPP, una sala MUC se crea automáticamente cuando el primer
    ocupante se une a un JID que no existe en el servicio de
    conferencias.  Esta función utiliza un agente temporal que se
    une brevemente a cada sala para garantizar que existe, y luego
    se desconecta.

    Además construye un diccionario de asignación que indica a qué
    sala debe unirse cada tablero y cada jugador.

    Args:
        torneos: Lista de definiciones de torneos leída de
            torneos.yaml.
        config_xmpp: Configuración XMPP resuelta (perfil activo).

    Returns:
        Diccionario de asignaciones ``{nombre_agente: nombre_sala}``
        que se inyectará como ``sala_asignada`` en cada agente.
    """
    asignaciones: dict[str, str] = {}

    if not torneos:
        return asignaciones

    servicio_muc = config_xmpp.get("servicio_muc", "conference.localhost")
    dominio = config_xmpp.get("dominio", "localhost")
    password = config_xmpp.get("password_defecto", "secret")

    # Crear un agente temporal para unirse a las salas y crearlas
    jid_creador = f"_creador_salas@{dominio}"

    agente_temporal = crear_agente(Agent, "_creador_salas", config_xmpp)

    try:
        await arrancar_agente(agente_temporal, config_xmpp)

        for torneo in torneos:
            nombre_sala = torneo.get("sala", torneo.get("nombre", ""))
            if not nombre_sala:
                continue

            # Canonizar el nombre con la forma común (la misma que
            # usa el supervisor del profesor) para que la sala que se
            # crea aquí coincida exactamente con la que esperan tanto
            # el supervisor como el resto de agentes, sin discrepancias
            # por mayúsculas, espacios o ceros a la izquierda.
            nombre_canonico = normalizar_nombre_sala(nombre_sala)
            jid_sala = f"{nombre_canonico}@{servicio_muc}"

            # Suscribirse a la sala la crea si no existe
            agente_temporal.presence.subscribe(jid_sala)
            logger.info(
                "Sala MUC '%s' preparada para torneo '%s'",
                jid_sala, torneo.get("nombre", nombre_sala),
            )

            # Registrar las asignaciones de tableros y jugadores
            for tablero in torneo.get("tableros", []):
                asignaciones[tablero] = nombre_canonico
            for jugador in torneo.get("jugadores", []):
                asignaciones[jugador] = nombre_canonico

        # Esperar un momento para que las suscripciones se procesen
        await asyncio.sleep(1)

    except Exception as error:
        logger.warning(
            "Error al crear salas de torneos: %s. "
            "Los agentes usarán la sala por defecto.",
            error,
        )
    finally:
        try:
            await agente_temporal.stop()
        except Exception:
            pass

    logger.info(
        "Asignaciones de torneos: %d agentes → salas asignadas",
        len(asignaciones),
    )

    return asignaciones


async def arrancar_sistema(
    ruta_config: str, ruta_agentes: str, ruta_torneos: str,
) -> None:
    """Arranca todo el sistema multiagente.

    Carga la configuración, crea las salas de los torneos definidos
    (si existen), crea las instancias de los agentes en orden ALEATORIO
    y los arranca con retardos aleatorios entre sí para simular un
    entorno realista.

    Args:
        ruta_config: Ruta al fichero config.yaml.
        ruta_agentes: Ruta al fichero agents.yaml.
        ruta_torneos: Ruta al fichero torneos.yaml.
    """
    # ── Cargar configuración ───────────────────────────────────
    logger.info("Cargando configuración desde: %s", ruta_config)
    config = cargar_configuracion(ruta_config)
    config_xmpp = config["xmpp"]
    config_llm = config["llm"]
    config_sistema = config["sistema"]
    seccion_alumno = config.get("alumno", {})

    # Ajustar nivel de logging según configuración
    nivel_log = config_sistema.get("nivel_log", "INFO")
    logging.getLogger().setLevel(getattr(logging, nivel_log, logging.INFO))

    # ── Normalización explícita de la sala destino ─────────────
    # 'cargar_configuracion' ya canoniza 'alumno.pc' al formato
    # 'pc-NN' mediante 'normalizar_nombre_sala' (la forma común que
    # comparte con el supervisor). Aquí se emite un log explícito
    # para que el alumno vea, antes de cualquier intento de
    # conexión, a qué sala se va a unir realmente: si escribió
    # 'PC-5', debe leer 'pc-05@examen.<dominio>'. Este es el
    # único punto donde se mira la sala MUC desde main.py, de modo
    # que el alumno puede confiar en lo que aparece aquí.
    sala_muc_completa = config_xmpp.get("sala_muc_completa", "")
    modalidad = (seccion_alumno.get("modalidad") or "").strip()
    submodo = (seccion_alumno.get("submodo") or "").strip()
    if modalidad == MODALIDAD_REQUIERE_SUPERVISOR:
        logger.info(
            "Modo examen activo (submodo '%s'): los agentes se unirán "
            "a la sala MUC '%s' (nombre normalizado desde el "
            "config.yaml del alumno).",
            submodo or "?", sala_muc_completa,
        )
    else:
        logger.info(
            "Modalidad activa: '%s'. Sala MUC destino: '%s'.",
            modalidad or "?", sala_muc_completa,
        )

    # ── Sonda del supervisor (solo modalidad examen) ────────────
    # Antes de crear los agentes reales, se comprueba con UNA
    # consulta disco#info si la sala MUC del examen está creada.
    # Si el supervisor del profesor no la ha creado todavía, el
    # lanzador aborta SIN crear ningún agente: así el alumno ve
    # el motivo UNA sola vez, en lugar de 15 errores idénticos.
    if modalidad == MODALIDAD_REQUIERE_SUPERVISOR and sala_muc_completa:
        logger.info(
            "Comprobando si el supervisor del examen está activo en "
            "la sala '%s'...", sala_muc_completa,
        )
        activo, mensaje = await comprobar_supervisor_activo(
            config_xmpp, sala_muc_completa,
        )
        if not activo:
            detalle = f". {mensaje}" if mensaje else ""
            logger.critical(
                "El supervisor del examen NO está activo: la sala "
                "MUC '%s' aún no está creada en el servidor%s.\n"
                "  Espera a que el profesor arranque su supervisor y "
                "vuelve a lanzar 'python main.py'. No se crea ningún "
                "agente para no saturar el log del servidor con "
                "rechazos repetidos.",
                sala_muc_completa, detalle,
            )
            sys.exit(CODIGO_SALIDA_SUPERVISOR_INACTIVO)
        logger.info(
            "Supervisor activo: la sala '%s' existe en el servidor.",
            sala_muc_completa,
        )

    logger.info("Cargando plantillas de agentes desde: %s", ruta_agentes)
    plantillas = cargar_plantillas(ruta_agentes)
    definiciones = generar_agentes(config, plantillas)

    # ── Crear salas de torneos (Opción B) ─────────────────────
    torneos = cargar_torneos(ruta_torneos)
    asignaciones = await crear_salas_torneos(torneos, config_xmpp)

    # Inyectar sala_asignada en los parámetros de cada agente que
    # participe en un torneo
    for definicion in definiciones:
        nombre = definicion["nombre"]
        if nombre in asignaciones:
            definicion["parametros"]["sala_asignada"] = asignaciones[nombre]
            logger.debug(
                "Agente '%s' asignado a sala '%s'",
                nombre, asignaciones[nombre],
            )

    if not definiciones:
        logger.warning("No hay agentes activos definidos en %s", ruta_agentes)
        return

    # ── Aleatorizar el orden de arranque ───────────────────────
    # DELIBERADO: fuerza que el diseño tolere la ausencia temporal
    # de otros agentes. Si un jugador arranca antes que cualquier
    # tablero, debe saber esperar. Si un tablero arranca solo,
    # debe funcionar igualmente hasta que lleguen jugadores.
    random.shuffle(definiciones)

    logger.info(
        "Orden de arranque (aleatorio): %s",
        [d["nombre"] for d in definiciones],
    )

    # ── Crear e iniciar los agentes ────────────────────────────
    agentes_activos: list[Agent] = []

    for definicion in definiciones:
        try:
            agente = crear_instancia_agente(definicion, config_xmpp, config_llm)
            await agente.start(auto_register=config_xmpp.get("auto_register", True))
            agentes_activos.append(agente)

            logger.info(
                "Agente '%s' arrancado correctamente (JID: %s)",
                definicion["nombre"],
                str(agente.jid),
            )

            # Retardo aleatorio entre arranques para simular un entorno
            # donde los agentes no se lanzan todos al mismo instante
            retardo = random.uniform(0.5, 2.0)
            logger.debug("Esperando %.1f s antes del siguiente agente...", retardo)
            await asyncio.sleep(retardo)

        except Exception as error:
            logger.error(
                "Error al arrancar agente '%s': %s",
                definicion["nombre"],
                error,
            )
            # No detenemos el sistema: los demás agentes deben poder funcionar
            # aunque uno falle (tolerancia a fallos parciales)

    # ── Mantener el sistema en ejecución ───────────────────────
    if agentes_activos:
        logger.info(
            "Sistema arrancado: %d agentes activos. "
            "Pulsa Ctrl+C para detener.",
            len(agentes_activos),
        )

        # Esperar hasta recibir señal de parada
        evento_parada = asyncio.Event()

        def manejar_senal(signum: int, frame: Any) -> None:
            """Manejador de señales SIGINT/SIGTERM para parada ordenada."""
            logger.info("Señal de parada recibida (%s). Deteniendo agentes...", signum)
            evento_parada.set()

        signal.signal(signal.SIGINT, manejar_senal)
        signal.signal(signal.SIGTERM, manejar_senal)

        await evento_parada.wait()

        # ── Detener todos los agentes de forma ordenada ────────
        for agente in agentes_activos:
            try:
                await agente.stop()
                logger.info("Agente %s detenido", agente.jid)
            except Exception as error:
                logger.error("Error al detener %s: %s", agente.jid, error)

        logger.info("Sistema detenido correctamente.")
    else:
        logger.error("Ningún agente pudo arrancarse. Revisa la configuración.")


def main() -> None:
    """Punto de entrada principal del lanzador.

    Analiza los argumentos de la línea de órdenes y ejecuta el bucle
    asíncrono que arranca todo el sistema multiagente.
    """
    argumentos = parsear_argumentos()

    try:
        asyncio.run(
            arrancar_sistema(
                argumentos.config, argumentos.agents, argumentos.torneos,
            ),
        )
    except KeyboardInterrupt:
        logger.info("Ejecución interrumpida por el usuario.")
    except FileNotFoundError as error:
        logger.error("Fichero no encontrado: %s", error)
        sys.exit(1)
    except ValueError as error:
        logger.error("Error de configuración: %s", error)
        sys.exit(1)


if __name__ == "__main__":
    main()
