"""Supervisor simulado — oráculo del protocolo de informe.

Reproduce la única interacción del supervisor del profesor que el
agente tablero del alumno debe atender: la solicitud de informe de
partida (``game-report``). Se usa para verificar que el tablero
responde a esa solicitud conforme a la ontología.

Implementa la **cortesía de reintento 1×** descrita en
``doc/GUIA_THREAD_Y_GAME_START.md`` §5.4: si la primera solicitud
agota el plazo sin respuesta, el simulador la reenvía una segunda
y última vez antes de dar el informe por no entregado. La regla
es paralela a la cortesía del Tablero ante el primer ``CFP turn``
(§5.3) y reproduce, en versión simplificada para pruebas, el
mecanismo de retroceso del agente supervisor real (en
``feature/agente-supervisor:behaviours/supervisor_behaviours.py``).

No es un agente SPADE: es una clase ligera conectada a la
:class:`~tests.simuladores.sala_simulada.SalaSimulada`.
"""
import logging
from typing import Any, Optional

from ontologia.ontologia import (
    PREFIJO_THREAD_REPORT,
    crear_cuerpo_game_report_request,
    crear_thread_unico,
    obtener_conversation_id,
)
from tests.simuladores.mensajeria import construir_mensaje, privado

logger = logging.getLogger(__name__)

# Plazo de espera de la respuesta del tablero a UN solo envío. La
# cortesía aplica dos veces seguidas como máximo (envío inicial +
# un reintento), de modo que el plazo total que la prueba puede
# esperar es 2 × TIMEOUT_SIMULADOR_SEGUNDOS.
TIMEOUT_SIMULADOR_SEGUNDOS = 5.0


class SupervisorSimulado:
    """Supervisor simulado que solicita el informe de una partida.

    Cada llamada a :meth:`solicitar_informe` realiza, conforme a
    ``doc/GUIA_THREAD_Y_GAME_START.md`` §5.4:

    1. Envío inicial del ``REQUEST game-report`` con un ``thread``
       único de prefijo ``report-``.
    2. Si vence el plazo sin respuesta, **un único reintento** del
       mismo mensaje (mismo ``thread``, mismo cuerpo, misma
       performativa). El reintento se contabiliza en el atributo
       :attr:`reintentos_realizados` para que las pruebas puedan
       comprobar que la cortesía se ha disparado.
    3. Si la segunda espera también vence, devuelve ``None``.
    """

    def __init__(self, sala: Any, nick: str = "supervisor_sim") -> None:
        self.sala = sala
        self.nick = nick
        self.conexion = sala.conectar(nick, None)
        # Cuenta los reintentos que la cortesía §5.4 ha disparado
        # a lo largo de la vida del simulador (sumando todas las
        # llamadas a :meth:`solicitar_informe`).
        self.reintentos_realizados = 0

    async def solicitar_informe(
        self, nick_tablero: str,
    ) -> Optional[Any]:
        """Pide a un tablero el informe de su partida y espera respuesta.

        Envía un ``game-report`` (REQUEST) en privado al tablero,
        con ``conversation-id`` ``game-report`` y un ``thread``
        único. Si el tablero no responde dentro del plazo, aplica
        la cortesía §5.4 reenviando exactamente el mismo mensaje
        una segunda y última vez antes de devolver ``None``.

        Args:
            nick_tablero: Nick del tablero al que se pide el informe.

        Returns:
            El mensaje de respuesta del tablero (``game-report``
            INFORM o REFUSE), o ``None`` si tampoco contesta tras
            el reintento de cortesía.
        """
        thread = crear_thread_unico(
            f"{self.nick}@localhost", PREFIJO_THREAD_REPORT,
        )
        mensaje = construir_mensaje(
            privado(self.sala.jid_sala, nick_tablero),
            crear_cuerpo_game_report_request(),
            thread=thread,
            conversation_id=obtener_conversation_id("game-report"),
        )

        # Envío inicial + espera.
        await self.conexion.send(mensaje)
        respuesta = await self.conexion.receive(
            timeout=TIMEOUT_SIMULADOR_SEGUNDOS,
        )
        if respuesta is not None:
            resultado = respuesta
        else:
            # Cortesía §5.4: reintento 1×. El mensaje es el mismo
            # objeto (mismo thread, mismo cuerpo, misma metadata).
            self.reintentos_realizados += 1
            logger.info(
                "SupervisorSimulado %s | cortesía §5.4: el primer "
                "REQUEST game-report a %s no obtuvo respuesta; "
                "reenviando (thread=%s)",
                self.nick, nick_tablero, thread,
            )
            await self.conexion.send(mensaje)
            resultado = await self.conexion.receive(
                timeout=TIMEOUT_SIMULADOR_SEGUNDOS,
            )
        return resultado
