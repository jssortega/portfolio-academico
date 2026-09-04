"""
Script de verificación exhaustiva de los servicios de Villa Olivar (Nivel 2).

Comprueba, en este orden:

  1. **XMPP — alcanzabilidad**: el puerto del servidor XMPP del perfil
     activo es accesible (TCP).
  2. **XMPP — registro y sesión SPADE**: dos agentes SPADE temporales se
     registran (in-band) y autentican contra el servidor XMPP.
  3. **XMPP — MUC**: uno de los agentes crea/se une a una sala MUC en el
     componente de conferencia y el otro la descubre vía disco#items.
  4. **LLM — listado de modelos**: se interroga al proveedor activo
     (Ollama o Gemini) para ver qué modelos están realmente disponibles.
  5. **LLM — generación**: se envía un mensaje de prueba y se imprime la
     respuesta para comprobar que la pila completa funciona.

El objetivo es que el alumno tenga UN solo punto de verificación que le
indique exactamente dónde está el problema cuando algo falla, sin tener
que ir abriendo logs de Docker o adivinar si el problema es del cliente
SPADE o del servidor.

Uso:
    python verificar_conexion.py                # Ambos servicios
    python verificar_conexion.py xmpp           # Solo XMPP
    python verificar_conexion.py llm            # Solo LLM
    python verificar_conexion.py xmpp servidor  # Forzar perfil XMPP
    python verificar_conexion.py llm gemini     # Forzar perfil LLM

Si no se indica perfil, se usa el activo en config.yaml.

Para el perfil Gemini se requiere haber exportado la variable de entorno
con la API key (por defecto GOOGLE_API_KEY), tal como indica el campo
`api_key_env` del perfil correspondiente.
"""
import asyncio
import logging
import os
import socket
import sys
from typing import Any

import httpx

# IMPORTANTE: la importación de utils debe hacerse ANTES que cualquier uso de
# spade.Agent. utils.py aplica al importarse el parche que habilita SASL sin
# TLS (PLAIN/SCRAM), necesario para que SPADE pueda autenticarse contra el
# Prosody local en Docker (que no tiene STARTTLS).
from utils import (  # noqa: E402  (intencional: ver comentario anterior)
    arrancar_agente,
    cargar_configuracion,
    construir_jid,
    crear_agente,
)
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour

# ─── Configuración del registro de trazas ────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)
# Silenciar el ruido de slixmpp/asyncio durante el handshake y los
# detalles de bajo nivel de las peticiones HTTP de httpx.
logging.getLogger("slixmpp").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# ─── Constantes ──────────────────────────────────────────────────────────────
USUARIO_PRUEBA_ALFA = "verif_alfa"
USUARIO_PRUEBA_BETA = "verif_beta"
CONTRASENA_PRUEBA = "verif_pass"
NOMBRE_SALA_PRUEBA = "verif_sala"
PREFIJO_MUC = "conference"

TIMEOUT_PUERTO_TCP = 5.0
TIMEOUT_HANDSHAKE_XMPP = 5.0
TIMEOUT_MUC = 5.0
TIMEOUT_LLM_HTTP = 10.0
TIMEOUT_LLM_GENERACION = 180.0

# Cuotas publicadas por Google AI Studio (estado 2026-04). Última revisión:
# 2026-04. Fuente: https://ai.google.dev/gemini-api/docs/rate-limits
# Una entrada `None` en `gratis` o `pago` significa que ese tier no aplica
# para el modelo. Un 0 en RPD significa que el tier no impone tope diario.
TABLA_CUOTAS_GEMINI: dict = {
    "gemini-2.0-flash-lite": {"gratis": (30, 200), "pago": (4000, 0)},
    "gemini-2.0-flash":      {"gratis": (15, 200), "pago": (2000, 0)},
    "gemini-2.5-flash-lite": {"gratis": (15, 1000), "pago": (4000, 0)},
    "gemini-2.5-flash":      {"gratis": (10, 250), "pago": (1000, 0)},
    "gemini-2.5-pro":        {"gratis": (5, 100), "pago": (1000, 0)},
    "gemini-3-flash":        {"gratis": (5, 20), "pago": (1000, 0)},
    "gemini-3-pro":          {"gratis": None, "pago": (150, 0)},
    "gemma-3":               {"gratis": (30, 14400), "pago": None},
    "gemma-3n":              {"gratis": (30, 14400), "pago": None},
}
URL_LIMITES_GEMINI = "https://ai.google.dev/gemini-api/docs/rate-limits"
URL_API_GEMINI_LIST = "https://generativelanguage.googleapis.com/v1beta/models"
URL_API_GEMINI_GEN = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{modelo}:generateContent"
)


# =============================================================================
# Comportamientos auxiliares para las pruebas MUC
# =============================================================================

class _UnirseSala(OneShotBehaviour):
    """Crea o se une a una sala MUC en el servidor del agente."""

    def __init__(self, sala_jid: str) -> None:
        super().__init__()
        self._sala_jid = sala_jid
        self.exitoso = False

    async def run(self) -> None:
        cliente = self.agent.client
        # Registrar plugin XEP-0045 (MUC) si no está cargado todavía.
        if "xep_0045" not in cliente.plugin:
            cliente.register_plugin("xep_0045")
        muc = cliente.plugin["xep_0045"]
        nick = str(self.agent.jid).split("@")[0]
        try:
            muc.join_muc(self._sala_jid, nick)
            await asyncio.sleep(TIMEOUT_MUC)
            self.exitoso = self._sala_jid in muc.get_joined_rooms()
        except Exception as error:
            logger.error("    Fallo al unirse a la sala MUC: %s", error)
            self.exitoso = False


class _DescubrirSala(OneShotBehaviour):
    """Verifica que un segundo agente puede unirse a la sala existente.

    En Prosody, las salas recién creadas NO siempre aparecen en
    ``disco#items`` hasta que el dueño envía el formulario de
    configuración. Por eso, en lugar de hacer descubrimiento por
    listado del componente MUC, este comportamiento intenta que el
    segundo agente se una a la misma sala — que es lo que en la
    práctica necesitan los agentes del proyecto para coordinarse.
    """

    def __init__(self, sala_jid: str) -> None:
        super().__init__()
        self._sala_jid = sala_jid
        self.exitoso = False
        self.ocupantes: list = []

    async def run(self) -> None:
        cliente = self.agent.client
        if "xep_0045" not in cliente.plugin:
            cliente.register_plugin("xep_0045")
        muc = cliente.plugin["xep_0045"]
        nick = str(self.agent.jid).split("@")[0]
        try:
            muc.join_muc(self._sala_jid, nick)
            await asyncio.sleep(TIMEOUT_MUC)
            self.exitoso = self._sala_jid in muc.get_joined_rooms()
            if self.exitoso:
                # Listamos los ocupantes de la sala vistos por slixmpp:
                # debería contener al menos al primer agente y al actual.
                self.ocupantes = list(muc.rooms.get(self._sala_jid, {}).keys())
        except Exception as error:
            logger.error("    Fallo al unirse a la sala desde el segundo "
                         "agente: %s", error)


# =============================================================================
# Verificación XMPP
# =============================================================================

def _puerto_abierto(servidor: str, puerto: int) -> bool:
    """Comprueba si un puerto TCP está abierto sin enviar datos."""
    accesible = False
    try:
        with socket.create_connection((servidor, puerto),
                                      timeout=TIMEOUT_PUERTO_TCP):
            accesible = True
    except (socket.timeout, ConnectionRefusedError, OSError) as error:
        logger.warning("    Puerto %d en %s no accesible: %s",
                       puerto, servidor, error)
    return accesible


async def _arrancar_dos_agentes(
    config_xmpp: dict[str, Any],
) -> tuple[Agent, Agent]:
    """Arranca dos agentes SPADE auxiliares para las pruebas MUC."""
    alfa = crear_agente(Agent, USUARIO_PRUEBA_ALFA, CONTRASENA_PRUEBA,
                        config_xmpp)
    beta = crear_agente(Agent, USUARIO_PRUEBA_BETA, CONTRASENA_PRUEBA,
                        config_xmpp)
    await arrancar_agente(alfa, config_xmpp)
    await arrancar_agente(beta, config_xmpp)
    # Registrar plugins XMPP necesarios para MUC y descubrimiento de
    # servicios. Hay que hacerlo justo después de start(), porque slixmpp
    # solo activa los plugins cargados en el momento de la primera
    # presencia.
    for cliente in (alfa.client, beta.client):
        if "xep_0030" not in cliente.plugin:
            cliente.register_plugin("xep_0030")
        if "xep_0045" not in cliente.plugin:
            cliente.register_plugin("xep_0045")
    await asyncio.sleep(TIMEOUT_HANDSHAKE_XMPP / 2)
    return alfa, beta


async def _detener_agentes(*agentes: Agent) -> None:
    """Detiene los agentes pasados, ignorando errores idempotentes."""
    for agente in agentes:
        try:
            if agente.is_alive():
                await agente.stop()
        except Exception as error:
            logger.warning("    Error al detener %s: %s", agente.jid, error)


async def verificar_xmpp(nombre_perfil: str,
                         config_xmpp: dict[str, Any]) -> bool:
    """Ejecuta la batería de pruebas XMPP para un perfil concreto."""
    servidor = config_xmpp["servidor"]
    puerto = config_xmpp.get("puerto", 5222)
    servidor_muc = f"{PREFIJO_MUC}.{servidor}"
    sala_jid = f"{NOMBRE_SALA_PRUEBA}@{servidor_muc}"

    logger.info("=" * 70)
    logger.info("Verificación XMPP — perfil '%s' (%s:%d)",
                nombre_perfil, servidor, puerto)
    logger.info("=" * 70)

    todo_correcto = False
    alfa: Agent | None = None
    beta: Agent | None = None

    # ── Paso 1: alcanzabilidad TCP ─────────────────────────────────────────
    logger.info("[1/4] Comprobando alcanzabilidad TCP del servidor XMPP...")
    if not _puerto_abierto(servidor, puerto):
        logger.error("  FALLO. El servidor %s:%d no responde.",
                     servidor, puerto)
        logger.error("  Causas habituales:")
        logger.error("    - El contenedor Prosody no está arrancado "
                     "(docker compose up -d).")
        logger.error("    - Estás fuera de la red del laboratorio "
                     "(perfil 'servidor').")
        logger.error("    - Algún cortafuegos bloquea el puerto %d.", puerto)
    else:
        logger.info("  OK. Puerto %d abierto en %s.", puerto, servidor)

        # ── Paso 2: registro + autenticación SPADE ─────────────────────────
        logger.info("[2/4] Registrando dos agentes SPADE temporales...")
        try:
            alfa, beta = await _arrancar_dos_agentes(config_xmpp)
        except Exception as error:
            logger.error("  FALLO al registrar/conectar agentes: %s", error)
            logger.error("  Causas habituales:")
            logger.error("    - Prosody no permite registro automático "
                         "(allow_registration = false).")
            logger.error("    - El parche SASL sin TLS de utils.py no se "
                         "aplicó (¿se importó utils antes de Agent?).")
            logger.error("    - Las cuentas '%s'/'%s' ya existen en el "
                         "servidor con OTRA contraseña.",
                         USUARIO_PRUEBA_ALFA, USUARIO_PRUEBA_BETA)

        if alfa is not None and beta is not None and alfa.is_alive() \
                and beta.is_alive():
            logger.info("  OK. %s y %s autenticados.", alfa.jid, beta.jid)

            # ── Paso 3: creación / unión a sala MUC ────────────────────────
            logger.info("[3/4] Creando sala MUC '%s'...", sala_jid)
            unirse = _UnirseSala(sala_jid)
            alfa.add_behaviour(unirse)
            await unirse.join(timeout=TIMEOUT_MUC * 3)
            if unirse.exitoso:
                logger.info("  OK. %s está dentro de la sala.",
                            construir_jid(USUARIO_PRUEBA_ALFA, config_xmpp))
            else:
                logger.error("  FALLO al unirse a la sala MUC.")
                logger.error("    - Verifica que el componente MUC está "
                             "habilitado en el servidor (%s).", servidor_muc)
                logger.error("    - Si usas perfil 'servidor', tu grupo "
                             "puede tener restringido el componente MUC.")

            # ── Paso 4: el segundo agente se une a la misma sala ───────
            # Pausa breve para que Prosody propague la creación.
            await asyncio.sleep(1)
            logger.info("[4/4] Uniendo al segundo agente a la misma sala...")
            descubrir = _DescubrirSala(sala_jid)
            beta.add_behaviour(descubrir)
            await descubrir.join(timeout=TIMEOUT_MUC * 3)
            if descubrir.exitoso:
                logger.info("  OK. %s también está en la sala. "
                            "Ocupantes vistos: %s",
                            beta.jid, descubrir.ocupantes)
                todo_correcto = unirse.exitoso
            else:
                logger.error("  FALLO. El segundo agente no pudo unirse "
                             "a la sala.")
                logger.error("    Causas habituales:")
                logger.error("      - El componente MUC '%s' no está "
                             "habilitado en el servidor.", servidor_muc)
                logger.error("      - La sala se creó como members-only "
                             "y la cuenta no tiene invitación.")

    if alfa is not None or beta is not None:
        await _detener_agentes(*[a for a in (alfa, beta) if a is not None])

    logger.info("Resultado XMPP perfil '%s': %s",
                nombre_perfil, "CORRECTO" if todo_correcto else "FALLO")
    return todo_correcto


# =============================================================================
# Verificación LLM
# =============================================================================

def _obtener_perfil_llm(config: dict[str, Any],
                        nombre_perfil: str) -> dict[str, Any]:
    """Obtiene el bloque de configuración del perfil LLM indicado."""
    perfiles = config.get("perfiles_llm", {})
    if nombre_perfil not in perfiles:
        raise RuntimeError(
            f"El perfil LLM '{nombre_perfil}' no existe en config.yaml. "
            f"Perfiles disponibles: {list(perfiles)}"
        )
    return perfiles[nombre_perfil]


def _formato_cuota(valor: int | None, ancho: int) -> str:
    """Formatea un componente RPM/RPD para la columna del listado."""
    if valor is None:
        texto = "—"
    elif valor == 0:
        texto = "ilim."
    else:
        texto = str(valor)
    return f"{texto:>{ancho}}"


def _cuota_publicada(nombre_modelo: str, es_gratuito: bool) -> tuple:
    """Devuelve la tupla (RPM, RPD) publicada para el modelo Gemini."""
    coincidencias = sorted(
        (p for p in TABLA_CUOTAS_GEMINI if nombre_modelo.startswith(p)),
        key=len,
        reverse=True,
    )
    cuota = (None, None)
    if coincidencias:
        clave = "gratis" if es_gratuito else "pago"
        valor = TABLA_CUOTAS_GEMINI[coincidencias[0]].get(clave)
        if valor is not None:
            cuota = valor
    return cuota


def _es_gemini_gratuito(nombre_modelo: str) -> bool:
    """Heurística por prefijo: ¿está en el nivel gratuito de Google?"""
    prefijos_gratis = (
        "gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro",
        "gemini-3-flash", "gemma-3",
    )
    return any(nombre_modelo.startswith(p) for p in prefijos_gratis)


def _listar_modelos_ollama(url_base: str) -> list:
    """Devuelve los modelos descargados en el servidor Ollama indicado."""
    url = f"{url_base}/api/tags"
    respuesta = httpx.get(url, timeout=TIMEOUT_LLM_HTTP)
    respuesta.raise_for_status()
    nombres = [m["name"] for m in respuesta.json().get("models", [])]
    return nombres


def _listar_modelos_gemini(api_key: str) -> list:
    """Devuelve los modelos publicados con soporte generateContent."""
    respuesta = httpx.get(
        URL_API_GEMINI_LIST,
        params={"key": api_key},
        timeout=TIMEOUT_LLM_HTTP,
    )
    respuesta.raise_for_status()
    expuestos = [
        modelo["name"].removeprefix("models/")
        for modelo in respuesta.json().get("models", [])
        if "generateContent" in modelo.get("supportedGenerationMethods", [])
    ]
    return expuestos


def _imprimir_modelos_gemini(modelos: list, modelo_activo: str) -> None:
    """Imprime el listado de modelos Gemini con etiquetas y cuotas."""
    gratuitos = [m for m in modelos if _es_gemini_gratuito(m)]
    pago = [m for m in modelos if not _es_gemini_gratuito(m)]
    for nombre in gratuitos + pago:
        marca = "→" if nombre == modelo_activo else " "
        es_gratuito = _es_gemini_gratuito(nombre)
        etiqueta = "[gratis]" if es_gratuito else "[pago] "
        rpm, rpd = _cuota_publicada(nombre, es_gratuito)
        logger.info(
            "  %s %s  %-38s  %s RPM · %s RPD",
            marca, etiqueta, nombre,
            _formato_cuota(rpm, 4), _formato_cuota(rpd, 5),
        )
    logger.info("-" * 70)
    logger.info("  Total: %d gratuitos, %d de pago.",
                len(gratuitos), len(pago))
    logger.info("  Cuotas oficiales: %s", URL_LIMITES_GEMINI)


def _verificar_generacion_ollama(
    perfil: dict[str, Any], parametros: dict[str, Any],
) -> bool:
    """Envía un mensaje de prueba al servidor Ollama y muestra la respuesta."""
    url = f"{perfil['url_base']}/api/generate"
    cuerpo = {
        "model": perfil["modelo"],
        "prompt": parametros["mensaje_prueba"],
        "stream": False,
        "options": {
            "temperature": parametros["temperatura"],
            "num_predict": parametros["max_tokens"],
        },
    }
    correcto = False
    try:
        respuesta = httpx.post(url, json=cuerpo, timeout=TIMEOUT_LLM_GENERACION)
        respuesta.raise_for_status()
        texto = respuesta.json().get("response", "").strip()
        if texto:
            logger.info("Respuesta del LLM:")
            logger.info("-" * 70)
            logger.info(texto)
            logger.info("-" * 70)
            correcto = True
        else:
            logger.error("  El servidor devolvió respuesta vacía.")
    except httpx.HTTPError as error:
        logger.error("  Fallo al llamar al servidor Ollama: %s", error)
    return correcto


def _verificar_generacion_gemini(
    perfil: dict[str, Any], parametros: dict[str, Any], api_key: str,
) -> bool:
    """Envía un mensaje de prueba a Google AI Studio y muestra la respuesta."""
    url = URL_API_GEMINI_GEN.format(modelo=perfil["modelo"])
    cuerpo = {
        "contents": [
            {"parts": [{"text": parametros["mensaje_prueba"]}]},
        ],
        "generationConfig": {
            "temperature": parametros["temperatura"],
            "maxOutputTokens": parametros["max_tokens"],
        },
    }
    correcto = False
    try:
        respuesta = httpx.post(
            url,
            params={"key": api_key},
            json=cuerpo,
            timeout=TIMEOUT_LLM_GENERACION,
        )
        if respuesta.status_code == 429:
            logger.error("  Cuota agotada (429). Mensaje: %s",
                         respuesta.json().get("error", {}).get("message", ""))
        else:
            respuesta.raise_for_status()
            datos = respuesta.json()
            partes = (
                datos.get("candidates", [{}])[0]
                     .get("content", {})
                     .get("parts", [])
            )
            texto = "".join(p.get("text", "") for p in partes).strip()
            if texto:
                logger.info("Respuesta del LLM:")
                logger.info("-" * 70)
                logger.info(texto)
                logger.info("-" * 70)
                correcto = True
            else:
                logger.error("  Respuesta sin texto. Cuerpo: %s", datos)
    except httpx.HTTPError as error:
        logger.error("  Fallo al llamar a Google AI Studio: %s", error)
    return correcto


async def verificar_llm(nombre_perfil: str,
                        config: dict[str, Any]) -> bool:
    """Ejecuta la batería de pruebas LLM para un perfil concreto."""
    perfil = _obtener_perfil_llm(config, nombre_perfil)
    proveedor = perfil.get("proveedor", "ollama")
    parametros = config.get("verificacion", {
        "mensaje_prueba": "Responde con una frase corta en español.",
        "temperatura": 0.2,
        "max_tokens": 256,
    })

    logger.info("=" * 70)
    logger.info("Verificación LLM — perfil '%s' (proveedor '%s', modelo '%s')",
                nombre_perfil, proveedor, perfil["modelo"])
    logger.info("=" * 70)

    todo_correcto = False

    if proveedor == "ollama":
        logger.info("[1/2] Listando modelos descargados en el servidor "
                    "Ollama...")
        try:
            modelos = _listar_modelos_ollama(perfil["url_base"])
        except httpx.HTTPError as error:
            logger.error("  FALLO al consultar Ollama: %s", error)
            logger.error("  Causas habituales:")
            logger.error("    - El contenedor Ollama no está arrancado "
                         "(docker compose up -d).")
            logger.error("    - Perfil 'servidor' fuera de la red del "
                         "laboratorio.")
            modelos = []
        if modelos:
            for nombre in modelos:
                marca = "→" if nombre == perfil["modelo"] else " "
                logger.info("  %s %s", marca, nombre)
            logger.info("-" * 70)
            if perfil["modelo"] not in modelos:
                logger.error("  AVISO: el modelo '%s' del perfil NO está "
                             "descargado.", perfil["modelo"])
                logger.error("    Descárgalo con: docker compose exec "
                             "ollama ollama pull %s", perfil["modelo"])
            else:
                logger.info("[2/2] Enviando mensaje de prueba al modelo...")
                todo_correcto = _verificar_generacion_ollama(perfil, parametros)

    elif proveedor == "gemini":
        nombre_var = perfil.get("api_key_env", "GOOGLE_API_KEY")
        api_key = os.environ.get(nombre_var, "").strip()
        if not api_key:
            logger.error("  FALLO. La variable de entorno %s no está "
                         "definida.", nombre_var)
            logger.error("    Crea tu API key en: "
                         "https://aistudio.google.com/apikey")
            logger.error("    Luego: export %s='tu-api-key'", nombre_var)
        else:
            logger.info("[1/2] Listando modelos publicados por Google AI "
                        "Studio...")
            try:
                modelos = _listar_modelos_gemini(api_key)
            except httpx.HTTPError as error:
                logger.error("  FALLO al consultar Google AI Studio: %s",
                             error)
                logger.error("  Causas habituales:")
                logger.error("    - API key inválida o caducada.")
                logger.error("    - API 'Generative Language' no habilitada "
                             "en el proyecto Google Cloud.")
                logger.error("    - Restricciones de IP/HTTP referrer en la "
                             "API key.")
                modelos = []
            if modelos:
                _imprimir_modelos_gemini(modelos, perfil["modelo"])
                if perfil["modelo"] not in modelos:
                    logger.error("  AVISO: el modelo '%s' no aparece en el "
                                 "listado.", perfil["modelo"])
                else:
                    logger.info("[2/2] Enviando mensaje de prueba al modelo...")
                    todo_correcto = _verificar_generacion_gemini(
                        perfil, parametros, api_key,
                    )
    else:
        logger.error("Proveedor LLM no soportado: '%s'", proveedor)

    logger.info("Resultado LLM perfil '%s': %s",
                nombre_perfil, "CORRECTO" if todo_correcto else "FALLO")
    return todo_correcto


# =============================================================================
# Punto de entrada
# =============================================================================

def _parsear_argumentos() -> tuple[bool, bool, str | None, str | None]:
    """Devuelve (probar_xmpp, probar_llm, perfil_xmpp, perfil_llm).

    Si se omite el perfil, se usa el activo en config.yaml.
    """
    args = sys.argv[1:]
    probar_xmpp = True
    probar_llm = True
    perfil_xmpp_forzado: str | None = None
    perfil_llm_forzado: str | None = None

    if args:
        if args[0] == "xmpp":
            probar_llm = False
            if len(args) > 1:
                perfil_xmpp_forzado = args[1]
        elif args[0] == "llm":
            probar_xmpp = False
            if len(args) > 1:
                perfil_llm_forzado = args[1]
        else:
            logger.error("Argumento no reconocido: '%s'", args[0])
            logger.error("Uso: python verificar_conexion.py "
                         "[xmpp|llm] [<perfil>]")
            sys.exit(1)

    return probar_xmpp, probar_llm, perfil_xmpp_forzado, perfil_llm_forzado


async def main() -> int:
    """Orquesta las verificaciones según los argumentos pasados."""
    probar_xmpp, probar_llm, perfil_xmpp, perfil_llm = _parsear_argumentos()
    config = cargar_configuracion()

    resultados: dict[str, bool] = {}

    if probar_xmpp:
        nombre = perfil_xmpp or config.get("perfil_xmpp_activo", "local")
        perfiles_xmpp = config.get("perfiles_xmpp", {})
        if nombre not in perfiles_xmpp:
            logger.error("Perfil XMPP '%s' no existe en config.yaml.", nombre)
            resultados[f"xmpp:{nombre}"] = False
        else:
            resultados[f"xmpp:{nombre}"] = await verificar_xmpp(
                nombre, perfiles_xmpp[nombre],
            )

    if probar_llm:
        nombre = perfil_llm or config.get("perfil_llm_activo", "local")
        try:
            resultados[f"llm:{nombre}"] = await verificar_llm(nombre, config)
        except RuntimeError as error:
            logger.error(str(error))
            resultados[f"llm:{nombre}"] = False

    logger.info("")
    logger.info("=" * 70)
    logger.info("RESUMEN")
    logger.info("=" * 70)
    for clave, exito in resultados.items():
        estado = "CORRECTO" if exito else "FALLO"
        logger.info("  %-25s → %s", clave, estado)
    logger.info("=" * 70)

    codigo_salida = 0 if all(resultados.values()) else 1
    return codigo_salida


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
