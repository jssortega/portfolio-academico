"""
Tests de integración del Agente Supervisor.

Estos tests arrancan agentes SPADE reales (supervisor + agentes
simulados) contra el servidor XMPP configurado en
``config/config.yaml`` para verificar el funcionamiento completo
del sistema en escenarios de laboratorio.

El servidor XMPP utilizado depende del ``perfil_activo`` de
``config.yaml``:

- **local**: Prosody en Docker (localhost:5222).
- **servidor**: Prosody de la asignatura (sinbad2.ujaen.es:8022).

Se puede forzar un perfil distinto al activo mediante la variable
de entorno ``XMPP_PERFIL``::

    # Usar el perfil que esté activo en config.yaml
    pytest tests/test_integracion_supervisor.py -v

    # Forzar perfil local (Docker)
    XMPP_PERFIL=local pytest tests/test_integracion_supervisor.py -v

    # Forzar perfil servidor (sinbad2.ujaen.es)
    XMPP_PERFIL=servidor pytest tests/test_integracion_supervisor.py -v

Si el servidor no está disponible, los tests se omiten
automáticamente.

Escenarios cubiertos:
- Partida con victoria, empate y abortada.
- Tablero que no responde (timeout).
- Respuesta con JSON inválido (ontología incorrecta).
- Entrada y salida de agentes en la sala MUC.
- Múltiples salas simultáneas.
- Protocolo de dos pasos (AGREE + INFORM).
- Tablero que rechaza la solicitud (REFUSE).
"""

import asyncio
import logging
import os
import socket
import time

import aiohttp
import pytest

from agentes.agente_supervisor import AgenteSupervisor
from behaviours.supervisor_behaviours import TIMEOUT_RESPUESTA
from config.configuracion import cargar_configuracion
from tests.simuladores.jugador_simulado import JugadorSimulado
from tests.simuladores.tablero_simulado import TableroSimulado
from utils import crear_agente, arrancar_agente

# ── Configuración del logging para los tests ─────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("test_integracion")


# ═══════════════════════════════════════════════════════════════
#  Carga de configuración XMPP desde config.yaml
# ═══════════════════════════════════════════════════════════════
# Se lee el perfil activo de config.yaml, salvo que la variable
# de entorno XMPP_PERFIL fuerce un perfil concreto. Esto permite
# ejecutar los tests tanto contra el servidor Docker local como
# contra el servidor de la asignatura (sinbad2.ujaen.es).

def _cargar_config_xmpp() -> dict:
    """Lee la configuración XMPP del perfil activo (o del perfil
    forzado por la variable de entorno ``XMPP_PERFIL``).

    Returns:
        Diccionario con la configuración del perfil XMPP resuelto.
    """
    config = cargar_configuracion()
    config_xmpp = config["xmpp"]

    # Si el usuario fuerza un perfil vía variable de entorno,
    # releer el fichero con ese perfil
    perfil_forzado = os.environ.get("XMPP_PERFIL", "")
    if perfil_forzado and perfil_forzado != config_xmpp.get("perfil"):
        import yaml
        with open("config/config.yaml", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        perfiles = raw.get("xmpp", {}).get("perfiles", {})
        if perfil_forzado in perfiles:
            config_xmpp = perfiles[perfil_forzado].copy()
            config_xmpp["perfil"] = perfil_forzado
            logger.info(
                "Perfil XMPP forzado por XMPP_PERFIL: %s",
                perfil_forzado,
            )

    return config_xmpp


CONFIG_XMPP = _cargar_config_xmpp()

# Información del perfil para los mensajes de log y skip
_PERFIL_NOMBRE = CONFIG_XMPP.get("perfil", "desconocido")
_XMPP_HOST = CONFIG_XMPP.get("host", "localhost")
_XMPP_PUERTO = CONFIG_XMPP.get("puerto", 5222)
_SERVICIO_MUC = CONFIG_XMPP.get(
    "servicio_muc", f"conference.{_XMPP_HOST}",
)

logger.info(
    "Tests de integración — perfil XMPP: '%s' (%s:%d)",
    _PERFIL_NOMBRE, _XMPP_HOST, _XMPP_PUERTO,
)


# ═══════════════════════════════════════════════════════════════
#  Verificación de disponibilidad del servidor XMPP
# ═══════════════════════════════════════════════════════════════

def _servidor_xmpp_disponible() -> bool:
    """Comprueba si el servidor XMPP del perfil activo acepta
    conexiones TCP en el host y puerto configurados."""
    disponible = False
    try:
        conexion = socket.create_connection(
            (_XMPP_HOST, _XMPP_PUERTO), timeout=5,
        )
        conexion.close()
        disponible = True
    except (ConnectionRefusedError, OSError):
        pass
    return disponible


pytestmark = pytest.mark.skipif(
    not _servidor_xmpp_disponible(),
    reason=(
        f"Servidor XMPP no disponible en "
        f"{_XMPP_HOST}:{_XMPP_PUERTO} "
        f"(perfil: {_PERFIL_NOMBRE})"
    ),
)


# ═══════════════════════════════════════════════════════════════
#  Constantes de temporización
# ═══════════════════════════════════════════════════════════════
# Tiempos más holgados para el perfil "servidor" (red UJA/VPN)
# que para Docker local, donde la latencia es mínima.

_ES_SERVIDOR_REMOTO = _PERFIL_NOMBRE == "servidor"

# Puerto del dashboard web para tests (distinto al de producción)
PUERTO_WEB_TEST = 10099

# Ruta del fichero SQLite para persistir los resultados de los tests
# de integración. Permite revisar después los informes y eventos con:
#   python supervisor_main.py --modo consulta --db data/integracion.db
RUTA_DB_INTEGRACION = "data/integracion.db"

# Tiempo de espera para que las presencias se propaguen (segundos)
PAUSA_PRESENCIA = 4 if _ES_SERVIDOR_REMOTO else 2

# Tiempo de espera para que el supervisor procese un informe
PAUSA_INFORME = 5 if _ES_SERVIDOR_REMOTO else 3

# Timeout de pytest para tests normales y para tests de timeout
TIMEOUT_TEST = 45 if _ES_SERVIDOR_REMOTO else 30
TIMEOUT_TEST_LARGO = 60 if _ES_SERVIDOR_REMOTO else 45


# ═══════════════════════════════════════════════════════════════
#  Utilidad: esperar una condición con timeout
# ═══════════════════════════════════════════════════════════════

async def esperar_condicion(condicion_fn, timeout=15, intervalo=0.5):
    """Espera activamente hasta que ``condicion_fn()`` devuelva
    ``True``, o lanza ``AssertionError`` si se agota el tiempo.

    Args:
        condicion_fn: Función sin argumentos que devuelve bool.
        timeout: Segundos máximos de espera.
        intervalo: Segundos entre comprobaciones.

    Raises:
        AssertionError: Si la condición no se cumple a tiempo.
    """
    inicio = time.time()
    cumplida = False
    while not cumplida and (time.time() - inicio) < timeout:
        if condicion_fn():
            cumplida = True
        else:
            await asyncio.sleep(intervalo)

    if not cumplida:
        raise AssertionError(
            f"Condición no cumplida tras {timeout} segundos",
        )


async def consultar_api_state(puerto_web: int) -> dict:
    """Consulta el endpoint /supervisor/api/state y devuelve
    el JSON de respuesta.

    Args:
        puerto_web: Puerto del dashboard web del supervisor.

    Returns:
        Diccionario con la respuesta JSON (claves: salas, timestamp).
    """
    url = f"http://localhost:{puerto_web}/supervisor/api/state"
    resultado = {}
    async with aiohttp.ClientSession() as sesion:
        async with sesion.get(url) as resp:
            if resp.status == 200:
                resultado = await resp.json()
    return resultado


# ═══════════════════════════════════════════════════════════════
#  Factoría de agentes para tests
# ═══════════════════════════════════════════════════════════════

def _nombre_unico(prefijo: str) -> str:
    """Genera un nombre de agente único basado en timestamp para
    evitar colisiones entre tests."""
    marca = int(time.time() * 1000) % 100000
    nombre = f"{prefijo}_{marca}"
    return nombre


async def _crear_supervisor(salas, puerto_web: int):
    """Crea y arranca un AgenteSupervisor configurado con
    descubrimiento manual para las salas indicadas.

    Args:
        salas: Nombre de una sala (str) o lista de nombres.
        puerto_web: Puerto para el dashboard web.

    Returns:
        Instancia del supervisor ya arrancada.
    """
    # Aceptar tanto un string como una lista
    lista_salas = [salas] if isinstance(salas, str) else list(salas)

    nombre = _nombre_unico("supervisor")
    supervisor = crear_agente(
        AgenteSupervisor, nombre, CONFIG_XMPP,
    )
    supervisor.config_xmpp = CONFIG_XMPP
    supervisor.config_parametros = {
        "intervalo_consulta": 5,
        "puerto_web": puerto_web,
        "ruta_db": RUTA_DB_INTEGRACION,
        "descubrimiento_salas": "manual",
        "salas_muc": lista_salas,
    }
    supervisor.config_llm = None
    await arrancar_agente(supervisor, CONFIG_XMPP)
    # Esperar a que se una a las salas MUC
    await asyncio.sleep(PAUSA_PRESENCIA)
    return supervisor


async def _crear_tablero(
    nick: str, sala_jid: str, modo: str = "victoria",
):
    """Crea y arranca un TableroSimulado.

    Args:
        nick: Apodo MUC del tablero.
        sala_jid: JID completo de la sala MUC.
        modo: Modo de respuesta a game-report.

    Returns:
        Instancia del tablero ya arrancada.
    """
    nombre = _nombre_unico(nick)
    tablero = crear_agente(
        TableroSimulado, nombre, CONFIG_XMPP,
    )
    tablero.nick = nick
    tablero.sala_jid = sala_jid
    tablero.modo_respuesta = modo
    await arrancar_agente(tablero, CONFIG_XMPP)
    await asyncio.sleep(PAUSA_PRESENCIA)
    return tablero


async def _crear_jugador(
    nick: str, sala_jid: str, nivel_estrategia: int = 1,
):
    """Crea y arranca un JugadorSimulado.

    Args:
        nick: Apodo MUC del jugador.
        sala_jid: JID completo de la sala MUC.
        nivel_estrategia: Nivel de estrategia simulado
            (1=Posicional, 2=Reglas, 3=Minimax, 4=LLM).

    Returns:
        Instancia del jugador ya arrancada.
    """
    nombre = _nombre_unico(nick)
    jugador = crear_agente(
        JugadorSimulado, nombre, CONFIG_XMPP,
    )
    jugador.nick = nick
    jugador.sala_jid = sala_jid
    jugador.nivel_estrategia = nivel_estrategia
    await arrancar_agente(jugador, CONFIG_XMPP)
    await asyncio.sleep(PAUSA_PRESENCIA)
    return jugador


async def _detener_agentes(*agentes):
    """Detiene una lista de agentes de forma segura, ignorando
    errores si alguno ya se desconectó.

    Si alguno de los agentes es un AgenteSupervisor, finaliza su
    persistencia antes de detenerlo para que la ejecución quede
    correctamente cerrada en la base de datos SQLite.
    """
    for agente in agentes:
        try:
            if hasattr(agente, "detener_persistencia"):
                await agente.detener_persistencia()
            await agente.stop()
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════
#  Fixture: sala de test con nombre único
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def sala_test():
    """Genera un nombre de sala MUC único para cada test, usando
    el servicio MUC del perfil XMPP activo."""
    marca = int(time.time() * 1000) % 100000
    sala_id = f"test_sala_{marca}"
    sala_jid = f"{sala_id}@{_SERVICIO_MUC}"
    resultado = {"id": sala_id, "jid": sala_jid}
    return resultado


# ═══════════════════════════════════════════════════════════════
#  Tests de integración
# ═══════════════════════════════════════════════════════════════

class TestPartidaNormal:
    """Verifica que el supervisor recibe correctamente los informes
    de partidas que terminan con normalidad."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_partida_victoria(self, sala_test):
        """Un tablero que finaliza con victoria debe generar un
        informe con resultado 'win' en el supervisor."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(sala_id, PUERTO_WEB_TEST)
        tablero = await _crear_tablero(
            "tablero_mesa1", sala_jid, "victoria",
        )

        try:
            # Simular ciclo de vida: waiting → playing → finished
            await tablero.cambiar_estado_muc("playing")
            await asyncio.sleep(1)
            await tablero.cambiar_estado_muc("finished")

            # Esperar a que el supervisor reciba el informe
            await esperar_condicion(
                lambda: len(
                    supervisor.informes_por_sala.get(sala_id, {}),
                ) > 0,
            )

            informes = supervisor.informes_por_sala[sala_id]
            assert len(informes) == 1

            informe = list(informes.values())[0]
            assert informe["result"] == "win"
            assert informe["winner"] == "X"
        finally:
            await _detener_agentes(tablero, supervisor)

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_partida_empate(self, sala_test):
        """Un tablero que finaliza en empate debe generar un
        informe con resultado 'draw'."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(sala_id, PUERTO_WEB_TEST)
        tablero = await _crear_tablero(
            "tablero_mesa1", sala_jid, "empate",
        )

        try:
            await tablero.cambiar_estado_muc("finished")

            await esperar_condicion(
                lambda: len(
                    supervisor.informes_por_sala.get(sala_id, {}),
                ) > 0,
            )

            informe = list(
                supervisor.informes_por_sala[sala_id].values(),
            )[0]
            assert informe["result"] == "draw"
            assert informe["winner"] is None
        finally:
            await _detener_agentes(tablero, supervisor)

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_partida_abortada(self, sala_test):
        """Un tablero que envía un informe de partida abortada debe
        registrarlo con resultado 'aborted' y el motivo."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(sala_id, PUERTO_WEB_TEST)
        tablero = await _crear_tablero(
            "tablero_mesa1", sala_jid, "abortada",
        )

        try:
            await tablero.cambiar_estado_muc("finished")

            await esperar_condicion(
                lambda: len(
                    supervisor.informes_por_sala.get(sala_id, {}),
                ) > 0,
            )

            informe = list(
                supervisor.informes_por_sala[sala_id].values(),
            )[0]
            assert informe["result"] == "aborted"
            assert informe["reason"] == "both-timeout"
        finally:
            await _detener_agentes(tablero, supervisor)


class TestProtocoloDePasos:
    """Verifica el protocolo FIPA-Request con respuesta en dos
    pasos (AGREE seguido de INFORM)."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_agree_luego_inform(self, sala_test):
        """Un tablero que responde primero con AGREE y luego con
        INFORM debe generar un informe válido."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(sala_id, PUERTO_WEB_TEST)
        tablero = await _crear_tablero(
            "tablero_mesa1", sala_jid, "agree_luego_inform",
        )

        try:
            await tablero.cambiar_estado_muc("finished")

            await esperar_condicion(
                lambda: len(
                    supervisor.informes_por_sala.get(sala_id, {}),
                ) > 0,
            )

            informes = supervisor.informes_por_sala[sala_id]
            assert len(informes) == 1
        finally:
            await _detener_agentes(tablero, supervisor)


class TestErrores:
    """Verifica que el supervisor gestiona correctamente los
    escenarios de error sin interrumpir su ejecución."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST_LARGO)
    async def test_timeout_sin_respuesta(self, sala_test):
        """Si el tablero no responde al REQUEST, el supervisor
        debe registrar un evento de timeout en el log."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(sala_id, PUERTO_WEB_TEST)
        tablero = await _crear_tablero(
            "tablero_mesa1", sala_jid, "timeout",
        )

        try:
            await tablero.cambiar_estado_muc("finished")

            # Esperar más que el TIMEOUT_RESPUESTA del FSM
            await esperar_condicion(
                lambda: any(
                    e["tipo"] == "timeout"
                    for e in supervisor.log_por_sala.get(
                        sala_id, [],
                    )
                ),
                timeout=TIMEOUT_RESPUESTA + 10,
            )

            # No debe haber informes almacenados
            informes = supervisor.informes_por_sala.get(
                sala_id, {},
            )
            assert len(informes) == 0
        finally:
            await _detener_agentes(tablero, supervisor)

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_json_invalido(self, sala_test):
        """Si el tablero envía un INFORM con JSON inválido, el
        supervisor no debe almacenar informe ni lanzar excepción."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(sala_id, PUERTO_WEB_TEST)
        tablero = await _crear_tablero(
            "tablero_mesa1", sala_jid, "json_invalido",
        )

        try:
            await tablero.cambiar_estado_muc("finished")

            # Esperar tiempo suficiente para que el FSM procese
            await asyncio.sleep(PAUSA_INFORME + 2)

            informes = supervisor.informes_por_sala.get(
                sala_id, {},
            )
            assert len(informes) == 0
        finally:
            await _detener_agentes(tablero, supervisor)

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_esquema_invalido(self, sala_test):
        """Si el tablero envía un JSON válido pero con esquema
        incorrecto (campos obligatorios ausentes), el informe no
        debe almacenarse."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(sala_id, PUERTO_WEB_TEST)
        tablero = await _crear_tablero(
            "tablero_mesa1", sala_jid, "esquema_invalido",
        )

        try:
            await tablero.cambiar_estado_muc("finished")
            await asyncio.sleep(PAUSA_INFORME + 2)

            informes = supervisor.informes_por_sala.get(
                sala_id, {},
            )
            assert len(informes) == 0
        finally:
            await _detener_agentes(tablero, supervisor)

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_refuse(self, sala_test):
        """Si el tablero rechaza la solicitud con REFUSE, no debe
        almacenarse informe y el FSM debe terminar sin error."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(sala_id, PUERTO_WEB_TEST)
        tablero = await _crear_tablero(
            "tablero_mesa1", sala_jid, "refuse",
        )

        try:
            await tablero.cambiar_estado_muc("finished")
            await asyncio.sleep(PAUSA_INFORME + 2)

            informes = supervisor.informes_por_sala.get(
                sala_id, {},
            )
            assert len(informes) == 0
        finally:
            await _detener_agentes(tablero, supervisor)


class TestPresenciaMUC:
    """Verifica la detección de entradas, salidas y cambios de
    estado de los agentes en la sala MUC."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_entrada_de_agentes(self, sala_test):
        """Cuando un jugador y un tablero se unen a la sala, el
        supervisor debe detectarlos como ocupantes."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(sala_id, PUERTO_WEB_TEST)
        tablero = await _crear_tablero(
            "tablero_mesa1", sala_jid, "timeout",
        )
        jugador = await _crear_jugador("jugador_ana", sala_jid)

        try:
            await esperar_condicion(
                lambda: len(
                    supervisor.ocupantes_por_sala.get(sala_id, []),
                ) >= 2,
            )

            ocupantes = supervisor.ocupantes_por_sala[sala_id]
            nicks = [o["nick"] for o in ocupantes]
            assert "tablero_mesa1" in nicks
            assert "jugador_ana" in nicks

            # Debe haber eventos de entrada en el log
            tipos_log = [
                e["tipo"]
                for e in supervisor.log_por_sala.get(sala_id, [])
            ]
            assert "entrada" in tipos_log
        finally:
            await _detener_agentes(jugador, tablero, supervisor)

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_salida_de_agente(self, sala_test):
        """Cuando un jugador abandona la sala, el supervisor debe
        detectar su salida y registrar el evento."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(sala_id, PUERTO_WEB_TEST)
        jugador = await _crear_jugador("jugador_luis", sala_jid)

        try:
            # Esperar a que el supervisor lo detecte
            await esperar_condicion(
                lambda: len(
                    supervisor.ocupantes_por_sala.get(sala_id, []),
                ) >= 1,
            )

            # El jugador abandona la sala
            await jugador.abandonar_sala()
            await asyncio.sleep(PAUSA_PRESENCIA)

            # El supervisor debe haber registrado la salida
            tipos_log = [
                e["tipo"]
                for e in supervisor.log_por_sala.get(sala_id, [])
            ]
            assert "salida" in tipos_log
        finally:
            await _detener_agentes(jugador, supervisor)

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_cambio_estado_tablero_en_log(self, sala_test):
        """Los cambios de estado del tablero (waiting → playing →
        finished) deben registrarse en el log del supervisor."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(sala_id, PUERTO_WEB_TEST)
        tablero = await _crear_tablero(
            "tablero_mesa1", sala_jid, "victoria",
        )

        try:
            await tablero.cambiar_estado_muc("playing")
            await asyncio.sleep(1)
            await tablero.cambiar_estado_muc("finished")

            # Esperar a que se procese el informe
            await esperar_condicion(
                lambda: len(
                    supervisor.informes_por_sala.get(sala_id, {}),
                ) > 0,
            )

            # Buscar eventos de cambio de estado en el log
            eventos = supervisor.log_por_sala.get(sala_id, [])
            detalles = " ".join(e["detalle"] for e in eventos)
            assert "waiting" in detalles
            assert "playing" in detalles
        finally:
            await _detener_agentes(tablero, supervisor)


class TestMultiplesSalas:
    """Verifica el funcionamiento simultáneo con varias salas."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_dos_salas_independientes(self):
        """El supervisor debe gestionar dos salas de forma
        independiente, cada una con sus propios ocupantes e
        informes."""
        marca = int(time.time() * 1000) % 100000
        sala_a = f"test_sala_a_{marca}"
        sala_b = f"test_sala_b_{marca}"
        jid_a = f"{sala_a}@{_SERVICIO_MUC}"
        jid_b = f"{sala_b}@{_SERVICIO_MUC}"

        # Crear supervisor con dos salas
        nombre_sup = _nombre_unico("supervisor")
        supervisor = crear_agente(
            AgenteSupervisor, nombre_sup, CONFIG_XMPP,
        )
        supervisor.config_xmpp = CONFIG_XMPP
        supervisor.config_parametros = {
            "intervalo_consulta": 5,
            "puerto_web": PUERTO_WEB_TEST,
            "ruta_db": RUTA_DB_INTEGRACION,
            "descubrimiento_salas": "manual",
            "salas_muc": [sala_a, sala_b],
        }
        supervisor.config_llm = None
        await arrancar_agente(supervisor, CONFIG_XMPP)
        await asyncio.sleep(PAUSA_PRESENCIA)

        tablero_a = await _crear_tablero(
            "tablero_mesa1", jid_a, "victoria",
        )
        tablero_b = await _crear_tablero(
            "tablero_mesa2", jid_b, "empate",
        )

        try:
            # Ambos tableros pasan a finished
            await tablero_a.cambiar_estado_muc("finished")
            await tablero_b.cambiar_estado_muc("finished")

            # Esperar informes en ambas salas
            await esperar_condicion(
                lambda: (
                    len(supervisor.informes_por_sala.get(
                        sala_a, {},
                    )) > 0
                    and len(supervisor.informes_por_sala.get(
                        sala_b, {},
                    )) > 0
                ),
            )

            informe_a = list(
                supervisor.informes_por_sala[sala_a].values(),
            )[0]
            informe_b = list(
                supervisor.informes_por_sala[sala_b].values(),
            )[0]

            # Cada sala tiene su propio resultado
            assert informe_a["result"] == "win"
            assert informe_b["result"] == "draw"
        finally:
            await _detener_agentes(
                tablero_a, tablero_b, supervisor,
            )


class TestAPIWeb:
    """Verifica que el dashboard web expone correctamente el
    estado del supervisor a través de la API HTTP."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_api_state_con_informe(self, sala_test):
        """El endpoint /supervisor/api/state debe devolver los
        informes recibidos en formato JSON."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(
            sala_id, PUERTO_WEB_TEST,
        )
        tablero = await _crear_tablero(
            "tablero_mesa1", sala_jid, "victoria",
        )

        try:
            await tablero.cambiar_estado_muc("finished")

            await esperar_condicion(
                lambda: len(
                    supervisor.informes_por_sala.get(sala_id, {}),
                ) > 0,
            )

            # Consultar la API HTTP del dashboard
            url = (
                f"http://localhost:{PUERTO_WEB_TEST}"
                "/supervisor/api/state"
            )
            async with aiohttp.ClientSession() as sesion:
                async with sesion.get(url) as resp:
                    assert resp.status == 200
                    datos = await resp.json()

            # Buscar la sala de test en la respuesta
            sala_encontrada = None
            for sala in datos["salas"]:
                if sala["id"] == sala_id:
                    sala_encontrada = sala

            assert sala_encontrada is not None
            assert len(sala_encontrada["informes"]) == 1
            assert (
                sala_encontrada["informes"][0]["resultado"]
                == "victoria"
            )
        finally:
            await _detener_agentes(tablero, supervisor)

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_api_state_con_ocupantes(self, sala_test):
        """El endpoint /supervisor/api/state debe reflejar los
        ocupantes detectados en la sala MUC."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(
            sala_id, PUERTO_WEB_TEST,
        )
        jugador = await _crear_jugador("jugador_test", sala_jid)

        try:
            await esperar_condicion(
                lambda: len(
                    supervisor.ocupantes_por_sala.get(sala_id, []),
                ) >= 1,
            )

            url = (
                f"http://localhost:{PUERTO_WEB_TEST}"
                "/supervisor/api/state"
            )
            async with aiohttp.ClientSession() as sesion:
                async with sesion.get(url) as resp:
                    datos = await resp.json()

            sala_encontrada = None
            for sala in datos["salas"]:
                if sala["id"] == sala_id:
                    sala_encontrada = sala

            assert sala_encontrada is not None
            nicks = [
                o["nick"] for o in sala_encontrada["ocupantes"]
            ]
            assert "jugador_test" in nicks
        finally:
            await _detener_agentes(jugador, supervisor)


class TestVisibilidadProgresivaSalas:
    """Verifica que la API del dashboard solo devuelve salas con
    actividad y que estas aparecen progresivamente conforme los
    alumnos se incorporan a la sesión.

    Simula un escenario de laboratorio con 3 salas donde los
    alumnos se van incorporando en momentos distintos. Las salas
    sin actividad no deben aparecer en la respuesta de la API.
    Una sala que tuvo actividad debe seguir visible aunque los
    agentes se desconecten (porque conserva eventos en el log).
    """

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_sala_sin_agentes_no_tiene_ocupantes(self):
        """Una sala donde nadie se ha conectado debe tener la
        lista de ocupantes vacía en la API."""
        marca = int(time.time() * 1000) % 100000
        sala_vacia = f"test_vacia_{marca}"

        supervisor = await _crear_supervisor(
            sala_vacia, PUERTO_WEB_TEST,
        )

        try:
            datos = await consultar_api_state(PUERTO_WEB_TEST)
            sala_encontrada = None
            for sala in datos["salas"]:
                if sala["id"] == sala_vacia:
                    sala_encontrada = sala

            assert sala_encontrada is not None
            assert len(sala_encontrada["ocupantes"]) == 0
        finally:
            await _detener_agentes(supervisor)

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_salas_aparecen_conforme_se_unen_agentes(self):
        """Los alumnos se incorporan progresivamente. Cada sala
        debe aparecer con ocupantes solo cuando su primer agente
        se une, y las demás deben permanecer sin ocupantes
        hasta que les lleguen los suyos."""
        marca = int(time.time() * 1000) % 100000
        sala_a = f"test_prog_a_{marca}"
        sala_b = f"test_prog_b_{marca}"
        sala_c = f"test_prog_c_{marca}"
        jid_a = f"{sala_a}@{_SERVICIO_MUC}"
        jid_b = f"{sala_b}@{_SERVICIO_MUC}"
        jid_c = f"{sala_c}@{_SERVICIO_MUC}"

        supervisor = await _crear_supervisor(
            [sala_a, sala_b, sala_c], PUERTO_WEB_TEST,
        )

        try:
            # ── Fase 1: nadie conectado ──────────────────────
            datos = await consultar_api_state(PUERTO_WEB_TEST)
            ids_con_ocupantes = [
                s["id"] for s in datos["salas"]
                if s["ocupantes"]
            ]
            assert len(ids_con_ocupantes) == 0

            # ── Fase 2: alumno se une a sala_a ───────────────
            jugador_a = await _crear_jugador(
                "jugador_alumno_a", jid_a,
            )
            await esperar_condicion(
                lambda: len(
                    supervisor.ocupantes_por_sala.get(sala_a, []),
                ) >= 1,
            )

            datos = await consultar_api_state(PUERTO_WEB_TEST)
            ids_con_ocupantes = [
                s["id"] for s in datos["salas"]
                if s["ocupantes"]
            ]
            assert sala_a in ids_con_ocupantes
            assert sala_b not in ids_con_ocupantes
            assert sala_c not in ids_con_ocupantes

            # ── Fase 3: alumno se une a sala_c (sala_b sigue
            #    vacía, sala_a ya tiene agente) ───────────────
            jugador_c = await _crear_jugador(
                "jugador_alumno_c", jid_c,
            )
            await esperar_condicion(
                lambda: len(
                    supervisor.ocupantes_por_sala.get(sala_c, []),
                ) >= 1,
            )

            datos = await consultar_api_state(PUERTO_WEB_TEST)
            ids_con_ocupantes = [
                s["id"] for s in datos["salas"]
                if s["ocupantes"]
            ]
            assert sala_a in ids_con_ocupantes
            assert sala_c in ids_con_ocupantes
            assert sala_b not in ids_con_ocupantes

            # ── Fase 4: alumno se une a sala_b (las 3 activas)
            jugador_b = await _crear_jugador(
                "jugador_alumno_b", jid_b,
            )
            await esperar_condicion(
                lambda: len(
                    supervisor.ocupantes_por_sala.get(sala_b, []),
                ) >= 1,
            )

            datos = await consultar_api_state(PUERTO_WEB_TEST)
            ids_con_ocupantes = [
                s["id"] for s in datos["salas"]
                if s["ocupantes"]
            ]
            assert sala_a in ids_con_ocupantes
            assert sala_b in ids_con_ocupantes
            assert sala_c in ids_con_ocupantes
        finally:
            await _detener_agentes(
                jugador_a, jugador_b, jugador_c, supervisor,
            )

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_sala_persiste_tras_desconexion_agentes(self):
        """Cuando todos los agentes de una sala se desconectan, la
        sala debe seguir visible en la API porque conserva eventos
        de entrada y salida en su log."""
        marca = int(time.time() * 1000) % 100000
        sala_id = f"test_persist_{marca}"
        sala_jid = f"{sala_id}@{_SERVICIO_MUC}"

        supervisor = await _crear_supervisor(
            sala_id, PUERTO_WEB_TEST,
        )
        jugador = await _crear_jugador("jugador_efimero", sala_jid)

        try:
            # Esperar a que el supervisor detecte la entrada
            await esperar_condicion(
                lambda: len(
                    supervisor.ocupantes_por_sala.get(sala_id, []),
                ) >= 1,
            )

            # El jugador abandona la sala
            await jugador.abandonar_sala()
            await asyncio.sleep(PAUSA_PRESENCIA)

            # La sala debe tener 0 ocupantes pero seguir visible
            # en la API porque tiene eventos en el log
            datos = await consultar_api_state(PUERTO_WEB_TEST)
            sala_encontrada = None
            for sala in datos["salas"]:
                if sala["id"] == sala_id:
                    sala_encontrada = sala

            assert sala_encontrada is not None
            assert len(sala_encontrada["ocupantes"]) == 0
            assert len(sala_encontrada["log"]) >= 2  # entrada + salida
        finally:
            await _detener_agentes(jugador, supervisor)


class TestEscenariosLLM:
    """Verifica que el supervisor gestiona correctamente los
    escenarios donde algún jugador usa estrategia LLM (nivel 4).

    Los modelos LLM pueden causar dos tipos de fallo:
    - **Timeout**: el modelo no genera una respuesta a tiempo y
      el tablero aborta la partida.
    - **Movimiento inválido**: el modelo genera una respuesta que
      no corresponde a un movimiento válido y el tablero aborta.

    En ambos casos, el tablero envía un informe con
    ``result="aborted"`` y el motivo correspondiente. El supervisor
    debe almacenar el informe y reflejar el motivo en el dashboard.
    """

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_abortada_por_timeout_llm(self, sala_test):
        """Cuando un jugador LLM no responde a tiempo, el tablero
        aborta con reason='timeout' y el rival gana. El supervisor
        debe almacenar el informe con el motivo correcto."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(sala_id, PUERTO_WEB_TEST)
        tablero = await _crear_tablero(
            "tablero_mesa1", sala_jid, "abortada_timeout_llm",
        )
        # Jugador normal y jugador con estrategia LLM
        jugador_normal = await _crear_jugador(
            "jugador_ana", sala_jid, nivel_estrategia=2,
        )
        jugador_ia = await _crear_jugador(
            "jugador_ia", sala_jid, nivel_estrategia=4,
        )

        try:
            await tablero.cambiar_estado_muc("playing")
            await asyncio.sleep(1)
            await tablero.cambiar_estado_muc("finished")

            await esperar_condicion(
                lambda: len(
                    supervisor.informes_por_sala.get(sala_id, {}),
                ) > 0,
            )

            informe = list(
                supervisor.informes_por_sala[sala_id].values(),
            )[0]
            assert informe["result"] == "aborted"
            assert informe["reason"] == "timeout"
            # El rival del jugador LLM gana
            assert informe["winner"] == "X"
        finally:
            await _detener_agentes(
                jugador_ia, jugador_normal, tablero, supervisor,
            )

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_abortada_por_movimiento_invalido_llm(self, sala_test):
        """Cuando un jugador LLM genera un movimiento inválido, el
        tablero aborta con reason='invalid'. El supervisor debe
        almacenar el informe con el motivo."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(sala_id, PUERTO_WEB_TEST)
        tablero = await _crear_tablero(
            "tablero_mesa1", sala_jid, "abortada_movimiento_invalido",
        )
        jugador_ia = await _crear_jugador(
            "jugador_ia", sala_jid, nivel_estrategia=4,
        )

        try:
            await tablero.cambiar_estado_muc("finished")

            await esperar_condicion(
                lambda: len(
                    supervisor.informes_por_sala.get(sala_id, {}),
                ) > 0,
            )

            informe = list(
                supervisor.informes_por_sala[sala_id].values(),
            )[0]
            assert informe["result"] == "aborted"
            assert informe["reason"] == "invalid"
        finally:
            await _detener_agentes(
                jugador_ia, tablero, supervisor,
            )

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_ambos_jugadores_llm_timeout(self, sala_test):
        """Cuando ambos jugadores LLM no responden, el tablero
        aborta con reason='both-timeout' y sin ganador. El
        supervisor debe almacenar el informe correctamente."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(sala_id, PUERTO_WEB_TEST)
        # Modo "abortada" ya usa both-timeout como motivo
        tablero = await _crear_tablero(
            "tablero_mesa1", sala_jid, "abortada",
        )
        jugador_ia_x = await _crear_jugador(
            "jugador_ia_x", sala_jid, nivel_estrategia=4,
        )
        jugador_ia_o = await _crear_jugador(
            "jugador_ia_o", sala_jid, nivel_estrategia=4,
        )

        try:
            await tablero.cambiar_estado_muc("finished")

            await esperar_condicion(
                lambda: len(
                    supervisor.informes_por_sala.get(sala_id, {}),
                ) > 0,
            )

            informe = list(
                supervisor.informes_por_sala[sala_id].values(),
            )[0]
            assert informe["result"] == "aborted"
            assert informe["reason"] == "both-timeout"
            assert informe["winner"] is None
        finally:
            await _detener_agentes(
                jugador_ia_x, jugador_ia_o, tablero, supervisor,
            )

    @pytest.mark.asyncio
    @pytest.mark.timeout(TIMEOUT_TEST)
    async def test_victoria_normal_contra_jugador_ia(self, sala_test):
        """Una partida que termina con victoria normal donde uno de
        los jugadores usa estrategia LLM. El supervisor debe recibir
        un informe de victoria estándar."""
        sala_id = sala_test["id"]
        sala_jid = sala_test["jid"]

        supervisor = await _crear_supervisor(sala_id, PUERTO_WEB_TEST)
        tablero = await _crear_tablero(
            "tablero_mesa1", sala_jid, "victoria",
        )
        jugador_minimax = await _crear_jugador(
            "jugador_minimax", sala_jid, nivel_estrategia=3,
        )
        jugador_ia = await _crear_jugador(
            "jugador_ia", sala_jid, nivel_estrategia=4,
        )

        try:
            await tablero.cambiar_estado_muc("playing")
            await asyncio.sleep(1)
            await tablero.cambiar_estado_muc("finished")

            await esperar_condicion(
                lambda: len(
                    supervisor.informes_por_sala.get(sala_id, {}),
                ) > 0,
            )

            informe = list(
                supervisor.informes_por_sala[sala_id].values(),
            )[0]
            assert informe["result"] == "win"

            # Verificar que ambos jugadores aparecen como ocupantes
            ocupantes = supervisor.ocupantes_por_sala.get(
                sala_id, [],
            )
            nicks = [o["nick"] for o in ocupantes]
            assert "jugador_minimax" in nicks
            assert "jugador_ia" in nicks
        finally:
            await _detener_agentes(
                jugador_ia, jugador_minimax, tablero, supervisor,
            )
