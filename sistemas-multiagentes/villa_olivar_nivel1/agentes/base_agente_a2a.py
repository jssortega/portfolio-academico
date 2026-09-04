"""
Clase base de los agentes A2A del Nivel 3 — Villa Olivar.

Este módulo proporciona `BaseAgenteA2A`, la infraestructura común a los
cinco agentes del sistema (Centralita, Bomberos, Sanitario, Policía y
Servicios Municipales). Cada agente concreto **hereda** de esta clase y
solo aporta su capa de razonamiento.

Arquitectura por capas (doc/ARQUITECTURA.md §4.2). `BaseAgenteA2A`
cubre las dos capas superiores; cada subclase aporta las dos inferiores:

    ┌────────────────────────────────────────────────┐
    │  Transporte + Despacho   →  BaseAgenteA2A        │  servidor aiohttp
    │                                                 │  + despacho JSON-RPC
    │  Razonamiento (Nivel 2)  →  subclase concreta    │  LlmAgent + FunctionTool
    │  Dominio (Nivel 1)       →  logica/*.py          │  funciones puras
    └────────────────────────────────────────────────┘

POR QUÉ aiohttp Y NO LA CLASE A2AStarletteApplication DE a2a-sdk
----------------------------------------------------------------
El supervisor del profesor y el contrato del Nivel 3
(doc/contrato_supervisor_nivel3.md §3 y §5) emplean el método JSON-RPC
`tasks/send`. La clase `A2AStarletteApplication` de a2a-sdk 0.3.x solo
reconoce el método `message/send`: ante un `tasks/send` responde con el
error -32601 («método no encontrado») ANTES de invocar ningún manejador.
Por eso, en este proyecto el extremo HTTP del agente y el despacho de
los métodos JSON-RPC se construyen explícitamente con aiohttp. Es la
misma arquitectura de la factoría `factoria.AgenteA2A` de la rama
`examen-alumno`: heredar de esta base hace que la migración al esquema
del examen consista en cambiar una sola línea (la clase base).

ADAPTACIÓN RESPECTO AL GUIÓN 9
------------------------------
En el Guión 9 (Lecturas/nivel 3/guion9-a2a-adk-ollama) el servidor A2A
se ensamblaba con a2a-sdk y el cliente usaba `message/send`. Lo que se
aprendió allí se adapta a este proyecto así:

  - Guión 9: `construir_aplicacion()` ensambla `A2AStarletteApplication`
    + `DefaultRequestHandler`. Aquí: `_construir_aplicacion()` ensambla
    una `web.Application` de aiohttp con un despacho JSON-RPC propio.
  - Guión 9: `AgenteInteligenteExecutor.execute()` traduce la Task A2A
    y delega en el `Runner` de ADK. Aquí: `manejar_alerta()` recibe la
    `AlertaEmergencia` ya validada y delega en el razonamiento de ADK.
  - El razonamiento de ADK (LlmAgent, FunctionTool, Runner) que se
    estudió en el Guión 9 NO cambia: se reutiliza intacto dentro de
    `manejar_alerta` en cada subclase.

QUÉ ESCRIBE EL GRUPO
--------------------
La capa de transporte de esta base está completa: no hay que tocarla.
Cada subclase concreta implementa, como mínimo, `manejar_alerta`; los
detalles están en doc/guia_base_agente_a2a.md.

Autor(es): [Nombre del grupo]
Grupo: <denominación del grupo>
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable
from datetime import datetime, timezone

from aiohttp import web
from pydantic import ValidationError

from contrato.agent_card import AgentCard, Habilidad
from contrato.alerta_emergencia import AlertaEmergencia
from contrato.informe_resolucion import InformeResolucion
from contrato.tipos import EstadoTask
from contrato.consulta_estado import ConsultaEstado
from contrato.estado_agente import EstadoAgente

logger = logging.getLogger(__name__)


# ─── Constantes del protocolo A2A / JSON-RPC ─────────────────────────────────

# Versión del protocolo JSON-RPC que viaja en cada envoltura.
VERSION_JSONRPC = "2.0"

# Métodos JSON-RPC del protocolo A2A que reconoce el agente.
METODO_TASKS_SEND = "tasks/send"
METODO_TASKS_GET = "tasks/get"
METODO_TASKS_SEND_SUBSCRIBE = "tasks/sendSubscribe"

# Códigos de error normalizados de JSON-RPC 2.0.
CODIGO_JSON_MAL_FORMADO = -32700
CODIGO_PETICION_INVALIDA = -32600
CODIGO_METODO_NO_ENCONTRADO = -32601
CODIGO_ERROR_SERVIDOR = -32000

# Códigos de estado HTTP de las respuestas de error.
HTTP_PETICION_INCORRECTA = 400
HTTP_NO_ENCONTRADO = 404
HTTP_ERROR_SERVIDOR = 500

# Rutas HTTP que publica el agente. El extremo JSON-RPC es la raíz, igual
# que en la factoría del examen; la tarjeta de agente vive en la ruta
# estándar de descubrimiento.
RUTA_AGENT_CARD = "/.well-known/agent.json"
RUTA_JSONRPC = "/"
RUTA_JSONRPC_A2A = "/a2a"

# Discriminador del tipo de Part que transporta datos estructurados
# (la AlertaEmergencia viaja en una Part de este tipo).
TIPO_PARTE_DATOS = "data"

# Versión por defecto que se publica en la tarjeta de agente.
VERSION_AGENTE_POR_DEFECTO = "1.0.0"

# Cabeceras de una respuesta SSE (tasks/sendSubscribe, Hito 6).
CABECERAS_SSE = {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}


@dataclass
class EspecificacionAgente:
    """Datos declarativos que la base necesita para arrancar un agente.

    Estos datos se leen del fichero `agents.yaml` del grupo (un bloque
    por agente) y los inyecta el lanzador `main.py`. Coinciden, campo a
    campo, con la `EspecificacionAgente` de la factoría del examen, de
    modo que el mismo `agents.yaml` sirve para las dos ramas.

    Attributes:
        identificador: Nombre del agente; se usa también como `id` en el
            registro REST del aula.
        rol: Rol funcional (`centralita`, `bomberos`, `sanitario`,
            `policia` o `municipal`).
        visibilidad: `publico` (se registra en el directorio REST) o
            `privado` (solo alcanzable a través de la Centralita).
        puerto: Puerto HTTP en el que escucha el agente.
        host: Interfaz de escucha (`0.0.0.0` para exponerse en la IP del
            aula; `127.0.0.1` para un agente privado).
        modulo: Ruta importable del módulo con la clase concreta del
            agente (por ejemplo, `agentes.agente_bomberos`).
        clase: Nombre de la clase concreta dentro de ese módulo.
        parametros: Diccionario libre con parámetros propios del agente
            (por ejemplo, las URL de los especialistas privados de la
            Centralita o el perfil de modelo de lenguaje). La base no lo
            interpreta: lo entrega tal cual a la subclase.
    """

    identificador: str
    rol: str
    visibilidad: str
    puerto: int
    host: str
    modulo: str
    clase: str
    parametros: dict[str, Any] = field(default_factory=dict)


# Firma de un manejador registrado para un método JSON-RPC adicional
# (por ejemplo, `contract_net/cfp`). Recibe el bloque `params` ya
# deserializado y devuelve el bloque `result` de la respuesta.
HandlerJsonRpc = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class BaseAgenteA2A:
    """Clase base común a los cinco agentes A2A del sistema.

    Encapsula el servidor `aiohttp` que expone la tarjeta de agente y el
    extremo JSON-RPC del protocolo A2A, y delega la lógica de dominio en
    el método `manejar_alerta`, que cada agente concreto implementa.

    La frontera de responsabilidades es estricta:

    - **La base** (esta clase) se ocupa del transporte: arrancar el
      servidor, interpretar la envoltura JSON-RPC, despachar los métodos
      del protocolo, validar la entrada contra el contrato y componer la
      Task de respuesta. El grupo no necesita modificarla.
    - **La subclase** se ocupa del razonamiento: construye su `LlmAgent`
      de ADK e implementa `manejar_alerta`. Es el único punto de entrada
      funcional del agente.

    Esa separación es la que hace mecánica la migración a la factoría
    `factoria.AgenteA2A` del examen: misma interfaz para la subclase.
    """

    def __init__(self, especificacion: EspecificacionAgente) -> None:
        """Crea el agente a partir de su especificación declarativa.

        No arranca el servidor: eso lo hace `arrancar()`. El constructor
        solo guarda la especificación e inicia las estructuras internas.

        Args:
            especificacion: Datos del agente leídos de `agents.yaml`.
        """
        self.especificacion = especificacion
        # Manejadores de métodos JSON-RPC adicionales (Contract Net,
        # Hito 4). Se inician al diccionario vacío: una subclase los
        # añade con `registrar_handler` desde su constructor.
        self._handlers_personalizados: dict[str, HandlerJsonRpc] = {}
        # Recursos del servidor HTTP; se crean en `arrancar()`.
        self._aplicacion: web.Application | None = None
        self._runner: web.AppRunner | None = None

    # ─── Puntos de extensión que implementa cada subclase ────────────────────

    async def manejar_alerta(self, alerta: AlertaEmergencia) -> InformeResolucion:
        """Procesa una alerta y devuelve el informe de resolución.

        **Método obligatorio.** Cada agente concreto debe sobrescribirlo:
        la Centralita orquesta a los especialistas y agrega el informe;
        cada especialista atiende su subtarea y devuelve un informe
        parcial. Es el equivalente, en este proyecto, al `execute()` del
        `AgentExecutor` del Guión 9: aquí recibe la `AlertaEmergencia` ya
        validada y delega en el razonamiento de ADK que el grupo conserva
        del Nivel 2.

        Args:
            alerta: `AlertaEmergencia` ya validada por Pydantic. La base
                garantiza que llega conforme al contrato.

        Returns:
            `InformeResolucion` validado. La base lo serializa como Part
            de datos dentro de la Task de respuesta.

        Raises:
            NotImplementedError: Si la subclase no implementa el método.
                Cualquier otra excepción que lance la subclase la traduce
                la base a una Task con estado `failed`.
        """
        raise NotImplementedError(
            f"El agente '{self.especificacion.identificador}' debe implementar "
            "manejar_alerta(alerta)."
        )

    def construir_agent_card(self) -> AgentCard:
        """Compone la tarjeta de agente (Agent Card) que se publica.

        Esta implementación por defecto produce una tarjeta mínima válida
        con una sola habilidad declarada. Conviene **sobrescribirla** en
        la subclase para enriquecer el campo `skills` con la descripción
        real del rol. Es el equivalente a `crear_agent_card()` del
        Guión 9, pero compuesta a partir de la especificación en lugar de
        leerse de un fichero JSON suelto.

        Returns:
            `AgentCard` conforme al esquema de `contrato.agent_card`.
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
        tarjeta = AgentCard(
            name=self.especificacion.identificador,
            description=(
                f"Agente A2A del grupo, rol {self.especificacion.rol} "
                f"({self.especificacion.visibilidad})."
            ),
            url=self._url_publica(),
            version=VERSION_AGENTE_POR_DEFECTO,
            skills=[habilidad],
        )
        return tarjeta

    def registrar_handler(self, metodo: str, handler: HandlerJsonRpc) -> None:
        """Registra un manejador para un método JSON-RPC adicional.

        Es el mecanismo de extensión del protocolo: en lugar de modificar
        el despacho de la base, una subclase añade los métodos que
        necesite (por ejemplo, `contract_net/cfp` y `contract_net/award`
        del Hito 4) llamando a este método desde su constructor.

        Args:
            metodo: Nombre del método JSON-RPC (por ejemplo,
                `contract_net/cfp`).
            handler: Corrutina que recibe el bloque `params` y devuelve
                el bloque `result` de la respuesta.
        """
        self._handlers_personalizados[metodo] = handler

    # ─── Ciclo de vida del servidor HTTP ─────────────────────────────────────

    async def arrancar(self) -> None:
        """Arranca el servidor HTTP del agente.

        Construye la `web.Application`, la pone en marcha sobre el
        `host:puerto` de la especificación y deja el agente atendiendo
        peticiones. El alta en el registro REST del aula y la señal de
        vida (heartbeat) no se hacen aquí: una subclase pública los añade
        sobrescribiendo este método con `await super().arrancar()` al
        principio (doc/guia_base_agente_a2a.md §9).
        """
        if self._runner is None:
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
                "Agente '%s' (%s) escuchando en %s:%d",
                self.especificacion.identificador,
                self.especificacion.rol,
                self.especificacion.host,
                self.especificacion.puerto,
            )

    async def detener(self) -> None:
        """Detiene ordenadamente el servidor HTTP del agente.

        Una subclase pública se da de baja del registro REST antes de
        llamar a `await super().detener()` (doc/guia_base_agente_a2a.md
        §9).
        """
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None
            self._aplicacion = None
            logger.info(
                "Agente '%s' detenido", self.especificacion.identificador
            )

    # ─── Composición interna del servidor (no hay que tocarla) ───────────────

    def _url_publica(self) -> str:
        """Devuelve la URL base que se anuncia en la tarjeta de agente.

        Se compone como `http://<host>:<puerto>`. En el aula conviene que
        `host` sea la IP privada del PC, no `0.0.0.0`; eso se ajusta en
        `config.yaml`.
        """
        url = f"http://{self.especificacion.host}:{self.especificacion.puerto}"
        return url

    def _construir_aplicacion(self) -> web.Application:
        """Construye la `web.Application` de aiohttp con sus dos rutas.

        Es el equivalente a `construir_aplicacion()` del Guión 9, pero en
        lugar de delegar el enrutado en a2a-sdk se declaran a mano las
        dos rutas del protocolo: la tarjeta de agente y el extremo
        JSON-RPC.
        """
        aplicacion = web.Application()
        aplicacion.router.add_get(RUTA_AGENT_CARD, self._manejar_get_agent_card)
        aplicacion.router.add_post(RUTA_JSONRPC, self._manejar_post_jsonrpc)
        aplicacion.router.add_post(RUTA_JSONRPC_A2A, self._manejar_post_jsonrpc)
        return aplicacion

    async def _manejar_get_agent_card(self, _: web.Request) -> web.Response:
        """Sirve la tarjeta de agente en la ruta estándar de descubrimiento."""
        tarjeta = self.construir_agent_card()
        return web.json_response(tarjeta.model_dump(mode="json"))

    async def _manejar_post_jsonrpc(
        self, peticion: web.Request
    ) -> web.StreamResponse:
        """Extremo único del protocolo: interpreta y despacha el JSON-RPC.

        Esta es la pieza que el Guión 9 delegaba en `A2AStarletteApplication`
        y que aquí se escribe explícitamente, porque aquel componente no
        reconoce el método `tasks/send`. La secuencia es:

        1. Interpretar el cuerpo como JSON; si falla, error -32700.
        2. Leer el campo `method`; si falta, error -32600.
        3. Encaminar el método hacia su procesador. Si no se reconoce ni
           figura entre los handlers registrados, error -32601.

        Mantiene un único punto de retorno: cada rama asigna la respuesta
        a `respuesta` y la función la devuelve al final.
        """
        respuesta: web.StreamResponse
        try:
            cuerpo = await peticion.json()
        except json.JSONDecodeError:
            respuesta = self._respuesta_error(
                None, CODIGO_JSON_MAL_FORMADO, "JSON mal formado"
            )
        else:
            metodo = cuerpo.get("method")
            id_jsonrpc = cuerpo.get("id")
            parametros = cuerpo.get("params") or {}
            if metodo is None:
                respuesta = self._respuesta_error(
                    id_jsonrpc,
                    CODIGO_PETICION_INVALIDA,
                    "Falta el campo 'method' en la envoltura JSON-RPC",
                )
            elif metodo == METODO_TASKS_SEND:
                respuesta = await self._procesar_tasks_send(parametros, id_jsonrpc)
            elif metodo == METODO_TASKS_GET:
                respuesta = await self._procesar_tasks_get(parametros, id_jsonrpc)
            elif metodo == METODO_TASKS_SEND_SUBSCRIBE:
                respuesta = await self._procesar_tasks_send_subscribe(
                    parametros, id_jsonrpc
                )
            elif metodo in self._handlers_personalizados:
                respuesta = await self._procesar_handler_personalizado(
                    metodo, parametros, id_jsonrpc
                )
            else:
                respuesta = self._respuesta_error(
                    id_jsonrpc,
                    CODIGO_METODO_NO_ENCONTRADO,
                    f"Método '{metodo}' no reconocido",
                    HTTP_NO_ENCONTRADO,
                )
        return respuesta

    async def _procesar_tasks_send(
        self, parametros: dict[str, Any], id_jsonrpc: Any
    ) -> web.Response:
        """Despacha el flujo síncrono `tasks/send`.

        Localiza la `AlertaEmergencia` en la Part de datos del mensaje,
        la valida contra el contrato, delega en `manejar_alerta` y
        compone la Task de respuesta. Cualquier fallo de validación o
        cualquier excepción de la subclase se traduce a una Task con
        estado `failed`: el grupo no necesita envolver `manejar_alerta`
        en `try/except` defensivos.
        """
        id_task = parametros.get("id") or str(uuid.uuid4())
        datos = self._extraer_datos_alerta(parametros)
        cuerpo: dict[str, Any]

        # Protocolo 2 del supervisor: sondeo de estado.
        # El supervisor manda ConsultaEstado por tasks/send, no AlertaEmergencia.
        if datos.get("operacion") == "consultar_estado" or (
                "id_emergencia" not in datos and "texto" not in datos
        ):
            try:
                ConsultaEstado.model_validate(datos)
            except ValidationError as error:
                cuerpo = self._cuerpo_jsonrpc_failed(id_jsonrpc, id_task, str(error))
            else:
                cuerpo = self._cuerpo_jsonrpc_estado_agente(id_jsonrpc, id_task)

            return web.json_response(cuerpo)

        # Protocolo 1 del supervisor: alerta de emergencia.
        try:
            alerta = AlertaEmergencia.model_validate(datos)
        except ValidationError as error:
            cuerpo = self._cuerpo_jsonrpc_failed(id_jsonrpc, id_task, str(error))
        else:
            try:
                informe = await self.manejar_alerta(alerta)
            except Exception as error:
                cuerpo = self._cuerpo_jsonrpc_failed(
                    id_jsonrpc, id_task, str(error)
                )
            else:
                cuerpo = self._cuerpo_jsonrpc_completed(
                    id_jsonrpc, id_task, informe
                )

        return web.json_response(cuerpo)

    async def _procesar_tasks_get(
        self, parametros: dict[str, Any], id_jsonrpc: Any
    ) -> web.Response:
        """Atiende `tasks/get` (consulta del estado de una Task).

        La base no persiste el historial de Tasks. Un grupo que necesite
        exponer un historial real debe sobrescribir este método o
        registrar su propio manejador. Por defecto devuelve -32601 con un
        mensaje accionable.
        """
        respuesta = self._respuesta_error(
            id_jsonrpc,
            CODIGO_METODO_NO_ENCONTRADO,
            "tasks/get no implementado por defecto: sobrescribe "
            "_procesar_tasks_get en tu subclase si necesitas historial.",
            HTTP_NO_ENCONTRADO,
        )
        return respuesta

    async def _procesar_tasks_send_subscribe(
        self, parametros: dict[str, Any], id_jsonrpc: Any
    ) -> web.StreamResponse:
        """Atiende `tasks/sendSubscribe` (envío con transmisión continua).

        El Hito 6 pide una respuesta Server-Sent Events (SSE) con eventos
        parciales de progreso. La base deja el método como punto de
        extensión: el grupo que aspire a ese hito debe sobrescribirlo
        para emitir SSE (cabeceras en `CABECERAS_SSE`). Por defecto
        devuelve -32601 con un mensaje accionable.
        """
        respuesta = self._respuesta_error(
            id_jsonrpc,
            CODIGO_METODO_NO_ENCONTRADO,
            "tasks/sendSubscribe no implementado por defecto: sobrescribe "
            "_procesar_tasks_send_subscribe para emitir SSE (Hito 6).",
            HTTP_NO_ENCONTRADO,
        )
        return respuesta

    async def _procesar_handler_personalizado(
        self, metodo: str, parametros: dict[str, Any], id_jsonrpc: Any
    ) -> web.Response:
        """Invoca un manejador registrado con `registrar_handler`.

        Traduce cualquier excepción del manejador a un error JSON-RPC
        -32000, igual que `_procesar_tasks_send` hace con `manejar_alerta`.
        """
        handler = self._handlers_personalizados[metodo]
        respuesta: web.Response
        try:
            resultado = await handler(parametros)
        except Exception as error:  # noqa: BLE001 — traducción a error JSON-RPC
            respuesta = self._respuesta_error(
                id_jsonrpc, CODIGO_ERROR_SERVIDOR, str(error), HTTP_ERROR_SERVIDOR
            )
        else:
            cuerpo = {
                "jsonrpc": VERSION_JSONRPC,
                "id": id_jsonrpc,
                "result": resultado,
            }
            respuesta = web.json_response(cuerpo)
        return respuesta

    # ─── Composición de respuestas JSON-RPC ──────────────────────────────────

    def _extraer_datos_alerta(self, parametros: dict[str, Any]) -> dict[str, Any]:
        """Localiza la Part de datos del mensaje y devuelve su contenido.

        La `AlertaEmergencia` no viaja «en crudo»: está anidada en
        `params.message.parts`, dentro de la primera Part cuyo `type` sea
        `data`. Si no hay ninguna, devuelve el diccionario vacío y la
        validación posterior producirá un error claro.
        """
        mensaje = parametros.get("message") or {}
        partes = mensaje.get("parts") or []
        parte_datos = next(
            (
                parte
                for parte in partes
                if isinstance(parte, dict)
                and parte.get("type") == TIPO_PARTE_DATOS
            ),
            {},
        )
        datos = parte_datos.get("data") or {}
        return datos

    def _respuesta_error(
        self,
        id_jsonrpc: Any,
        codigo: int,
        mensaje: str,
        estado_http: int = HTTP_PETICION_INCORRECTA,
    ) -> web.Response:
        """Compone una respuesta JSON-RPC con el campo `error`."""
        cuerpo = {
            "jsonrpc": VERSION_JSONRPC,
            "id": id_jsonrpc,
            "error": {"code": codigo, "message": mensaje},
        }
        respuesta = web.json_response(cuerpo, status=estado_http)
        return respuesta

    def _cuerpo_jsonrpc_estado_agente(
            self, id_jsonrpc: Any, id_task: str
    ) -> dict[str, Any]:
        """Compone una respuesta válida a ConsultaEstado del supervisor."""

        estado = EstadoAgente(
            agente_id=self.especificacion.identificador,
            rol=self.especificacion.rol,
            estado=getattr(self, "estado_actual", "libre"),
            emergencia_actual=getattr(self, "id_emergencia_activa", None),
            detalle=getattr(self, "detalle_estado", "Agente operativo."),
            momento=datetime.now(timezone.utc),
        )

        datos_estado = estado.model_dump(mode="json")

        return {
            "jsonrpc": VERSION_JSONRPC,
            "id": id_jsonrpc,
            "result": {
                "id": id_task,
                "status": {
                    "state": EstadoTask.COMPLETED.value,
                    "message": {
                        "role": "agent",
                        "parts": [
                            {
                                "type": TIPO_PARTE_DATOS,
                                "data": datos_estado,
                            }
                        ],
                    },
                },
                "history": [
                    {"state": EstadoTask.SUBMITTED.value},
                    {"state": EstadoTask.WORKING.value},
                    {"state": EstadoTask.COMPLETED.value},
                ],
                "artifacts": [
                    {
                        "parts": [
                            {
                                "type": TIPO_PARTE_DATOS,
                                "data": datos_estado,
                            }
                        ]
                    }
                ],
            },
        }

    def _cuerpo_jsonrpc_completed(
            self, id_jsonrpc: Any, id_task: str, informe: InformeResolucion
    ) -> dict[str, Any]:
        """Compone la respuesta JSON-RPC con la Task en estado `completed`.

        El InformeResolucion se devuelve en status.message.parts, que es
        lo que consume el supervisor, y también en artifacts para mantener
        compatibilidad con el cliente interno de la Centralita.
        """
        datos_informe = informe.model_dump(mode="json")

        parte_datos = {
            "type": TIPO_PARTE_DATOS,
            "data": datos_informe,
        }

        cuerpo = {
            "jsonrpc": VERSION_JSONRPC,
            "id": id_jsonrpc,
            "result": {
                "id": id_task,
                "status": {
                    "state": EstadoTask.COMPLETED.value,
                    "message": {
                        "role": "agent",
                        "parts": [parte_datos],
                    },
                },
                "history": [
                    {"state": EstadoTask.SUBMITTED.value},
                    {"state": EstadoTask.WORKING.value},
                    {"state": EstadoTask.COMPLETED.value},
                ],
                # Lo mantenemos para que tu Centralita siga pudiendo leer
                # respuestas de especialistas como hasta ahora.
                "artifacts": [
                    {
                        "parts": [parte_datos],
                    }
                ],
            },
        }
        return cuerpo

    def _cuerpo_jsonrpc_failed(
        self, id_jsonrpc: Any, id_task: str, mensaje_error: str
    ) -> dict[str, Any]:
        """Compone la respuesta JSON-RPC con la Task en estado `failed`.

        Un `tasks/send` mal validado o una excepción de la subclase no
        son un error de transporte: la petición se atendió. Por eso la
        respuesta es una Task con estado `failed` dentro de `result`, no
        un objeto `error` de JSON-RPC.
        """
        cuerpo = {
            "jsonrpc": VERSION_JSONRPC,
            "id": id_jsonrpc,
            "result": {
                "id": id_task,
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
