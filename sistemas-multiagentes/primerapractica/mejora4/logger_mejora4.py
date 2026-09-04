"""
Agente Logger
===============
Agente que escucha y recibe mensajes de los agentes Emisor
y Receptor utilizando un CyclicBehaviour para escucha continua.

El behaviour espera mensajes con un timeout de 10 segundos
para evitar consumo excesivo de CPU.

Cuando recibe los mensajes los escribe en un archivo de texto
llamado "log.txt"

En esta práctica se utiliza el servidor XMPP de SPADE (lanzado con
"spade run"), por lo que los JIDs usan el dominio "localhost" y los
agentes se registran automáticamente (no es necesario crear cuentas).

Asignatura: Sistemas Multiagente
Grado en Ingeniería Informática - Universidad de Jaén
"""

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour


class AgenteLogger(Agent):
    class RecibirLogBehaviour(CyclicBehaviour):
        async def run(self):

            msg = await self.receive(timeout=10)

            if msg:
                linea = (
                    f"{msg.get_metadata('timestamp')} | "
                    f"{msg.sender} -> {msg.get_metadata('original_to')} | "
                    f"{msg.get_metadata('performative')} | "
                    f"{msg.body}\n"
                )
                with open("mejora4/log.txt", "a") as log:
                    log.write(linea)
                print(f"[LOGGER] Mensaje guardado en log: {msg.body}")
                if msg.get_metadata('performative') == 'confirm_cancel':
                    await self.agent.stop()

    async def setup(self):
        """Configura el agente: activa la interfaz web y añade el behaviour."""
        print(f"[LOGGER] Agente {self.jid} iniciado")

        # Activar interfaz web en puerto 10002
        self.web.start(hostname="localhost", port=10003)
        print("[LOGGER] Web: http://localhost:10003/spade")

        # Añadir behaviour de recepción
        behaviour = self.RecibirLogBehaviour()
        self.add_behaviour(behaviour)