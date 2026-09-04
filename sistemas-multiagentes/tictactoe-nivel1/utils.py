"""
Módulo de utilidades y funciones factoría para agentes SPADE.

Centraliza la creación y el arranque de agentes SPADE encapsulando
la separación de parámetros que impone SPADE 4.x: el constructor del
agente acepta ``port`` y ``verify_security``, mientras que el método
``start()`` acepta ``auto_register``.  Las funciones factoría de este
módulo evitan que el alumno tenga que recordar estos detalles.

Las funciones de carga de configuración (``cargar_configuracion``,
``cargar_plantillas``, ``generar_agentes``, ``construir_jid``) residen en
``config/configuracion.py``
y se re-exportan aquí por conveniencia, de forma que el alumno pueda
importar todo desde un único punto::

    from utils import cargar_configuracion, crear_agente, arrancar_agente

Autor: Profesor (material de apoyo)
"""
import asyncio
import logging
from typing import Any

from spade.agent import Agent

# Re-exportar las funciones de configuración para acceso centralizado
from config.configuracion import (   # noqa: F401
    cargar_configuracion,
    cargar_plantillas,
    cargar_torneos,
    construir_jid,
    construir_nick_jugador,
    construir_nick_tablero,
    generar_agentes,
    normalizar_nombre_sala,
)

logger = logging.getLogger(__name__)


# ─── Funciones factoría para agentes SPADE ───────────────────────────────────

def crear_agente(
    clase_agente: type[Agent],
    nombre: str,
    config_xmpp: dict[str, Any],
    contrasena: str | None = None,
) -> Agent:
    """Crea una instancia de agente SPADE con los parámetros de conexión.

    Construye el JID y pasa al constructor únicamente los parámetros que
    este acepta (``port`` y ``verify_security``).  El parámetro
    ``auto_register`` se gestiona aparte en ``arrancar_agente()``, ya que
    pertenece a ``start()``.

    Args:
        clase_agente: Clase (o subclase) de ``spade.agent.Agent`` a
            instanciar (por ejemplo, ``AgenteTablero``).
        nombre: Nombre del agente (parte local del JID, sin dominio).
        config_xmpp: Diccionario con la configuración del perfil XMPP
            activo (resultado de ``cargar_configuracion()["xmpp"]``).
        contrasena: Contraseña del agente en el servidor XMPP.  Si no
            se proporciona, se usa ``password_defecto`` del perfil.

    Además, si la configuración incluye el JID completo de la sala MUC
    (``sala_muc_completa``), esta función deja instaladas
    automáticamente en el agente las dos utilidades del modo examen,
    sin que el alumno tenga que **añadir ninguna línea** a sus agentes:

    * el **aviso de errores** cuando la sala todavía no existe porque
      el supervisor aún no la ha creado (ver
      ``registrar_aviso_errores_examen``);
    * el **cierre ordenado** cuando el supervisor finaliza el examen y
      expulsa a los agentes o destruye la sala (ver
      ``registrar_cierre_ordenado_examen``).

    Returns:
        Instancia del agente, lista para ser arrancada con
        ``arrancar_agente()``.
    """
    jid = construir_jid(nombre, config_xmpp)
    password = contrasena or config_xmpp.get("password_defecto", "secret")

    resultado = clase_agente(
        jid,
        password,
        port=config_xmpp.get("puerto", 5222),
        verify_security=config_xmpp.get("verify_security", False),
    )

    # Dejar instaladas las utilidades del modo examen sin intervención
    # del alumno: si la configuración trae el JID completo de la sala
    # MUC, los manejadores de presencia (aviso de errores al inicio y
    # cierre ordenado al final) se registrarán automáticamente en el
    # momento adecuado del ciclo de vida del agente.
    sala_examen = config_xmpp.get("sala_muc_completa")
    if sala_examen:
        _instalar_aviso_examen(resultado, sala_examen)
        _instalar_cierre_ordenado_examen(resultado, sala_examen)

    return resultado


async def arrancar_agente(
    agente: Agent,
    config_xmpp: dict[str, Any],
) -> None:
    """Arranca un agente SPADE pasando ``auto_register`` a ``start()``.

    En SPADE 4.x, ``auto_register`` es parámetro de ``start()``, no del
    constructor.  Esta función encapsula esa particularidad.

    Args:
        agente: Instancia del agente ya creada con ``crear_agente()``.
        config_xmpp: Diccionario con la configuración del perfil XMPP
            activo.
    """
    auto_registro = config_xmpp.get("auto_register", True)
    await agente.start(auto_register=auto_registro)


# ─── Sonda del supervisor: ¿está creada la sala del examen? ──────────────────
# En el modo examen, el componente MUC dedicado del servidor de la
# asignatura ('examen.<dominio>') tiene 'restrict_room_creation =
# "admin"': si el supervisor del profesor no ha creado todavía la
# sala, ningún agente del alumno puede unirse a ella. Sin una
# comprobación previa, los 16 agentes del laboratorio (o los 15 del
# examen individual) intentarían unirse en paralelo y el servidor
# devolvería el mismo error a cada uno: el log del alumno se llenaría
# con 15-16 mensajes idénticos antes de que el lanzador concluyera
# nada.
#
# La sonda evita ese ruido. Antes de generar los agentes reales, un
# agente temporal lanza UNA consulta de Service Discovery (XEP-0030,
# disco#info) al JID de la sala:
#
#   - Si el servidor responde con identidades MUC, la sala ya está
#     creada y los agentes pueden unirse. El lanzador continúa.
#   - Si el servidor responde con error ('item-not-found',
#     'forbidden', 'not-allowed'…), la sala no existe. El lanzador
#     muestra UNA vez el motivo (con la marca '[Examen]' si el
#     servidor la añadió) y aborta con SystemExit, sin crear ningún
#     agente.
#
# El alumno no tiene que invocar esta sonda a mano: 'main.py' la
# ejecuta automáticamente cuando la modalidad activa es 'examen'.

# Margen de espera para la consulta disco#info. Es una operación
# síncrona del lado del servidor (consulta de tabla de salas), así
# que un valor pequeño basta para no entorpecer el arranque cuando
# el supervisor sí está activo.
TIMEOUT_SONDA_SUPERVISOR_SEGUNDOS = 8.0

# Nombre local del agente sonda. Se elige uno reconocible para que,
# si aparece en logs del servidor, sea evidente que es la
# comprobación previa del lanzador y no un agente del alumno.
_NOMBRE_AGENTE_SONDA = "sonda_supervisor"


async def comprobar_supervisor_activo(
    config_xmpp: dict[str, Any],
    sala_jid: str,
    timeout: float = TIMEOUT_SONDA_SUPERVISOR_SEGUNDOS,
) -> tuple[bool, str]:
    """Comprueba si el supervisor del examen tiene creada la sala.

    Arranca un agente sonda temporal, lanza una consulta disco#info
    al JID de la sala MUC del examen y devuelve si la sala existe.
    Si el servidor responde con error, se extrae la condición XMPP
    y el texto explicativo (que el servidor antepone con la marca
    ``[Examen]`` cuando el módulo del Prosody está cargado) para
    que el llamador pueda mostrarlo UNA sola vez.

    La sonda no se une a la sala: solo pregunta por sus
    capacidades. El cliente XMPP se detiene siempre antes de
    retornar, incluso si la consulta lanzó excepción, para no dejar
    sesiones colgadas en el servidor.

    Args:
        config_xmpp: Perfil XMPP resuelto (resultado de
            ``cargar_configuracion()["xmpp"]``).
        sala_jid: JID completo de la sala MUC que se debe consultar
            (típicamente ``config_xmpp["sala_muc_completa"]``).
        timeout: Segundos máximos que se espera la respuesta del
            servidor. El valor por defecto es generoso para tolerar
            redes lentas (VPN universitaria).

    Returns:
        Tupla ``(activo, mensaje)``:

        - ``activo`` (bool): ``True`` si la sala existe y los
          agentes pueden unirse; ``False`` si no existe o si la
          consulta falló por cualquier motivo.
        - ``mensaje`` (str): explicación del servidor o resumen del
          fallo. Cadena vacía cuando ``activo`` es ``True``. Pensado
          para registrarlo UNA sola vez en el log del lanzador.
    """
    sonda = crear_agente(Agent, _NOMBRE_AGENTE_SONDA, config_xmpp)
    activo = False
    mensaje = ""

    try:
        await arrancar_agente(sonda, config_xmpp)
        cliente = sonda.client
        # 'get_info' es coroutine en slixmpp 1.8+. La llamada lanza
        # IqError cuando el servidor responde con error de presencia
        # o de IQ, y IqTimeout si no llega respuesta en el plazo.
        try:
            await asyncio.wait_for(
                cliente["xep_0030"].get_info(jid=sala_jid),
                timeout=timeout,
            )
            activo = True
        except asyncio.TimeoutError:
            mensaje = (
                f"sin respuesta del servidor a la consulta "
                f"disco#info de la sala '{sala_jid}' tras "
                f"{timeout:.1f} s"
            )
        except Exception as error:  # noqa: BLE001
            # IqError de slixmpp expone 'iq' con la respuesta de error.
            # Se intenta extraer condición y texto sin acoplar el
            # código a un tipo concreto de la librería.
            condicion, texto = _extraer_error_disco(error)
            partes = []
            if condicion:
                partes.append(f"condición XMPP '{condicion}'")
            if texto:
                partes.append(texto)
            if partes:
                mensaje = ". ".join(partes)
            else:
                mensaje = str(error)
    finally:
        try:
            await sonda.stop()
        except Exception as error_stop:  # noqa: BLE001
            logger.debug(
                "Excepción ignorada al detener la sonda del "
                "supervisor: %s", error_stop,
            )

    return (activo, mensaje)


def _extraer_error_disco(error: Exception) -> tuple[str, str]:
    """Extrae condición XMPP y texto explicativo de un error de IQ.

    ``slixmpp.exceptions.IqError`` expone el ``Iq`` de respuesta en
    ``error.iq``; dentro está el bloque ``<error>`` con la
    condición estándar (``item-not-found``, ``forbidden``,
    ``not-allowed``…) y un ``<text>`` con la explicación que el
    servidor añade. El módulo Lua ``mod_examen_friendly_error``
    antepone la marca ``[Examen]`` a ese texto.

    Esta función no importa ``IqError`` directamente: se apoya en
    la API pública de cualquier excepción slixmpp con el atributo
    ``iq`` para que el archivo siga siendo testeable sin un
    servidor XMPP real.

    Args:
        error: Excepción capturada al consultar disco#info.

    Returns:
        Tupla ``(condicion, texto)``. Ambas pueden ser cadena vacía
        si la excepción no expone esa información.
    """
    condicion = ""
    texto = ""
    iq = getattr(error, "iq", None)
    if iq is not None:
        try:
            condicion = iq["error"]["condition"] or ""
            texto = (iq["error"]["text"] or "").strip()
        except (KeyError, TypeError):
            pass
    return (condicion, texto)


def unirse_a_sala_muc(
    agente: Agent,
    sala_jid: str,
    nick: str | None = None,
) -> None:
    """Hace que un agente del alumno se una a la sala MUC con un nick
    único y coherente con su configuración.

    En la sala del examen, el profesor ve a la vez los tableros y
    los jugadores de todos los alumnos. Si dos agentes intentaran
    unirse con el mismo nick, el servidor rechazaría al segundo con
    el error ``conflict``; y si los 12 jugadores de un alumno
    entraran con el mismo nick, el panel del supervisor sería
    ilegible. Esta función traslada el nick que la utilidad ya
    asignó a cada agente al ``join`` MUC.

    Resolución del nick:

    1. Si el llamador pasa ``nick`` explícitamente, ese valor se
       usa tal cual (válido para los agentes que el alumno cree
       fuera del flujo del lanzador).
    2. Si el agente lleva ``nick_muc`` en ``config_parametros``
       (caso normal: ``main.py`` lo inyecta a través de
       ``generar_agentes``), se usa ese.
    3. En último caso se cae a la parte local del JID del agente,
       que es siempre única dentro del servidor.

    Args:
        agente: Agente SPADE ya arrancado (su ``client`` debe
            existir y tener registrado el plugin XEP-0045).
        sala_jid: JID completo de la sala MUC.
        nick: Nick explícito a usar. Si es ``None``, se aplica la
            resolución de los puntos 2 y 3.
    """
    parametros = getattr(agente, "config_parametros", {}) or {}
    parte_local = str(agente.jid).split("@", 1)[0]

    if nick is not None:
        nick_efectivo = nick
    elif parametros.get("nick_muc"):
        nick_efectivo = str(parametros["nick_muc"])
    else:
        nick_efectivo = parte_local

    muc = agente.client.plugin["xep_0045"]
    muc.join_muc(sala_jid, nick=nick_efectivo)
    logger.info(
        "Agente '%s' unido a la sala MUC '%s' con nick '%s'",
        agente.jid, sala_jid, nick_efectivo,
    )


# ─── Aviso del error amigable del modo examen ────────────────────────────────
# En el modo examen, el componente MUC dedicado del servidor de la
# asignatura ('examen.<dominio>') tiene la directiva
# 'restrict_room_creation = "admin"': solo el supervisor del profesor
# puede crear las salas. Si un agente del alumno arranca antes que el
# supervisor, su intento de unirse a la sala recibe un error de
# presencia (condición XMPP 'item-not-found', 'not-allowed' o
# 'forbidden'). El módulo Lua 'mod_examen_friendly_error' del servidor
# añade a ese error un elemento <text> con la marca '[Examen]'
# y una explicación en español de qué hacer (esperar al supervisor).

# Marca que el módulo 'mod_examen_friendly_error' del servidor antepone
# al texto explicativo. Se documenta como constante para que el alumno
# pueda reconocerla en los logs y, si lo desea, filtrarla.
MARCA_ERROR_EXAMEN = "[Examen]"

# Códigos de estado MUC (XEP-0045) que el servidor incluye en las
# presencias 'unavailable' y que permiten reconocer el FIN del examen:
#   110 → la presencia se refiere a uno mismo (autopresencia). Permite
#         distinguir la propia salida de la de otros ocupantes.
#   307 → el ocupante ha sido expulsado de la sala (kick).
#   332 → la sala ha sido destruida.
# El Agente Supervisor del profesor, al apagarse, expulsa a los
# ocupantes (307) y destruye las salas (332) del examen.
CODIGO_MUC_AUTOPRESENCIA = "110"
CODIGO_MUC_EXPULSADO = "307"
CODIGO_MUC_SALA_DESTRUIDA = "332"


def _extraer_condicion_y_texto_error(presencia) -> tuple[str, str]:
    """Extrae la condición XMPP y el texto explicativo de un error.

    Un ``<presence type="error">`` contiene un elemento ``<error>``
    con una condición estándar (``item-not-found``, ``not-allowed``,
    ``forbidden``, …) y, opcionalmente, un ``<text>`` con una
    explicación legible. En el modo examen, el módulo Lua
    ``mod_examen_friendly_error`` del servidor rellena ese ``<text>``
    con la marca ``[Examen]`` y una explicación en español.

    Args:
        presencia: Stanza de presencia de tipo ``error`` (slixmpp).

    Returns:
        Tupla ``(condicion, texto)``. ``condicion`` es la condición
        XMPP (``"desconocida"`` si no se encuentra); ``texto`` es la
        explicación del servidor (cadena vacía si el error no
        incluye el elemento ``<text>``).
    """
    # El elemento <error> puede llegar con el espacio de nombres del
    # stream ('{jabber:client}error') o sin él. Se prueban ambos con
    # comparaciones explícitas a None: un Element no debe evaluarse
    # por su valor de verdad (ElementTree lo desaconseja).
    elemento_error = presencia.xml.find("{jabber:client}error")
    if elemento_error is None:
        elemento_error = presencia.xml.find("error")
    condicion = "desconocida"
    texto = ""
    if elemento_error is not None:
        for hijo in elemento_error:
            # El tag llega como '{espacio_de_nombres}etiqueta'; se
            # conserva solo la etiqueta local.
            etiqueta = hijo.tag.split("}", 1)[-1]
            if etiqueta == "text":
                texto = (hijo.text or "").strip()
            elif condicion == "desconocida":
                condicion = etiqueta
    return (condicion, texto)


def registrar_aviso_errores_examen(
    agente: Agent, sala_jid: str,
) -> None:
    """Registra en el agente el aviso del error amigable del modo examen.

    Esta función deja al agente preparado para **mostrar** el mensaje
    que el servidor envía cuando un tablero o un jugador intenta
    unirse a la sala del examen antes de que el supervisor del
    profesor la haya creado. Sin ella, ese mensaje llega al cliente
    XMPP pero se descarta en silencio: el agente solo percibiría un
    timeout sin causa aparente, fácil de confundir con un fallo de
    credenciales, de red o del propio código del alumno.

    En el flujo normal del examen **el alumno no tiene que hacer nada**:
    el lanzador (``main.py``) crea los agentes con ``crear_agente()``, y
    esa factoría ya deja instalado el aviso automáticamente. Esta
    función queda como punto de entrada para los casos en que el alumno
    arranque sus agentes sin la factoría: en tal caso, se invoca una
    sola vez en el ``setup()`` del agente, **antes** de enviar el join a
    la sala MUC::

        from utils import registrar_aviso_errores_examen

        async def setup(self):
            self.client.register_plugin("xep_0045")
            registrar_aviso_errores_examen(self, self.SALA_MUC)
            # ... a continuación, el join MUC del agente ...

    Internamente registra un manejador del evento ``presence_error``
    del cliente XMPP. El manejador solo atiende los errores cuyo
    origen empieza por ``sala_jid`` (ignora los de otros orígenes
    para no mezclar diagnósticos), extrae la condición XMPP y el
    texto explicativo del servidor, y los registra con
    ``logger.error``.

    Args:
        agente: Agente SPADE cuyo cliente XMPP (``agente.client``)
            recibirá el manejador. Debe invocarse después de que el
            cliente exista (es decir, dentro de ``setup()`` o, como
            hace ``crear_agente()``, en el hook posterior a la
            conexión).
        sala_jid: JID de la sala MUC a la que el agente intenta
            unirse (por ejemplo ``"examen@examen.sinbad2.ujaen.es"``).
    """
    def _on_presencia_error(presencia) -> None:
        jid_origen = (
            str(presencia["from"]) if presencia["from"] else ""
        )
        # Solo se procesan los errores que provienen de la sala MUC
        # a la que este agente intenta unirse. La comparación es
        # insensible a mayúsculas: el localpart de un JID XMPP no lo
        # es (RFC 7622) y el servidor entrega el 'from' del error ya
        # normalizado a minúsculas, mientras que 'sala_jid' podría
        # llegar con otra combinación de mayúsculas y minúsculas si el
        # agente lo construyó sin canonizar.
        if jid_origen.lower().startswith(sala_jid.lower()):
            condicion, texto = _extraer_condicion_y_texto_error(
                presencia,
            )
            if texto:
                logger.error(
                    "El servidor rechazó la unión a la sala '%s' "
                    "(condición XMPP: %s). %s",
                    sala_jid, condicion, texto,
                )
            else:
                logger.error(
                    "El servidor rechazó la unión a la sala '%s': "
                    "condición XMPP '%s' (el servidor no añadió "
                    "texto explicativo).",
                    sala_jid, condicion,
                )

    agente.client.add_event_handler(
        "presence_error", _on_presencia_error,
    )
    logger.debug(
        "Aviso de errores del modo examen registrado para la sala %s",
        sala_jid,
    )


def _instalar_aviso_examen(agente: Agent, sala_jid: str) -> None:
    """Programa el registro automático del aviso del modo examen.

    Esta función resuelve un problema de orden temporal. El manejador
    de ``presence_error`` debe quedar registrado **antes** de que el
    agente intente unirse a la sala MUC; de lo contrario, el error de
    presencia que devuelve el servidor podría llegar y descartarse sin
    que nadie lo escuche. Pero el cliente XMPP del agente
    (``agente.client``) no existe hasta que ``start()`` lo crea, de
    modo que no se puede registrar el manejador en el momento de
    construir el agente.

    La solución se apoya en ``_hook_plugin_after_connection``, un punto
    del ciclo de vida de SPADE pensado precisamente para enganchar
    extensiones: se ejecuta **después** de que el cliente esté creado y
    conectado, y **antes** de ``setup()`` (donde el alumno hace el
    join). Esta función envuelve ese hook para que, además de su
    comportamiento original, registre el aviso del modo examen.

    Gracias a ello, ``crear_agente()`` puede dejar el aviso instalado
    sin que el alumno añada ninguna línea a sus agentes.

    Args:
        agente: Instancia de agente recién creada y todavía sin
            arrancar (su cliente XMPP aún no existe).
        sala_jid: JID completo de la sala MUC del modo examen.
    """
    # Se conserva el hook original (por defecto no hace nada, pero
    # podría estar sobrescrito) para no perder su comportamiento.
    hook_original = agente._hook_plugin_after_connection

    async def _hook_con_aviso_examen() -> None:
        await hook_original()
        registrar_aviso_errores_examen(agente, sala_jid)

    agente._hook_plugin_after_connection = _hook_con_aviso_examen


# ─── Cierre ordenado al finalizar el examen ──────────────────────────────────
# Cuando el profesor detiene su Agente Supervisor, este —como parte de
# su apagado ordenado— expulsa a los ocupantes de las salas del examen y
# a continuación destruye las salas, para que la siguiente ejecución del
# supervisor parta de salas nuevas. El servidor comunica esto a cada
# agente del alumno con una presencia 'unavailable' que lleva un código
# de estado MUC: 307 (expulsado) o 332 (sala destruida). El propósito de
# esa limpieza del supervisor NO es provocar fallos en los agentes del
# alumno: lo correcto es que estos lo detecten y finalicen de forma
# ordenada, en lugar de quedarse esperando mensajes que ya no llegarán o
# fallar al intentar enviar a una sala que ya no existe.


def _extraer_codigos_estado_muc(presencia) -> set[str]:
    """Extrae los códigos ``<status>`` del elemento ``muc#user`` de una
    presencia.

    Una presencia MUC puede llevar un elemento
    ``<x xmlns="http://jabber.org/protocol/muc#user">`` con uno o varios
    ``<status code="..."/>``. Esta función devuelve el conjunto de
    códigos presentes (como cadenas), o un conjunto vacío si la
    presencia no incluye ninguno.

    Args:
        presencia: Stanza de presencia (slixmpp).

    Returns:
        Conjunto con los códigos de estado MUC encontrados.
    """
    espacio_muc_user = "{http://jabber.org/protocol/muc#user}"
    codigos: set[str] = set()
    elemento_x = presencia.xml.find(f"{espacio_muc_user}x")
    if elemento_x is not None:
        for hijo in elemento_x:
            if hijo.tag.split("}", 1)[-1] == "status":
                codigo = hijo.get("code", "")
                if codigo:
                    codigos.add(codigo)
    return codigos


def _es_fin_de_examen(codigos: set[str]) -> bool:
    """Determina si unos códigos de estado MUC indican el fin del examen.

    El examen ha terminado para este agente cuando su **propia**
    presencia (código 110) sale de la sala por **expulsión** (307) o
    por **destrucción de la sala** (332). El código 110 es esencial:
    sin él, la presencia podría corresponder a la salida de otro
    ocupante, no a la de este agente.

    Args:
        codigos: Conjunto de códigos de estado MUC de una presencia.

    Returns:
        ``True`` si la presencia indica que el examen ha terminado
        para este agente; ``False`` en caso contrario.
    """
    es_autopresencia = CODIGO_MUC_AUTOPRESENCIA in codigos
    fin_de_sala = bool(
        codigos & {CODIGO_MUC_EXPULSADO, CODIGO_MUC_SALA_DESTRUIDA},
    )
    return es_autopresencia and fin_de_sala


def registrar_cierre_ordenado_examen(
    agente: Agent, sala_jid: str,
) -> None:
    """Registra en el agente el cierre ordenado al finalizar el examen.

    Cuando el Agente Supervisor del profesor se detiene, expulsa a los
    ocupantes de las salas del examen y destruye dichas salas. El
    servidor avisa de ello a cada agente del alumno con una presencia
    ``unavailable`` que lleva el código de estado MUC 307 (expulsado) o
    332 (sala destruida).

    Sin un manejador que lo capture, el agente del alumno no se entera
    de que el examen ha terminado: sus comportamientos seguirían
    esperando mensajes que ya no llegarán (esperas que nunca terminan)
    o fallarían al intentar enviar a una sala que ya no existe
    (finalización abrupta por una excepción no controlada). Ninguno de
    los dos comportamientos es la intención de la utilidad de limpieza
    del supervisor.

    Esta función deja al agente preparado para **finalizar de forma
    ordenada**: al detectar que su propia presencia (código 110) sale
    de la sala del examen por expulsión o destrucción, registra un
    mensaje informativo y detiene el agente con ``agente.stop()``.

    Al igual que :func:`registrar_aviso_errores_examen`, el alumno
    **no tiene que escribir código nuevo**: ``crear_agente()`` deja
    esta utilidad instalada automáticamente. Si se quisiera registrar
    a mano, basta con invocarla una vez en el ``setup()`` del agente,
    después de crear el cliente XMPP::

        from utils import registrar_cierre_ordenado_examen

        async def setup(self):
            self.client.register_plugin("xep_0045")
            registrar_cierre_ordenado_examen(self, self.SALA_MUC)
            # ... a continuación, el join MUC del agente ...

    Args:
        agente: Agente SPADE cuyo cliente XMPP (``agente.client``)
            recibirá el manejador. Debe invocarse después de que el
            cliente exista.
        sala_jid: JID completo de la sala MUC del modo examen.
    """
    def _on_presencia_cierre(presencia) -> None:
        if presencia["type"] != "unavailable":
            return
        jid_origen = (
            str(presencia["from"]) if presencia["from"] else ""
        )
        # Solo se atiende la presencia que proviene de la sala del
        # examen. La comparación es insensible a mayúsculas (el
        # localpart de un JID no lo es, RFC 7622).
        if not jid_origen.lower().startswith(sala_jid.lower()):
            return
        if _es_fin_de_examen(_extraer_codigos_estado_muc(presencia)):
            codigos = _extraer_codigos_estado_muc(presencia)
            motivo = (
                "el supervisor ha expulsado al agente de la sala"
                if CODIGO_MUC_EXPULSADO in codigos
                else "el supervisor ha destruido la sala del examen"
            )
            logger.info(
                "Fin del examen: %s. El agente '%s' se detiene de "
                "forma ordenada.", motivo, agente.jid,
            )
            # La parada se programa como tarea aparte para no detener
            # el cliente XMPP desde dentro de su propio manejador de
            # eventos de presencia.
            asyncio.ensure_future(agente.stop())

    agente.client.add_event_handler("presence", _on_presencia_cierre)
    logger.debug(
        "Cierre ordenado del modo examen registrado para la sala %s",
        sala_jid,
    )


def _instalar_cierre_ordenado_examen(
    agente: Agent, sala_jid: str,
) -> None:
    """Programa el registro automático del cierre ordenado del examen.

    Es la función gemela de :func:`_instalar_aviso_examen`, pero para
    el manejador del FIN del examen. Envuelve
    ``_hook_plugin_after_connection`` para que el manejador de
    presencia se registre cuando el cliente XMPP del agente ya existe
    (después de ``start()``), sin que el alumno tenga que añadir
    ninguna línea a sus agentes.

    Args:
        agente: Instancia de agente recién creada y todavía sin
            arrancar (su cliente XMPP aún no existe).
        sala_jid: JID completo de la sala MUC del modo examen.
    """
    hook_original = agente._hook_plugin_after_connection

    async def _hook_con_cierre_ordenado() -> None:
        await hook_original()
        registrar_cierre_ordenado_examen(agente, sala_jid)

    agente._hook_plugin_after_connection = _hook_con_cierre_ordenado