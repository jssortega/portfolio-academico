"""
Agente Supervisor del sistema Tic-Tac-Toe Multiagente.

Observa una o varias salas MUC para detectar tableros cuyas partidas
han finalizado y les solicita un informe de partida (``game-report``).
Los informes recibidos se almacenan internamente para consulta
posterior, organizados por sala.

La detección de tableros finalizados se realiza de forma reactiva
mediante el callback de presencia ``on_available`` de SPADE (modelo
push, coherente con XEP-0045): cuando la sala MUC notifica un cambio
de presencia con ``status="finished"``, el supervisor crea un
``SolicitarInformeBehaviour`` que gestiona el protocolo FIPA-Request
completo para ese tablero.

Además, expone un dashboard web accesible en el puerto configurado
(por defecto 8000) que permite visualizar en tiempo real los informes
recibidos, la presencia MUC, la clasificación y el log de eventos
de cada sala monitorizada.

Supervisor único por sala (S-02 — corrige P-02):

    Tras unirse a cada sala MUC, el agente comprueba la afiliación
    que Prosody le ha asignado. Solo se considera autorizado si la
    afiliación es ``admin`` u ``owner``; en otro caso, escribe un
    aviso muy visible en ``stderr`` (banner con el JID del agente,
    la sala y la afiliación recibida) y se autodetiene de forma
    ordenada. La afiliación la asigna Prosody en función de la
    directiva ``muc_room_default_admins`` definida en el
    ``prosody.cfg.lua`` del repositorio de infraestructura de la
    asignatura
    (https://gitlab.com/ssmmaa/infraestructurassmmaa/ssmmaa-infraestructura);
    al residir en el servidor, no puede ser alterada desde el código
    del agente. El análisis de diseño completo está en la rama
    ``feature/agente-supervisor``.

Uso (a través de la factoría)::

    from utils import crear_agente, arrancar_agente
    from agentes.agente_supervisor import AgenteSupervisor

    agente = crear_agente(AgenteSupervisor, "supervisor", config_xmpp)
    await arrancar_agente(agente, config_xmpp)
"""

import asyncio
import logging
import sys
from datetime import datetime
from xml.etree.ElementTree import SubElement

from spade.agent import Agent
from spade.template import Template

from collections import deque

# ── Afiliaciones MUC autorizadas para el rol de supervisor ──────
# La afiliación la asigna Prosody (no el cliente) en función de la
# directiva muc_room_default_admins del prosody.cfg.lua publicado en
# el repositorio de infraestructura de la asignatura
# (https://gitlab.com/ssmmaa/infraestructurassmmaa/ssmmaa-infraestructura).
# Solo los agentes con afiliación 'admin' u 'owner' pueden actuar
# como supervisor; los demás se autodetienen al detectar afiliación
# insuficiente.
AFILIACIONES_AUTORIZADAS = ("admin", "owner")

# ── Modo de ejecución que activa la limpieza de salas al apagar ──
# Solo en modo examen el supervisor, al detenerse, expulsa a los
# ocupantes de sus salas MUC (expulsar_ocupantes_salas) y a
# continuación las destruye (eliminar_salas_examen). El propio
# supervisor recrea las salas al arrancar, así que cada sesión del
# supervisor parte de salas nuevas, sin ocupantes ni estado residual
# de la sesión anterior.
MODO_EXAMEN = "examen"

# Rol MUC que se asigna a un ocupante para expulsarlo de la sala:
# según XEP-0045 §9.1, cambiar el rol de un ocupante a 'none'
# equivale a expulsarlo (en jerga XMPP, un *kick*).
ROL_MUC_EXPULSADO = "none"

# Motivo que el supervisor adjunta al destruir una sala MUC del
# examen durante su apagado ordenado (XEP-0045 §10.9).
RAZON_DESTRUCCION_SALA = "Sesión del supervisor finalizada"

from behaviours.supervisor_behaviours import (
    LOG_ADVERTENCIA,
    LOG_ENTRADA,
    LOG_ERROR,
    LOG_PRESENCIA,
    LOG_SALIDA,
    LOG_SOLICITUD,
    INTERVALO_REVISION_INACTIVIDAD_S,
    MAX_FSM_CONCURRENTES,
    MAX_REINTENTOS,
    TIMEOUT_RESPUESTA,
    UMBRAL_JUGADOR_SIN_PARTIDA_S,
    UMBRAL_TABLERO_ESTADO_ESTANCADO_S,
    UMBRAL_TABLERO_PLAYING_SIN_FIN_S,
    MonitorizarMUCBehaviour,
    RevisarInactividadBehaviour,
    SolicitarInformeFSM,
)
from config.configuracion import normalizar_nombre_sala
from ontologia.ontologia import (
    ONTOLOGIA, PREFIJO_THREAD_REPORT, crear_thread_unico,
)
from persistencia.almacen_supervisor import AlmacenSupervisor
from web.supervisor_handlers import (
    crear_middleware_auth,
    registrar_rutas_supervisor,
)

logger = logging.getLogger(__name__)


class AgenteSupervisor(Agent):
    """Agente que monitoriza partidas en múltiples salas MUC.

    Atributos inyectados antes de ``setup()`` (por el lanzador o la factoría):
        config_xmpp (dict): Configuración del perfil XMPP activo, que
            incluye ``servicio_muc`` y ``sala_tictactoe``.
        config_parametros (dict): Parámetros específicos del agente,
            como ``intervalo_consulta``, ``puerto_web``,
            ``descubrimiento_salas`` (``"auto"`` o ``"manual"``) y
            ``salas_muc`` (lista de salas para modo manual).
    """

    async def setup(self) -> None:
        """Inicializa el supervisor: estado interno, salas MUC, behaviours y web.

        Se une a cada sala MUC configurada con el apodo ``supervisor``,
        registra el callback de presencia para detección reactiva de
        tableros finalizados, el behaviour periódico para el dashboard
        y arranca el servidor web.
        """
        # ── Construir la lista de salas a monitorizar ────────────
        servicio_muc = self.config_xmpp.get(
            "servicio_muc", "conference.localhost",
        )
        modo_descubrimiento = self.config_parametros.get(
            "descubrimiento_salas", "auto",
        )
        salas_config = self.config_parametros.get("salas_muc", [])

        # Modo "auto" (por defecto): descubrir salas mediante
        # XEP-0030 (Service Discovery) contra el servicio MUC.
        # Modo "manual": usar la lista explícita de salas_muc.
        # Si salas_muc está vacía y el descubrimiento no encuentra
        # nada, se usa la sala por defecto del perfil XMPP.
        if modo_descubrimiento == "auto" and not salas_config:
            salas_config = await self._descubrir_salas_muc(servicio_muc)

        # Si no hay salas (ni manuales ni descubiertas), usar la
        # sala por defecto del perfil XMPP (retrocompatibilidad)
        if not salas_config:
            sala_defecto = self.config_xmpp.get(
                "sala_tictactoe", "tictactoe",
            )
            salas_config = [sala_defecto]
            logger.info(
                "Sin salas descubiertas ni configuradas; "
                "usando sala por defecto: %s",
                sala_defecto,
            )

        # Construir la lista de salas con su JID completo. El nombre
        # de cada sala se canoniza con normalizar_nombre_sala() —la
        # función común que también usan el creador de salas del
        # supervisor y los agentes del alumno— para que el supervisor
        # monitorice EXACTAMENTE las mismas salas a las que se unirán
        # los agentes, sin discrepancias por mayúsculas, espacios o
        # ceros a la izquierda. Sin esta forma común, una sala
        # declarada como 'PC-13' en el YAML no casaría con el 'from'
        # de las presencias entrantes ('pc-13@...') ni con el JID que
        # construye el alumno, y _on_presencia_muc descartaría a sus
        # ocupantes. El 'id' canonizado se usa como clave interna y
        # como base de la etiqueta del panel ('Sala PC-13').
        self.salas_muc: list[dict] = []
        for nombre_sala in salas_config:
            nombre_canonico = normalizar_nombre_sala(nombre_sala)
            jid_sala = f"{nombre_canonico}@{servicio_muc}".lower()
            self.salas_muc.append({
                "id": nombre_canonico,
                "jid": jid_sala,
            })

        # ── Estado interno organizado por sala ───────────────────
        # Informes indexados por sala y luego por JID del tablero.
        # Cada tablero puede acumular varios informes si ejecuta
        # múltiples partidas en la misma sala durante la ejecución.
        self.informes_por_sala: dict[str, dict[str, list[dict]]] = {
            s["id"]: {} for s in self.salas_muc
        }
        # Conjunto global de tableros ya consultados (JIDs únicos)
        self.tableros_consultados: set[str] = set()
        # Mapeo tablero JID → sala ID para saber a qué sala pertenece
        self.tablero_a_sala: dict[str, str] = {}

        # Ocupantes por sala para el dashboard (foto en tiempo real)
        self.ocupantes_por_sala: dict[str, list[dict]] = {
            s["id"]: [] for s in self.salas_muc
        }
        # Histórico de ocupantes: acumula JIDs y nicks de todos
        # los agentes que han estado en cada sala durante la
        # ejecución. No se eliminan al recibir 'unavailable'.
        # Se usa para la validación de jugadores observados (P-04)
        # en vez de la foto en tiempo real, evitando falsos
        # positivos cuando un jugador abandona la sala antes de
        # que se procese el informe.
        self.ocupantes_historicos_por_sala: dict[str, set[str]] = {
            s["id"]: set() for s in self.salas_muc
        }
        # Log cronológico por sala
        self.log_por_sala: dict[str, list[dict]] = {
            s["id"]: [] for s in self.salas_muc
        }

        # Threads de solicitudes cuyo informe ya se ha procesado.
        # Permite detectar informes duplicados por identidad de
        # solicitud (thread) en vez de por contenido (P-05).
        self.threads_procesados_por_sala: dict[str, set[str]] = {
            s["id"]: set() for s in self.salas_muc
        }

        # Solicitudes de informe en curso (jid_tablero → sala_id).
        # Se rellena al crear un SolicitarInformeFSM y se vacía
        # cuando el FSM alcanza un estado terminal. Al detener el
        # supervisor, las entradas restantes se registran como
        # informes no recibidos.
        self.informes_pendientes: dict[str, str] = {}

        # Cola de tableros pendientes de solicitar informe.
        # Cuando el número de FSMs activos alcanza el límite
        # (max_fsm_concurrentes), los nuevos tableros finalizados
        # se encolan aquí en vez de crear un FSM inmediatamente.
        # Se procesan conforme los FSMs activos terminan.
        self.tableros_en_cola: deque[tuple[str, str]] = deque()

        # ── Persistencia SQLite ───────────────────────────────────
        ruta_db = self.config_parametros.get(
            "ruta_db", "data/supervisor.db",
        )
        # Guardamos la ruta para que los handlers web puedan abrir
        # conexiones de lectura transitorias incluso después de que
        # detener_persistencia() haya cerrado el almacén principal.
        self.ruta_db = ruta_db
        self.almacen = AlmacenSupervisor(ruta_db)
        self.almacen.crear_ejecucion(self.salas_muc)

        # ── Keepalive XMPP ────────────────────────────────────────
        # slixmpp envía un espacio en blanco periódicamente para
        # mantener viva la conexión TCP. El intervalo por defecto
        # (300 s) es demasiado largo: los firewalls y NATs de la
        # red universitaria pueden cerrar conexiones inactivas
        # antes de que se envíe el keepalive, provocando la
        # expulsión silenciosa de las salas MUC. Un intervalo de
        # 60 s previene este problema sin generar tráfico excesivo.
        self.client.whitespace_keepalive_interval = 60

        # ── Registrar plugin MUC en el cliente XMPP ─────────────
        # Necesario para que slixmpp interprete correctamente el
        # elemento <x xmlns="...muc#user"> de las stanzas de presencia
        # (sin esto, el campo muc.item.jid no se parsea).
        self.client.register_plugin("xep_0045")

        # ── Unirse a cada sala MUC ──────────────────────────────
        # Se envía una stanza de presencia con namespace MUC a cada
        # sala. presence.subscribe() solo gestiona suscripciones
        # estándar XMPP, NO join de sala MUC (XEP-0045).
        self.muc_apodo = "supervisor"

        # ── Validación de afiliación MUC (S-02) ───────────────────
        # Conjunto de salas en las que ya se ha verificado la
        # afiliación del supervisor para evitar comprobaciones
        # repetidas a cada cambio de presencia.
        self._afiliacion_validada: set[str] = set()
        # Indicador de parada por afiliación insuficiente: una vez
        # activado, los handlers de presencia ignoran nuevos
        # eventos para no contaminar el dashboard ni el log.
        self._detenido_por_afiliacion = False

        for sala in self.salas_muc:
            logger.info(
                "Supervisor uniéndose a la sala MUC: %s con apodo '%s'",
                sala["jid"], self.muc_apodo,
            )
            self._unirse_sala_muc(sala["jid"], self.muc_apodo)

        # ── Handler de presencia MUC (modelo push, paso 0) ───────
        # Captura las stanzas de presencia de las salas MUC para:
        # 1. Mantener actualizada la lista de ocupantes (dashboard)
        # 2. Detectar tableros con status="finished" (protocolo)
        self.client.add_event_handler(
            "presence", self._on_presencia_muc,
        )

        # ── Reconexión automática a salas MUC (M-11) ─────────
        # Cuando slixmpp restablece la sesión XMPP tras una
        # desconexión (reinicio del servidor, interrupción de
        # red), se vuelven a enviar los joins MUC para cada sala.
        # Se registra una advertencia para que quede constancia
        # en la pestaña de Incidencias.
        self.client.add_event_handler(
            "session_start", self._on_reconexion_sesion,
        )
        self.client.add_event_handler(
            "disconnected", self._on_desconexion,
        )
        self._reconexion_activa = False

        # ── Parámetros de temporización ──────────────────────────
        intervalo = self.config_parametros.get("intervalo_consulta", 10)
        self.timeout_respuesta = self.config_parametros.get(
            "timeout_respuesta", TIMEOUT_RESPUESTA,
        )
        self.max_reintentos = self.config_parametros.get(
            "max_reintentos", MAX_REINTENTOS,
        )
        self.max_fsm_concurrentes = self.config_parametros.get(
            "max_fsm_concurrentes", MAX_FSM_CONCURRENTES,
        )

        # Monitorización periódica: solo actualiza ocupantes del
        # dashboard, NO detecta tableros finalizados
        comportamiento_monitorizar = MonitorizarMUCBehaviour(
            period=intervalo,
        )
        self.add_behaviour(comportamiento_monitorizar)
        logger.info(
            "Behaviour MonitorizarMUC registrado (intervalo: %d s, "
            "salas: %d)",
            intervalo, len(self.salas_muc),
        )

        # ── Revisor de inactividad ────────────────────────────────
        # Cada N segundos comprueba: (1) jugadores que llevan tiempo
        # suficiente en la sala como para haber jugado pero no
        # aparecen en ningún informe; (2) tableros cuya presencia
        # no progresa; y (3) tableros que pasaron a 'playing' pero
        # nunca llegan a 'finished'. Cada hallazgo se emite como
        # advertencia (LOG_ADVERTENCIA) UNA sola vez por agente.
        self.alertas_inactividad_emitidas: set[tuple[str, str, str]] \
            = set()
        self.umbral_jugador_sin_partida_s = self.config_parametros.get(
            "umbral_jugador_sin_partida_s",
            UMBRAL_JUGADOR_SIN_PARTIDA_S,
        )
        self.umbral_tablero_estado_estancado_s = (
            self.config_parametros.get(
                "umbral_tablero_estado_estancado_s",
                UMBRAL_TABLERO_ESTADO_ESTANCADO_S,
            )
        )
        self.umbral_tablero_playing_sin_fin_s = (
            self.config_parametros.get(
                "umbral_tablero_playing_sin_fin_s",
                UMBRAL_TABLERO_PLAYING_SIN_FIN_S,
            )
        )
        intervalo_revision = self.config_parametros.get(
            "intervalo_revision_inactividad_s",
            INTERVALO_REVISION_INACTIVIDAD_S,
        )
        self.add_behaviour(
            RevisarInactividadBehaviour(period=intervalo_revision),
        )
        logger.info(
            "Behaviour RevisarInactividad registrado (intervalo: "
            "%d s; umbrales: jugador=%ds, tablero_estado=%ds, "
            "tablero_playing=%ds)",
            intervalo_revision,
            self.umbral_jugador_sin_partida_s,
            self.umbral_tablero_estado_estancado_s,
            self.umbral_tablero_playing_sin_fin_s,
        )

        # ── Servidor web del dashboard ────────────────────────────
        puerto_web = self.config_parametros.get("puerto_web", 8000)

        # Autenticación HTTP Basic (M-10): si se configuran
        # usuario y contraseña, se añade un middleware que
        # exige credenciales en todas las rutas excepto estáticos.
        auth_usuario = self.config_parametros.get("auth_usuario", "")
        auth_contrasena = self.config_parametros.get(
            "auth_contrasena", "",
        )
        if auth_usuario and auth_contrasena:
            middleware = crear_middleware_auth(
                auth_usuario, auth_contrasena,
            )
            self.web.app.middlewares.append(middleware)
            logger.info(
                "Autenticación HTTP Basic activada "
                "(usuario: %s)", auth_usuario,
            )

        self.web.start(
            hostname="0.0.0.0",
            port=puerto_web,
        )
        registrar_rutas_supervisor(self.web.app)
        self.web.app["agente"] = self

        salas_str = ", ".join(s["jid"] for s in self.salas_muc)
        logger.info(
            "Dashboard web del supervisor disponible en "
            "http://localhost:%d/supervisor",
            puerto_web,
        )
        logger.info(
            "AgenteSupervisor configurado — %d sala(s): %s",
            len(self.salas_muc), salas_str,
        )

    # ── Reconexión automática a salas MUC (M-11) ────────────────

    def _on_desconexion(self, _evento) -> None:
        """Handler de desconexión XMPP.

        Se invoca cuando slixmpp pierde la conexión con el
        servidor. Marca la reconexión como activa para que
        ``_on_reconexion_sesion`` sepa que debe rejoin de las
        salas y registrar la advertencia.

        Si la desconexión es consecuencia de una autodetención por
        afiliación insuficiente (S-02), se omite el aviso de
        "reconexión automática" porque sería contradictorio con el
        banner ya mostrado y confundiría al alumno: la pérdida de
        conexión es intencional y no procede ningún reintento.
        """
        if getattr(self, "_detenido_por_afiliacion", False):
            # Cierre intencional: no marcar reconexión automática
            # ni emitir el warning genérico — el banner S-02 ya ha
            # explicado por qué nos vamos.
            self._reconexion_activa = False
            logger.info(
                "Cierre completado: el supervisor no autorizado "
                "se ha desconectado del servidor XMPP.",
            )
            return

        self._reconexion_activa = True
        logger.warning(
            "Conexión XMPP perdida — se intentará "
            "reconexión automática a las salas MUC",
        )

    def _on_reconexion_sesion(self, _evento) -> None:
        """Handler de restablecimiento de sesión XMPP.

        Se invoca cuando slixmpp restablece la sesión tras una
        desconexión. Reenvía los joins MUC a todas las salas
        monitorizadas y registra una advertencia en el log de
        cada sala para que aparezca en la pestaña de Incidencias.
        """
        if not self._reconexion_activa:
            return

        self._reconexion_activa = False

        logger.info(
            "Sesión XMPP restablecida — reconectando a %d "
            "sala(s) MUC",
            len(self.salas_muc),
        )

        for sala in self.salas_muc:
            self._unirse_sala_muc(sala["jid"], self.muc_apodo)
            self.registrar_evento_log(
                LOG_ADVERTENCIA, "supervisor",
                "Reconexión automática a la sala tras "
                "pérdida de conexión XMPP — los ocupantes "
                "anteriores pueden no reflejarse hasta que "
                "vuelvan a enviar presencia",
                sala["id"],
            )
            logger.info(
                "Reconectado a sala MUC: %s", sala["jid"],
            )

    # ── Validación de afiliación MUC (S-02 — corrige P-02) ─────

    def _extraer_afiliacion(self, presencia):
        """Devuelve la afiliación MUC anunciada por el servidor en
        una stanza de presencia, o ``None`` si la stanza no es una
        presencia MUC reconocible (sin elemento
        ``<x xmlns="http://jabber.org/protocol/muc#user">``).

        En XEP-0045 la afiliación llega dentro del elemento
        ``<x xmlns="...muc#user"><item affiliation="..."/>``. Cuando
        ese elemento no existe (presencia no MUC o stanza simulada
        en tests unitarios) la función devuelve ``None`` para que
        el llamador omita la validación.

        Args:
            presencia: Stanza de presencia recibida (slixmpp).

        Returns:
            Cadena con la afiliación (``"owner"``, ``"admin"``,
            ``"member"``, ``"none"`` u ``"outcast"``) o ``None`` si
            la stanza no incluye información MUC.
        """
        afiliacion = None
        try:
            elemento_muc = presencia.get("muc", None)
            if elemento_muc is None:
                return None
            valor = elemento_muc["affiliation"]
            afiliacion = str(valor) if valor else "none"
        except Exception:
            afiliacion = None
        return afiliacion

    def _validar_afiliacion(
        self, sala_id: str, sala_jid: str, presencia,
    ) -> None:
        """Comprueba la afiliación MUC propia y detiene el agente
        si no está autorizado a actuar como supervisor.

        Esta protección es la cara cliente del par S-02 y trabaja
        junto con la directiva ``muc_room_default_admins`` de
        Prosody. Si Prosody asigna a este JID una afiliación que no
        sea ``admin`` u ``owner``, el supervisor escribe un mensaje
        crítico en consola y programa su parada ordenada.

        Args:
            sala_id: Identificador corto de la sala.
            sala_jid: JID completo de la sala MUC.
            presencia: Stanza de presencia con la afiliación.
        """
        afiliacion = self._extraer_afiliacion(presencia)
        if afiliacion is None:
            # Stanza sin información MUC fiable; no se valida ni se
            # marca la sala como validada (puede llegar otra stanza
            # con la afiliación correcta más tarde).
            return

        # Inicializar de forma idempotente los atributos de estado:
        # esto permite que la validación funcione también cuando los
        # tests construyen el agente sin pasar por setup() completo.
        if not hasattr(self, "_afiliacion_validada"):
            self._afiliacion_validada = set()
        if not hasattr(self, "_detenido_por_afiliacion"):
            self._detenido_por_afiliacion = False
        self._afiliacion_validada.add(sala_id)

        if afiliacion in AFILIACIONES_AUTORIZADAS:
            logger.info(
                "Supervisor autorizado en %s (afiliación: '%s')",
                sala_jid, afiliacion,
            )
            return

        # Afiliación insuficiente: avisar de forma muy visible y
        # programar la parada del agente para impedir cualquier
        # actividad posterior.
        self._detenido_por_afiliacion = True
        jid_propio = str(self.jid)
        mensaje = (
            "\n"
            "═══════════════════════════════════════════════════════════════\n"
            "  SUPERVISOR NO AUTORIZADO\n"
            "═══════════════════════════════════════════════════════════════\n"
            f"  Sala MUC      : {sala_jid}\n"
            f"  JID del agente: {jid_propio}\n"
            f"  Afiliación    : '{afiliacion}' "
            "(se requiere 'admin' u 'owner')\n"
            "\n"
            "  Solo el supervisor del profesor está autorizado a actuar\n"
            "  como tal en este servidor XMPP. La afiliación la asigna\n"
            "  Prosody (no el cliente) mediante la directiva\n"
            "  'muc_room_default_admins' del prosody.cfg.lua que vive en\n"
            "  el repositorio de infraestructura de la asignatura.\n"
            "\n"
            "  El agente se va a detener.\n"
            "═══════════════════════════════════════════════════════════════"
        )
        # stderr para que el aviso se vea aunque el logging esté
        # filtrado o redirigido; logger.critical para que también
        # aparezca en los archivos de log persistentes.
        print(mensaje, file=sys.stderr, flush=True)
        logger.critical(
            "Supervisor no autorizado en %s (afiliación '%s'). "
            "Se requiere admin/owner. Deteniendo agente.",
            sala_jid, afiliacion,
        )
        try:
            self.registrar_evento_log(
                LOG_ERROR, self.muc_apodo,
                f"Supervisor no autorizado: afiliación "
                f"'{afiliacion}' insuficiente (se requiere "
                f"admin/owner). El agente se detendrá.",
                sala_id,
            )
        except Exception:
            # Si el log persistente todavía no está listo no debe
            # impedir la parada por afiliación.
            pass

        # Programar la parada en el bucle asyncio activo. Si el
        # método se invoca fuera de un bucle (caso típico en tests
        # unitarios), evitamos crear la corrutina para que no quede
        # huérfana y dejamos al llamador la responsabilidad del cierre.
        try:
            bucle = asyncio.get_running_loop()
        except RuntimeError:
            bucle = None
        if bucle is not None:
            bucle.create_task(self._detener_por_afiliacion())

    async def _detener_por_afiliacion(self) -> None:
        """Detiene el agente de forma ordenada tras detectar una
        afiliación MUC insuficiente.

        Se ejecuta como tarea asyncio porque ``stop()`` es una
        corrutina y el handler de presencia es síncrono.
        """
        try:
            if hasattr(self, "detener_persistencia"):
                await self.detener_persistencia()
        except Exception:
            pass
        try:
            await self.stop()
        except Exception:
            pass

    # ── Join MUC real mediante stanza de presencia ─────────────

    def _unirse_sala_muc(self, jid_sala: str, apodo: str) -> None:
        """Se une a una sala MUC enviando una stanza de presencia
        con el namespace ``http://jabber.org/protocol/muc``.

        A diferencia de ``presence.subscribe()``, este método realiza
        un join MUC real según XEP-0045: el servidor envía de vuelta
        las presencias de todos los ocupantes de la sala, lo que
        permite detectarlos en el handler ``_on_presencia_muc``.

        Args:
            jid_sala: JID completo de la sala (ej:
                ``tictactoe@conference.sinbad2.ujaen.es``).
            apodo: Nick con el que se une el supervisor.
        """
        stanza = self.client.make_presence(
            pto=f"{jid_sala}/{apodo}",
        )
        x_elem = SubElement(
            stanza.xml,
            "{http://jabber.org/protocol/muc}x",
        )
        # Solicitar 0 líneas de historial para evitar carga
        hist = SubElement(x_elem, "history")
        hist.set("maxchars", "0")
        stanza.send()

    # ── Handler de presencia MUC ─────────────────────────────────

    def _on_presencia_muc(self, presencia) -> None:
        """Handler que procesa TODAS las stanzas de presencia MUC.

        Se invoca cada vez que el cliente XMPP recibe una presencia.
        Filtra las que provienen de las salas MUC monitorizadas y
        realiza dos funciones:

        1. **Dashboard**: actualiza ``ocupantes_por_sala`` en tiempo
           real (añade, actualiza o elimina ocupantes).
        2. **Protocolo**: si un tablero cambia su status a
           ``"finished"``, crea un ``SolicitarInformeFSM`` para
           solicitar el informe de partida (paso 0).

        Args:
            presencia: Stanza de presencia recibida (slixmpp).
        """
        jid_from = presencia["from"]
        sala_jid_str = str(jid_from.bare)
        nick = str(jid_from.resource) if jid_from.resource else ""
        tipo = presencia["type"]

        # Solo procesar presencias de nuestras salas MUC
        sala_id = ""
        for sala in self.salas_muc:
            if sala["jid"] == sala_jid_str:
                sala_id = sala["id"]

        # ── Validación de afiliación (S-02) ───────────────────────
        # Cuando recibimos nuestra propia presencia MUC tras el
        # join, Prosody incluye la afiliación que nos ha asignado.
        # Si no es admin/owner, somos un supervisor no autorizado y
        # detenemos el agente con un mensaje claro en consola.
        # Se usa getattr() con valores por defecto para que los
        # tests unitarios que construyen el agente sin pasar por
        # setup() completo no fallen al ejecutar este handler.
        detenido = getattr(self, "_detenido_por_afiliacion", False)
        validadas = getattr(self, "_afiliacion_validada", set())
        if (
            sala_id
            and nick == self.muc_apodo
            and tipo != "unavailable"
            and not detenido
            and sala_id not in validadas
        ):
            self._validar_afiliacion(sala_id, sala_jid_str, presencia)

        if not sala_id or not nick or nick == self.muc_apodo:
            return

        # Tras detectar una afiliación insuficiente y solicitar la
        # parada del agente, ignorar cualquier presencia adicional
        # para no añadir ruido al log mientras el cierre se procesa.
        if getattr(self, "_detenido_por_afiliacion", False):
            return

        # ── Extraer información del ocupante ─────────────────
        show = str(presencia.get("show", ""))
        status = str(presencia.get("status", ""))
        jid_real = ""
        try:
            item_muc = presencia["muc"]["item"]
            if item_muc["jid"]:
                jid_real = str(item_muc["jid"])
        except Exception:
            pass

        jid_bare = jid_real.split("/")[0] if "/" in jid_real \
            else jid_real

        # Determinar rol y estado legible
        rol = "tablero" if nick.startswith("tablero_") else "jugador"
        estado = status if status else (show if show else "online")

        ocupantes = self.ocupantes_por_sala.get(sala_id, [])

        if tipo == "unavailable":
            # ── Ocupante abandona la sala ─────────────────────
            self.ocupantes_por_sala[sala_id] = [
                o for o in ocupantes if o["nick"] != nick
            ]
            self.registrar_evento_log(
                LOG_SALIDA, nick, "Ha abandonado la sala", sala_id,
            )

            # Si el tablero tenía un informe pendiente de
            # recibir, registrar un error en el log
            if nick.startswith("tablero_"):
                jid_tablero_muc = f"{sala_jid_str}/{nick}"
                jid_pendiente = ""
                if jid_tablero_muc in self.informes_pendientes:
                    jid_pendiente = jid_tablero_muc
                elif jid_bare \
                        and jid_bare in self.informes_pendientes:
                    jid_pendiente = jid_bare

                if jid_pendiente:
                    self.informes_pendientes.pop(
                        jid_pendiente, None,
                    )
                    self.registrar_evento_log(
                        LOG_ERROR, nick,
                        "Se desconectó con un informe "
                        "solicitado sin entregar",
                        sala_id,
                    )
                    logger.warning(
                        "Tablero %s abandonó sala %s con "
                        "informe pendiente",
                        nick, sala_id,
                    )
            return

        # ── Ocupante presente: añadir o actualizar ───────────
        # Las marcas temporales (joined_at, estado_cambiado_at) las
        # consume RevisarInactividadBehaviour para detectar
        # jugadores que llevan mucho tiempo sin jugar y tableros
        # cuya presencia no progresa (no cambian de estado o no
        # llegan nunca a 'finished').
        ahora = datetime.now()
        encontrado = False
        estado_anterior = ""
        for occ in ocupantes:
            if occ["nick"] == nick:
                estado_anterior = occ["estado"]
                occ["estado"] = estado
                if estado_anterior != estado:
                    occ["estado_cambiado_at"] = ahora
                if jid_bare:
                    occ["jid"] = jid_bare
                encontrado = True

        if not encontrado:
            # Nuevo ocupante: registrar entrada en la sala
            ocupantes.append({
                "nick": nick,
                "jid": jid_bare,
                "rol": rol,
                "estado": estado,
                "joined_at": ahora,
                "estado_cambiado_at": ahora,
            })
            self.ocupantes_por_sala[sala_id] = ocupantes

            # Registrar en el histórico (P-04): acumular JID y
            # nick para que la validación de jugadores observados
            # no genere falsos positivos si el jugador abandona
            # la sala antes de que se procese el informe.
            historico = self.ocupantes_historicos_por_sala.get(
                sala_id, set(),
            )
            if jid_bare:
                historico.add(jid_bare)
            historico.add(nick)
            self.ocupantes_historicos_por_sala[sala_id] = historico

            self.registrar_evento_log(
                LOG_ENTRADA, nick,
                f"Se ha unido a la sala ({rol})",
                sala_id,
            )
        elif estado_anterior and estado_anterior != estado \
                and nick.startswith("tablero_"):
            # Cambio de estado de un tablero: registrar transición
            self.registrar_evento_log(
                LOG_PRESENCIA, nick,
                f"Cambio de estado: {estado_anterior} → {estado}",
                sala_id,
            )

        # ── Mapeo tablero → sala ─────────────────────────────
        if nick.startswith("tablero_"):
            jid_completo = f"{sala_jid_str}/{nick}"
            self.tablero_a_sala[jid_completo] = sala_id
            if jid_bare:
                self.tablero_a_sala[jid_bare] = sala_id

        # ── Detección de tablero finalizado (paso 0) ─────────
        if not nick.startswith("tablero_") or status != "finished":
            return

        # Solo detectar si el estado CAMBIÓ a "finished" (S-01,
        # cambio 1). Ignorar redistribuciones de presencia donde
        # el tablero ya estaba en "finished" — estas son causadas
        # por eventos XMPP incidentales, no por una nueva partida.
        if estado_anterior == "finished":
            return

        jid_tablero = jid_bare if jid_bare \
            else f"{sala_jid_str}/{nick}"

        if jid_tablero in self.tableros_consultados:
            return

        self.tableros_consultados.add(jid_tablero)

        self.registrar_evento_log(
            LOG_PRESENCIA, nick, "Partida finalizada", sala_id,
        )

        # Comprobar si hay capacidad para crear un FSM nuevo
        # o si hay que encolar la solicitud para más adelante
        if len(self.informes_pendientes) \
                < self.max_fsm_concurrentes:
            self._crear_fsm_solicitud(jid_tablero, sala_id)
        else:
            self.tableros_en_cola.append(
                (jid_tablero, sala_id),
            )
            logger.info(
                "FSMs al límite (%d/%d): tablero %s encolado "
                "[sala: %s]",
                len(self.informes_pendientes),
                self.max_fsm_concurrentes,
                jid_tablero, sala_id,
            )

        # No desbloquear aqui: el discard se ejecuta en los
        # estados terminales del FSM, no en el handler de
        # presencia (S-01, cambio 2). Esto evita que una segunda
        # deteccion pase la guardia mientras el FSM esta activo.

    # ── Creación de FSM y gestión de la cola ─────────────────────────

    def _crear_fsm_solicitud(
        self, jid_tablero: str, sala_id: str,
    ) -> None:
        """Crea un SolicitarInformeFSM para un tablero finalizado.

        Registra el tablero en ``informes_pendientes`` y añade el
        behaviour al agente. Si ya existe un FSM activo para este
        tablero (defensa en profundidad S-01), ignora la solicitud.

        Args:
            jid_tablero: JID completo del tablero.
            sala_id: ID de la sala MUC.
        """
        # Guardia: evitar crear un FSM duplicado (S-01, cambio 2)
        if jid_tablero in self.informes_pendientes:
            logger.debug(
                "FSM ya activo para %s, ignorando duplicado",
                jid_tablero,
            )
            return

        self.informes_pendientes[jid_tablero] = sala_id

        nick = jid_tablero.split("/")[-1] \
            if "/" in jid_tablero else jid_tablero.split("@")[0]

        logger.info(
            "Creando SolicitarInformeFSM para %s [sala: %s] "
            "(activos: %d/%d, en cola: %d)",
            jid_tablero, sala_id,
            len(self.informes_pendientes),
            self.max_fsm_concurrentes,
            len(self.tableros_en_cola),
        )

        # Thread unico de la solicitud de informe. Se genera con la
        # utilidad comun de la ontologia para que todos los agentes del
        # sistema (jugador, tablero, supervisor) compartan el mismo
        # mecanismo de generacion y se evite cualquier colision.
        hilo = crear_thread_unico(jid_tablero, PREFIJO_THREAD_REPORT)

        fsm = SolicitarInformeFSM(
            jid_tablero=jid_tablero,
            sala_id=sala_id,
            hilo=hilo,
            timeout=self.timeout_respuesta,
            max_reintentos=self.max_reintentos,
        )

        plantilla = Template(thread=hilo)
        plantilla.set_metadata("ontology", ONTOLOGIA)

        self.add_behaviour(fsm, plantilla)

    def solicitar_siguiente_en_cola(self) -> None:
        """Procesa el siguiente tablero de la cola de espera.

        Se invoca desde los estados terminales del FSM cuando un
        ``informes_pendientes`` se libera. Si hay tableros
        encolados y hay capacidad, crea un nuevo FSM para el
        primero de la cola.
        """
        if not self.tableros_en_cola:
            return

        if len(self.informes_pendientes) \
                >= self.max_fsm_concurrentes:
            return

        jid_tablero, sala_id = self.tableros_en_cola.popleft()

        nick = jid_tablero.split("/")[-1] \
            if "/" in jid_tablero else jid_tablero.split("@")[0]

        logger.info(
            "Desencolando tablero %s [sala: %s] "
            "(restantes en cola: %d)",
            jid_tablero, sala_id,
            len(self.tableros_en_cola),
        )

        self.registrar_evento_log(
            LOG_SOLICITUD, nick,
            "Informe de partida solicitado (desde cola)",
            sala_id,
        )

        self._crear_fsm_solicitud(jid_tablero, sala_id)

    # ── Descubrimiento de salas MUC ────────────────────────────────

    async def _descubrir_salas_muc(self, servicio_muc: str) -> list[str]:
        """Descubre las salas disponibles en el servicio MUC mediante
        XEP-0030 (Service Discovery).

        Envía una consulta ``disco#items`` al servicio de conferencias
        (por ejemplo ``conference.sinbad2.ujaen.es``) y extrae los
        nombres de las salas que devuelve el servidor.

        Si el descubrimiento falla (servidor no disponible, servicio
        MUC sin soporte para disco, etc.), devuelve una lista vacía
        y registra un aviso en el log.

        Args:
            servicio_muc: JID del servicio de conferencias
                (ej: ``conference.sinbad2.ujaen.es``).

        Returns:
            Lista de nombres de salas descubiertas (parte local del
            JID, sin el dominio). Lista vacía si no se encuentra
            ninguna o si falla la consulta.
        """
        salas_descubiertas: list[str] = []

        try:
            self.client.register_plugin("xep_0030")

            resultado = await self.client.plugin["xep_0030"].get_items(
                jid=servicio_muc,
            )

            items = resultado["disco_items"]["items"]
            for item in items:
                jid_sala = str(item[0])
                # Extraer la parte local del JID (antes de @)
                nombre = jid_sala.split("@")[0] if "@" in jid_sala \
                    else jid_sala
                salas_descubiertas.append(nombre)

            logger.info(
                "Descubrimiento XEP-0030 en %s: %d sala(s) encontrada(s)%s",
                servicio_muc,
                len(salas_descubiertas),
                " — " + ", ".join(salas_descubiertas)
                if salas_descubiertas else "",
            )

        except Exception as error:
            logger.warning(
                "No se pudieron descubrir salas en %s: %s. "
                "Se usará la configuración por defecto.",
                servicio_muc, error,
            )

        return salas_descubiertas

    # ── Métodos auxiliares ────────────────────────────────────────

    def _identificar_sala(self, jid_str: str) -> str:
        """Determina a qué sala MUC pertenece un JID.

        Busca qué sala contiene el JID comprobando si el JID de la
        sala está incluido en el JID del contacto.

        Args:
            jid_str: JID completo del contacto.

        Returns:
            ID de la sala o cadena vacía si no pertenece a ninguna.
        """
        resultado = ""
        for sala in self.salas_muc:
            if sala["jid"] in jid_str:
                resultado = sala["id"]

        return resultado

    def obtener_sala_de_tablero(self, jid_tablero: str) -> str:
        """Busca a qué sala pertenece un tablero por su JID.

        Consulta el mapeo ``tablero_a_sala`` que se rellena durante
        la monitorización de presencia y el callback.

        Args:
            jid_tablero: JID del tablero (puede incluir recurso).

        Returns:
            ID de la sala a la que pertenece el tablero.
        """
        jid_base = jid_tablero.split("/")[0] if "/" in jid_tablero \
            else jid_tablero
        resultado = self.tablero_a_sala.get(
            jid_tablero,
            self.tablero_a_sala.get(jid_base, ""),
        )

        # Fallback: primera sala configurada
        if not resultado and self.salas_muc:
            resultado = self.salas_muc[0]["id"]

        return resultado

    def registrar_evento_log(
        self, tipo: str, de: str, detalle: str, sala_id: str = "",
    ) -> None:
        """Añade un evento al log cronológico de una sala.

        Args:
            tipo: Tipo del evento (presencia, informe, abortada,
                salida, timeout).
            de: Identificador del agente que origina el evento.
            detalle: Descripción legible del evento.
            sala_id: ID de la sala a la que pertenece el evento.
        """
        sala_destino = sala_id
        if not sala_destino and self.salas_muc:
            sala_destino = self.salas_muc[0]["id"]

        evento = {
            "ts": datetime.now().strftime("%H:%M:%S"),
            "tipo": tipo,
            "de": de,
            "detalle": detalle,
        }

        if sala_destino not in self.log_por_sala:
            self.log_por_sala[sala_destino] = []

        self.log_por_sala[sala_destino].insert(0, evento)

        # Persistir en SQLite
        if hasattr(self, "almacen") and self.almacen is not None:
            self.almacen.guardar_evento(
                sala_destino, tipo, de, detalle, evento["ts"],
            )

        # Notificar a los suscriptores SSE
        try:
            from web.supervisor_handlers import notificar_sse
            notificar_sse("state", {
                "sala_id": sala_destino,
                "evento": evento,
            })
        except ImportError:
            pass

        logger.debug(
            "Evento de log [%s/%s] %s — %s",
            sala_destino, tipo, de, detalle,
        )

    async def expulsar_ocupantes_salas(self) -> None:
        """Expulsa a todos los ocupantes de las salas MUC monitorizadas.

        Solo actúa en modo examen. Forma parte de la secuencia de
        apagado ordenado del supervisor: una vez cerrada la
        persistencia, se expulsa a los agentes que aún estén en cada
        sala del examen (``examen@examen...`` en el submodo grupo,
        ``PC-NN@examen...`` en el submodo individual) cambiando su rol
        MUC a ``none`` (XEP-0045 §9.1), de modo que finalicen de forma
        limpia. A continuación, :meth:`eliminar_salas_examen` destruye
        las salas. El supervisor tiene afiliación ``owner``/``admin``
        en estas salas —se la asigna Prosody mediante
        ``muc_room_default_admins``—, lo que le autoriza tanto a
        expulsar ocupantes como a destruir la sala.

        El método es defensivo: el fallo al expulsar a un ocupante
        concreto o al contactar con una sala se registra como
        advertencia, pero no interrumpe el resto de expulsiones ni el
        apagado ordenado del supervisor. Debe invocarse **después** de
        ``detener_persistencia()`` —para que los datos de la sesión
        queden guardados antes de cualquier tarea de limpieza— y
        **antes** de ``stop()``, porque necesita el cliente XMPP
        todavía conectado. Tras cerrar la persistencia, los eventos de
        log que registre este método se mantienen solo en memoria.
        """
        modo = getattr(self, "modo", "")
        if modo == MODO_EXAMEN:
            plugin_muc = self.client.plugin["xep_0045"]
            total_expulsados = 0
            for sala in self.salas_muc:
                sala_id = sala["id"]
                jid_sala = sala["jid"]
                # Se copia la lista de ocupantes porque las stanzas
                # de presencia 'unavailable' que el servidor envía al
                # expulsar a cada ocupante modifican ocupantes_por_sala
                # y no se debe alterar la colección que se itera.
                ocupantes = list(
                    self.ocupantes_por_sala.get(sala_id, []),
                )
                expulsados_sala = 0
                for ocupante in ocupantes:
                    nick = ocupante["nick"]
                    # El supervisor no se expulsa a sí mismo: abandona
                    # la sala por su cuenta al ejecutar stop().
                    es_el_propio_supervisor = nick == self.muc_apodo
                    if not es_el_propio_supervisor:
                        try:
                            await plugin_muc.set_role(
                                jid_sala, nick, ROL_MUC_EXPULSADO,
                            )
                            expulsados_sala += 1
                        except Exception as error:  # noqa: BLE001
                            logger.warning(
                                "No se pudo expulsar a '%s' de la "
                                "sala %s: %s", nick, sala_id, error,
                            )
                if expulsados_sala > 0:
                    total_expulsados += expulsados_sala
                    self.registrar_evento_log(
                        LOG_ADVERTENCIA, "supervisor",
                        f"{expulsados_sala} agente(s) expulsado(s) "
                        f"de la sala al finalizar el supervisor",
                        sala_id,
                    )
            logger.info(
                "Expulsión de ocupantes (modo examen) completada: "
                "%d agente(s) expulsado(s) de %d sala(s)",
                total_expulsados, len(self.salas_muc),
            )

    async def eliminar_salas_examen(self) -> None:
        """Destruye las salas MUC del examen creadas por el supervisor.

        Solo actúa en modo examen. Es el último paso de limpieza del
        apagado ordenado: una vez cerrada la persistencia y expulsados
        los ocupantes, el supervisor destruye cada sala del examen
        (``examen@examen...`` en el submodo grupo, ``PC-NN@examen...``
        en el submodo individual) mediante la operación de destrucción
        de XEP-0045 §10.9.

        Como el propio supervisor vuelve a crear las salas al arrancar
        —tiene afiliación ``owner``/``admin`` en el componente del
        examen—, destruirlas al apagar garantiza que cada ejecución
        del supervisor parte de salas nuevas, sin ocupantes ni estado
        residual de la sesión anterior.

        El método es defensivo: el fallo al destruir una sala concreta
        se registra como advertencia y no interrumpe el resto de
        destrucciones ni el apagado ordenado del supervisor. Debe
        invocarse con el cliente XMPP todavía conectado, es decir,
        después de ``detener_persistencia()`` y
        ``expulsar_ocupantes_salas()``, y antes de ``stop()``.
        """
        modo = getattr(self, "modo", "")
        if modo == MODO_EXAMEN:
            plugin_muc = self.client.plugin["xep_0045"]
            total_eliminadas = 0
            for sala in self.salas_muc:
                jid_sala = sala["jid"]
                try:
                    await plugin_muc.destroy(
                        jid_sala, reason=RAZON_DESTRUCCION_SALA,
                    )
                    total_eliminadas += 1
                except Exception as error:  # noqa: BLE001
                    logger.warning(
                        "No se pudo destruir la sala %s: %s",
                        jid_sala, error,
                    )
            logger.info(
                "Destrucción de salas (modo examen) completada: "
                "%d de %d sala(s) destruida(s)",
                total_eliminadas, len(self.salas_muc),
            )

    async def detener_persistencia(self) -> None:
        """Finaliza la ejecución actual y cierra el almacén SQLite.

        Debe invocarse antes de detener el agente para que la
        ejecución quede correctamente marcada como finalizada.

        Si quedan solicitudes de informe en curso (FSMs que aún
        no han recibido respuesta), se registra un evento
        ``pendiente`` en el log de cada sala afectada para dejar
        constancia de los informes no recibidos.
        """
        # Registrar informes que se solicitaron pero no se
        # recibieron antes de la detención del supervisor
        if hasattr(self, "informes_pendientes"):
            for jid_tablero, sala_id \
                    in self.informes_pendientes.items():
                nick_tablero = jid_tablero.split("/")[-1] \
                    if "/" in jid_tablero \
                    else jid_tablero.split("@")[0]
                self.registrar_evento_log(
                    LOG_ADVERTENCIA, nick_tablero,
                    "Informe solicitado sin recibir al "
                    "finalizar el supervisor",
                    sala_id,
                )
                logger.warning(
                    "Informe pendiente de %s [sala: %s] no "
                    "recibido al detener el supervisor",
                    jid_tablero, sala_id,
                )
            self.informes_pendientes.clear()

        # Registrar tableros que estaban en cola (detectados
        # como finalizados pero cuyo informe nunca se solicitó
        # porque se alcanzó el límite de FSMs concurrentes)
        if hasattr(self, "tableros_en_cola"):
            for jid_tablero, sala_id in self.tableros_en_cola:
                nick_tablero = jid_tablero.split("/")[-1] \
                    if "/" in jid_tablero \
                    else jid_tablero.split("@")[0]
                self.registrar_evento_log(
                    LOG_ADVERTENCIA, nick_tablero,
                    "Informe no solicitado al finalizar el "
                    "supervisor (estaba en cola de espera)",
                    sala_id,
                )
                logger.warning(
                    "Tablero encolado %s [sala: %s] no "
                    "solicitado al detener el supervisor",
                    jid_tablero, sala_id,
                )
            self.tableros_en_cola.clear()

        if hasattr(self, "almacen") and self.almacen is not None:
            self.almacen.finalizar_ejecucion()
            self.almacen.cerrar()
            self.almacen = None
            logger.info("Persistencia detenida correctamente")
