"""
Agente Receptor
===============
Agente que escucha y recibe mensajes del Agente Emisor
utilizando un CyclicBehaviour para escucha continua.

El behaviour espera mensajes con un timeout de 10 segundos
para evitar consumo excesivo de CPU.

En esta práctica se utiliza el servidor XMPP de SPADE (lanzado con
"spade run"), por lo que los JIDs usan el dominio "localhost" y los
agentes se registran automáticamente (no es necesario crear cuentas).

Asignatura: Sistemas Multiagente
Grado en Ingeniería Informática - Universidad de Jaén
"""

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message


class AgenteReceptor(Agent):
    """Agente que recibe y procesa mensajes entrantes."""

    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.mensajes_recibidos = 0
        self.mensajes_maximos = 5

    class RecibirMensajeBehaviour(CyclicBehaviour):
        """Behaviour cíclico que escucha mensajes entrantes."""

        async def run(self):
            """Espera y procesa un mensaje entrante."""
            # Esperar mensaje con timeout de 10 segundos
            msg = await self.receive(timeout=10)

            if msg:
                if msg.get_metadata("performative") == "inform":
                    print(f"[RECEPTOR] Recibido de {msg.sender}:")
                    print(f"           Contenido: {msg.body}")
                    print(f"           Performativa: {msg.get_metadata('performative')}")
                    print(f"           Fecha y hora: {msg.get_metadata('timestamp')}")

                    msg_confirm = Message(to=str(msg.sender))
                    msg_confirm.set_metadata("performative", "confirm")
                    msg_confirm.body = f"{msg.body}"

                    await self.send(msg_confirm)
                    print(f"[RECEPTOR] Enviado: Confirmación {msg.body}")

                    self.agent.mensajes_recibidos += 1

                    if self.agent.mensajes_recibidos >= self.agent.mensajes_maximos:
                        msg_cancel = Message(to=str(msg.sender))
                        msg_cancel.set_metadata("performative", "cancel")

                        print(f"[RECEPTOR] Umbral de mensajes alcanzado ({self.agent.mensajes_recibidos}). Enviando mensaje cancel...")
                        await self.send(msg_cancel)
                elif msg.get_metadata("performative") == "confirm_cancel":
                    await self.agent.stop()
            else:
                print("[RECEPTOR] Esperando mensajes...")

    async def setup(self):
        """Configura el agente: activa la interfaz web y añade el behaviour."""
        print(f"[RECEPTOR] Agente {self.jid} iniciado")

        # Activar interfaz web en puerto 10002
        self.web.start(hostname="localhost", port=10002)
        print("[RECEPTOR] Web: http://localhost:10002/spade")

        # Añadir behaviour de recepción
        behaviour = self.RecibirMensajeBehaviour()
        self.add_behaviour(behaviour)
