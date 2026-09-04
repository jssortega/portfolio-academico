import json

from spade.behaviour import CyclicBehaviour
from spade.message import Message

from ontologia import (
    ONTOLOGIA,
    crear_cuerpo_game_report,
    crear_cuerpo_game_report_refused,
    validar_cuerpo,
)


class ResponderInformeSupervisor(CyclicBehaviour):
    async def run(self):
        msg = await self.receive(timeout=10)

        if msg is None:
            return

        cuerpo = json.loads(msg.body)

        errores = validar_cuerpo(cuerpo)
        if not errores["valido"]:
            print(
                f"[TABLERO {self.agent.id_tablero}] "
                f"Solicitud de informe inválida: {errores['errores']}"
            )
            return

        if cuerpo.get("action") != "game-report":
            return

        respuesta = Message(to=str(msg.sender))
        respuesta.set_metadata("ontology", ONTOLOGIA)
        respuesta.thread = msg.thread

        if self.agent.ultimo_informe_partida is None:
            contenido = crear_cuerpo_game_report_refused()
            respuesta.set_metadata("performative", contenido.performativa)
            respuesta.body = contenido.cuerpo

            await self.send(respuesta)

            print(f"[TABLERO {self.agent.id_tablero}] REFUSE enviado al supervisor: no hay informe disponible")
            return

        informe = self.agent.ultimo_informe_partida

        contenido = crear_cuerpo_game_report(
            resultado_partida=informe["result"],
            ganador=informe["winner"],
            jugadores=informe["players"],
            turnos=informe["turns"],
            tablero=informe["board"],
            razon=informe.get("reason"),
        )
        respuesta.set_metadata("performative", contenido.performativa)
        respuesta.body = contenido.cuerpo

        await self.send(respuesta)

        print(f"[TABLERO {self.agent.id_tablero}] INFORM game-report enviado al supervisor")

        self.agent.ultimo_informe_partida = None
        self.agent.reactivar_para_nueva_partida()