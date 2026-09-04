"""
Script Principal - Sistema Emisor-Receptor
==========================================
Orquesta la creación, inicio y parada de los agentes
Emisor Receptor y Logger del sistema multiagente.

SERVIDOR XMPP:
    Esta práctica utiliza el servidor XMPP que SPADE incluye de forma
    nativa (basado en PyJabber). Se lanza de forma independiente con
    el comando "spade run" en un terminal separado. Esto significa que:
      - NO es necesario instalar ni configurar ningún servidor XMPP externo.
      - Los JIDs de los agentes deben usar el dominio "localhost".
      - Los agentes se registran automáticamente en el servidor.
      - La contraseña puede ser cualquier cadena de texto.

    En prácticas posteriores se utilizará un servidor XMPP externo
    (Prosody, jabber.fr, etc.) para trabajar con entornos distribuidos.

IMPORTANTE: El receptor debe iniciarse ANTES que el emisor
para que esté escuchando cuando lleguen los primeros mensajes.

Asignatura: Sistemas Multiagente
Grado en Ingeniería Informática - Universidad de Jaén

Uso:
    1. Arranca el servidor XMPP: spade run
    2. En otro terminal: python main_mejora4.py
    (Presionar Ctrl+C para detener el sistema)
"""

import spade
import asyncio
from emisor_mejora4 import AgenteEmisor
from receptor_mejora4 import AgenteReceptor
from logger_mejora4 import AgenteLogger

# ============================================================
# CONFIGURACIÓN DE AGENTES
# Al usar el servidor XMPP de SPADE (lanzado con "spade run"),
# el dominio de los JIDs debe ser "localhost". Las contraseñas
# pueden ser cualquier cadena, ya que el servidor registra
# automáticamente a los agentes al conectarse.
# ============================================================
EMISOR_JID = "emisor@localhost"
EMISOR_PASS = "password_emisor"
RECEPTOR_JID = "receptor@localhost"
RECEPTOR_PASS = "password_receptor"
LOGGER_JID = "logger@localhost"
LOGGER_PASS = "password_logger"

async def main():
    """Función principal que inicia el sistema multiagente."""

    # Crear agentes
    logger = AgenteLogger(LOGGER_JID,LOGGER_PASS)
    receptor = AgenteReceptor(RECEPTOR_JID, RECEPTOR_PASS, LOGGER_JID)
    emisor = AgenteEmisor(EMISOR_JID, EMISOR_PASS, RECEPTOR_JID, LOGGER_JID)

    # Iniciar receptor y logger primero (deben estar escuchando)
    await logger.start()
    await receptor.start()
    await emisor.start()


    print("Sistema activo. Presiona Ctrl+C para detener.")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Deteniendo agentes...")

    await emisor.stop()
    await receptor.stop()
    await logger.stop()


if __name__ == "__main__":
    # IMPORTANTE: el servidor XMPP debe estar ejecutándose
    # previamente con el comando: spade run
    spade.run(main())