"""Clase base homogénea para los agentes A2A del alumno.

El objetivo del módulo es ofrecer a cada grupo un punto de partida
**común** sobre el que construir sus agentes (Centralita 112 y los
cuatro especialistas). La forma externa de los agentes —Agent
Card, extremo HTTP, ciclo de vida de las Tasks— queda fijada por
la factoría; la lógica interna (clasificación, orquestación,
selección Contract Net, etc.) es responsabilidad del grupo y se
incorpora a través de los puntos de extensión documentados.

Decisiones de diseño que el grupo NO debe alterar:

- El extremo HTTP del agente se atiende, con el mismo manejador, en
  ``POST /`` y en ``POST /a2a``, y acepta JSON-RPC 2.0 con los
  métodos ``tasks/send``, ``tasks/get`` y, opcionalmente,
  ``tasks/sendSubscribe`` (Server-Sent Events). La doble ruta es
  deliberada: el cliente del coordinador inyecta en la raíz ``/`` y
  el supervisor del profesor en ``/a2a`` (``url_a2a`` + ``/a2a``).
  El grupo no debe elegir entre una y otra ni suprimir ninguna: la
  factoría las expone ambas para que el agente sea verificable por
  las dos herramientas sin cambios en su implementación.
- La Agent Card vive en ``GET /.well-known/agent.json`` y respeta
  el esquema ``contrato.agent_card.AgentCard``.

Puntos de extensión que el grupo SÍ debe implementar:

- **La inscripción en el registro REST del aula** (alta, señal de
  vida y baja): la factoría **no** la realiza automáticamente. El
  grupo debe implementarla en su agente concreto según la política
  que elija (catálogo de habilidades, reparto público/privado y
  cadencia de la señal de vida), leyendo la URL del registro de
  ``config/config.yaml`` (Hito 5). Véase la sección «Conexión con
  el registro REST» de ``doc/PREPARACION_EXAMEN_ALUMNO.md``.
- :meth:`AgenteA2A.manejar_alerta` — recibe el ``AlertaEmergencia``
  Pydantic-validado y debe devolver un ``InformeResolucion`` (o
  lanzar una excepción que el servidor traducirá a estado
  ``failed``). Es el único método obligatorio.
- :meth:`AgenteA2A.construir_agent_card` — opcional. La factoría
  ofrece una implementación por defecto compatible con el
  contrato; conviene extenderla para enriquecer el campo
  ``skills`` con la descripción real del rol.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

from aiohttp import web
from pydantic import ValidationError

from contrato.agent_card import AgentCard, Habilidad
from contrato.alerta_emergencia import AlertaEmergencia
from contrato.informe_resolucion import InformeResolucion
from contrato.tipos import EstadoTask


logger = logging.getLogger("factoria.agente_a2a")


# Cabeceras de respuesta para los flujos SSE de ``tasks/sendSubscribe``.
CABECERAS_SSE = {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}


@dataclass
class EspecificacionAgente:
    """Datos declarativos que la factoría necesita para arrancar un agente.

    Estos datos se leen del fichero ``agents.yaml`` del grupo (un
    bloque por agente) y se inyectan en la factoría a través del
    lanzador ``factoria.lanzador.arrancar_agentes_desde_configuracion``.

    Attributes:
        identificador: Nombre del agente (también usado como ``id``
            del registro REST).
        rol: Rol funcional del agente (``centralita`` u uno de los
            cuatro especialistas).
        visibilidad: ``publico`` (registrado en el directorio REST)
            o ``privado`` (solo alcanzable a través de la Centralita).
        puerto: Puerto HTTP del agente.
        host: Interfaz de escucha (típicamente ``0.0.0.0`` para
            exponerse en la IP del aula).
        modulo: Ruta importable del módulo que contiene la clase
            concreta del agente (p. ej. ``agentes.centralita``).
        clase: Nombre de la clase en ese módulo.
        parametros: Diccionario libre con parámetros propios del
            agente; la factoría lo pasa al constructor de la clase
            concreta sin interpretarlo.
    """

    identificador: str
    rol: str
    visibilidad: str
    puerto: int
    host: str
    modulo: str
    clase: str
    parametros: dict[str, Any] = field(default_factory=dict)


# Firma de un handler personalizado registrado para un método
# JSON-RPC adicional (p. ej. ``contract_net/cfp``).
HandlerJsonRpc = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class AgenteA2A:
    """Clase base para todos los agentes A2A del alumno.

    Encapsula el servidor ``aiohttp`` que expone la Agent Card y
    los extremos JSON-RPC del protocolo A2A, y delega la lógica
    de dominio en el método :meth:`manejar_alerta` que cada
    agente concreto debe implementar.

    Los agentes que no atienden alertas (p. ej. un especialista
    que solo recibe subtareas de la Centralita) pueden sobrescribir
    :meth:`manejar_alerta` para limitarse a procesar las
    subtareas y devolver un ``InformeResolucion`` con un único
    especialista en ``informes_especialistas``.
    """

    def __init__(self, especificacion: EspecificacionAgente) -> None:
        """Crea el agente con la especificación cargada del YAML."""
        self.especificacion = especificacion
        self._aplicacion: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
        self._handlers_personalizados: dict[str, HandlerJsonRpc] = {}

    # ------------------------------------------------------------------
    # Puntos de extensión que el grupo implementa.
    # ------------------------------------------------------------------

    async def manejar_alerta(
        self,
        alerta: AlertaEmergencia,
    ) -> InformeResolucion:
        """Procesa una alerta y devuelve el informe agregado.

        **Método obligatorio.** Cada agente concreto debe
        implementarlo: la Centralita orquesta a los especialistas y
        agrega el informe; cada especialista atiende su subtarea y
        devuelve un informe parcial con un único elemento en
        ``informes_especialistas``.

        Args:
            alerta: ``AlertaEmergencia`` ya validada por Pydantic.

        Returns:
            ``InformeResolucion`` que la factoría serializa como
            DataPart de la respuesta JSON-RPC.

        Raises:
            Cualquier excepción no controlada se traduce en una
            Task ``failed`` con el mensaje de la excepción.
        """
        raise NotImplementedError(
            f"El agente {self.especificacion.identificador} debe implementar "
            "manejar_alerta(...).",
        )

    def construir_agent_card(self) -> AgentCard:
        """Compone la Agent Card del agente.

        La implementación por defecto crea una card mínima válida
        con una sola habilidad declarada. Conviene sobrescribirla
        para enriquecer el campo ``skills`` con la descripción
        real del rol y de las habilidades expuestas.
        """
        habilidad = Habilidad(
            id=f"atender_{self.especificacion.rol}",
            name=f"Atención de {self.especificacion.rol}",
            description=(
                f"Atiende solicitudes vinculadas al rol "
                f"{self.especificacion.rol}."
            ),
            tags=[self.especificacion.rol, self.especificacion.visibilidad],
        )
        card = AgentCard(
            name=self.especificacion.identificador,
            description=(
                f"Agente A2A del grupo, rol {self.especificacion.rol} "
                f"({self.especificacion.visibilidad})."
            ),
            url=self._url_publica(),
            version="1.0.0",
            skills=[habilidad],
        )
        return card

    # ------------------------------------------------------------------
    # Registro de handlers JSON-RPC adicionales.
    # ------------------------------------------------------------------

    def registrar_handler(self, metodo: str, handler: HandlerJsonRpc) -> None:
        """Registra un handler para un método JSON-RPC adicional.

        Útil para implementar negociaciones Contract Net o
        cualquier extensión del protocolo que el grupo necesite.
        El handler recibe el bloque ``params`` ya deserializado y
        debe devolver el bloque ``result`` de la respuesta.
        """
        self._handlers_personalizados[metodo] = handler

    # ------------------------------------------------------------------
    # Ciclo de vida del servidor HTTP.
    # ------------------------------------------------------------------

    async def arrancar(self) -> None:
        """Arranca el servidor HTTP del agente."""
        if self._runner is not None:
            return
        self._aplicacion = self._construir_aplicacion()
        self._runner = web.AppRunner(self._aplicacion)
        await self._runner.setup()
        sitio = web.TCPSite(
            self._runner,
            host=self.especificacion.host,
            port=self.especificacion.puerto,
        )
        await sitio.start()
        logger.info(
            "Agente %s (%s) escuchando en %s:%d.",
            self.especificacion.identificador,
            self.especificacion.rol,
            self.especificacion.host,
            self.especificacion.puerto,
        )

    async def detener(self) -> None:
        """Detiene el servidor HTTP del agente."""
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None
            self._aplicacion = None
            logger.info(
                "Agente %s detenido.", self.especificacion.identificador,
            )

    # ------------------------------------------------------------------
    # Composición interna del servidor.
    # ------------------------------------------------------------------

    def _url_publica(self) -> str:
        """URL base anunciada en la Agent Card.

        Se compone como ``http://<host>:<puerto>``. En despliegues
        de aula conviene que ``host`` sea la IP privada del PC, no
        ``0.0.0.0``; eso se hace ajustando ``host`` en
        ``config/config.yaml``.
        """
        url = f"http://{self.especificacion.host}:{self.especificacion.puerto}"
        return url

    def _construir_aplicacion(self) -> web.Application:
        """Construye la aplicación ``aiohttp`` con sus rutas."""
        aplicacion = web.Application()
        aplicacion.router.add_get(
            "/.well-known/agent.json",
            self._manejar_get_agent_card,
        )
        # El extremo JSON-RPC se atiende en la raíz ``/`` y, además, en
        # ``/a2a``. La raíz es la ruta histórica que emplea el cliente del
        # coordinador; ``/a2a`` es la que fija el contrato del supervisor del
        # profesor (``url_a2a`` + ``/a2a``). Exponer ambas con el mismo
        # manejador hace que el agente sea verificable por las dos
        # herramientas del profesor sin que el grupo tenga que elegir una.
        aplicacion.router.add_post("/", self._manejar_post_jsonrpc)
        aplicacion.router.add_post("/a2a", self._manejar_post_jsonrpc)
        return aplicacion

    async def _manejar_get_agent_card(self, _: web.Request) -> web.Response:
        """Sirve la Agent Card en la ruta estándar."""
        card = self.construir_agent_card()
        return web.json_response(card.model_dump(mode="json"))

    async def _manejar_post_jsonrpc(self, peticion: web.Request) -> web.StreamResponse:
        """Punto único del extremo JSON-RPC del agente.

        Despacha entre ``tasks/send``, ``tasks/get``,
        ``tasks/sendSubscribe`` y los handlers personalizados.
        Cualquier error del despacho se traduce a un cuerpo
        JSON-RPC con el campo ``error`` y código 4xx adecuado.
        """
        try:
            cuerpo = await peticion.json()
        except json.JSONDecodeError:
            return web.json_response(
                {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}},
                status=400,
            )

        metodo = cuerpo.get("method")
        identificador_jsonrpc = cuerpo.get("id")
        parametros = cuerpo.get("params") or {}

        if metodo == "tasks/send":
            return await self._procesar_tasks_send(parametros, identificador_jsonrpc)
        if metodo == "tasks/get":
            return await self._procesar_tasks_get(parametros, identificador_jsonrpc)
        if metodo == "tasks/sendSubscribe":
            return await self._procesar_tasks_send_subscribe(parametros, identificador_jsonrpc)
        if metodo in self._handlers_personalizados:
            handler = self._handlers_personalizados[metodo]
            try:
                resultado = await handler(parametros)
                respuesta = {"jsonrpc": "2.0", "id": identificador_jsonrpc, "result": resultado}
                return web.json_response(respuesta)
            except Exception as error:
                respuesta = {
                    "jsonrpc": "2.0",
                    "id": identificador_jsonrpc,
                    "error": {"code": -32000, "message": str(error)},
                }
                return web.json_response(respuesta, status=500)

        return web.json_response(
            {
                "jsonrpc": "2.0",
                "id": identificador_jsonrpc,
                "error": {"code": -32601, "message": f"Método '{metodo}' no soportado"},
            },
            status=404,
        )

    async def _procesar_tasks_send(
        self,
        parametros: dict[str, Any],
        identificador_jsonrpc: Any,
    ) -> web.Response:
        """Despacha el flujo síncrono ``tasks/send``."""
        identificador_task = parametros.get("id") or str(uuid.uuid4())
        datos = self._extraer_datos_alerta(parametros)
        try:
            alerta = AlertaEmergencia.model_validate(datos)
        except ValidationError as error:
            cuerpo_failed = self._cuerpo_jsonrpc_failed(
                identificador_jsonrpc, identificador_task, str(error),
            )
            return web.json_response(cuerpo_failed)
        try:
            informe = await self.manejar_alerta(alerta)
        except Exception as error:
            cuerpo_failed = self._cuerpo_jsonrpc_failed(
                identificador_jsonrpc, identificador_task, str(error),
            )
            return web.json_response(cuerpo_failed)
        cuerpo_completed = self._cuerpo_jsonrpc_completed(
            identificador_jsonrpc, identificador_task, informe,
        )
        return web.json_response(cuerpo_completed)

    async def _procesar_tasks_get(
        self,
        parametros: dict[str, Any],
        identificador_jsonrpc: Any,
    ) -> web.Response:
        """Stub de ``tasks/get``.

        La factoría no persiste las Tasks: el grupo debe sobrescribir
        este comportamiento si necesita exponer un historial real
        a través de ``tasks/get``. Sin esa sobrescritura, devuelve
        404 con un mensaje accionable.
        """
        return web.json_response(
            {
                "jsonrpc": "2.0",
                "id": identificador_jsonrpc,
                "error": {
                    "code": -32601,
                    "message": (
                        "tasks/get no implementado por defecto en la factoría. "
                        "El grupo debe registrar su propio handler con "
                        "self.registrar_handler('tasks/get', ...) o sobrescribir "
                        "_procesar_tasks_get."
                    ),
                },
            },
            status=404,
        )

    async def _procesar_tasks_send_subscribe(
        self,
        parametros: dict[str, Any],
        identificador_jsonrpc: Any,
    ) -> web.StreamResponse:
        """Stub de ``tasks/sendSubscribe``.

        Emite dos eventos SSE de cortesía (un ``working`` y un
        ``failed`` indicando que el grupo debe implementar el
        streaming si quiere aspirar a nota 10). El grupo que
        quiera implementar el Hito 6 E3 debe sobrescribir este
        método o registrar un handler personalizado.
        """
        identificador_task = parametros.get("id") or str(uuid.uuid4())
        respuesta = web.StreamResponse(headers=CABECERAS_SSE)
        await respuesta.prepare(  # noqa: F841 — la respuesta queda abierta
            web.Request.empty(),
        ) if False else None  # placeholder; ver nota más abajo
        # Nota: aiohttp exige `await respuesta.prepare(request)` con la
        # `Request` real para emitir SSE. La implementación didáctica
        # se traslada al grupo, que debe sobrescribir este método.
        return web.json_response(
            {
                "jsonrpc": "2.0",
                "id": identificador_jsonrpc,
                "error": {
                    "code": -32601,
                    "message": (
                        "tasks/sendSubscribe no implementado por defecto en la "
                        "factoría. El grupo debe sobrescribir "
                        "_procesar_tasks_send_subscribe para emitir SSE."
                    ),
                },
            },
            status=404,
        )

    # ------------------------------------------------------------------
    # Helpers de composición de respuestas JSON-RPC.
    # ------------------------------------------------------------------

    def _extraer_datos_alerta(self, parametros: dict[str, Any]) -> dict[str, Any]:
        """Localiza el DataPart con los datos de la alerta."""
        mensaje = parametros.get("message") or {}
        partes = mensaje.get("parts") or []
        for parte in partes:
            if isinstance(parte, dict) and parte.get("type") == "data":
                datos = parte.get("data") or {}
                return datos
        return {}

    def _cuerpo_jsonrpc_completed(
        self,
        identificador_jsonrpc: Any,
        identificador_task: str,
        informe: InformeResolucion,
    ) -> dict[str, Any]:
        """Compone la respuesta JSON-RPC con la Task ``completed``."""
        cuerpo = {
            "jsonrpc": "2.0",
            "id": identificador_jsonrpc,
            "result": {
                "id": identificador_task,
                "status": {"state": EstadoTask.COMPLETED.value},
                "history": [
                    {"state": EstadoTask.SUBMITTED.value},
                    {"state": EstadoTask.WORKING.value},
                    {"state": EstadoTask.COMPLETED.value},
                ],
                "artifacts": [
                    {
                        "parts": [
                            {"type": "data", "data": informe.model_dump(mode="json")},
                        ],
                    },
                ],
            },
        }
        return cuerpo

    def _cuerpo_jsonrpc_failed(
        self,
        identificador_jsonrpc: Any,
        identificador_task: str,
        mensaje_error: str,
    ) -> dict[str, Any]:
        """Compone la respuesta JSON-RPC con la Task ``failed``."""
        cuerpo = {
            "jsonrpc": "2.0",
            "id": identificador_jsonrpc,
            "result": {
                "id": identificador_task,
                "status": {
                    "state": EstadoTask.FAILED.value,
                    "message": mensaje_error,
                },
                "history": [
                    {"state": EstadoTask.SUBMITTED.value},
                    {"state": EstadoTask.WORKING.value},
                    {"state": EstadoTask.FAILED.value},
                ],
            },
        }
        return cuerpo
