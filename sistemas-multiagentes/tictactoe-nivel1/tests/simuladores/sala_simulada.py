"""Sala MUC simulada en memoria para las pruebas de protocolo.

El examen real transcurre dentro de una sala MUC del servidor
XMPP de la asignatura. Para poder verificar los agentes del
alumno **sin** levantar ningún servidor, este módulo reproduce en
memoria el comportamiento esencial de esa sala:

* difunde los mensajes ``groupchat`` a todos los ocupantes salvo
  al emisor (un servidor MUC real tampoco devuelve al emisor su
  propia difusión);
* entrega los mensajes privados (``sala@servicio/nick``) solo al
  ocupante indicado;
* fija el remitente de cada mensaje entregado como
  ``sala@servicio/nick_emisor``, igual que hace un servidor MUC;
* registra todo el tráfico en un histórico consultable, con cada
  cuerpo ya validado contra la ontología, para que las pruebas
  comprueben la conformidad del protocolo paso a paso.

El enrutado respeta el ``Template`` de cada comportamiento: un
mensaje solo entra en la cola de un comportamiento si su metadata
encaja con la plantilla (o si el comportamiento no declaró
ninguna). Así se reproduce el mismo emparejado por plantilla que
usa SPADE cuando un agente registra varios comportamientos.
"""
import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Optional

from ontologia.ontologia import validar_cuerpo


# ── Presencias MUC simuladas ───────────────────────────────────

class _PresenciaSimulada:
    """Stanza de presencia simulada con la interfaz mínima de ``slixmpp``.

    El alumno puede descubrir tableros (u otros ocupantes) mediante
    los eventos del plugin XEP-0045 de slixmpp
    (``muc::<sala>::got_online``, ``muc::<sala>::presence``,
    ``muc::<sala>::got_offline``) o mediante el evento genérico
    ``presence``. Esta clase reproduce el acceso por clave
    (``presencia["from"]``, ``presencia["type"]``,
    ``presencia["status"]``) que esos handlers reciben, de modo que
    el código que el alumno escriba en producción contra slixmpp
    funcione sin cambios sobre la sala simulada.
    """

    def __init__(
        self, from_jid: str, tipo: str, status: str,
    ) -> None:
        self._campos = {
            "from": from_jid,
            "type": tipo,
            "status": status,
        }

    def __getitem__(self, clave: str) -> str:
        return self._campos.get(clave, "")

    def get(self, clave: str, valor_defecto: str = "") -> str:
        return self._campos.get(clave, valor_defecto)


@dataclass
class RegistroMensaje:
    """Una entrada del histórico de la sala simulada.

    Reúne, ya desglosado, todo lo que una prueba necesita para
    comprobar un mensaje del protocolo sin volver a interpretar el
    cuerpo JSON ni la metadata.
    """

    emisor: str
    destino: str
    performativa: str
    conversacion: str
    thread: Optional[str]
    accion: str
    cuerpo: dict[str, Any]
    valido: bool
    errores: list[str] = field(default_factory=list)


class MensajeEntrante:
    """Mensaje tal y como lo recibe un agente dentro de la sala.

    Expone la superficie mínima que usan los agentes al recibir:
    ``body``, ``sender``, ``thread`` y ``get_metadata``. Coincide
    con la de un ``spade.message.Message`` para que el código del
    agente no distinga si se ejecuta contra la sala simulada o
    contra un servidor real.
    """

    def __init__(
        self,
        body: str,
        sender: str,
        thread: Optional[str],
        metadata: dict[str, str],
    ) -> None:
        self.body = body
        self.sender = sender
        self.thread = thread
        self.metadata = dict(metadata)

    def get_metadata(self, clave: str) -> Optional[str]:
        """Devuelve el valor de una clave de metadata, o ``None``."""
        return self.metadata.get(clave)

    def make_reply(self) -> Any:
        """Construye un mensaje de respuesta dirigido al emisor.

        Reproduce ``spade.message.Message.make_reply``: la respuesta
        se dirige al ocupante que envió este mensaje —su JID de sala
        ``sala@servicio/nick``— y hereda el ``thread`` y la metadata.
        Se devuelve un ``spade.message.Message`` real, de modo que el
        agente pueda fijarle ``body`` y metadata y enviarlo igual que
        contra un servidor XMPP real.
        """
        from spade.message import Message
        respuesta = Message(to=str(self.sender))
        respuesta.thread = self.thread
        for clave, valor in self.metadata.items():
            respuesta.set_metadata(clave, valor)
        return respuesta


class Conexion:
    """Enlace de un comportamiento concreto con la sala simulada.

    Cada comportamiento de un agente obtiene su propia conexión, con
    una cola de entrada independiente. Las funciones :meth:`send` y
    :meth:`receive` se enchufan al comportamiento en sustitución de
    las de SPADE.
    """

    def __init__(
        self, sala: "SalaSimulada", nick: str, plantilla: Any,
    ) -> None:
        self.sala = sala
        self.nick = nick
        self.plantilla = plantilla
        self.buzon: asyncio.Queue = asyncio.Queue()

    async def send(self, mensaje: Any) -> None:
        """Entrega ``mensaje`` a la sala en nombre de este ocupante."""
        self.sala.entregar(mensaje, self.nick)

    async def receive(
        self, timeout: Optional[float] = None,
    ) -> Optional[MensajeEntrante]:
        """Espera un mensaje de la cola, o ``None`` si vence el plazo."""
        try:
            recibido = await asyncio.wait_for(self.buzon.get(), timeout)
        except asyncio.TimeoutError:
            recibido = None
        return recibido

    def acepta(self, mensaje: MensajeEntrante) -> bool:
        """Indica si el mensaje encaja con la plantilla del comportamiento."""
        return _plantilla_coincide(self.plantilla, mensaje)


class SalaSimulada:
    """Sala MUC en memoria para las pruebas de protocolo.

    Además del enrutado de mensajes (privados y de difusión), la
    sala reproduce el subsistema de presencias del componente MUC
    real. Los agentes del alumno pueden descubrir ocupantes —en
    particular tableros disponibles— enganchándose a los eventos
    de slixmpp ``presence``, ``muc::<sala>::presence``,
    ``muc::<sala>::got_online`` o ``muc::<sala>::got_offline`` con
    ``self.client.add_event_handler(...)``. La sala dispara esos
    handlers a través del cliente doble que el arnés registra en
    cada agente, de modo que el alumno no necesita ningún punto de
    integración con el simulador para descubrir tableros: usa el
    mismo mecanismo de slixmpp que utilizaría en producción.

    Las pruebas que necesiten anunciar un tablero simulado en la
    sala disponen del helper
    :func:`tests.simuladores.arnes.anunciar_tablero_descubierto`,
    que internamente invoca :meth:`propagar_presencia` para emitir
    una stanza con ``status="waiting"``.
    """

    def __init__(self, jid_sala: str) -> None:
        self.jid_sala = jid_sala
        self.conexiones: list[Conexion] = []
        self.historico: list[RegistroMensaje] = []
        # Clientes XMPP (mockeados por el arnés) de los agentes del
        # alumno registrados en la sala. La clave es el nick MUC.
        self._clientes_por_nick: dict[str, Any] = {}
        # Último status conocido por nick, para no replicar
        # presencias que no aportan cambio.
        self._status_por_nick: dict[str, str] = {}

    def conectar(self, nick: str, plantilla: Any = None) -> Conexion:
        """Da de alta un comportamiento como ocupante de la sala.

        Args:
            nick: Nick del ocupante en la sala.
            plantilla: ``Template`` de SPADE que filtra qué mensajes
                recibe este comportamiento, o ``None`` para recibir
                todos los dirigidos a su nick o difundidos.

        Returns:
            La conexión con las funciones ``send`` y ``receive``.
        """
        conexion = Conexion(self, nick, plantilla)
        self.conexiones.append(conexion)
        return conexion

    def registrar_cliente_agente(
        self, nick: str, cliente: Any,
        status_inicial: str = "",
    ) -> None:
        """Registra el cliente XMPP de un agente real montado.

        El arnés invoca este método al montar cada agente del
        alumno (después de su ``setup()``), de modo que las
        presencias propagadas por la sala lleguen a los handlers
        que el agente haya registrado con
        ``self.client.add_event_handler(...)``. El cliente es el
        doble mockeado por :func:`_crear_cliente_doble`.

        Reproduce el **snapshot inicial** del servidor MUC real:
        cuando un agente se une a la sala, el servidor le envía la
        presencia de cada ocupante ya presente. Aquí se hace lo
        mismo: tras registrar el cliente, se le entregan las
        presencias de los ocupantes anteriores; después se anuncia
        la presencia del recién llegado a los demás.

        Args:
            nick: Nick del ocupante.
            cliente: Doble de prueba del cliente XMPP del agente,
                con un atributo ``_handlers`` que mantiene los
                callbacks registrados por evento.
            status_inicial: ``<status>`` con el que el ocupante se
                anuncia (``"waiting"`` para un tablero,
                cadena vacía para un jugador).
        """
        if nick in self._clientes_por_nick:
            return
        # Snapshot inicial: entrega al nuevo cliente las presencias
        # ``available`` de los ocupantes ya presentes en la sala.
        previos = [
            (nick_previo, self._status_por_nick.get(nick_previo, ""))
            for nick_previo in self._clientes_por_nick.keys()
        ]
        self._clientes_por_nick[nick] = cliente
        self._status_por_nick[nick] = status_inicial
        for nick_previo, status_previo in previos:
            self._disparar_presencia(
                cliente_destino=cliente,
                nick_emisor=nick_previo,
                tipo="available",
                status=status_previo,
                es_primera_vez=True,
            )
        # Anuncia al nuevo ocupante a los demás clientes
        # registrados, simulando el broadcast que un servidor MUC
        # real hace en la unión de un usuario a la sala.
        self.propagar_presencia(nick, tipo="available", status=status_inicial)

    def propagar_presencia(
        self, nick: str, tipo: str = "available", status: str = "",
    ) -> None:
        """Anuncia una presencia MUC a los demás ocupantes.

        Dispara los eventos del plugin XEP-0045 de slixmpp en cada
        cliente registrado distinto del emisor:
        ``presence``, ``muc::<sala>::presence`` y, según el caso,
        ``muc::<sala>::got_online`` (al unirse o reaparecer) o
        ``muc::<sala>::got_offline`` (al marcharse). El alumno usa
        los handlers de slixmpp que considere oportunos.

        Args:
            nick: Nick del ocupante cuya presencia se anuncia.
            tipo: Tipo de la stanza (``"available"`` o
                ``"unavailable"``).
            status: Texto del ``<status>`` de la presencia
                (``"waiting"``, ``"playing"``, ``"finished"``…).
        """
        es_primera_vez = nick not in self._status_por_nick
        self._status_por_nick[nick] = status
        for nick_destino, cliente in self._clientes_por_nick.items():
            if nick_destino == nick:
                continue
            self._disparar_presencia(
                cliente_destino=cliente,
                nick_emisor=nick,
                tipo=tipo,
                status=status,
                es_primera_vez=es_primera_vez,
            )

    def _disparar_presencia(
        self, cliente_destino: Any, nick_emisor: str,
        tipo: str, status: str, es_primera_vez: bool,
    ) -> None:
        """Dispara los handlers MUC de un cliente con una presencia."""
        presencia = _PresenciaSimulada(
            from_jid=f"{self.jid_sala}/{nick_emisor}",
            tipo=tipo, status=status,
        )
        eventos: list[str] = [
            "presence",
            f"muc::{self.jid_sala}::presence",
        ]
        if tipo == "unavailable":
            eventos.append(f"muc::{self.jid_sala}::got_offline")
        elif es_primera_vez:
            eventos.append(f"muc::{self.jid_sala}::got_online")
        handlers = getattr(cliente_destino, "_handlers", {}) or {}
        for evento in eventos:
            for callback in list(handlers.get(evento, [])):
                callback(presencia)

    def entregar(self, mensaje_saliente: Any, nick_emisor: str) -> None:
        """Distribuye un mensaje a los ocupantes que correspondan.

        Args:
            mensaje_saliente: ``Message`` de SPADE construido por el
                agente emisor.
            nick_emisor: Nick del ocupante que lo envía.
        """
        destino = str(mensaje_saliente.to)
        cuerpo_texto = mensaje_saliente.body or ""
        thread = mensaje_saliente.thread
        metadata = dict(getattr(mensaje_saliente, "metadata", {}) or {})

        es_privado = "/" in destino
        nick_destino = destino.split("/", 1)[1] if es_privado else ""

        self._anotar_historico(
            nick_emisor,
            nick_destino if es_privado else "difusion",
            cuerpo_texto, thread, metadata,
        )

        for conexion in self.conexiones:
            if conexion.nick == nick_emisor:
                continue
            if es_privado and conexion.nick != nick_destino:
                continue
            entrante = MensajeEntrante(
                cuerpo_texto,
                f"{self.jid_sala}/{nick_emisor}",
                thread,
                metadata,
            )
            if conexion.acepta(entrante):
                conexion.buzon.put_nowait(entrante)

    def _anotar_historico(
        self,
        emisor: str,
        destino: str,
        cuerpo_texto: str,
        thread: Optional[str],
        metadata: dict[str, str],
    ) -> None:
        """Registra un mensaje en el histórico, ya validado."""
        cuerpo = _decodificar(cuerpo_texto)
        validacion = validar_cuerpo(cuerpo) if cuerpo else {
            "valido": False, "errores": ["El cuerpo no es un objeto JSON"],
        }
        self.historico.append(RegistroMensaje(
            emisor=emisor,
            destino=destino,
            performativa=metadata.get("performative", ""),
            conversacion=metadata.get("conversation-id", ""),
            thread=thread,
            accion=str(cuerpo.get("action", "")),
            cuerpo=cuerpo,
            valido=bool(validacion["valido"]),
            errores=list(validacion["errores"]),
        ))

    def buscar(
        self,
        *,
        accion: Optional[str] = None,
        emisor: Optional[str] = None,
        performativa: Optional[str] = None,
    ) -> list[RegistroMensaje]:
        """Filtra el histórico por acción, emisor o performativa.

        Cualquier criterio que sea ``None`` no filtra. Es la forma
        cómoda de que una prueba localice los mensajes de una fase
        concreta del protocolo.

        Args:
            accion: Valor del campo ``action`` del cuerpo.
            emisor: Nick del ocupante emisor.
            performativa: Performativa FIPA-ACL del mensaje.

        Returns:
            Lista de registros que cumplen todos los criterios
            dados, en orden de envío.
        """
        seleccion = [
            registro for registro in self.historico
            if (accion is None or registro.accion == accion)
            and (emisor is None or registro.emisor == emisor)
            and (performativa is None or registro.performativa == performativa)
        ]
        return seleccion


# ── Funciones auxiliares ───────────────────────────────────────

def _decodificar(cuerpo_texto: str) -> dict[str, Any]:
    """Interpreta un cuerpo de mensaje como diccionario JSON."""
    cuerpo: dict[str, Any] = {}
    if cuerpo_texto:
        try:
            datos = json.loads(cuerpo_texto)
        except (json.JSONDecodeError, TypeError):
            datos = None
        if isinstance(datos, dict):
            cuerpo = datos
    return cuerpo


def _plantilla_coincide(plantilla: Any, mensaje: MensajeEntrante) -> bool:
    """Indica si un mensaje encaja con la plantilla de un comportamiento.

    Reproduce, de forma simplificada, el emparejado por ``Template``
    de SPADE: un comportamiento sin plantilla recibe todo lo que le
    llega; con plantilla, el mensaje debe coincidir en toda la
    metadata declarada (``performative``, ``conversation-id``,
    ``ontology``…) y en el ``thread`` si la plantilla lo fija.

    Args:
        plantilla: ``Template`` de SPADE, o ``None``.
        mensaje: Mensaje entrante candidato.

    Returns:
        ``True`` si el comportamiento debe recibir el mensaje.
    """
    if plantilla is None:
        coincide = True
    else:
        requisitos = dict(getattr(plantilla, "metadata", {}) or {})
        coincide = all(
            mensaje.get_metadata(clave) == valor
            for clave, valor in requisitos.items()
        )
        thread_plantilla = getattr(plantilla, "thread", None)
        if coincide and thread_plantilla is not None:
            coincide = mensaje.thread == thread_plantilla
    return coincide
