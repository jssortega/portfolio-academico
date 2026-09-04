"""Tablero simulado — oráculo del comportamiento esperado del árbitro.

Este simulador reproduce el comportamiento que se espera de un
agente tablero correcto. Se usa para verificar el agente
**jugador** del alumno: hace de árbitro de la partida mientras las
pruebas observan si el jugador responde a la ontología como debe.

No es un agente SPADE: es una clase ligera que se conecta a la
:class:`~tests.simuladores.sala_simulada.SalaSimulada` y conduce el
protocolo. Su lógica es independiente de ``agentes/agente_tablero.py``
para que sirva de referencia imparcial.

Modos de funcionamiento (parámetro ``modo``):

* ``"normal"``  — registro de dos jugadores y partida completa.
* ``"rechaza"`` — responde ``join-refused`` a la primera solicitud.
* ``"timeout_registro"`` — responde ``join-timeout`` a la primera
  solicitud (como si nunca llegara un segundo jugador).
"""
import asyncio
import logging
from typing import Any, Optional

from agentes.reglas_juego import (
    RESULTADO_EMPATE,
    RESULTADO_VICTORIA,
    SIMBOLO_O,
    SIMBOLO_X,
    aplicar_movimiento,
    crear_tablero_vacio,
    evaluar_resultado,
    posicion_libre,
)
from ontologia.ontologia import (
    PREFIJO_THREAD_GAME,
    crear_cuerpo_game_over,
    crear_cuerpo_game_start,
    crear_cuerpo_join_accepted,
    crear_cuerpo_join_refused,
    crear_cuerpo_join_timeout,
    crear_cuerpo_move_confirmado,
    crear_cuerpo_turn,
    crear_thread_unico,
)
from tests.simuladores.mensajeria import (
    construir_mensaje,
    extraer_nick,
    leer_cuerpo,
    privado,
)

logger = logging.getLogger(__name__)

# Plazo amplio de espera del simulador: el agente real bajo prueba,
# con sus tiempos ya acelerados, siempre actúa mucho antes.
TIMEOUT_SIMULADOR_SEGUNDOS = 5.0

# Número de jugadores de una partida.
NUM_JUGADORES = 2


class TableroSimulado:
    """Árbitro simulado de una partida de tres en raya."""

    def __init__(
        self, sala: Any, nick: str = "tablero_sim", modo: str = "normal",
        retardo_primer_cfp: float = 0.1,
    ) -> None:
        self.sala = sala
        self.nick = nick
        self.modo = modo
        # Retardo entre el envío del ``game-start`` y la difusión del
        # primer ``CFP turn``. Por defecto, 0.1 s para reproducir la
        # pausa que da margen al Jugador a registrar su comportamiento
        # de partida. Las pruebas pueden alargarlo para verificar que
        # el Jugador no cierra la partida por un plazo local propio.
        self.retardo_primer_cfp = retardo_primer_cfp
        self.conexion = sala.conectar(nick, None)
        # Informe de la partida disputada (None mientras no termina).
        self.informe: Optional[dict[str, Any]] = None

    async def ejecutar(self) -> None:
        """Conduce el registro y, si procede, la partida completa."""
        inscritos = await self._registro()
        if self.modo in ("rechaza", "timeout_registro"):
            return
        if len(inscritos) >= NUM_JUGADORES:
            await self._partida(inscritos)

    # ── Registro ───────────────────────────────────────────────

    async def _registro(self) -> dict[str, str]:
        """Acepta inscripciones hasta completar la mesa."""
        inscritos: dict[str, str] = {}
        simbolos = (SIMBOLO_X, SIMBOLO_O)
        fin = False
        while not fin:
            msg = await self.conexion.receive(
                timeout=TIMEOUT_SIMULADOR_SEGUNDOS,
            )
            if msg is None:
                fin = True
                continue
            cuerpo = leer_cuerpo(msg)
            if cuerpo.get("action") != "join":
                continue
            nick = extraer_nick(str(msg.sender))
            if not nick or nick in inscritos:
                continue
            if self.modo == "rechaza":
                await self._responder(
                    nick, crear_cuerpo_join_refused("full"), msg.thread,
                )
                fin = True
            elif self.modo == "timeout_registro":
                await self._responder(
                    nick, crear_cuerpo_join_timeout("no opponent"),
                    msg.thread,
                )
                fin = True
            elif len(inscritos) >= NUM_JUGADORES:
                await self._responder(
                    nick, crear_cuerpo_join_refused("full"), msg.thread,
                )
            else:
                simbolo = simbolos[len(inscritos)]
                inscritos[nick] = simbolo
                await self._responder(
                    nick, crear_cuerpo_join_accepted(simbolo), msg.thread,
                )
                if len(inscritos) >= NUM_JUGADORES:
                    fin = True
        return inscritos

    # ── Partida ────────────────────────────────────────────────

    async def _partida(self, inscritos: dict[str, str]) -> None:
        """Arbitra la partida entre los dos jugadores inscritos."""
        nick_por_simbolo = {s: n for n, s in inscritos.items()}
        thread = crear_thread_unico(
            "tablero-sim@localhost", PREFIJO_THREAD_GAME,
        )
        for simbolo, nick in nick_por_simbolo.items():
            rival = nick_por_simbolo[_rival(simbolo)]
            await self._responder(
                nick, crear_cuerpo_game_start(rival, thread), thread,
            )

        # Pausa configurable entre el ``game-start`` y el primer
        # ``CFP turn``. Por defecto da margen al Jugador a registrar
        # su comportamiento de partida; las pruebas pueden alargarla
        # para verificar que la espera del Jugador no caduca por un
        # plazo local propio (§5.2 del diseño Fase 2).
        if self.retardo_primer_cfp > 0:
            await asyncio.sleep(self.retardo_primer_cfp)

        tablero = crear_tablero_vacio()
        activo = SIMBOLO_X
        turnos = 0
        informe: Optional[dict[str, Any]] = None
        while informe is None:
            await self._difundir(crear_cuerpo_turn(activo), thread)
            nick_activo = nick_por_simbolo[activo]
            jugada = await self._esperar("move", nick_activo)
            posicion = _posicion_de(jugada)
            if posicion is None or not posicion_libre(tablero, posicion):
                razon = "timeout" if jugada is None else "invalid"
                ganador = _rival(activo)
                await self._difundir(
                    crear_cuerpo_game_over(razon, ganador), thread,
                )
                informe = {"result": "aborted", "winner": ganador}
            else:
                tablero = aplicar_movimiento(tablero, posicion, activo)
                turnos += 1
                await self._difundir(
                    crear_cuerpo_move_confirmado(posicion, activo), thread,
                )
                await self._esperar("turn-result", nick_activo)
                resultado, ganador = evaluar_resultado(tablero, activo)
                if resultado == RESULTADO_VICTORIA:
                    informe = {"result": "win", "winner": ganador}
                elif resultado == RESULTADO_EMPATE:
                    informe = {"result": "draw", "winner": None}
                else:
                    activo = _rival(activo)
        informe["turns"] = turnos
        informe["board"] = tablero
        self.informe = informe

    # ── Envío y recepción ──────────────────────────────────────

    async def _responder(
        self, nick: str, contenido: Any, thread: Optional[str],
    ) -> None:
        """Envía un mensaje privado a un ocupante de la sala."""
        destino = privado(self.sala.jid_sala, nick)
        await self.conexion.send(
            construir_mensaje(destino, contenido, thread=thread),
        )

    async def _difundir(self, contenido: Any, thread: str) -> None:
        """Difunde un mensaje a toda la sala."""
        await self.conexion.send(construir_mensaje(
            self.sala.jid_sala, contenido, thread=thread, groupchat=True,
        ))

    async def _esperar(
        self, accion: str, nick_emisor: str,
    ) -> Optional[Any]:
        """Espera un mensaje de una acción y un emisor concretos."""
        encontrado: Optional[Any] = None
        fin = False
        while not fin:
            msg = await self.conexion.receive(
                timeout=TIMEOUT_SIMULADOR_SEGUNDOS,
            )
            if msg is None:
                fin = True
                continue
            cuerpo = leer_cuerpo(msg)
            if cuerpo.get("action") != accion:
                continue
            if extraer_nick(str(msg.sender)) != nick_emisor:
                continue
            encontrado = msg
            fin = True
        return encontrado


# ── Funciones auxiliares ───────────────────────────────────────

def _rival(simbolo: str) -> str:
    """Devuelve el símbolo del jugador contrario."""
    return SIMBOLO_O if simbolo == SIMBOLO_X else SIMBOLO_X


def _posicion_de(jugada: Optional[Any]) -> Optional[int]:
    """Extrae el campo ``position`` de un mensaje ``move``."""
    posicion: Optional[int] = None
    if jugada is not None:
        valor = leer_cuerpo(jugada).get("position")
        if isinstance(valor, int) and not isinstance(valor, bool):
            posicion = valor
    return posicion