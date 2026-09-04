"""
Agente "Hola Mundo" con SPADE
=============================
Primer agente básico que se conecta al servidor XMPP,
muestra un saludo y se detiene.

Asignatura: Sistemas Multiagente
Grado en Ingeniería Informática - Universidad de Jaén

Uso:
    1. Arranca el servidor XMPP: spade run
    2. En otro terminal: python hola_mundo.py
"""

import spade
from spade import wait_until_finished
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour


class AgenteHolaMundo(Agent):
    """Mi primer agente SPADE."""

    class SaludoBehaviour(OneShotBehaviour):
        """Behaviour que se ejecuta una sola vez para mostrar un saludo."""

        async def run(self):
            print("=" * 40)
            print(f"¡Hola Mundo desde SPADE!")
            print(f"Soy el agente: {self.agent.jid}")
            print("=" * 40)
            # Detener el agente tras el saludo
            await self.agent.stop()

    async def setup(self):
        """Método de configuración que se ejecuta al iniciar el agente."""
        print(f"Agente {self.jid} iniciando...")
        self.add_behaviour(self.SaludoBehaviour())


async def main():
    # Crear agente con JID en el servidor XMPP de SPADE.
    # El dominio del JID debe ser "localhost" (donde corre el servidor).
    # La contraseña puede ser cualquier cadena (el servidor
    # registra automáticamente a los agentes).
    agente = AgenteHolaMundo(
        "holamundo@localhost",   # JID del agente (dominio = localhost)
        "password"               # Contraseña (libre, registro automático)
    )
    await agente.start()
    # Esperar a que el agente se detenga por sí mismo
    await wait_until_finished(agente)


if __name__ == "__main__":
    # IMPORTANTE: el servidor XMPP debe estar ejecutándose
    # previamente con el comando: spade run
    spade.run(main())
