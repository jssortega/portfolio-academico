"""Behaviour de recepción y correlación de respuestas.

El supervisor recibe en este behaviour los mensajes FIPA-ACL
provenientes de los grupos, los correlaciona con el seguimiento
abierto vía ``conversation_id`` y avanza el autómata.

Performativas que se manejan:

- ``agree``           → ``ACEPTADO`` (registrar latencia agree).
- ``inform``          → ``RESUELTO`` si el cuerpo es un
                        ``InformeResolucion`` válido; ``FALLIDO``
                        en caso contrario.
- ``refuse`` / ``not-understood`` → ``RECHAZADO``.

Cualquier otro mensaje se ignora silenciosamente para no romper si
un grupo envía mensajes de su mensajería interna por error.
"""
import json
import logging

from pydantic import ValidationError
from spade.behaviour import CyclicBehaviour

from agente_profesor.comportamientos.sondeo import (
    procesar_estado_agente_recibido,
)
from agente_profesor.seguimientos import EstadoSeguimiento
from ontologia.modelos_compartidos import InformeResolucion

logger = logging.getLogger(__name__)


# ─── Constantes simbólicas ──────────────────────────────────────────────────

# Tiempo (segundos) que el receptor espera por cada mensaje antes de
# ceder el control al planificador. Lo mantenemos corto para que el
# behaviour reaccione rápido a las paradas.
TIEMPO_ESPERA_MENSAJE = 1.0


class ReceptorRespuestasBehaviour(CyclicBehaviour):
    """Recibe mensajes y avanza el autómata del seguimiento."""

    async def run(self) -> None:
        """Espera un mensaje y lo procesa según su performativa."""
        mensaje = await self.receive(timeout=TIEMPO_ESPERA_MENSAJE)
        if mensaje is None:
            return

        performativa = mensaje.get_metadata("performative") or ""
        conversation_id = mensaje.get_metadata("conversation_id") or ""

        # Si la conversación pertenece a un sondeo de estado, lo
        # delegamos al módulo correspondiente y salimos.
        if performativa == "inform" and procesar_estado_agente_recibido(
                self.agent, conversation_id, mensaje.body or "",
        ):
            return

        seguimiento = self.agent.seguimientos.get(conversation_id)
        if seguimiento is None:
            self.agent.registrar_evento(
                "warn", "receptor",
                f"Mensaje '{performativa}' sin seguimiento "
                f"(conversation_id desconocido).",
            )
            return

        if performativa == "agree":
            self._procesar_agree(seguimiento)
        elif performativa == "inform":
            self._procesar_inform(seguimiento, mensaje.body or "")
        elif performativa in ("refuse", "not-understood"):
            self._procesar_rechazo(seguimiento, performativa)
        else:
            self.agent.registrar_evento(
                "warn", "receptor",
                f"Performativa no esperada '{performativa}' "
                f"para {seguimiento.grupo}.",
            )

    # ── Manejadores por performativa ────────────────────────────────────

    def _procesar_agree(self, seguimiento) -> None:
        """Anota la recepción del ``agree`` y transiciona a ACEPTADO."""
        seguimiento.registrar_agree()
        self.agent.registrar_seguimiento(seguimiento)
        self.agent.registrar_evento(
            "agree", "receptor",
            f"agree ← {seguimiento.grupo} "
            f"({seguimiento.latencia_agree_ms()} ms)",
        )

    def _procesar_inform(self, seguimiento, cuerpo: str) -> None:
        """Valida el InformeResolucion y transiciona a RESUELTO/FALLIDO."""
        try:
            datos = json.loads(cuerpo) if cuerpo else {}
            informe = InformeResolucion.model_validate(datos)
        except (json.JSONDecodeError, ValidationError) as err:
            seguimiento.registrar_error(
                EstadoSeguimiento.FALLIDO,
                f"Cuerpo del inform no interpretable: {err}",
            )
            self.agent.registrar_seguimiento(seguimiento)
            self.agent.registrar_evento(
                "fallido", "receptor",
                f"inform inválido ← {seguimiento.grupo}: {err}",
            )
            return

        # Coherencia con el request original (ver contrato §2.3)
        coherente = (
            informe.id_emergencia == seguimiento.id_emergencia
            and informe.tipo_emergencia.value
                == seguimiento.tipo_emergencia
            and informe.prioridad.value == seguimiento.prioridad
        )
        if not coherente:
            seguimiento.registrar_error(
                EstadoSeguimiento.FALLIDO,
                "InformeResolucion incoherente con el request.",
            )
            self.agent.registrar_seguimiento(seguimiento)
            self.agent.registrar_evento(
                "fallido", "receptor",
                f"inform incoherente ← {seguimiento.grupo}",
            )
            return

        # Conversión a dict serializable para SQLite/SSE/CSV
        seguimiento.registrar_informe(informe.model_dump(mode="json"))
        self.agent.registrar_seguimiento(seguimiento)
        self.agent.registrar_evento(
            "resuelto", "receptor",
            f"inform ← {seguimiento.grupo} "
            f"({seguimiento.latencia_informe_ms()} ms)",
        )

    def _procesar_rechazo(self, seguimiento, performativa: str) -> None:
        """Lleva el seguimiento a RECHAZADO."""
        seguimiento.registrar_error(
            EstadoSeguimiento.RECHAZADO,
            f"La Centralita respondió con '{performativa}'.",
        )
        self.agent.registrar_seguimiento(seguimiento)
        self.agent.registrar_evento(
            "rechazado", "receptor",
            f"{performativa} ← {seguimiento.grupo}",
        )
