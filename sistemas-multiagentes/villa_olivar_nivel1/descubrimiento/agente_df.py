"""
Agente DF — Villa Olivar.
Directorio de Facilitadores para registrar y buscar agentes por servicio.
"""

import json

from spade.agent import Agent
from spade.template import Template
from spade.behaviour import CyclicBehaviour


class AgenteDF(Agent):
    def __init__(self, jid_str, password, **kwargs):
        super().__init__(jid_str, password, **kwargs)
        self.directorio = {}

    class ProcesarPeticiones(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)

            if msg is None:
                return

            respuesta = msg.make_reply()
            respuesta.set_metadata("ontology", "fipa-df")
            respuesta.set_metadata("protocol", "fipa-request")
            respuesta.set_metadata("language", "application/json")

            try:
                accion = msg.get_metadata("ontology")
                body = json.loads(msg.body or "{}")
            except Exception as exc:
                respuesta.set_metadata("performative", "failure")
                respuesta.body = json.dumps({
                    "error": f"Mensaje DF no parseable: {exc}"
                })
                await self.send(respuesta)
                return

            if accion == "df-register":
                tipo = body.get("tipo")

                if not tipo:
                    respuesta.set_metadata("performative", "failure")
                    respuesta.body = json.dumps({
                        "error": "Falta el campo 'tipo' en df-register"
                    })
                    await self.send(respuesta)
                    return

                jid_remitente = str(msg.sender).split("/")[0]

                if tipo not in self.agent.directorio:
                    self.agent.directorio[tipo] = []

                if jid_remitente not in self.agent.directorio[tipo]:
                    self.agent.directorio[tipo].append(jid_remitente)

                print(f"[DF] Registrado servicio '{tipo}': {jid_remitente}")

                respuesta.set_metadata("performative", "inform")
                respuesta.body = json.dumps({
                    "status": "ok",
                    "tipo": tipo,
                    "jid": jid_remitente,
                })

            elif accion == "df-search":
                tipo = body.get("tipo")
                jids = self.agent.directorio.get(tipo, [])

                print(f"[DF] Busqueda servicio '{tipo}': {jids}")

                respuesta.set_metadata("performative", "inform")
                respuesta.body = json.dumps({
                    "tipo": tipo,
                    "jids": jids,
                })

            else:
                respuesta.set_metadata("performative", "failure")
                respuesta.body = json.dumps({
                    "error": f"Accion DF no reconocida: {accion}"
                })

            await self.send(respuesta)

    async def setup(self):
        print(f"[DF] Agente iniciado: {self.jid}")

        template_register = Template()
        template_register.set_metadata("performative", "request")
        template_register.set_metadata("ontology", "df-register")

        template_search = Template()
        template_search.set_metadata("performative", "request")
        template_search.set_metadata("ontology", "df-search")

        self.add_behaviour(
            self.ProcesarPeticiones(),
            template_register | template_search
        )