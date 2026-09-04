# -*- coding: utf-8 -*-
"""
Cliente del servicio REST de registro de agentes públicos.

Cada agente público (Centralita y los dos especialistas elegidos por el
grupo) se da de alta en el registro al arrancar, mantiene un heartbeat
periódico mientras está vivo y se da de baja al apagarse. Otros agentes
consultan el registro para descubrir las URL A2A vigentes por categoría.

Modelo de autorización (§6 documento de discusión):
  - El agente genera un token aleatorio la primera vez que arranca y lo
    persiste en .runtime/tokens/{nombre_agente}.token con permisos 0600.
  - Ese token viaja en el cuerpo del POST /agentes (alta).
  - Heartbeat y baja viajan con cabecera Authorization: Bearer <token>.
  - El registro guarda sólo el hash SHA-256 del token; nunca el valor
    en claro.

Ciclo de uso típico:

    cliente = ClienteRegistro(
        base_url="http://sinbad2.ujaen.es:8020",
        proyecto="villa-olivar",
        nombre_agente="centralita",
    )
    await cliente.alta(
        grupo="g1", rol="centralita",
        url_a2a="http://192.168.1.11:8110",
        url_agent_card="http://192.168.1.11:8110/.well-known/agent.json",
    )
    await cliente.arrancar_heartbeats()
    # ... agente vivo ...
    await cliente.parar_heartbeats()
    await cliente.baja()
    await cliente.aclose()
"""
from __future__ import annotations

import asyncio
import logging
import secrets
from pathlib import Path
from typing import Any, Optional

import httpx


# Longitud del token autogenerado. 32 caracteres URL-safe ≈ 192 bits de
# entropía, suficientes para impedir adivinación dirigida. Coincide con
# LONGITUD_MINIMA_TOKEN del paquete registro/modelos.py.
LONGITUD_TOKEN_BYTES: int = 32

# Directorio relativo al CWD donde se persisten los tokens. Se añade al
# .gitignore del proyecto (entry ".runtime/") para no comprometer secretos.
DIRECTORIO_TOKENS_DEFECTO: Path = Path(".runtime/tokens")

# Permisos del fichero de token: lectura y escritura sólo para el
# propietario. Octal explícito por claridad: 0o600 == rw- --- ---
PERMISOS_FICHERO_TOKEN: int = 0o600

# Periodo entre heartbeats. Debe ser ≤ TTL/3 según §7 del documento de
# discusión (TTL = 90 s, heartbeat = 30 s).
HEARTBEAT_SEGUNDOS_DEFECTO: int = 30

# Timeout de las llamadas HTTP. Acorde con config.yaml del proyecto.
TIMEOUT_SEGUNDOS_DEFECTO: int = 5


logger = logging.getLogger(__name__)


class ErrorRegistro(Exception):
    """Error genérico del cliente del registro."""


class AgenteNoRegistrado(ErrorRegistro):
    """Se ha llamado a heartbeat() o baja() sin haber hecho alta() antes."""


class ClienteRegistro:
    """Cliente HTTP del servicio REST de registro de agentes públicos.

    El cliente es **stateful**: tras una llamada exitosa a alta() recuerda
    el id devuelto por el registro y el token con el que se autenticará en
    heartbeat() y baja(). No es seguro compartir una instancia entre
    agentes distintos del mismo proceso; cada agente debe instanciar el
    suyo con su propio nombre.
    """

    def __init__(
        self,
        base_url: str,
        proyecto: str,
        nombre_agente: str,
        directorio_tokens: Optional[Path] = None,
        heartbeat_segundos: int = HEARTBEAT_SEGUNDOS_DEFECTO,
        timeout_segundos: int = TIMEOUT_SEGUNDOS_DEFECTO,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._proyecto = proyecto
        self._nombre_agente = nombre_agente
        self._directorio_tokens = directorio_tokens or DIRECTORIO_TOKENS_DEFECTO
        self._heartbeat_segundos = heartbeat_segundos

        # httpx.AsyncClient se crea perezosamente para no abrir conexiones
        # antes de la primera operación. Se cierra con aclose() o saliendo
        # del context manager.
        self._http: Optional[httpx.AsyncClient] = None
        self._timeout_segundos = timeout_segundos

        # Estado de la sesión: se rellena tras un alta exitoso.
        self._id_registrado: Optional[str] = None
        self._tarea_heartbeats: Optional[asyncio.Task[None]] = None

    # ─── Operaciones REST ───────────────────────────────────────────────────

    async def alta(
        self,
        grupo: str,
        rol: str,
        url_a2a: str,
        url_agent_card: str,
    ) -> dict[str, Any]:
        """
        Da de alta el agente en el registro.

        Recupera o genera el token persistido en disco, lo envía en el
        cuerpo del POST y guarda el id devuelto para usarlo en heartbeat
        y baja. Lanza ErrorRegistro si el servidor responde con un código
        distinto de 201.
        """

        token = self._token_persistente()
        cuerpo = {
            "grupo": grupo,
            "rol": rol,
            "url_a2a": url_a2a,
            "url_agent_card": url_agent_card,
            "token": token,
        }

        cliente_http = await self._cliente_http()
        ruta = f"/proyectos/{self._proyecto}/agentes"
        respuesta = await cliente_http.post(ruta, json=cuerpo)
        if respuesta.status_code != 201:
            raise ErrorRegistro(
                f"Alta fallida con código {respuesta.status_code}: "
                f"{respuesta.text}"
            )

        registro = respuesta.json()
        self._id_registrado = registro["id"]
        logger.info(
            "Agente registrado en %s/proyectos/%s con id=%s",
            self._base_url,
            self._proyecto,
            self._id_registrado,
        )
        return registro

    async def heartbeat(self) -> None:
        """Envía un heartbeat puntual al registro autenticado con el token."""
        if self._id_registrado is None:
            raise AgenteNoRegistrado(
                "Antes de heartbeat() hay que llamar a alta()."
            )

        cliente_http = await self._cliente_http()
        ruta = f"/proyectos/{self._proyecto}/agentes/id/{self._id_registrado}/heartbeat"
        respuesta = await cliente_http.post(
            ruta, headers=self._cabecera_authorization()
        )
        if respuesta.status_code != 204:
            raise ErrorRegistro(
                f"Heartbeat fallido con código {respuesta.status_code}: "
                f"{respuesta.text}"
            )

    async def baja(self) -> None:
        """Da de baja el agente y detiene los heartbeats si están en marcha."""
        await self.parar_heartbeats()

        if self._id_registrado is None:
            # No se considera error llamar a baja() sin haber hecho alta();
            # el agente puede estar en estado de cierre tras un alta fallido.
            logger.info("baja() llamado sin id registrado; no-op.")
            return None

        cliente_http = await self._cliente_http()
        ruta = f"/proyectos/{self._proyecto}/agentes/id/{self._id_registrado}"
        respuesta = await cliente_http.delete(
            ruta, headers=self._cabecera_authorization()
        )
        if respuesta.status_code not in (204, 404):
            # 404 significa que ya estaba dado de baja (purga TTL o doble
            # baja); lo aceptamos como éxito silencioso.
            raise ErrorRegistro(
                f"Baja fallida con código {respuesta.status_code}: "
                f"{respuesta.text}"
            )
        logger.info("Agente %s dado de baja.", self._id_registrado)
        self._id_registrado = None
        return None

    async def descubrir(self, rol: str) -> list[dict[str, Any]]:
        """Devuelve la lista de agentes vigentes en el proyecto con la categoría dada."""
        cliente_http = await self._cliente_http()
        ruta = f"/proyectos/{self._proyecto}/agentes/{rol}"
        respuesta = await cliente_http.get(ruta)
        if respuesta.status_code != 200:
            raise ErrorRegistro(
                f"Descubrimiento fallido con código {respuesta.status_code}: "
                f"{respuesta.text}"
            )
        return respuesta.json()

    # ─── Bucle periódico de heartbeats ──────────────────────────────────────

    async def arrancar_heartbeats(self) -> None:
        """Arranca la tarea de fondo que envía heartbeats periódicamente."""
        if self._tarea_heartbeats is not None:
            return None
        self._tarea_heartbeats = asyncio.create_task(self._bucle_heartbeats())
        return None

    async def parar_heartbeats(self) -> None:
        """Cancela la tarea de heartbeats. Idempotente."""
        tarea = self._tarea_heartbeats
        if tarea is None:
            return None
        self._tarea_heartbeats = None
        tarea.cancel()
        try:
            await tarea
        except asyncio.CancelledError:
            pass
        return None

    async def _bucle_heartbeats(self) -> None:
        """Bucle interno que latea cada self._heartbeat_segundos."""
        while True:
            await asyncio.sleep(self._heartbeat_segundos)
            try:
                await self.heartbeat()
            except Exception:
                # No queremos que un fallo de red puntual termine el bucle.
                # Logueamos y seguimos; si el problema persiste, el TTL del
                # registro acabará purgando al agente.
                logger.exception("Error enviando heartbeat; reintento en el siguiente ciclo")

    # ─── Gestión del token persistido ───────────────────────────────────────

    def _ruta_token(self) -> Path:
        """Ruta del fichero donde se persiste el token de este agente."""
        return self._directorio_tokens / f"{self._nombre_agente}.token"

    def _token_persistente(self) -> str:
        """
        Devuelve el token del agente, generándolo y persistiéndolo si no existe.

        El fichero se crea con permisos 0600 para que sólo el propietario
        pueda leerlo. Si ya existe, se reutiliza tal cual: esto permite que
        un reinicio del agente conserve su entrada en el registro al hacer
        un alta inmediato con el mismo token.
        """
        ruta = self._ruta_token()
        if ruta.is_file():
            token = ruta.read_text(encoding="utf-8").strip()
            if len(token) > 0:
                return token
            # Fichero vacío o corrupto: lo regeneramos.
            logger.warning("Fichero de token vacío, regenerando: %s", ruta)

        token = secrets.token_urlsafe(LONGITUD_TOKEN_BYTES)
        self._directorio_tokens.mkdir(parents=True, exist_ok=True)
        # Escribimos primero a un fichero temporal y movemos para evitar
        # estados intermedios visibles si dos arranques coinciden.
        ruta_temporal = ruta.with_suffix(".tmp")
        ruta_temporal.write_text(token, encoding="utf-8")
        ruta_temporal.chmod(PERMISOS_FICHERO_TOKEN)
        ruta_temporal.replace(ruta)
        return token

    def _cabecera_authorization(self) -> dict[str, str]:
        """Construye la cabecera Authorization: Bearer <token> para mutaciones."""
        token = self._token_persistente()
        return {"Authorization": f"Bearer {token}"}

    # ─── Cliente HTTP perezoso ──────────────────────────────────────────────

    async def _cliente_http(self) -> httpx.AsyncClient:
        """Devuelve el AsyncClient interno, creándolo si es la primera llamada."""
        if self._http is None:
            self._http = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout_segundos,
            )
        return self._http

    async def aclose(self) -> None:
        """Cierra el AsyncClient interno. Idempotente."""
        await self.parar_heartbeats()
        if self._http is not None:
            await self._http.aclose()
            self._http = None
        return None

    # ─── Soporte para `async with` ──────────────────────────────────────────

    async def __aenter__(self) -> "ClienteRegistro":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()
        return None
