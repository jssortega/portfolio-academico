"""Behaviour de sondeo periódico de estados de los agentes.

Cada cierto tiempo, el supervisor envía un ``query-ref`` con un
``ConsultaEstado`` a cada agente del grupo (Centralita, Bomberos,
Sanitario, Policía, Municipal) y registra el ``EstadoAgente``
recibido como respuesta. La pestaña "Estados de agentes" del panel
consume esa información.

El sondeo es **auxiliar**: no transiciona seguimientos ni participa
en el protocolo de inyección. Sirve de telemetría para el profesor
durante la corrección.

Configuración (``config_profesor.yaml``):

```yaml
sondeo:
  intervalo_segundos: 15      # Cada cuánto se sondea
  roles:                      # Roles a sondear (sufijo del JID)
    - centralita
    - bomberos
    - sanitario
    - policia
    - municipal
```
"""
import json
import logging
import uuid
from datetime import datetime

from pydantic import ValidationError
from spade.behaviour import PeriodicBehaviour
from spade.message import Message

from ontologia.modelos_compartidos import EstadoAgente

logger = logging.getLogger(__name__)


# ─── Constantes simbólicas ──────────────────────────────────────────────────

ONTOLOGIA_EMERGENCIAS = "emergencias-villaolivar"
LENGUAJE_PYDANTIC = "json-pydantic"
PROTOCOLO_CONSULTA = "fipa-query"
TIPO_MENSAJE_CONSULTA = "consulta_estado"

ROLES_POR_DEFECTO = (
    "centralita", "bomberos", "sanitario", "policia", "municipal",
)


class SondeoEstadoBehaviour(PeriodicBehaviour):
    """Envía ``query-ref`` periódicos y guarda los ``EstadoAgente``.

    Las respuestas no se procesan aquí (las gestiona el receptor
    general distinguiendo por ``conversation_id``); este behaviour
    solo emite. Para que el receptor sepa diferenciarlas, este
    behaviour mantiene el conjunto ``self.agent.consultas_en_curso``
    con los ``conversation_id`` que ha emitido.
    """

    async def on_start(self) -> None:
        """Inicializa la estructura de consultas en curso."""
        if not hasattr(self.agent, "consultas_en_curso"):
            self.agent.consultas_en_curso = {}
        if not hasattr(self.agent, "estados_agentes"):
            self.agent.estados_agentes = {}
        config = getattr(self.agent, "config_supervisor", {})
        self._roles = tuple(
            config.get("sondeo", {}).get("roles", ROLES_POR_DEFECTO),
        )

    async def run(self) -> None:
        """Lanza una consulta de estado a cada agente de cada grupo."""
        for grupo in self.agent.grupos:
            jid_centralita = grupo.get("jid_centralita", "")
            if "@" not in jid_centralita:
                continue
            dominio = jid_centralita.split("@", 1)[1]
            id_grupo = grupo.get("id", "")
            for rol in self._roles:
                jid_destino = self._construir_jid(
                    rol, id_grupo, dominio,
                )
                await self._consultar(jid_destino, rol, id_grupo)

    async def _consultar(
        self, jid_destino: str, rol: str, id_grupo: str,
    ) -> None:
        """Envía un único ``query-ref`` con ``ConsultaEstado``."""
        conversation_id = f"sondeo-{uuid.uuid4()}"
        cuerpo = {
            "tipo_mensaje": TIPO_MENSAJE_CONSULTA,
            "agente_destino": jid_destino,
        }
        mensaje = Message(to=jid_destino)
        mensaje.set_metadata("performative", "query-ref")
        mensaje.set_metadata("protocol", PROTOCOLO_CONSULTA)
        mensaje.set_metadata("ontology", ONTOLOGIA_EMERGENCIAS)
        mensaje.set_metadata("language", LENGUAJE_PYDANTIC)
        mensaje.set_metadata("conversation_id", conversation_id)
        mensaje.body = json.dumps(cuerpo, ensure_ascii=False)

        # Registramos la consulta para que el receptor la reconozca
        # cuando llegue el inform de respuesta.
        self.agent.consultas_en_curso[conversation_id] = {
            "rol": rol,
            "grupo": id_grupo,
            "jid_destino": jid_destino,
            "instante_envio": datetime.now(),
        }
        await self.send(mensaje)

    @staticmethod
    def _construir_jid(rol: str, id_grupo: str, dominio: str) -> str:
        """Convención: ``<rol>_<id_grupo>@<dominio>``."""
        resultado = f"{rol}_{id_grupo}@{dominio}"
        return resultado


# ─── Procesador de respuestas (lo invoca el receptor general) ───────────────

def procesar_estado_agente_recibido(
    agente, conversation_id: str, cuerpo: str,
) -> bool:
    """Procesa un inform que es respuesta a un sondeo.

    Devuelve ``True`` si el ``conversation_id`` corresponde a una
    consulta abierta y se ha podido interpretar el cuerpo, ``False``
    en caso contrario (para que el receptor general sepa que no
    debe tratar el mensaje como un InformeResolucion del protocolo
    principal).
    """
    consultas = getattr(agente, "consultas_en_curso", {})
    metadatos = consultas.pop(conversation_id, None)
    if metadatos is None:
        return False

    try:
        datos = json.loads(cuerpo) if cuerpo else {}
        estado = EstadoAgente.model_validate(datos)
    except (json.JSONDecodeError, ValidationError) as err:
        agente.registrar_evento(
            "warn", "sondeo",
            f"EstadoAgente inválido de {metadatos['rol']}_"
            f"{metadatos['grupo']}: {err}",
        )
        return True

    # Latencia del sondeo en ms
    latencia_ms = int(
        (datetime.now() - metadatos["instante_envio"])
        .total_seconds() * 1000,
    )

    estados = getattr(agente, "estados_agentes", {})
    clave = (metadatos["grupo"], metadatos["rol"])
    estados[clave] = {
        "grupo": metadatos["grupo"],
        "rol": metadatos["rol"],
        "jid": metadatos["jid_destino"],
        "estado": estado.estado,
        "emergencia_actual": estado.emergencia_actual,
        "detalle": estado.detalle,
        "marca_temporal": datetime.now().isoformat(),
        "latencia_ms": latencia_ms,
    }
    agente.estados_agentes = estados
    agente.registrar_evento(
        "estado", "sondeo",
        f"{metadatos['rol']}_{metadatos['grupo']}: "
        f"{estado.estado} ({latencia_ms} ms)",
    )
    return True
