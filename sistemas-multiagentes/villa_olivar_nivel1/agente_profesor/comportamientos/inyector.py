"""Behaviour de inyección de incidentes.

El supervisor selecciona un escenario del catálogo, construye un
``DatosEmergencia`` y lo envía como ``request`` FIPA-ACL a la
Centralita del grupo. Crea un seguimiento en estado ``PREPARADO``,
lo transiciona a ``ENVIADO`` y registra el suceso en la línea de
tiempo y en SQLite. La correlación posterior se hace por
``conversation_id`` (que reutiliza el ``id_emergencia``).

El behaviour soporta dos modos:

- **Automático** (``inyeccion.automatica: true``): cada
  ``intervalo_segundos`` selecciona un grupo (round-robin) y un
  escenario (aleatorio o cíclico) e inyecta. Útil para corregir.

- **Manual** (``inyeccion.automatica: false``): no inyecta solo;
  espera a que el panel llame a ``inyectar_a_grupo()`` desde el
  endpoint ``POST /supervisor/api/inyectar``.
"""
import json
import logging
import random
from typing import Optional

from spade.behaviour import PeriodicBehaviour
from spade.message import Message

from agente_profesor.escenarios import (
    _DEFINICIONES_ESCENARIOS,
    claves_escenarios,
    construir_id_emergencia,
)
from agente_profesor.seguimientos import (
    EstadoSeguimiento,
    Seguimiento,
)

logger = logging.getLogger(__name__)


# ─── Constantes simbólicas ──────────────────────────────────────────────────

# Cabeceras FIPA-ACL fijas del protocolo de inyección de incidentes
# (ver docs/contrato_supervisor.md §1).
ONTOLOGIA_EMERGENCIAS = "emergencias-villaolivar"
LENGUAJE_PYDANTIC = "json-pydantic"
PROTOCOLO_INYECCION = "fipa-request"

# Tipo de mensaje que viaja en el cuerpo del request, conforme al
# enumerado de TipoEmergencia y al campo tipo_mensaje del modelo
# Pydantic DatosEmergencia.
TIPO_MENSAJE_INYECCION = "alerta_emergencia"


class InyectorIncidentesBehaviour(PeriodicBehaviour):
    """Behaviour periódico que dispara inyecciones a los grupos.

    En modo automático, cada disparo elige un grupo y un escenario.
    En modo manual, el método ``run`` no hace nada y el lanzamiento
    real se delega a ``inyectar_a_grupo()`` desde el panel web.
    """

    async def on_start(self) -> None:
        """Prepara el estado interno antes del primer disparo."""
        self._indice_grupo = 0
        self._aleatorio = random.Random()
        # Lista (estable) de claves del catálogo, para selección
        # deterministe cuando se quiera reproducibilidad.
        self._claves_catalogo: list[str] = claves_escenarios()
        self.agent.registrar_evento(
            "info", "inyector",
            "Behaviour de inyección listo "
            f"(automático: {self._es_automatico()}, "
            f"intervalo: {self.period} s).",
        )

    async def run(self) -> None:
        """Disparo periódico. Solo actúa si el modo es automático."""
        if not self._es_automatico():
            return
        if not self.agent.grupos:
            return
        grupo = self._siguiente_grupo_round_robin()
        clave = self._aleatorio.choice(self._claves_catalogo)
        await self.inyectar_a_grupo(
            id_grupo=grupo["id"], clave_escenario=clave,
        )

    async def inyectar_a_grupo(
        self, id_grupo: str,
        clave_escenario: Optional[str] = None,
    ) -> Optional[Seguimiento]:
        """Inyecta un escenario a un grupo concreto.

        Args:
            id_grupo: Identificador del grupo (campo ``id`` del bloque
                ``grupos`` del config_profesor.yaml).
            clave_escenario: Clave del catálogo (p. ej. ``incendio_alta``).
                Si es ``None``, se elige una al azar.

        Returns:
            El ``Seguimiento`` creado, o ``None`` si el grupo no existe
            o el escenario no está en el catálogo.
        """
        grupo = self._buscar_grupo(id_grupo)
        if grupo is None:
            self.agent.registrar_evento(
                "warn", "inyector",
                f"Grupo desconocido al intentar inyectar: '{id_grupo}'.",
            )
            return None

        if clave_escenario is None:
            clave_escenario = self._aleatorio.choice(self._claves_catalogo)

        definicion = next(
            (d for d in _DEFINICIONES_ESCENARIOS if d[0] == clave_escenario),
            None,
        )
        if definicion is None:
            self.agent.registrar_evento(
                "warn", "inyector",
                f"Escenario desconocido: '{clave_escenario}'.",
            )
            return None

        # Construir el seguimiento y el cuerpo del request
        _, tipo_emergencia, prioridad, ubicacion, descripcion = definicion
        id_emergencia = construir_id_emergencia(clave_escenario)
        seguimiento = Seguimiento(
            id_emergencia=id_emergencia,
            grupo=grupo["id"],
            jid_destino=grupo["jid_centralita"],
            tipo_emergencia=tipo_emergencia,
            prioridad=prioridad,
            descripcion=f"{ubicacion} — {descripcion}",
        )
        self.agent.registrar_seguimiento(seguimiento)

        # Construir y enviar el mensaje FIPA-ACL
        cuerpo = {
            "tipo_mensaje": TIPO_MENSAJE_INYECCION,
            "id_emergencia": id_emergencia,
            "tipo_emergencia": tipo_emergencia,
            "prioridad": prioridad,
            "ubicacion": ubicacion,
            "descripcion": descripcion,
            # marca_temporal la añade Pydantic en el otro extremo si
            # falta; aquí no la incluimos para reducir desviaciones.
        }
        mensaje = Message(to=grupo["jid_centralita"])
        mensaje.set_metadata("performative", "request")
        mensaje.set_metadata("protocol", PROTOCOLO_INYECCION)
        mensaje.set_metadata("ontology", ONTOLOGIA_EMERGENCIAS)
        mensaje.set_metadata("language", LENGUAJE_PYDANTIC)
        mensaje.set_metadata("conversation_id", id_emergencia)
        mensaje.body = json.dumps(cuerpo, ensure_ascii=False)

        await self.send(mensaje)
        seguimiento.registrar_envio()
        self.agent.registrar_seguimiento(seguimiento)
        self.agent.registrar_evento(
            "request", "inyector",
            f"request → {grupo['id']} "
            f"({tipo_emergencia}/{prioridad})",
        )
        return seguimiento

    # ── Utilidades privadas ─────────────────────────────────────────────

    def _es_automatico(self) -> bool:
        """Lee la bandera ``inyeccion.automatica`` de la configuración."""
        config = getattr(self.agent, "config_supervisor", {})
        resultado = bool(
            config.get("inyeccion", {}).get("automatica", False),
        )
        return resultado

    def _siguiente_grupo_round_robin(self) -> dict:
        """Devuelve el siguiente grupo siguiendo round-robin."""
        grupos = self.agent.grupos
        grupo = grupos[self._indice_grupo % len(grupos)]
        self._indice_grupo = (self._indice_grupo + 1) % len(grupos)
        return grupo

    def _buscar_grupo(self, id_grupo: str) -> Optional[dict]:
        """Localiza un grupo por su ``id``."""
        resultado = next(
            (g for g in self.agent.grupos if g.get("id") == id_grupo),
            None,
        )
        return resultado
