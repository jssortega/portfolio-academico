"""Sembrado automático de la BD con una ejecución demo.

La idea es que, al arrancar el supervisor en modo consulta sobre una
BD recién creada, el dashboard tenga al menos una ejecución que
mostrar. Esta utilidad inserta los seguimientos del catálogo demo
como si hubiesen ocurrido durante una sesión real ya finalizada.

Es seguro llamarla múltiples veces: solo siembra si la tabla
``ejecuciones`` está vacía.
"""
import logging
from datetime import datetime, timedelta

from agente_profesor.escenarios import (
    construir_seguimientos_demo,
    grupos_demo,
)
from agente_profesor.persistencia.almacen_supervisor import (
    AlmacenSupervisor,
)

logger = logging.getLogger(__name__)


# ─── Constantes simbólicas ──────────────────────────────────────────────────

ETIQUETA_MODO_DEMO = "demo"
DESCRIPCION_DEMO = "Ejecución de muestra cargada al inicializar la BD"
DURACION_SESION_MINUTOS = 18.0


def sembrar_demo_si_vacio(almacen: AlmacenSupervisor) -> bool:
    """Siembra una ejecución demo si la BD está vacía.

    Args:
        almacen: Almacén abierto sobre el fichero SQLite.

    Returns:
        ``True`` si se ha insertado la ejecución; ``False`` si la
        BD ya tenía datos previos.
    """
    sembrada = False
    if almacen.hay_ejecuciones():
        logger.debug("BD ya inicializada, no se siembra demo")
    else:
        seguimientos = construir_seguimientos_demo()
        grupos = grupos_demo()

        # La sesión demo se sitúa "hace 20 minutos" para que la línea
        # de tiempo de cada seguimiento (que ya está desplazada hacia
        # atrás por escenarios.py) caiga dentro del intervalo de la
        # ejecución y no en el futuro.
        fin = datetime.now()
        inicio = fin - timedelta(minutes=DURACION_SESION_MINUTOS)

        seguimientos_dict = [s.a_dict() for s in seguimientos]

        log_demo = _construir_log_demo(
            inicio=inicio, seguimientos=seguimientos,
        )

        almacen.insertar_ejecucion_completa(
            modo=ETIQUETA_MODO_DEMO,
            inicio_iso=inicio.isoformat(timespec="seconds"),
            fin_iso=fin.isoformat(timespec="seconds"),
            descripcion=DESCRIPCION_DEMO,
            grupos=grupos,
            seguimientos=seguimientos_dict,
            log=log_demo,
        )
        sembrada = True
        logger.info(
            "BD vacía → sembrada con ejecución demo "
            "(%d seguimientos, %d grupos)",
            len(seguimientos_dict), len(grupos),
        )
    return sembrada


def _construir_log_demo(inicio, seguimientos) -> list[dict]:
    """Genera entradas de log coherentes con los seguimientos demo.

    El log se ordena del más reciente al más antiguo (igual que en
    el dashboard en vivo) para que el panel "Log" no necesite
    invertir el orden al renderizar.
    """
    eventos: list[dict] = []
    eventos.append({
        "ts": inicio.strftime("%H:%M:%S"),
        "tipo": "info",
        "de": "supervisor",
        "detalle": "Banco de pruebas iniciado",
    })

    for seguimiento in seguimientos:
        eventos.append({
            "ts": seguimiento.instante_creacion.strftime("%H:%M:%S"),
            "tipo": "info",
            "de": f"grupo:{seguimiento.grupo}",
            "detalle": (
                f"Inyectado {seguimiento.tipo_emergencia} "
                f"(prioridad {seguimiento.prioridad})"
            ),
        })
        if seguimiento.error:
            eventos.append({
                "ts": (
                    seguimiento.instante_agree.strftime("%H:%M:%S")
                    if seguimiento.instante_agree else
                    seguimiento.instante_creacion.strftime("%H:%M:%S")
                ),
                "tipo": "error",
                "de": f"grupo:{seguimiento.grupo}",
                "detalle": seguimiento.error,
            })
        elif seguimiento.instante_informe is not None:
            eventos.append({
                "ts": seguimiento.instante_informe.strftime("%H:%M:%S"),
                "tipo": "ok",
                "de": f"grupo:{seguimiento.grupo}",
                "detalle": (
                    f"Informe de resolución recibido "
                    f"({seguimiento.tipo_emergencia})"
                ),
            })

    # Ordenar de más reciente a más antiguo
    eventos.sort(key=lambda e: e["ts"], reverse=True)
    return eventos
