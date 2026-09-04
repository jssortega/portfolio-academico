"""Configuración común y simuladores para los tests del agente profesor.

Los tests del supervisor del profesor están diseñados para ejecutarse
sin SPADE ni servidor XMPP. Para ello se utilizan simuladores ligeros
del agente y de los métodos asíncronos ``send`` / ``receive`` de los
behaviours, definidos aquí para reutilizarse desde varios módulos de
test (estilo TicTacToe — ``tests/conftest.py``).

Decisiones de diseño:

- Se usa una **clase simulada** en lugar de ``unittest.mock.MagicMock``
  porque queremos que los tests fallen explícitamente al acceder a
  atributos no inicializados, y que la inspección visual del estado
  sea trivial.
- Todos los simuladores son **síncronos**: si un test necesita un
  comportamiento ``async`` (p. ej. ``self.send`` en un behaviour),
  envuelve la llamada con ``asyncio.run`` o ``pytest.mark.asyncio``.
"""
from __future__ import annotations

import os
import sys
from collections import deque
from pathlib import Path
from typing import Optional

import pytest


# ─── Inserción de la raíz del proyecto en sys.path ─────────────────────────
# Para que `import agente_profesor` funcione cuando pytest se invoca
# desde la raíz del proyecto. No es necesario si el usuario ejecuta
# los tests con `python -m pytest` desde la raíz, pero lo añadimos
# por robustez.

_RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
if str(_RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROYECTO))


# ─── Simulador del agente supervisor ───────────────────────────────────────

class AgenteSupervisorSimulado:
    """Simulador del ``SupervisorEmergencias`` para tests sin SPADE.

    Replica la API pública que consumen los behaviours y los handlers
    HTTP (``seguimientos``, ``log_eventos``, ``grupos``, ``timeouts``,
    ``estados_agentes``, ``consultas_en_curso``, ``almacen``,
    ``modo``…) sin arrastrar el ciclo de vida de un agente SPADE real.

    Los métodos ``registrar_seguimiento`` y ``registrar_evento``
    almacenan las llamadas en listas (``llamadas_seguimientos`` y
    ``llamadas_eventos``) para que los tests puedan inspeccionarlas
    con aserciones expresivas.
    """

    def __init__(
        self,
        grupos: Optional[list[dict]] = None,
        timeouts: Optional[dict] = None,
        modo: str = "activo",
    ) -> None:
        self.modo = modo
        self.es_agente_vivo = True
        self.grupos: list[dict] = list(grupos or [])
        self.timeouts: dict = dict(timeouts or {})
        self.seguimientos: dict = {}
        self.log_eventos: deque = deque(maxlen=500)
        self.estados_agentes: dict = {}
        self.consultas_en_curso: dict = {}
        self.config_supervisor: dict = {
            "grupos": self.grupos,
            "timeouts": self.timeouts,
            "modo_arranque": modo,
            "inyeccion": {"automatica": False, "intervalo_segundos": 30},
            "sondeo": {
                "intervalo_segundos": 15,
                "roles": (
                    "centralita", "bomberos", "sanitario",
                    "policia", "municipal",
                ),
            },
        }
        self.almacen = None
        self.ruta_db: str = ""
        self.jid = "profesor_emergencias@localhost"
        self.inyector = None

        # Registros de llamadas para aserciones desde los tests.
        self.llamadas_seguimientos: list = []
        self.llamadas_eventos: list[dict] = []

    # ── API consumida por los behaviours ────────────────────────────────

    def registrar_seguimiento(self, seguimiento) -> None:
        """Inserta o actualiza un seguimiento; registra la llamada."""
        self.seguimientos[seguimiento.id_emergencia] = seguimiento
        self.llamadas_seguimientos.append(seguimiento)

    def registrar_evento(
        self, tipo: str, origen: str, detalle: str,
    ) -> None:
        """Añade un evento al log; registra la llamada."""
        evento = {"tipo": tipo, "de": origen, "detalle": detalle}
        self.log_eventos.appendleft(evento)
        self.llamadas_eventos.append(evento)


# ─── Fixtures pytest ───────────────────────────────────────────────────────

@pytest.fixture
def agente_simulado() -> AgenteSupervisorSimulado:
    """Devuelve un agente simulado con dos grupos de muestra."""
    grupos = [
        {
            "id": "fenix",
            "nombre": "Equipo Fénix",
            "jid_centralita": "centralita_fenix@localhost",
            "descripcion": "Grupo bajo prueba.",
        },
        {
            "id": "olivar42",
            "nombre": "Equipo Olivar 42",
            "jid_centralita": "centralita_olivar42@localhost",
            "descripcion": "Grupo bajo prueba.",
        },
    ]
    timeouts = {
        "agree_segundos": 5,
        "informe_segundos": 180,
        "consulta_estado_segundos": 2,
    }
    return AgenteSupervisorSimulado(grupos=grupos, timeouts=timeouts)


@pytest.fixture
def db_temporal(tmp_path) -> str:
    """Ruta a un fichero SQLite temporal único por test."""
    ruta = tmp_path / "supervisor.db"
    return str(ruta)


@pytest.fixture
def almacen_temporal(db_temporal):
    """Almacén SQLite temporal abierto y cerrado automáticamente."""
    from agente_profesor.persistencia.almacen_supervisor import (
        AlmacenSupervisor,
    )
    almacen = AlmacenSupervisor(db_temporal)
    yield almacen
    almacen.cerrar()
    if os.path.exists(db_temporal):
        os.remove(db_temporal)


# ─── Mensaje SPADE simulado ────────────────────────────────────────────────

class MensajeSimulado:
    """Sustituto mínimo de ``spade.message.Message`` para los tests.

    Permite inspeccionar las metadatas y el cuerpo, y cumple la
    interfaz mínima que usan los behaviours del supervisor.
    """

    def __init__(
        self, performativa: str = "", cuerpo: str = "",
        conversation_id: str = "",
    ) -> None:
        self._metadata: dict[str, str] = {}
        self.body = cuerpo
        if performativa:
            self._metadata["performative"] = performativa
        if conversation_id:
            self._metadata["conversation_id"] = conversation_id

    def set_metadata(self, clave: str, valor: str) -> None:
        self._metadata[clave] = valor

    def get_metadata(self, clave: str) -> Optional[str]:
        return self._metadata.get(clave)
