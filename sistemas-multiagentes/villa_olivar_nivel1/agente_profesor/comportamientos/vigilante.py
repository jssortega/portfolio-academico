"""Behaviour de vigilancia de timeouts.

Cada cierto tiempo recorre los seguimientos no terminales y
comprueba si ha caducado alguno de los dos plazos del protocolo
de inyección:

- Si el seguimiento está en ``ENVIADO`` y han pasado más de
  ``timeout_agree`` segundos desde el envío del ``request``, se
  transiciona a ``TIMEOUT``.
- Si el seguimiento está en ``ACEPTADO`` y han pasado más de
  ``timeout_informe`` segundos desde el ``agree``, se transiciona
  a ``TIMEOUT``.

Los plazos se leen del bloque ``timeouts`` de ``config_profesor.yaml``.
"""
import logging
from datetime import datetime

from spade.behaviour import PeriodicBehaviour

from agente_profesor.seguimientos import EstadoSeguimiento

logger = logging.getLogger(__name__)


# ─── Constantes simbólicas ──────────────────────────────────────────────────

# Valores por defecto si la configuración no los provee. Coinciden
# con los del contrato_supervisor.md §4.
TIMEOUT_AGREE_DEFECTO_S = 5.0
TIMEOUT_INFORME_DEFECTO_S = 180.0


class VigilanteTimeoutsBehaviour(PeriodicBehaviour):
    """Recorre los seguimientos abiertos y caduca los que toque."""

    async def run(self) -> None:
        """Comprueba los plazos de cada seguimiento no terminal."""
        timeouts = getattr(self.agent, "timeouts", {})
        plazo_agree = float(
            timeouts.get("agree_segundos", TIMEOUT_AGREE_DEFECTO_S),
        )
        plazo_informe = float(
            timeouts.get("informe_segundos", TIMEOUT_INFORME_DEFECTO_S),
        )

        ahora = datetime.now()
        # Copiamos a lista para iterar sin riesgo de mutación durante
        # el recorrido (otros behaviours pueden modificar el dict).
        seguimientos = list(self.agent.seguimientos.values())
        for seguimiento in seguimientos:
            if seguimiento.es_terminal():
                continue
            self._verificar_uno(
                seguimiento, ahora, plazo_agree, plazo_informe,
            )

    def _verificar_uno(
        self, seguimiento, ahora: datetime,
        plazo_agree: float, plazo_informe: float,
    ) -> None:
        """Aplica las dos reglas de timeout a un seguimiento."""
        if (seguimiento.estado == EstadoSeguimiento.ENVIADO
                and seguimiento.instante_envio is not None):
            transcurridos = (
                ahora - seguimiento.instante_envio
            ).total_seconds()
            if transcurridos > plazo_agree:
                self._caducar(
                    seguimiento,
                    f"No llegó agree en {plazo_agree:.0f} s",
                )
                return

        if (seguimiento.estado == EstadoSeguimiento.ACEPTADO
                and seguimiento.instante_agree is not None):
            transcurridos = (
                ahora - seguimiento.instante_agree
            ).total_seconds()
            if transcurridos > plazo_informe:
                self._caducar(
                    seguimiento,
                    f"No llegó InformeResolucion en {plazo_informe:.0f} s",
                )

    def _caducar(self, seguimiento, motivo: str) -> None:
        """Transición a TIMEOUT con persistencia y SSE."""
        seguimiento.registrar_error(EstadoSeguimiento.TIMEOUT, motivo)
        self.agent.registrar_seguimiento(seguimiento)
        self.agent.registrar_evento(
            "timeout", "vigilante",
            f"{seguimiento.grupo}: {motivo}",
        )
