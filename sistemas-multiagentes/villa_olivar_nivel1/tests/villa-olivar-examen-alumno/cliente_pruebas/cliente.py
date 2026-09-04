"""Cliente A2A asíncrono empleado por el coordinador del profesor.

Este módulo implementa la lógica de cliente que las pruebas del
profesor utilizan para interactuar con la Centralita del grupo
evaluado. Encapsula tres responsabilidades:

1. **Descubrimiento**: localizar la Centralita y los especialistas
   públicos consultando el registro central en `sinbad2.ujaen.es` y
   leyendo sus Agent Cards en `/.well-known/agent.json`.
2. **Envío de Tasks**: construir peticiones JSON-RPC 2.0 sobre el
   protocolo A2A, enviarlas a la Centralita y recoger la respuesta.
3. **Consulta de estado**: obtener el historial de una Task previa
   mediante `tasks/get` para validar el ciclo de vida.

El cliente es asíncrono y se construye sobre `httpx.AsyncClient`,
lo que permite reutilizar conexiones y gestionar tiempos de espera
de forma uniforme.
"""

import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional

import httpx

from contrato.agent_card import AgentCard
from contrato.alerta_emergencia import AlertaEmergencia
from contrato.informe_resolucion import InformeResolucion
from contrato.tipos import EstadoTask


# Tiempo de espera predeterminado para todas las llamadas HTTP. Se puede
# anular en el constructor del cliente cuando una prueba concreta
# necesite un valor distinto.
TIEMPO_ESPERA_PREDETERMINADO = 30.0

# Versión del protocolo JSON-RPC empleada por el A2A.
VERSION_JSON_RPC = "2.0"

# Ruta estándar de la Agent Card en el dominio del agente.
RUTA_AGENT_CARD = "/.well-known/agent.json"

# Nombre del proyecto bajo el que el registro REST namespacea los
# agentes de Villa Olivar. El registro central de la asignatura
# alberga varios proyectos (`villa-olivar`, `tic-tac-toe`, ...) y
# cada uno tiene su propio catálogo. Esta constante se puede
# sobrescribir al construir el cliente con `nombre_proyecto=`.
NOMBRE_PROYECTO_POR_DEFECTO = "villa-olivar"

# Plantilla de la ruta del catálogo completo de un proyecto. El
# registro REST de Villa Olivar (documentado en
# `doc/registro_rest_para_clientes.md` de la rama
# `desarrollo-nivel3`) responde a esta ruta con un objeto
# {rol: [descriptor, ...]} que el cliente aplana antes de
# devolverlo.
PLANTILLA_RUTA_CATALOGO_PROYECTO = "/proyectos/{proyecto}/agentes"

# Métodos JSON-RPC del protocolo A2A relevantes para el cliente.
METODO_TASKS_SEND = "tasks/send"
METODO_TASKS_GET = "tasks/get"
METODO_TASKS_SEND_SUBSCRIBE = "tasks/sendSubscribe"

# Prefijo que identifica los datos de un evento Server-Sent Events
# en la transmisión continua (``tasks/sendSubscribe``). Las líneas que
# empiezan por ``data: `` contienen el cuerpo JSON del evento; el
# resto (líneas en blanco, comentarios ``: `` u otros campos del
# protocolo SSE como ``event:``) se ignoran.
PREFIJO_EVENTO_SSE = "data: "


# Rol que identifica al agente central de un grupo. Cuando se
# agrupan los descriptores devueltos por el registro REST, el
# descriptor cuyo `rol` coincide con este valor se interpreta como
# la Centralita del grupo y su `url_a2a` se promueve al atributo
# ``url_centralita`` del :class:`GrupoDescubierto`.
ROL_CENTRALITA = "centralita"


@dataclass
class GrupoDescubierto:
    """Grupo del aula descubierto a partir del registro REST.

    Reúne los descriptores que el registro devuelve para un mismo
    `id_grupo` y los organiza en una vista cómoda para el lanzador
    del Coordinador:

    - `id_grupo`: identificador del grupo según el campo ``grupo``
      del registro.
    - `url_centralita`: URL del agente con `rol="centralita"`, si lo
      hay; ``None`` si el grupo no expone Centralita pública (caso
      degenerado, normalmente filtrado por el lanzador).
    - `publicos_por_rol`: mapa ``rol → url_a2a`` con los demás
      agentes públicos declarados por el grupo (los dos
      especialistas que ha hecho públicos).
    - `descriptores`: lista cruda de descriptores tal como los
      devolvió el registro, conservada para diagnóstico.
    """

    id_grupo: str
    url_centralita: Optional[str]
    publicos_por_rol: dict[str, str]
    descriptores: list[dict[str, Any]]


@dataclass
class RespuestaTask:
    """Resultado estructurado del envío o consulta de una Task A2A.

    Reúne los campos que el coordinador necesita observar:

    - `task_id`: identificador devuelto por la Centralita.
    - `estado`: estado actual de la Task según el ciclo A2A.
    - `informe`: `InformeResolucion` parseado, si la Task ha
      terminado correctamente.
    - `mensaje_error`: descripción del fallo, si la Task terminó en
      `EstadoTask.FAILED`.
    - `respuesta_cruda`: cuerpo JSON original devuelto por el
      servidor, útil para diagnóstico fino.
    """

    task_id: str
    estado: EstadoTask
    informe: Optional[InformeResolucion] = None
    mensaje_error: Optional[str] = None
    respuesta_cruda: Optional[dict[str, Any]] = None


class ClienteCoordinador:
    """Cliente asíncrono que el coordinador del profesor utiliza para evaluar.

    El cliente recibe en el constructor el cliente HTTP subyacente
    (`httpx.AsyncClient`) para favorecer la inyección de dependencias
    en las pruebas. En entornos reales se construye con un
    `AsyncClient` configurado con tiempos de espera y reintentos
    apropiados; en pruebas unitarias se inyecta un cliente que
    intercepta las peticiones con `respx` u otra biblioteca
    equivalente.
    """

    def __init__(
        self,
        cliente_http: httpx.AsyncClient,
        url_registro: Optional[str] = None,
        nombre_proyecto: str = NOMBRE_PROYECTO_POR_DEFECTO,
    ) -> None:
        """Construye el cliente con un `AsyncClient` ya configurado.

        Args:
            cliente_http: cliente HTTP asíncrono reutilizable.
            url_registro: URL base del registro central. Si se omite,
                las operaciones de descubrimiento que dependen del
                registro lanzan un `ValueError` al ser invocadas.
            nombre_proyecto: identificador del proyecto bajo el que el
                registro REST namespacea los agentes (por defecto
                `villa-olivar`). El registro alberga varios
                proyectos; este parámetro selecciona el suyo.
        """
        self._cliente_http = cliente_http
        self._url_registro = url_registro
        self._nombre_proyecto = nombre_proyecto

    async def leer_agent_card(self, url_base_agente: str) -> AgentCard:
        """Descarga y valida la Agent Card de un agente.

        Args:
            url_base_agente: URL base del agente (sin la ruta
                `/.well-known/agent.json`).

        Returns:
            La Agent Card validada como instancia de `AgentCard`.

        Raises:
            httpx.HTTPStatusError: si el servidor responde con un
                código HTTP de error.
            pydantic.ValidationError: si el JSON devuelto no cumple
                el esquema del contrato.
        """
        url_completa = f"{url_base_agente.rstrip('/')}{RUTA_AGENT_CARD}"
        respuesta = await self._cliente_http.get(url_completa)
        respuesta.raise_for_status()
        agent_card = AgentCard.model_validate(respuesta.json())
        return agent_card

    async def listar_agentes_publicos(self) -> list[dict[str, Any]]:
        """Consulta el catálogo del proyecto y devuelve los agentes públicos.

        El registro REST namespacea los agentes por proyecto y
        responde a ``GET /proyectos/{proyecto}/agentes`` con un
        **objeto** ``{rol: [descriptor, ...]}``. Este método aplana
        ese objeto en una **lista** de descriptores, añadiendo el
        campo ``rol`` a los que no lo traen ya (el rol viene
        implícito en la clave de la categoría).

        Returns:
            Lista de descriptores con, al menos, los campos
            ``id``, ``grupo``, ``rol``, ``url_a2a`` y
            ``url_agent_card`` (formato documentado en
            ``doc/registro_rest_para_clientes.md`` de la rama
            `desarrollo-nivel3`).

        Raises:
            ValueError: si el cliente se construyó sin URL de registro.
            httpx.HTTPStatusError: si el registro responde con error.
        """
        url_registro = self._exigir_url_registro()
        ruta = PLANTILLA_RUTA_CATALOGO_PROYECTO.format(
            proyecto=self._nombre_proyecto,
        )
        url_completa = f"{url_registro.rstrip('/')}{ruta}"
        respuesta = await self._cliente_http.get(url_completa)
        respuesta.raise_for_status()
        catalogo = respuesta.json()
        descriptores = _aplanar_catalogo_por_rol(catalogo)
        return descriptores

    async def descubrir_grupos(self) -> list[GrupoDescubierto]:
        """Consulta el registro y devuelve un :class:`GrupoDescubierto` por grupo.

        Es el método que el lanzador del Coordinador usa para
        decidir contra qué grupos se ejecutará la batería el día
        del examen: el aula es exactamente la lista de grupos
        publicada por el registro REST en el instante de la
        invocación.

        Si el registro responde con la lista vacía (no hay grupos
        inscritos), este método devuelve también la lista vacía.
        Es responsabilidad del lanzador interpretar ese caso como
        «no hay grupos a los que evaluar»; no se trata como un
        error: simplemente no hay nada que medir.

        Returns:
            Lista de :class:`GrupoDescubierto` ordenada por
            `id_grupo` para que la salida sea reproducible entre
            ejecuciones. Los descriptores del registro que no
            traen campo `grupo` se descartan silenciosamente.

        Raises:
            ValueError: si el cliente se construyó sin URL de registro.
            httpx.HTTPStatusError: si el registro responde con error.
        """
        descriptores = await self.listar_agentes_publicos()
        grupos = agrupar_descriptores_por_grupo(descriptores)
        return grupos

    async def enviar_alerta(
        self,
        url_centralita: str,
        alerta: AlertaEmergencia,
        identificador_task: str,
    ) -> RespuestaTask:
        """Envía una alerta de emergencia a la Centralita y espera la respuesta.

        Construye una petición JSON-RPC con el método `tasks/send` y
        un `DataPart` que contiene la alerta serializada. La
        respuesta se traduce a un `RespuestaTask` con el estado y,
        cuando procede, el `InformeResolucion` parseado.

        Args:
            url_centralita: URL base de la Centralita destino.
            alerta: alerta de emergencia ya validada.
            identificador_task: identificador único que el coordinador
                asigna a la Task. Se usa para correlacionar peticiones
                y respuestas en lotes concurrentes.

        Returns:
            Resultado estructurado de la operación.
        """
        peticion = self._construir_peticion_jsonrpc(
            metodo=METODO_TASKS_SEND,
            parametros={
                "id": identificador_task,
                "message": {
                    "role": "user",
                    "parts": [
                        {"type": "data", "data": alerta.model_dump(mode="json")},
                    ],
                },
            },
            id_peticion=identificador_task,
        )
        respuesta = await self._cliente_http.post(url_centralita.rstrip("/"), json=peticion)
        respuesta.raise_for_status()
        respuesta_estructurada = self._procesar_respuesta_task(respuesta.json())
        return respuesta_estructurada

    async def enviar_alerta_streaming(
        self,
        url_centralita: str,
        alerta: AlertaEmergencia,
        identificador_task: str,
    ) -> AsyncIterator[dict[str, Any]]:
        """Envía una alerta con ``tasks/sendSubscribe`` y produce los eventos SSE.

        El método A2A ``tasks/sendSubscribe`` abre una respuesta
        Server-Sent Events que entrega eventos intermedios (estados
        ``working`` con artefactos parciales) durante el procesado de
        la Task, no solo el evento final ``completed``. El generador
        asíncrono retorna cada evento como un diccionario tras
        deserializar su cuerpo JSON. Se ignoran las líneas SSE que no
        comienzan con ``data: `` (eventos de control, comentarios y
        líneas en blanco que actúan como separadores).

        Args:
            url_centralita: URL base de la Centralita destino.
            alerta: alerta de emergencia ya validada.
            identificador_task: identificador único de la Task.

        Yields:
            Cada evento SSE recibido del servidor, deserializado
            como diccionario.

        Raises:
            httpx.HTTPStatusError: si el servidor responde con un
                código HTTP de error al iniciar la suscripción.
        """
        peticion = self._construir_peticion_jsonrpc(
            metodo=METODO_TASKS_SEND_SUBSCRIBE,
            parametros={
                "id": identificador_task,
                "message": {
                    "role": "user",
                    "parts": [
                        {"type": "data", "data": alerta.model_dump(mode="json")},
                    ],
                },
            },
            id_peticion=identificador_task,
        )
        async with self._cliente_http.stream(
            "POST",
            url_centralita.rstrip("/"),
            json=peticion,
            headers={"Accept": "text/event-stream"},
        ) as respuesta:
            respuesta.raise_for_status()
            async for linea in respuesta.aiter_lines():
                if linea.startswith(PREFIJO_EVENTO_SSE):
                    cuerpo_evento = linea[len(PREFIJO_EVENTO_SSE):].strip()
                    if cuerpo_evento:
                        evento = json.loads(cuerpo_evento)
                        yield evento

    async def consultar_task(self, url_centralita: str, identificador_task: str) -> RespuestaTask:
        """Consulta el estado actual de una Task ya enviada.

        Args:
            url_centralita: URL base de la Centralita destino.
            identificador_task: identificador devuelto por la
                Centralita al enviar la Task original.

        Returns:
            Resultado estructurado con el estado actual y, si
            procede, el `InformeResolucion`.
        """
        peticion = self._construir_peticion_jsonrpc(
            metodo=METODO_TASKS_GET,
            parametros={"id": identificador_task},
            id_peticion=identificador_task,
        )
        respuesta = await self._cliente_http.post(url_centralita.rstrip("/"), json=peticion)
        respuesta.raise_for_status()
        respuesta_estructurada = self._procesar_respuesta_task(respuesta.json())
        return respuesta_estructurada

    def _construir_peticion_jsonrpc(
        self,
        metodo: str,
        parametros: dict[str, Any],
        id_peticion: str,
    ) -> dict[str, Any]:
        """Compone el sobre JSON-RPC 2.0 común a todas las peticiones A2A."""
        peticion = {
            "jsonrpc": VERSION_JSON_RPC,
            "method": metodo,
            "params": parametros,
            "id": id_peticion,
        }
        return peticion

    def _procesar_respuesta_task(self, cuerpo: dict[str, Any]) -> RespuestaTask:
        """Convierte un cuerpo JSON-RPC en una `RespuestaTask` estructurada."""
        resultado = cuerpo.get("result", {})
        task_id = resultado.get("id", "")
        estado_textual = resultado.get("status", {}).get("state", EstadoTask.SUBMITTED.value)
        estado = EstadoTask(estado_textual)
        informe = self._extraer_informe(resultado) if estado == EstadoTask.COMPLETED else None
        mensaje_error = self._extraer_mensaje_error(resultado) if estado == EstadoTask.FAILED else None
        respuesta = RespuestaTask(
            task_id=task_id,
            estado=estado,
            informe=informe,
            mensaje_error=mensaje_error,
            respuesta_cruda=cuerpo,
        )
        return respuesta

    def _extraer_informe(self, resultado: dict[str, Any]) -> Optional[InformeResolucion]:
        """Localiza el `InformeResolucion` en el cuerpo de respuesta.

        El protocolo A2A admite el resultado dentro de varias formas
        (`artifacts`, `message.parts`...); aquí se busca el primer
        `DataPart` que contenga el campo `tipo_emergencia`, marca
        distintiva del informe.
        """
        partes = self._recolectar_partes_de_datos(resultado)
        candidato = next(
            (parte for parte in partes if isinstance(parte, dict) and "tipo_emergencia" in parte),
            None,
        )
        informe = InformeResolucion.model_validate(candidato) if candidato is not None else None
        return informe

    def _extraer_mensaje_error(self, resultado: dict[str, Any]) -> Optional[str]:
        """Localiza el mensaje de error asociado a una Task `failed`."""
        estado = resultado.get("status", {})
        mensaje = estado.get("message")
        return mensaje

    def _recolectar_partes_de_datos(self, resultado: dict[str, Any]) -> list[Any]:
        """Devuelve todos los `DataPart.data` presentes en la respuesta."""
        artefactos = resultado.get("artifacts", [])
        mensaje = resultado.get("message", {})
        partes_mensaje = mensaje.get("parts", []) if isinstance(mensaje, dict) else []
        partes_artefactos = [
            parte
            for artefacto in artefactos
            if isinstance(artefacto, dict)
            for parte in artefacto.get("parts", [])
        ]
        partes_brutas = [*partes_mensaje, *partes_artefactos]
        datos = [
            parte.get("data")
            for parte in partes_brutas
            if isinstance(parte, dict) and parte.get("type") == "data"
        ]
        return datos

    def _exigir_url_registro(self) -> str:
        """Devuelve la URL del registro o lanza un error si no se configuró."""
        if self._url_registro is None:
            raise ValueError(
                "El cliente no se ha configurado con una URL de registro central; "
                "no se pueden realizar operaciones de descubrimiento.",
            )
        return self._url_registro


def _aplanar_catalogo_por_rol(catalogo: Any) -> list[dict[str, Any]]:
    """Convierte ``{rol: [descriptor, ...]}`` en una lista plana.

    El registro REST de Villa Olivar devuelve los agentes públicos
    de un proyecto agrupados por rol. El cliente prefiere trabajar
    con una lista plana, así que esta función pura aplana la
    estructura y añade el campo ``rol`` a los descriptores que no
    lo traen ya (rol implícito en la clave de la categoría).

    Tolera respuestas mal formadas: descriptores que no son
    diccionarios se descartan; categorías cuya lista no es
    iterable se ignoran. Devuelve siempre una lista (posiblemente
    vacía), nunca lanza por estructura inesperada.
    """
    descriptores: list[dict[str, Any]] = []
    if not isinstance(catalogo, dict):
        return descriptores
    for rol, inscripciones in catalogo.items():
        if not isinstance(inscripciones, list):
            continue
        for descriptor in inscripciones:
            if not isinstance(descriptor, dict):
                continue
            enriquecido = dict(descriptor)
            enriquecido.setdefault("rol", rol)
            descriptores.append(enriquecido)
    return descriptores


def agrupar_descriptores_por_grupo(
    descriptores: list[dict[str, Any]],
) -> list[GrupoDescubierto]:
    """Agrupa los descriptores devueltos por el registro por ``grupo``.

    Función pura (sin red ni estado): facilita las pruebas
    unitarias del cliente sin necesidad de levantar un servidor.

    Para cada `id_grupo` distinto en la lista de entrada construye
    un :class:`GrupoDescubierto` con:

    - La URL del agente cuyo `rol` coincide con
      :data:`ROL_CENTRALITA` (si lo hay).
    - Un mapa ``rol → url_a2a`` con los demás agentes públicos.
    - La lista cruda de descriptores conservada para diagnóstico.

    Los descriptores que carecen de campo `grupo` o cuyo `grupo`
    es la cadena vacía se ignoran. Los grupos del resultado se
    devuelven ordenados alfabéticamente por `id_grupo` para que la
    salida sea reproducible.
    """
    descriptores_por_grupo: dict[str, list[dict[str, Any]]] = {}
    for descriptor in descriptores:
        if not isinstance(descriptor, dict):
            continue
        id_grupo = descriptor.get("grupo")
        if not isinstance(id_grupo, str) or not id_grupo:
            continue
        descriptores_por_grupo.setdefault(id_grupo, []).append(descriptor)

    grupos: list[GrupoDescubierto] = []
    for id_grupo in sorted(descriptores_por_grupo.keys()):
        descriptores_grupo = descriptores_por_grupo[id_grupo]
        url_centralita: Optional[str] = next(
            (
                d.get("url_a2a")
                for d in descriptores_grupo
                if d.get("rol") == ROL_CENTRALITA and d.get("url_a2a")
            ),
            None,
        )
        publicos_por_rol: dict[str, str] = {
            d["rol"]: d["url_a2a"]
            for d in descriptores_grupo
            if d.get("rol") != ROL_CENTRALITA
            and isinstance(d.get("rol"), str)
            and isinstance(d.get("url_a2a"), str)
        }
        grupos.append(
            GrupoDescubierto(
                id_grupo=id_grupo,
                url_centralita=url_centralita,
                publicos_por_rol=publicos_por_rol,
                descriptores=list(descriptores_grupo),
            ),
        )
    return grupos
