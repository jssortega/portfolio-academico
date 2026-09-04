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

    class EnviarMensajeBehaviour(PeriodicBehaviour):
        """Behaviour periódico que envía las preguntas al receptor."""

        async def run(self):
            #Primero comprueba si ya ha hecho todas las preguntas para saber si detenerse o no
            if self.agent.indice_pregunta >= len(self.agent.preguntas):
                print("[EMISOR] Máximo de preguntas enviado")
                cancel = Message(to=self.agent.receptor_jid)
                cancel.set_metadata("performative", "cancel")

                await self.send(cancel)
                await self.agent.stop()
                return

            pregunta = self.agent.preguntas[self.agent.indice_pregunta]

            """Envía la pregunta al receptor."""
            msg = Message(to=self.agent.receptor_jid)
            msg.set_metadata("performative", "query-if")
            msg.body = pregunta

            await self.send(msg)
            self.agent.indice_pregunta += 1
            print(f"[EMISOR] Enviado: {msg.body}")

    class RecibirRespuestaBehaviour(CyclicBehaviour):
        """Behaviour cíclico que escucha las respuestas entrantes."""

        async def run(self):
            """Espera y procesa un mensaje entrante."""
            # Esperar mensaje con timeout de 10 segundos
            respuesta = await self.receive(timeout=10)

            if respuesta:
                print(f"[EMISOR] Respuesta recibida de: {respuesta.sender}:")
                print(f"           Performativa: {respuesta.get_metadata('performative')}")
                print(f"           Mensaje: {respuesta.body}")
            else:
                print("[EMISOR] Esperando mensajes...")

    async def setup(self):
        """Configura el agente: activa la interfaz web y añade el behaviour."""
        print(f"[EMISOR] Agente {self.jid} iniciado")

        # Activar interfaz web en puerto 10001
        self.web.start(hostname="localhost", port=10001)
        print("[EMISOR] Web: http://localhost:10001/spade")

        #Una lista con las preguntas que va a realizar
        self.preguntas = [
            "capital_espana",
            "lenguaje_spade",
            "autor_quijote",
            "deporte_mas_popular"
        ]
        self.indice_pregunta = 0

        behaviour1 = self.EnviarMensajeBehaviour(period=3)
        behaviour2 = self.RecibirRespuestaBehaviour()
        self.add_behaviour(behaviour1)
        self.add_behaviour(behaviour2)
