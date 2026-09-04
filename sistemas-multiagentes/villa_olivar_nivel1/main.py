"""Lanzador del sistema multiagente del grupo — Nivel 3 (A2A).

Lee ``config/config.yaml`` y ``config/agents.yaml``, instancia
cada agente declarado a través de la factoría
``factoria.AgenteA2A`` y lo arranca en su puerto. Quedará a la
espera de SIGINT (Ctrl+C) para detener el sistema ordenadamente.

Uso típico durante el desarrollo en casa (perfil ``local`` activo
en ``config/config.yaml``):

.. code-block:: bash

    python main.py

Uso el día del examen (perfil ``servidor`` activo y
``direccion_publicada`` con la IP del PC del aula):

.. code-block:: bash

    python main.py

El comportamiento del lanzador no depende de argumentos de línea
de órdenes: toda la configuración vive en ``config/``. La
homogeneidad de arranque entre grupos es necesaria para que el
Coordinador del profesor pueda evaluar todos los sistemas con la
misma batería sin adaptaciones específicas.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from factoria import arrancar_agentes_desde_configuracion


RUTA_CONFIG = Path("config") / "config.yaml"
RUTA_AGENTES = Path("config") / "agents.yaml"


def main() -> None:
    """Punto de entrada del lanzador."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )
    asyncio.run(arrancar_agentes_desde_configuracion(RUTA_CONFIG, RUTA_AGENTES))


if __name__ == "__main__":
    main()
