"""Agente supervisor del profesor — Villa Olivar (Nivel 2).

El agente arranca, inicializa su estado interno, abre el almacén
SQLite, expone el panel web del banco de pruebas y, en modo
``activo``, conecta los cuatro comportamientos SPADE descritos en
``docs/agente_profesor/diseno_inicial.md`` §8:

- ``InyectorIncidentesBehaviour`` — Inyecta escenarios del catálogo
  como mensajes ``request`` a la Centralita de cada grupo.
- ``ReceptorRespuestasBehaviour`` — Correlaciona las respuestas y
  avanza el autómata de cada seguimiento.
- ``VigilanteTimeoutsBehaviour`` — Caduca seguimientos que han
  superado los plazos de ``agree`` o ``informe``.
- ``SondeoEstadoBehaviour`` — Sondea periódicamente el estado de
  los agentes del grupo para la pestaña "Estados de agentes".

En modo ``consulta`` los behaviours no se enganchan: el agente sólo
sirve el panel sobre la BD SQLite.

Diseño:

- ``setup()`` lee la configuración, prepara el diccionario de
  seguimientos, registra el log, abre el almacén SQLite (creando
  una nueva ejecución activa) y arranca el servidor web SPADE.
- ``registrar_seguimiento()`` y ``registrar_evento()`` son los
  puntos por los que los behaviours actualizan el estado,
  persisten en SQLite y empujan eventos SSE al panel.
"""
import logging
from collections import deque
from datetime import datetime
from typing import Optional

from spade.agent import Agent
from spade.template import Template

from agente_profesor.comportamientos import (
    InyectorIncidentesBehaviour,
    ReceptorRespuestasBehaviour,
    SondeoEstadoBehaviour,
    VigilanteTimeoutsBehaviour,
)
from agente_profesor.persistencia import AlmacenSupervisor
from agente_profesor.seguimientos import Seguimiento
from agente_profesor.web.handlers import (
    crear_middleware_auth,
    notificar_sse,
    registrar_rutas,
)

logger = logging.getLogger(__name__)


# ─── Constantes simbólicas ──────────────────────────────────────────────────
# Solo constantes internas del proceso. Los parámetros de despliegue
# (puerto, host, ruta de la BD) viven en config_profesor.yaml para
# evitar duplicar la fuente de verdad — ver directriz SMA.

LIMITE_LOG_EN_MEMORIA = 500

# Periodo del vigilante de timeouts. Granularidad fina para que
# ningún seguimiento sobrepase su plazo más de 1 s.
PERIODO_VIGILANTE_S = 1.0

# Intervalo por defecto del sondeo de estados (si no está en config).
INTERVALO_SONDEO_DEFECTO_S = 15.0

# Intervalo por defecto de inyección automática (si no está en config).
INTERVALO_INYECCION_DEFECTO_S = 30.0


# ─── Clase del supervisor ───────────────────────────────────────────────────

class SupervisorEmergencias(Agent):
    """Agente SPADE puro que actúa como banco de pruebas.

    Atributos inyectados antes de ``setup()`` por el lanzador:
        config_supervisor (dict): Bloque del config_profesor.yaml ya
            cargado (identidad, web, timeouts, grupos, modo_arranque,
            persistencia).
    """

    async def setup(self) -> None:
        """Inicializa estado interno y arranca el dashboard web."""

        config = getattr(self, "config_supervisor", {})

        # ── Estado interno público (consumido por web/handlers.py) ───
        self.modo: str = config.get("modo_arranque", "activo")
        self.es_agente_vivo: bool = True
        self.grupos: list[dict] = list(config.get("grupos", []))
        self.timeouts: dict = config.get("timeouts", {})
        self.seguimientos: dict[str, Seguimiento] = {}
        self.log_eventos: deque[dict] = deque(maxlen=LIMITE_LOG_EN_MEMORIA)
        # Sondeo: tabla por (grupo, rol) con el último EstadoAgente
        # recibido, y registro de las consultas actualmente abiertas.
        self.estados_agentes: dict = {}
        self.consultas_en_curso: dict = {}
        # Referencia al inyector — el endpoint POST /inyectar la usa.
        self.inyector: Optional[InyectorIncidentesBehaviour] = None

        # ── Persistencia SQLite ───────────────────────────────────────
        ruta_db = config["persistencia"]["ruta_db"]
        # Exponemos la ruta para que el handler de finalización pueda
        # derivar de ella el directorio donde guardar los CSV cuando el
        # profesor cierra el supervisor desde el panel.
        self.ruta_db: str = ruta_db
        self.almacen = AlmacenSupervisor(ruta_db)
        self.almacen.crear_ejecucion(
            modo=self.modo,
            grupos=self.grupos,
            descripcion=config.get(
                "persistencia", {},
            ).get("descripcion_sesion", ""),
        )
        self.registrar_evento(
            "info", "supervisor",
            f"Ejecución iniciada (modo {self.modo})",
        )

        # ── Servidor web SPADE ────────────────────────────────────────
        config_web = config["web"]
        puerto = config_web["puerto"]
        host = config_web["host"]
        auth_usuario = config_web.get("auth_usuario", "")
        auth_contrasena = config_web.get("auth_contrasena", "")

        if auth_usuario and auth_contrasena:
            middleware = crear_middleware_auth(
                auth_usuario, auth_contrasena,
            )
            self.web.app.middlewares.append(middleware)
            logger.info(
                "Autenticación HTTP Basic activada (usuario: %s)",
                auth_usuario,
            )

        self.web.start(hostname=host, port=puerto)
        registrar_rutas(self.web.app)
        self.web.app["agente"] = self
        self.web.app["modo"] = self.modo

        logger.info(
            "Supervisor del profesor disponible en "
            "http://localhost:%d/supervisor (modo: %s, grupos: %d, "
            "BD: %s)",
            puerto, self.modo, len(self.grupos), ruta_db,
        )

        # ── Comportamientos SPADE (sólo en modo activo) ───────────────
        # En modo "consulta" no se conecta a XMPP; los behaviours no
        # tendrían a quién enviar mensajes y bloquearían el bucle.
        if self.modo == "activo":
            self._enganchar_comportamientos(config)

    def _enganchar_comportamientos(self, config: dict) -> None:
        """Crea y arranca los cuatro behaviours del supervisor."""
        # Inyector
        intervalo_iny = float(
            config.get("inyeccion", {}).get(
                "intervalo_segundos", INTERVALO_INYECCION_DEFECTO_S,
            ),
        )
        self.inyector = InyectorIncidentesBehaviour(period=intervalo_iny)
        self.add_behaviour(self.inyector)

        # Receptor: filtra cualquier mensaje con la ontología de
        # emergencias para evitar mezclar con mensajería ajena al
        # supervisor (si la hubiera).
        plantilla = Template()
        plantilla.set_metadata("ontology", "emergencias-villaolivar")
        receptor = ReceptorRespuestasBehaviour()
        self.add_behaviour(receptor, plantilla)

        # Vigilante
        vigilante = VigilanteTimeoutsBehaviour(period=PERIODO_VIGILANTE_S)
        self.add_behaviour(vigilante)

        # Sondeo de estados
        intervalo_sondeo = float(
            config.get("sondeo", {}).get(
                "intervalo_segundos", INTERVALO_SONDEO_DEFECTO_S,
            ),
        )
        sondeo = SondeoEstadoBehaviour(period=intervalo_sondeo)
        self.add_behaviour(sondeo)

        self.registrar_evento(
            "info", "supervisor",
            f"Comportamientos activados (inyector cada "
            f"{intervalo_iny:.0f} s, sondeo cada {intervalo_sondeo:.0f} s).",
        )

    # ── API para los behaviours y para los handlers HTTP ────────────────

    async def inyectar_manualmente(
        self, id_grupo: str, clave_escenario: Optional[str] = None,
    ) -> Optional[Seguimiento]:
        """Punto de entrada del botón "Inyectar incidente" del panel.

        Devuelve el ``Seguimiento`` creado, o ``None`` si el modo no
        es ``activo`` o el inyector no está disponible.
        """
        resultado: Optional[Seguimiento] = None
        if self.modo == "activo" and self.inyector is not None:
            resultado = await self.inyector.inyectar_a_grupo(
                id_grupo=id_grupo, clave_escenario=clave_escenario,
            )
        return resultado

    # ── API para los behaviours ─────────────────────────────────────────

    def registrar_seguimiento(self, seguimiento: Seguimiento) -> None:
        """Inserta o actualiza un seguimiento, lo persiste y notifica."""
        self.seguimientos[seguimiento.id_emergencia] = seguimiento
        datos = seguimiento.a_dict()
        if self.almacen is not None:
            self.almacen.guardar_seguimiento(datos)
        notificar_sse("seguimiento", datos)

    def registrar_evento(
        self, tipo: str, origen: str, detalle: str,
    ) -> None:
        """Añade un evento al log, lo persiste y lo empuja por SSE."""
        evento = {
            "ts": datetime.now().strftime("%H:%M:%S"),
            "tipo": tipo,
            "de": origen,
            "detalle": detalle,
        }
        self.log_eventos.appendleft(evento)
        if self.almacen is not None:
            self.almacen.guardar_evento_log(evento)
        notificar_sse("log", evento)

    # ── Apagado ordenado ────────────────────────────────────────────────

    async def detener(self) -> None:
        """Cierra el supervisor liberando recursos.

        Marca la ejecución como finalizada en la BD, cierra el
        almacén y avisa por SSE para que el dashboard cierre la
        suscripción ordenadamente.
        """
        self.registrar_evento(
            "info", "supervisor",
            "Detención solicitada — apagando supervisor.",
        )
        if self.almacen is not None:
            self.almacen.finalizar_ejecucion()
            self.almacen.cerrar()
            self.almacen = None
        notificar_sse("cierre", {})
