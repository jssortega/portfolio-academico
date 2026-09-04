"""Arnés de pruebas — monta los agentes del alumno sobre la sala simulada.

El alumno entrega sus clases ``AgenteTablero`` y ``AgenteJugador``.
Para verificarlas **sin** un servidor XMPP, este arnés:

1. Crea el agente con la **factoría** ``utils.crear_agente`` —la
   misma cadena que usa ``main.py``—, de modo que cualquier fallo
   en el uso de la factoría aflora aquí.
2. Inyecta ``config_xmpp`` y ``config_parametros``, tal y como
   haría ``main.py``; los parámetros se completan con valores por
   defecto para que el ``setup()`` no falle si lee un parámetro
   sin valor alternativo.
3. Sustituye el cliente XMPP y el panel web por dobles de prueba,
   de modo que el ``setup()`` del agente se ejecute por completo
   sin abrir ninguna conexión de red ni ningún puerto.
4. Captura los comportamientos que el agente registra en su
   ``setup()`` —admitiendo la palabra clave ``template`` de SPADE—
   y conecta sus funciones ``send`` y ``receive`` a la
   :class:`~tests.simuladores.sala_simulada.SalaSimulada`.

El resultado es un :class:`AgenteMontado`: el agente **real** del
alumno, con sus comportamientos reales, intercambiando mensajes de
la ontología por la sala simulada. La prueba lo trata como una
caja negra y solo observa los mensajes que produce.
"""
import asyncio
import xml.etree.ElementTree as ET
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from spade.behaviour import FSMBehaviour, OneShotBehaviour

from utils import crear_agente

# Plazo de seguridad por defecto de un escenario de prueba. Si una
# corrutina no termina en este tiempo, se interrumpe para que la
# prueba falle con un mensaje claro en vez de quedar bloqueada.
LIMITE_ESCENARIO_SEGUNDOS = 90.0

# JID de la sala MUC que usan las pruebas de protocolo.
SALA_DE_PRUEBA = "examen@examen.localhost"

# ── Conducción de los comportamientos del agente bajo prueba ──────
# El arnés ejecuta los comportamientos reales del agente sobre la
# sala simulada. Como un protocolo correcto puede estar escrito con
# un FSMBehaviour, un CyclicBehaviour o un OneShotBehaviour, el
# arnés conduce cada tipo de la forma adecuada y se detiene cuando
# el intercambio de mensajes con los simuladores queda en reposo.
#
# Las cotas de reposo (PERIODO_QUIETUD y LIMITE_CONDUCCION) están
# dimensionadas con holgura para no obligar al alumno a usar plazos
# concretos en su agente. Un alumno con plazos «de producción»
# (decenas de segundos) podría tardar mucho en avanzar entre pasos
# del protocolo —p. ej. la ventana de gracia tras completar la
# inscripción, o el aborto por timeout—; estos techos permiten que
# ese alumno termine su escenario en una sola pasada del arnés sin
# imponer una interfaz de configuración por timeouts. Cuando el
# alumno responde rápido, la detección de reposo cierra el
# escenario en milisegundos y la prueba sigue siendo veloz.
INTERVALO_SONDEO_REPOSO = 0.05      # s entre comprobaciones de reposo
MIN_CONDUCCION_SEGUNDOS = 1.0       # tiempo mínimo de conducción
PERIODO_QUIETUD_SEGUNDOS = 1.5      # sin tráfico nuevo → escenario en reposo
LIMITE_CONDUCCION_SEGUNDOS = 45.0   # cota dura de conducción
PASO_CICLICO_SEGUNDOS = 0.02        # pausa entre iteraciones de un cíclico
MAX_PASOS_FSM = 600                 # cota de estados ejecutados de un FSM


def perfil_xmpp_de_prueba(
    dominio: str = "localhost",
    sala: str = SALA_DE_PRUEBA,
) -> dict[str, Any]:
    """Devuelve un perfil XMPP resuelto, válido para las pruebas.

    Reproduce la estructura del diccionario que ``main.py`` obtiene
    de :func:`config.configuracion.cargar_configuracion` e inyecta
    en cada agente como ``config_xmpp``.

    Args:
        dominio: Dominio XMPP con el que se construyen los JID de
            los agentes. Variarlo permite comprobar que el agente
            no fija ningún JID literal.
        sala: JID completo de la sala MUC del examen.

    Returns:
        Diccionario con el perfil XMPP resuelto.
    """
    return {
        "host": "localhost",
        "puerto": 5222,
        "dominio": dominio,
        "servicio_muc": "examen.localhost",
        "sala_tictactoe": "examen",
        "sala_muc_completa": sala,
        "password_defecto": "secret",
        "auto_register": True,
        "verify_security": False,
        "perfil": "local",
    }


class AgenteMontado:
    """Agente del alumno ya conectado a la sala simulada.

    Conduce los comportamientos de protocolo del agente —cualquiera
    que sea su tipo— sobre la :class:`SalaSimulada`:

    * un ``FSMBehaviour`` se conduce ejecutando su máquina de estados
      (cada ``_run`` ejecuta un estado y transita al siguiente);
    * un ``OneShotBehaviour`` se ejecuta una sola vez;
    * un ``CyclicBehaviour`` o ``PeriodicBehaviour`` se ejecuta en
      bucle hasta que el comportamiento se detiene o se cancela.

    Cada comportamiento se conduce una sola vez, aunque se invoquen
    :meth:`correr_unica` e :meth:`iniciar_ciclicos` sobre el mismo
    agente (caso de las pruebas de informe).

    Attributes:
        agente: La instancia real del agente del alumno.
        nick: Nick con el que el agente ocupa la sala.
    """

    def __init__(
        self, agente: Any, nick: str, sala: Any, capturados: list,
    ) -> None:
        self.agente = agente
        self.nick = nick
        self._sala = sala
        # Lista viva: el setup() y los propios comportamientos
        # siguen registrando comportamientos a través de la
        # ``add_behaviour`` interceptada, también durante el escenario.
        self._capturados = capturados
        self._tareas: dict[int, asyncio.Future] = {}

    def _enlazar(self, comportamiento: Any, plantilla: Any) -> None:
        """Conecta un comportamiento (y los estados de un FSM) a la sala."""
        conexion = self._sala.conectar(self.nick, plantilla)
        comportamiento.agent = self.agente
        comportamiento.send = conexion.send
        comportamiento.receive = conexion.receive
        # Los estados de un FSM tienen sus propias funciones
        # send/receive; se enchufan a la misma conexión que el FSM
        # para que el protocolo del estado activo viaje por la sala.
        if isinstance(comportamiento, FSMBehaviour):
            for estado in comportamiento._states.values():
                estado.agent = self.agente
                estado.send = conexion.send
                estado.receive = conexion.receive

    def _arrancar_pendientes(self) -> list[asyncio.Future]:
        """Enlaza y pone a correr los comportamientos aún no conducidos."""
        nuevas: list[asyncio.Future] = []
        for comportamiento, plantilla in list(self._capturados):
            clave = id(comportamiento)
            if clave not in self._tareas:
                self._enlazar(comportamiento, plantilla)
                tarea = asyncio.ensure_future(self._conducir(comportamiento))
                self._tareas[clave] = tarea
                nuevas.append(tarea)
        return nuevas

    def iniciar_ciclicos(self) -> list[asyncio.Future]:
        """Arranca en segundo plano los comportamientos del agente.

        Devuelve las tareas creadas, que la prueba debe cerrar con
        :func:`detener_tareas` al terminar el escenario.
        """
        return self._arrancar_pendientes()

    async def correr_unica(self) -> None:
        """Conduce los comportamientos del agente hasta el reposo.

        Pone a correr todos los comportamientos del agente —los ya
        registrados y los que se registren durante el escenario— y
        regresa cuando el intercambio de mensajes con los simuladores
        queda en reposo (ningún mensaje nuevo en la sala durante
        :data:`PERIODO_QUIETUD_SEGUNDOS`) o cuando se agota la cota
        :data:`LIMITE_CONDUCCION_SEGUNDOS`.
        """
        loop = asyncio.get_running_loop()
        inicio = loop.time()
        ultimo_cambio = inicio
        mensajes_previos = len(self._sala.historico)
        propias = self._arrancar_pendientes()
        try:
            en_reposo = False
            while not en_reposo:
                await asyncio.sleep(INTERVALO_SONDEO_REPOSO)
                propias.extend(self._arrancar_pendientes())
                ahora = loop.time()
                mensajes = len(self._sala.historico)
                if mensajes != mensajes_previos:
                    mensajes_previos = mensajes
                    ultimo_cambio = ahora
                transcurrido = ahora - inicio
                sin_trafico = (
                    (ahora - ultimo_cambio) >= PERIODO_QUIETUD_SEGUNDOS
                )
                if transcurrido >= LIMITE_CONDUCCION_SEGUNDOS:
                    en_reposo = True
                elif transcurrido >= MIN_CONDUCCION_SEGUNDOS and sin_trafico:
                    en_reposo = True
        finally:
            for tarea in propias:
                tarea.cancel()
            if propias:
                await asyncio.gather(*propias, return_exceptions=True)

    async def _conducir(self, comportamiento: Any) -> None:
        """Ejecuta un comportamiento según su tipo hasta que se cancela.

        Un ``FSMBehaviour`` se conduce estado a estado con su propio
        ``_run``; un ``OneShotBehaviour`` se ejecuta una vez; un
        ``CyclicBehaviour``/``PeriodicBehaviour`` se repite en bucle
        con una pausa breve entre iteraciones.
        """
        if isinstance(comportamiento, FSMBehaviour):
            pasos = 0
            while (
                comportamiento.current_state is not None
                and not comportamiento.is_killed()
                and pasos < MAX_PASOS_FSM
            ):
                await comportamiento._run()
                pasos += 1
        elif isinstance(comportamiento, OneShotBehaviour):
            await comportamiento.run()
        else:
            while not comportamiento.is_killed():
                await comportamiento.run()
                await asyncio.sleep(PASO_CICLICO_SEGUNDOS)


# Parámetros que ``main.py`` inyecta en cada agente a partir de
# ``agents.yaml``. El arnés los reproduce con valores neutros para
# que el ``setup()`` de un agente que lea un parámetro directamente
# —``config_parametros["puerto_web"]``, sin ``.get``— no falle con
# ``KeyError``. Los valores que pase la prueba tienen prioridad.
PARAMETROS_POR_DEFECTO: dict[str, Any] = {
    "nick_muc": "",
    "id_tablero": 1,
    "puerto_web": 0,
    "nivel_estrategia": 1,
    "max_partidas": 1,
}

# Valores del bloque 'sistema' que algunos agentes leen en su
# setup() (intervalos de sondeo, plazos de espera, etc.). Las claves
# que falten las cubre _ConfigTolerante con un valor neutro.
SISTEMA_POR_DEFECTO: dict[str, Any] = {
    "intervalo_busqueda_muc": 1,
    "timeout_inscripcion": 1,
    "timeout_turno": 0.3,
    "max_partidas_simultaneas": 1,
    "puerto_web_base": 0,
    "nivel_log": "WARNING",
}


class _ConfigTolerante(dict):
    """Diccionario de configuración tolerante a claves ausentes.

    Los ``config.yaml`` de los alumnos no siempre están al día con
    los últimos cambios de la infraestructura. Para que un desajuste
    de configuración no impida ejecutar las pruebas de protocolo,
    una clave ausente devuelve un valor neutro (``1``) en vez de
    elevar ``KeyError``. Las claves presentes se leen con su valor
    real. El acoplamiento correcto de la configuración lo verifican
    aparte ``test_configuracion_examen.py`` y ``test_factoria_jid.py``.
    """

    def __missing__(self, _clave: str) -> int:
        return 1


def _crear_cliente_doble() -> MagicMock:
    """Crea el doble de prueba del cliente XMPP.

    Para la mayoría de los agentes basta un ``MagicMock``: usan el
    cliente mediante llamadas de alto nivel (``register_plugin``,
    ``join_muc``) cuyo valor de retorno no se inspecciona. Pero
    algunos agentes construyen a mano la presencia de entrada a la
    sala MUC, con ``SubElement(stanza.xml, …)``. Para que su
    ``setup()`` también se ejecute, ``make_presence`` se configura
    de modo que devuelva una *stanza* cuyo atributo ``.xml`` es un
    ``Element`` real.

    El doble también almacena en el atributo ``_handlers`` los
    callbacks que el agente registra con
    ``client.add_event_handler(evento, callback)``: la
    :class:`SalaSimulada` los consulta al propagar presencias para
    que el alumno pueda descubrir tableros por el mismo mecanismo
    de slixmpp que usaría en producción.

    Returns:
        El cliente XMPP simulado.
    """
    cliente = MagicMock()

    def _stanza_de_prueba(*_args: Any, **_kwargs: Any) -> MagicMock:
        stanza = MagicMock()
        stanza.xml = ET.Element("presence")
        return stanza

    cliente.make_presence.side_effect = _stanza_de_prueba

    handlers: dict[str, list] = {}

    def _add_event_handler(evento: str, callback: Any) -> None:
        handlers.setdefault(evento, []).append(callback)

    cliente.add_event_handler.side_effect = _add_event_handler
    cliente._handlers = handlers
    return cliente


async def montar_agente(
    clase_agente: type,
    nombre: str,
    config_xmpp: dict[str, Any],
    config_parametros: dict[str, Any],
    sala: Any,
) -> AgenteMontado:
    """Crea un agente del alumno con la factoría y lo une a la sala.

    Args:
        clase_agente: Clase del agente del alumno (``AgenteTablero``
            o ``AgenteJugador``).
        nombre: Nombre del agente (parte local del JID).
        config_xmpp: Perfil XMPP resuelto (debe incluir
            ``sala_muc_completa``).
        config_parametros: Parámetros del agente; ``nick_muc`` fija
            el nick con el que ocupará la sala. Se completan con
            :data:`PARAMETROS_POR_DEFECTO`.
        sala: Instancia de :class:`SalaSimulada`.

    Returns:
        El :class:`AgenteMontado` listo para ejecutar sus
        comportamientos.
    """
    # 1. Crear el agente con la MISMA factoría que usa main.py.
    agente = crear_agente(clase_agente, nombre, config_xmpp)

    # 2. Inyectar la configuración, como hace main.py. Se usan
    #    diccionarios tolerantes: si el setup() del agente lee una
    #    clave que su config.yaml (a veces desactualizado) no trae,
    #    obtiene un valor neutro en vez de un KeyError, de modo que
    #    un desajuste de configuración no impida probar el protocolo.
    #    Se inyectan también config_sistema y config_llm, que main.py
    #    pone a disposición del agente.
    agente.config_xmpp = _ConfigTolerante(config_xmpp)
    agente.config_parametros = _ConfigTolerante(
        {**PARAMETROS_POR_DEFECTO, **config_parametros}
    )
    agente.config_sistema = _ConfigTolerante(SISTEMA_POR_DEFECTO)
    agente.config_llm = None

    # 3. Doble de prueba del cliente XMPP: permite que setup()
    #    ejecute el registro del plugin MUC y el join sin red.
    agente.client = _crear_cliente_doble()

    # 4. Doble del panel web: en SPADE, agente.web arranca un
    #    servidor aiohttp. Se sustituye por un mock para que el
    #    setup() de un agente con panel no abra ningún puerto.
    agente.web = MagicMock()
    agente.web.start = AsyncMock()

    # 5. Capturar los comportamientos que el agente registre. Se
    #    admite la palabra clave 'template' (la real de SPADE), la
    #    variante 'plantilla' y la forma posicional.
    capturados: list[tuple] = []

    def _capturar(
        comportamiento: Any,
        template: Any = None,
        plantilla: Any = None,
        **_resto: Any,
    ) -> None:
        capturados.append(
            (comportamiento, template if template is not None else plantilla)
        )

    agente.add_behaviour = _capturar

    # 6. Ejecutar el setup() real del agente. Se neutraliza además
    #    el arranque de servidores web por aiohttp directo (agentes
    #    que no usan agente.web, sino aiohttp a pelo), de modo que
    #    el setup() no abra puertos reales ni colisione entre pruebas.
    with patch("aiohttp.web.TCPSite.start", new=AsyncMock()), \
            patch("aiohttp.web.AppRunner.setup", new=AsyncMock()):
        await agente.setup()

    nick = agente.config_parametros.get("nick_muc") or nombre
    # Anunciar al agente como ocupante de la sala simulada. El
    # ``status`` inicial se deriva del prefijo del nick (convención
    # del proyecto): ``tablero_*`` se anuncia como ``"waiting"``
    # (disponible para inscripciones), cualquier otro entra con
    # ``status`` vacío. La sala propaga la presencia a los demás
    # ocupantes ya registrados, disparando los handlers que sus
    # clientes XMPP hayan suscrito a ``presence`` o
    # ``muc::<sala>::*``. Esto reproduce el descubrimiento por
    # presencias del servidor MUC real, sin obligar al alumno a
    # exponer ningún atributo de descubrimiento en su agente.
    status_inicial = (
        "waiting" if nick.startswith("tablero_") else ""
    )
    sala.registrar_cliente_agente(nick, agente.client, status_inicial)

    # El enlazado de los comportamientos con la sala y su ejecución
    # los gestiona AgenteMontado, que distingue FSMBehaviour,
    # OneShotBehaviour y cíclicos y conduce cada uno como corresponde.
    # Se le pasa la lista `capturados` viva: los comportamientos que
    # el agente registre durante el escenario (p. ej. el de jugar,
    # añadido al recibir game-start) también se conducirán.
    return AgenteMontado(agente, nick, sala, capturados)


async def ejecutar_escenario(
    *corrutinas: Any,
    limite: float = LIMITE_ESCENARIO_SEGUNDOS,
) -> None:
    """Ejecuta varias corrutinas en paralelo con un plazo de seguridad.

    Args:
        corrutinas: Corrutinas de los participantes del escenario
            (agentes del alumno y simuladores).
        limite: Segundos máximos antes de interrumpir el escenario.

    Raises:
        asyncio.TimeoutError: Si el escenario no termina a tiempo,
            lo que delata un protocolo que se ha quedado bloqueado.
    """
    await asyncio.wait_for(asyncio.gather(*corrutinas), timeout=limite)


def acelerar_tiempos(monkeypatch: Any) -> None:
    """Reduce los plazos de espera de simuladores y agentes.

    Los simuladores (Tablero y Jugador) usan, por defecto, plazos
    amplios (``TIMEOUT_SIMULADOR_SEGUNDOS = 5 s``) pensados para
    que un agente con tiempos de producción tenga tiempo de
    responder. En las pruebas todo viaja por la sala en memoria,
    así que esos plazos se acortan para que las pruebas terminen
    en menos de un segundo sin tocar el código de los agentes.

    El bloque ``sistema`` de la configuración del agente
    (``timeout_inscripcion``, ``intervalo_busqueda_muc``...) ya se
    inyecta con valores cortos en :data:`SISTEMA_POR_DEFECTO`; esta
    función afecta solo a los simuladores.

    Args:
        monkeypatch: Accesorio ``monkeypatch`` de pytest.
    """
    import tests.simuladores.jugador_simulado as mod_jugador_sim
    import tests.simuladores.tablero_simulado as mod_tablero_sim

    monkeypatch.setattr(
        mod_tablero_sim, "TIMEOUT_SIMULADOR_SEGUNDOS", 0.4,
    )
    monkeypatch.setattr(
        mod_jugador_sim, "TIMEOUT_SIMULADOR_SEGUNDOS", 0.4,
    )


def anunciar_tablero_descubierto(
    jugador: AgenteMontado, nick_tablero: str = "tablero_sim",
) -> None:
    """Anuncia en la sala simulada que un Tablero está disponible.

    Algunas pruebas montan al Jugador del alumno frente a un
    :class:`TableroSimulado` (un *oráculo* del Tablero, no un
    agente real); como ese tablero no se registra con
    :func:`montar_agente`, su presencia ``waiting`` no se ha
    propagado todavía en la sala. Esta función emite la stanza
    equivalente en el subsistema de presencias de la sala
    simulada para que el Jugador del alumno pueda descubrirlo por
    el mismo mecanismo de slixmpp que utilizaría en producción
    (``client.add_event_handler("muc::<sala>::got_online", ...)``
    u otros eventos MUC).

    No toca ningún atributo del agente del alumno: respeta la
    libertad de implementación del descubrimiento.

    Args:
        jugador: :class:`AgenteMontado` que envuelve al Jugador
            del alumno bajo prueba. Se usa para acceder a la
            sala.
        nick_tablero: Nick MUC con el que el Tablero contraparte
            ocupa la sala simulada. Por defecto, ``"tablero_sim"``
            (el nick del :class:`TableroSimulado`).
    """
    jugador._sala.propagar_presencia(
        nick_tablero, tipo="available", status="waiting",
    )


async def detener_tareas(tareas: list[asyncio.Future]) -> None:
    """Cancela y espera las tareas en segundo plano de un escenario.

    Se invoca al terminar una prueba para que los comportamientos
    cíclicos no queden pendientes entre pruebas.

    Args:
        tareas: Tareas devueltas por :meth:`AgenteMontado.iniciar_ciclicos`.
    """
    for tarea in tareas:
        tarea.cancel()
    if tareas:
        await asyncio.gather(*tareas, return_exceptions=True)
