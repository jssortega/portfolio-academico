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
from spade.template import Template


class AgenteReceptor(Agent):
    """Agente que recibe y procesa mensajes entrantes."""

    class PreguntaRespuestaBehaviour(CyclicBehaviour):
        """Behaviour cíclico que escucha mensajes entrantes."""

        async def run(self):
            """Espera y procesa un mensaje entrante consultando la respuesta de la pregunta
            recibida y mandando un mensaje de respuesta a la pregunta."""
            # Esperar mensaje con timeout de 10 segundos
            msg = await self.receive(timeout=10)

            if msg:
                respuesta_encontrada = None
                with open('mejora5/diccionario.txt', 'r') as fichero:
                    for linea in fichero.readlines():
                        linea = linea.strip()

                        if not linea:
                            continue

                        clave, valor = linea.split(":", 1)

                        if msg.body == clave:
                            respuesta_encontrada = valor
                            break

                respuesta = Message(to=str(msg.sender))
                if respuesta_encontrada:
                    #La pregunta está en el diccionario
                    respuesta.set_metadata("performative", "inform")
                    respuesta.body = respuesta_encontrada
                else:
                    #La pregunta no está en el diccionario
                    respuesta.set_metadata("performative", "failure")
                    respuesta.body = "Clave no encontrada"

                await self.send(respuesta)

                print(f"[RECEPTOR] Recibido de {msg.sender}:")
                print(f"           Pregunta: {msg.body}")
                print(f"           Respuesta: {respuesta.body}")
            else:
                print("[RECEPTOR] Esperando mensajes...")

    class RecibirParadaBehaviour(CyclicBehaviour):
        """Behaviour cíclico que escucha mensajes entrantes para saber cuando detenerse."""

        async def run(self):
            """Espera y procesa un mensaje entrante."""
            # Esperar mensaje con timeout de 10 segundos
            msg = await self.receive(timeout=10)

            if msg:
                print("[RECEPTOR] Mensaje de parada recibido.")
                await self.agent.stop()

    async def setup(self):
        """Configura el agente: activa la interfaz web y añade el behaviour."""
        print(f"[RECEPTOR] Agente {self.jid} iniciado")

        # Activar interfaz web en puerto 10002
        self.web.start(hostname="localhost", port=10002)
        print("[RECEPTOR] Web: http://localhost:10002/spade")

        #Las plantillas para asegurarse que recibe los mensajes adecuados
        template1 = Template()
        template1.set_metadata("performative", "query-if")

        template2 = Template()
        template2.set_metadata("performative", "cancel")

        # Añadir behaviour de recepción
        behaviour1 = self.PreguntaRespuestaBehaviour()
        self.add_behaviour(behaviour1,template1)
        behaviour2 = self.RecibirParadaBehaviour()
        self.add_behaviour(behaviour2, template2)