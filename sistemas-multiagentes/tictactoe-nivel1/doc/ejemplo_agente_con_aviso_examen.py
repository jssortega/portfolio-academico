"""Ejemplo mínimo: agente con el aviso del modo examen ya integrado.

Este fichero **no forma parte del sistema**: vive en ``doc/`` para que el
lanzador (``main.py``) no lo cargue. Es solo una referencia para que veas
exactamente dónde se coloca la llamada a ``registrar_aviso_errores_examen``
dentro del ``setup()`` de un agente (el «Caso B» de
``doc/AVISO_ERRORES_EXAMEN.md``).

Recuerda:

* Si arrancas tus agentes con el ``main.py`` del examen, **no necesitas
  esta línea**: la factoría ``crear_agente()`` ya instala el aviso por ti.
* Esta integración manual solo hace falta si lanzas tus agentes por tu
  cuenta, sin pasar por la factoría.

Para probarlo de forma aislada, desde la raíz del proyecto::

    python doc/ejemplo_agente_con_aviso_examen.py
"""
import asyncio

from spade.agent import Agent

# PASO 1 — Importar la función del material de apoyo (utils.py).
from utils import registrar_aviso_errores_examen


# JID completo de la sala MUC del modo examen. En un agente real este
# valor NO se escribe a mano: se lee de la configuración centralizada
# (config_xmpp["sala_muc_completa"]). Aquí se fija como constante solo
# para que el ejemplo sea autocontenido.
SALA_MUC_EXAMEN = "examen@examen.localhost"


class AgenteEjemplo(Agent):
    """Agente de demostración que se une a la sala del modo examen."""

    async def setup(self) -> None:
        """Prepara el agente: plugin MUC, aviso de examen y join."""
        # Registro del plugin de salas MUC (XEP-0045), como en cualquier
        # agente del curso.
        self.client.register_plugin("xep_0045")

        # PASO 2 — Registrar el aviso del modo examen ANTES del join.
        # El orden importa: si la sala rechaza la unión, el servidor
        # responde de inmediato, así que el manejador del error de
        # presencia debe estar ya registrado para no perder la respuesta.
        registrar_aviso_errores_examen(self, SALA_MUC_EXAMEN)

        # Join a la sala MUC: el agente intenta unirse. Si el supervisor
        # del profesor todavía no ha creado la sala, el servidor devuelve
        # un error de presencia con la marca [Examen]; gracias al paso 2,
        # ese mensaje aparecerá en la consola en lugar de perderse.
        muc = self.client.plugin["xep_0045"]
        muc.join_muc(SALA_MUC_EXAMEN, nick="agente_ejemplo")


async def main() -> None:
    """Arranca el agente de ejemplo y lo mantiene unos segundos vivo."""
    # En este ejemplo aislado se instancia el agente directamente. En el
    # sistema real, main.py lo crearía con la factoría crear_agente(),
    # que además instala el aviso automáticamente.
    agente = AgenteEjemplo("agente_ejemplo@localhost", "secret")
    await agente.start(auto_register=True)

    # Tiempo para que el servidor responda y el aviso pueda mostrarse.
    await asyncio.sleep(6)

    await agente.stop()


if __name__ == "__main__":
    asyncio.run(main())
