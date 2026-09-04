"""Autómata de seguimiento de incidentes del supervisor.

Cada vez que el supervisor inyecta un incidente a un grupo, crea una
instancia de ``Seguimiento`` que avanza por un autómata determinista.
Esta pieza es la columna vertebral del estado del agente y vive en su
propio módulo para poder probarse de forma aislada (tests puros, sin
SPADE ni red).

Estados (terminales en mayúsculas, transitorios en negrita):

- ``PREPARADO``  → ``ENVIADO``  → ``ACEPTADO``  → ``RESUELTO``  (OK)
                              ↘  ``RECHAZADO``                   (KO)
                              ↘  ``TIMEOUT``                     (KO)
                              ↘  ``FALLIDO``                     (KO)

Cada transición queda registrada con marca temporal para que la
interfaz web pueda mostrar la línea de tiempo del seguimiento.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ─── Constantes simbólicas ──────────────────────────────────────────────────

TIMEOUT_AGREE_DEFECTO = 5.0
TIMEOUT_INFORME_DEFECTO = 90.0


# ─── Enumeración de estados del autómata ────────────────────────────────────

class EstadoSeguimiento(str, Enum):
    """Estados posibles del seguimiento de un incidente.

    Los valores se almacenan como cadenas en mayúsculas para que se
    serialicen tal cual en la API JSON del dashboard.
    """
    PREPARADO = "PREPARADO"
    ENVIADO = "ENVIADO"
    ACEPTADO = "ACEPTADO"
    RESUELTO = "RESUELTO"
    RECHAZADO = "RECHAZADO"
    TIMEOUT = "TIMEOUT"
    FALLIDO = "FALLIDO"


# Conjunto de estados terminales (no admiten más transiciones)
ESTADOS_TERMINALES: frozenset[EstadoSeguimiento] = frozenset({
    EstadoSeguimiento.RESUELTO,
    EstadoSeguimiento.RECHAZADO,
    EstadoSeguimiento.TIMEOUT,
    EstadoSeguimiento.FALLIDO,
})

# Estados terminales considerados "OK" para los resúmenes
ESTADOS_OK: frozenset[EstadoSeguimiento] = frozenset({
    EstadoSeguimiento.RESUELTO,
})


# ─── Línea de tiempo del seguimiento ────────────────────────────────────────

@dataclass
class EventoTimeline:
    """Una entrada de la línea de tiempo de un seguimiento.

    Cada transición de estado y cada mensaje XMPP relevante se
    registra como un evento con marca temporal absoluta. La interfaz
    web los muestra en el detalle de cada incidente.
    """
    instante: datetime
    tipo: str
    detalle: str

    def a_dict(self) -> dict:
        """Serializa el evento para enviarlo al dashboard."""
        resultado = {
            "instante": self.instante.isoformat(),
            "tipo": self.tipo,
            "detalle": self.detalle,
        }
        return resultado


# ─── Seguimiento — pieza central del autómata ───────────────────────────────

@dataclass
class Seguimiento:
    """Estado de un incidente inyectado por el supervisor.

    Atributos:
        id_emergencia: UUID v4 generado por el supervisor.
        grupo: Etiqueta legible del grupo destino (no el JID completo).
        jid_destino: JID de la Centralita del grupo.
        tipo_emergencia: Tipo del incidente (``incendio``, ``inundacion``,
            ...).
        prioridad: Prioridad del incidente.
        descripcion: Descripción breve para mostrar en la tabla.
        estado: Estado actual del autómata.
        instante_envio: Instante en que se envió el ``request``.
        instante_agree: Instante en que se recibió el ``agree`` (o
            ``None`` si aún no llegó).
        instante_informe: Instante en que se recibió el ``inform`` (o
            ``None`` si aún no llegó).
        informe: Cuerpo del ``InformeResolucion`` recibido como dict
            serializable, o ``None``.
        error: Descripción del error si el estado terminal es
            ``FALLIDO`` o ``TIMEOUT``. ``None`` si no hubo error.
        eventos: Línea de tiempo del seguimiento.
    """

    id_emergencia: str
    grupo: str
    jid_destino: str
    tipo_emergencia: str
    prioridad: str
    descripcion: str
    estado: EstadoSeguimiento = EstadoSeguimiento.PREPARADO
    instante_creacion: datetime = field(default_factory=datetime.now)
    instante_envio: Optional[datetime] = None
    instante_agree: Optional[datetime] = None
    instante_informe: Optional[datetime] = None
    informe: Optional[dict] = None
    error: Optional[str] = None
    eventos: list[EventoTimeline] = field(default_factory=list)

    # ── Transiciones del autómata ───────────────────────────────────────

    def transicionar(
        self, nuevo_estado: EstadoSeguimiento, detalle: str = "",
    ) -> bool:
        """Aplica una transición al autómata.

        Returns:
            ``True`` si la transición se aplicó, ``False`` si era
            inválida (estado terminal o transición no permitida).
        """
        permitida = self.estado not in ESTADOS_TERMINALES \
            and self._transicion_es_valida(nuevo_estado)

        if permitida:
            self.estado = nuevo_estado
            self._registrar(f"estado:{nuevo_estado.value}", detalle)

        return permitida

    def _transicion_es_valida(
        self, destino: EstadoSeguimiento,
    ) -> bool:
        """Comprueba si una transición concreta está permitida.

        El autómata es lineal con tres ramas terminales: desde
        cualquier estado transitorio se puede ir a un terminal de
        error; desde ``ACEPTADO`` se puede además ir a ``RESUELTO``.
        """
        permitida = False

        if self.estado == EstadoSeguimiento.PREPARADO:
            permitida = destino in {
                EstadoSeguimiento.ENVIADO,
                EstadoSeguimiento.TIMEOUT,
                EstadoSeguimiento.RECHAZADO,
                EstadoSeguimiento.FALLIDO,
            }
        elif self.estado == EstadoSeguimiento.ENVIADO:
            permitida = destino in {
                EstadoSeguimiento.ACEPTADO,
                EstadoSeguimiento.RECHAZADO,
                EstadoSeguimiento.TIMEOUT,
                EstadoSeguimiento.FALLIDO,
            }
        elif self.estado == EstadoSeguimiento.ACEPTADO:
            permitida = destino in {
                EstadoSeguimiento.RESUELTO,
                EstadoSeguimiento.RECHAZADO,
                EstadoSeguimiento.TIMEOUT,
                EstadoSeguimiento.FALLIDO,
            }

        return permitida

    def registrar_envio(self) -> None:
        """Marca el instante de envío del ``request`` y transiciona."""
        self.instante_envio = datetime.now()
        self.transicionar(
            EstadoSeguimiento.ENVIADO,
            "request enviado a la Centralita",
        )

    def registrar_agree(self) -> None:
        """Marca el instante en que se recibió el ``agree``."""
        self.instante_agree = datetime.now()
        self.transicionar(
            EstadoSeguimiento.ACEPTADO,
            "agree recibido dentro de plazo",
        )

    def registrar_informe(self, informe: dict) -> None:
        """Marca el instante en que se recibió el ``inform`` válido."""
        self.instante_informe = datetime.now()
        self.informe = informe
        self.transicionar(
            EstadoSeguimiento.RESUELTO,
            "InformeResolucion válido recibido",
        )

    def registrar_error(
        self, estado_destino: EstadoSeguimiento, mensaje: str,
    ) -> None:
        """Lleva el seguimiento a un estado terminal de error."""
        self.error = mensaje
        self.transicionar(estado_destino, mensaje)

    def _registrar(self, tipo: str, detalle: str) -> None:
        """Añade una entrada a la línea de tiempo."""
        evento = EventoTimeline(
            instante=datetime.now(),
            tipo=tipo,
            detalle=detalle,
        )
        self.eventos.append(evento)

    # ── Métricas derivadas ──────────────────────────────────────────────

    def latencia_agree_ms(self) -> Optional[int]:
        """Tiempo en milisegundos entre el envío y el ``agree``.

        Returns:
            Latencia en ms, o ``None`` si aún no se ha recibido el
            ``agree``.
        """
        resultado: Optional[int] = None
        if self.instante_envio is not None \
                and self.instante_agree is not None:
            delta = self.instante_agree - self.instante_envio
            resultado = int(delta.total_seconds() * 1000)
        return resultado

    def latencia_informe_ms(self) -> Optional[int]:
        """Tiempo en milisegundos entre el ``agree`` y el ``inform``."""
        resultado: Optional[int] = None
        if self.instante_agree is not None \
                and self.instante_informe is not None:
            delta = self.instante_informe - self.instante_agree
            resultado = int(delta.total_seconds() * 1000)
        return resultado

    def es_terminal(self) -> bool:
        """¿El seguimiento ha alcanzado un estado terminal?"""
        resultado = self.estado in ESTADOS_TERMINALES
        return resultado

    # ── Serialización para la API JSON del dashboard ────────────────────

    def a_dict(self) -> dict:
        """Serializa el seguimiento al esquema público del dashboard.

        El esquema coincide con el documentado en
        ``docs/agente_profesor/caracteristicas_para_tests_grupo.md``
        (sección 7.6) para que los tests del grupo puedan consumirlo
        sin acoplarse a detalles internos.
        """
        resultado = {
            "id_emergencia": self.id_emergencia,
            "grupo": self.grupo,
            "jid_destino": self.jid_destino,
            "estado": self.estado.value,
            "tipo_emergencia": self.tipo_emergencia,
            "prioridad": self.prioridad,
            "descripcion": self.descripcion,
            "instante_creacion": self.instante_creacion.isoformat(),
            "instante_envio": self.instante_envio.isoformat()
                if self.instante_envio is not None else None,
            "instante_agree": self.instante_agree.isoformat()
                if self.instante_agree is not None else None,
            "instante_informe": self.instante_informe.isoformat()
                if self.instante_informe is not None else None,
            "latencia_agree_ms": self.latencia_agree_ms(),
            "latencia_informe_ms": self.latencia_informe_ms(),
            "informe": self.informe,
            "error": self.error,
            "eventos": [e.a_dict() for e in self.eventos],
        }
        return resultado
