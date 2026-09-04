"""Lanzador homogéneo de la batería de agentes A2A del alumno.

Lee ``config/config.yaml`` y ``config/agents.yaml``, importa
dinámicamente cada clase declarada y arranca los agentes en el
orden indicado. Esta es la única forma soportada de arrancar el
sistema del grupo de cara a la evaluación: cualquier otro lanzador
escrito por el grupo debe respetar la misma secuencia y la misma
publicación en el registro REST del aula.
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import signal
import sys
from pathlib import Path
from typing import Any

import yaml

from factoria.agente_a2a import AgenteA2A, EspecificacionAgente


logger = logging.getLogger("factoria.lanzador")


CODIGO_ERROR_CONFIGURACION = 2


def _cargar_yaml(ruta: Path) -> dict[str, Any]:
    """Lee un YAML como diccionario; lanza ``SystemExit`` si no existe."""
    if not ruta.is_file():
        logger.critical("No se encuentra el fichero '%s'.", ruta)
        raise SystemExit(CODIGO_ERROR_CONFIGURACION)
    with ruta.open(encoding="utf-8") as origen:
        contenido = yaml.safe_load(origen) or {}
    if not isinstance(contenido, dict):
        logger.critical("'%s' no contiene un objeto YAML válido.", ruta)
        raise SystemExit(CODIGO_ERROR_CONFIGURACION)
    return contenido


def _importar_clase(modulo: str, clase: str) -> type[AgenteA2A]:
    """Importa dinámicamente una clase de agente."""
    try:
        modulo_cargado = importlib.import_module(modulo)
    except ImportError as error:
        logger.critical(
            "No se puede importar el módulo '%s': %s. ¿Está en el PYTHONPATH?",
            modulo, error,
        )
        raise SystemExit(CODIGO_ERROR_CONFIGURACION) from error
    if not hasattr(modulo_cargado, clase):
        logger.critical(
            "El módulo '%s' no expone la clase '%s'.",
            modulo, clase,
        )
        raise SystemExit(CODIGO_ERROR_CONFIGURACION)
    referencia = getattr(modulo_cargado, clase)
    if not (isinstance(referencia, type) and issubclass(referencia, AgenteA2A)):
        logger.critical(
            "%s.%s no es subclase de factoria.AgenteA2A.",
            modulo, clase,
        )
        raise SystemExit(CODIGO_ERROR_CONFIGURACION)
    return referencia


def _construir_especificaciones(
    datos_agentes: list[dict[str, Any]],
    host_por_defecto: str,
) -> list[EspecificacionAgente]:
    """Construye la lista de :class:`EspecificacionAgente` activos."""
    especificaciones: list[EspecificacionAgente] = []
    for bruto in datos_agentes:
        if not bruto.get("activo", True):
            continue
        especificacion = EspecificacionAgente(
            identificador=bruto["identificador"],
            rol=bruto["rol"],
            visibilidad=bruto["visibilidad"],
            puerto=int(bruto["puerto"]),
            host=bruto.get("host") or host_por_defecto,
            modulo=bruto["modulo"],
            clase=bruto["clase"],
            parametros=bruto.get("parametros") or {},
        )
        especificaciones.append(especificacion)
    return especificaciones


async def arrancar_agentes_desde_configuracion(
    ruta_config: Path,
    ruta_agentes: Path,
) -> None:
    """Arranca todos los agentes declarados y queda a la espera de SIGINT.

    Args:
        ruta_config: Ruta a ``config/config.yaml``.
        ruta_agentes: Ruta a ``config/agents.yaml``.
    """
    configuracion = _cargar_yaml(ruta_config)
    agentes_brutos = (_cargar_yaml(ruta_agentes).get("agentes") or [])

    bloque_a2a = configuracion.get("a2a") or {}
    host_por_defecto = (bloque_a2a.get("host_por_defecto") or "0.0.0.0")

    especificaciones = _construir_especificaciones(agentes_brutos, host_por_defecto)
    if not especificaciones:
        logger.critical(
            "No hay agentes activos en '%s'. Marca 'activo: true' en al menos uno.",
            ruta_agentes,
        )
        raise SystemExit(CODIGO_ERROR_CONFIGURACION)

    agentes: list[AgenteA2A] = []
    for especificacion in especificaciones:
        clase = _importar_clase(especificacion.modulo, especificacion.clase)
        agente = clase(especificacion)
        agentes.append(agente)

    for agente in agentes:
        await agente.arrancar()

    evento_parada = asyncio.Event()
    bucle = asyncio.get_running_loop()
    for senal in (signal.SIGINT, signal.SIGTERM):
        try:
            bucle.add_signal_handler(senal, evento_parada.set)
        except NotImplementedError:
            # Windows no soporta add_signal_handler; el alumno
            # detiene con Ctrl+C y aiohttp se cierra por excepción.
            pass

    logger.info("Sistema multiagente arrancado. Pulsa Ctrl+C para detener.")
    await evento_parada.wait()

    logger.info("Deteniendo agentes...")
    for agente in reversed(agentes):
        await agente.detener()
