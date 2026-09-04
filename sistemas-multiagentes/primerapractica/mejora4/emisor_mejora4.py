"""
Agente Emisor
=============
Agente que envía mensajes periódicos al Agente Receptor y al Agente Logger
utilizando el protocolo FIPA-ACL sobre XMPP.

Utiliza un PeriodicBehaviour para enviar un mensaje cada 3 segundos
con un contador incremental y la performativa "inform".

También recibe mensajes de confirmación por parte del Agente Receptor utilizando un
CyclicBehaviour con performativa "confirm".

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
from datetime import datetime
import copy


class AgenteEmisor(Agent):
    """Agente que envía mensajes periódicos a un receptor."""

    def __init__(self, jid, password, receptor_jid, logger_jid):
        """
        Inicializa el agente emisor.

        Args:
            jid: Identificador Jabber (JID) del agente emisor.
            password: Contraseña del agente en el servidor XMPP.
            receptor_jid: JID del agente receptor al que se enviarán los mensajes.
        """
        super().__init__(jid, password)
        self.receptor_jid = receptor_jid
        self.logger_jid = logger_jid
        self.contador = 0

    class EnviarMensajeBehaviour(PeriodicBehaviour):
        """Behaviour periódico que envía mensajes al receptor y al logger."""

        async def run(self):
            """Envía un mensaje con un contador incremental y su respectiva copia al logger"""
            self.agent.contador += 1
            msg = Message(to=self.agent.receptor_jid)
            msg.set_metadata("performative", "inform")
            msg.set_metadata("timestamp", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            msg.body = f"Mensaje #{self.agent.contador}"

            await self.send(msg)
            print(f"[EMISOR] Enviado: {msg.body}")

            log_msg = copy.copy(msg)
            log_msg.to = self.agent.logger_jid
            log_msg.set_metadata("original_to", str(msg.to))

            await self.send(log_msg)

    class RecibirConfirmacionBehaviour(CyclicBehaviour):
        """Behaviour cíclico que escucha mensajes entrantes."""

        async def run(self):
            """Espera y procesa un mensaje entrante."""
            # Esperar mensaje con timeout de 10 segundos
            msg = await self.receive(timeout=10)

            if msg:
                if msg.get_metadata("performative") == "confirm":
                    print(f"[EMISOR] {msg.body} confirmado por: {msg.sender}:")
                    print(f"           Performativa: {msg.get_metadata('performative')}")
                elif msg.get_metadata("performative") == "cancel":
                    print("[EMISOR] Recibido mensaje de cancelación. Deteniendo agente emisor...")
                    msg_confirm = Message(to=self.agent.receptor_jid)
                    msg_confirm.set_metadata("performative", "confirm_cancel")
                    msg_confirm.set_metadata("timestamp", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
                    msg_confirm.body = f"{msg.body}"

                    await self.send(msg_confirm)

                    log_msg_confirm = copy.copy(msg_confirm)
                    log_msg_confirm.to = self.agent.logger_jid
                    log_msg_confirm.set_metadata("original_to", str(msg_confirm.to))

                    await self.send(log_msg_confirm)

                    await self.agent.stop()
            else:
                print("[EMISOR] Esperando mensajes...")



    async def setup(self):
        """Configura el agente: activa la interfaz web y añade los behaviour."""
        print(f"[EMISOR] Agente {self.jid} iniciado")

        # Activar interfaz web en puerto 10001
        self.web.start(hostname="localhost", port=10001)
        print("[EMISOR] Web: http://localhost:10001/spade")

        # Enviar mensaje cada 3 segundos
        behaviour1 = self.EnviarMensajeBehaviour(period=3)
        # Escuchar mensajes entrantes
        behaviour2 = self.RecibirConfirmacionBehaviour()
        self.add_behaviour(behaviour1)
        self.add_behaviour(behaviour2)