"""Jugador simulado — oráculo del comportamiento esperado del jugador.

Este simulador reproduce el comportamiento que se espera de un
agente jugador correcto. Se usa para dos fines:

* verificar el agente **tablero** del alumno, haciendo de los dos
  jugadores de la partida;
* hacer de jugador rival cuando se verifica el agente **jugador**
  del alumno.

No es un agente SPADE: es una clase ligera conectada a la
:class:`~tests.simuladores.sala_simulada.SalaSimulada`, con lógica
independiente de ``agentes/agente_jugador.py``.

Modos de funcionamiento (parámetro ``modo``):

* ``"normal"``           — inscripción y partida con estrategia
  posicional.
* ``"jugada_invalida"``  — en su primer turno propone una casilla
  ya ocupada (para provocar el ``game-over`` del tablero).
* ``"sin_jugada"``       — en su primer turno no envía ``move``
  (para provocar el ``game-over`` por timeout del tablero).
* ``"solo_inscripcion"`` — solicita inscribirse y no hace nada más
  (útil para provocar un ``join-refused`` o aislar el ``join``).

Direccionamiento del ``REQUEST join``: en el diseño de la Fase 1
el Jugador descubre el nick MUC del Tablero y le envía la
solicitud de inscripción de forma **directa** (sala/nick), no por
difusión. El simulador reproduce ese envío directo; el nick del
Tablero al que dirigir el ``REQUEST`` se indica con el parámetro
``nick_tablero`` (por defecto ``"tablero-sim"``, que es el nick
del propio :class:`TableroSimulado`).
"""
import asyncio
import logging
from typing import Any, Optional

from agentes.reglas_juego import (
    CASILLA_VACIA,
    RESULTADO_CONTINUA,
    SIMBOLO_O,
    SIMBOLO_X,
    aplicar_movimiento,
    crear_tablero_vacio,
    elegir_posicion,
    evaluar_resultado,
)
from ontologia.ontologia import (
    PREFIJO_THREAD_JOIN,
    crear_cuerpo_join,
    crear_cuerpo_move,
    crear_cuerpo_ok,
    crear_cuerpo_turn_result,
    crear_thread_unico,
    obtener_conversation_id,
)
from tests.simuladores.mensajeria import (
    construir_mensaje,
    extraer_nick,
    leer_cuerpo,
    privado,
)

logger = logging.getLogger(__name__)

# Plazo amplio de espera del simulador.
TIMEOUT_SIMULADOR_SEGUNDOS = 5.0


class JugadorSimulado:
    """Jugador simulado de una partida de tres en raya."""

    def __init__(
        self,
        sala: Any,
        nick: str = "jugador_sim",
        modo: str = "normal",
        retardo_inicial: float = 0.0,
        retardo_partida_inicial: float = 0.0,
        nick_tablero: str = "tablero_sim",
    ) -> None:
        self.sala = sala
        self.nick = nick
        self.modo = modo
        # Retardo antes de solicitar la inscripción: permite a las
        # pruebas decidir qué jugador se inscribe primero (y, por
        # tanto, recibe el símbolo X).
        self.retardo_inicial = retardo_inicial
        # Retardo entre la recepción del ``game-start`` y la entrada
        # al bucle de partida. Permite simular la carrera de arranque
        # descrita en ``doc/GUIA_THREAD_Y_GAME_START.md`` §5.3: el
        # simulador se queda «sordo» el tiempo justo para no atender
        # el primer ``CFP turn``, lo que obliga al Tablero a aplicar
        # su cortesía de reintento.
        self.retardo_partida_inicial = retardo_partida_inicial
        self.conexion = sala.conectar(nick, None)
        self.simbolo = ""
        # Nick MUC del Tablero al que se dirige el REQUEST join. Se
        # fija en el constructor (lo proporciona el escenario de
        # prueba a partir del nick del Tablero bajo prueba) y, tras
        # la respuesta AGREE, se reconfirma con el nick del
        # remitente para que los mensajes posteriores de la partida
        # se sigan dirigiendo al mismo Tablero.
        self.nick_tablero = nick_tablero

    async def ejecutar(self) -> None:
        """Conduce la inscripción y, si se acepta, la partida."""
        if self.retardo_inicial > 0:
            await asyncio.sleep(self.retardo_inicial)

        await self._solicitar_inscripcion()
        if self.modo == "solo_inscripcion":
            return

        respuesta = await self._esperar_respuesta_inscripcion()
        if respuesta is None:
            return
        self.simbolo, self.nick_tablero = respuesta

        datos = await self._esperar_game_start()
        if datos is None:
            return
        nick_rival, thread = datos
        await self._jugar(nick_rival, thread)

    # ── Inscripción ────────────────────────────────────────────

    async def _solicitar_inscripcion(self) -> None:
        """Envía la solicitud ``join`` directa al Tablero.

        Coherente con el diseño de la Fase 1: el Jugador, tras
        descubrir el nick MUC del Tablero, le dirige el ``REQUEST
        join`` en privado (``sala/nick_tablero``). No difunde la
        solicitud a la sala.
        """
        thread = crear_thread_unico(
            f"{self.nick}@localhost", PREFIJO_THREAD_JOIN,
        )
        destino = privado(self.sala.jid_sala, self.nick_tablero)
        await self.conexion.send(construir_mensaje(
            destino,
            crear_cuerpo_join(),
            thread=thread,
            conversation_id=obtener_conversation_id("join"),
        ))

    async def _esperar_respuesta_inscripcion(
        self,
    ) -> Optional[tuple[str, str]]:
        """Espera la respuesta del tablero a la solicitud de inscripción."""
        resultado: Optional[tuple[str, str]] = None
        fin = False
        while not fin:
            msg = await self.conexion.receive(
                timeout=TIMEOUT_SIMULADOR_SEGUNDOS,
            )
            if msg is None:
                fin = True
                continue
            cuerpo = leer_cuerpo(msg)
            accion = cuerpo.get("action")
            if accion == "join-accepted":
                resultado = (
                    str(cuerpo.get("symbol", "")),
                    extraer_nick(str(msg.sender)),
                )
                fin = True
            elif accion in ("join-refused", "join-timeout"):
                fin = True
        return resultado

    async def _esperar_game_start(self) -> Optional[tuple[str, str]]:
        """Espera el ``game-start`` que abre la partida."""
        datos: Optional[tuple[str, str]] = None
        fin = False
        while not fin:
            msg = await self.conexion.receive(
                timeout=TIMEOUT_SIMULADOR_SEGUNDOS,
            )
            if msg is None:
                fin = True
                continue
            cuerpo = leer_cuerpo(msg)
            if cuerpo.get("action") != "game-start":
                continue
            datos = (
                str(cuerpo.get("opponent", "")),
                str(cuerpo.get("thread", "")),
            )
            fin = True
        return datos

    # ── Partida ────────────────────────────────────────────────

    async def _jugar(self, nick_rival: str, thread: str) -> None:
        """Atiende los turnos hasta que la partida concluye.

        Conforme al diagrama de secuencia oficial del protocolo de
        partida, ante cada ``CFP turn`` el jugador activo responde
        con ``PROPOSE move`` y el rival con ``PROPOSE ok``; sin la
        respuesta del rival, el Tablero interpretaría el silencio
        como abandono.
        """
        if self.retardo_partida_inicial > 0:
            await asyncio.sleep(self.retardo_partida_inicial)
        tablero = crear_tablero_vacio()
        simbolo_rival = _rival(self.simbolo)
        fin = False
        while not fin:
            msg = await self.conexion.receive(
                timeout=TIMEOUT_SIMULADOR_SEGUNDOS,
            )
            if msg is None:
                fin = True
                continue
            cuerpo = leer_cuerpo(msg)
            accion = cuerpo.get("action")
            if accion == "game-over":
                fin = True
            elif accion == "turn":
                activo = cuerpo.get("active_symbol")
                if activo == self.simbolo:
                    tablero, fin = await self._jugar_turno(tablero, thread)
                elif activo == simbolo_rival:
                    await self._responder_ok(thread)
            elif accion == "move" and cuerpo.get("symbol") == simbolo_rival:
                posicion = cuerpo.get("position")
                if isinstance(posicion, int) and not isinstance(posicion, bool):
                    tablero = aplicar_movimiento(
                        tablero, posicion, simbolo_rival,
                    )
                    resultado, ganador = evaluar_resultado(
                        tablero, simbolo_rival,
                    )
                    # El protocolo obliga a que también el jugador
                    # rival envíe su INFORM turn-result tras cada
                    # confirmación pública.
                    await self.conexion.send(construir_mensaje(
                        privado(self.sala.jid_sala, self.nick_tablero),
                        crear_cuerpo_turn_result(resultado, ganador),
                        thread=thread,
                    ))
                    fin = resultado != RESULTADO_CONTINUA

    async def _responder_ok(self, thread: str) -> None:
        """Envía un ``PROPOSE ok`` privado al Tablero.

        Es la respuesta al ``CFP turn`` cuando el simulador no es el
        jugador activo: confirma la convocatoria sin proponer
        jugada. El protocolo exige esta confirmación; sin ella, el
        Tablero abortaría la partida por silencio del rival.
        """
        await self.conexion.send(construir_mensaje(
            privado(self.sala.jid_sala, self.nick_tablero),
            crear_cuerpo_ok(),
            thread=thread,
        ))

    async def _jugar_turno(
        self, tablero: list[str], thread: str,
    ) -> tuple[list[str], bool]:
        """Resuelve un turno propio según el modo configurado."""
        if self.modo == "sin_jugada":
            # No se envía 'move': el tablero debe abortar por timeout.
            return (tablero, True)

        posicion = self._elegir_posicion(tablero)
        await self.conexion.send(construir_mensaje(
            privado(self.sala.jid_sala, self.nick_tablero),
            crear_cuerpo_move(posicion),
            thread=thread,
        ))

        confirmada = await self._esperar_confirmacion()
        if not confirmada:
            return (tablero, True)

        tablero = aplicar_movimiento(tablero, posicion, self.simbolo)
        resultado, ganador = evaluar_resultado(tablero, self.simbolo)
        await self.conexion.send(construir_mensaje(
            privado(self.sala.jid_sala, self.nick_tablero),
            crear_cuerpo_turn_result(resultado, ganador),
            thread=thread,
        ))
        return (tablero, resultado != RESULTADO_CONTINUA)

    def _elegir_posicion(self, tablero: list[str]) -> int:
        """Elige la casilla a proponer según el modo del simulador."""
        if self.modo == "jugada_invalida":
            # Propone deliberadamente una casilla ya ocupada.
            ocupadas = [
                indice for indice, casilla in enumerate(tablero)
                if casilla != CASILLA_VACIA
            ]
            eleccion = ocupadas[0] if ocupadas else elegir_posicion(tablero)
        else:
            eleccion = elegir_posicion(tablero)
        return eleccion

    async def _esperar_confirmacion(self) -> bool:
        """Espera la confirmación ``move`` de la jugada propia."""
        confirmada = False
        fin = False
        while not fin:
            msg = await self.conexion.receive(
                timeout=TIMEOUT_SIMULADOR_SEGUNDOS,
            )
            if msg is None:
                fin = True
                continue
            cuerpo = leer_cuerpo(msg)
            accion = cuerpo.get("action")
            if accion == "game-over":
                fin = True
            elif accion == "move" and cuerpo.get("symbol") == self.simbolo:
                confirmada = True
                fin = True
        return confirmada


# ── Funciones auxiliares ───────────────────────────────────────

def _rival(simbolo: str) -> str:
    """Devuelve el símbolo del jugador contrario."""
    return SIMBOLO_O if simbolo == SIMBOLO_X else SIMBOLO_X