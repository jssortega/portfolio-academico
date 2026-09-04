"""
Agente Emisor
=============
Agente que envía mensajes periódicos al Agente Receptor
utilizando el protocolo FIPA-ACL sobre XMPP.

Utiliza un PeriodicBehaviour para enviar un mensaje cada 3 segundos
con un contador incremental y la performativa "inform".

En esta práctica se utiliza el servidor XMPP de SPADE (lanzado con
"spade run"), por lo que los JIDs usan el dominio "localhost" y los
agentes se registran automáticamente (no es necesario crear cuentas).

Asignatura: Sistemas Multiagente
Grado en Ingeniería Informática - Universidad de Jaén
"""

from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.behaviour import CyclicBehaviour
from spade.message import Message


class AgenteEmisor(Agent):
    """Agente que envía mensajes periódicos a un receptor."""

    def __init__(self, jid, password, receptor_jid):
        """
        Inicializa el agente emisor.

        Args:
            jid: Identificador Jabber (JID) del agente emisor.
            password: Contraseña del agente en el servidor XMPP.
            receptor_jid: JID del agente receptor al que se enviarán los mensajes.
        """
        super().__init__(jid, password)
        self.receptor_jid = receptor_jid
        self.contador = 0

    class EnviarMensajeBehaviour(PeriodicBehaviour):
        """Behaviour periódico que envía mensajes al receptor."""

        async def run(self):
            """Envía un mensaje con un contador incremental."""
            self.agent.contador += 1
            msg = Message(to=self.agent.receptor_jid)
            msg.set_metadata("performative", "inform")
            msg.body = f"Mensaje #{self.agent.contador}"

            await self.send(msg)
            print(f"[EMISOR] Enviado: {msg.body}")

    class RecibirConfirmacionBehaviour(CyclicBehaviour):
        """Behaviour cíclico que escucha mensajes entrantes."""

        async def run(self):
            """Espera y procesa un mensaje entrante."""
            # Esperar mensaje con timeout de 10 segundos
            msg = await self.receive(timeout=10)

            if msg:
                print(f"[EMISOR] {msg.body} confirmado por: {msg.sender}:")
                print(f"           Performativa: {msg.get_metadata('performative')}")
            else:
                print("[EMISOR] Esperando mensajes...")



    async def setup(self):
        """Configura el agente: activa la interfaz web y añade el behaviour."""
        print(f"[EMISOR] Agente {self.jid} iniciado")

        # Activar interfaz web en puerto 10001
        self.web.start(hostname="localhost", port=10001)
        print("[EMISOR] Web: http://localhost:10001/spade")

        # Enviar mensaje cada 3 segundos
        behaviour1 = self.EnviarMensajeBehaviour(period=3)
        behaviour2 = self.RecibirConfirmacionBehaviour()
        self.add_behaviour(behaviour1)
        self.add_behaviour(behaviour2)
