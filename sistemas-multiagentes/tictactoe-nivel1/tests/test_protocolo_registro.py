"""Pruebas del protocolo de REGISTRO en el tablero.

El protocolo de registro (acción ``join`` de la ontología) es el
primero que intercambian los agentes del alumno: el jugador,
después de descubrir un Tablero disponible en la sala MUC, le
**envía en privado** una solicitud de inscripción; el tablero le
responde aceptando (``AGREE``), rechazando (``REFUSE``) o
avisando de que no llegó un rival (``FAILURE``).

Estas pruebas verifican ese protocolo con la técnica de **caja
negra**: montan el agente real del alumno sobre una sala MUC
simulada y le enfrentan a un simulador del agente contrario,
después comprueban que los mensajes producidos cumplen la
ontología (performativa, cuerpo, ``conversation-id`` e hilo).

Mensajes verificados:

* ``join``          — REQUEST  Jugador → Tablero (directo).
* ``join-accepted`` — AGREE    Tablero → Jugador (símbolo asignado).
* ``join-refused``  — REFUSE   Tablero → Jugador (mesa llena).
* ``join-timeout``  — FAILURE  Tablero → Jugador (sin rival).

Convenciones de nombrado:

* Los **nombres de agente** (parte local del JID) y los **nicks
  MUC** siguen la factoría de :mod:`config.configuracion`. La
  factoría usa guiones bajos para la parte local del JID
  (``tablero_<usuario>_NN``, ``jugador_<usuario>_n<L>_NN``) y
  guiones para el nick MUC (``tablero_<usuario>-NN``,
  ``jugador_<usuario>-n<L>-NN``). Los simuladores adoptan la
  misma convención usando un usuario ficticio (``sim``, ``p01``…)
  como nick base.

Notas sobre el direccionamiento:

* El ``REQUEST join`` viaja **directo** al nick MUC del Tablero
  (``sala@servicio/nick_tablero``). La utilidad de descubrimiento
  (sección 5.8 del diseño) es la responsable de que el Jugador
  conozca ese nick. Su funcionamiento se verifica aparte en
  ``tests/test_descubrimiento.py``; aquí el arnés inyecta el
  Tablero directamente en ``tableros_disponibles`` con
  :func:`anunciar_tablero_descubierto` para concentrar la prueba
  en el protocolo posterior.
* Las respuestas del Tablero (``AGREE``, ``REFUSE``, ``FAILURE``)
  viajan en privado al nick MUC del Jugador solicitante,
  reutilizando el ``thread`` del ``REQUEST``.

Notas sobre la equidad:

* El Tablero usa un **gestor de equidad de inscripciones**
  (sección 4.6 del diseño) para repartir las plazas con
  imparcialidad cuando varias solicitudes llegan a la vez.
* Las pruebas que ejercitan esa lógica concreta (descarte por
  equidad cuando varias solicitudes compiten por la última plaza)
  se marcan como **voluntarias** con ``@pytest.mark.xfail``: el
  alumno no está obligado a implementar la equidad, así que un
  fallo aquí no se contabiliza como incidencia.
"""
import asyncio

import pytest

from agentes.agente_jugador import AgenteJugador
from agentes.agente_tablero import AgenteTablero
from ontologia.ontologia import (
    PERFORMATIVA_AGREE,
    PERFORMATIVA_FAILURE,
    PERFORMATIVA_REFUSE,
    PERFORMATIVA_REQUEST,
)
from tests.simuladores import (
    SALA_DE_PRUEBA,
    JugadorSimulado,
    SalaSimulada,
    TableroSimulado,
    acelerar_tiempos,
    detener_tareas,
    ejecutar_escenario,
    montar_agente,
    perfil_xmpp_de_prueba,
)
from tests.simuladores.arnes import anunciar_tablero_descubierto


# ── Nombres y nicks coherentes con la factoría ─────────────────
#
# El alumno real bajo prueba se llama "demo" (usuario UJA), nivel
# 1 de estrategia, único agente de cada rol. La factoría produce
# para esa configuración los nombres y nicks siguientes:
#
#   - JID localpart Tablero : tablero_demo_01    (guiones bajos)
#   - Nick MUC      Tablero : tablero_demo-01    (guion en el sufijo)
#   - JID localpart Jugador : jugador_demo_n1_01
#   - Nick MUC      Jugador : jugador_demo-n1-01
#
# Los simuladores adoptan la misma convención con usuarios
# ficticios distintos para no colisionar con el agente bajo
# prueba.
NOMBRE_JUGADOR_ALUMNO = "jugador_demo_n1_01"
NICK_JUGADOR_ALUMNO = "jugador_demo-n1-01"

NOMBRE_TABLERO_ALUMNO = "tablero_demo_01"
NICK_TABLERO_ALUMNO = "tablero_demo-01"

# Nick MUC del Tablero del simulador, usado por el
# :class:`JugadorSimulado` como destinatario del ``REQUEST join``
# y por el arnés para anunciarlo en ``tableros_disponibles`` del
# Jugador bajo prueba.
NICK_TABLERO_SIMULADO = "tablero_sim-01"


def _nick_jugador_simulado(indice: int) -> str:
    """Devuelve el nick MUC del jugador simulado número ``indice``.

    Mantiene el formato de la factoría
    (``jugador_<usuario>-n<L>-NN``) usando ``p<NN>`` como usuario
    ficticio, de modo que los nicks de los simuladores no choquen
    entre sí ni con el del agente bajo prueba.
    """
    return f"jugador_p{indice:02d}-n1-01"


@pytest.fixture(autouse=True)
def _acelerar(monkeypatch):
    """Acorta los plazos de espera de los simuladores en cada prueba."""
    acelerar_tiempos(monkeypatch)


async def _montar_jugador(
    sala: SalaSimulada,
    nick: str = NICK_JUGADOR_ALUMNO,
    max_partidas: int = 1,
) -> object:
    """Monta un Jugador del alumno sobre la sala simulada.

    Tras el montaje, el Tablero del simulador queda anunciado en
    ``tableros_disponibles`` del Jugador como si lo hubiera
    descubierto por presencia MUC. Eso desbloquea el coordinador
    ``ComportamientoBusquedaDeMesas`` para que autorice un
    intento de inscripción contra ese Tablero.

    Args:
        sala: sala MUC simulada en la que se monta el agente.
        nick: nick MUC con el que el Jugador ocupa la sala.
        max_partidas: tope de partidas simultáneas que el Jugador
            consiente. Las pruebas que verifican la capacidad de
            iniciar más de una inscripción suben este valor.
    """
    montado = await montar_agente(
        AgenteJugador, NOMBRE_JUGADOR_ALUMNO,
        perfil_xmpp_de_prueba(),
        {"nick_muc": nick, "max_partidas": max_partidas}, sala,
    )
    anunciar_tablero_descubierto(montado, NICK_TABLERO_SIMULADO)
    return montado


async def _montar_tablero(
    sala: SalaSimulada, nick: str = NICK_TABLERO_ALUMNO,
) -> object:
    """Monta un Tablero del alumno sobre la sala simulada."""
    return await montar_agente(
        AgenteTablero, NOMBRE_TABLERO_ALUMNO,
        perfil_xmpp_de_prueba(), {"nick_muc": nick}, sala,
    )


# ══════════════════════════════════════════════════════════════
#  El jugador del alumno en el protocolo de registro
# ══════════════════════════════════════════════════════════════

class TestRegistroJugador:
    """Verifica el agente JUGADOR del alumno durante el registro."""

    @pytest.mark.asyncio
    async def test_jugador_envia_solicitud_join_directa_al_tablero(self):
        """El jugador inicia el registro enviando un ``join`` directo.

        En el diseño de la Fase 1, el Jugador descubre el nick MUC
        del Tablero y le dirige el ``REQUEST join`` en privado
        (``sala@servicio/nick_tablero``). El mensaje debe ser un
        REQUEST de la ontología, con ``conversation-id = "join"`` y
        un ``thread`` único que permita correlacionar la respuesta
        del Tablero.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        jugador = await _montar_jugador(sala)
        tablero = TableroSimulado(
            sala, nick=NICK_TABLERO_SIMULADO, modo="normal",
        )

        await ejecutar_escenario(jugador.correr_unica(), tablero.ejecutar())

        solicitudes = sala.buscar(accion="join", emisor=jugador.nick)
        assert len(solicitudes) == 1
        join = solicitudes[0]
        assert join.performativa == PERFORMATIVA_REQUEST
        assert join.conversacion == "join"
        # Destino directo al nick MUC del Tablero, no difusión.
        assert join.destino == NICK_TABLERO_SIMULADO
        assert join.thread
        assert join.valido, join.errores

    @pytest.mark.asyncio
    async def test_jugador_completa_la_inscripcion_tras_join_accepted(self):
        """Tras un ``join-accepted``, la inscripción queda cerrada.

        La prueba comprueba el cierre del registro **por sus mensajes
        observables**, sin inspeccionar el estado interno del Jugador:
        este emite una **única** solicitud ``join`` válida y el
        Tablero le responde con un ``join-accepted`` (AGREE) que le
        asigna un símbolo legal. Que el Jugador no reintente la
        inscripción una vez aceptada evidencia que dio el registro por
        cerrado. Al no acoplarse a ningún atributo interno, cualquier
        implementación conforme satisface la prueba.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        jugador = await _montar_jugador(sala)
        tablero = TableroSimulado(
            sala, nick=NICK_TABLERO_SIMULADO, modo="normal",
        )

        await ejecutar_escenario(jugador.correr_unica(), tablero.ejecutar())

        # Una sola solicitud: aceptada la inscripción, el Jugador no
        # reintenta (tope de una partida simultánea en este escenario).
        solicitudes = sala.buscar(accion="join", emisor=jugador.nick)
        assert len(solicitudes) == 1
        aceptaciones = sala.buscar(
            accion="join-accepted", emisor=tablero.nick,
        )
        assert len(aceptaciones) == 1
        assert aceptaciones[0].cuerpo.get("symbol") in ("X", "O")

    @pytest.mark.asyncio
    async def test_jugador_se_detiene_si_el_tablero_lo_rechaza(self):
        """Ante un ``join-refused`` el jugador termina con orden.

        La prueba lo verifica **por los mensajes observables**: el
        Jugador envía su ``join``, recibe el ``join-refused`` (REFUSE)
        y, en consecuencia, **no llega a jugar** —no emite ningún
        ``move``—. No se inspecciona el estado interno del Jugador, de
        modo que la prueba no impone cómo representa internamente el
        abandono.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        jugador = await _montar_jugador(sala)
        tablero = TableroSimulado(
            sala, nick=NICK_TABLERO_SIMULADO, modo="rechaza",
        )

        await ejecutar_escenario(jugador.correr_unica(), tablero.ejecutar())

        assert sala.buscar(accion="join", emisor=jugador.nick)
        rechazos = sala.buscar(accion="join-refused", emisor=tablero.nick)
        assert len(rechazos) >= 1
        # Rechazada la inscripción, el Jugador no inicia partida alguna.
        assert not sala.buscar(accion="move", emisor=jugador.nick)

    @pytest.mark.asyncio
    async def test_jugador_se_detiene_si_no_llega_rival(self):
        """Ante un ``join-timeout`` el jugador termina con orden.

        La prueba lo verifica **por los mensajes observables**: el
        Jugador envía su ``join``, recibe el ``join-timeout`` (FAILURE)
        y **no llega a jugar** —no emite ningún ``move``—, en lugar de
        quedarse esperando indefinidamente un ``game-start`` que no
        llegará. No se inspecciona el estado interno del Jugador.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        jugador = await _montar_jugador(sala)
        tablero = TableroSimulado(
            sala, nick=NICK_TABLERO_SIMULADO, modo="timeout_registro",
        )

        await ejecutar_escenario(jugador.correr_unica(), tablero.ejecutar())

        assert sala.buscar(accion="join", emisor=jugador.nick)
        avisos = sala.buscar(accion="join-timeout", emisor=tablero.nick)
        assert len(avisos) >= 1
        # Sin rival y avisado del timeout, el Jugador no inicia partida.
        assert not sala.buscar(accion="move", emisor=jugador.nick)

    @pytest.mark.asyncio
    async def test_jugador_intenta_mas_de_una_inscripcion(self):
        """El jugador intenta inscribirse en más de una partida.

        Para sostener partidas simultáneas, el Jugador debe ser
        capaz de iniciar varias inscripciones mientras tenga hueco
        entre ``max_partidas``. Esta prueba ejerce ese
        comportamiento subiendo ``max_partidas`` a 2 y comprobando
        que el coordinador
        ``ComportamientoBusquedaDeMesas`` emite **más de una**
        solicitud ``REQUEST join`` durante el escenario.

        El Tablero simulado responde aceptando la primera
        solicitud y, una vez completada esa inscripción, el
        coordinador del Jugador detecta hueco (``compromisos < max``)
        y autoriza un segundo intento de inscripción contra el
        mismo Tablero. La prueba pasa si **al menos dos**
        solicitudes salen del Jugador.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        jugador = await _montar_jugador(sala, max_partidas=2)
        tablero = TableroSimulado(
            sala, nick=NICK_TABLERO_SIMULADO, modo="normal",
        )

        await ejecutar_escenario(jugador.correr_unica(), tablero.ejecutar())

        solicitudes = sala.buscar(accion="join", emisor=jugador.nick)
        assert len(solicitudes) >= 2


# ══════════════════════════════════════════════════════════════
#  El tablero del alumno en el protocolo de registro
# ══════════════════════════════════════════════════════════════

class TestRegistroTablero:
    """Verifica el agente TABLERO del alumno durante el registro."""

    @pytest.mark.asyncio
    async def test_tablero_acepta_la_inscripcion_con_join_accepted(self):
        """El tablero responde a un ``join`` con ``join-accepted``.

        La respuesta debe ser un AGREE con un símbolo válido y
        dirigida en privado al jugador que se inscribió.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        nick_jugador = _nick_jugador_simulado(1)
        jugador = JugadorSimulado(
            sala, nick_jugador, modo="solo_inscripcion",
            nick_tablero=NICK_TABLERO_ALUMNO,
        )

        await ejecutar_escenario(tablero.correr_unica(), jugador.ejecutar())

        aceptaciones = sala.buscar(
            accion="join-accepted", emisor=tablero.nick,
        )
        assert len(aceptaciones) == 1
        aceptacion = aceptaciones[0]
        assert aceptacion.performativa == PERFORMATIVA_AGREE
        assert aceptacion.cuerpo.get("symbol") in ("X", "O")
        assert aceptacion.destino == nick_jugador
        assert aceptacion.valido, aceptacion.errores

    @pytest.mark.asyncio
    async def test_tablero_asigna_x_al_primero_y_o_al_segundo(self):
        """El tablero asigna ``X`` al primer inscrito y ``O`` al segundo.

        Los dos jugadores llegan con un retardo suficiente para
        caer en **ventanas de equidad distintas**: el primero entra
        cuando la mesa está vacía y recibe ``X``; el segundo lo
        hace después, durante ``WAIT_PLAYER2``, y recibe ``O``.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        nick_primero = _nick_jugador_simulado(1)
        nick_segundo = _nick_jugador_simulado(2)
        primero = JugadorSimulado(
            sala, nick_primero, modo="solo_inscripcion",
            retardo_inicial=0.0, nick_tablero=NICK_TABLERO_ALUMNO,
        )
        segundo = JugadorSimulado(
            sala, nick_segundo, modo="solo_inscripcion",
            retardo_inicial=0.3, nick_tablero=NICK_TABLERO_ALUMNO,
        )

        await ejecutar_escenario(
            tablero.correr_unica(), primero.ejecutar(), segundo.ejecutar(),
        )

        por_destino = {
            m.destino: m
            for m in sala.buscar(accion="join-accepted", emisor=tablero.nick)
        }
        assert por_destino[nick_primero].cuerpo.get("symbol") == "X"
        assert por_destino[nick_segundo].cuerpo.get("symbol") == "O"

    @pytest.mark.xfail(
        reason=(
            "Prueba voluntaria: depende del descarte por equidad del "
            "gestor de inscripciones (sección 4.6 del diseño). Verifica "
            "que, cuando dos solicitudes compiten por la última plaza, "
            "la no elegida recibe REFUSE 'full'. La equidad es un "
            "comportamiento opcional para el alumno."
        ),
        strict=False,
    )
    @pytest.mark.asyncio
    async def test_tablero_rechaza_un_tercer_jugador_por_equidad(self):
        """El tablero rechaza al tercer jugador en condición de carrera.

        Escenario: el primer jugador inscribe normalmente y queda
        en ``WAIT_PLAYER2``. Tras un retardo lo bastante largo para
        que se cierre la primera ventana de equidad, los jugadores
        segundo y tercero llegan **a la vez**: ambos caen dentro de
        la misma ventana del gestor de equidad. El gestor elige al
        segundo (FIFO en el desempate) y descarta al tercero, que
        recibe un ``REFUSE`` con ``reason = "full"``.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        nick_primero = _nick_jugador_simulado(1)
        nick_segundo = _nick_jugador_simulado(2)
        nick_tercero = _nick_jugador_simulado(3)
        primero = JugadorSimulado(
            sala, nick_primero, modo="solo_inscripcion",
            retardo_inicial=0.0, nick_tablero=NICK_TABLERO_ALUMNO,
        )
        segundo = JugadorSimulado(
            sala, nick_segundo, modo="solo_inscripcion",
            retardo_inicial=0.4, nick_tablero=NICK_TABLERO_ALUMNO,
        )
        tercero = JugadorSimulado(
            sala, nick_tercero, modo="solo_inscripcion",
            retardo_inicial=0.4, nick_tablero=NICK_TABLERO_ALUMNO,
        )

        await ejecutar_escenario(
            tablero.correr_unica(),
            primero.ejecutar(), segundo.ejecutar(), tercero.ejecutar(),
        )

        rechazos = [
            m for m in sala.buscar(
                accion="join-refused", emisor=tablero.nick,
            )
            if m.destino == nick_tercero
        ]
        assert len(rechazos) == 1
        rechazo = rechazos[0]
        assert rechazo.performativa == PERFORMATIVA_REFUSE
        assert rechazo.cuerpo.get("reason") == "full"
        assert rechazo.valido, rechazo.errores

    @pytest.mark.asyncio
    async def test_tablero_avisa_con_join_timeout_si_falta_rival(self):
        """El tablero avisa con ``join-timeout`` si no llega un rival.

        El único jugador inscrito debe recibir un FAILURE con la
        razón ``no opponent`` tras el plazo ``timeout_inscripcion``,
        en lugar de quedarse esperando un ``game-start`` que nunca
        llegará.

        El escenario conduce los comportamientos del Tablero en
        segundo plano y espera explícitamente algo más que
        ``timeout_inscripcion``: la transición a ``SEND_FAILURE``
        debe producirse después del plazo y la cancelación
        prematura por reposo de :meth:`correr_unica` se evita
        usando :meth:`iniciar_ciclicos`.
        """
        sala = SalaSimulada(SALA_DE_PRUEBA)
        tablero = await _montar_tablero(sala)
        nick_jugador = _nick_jugador_simulado(1)
        jugador = JugadorSimulado(
            sala, nick_jugador, modo="solo_inscripcion",
            nick_tablero=NICK_TABLERO_ALUMNO,
        )

        tareas = tablero.iniciar_ciclicos()
        try:
            await jugador.ejecutar()
            # Plazo holgado sobre ``timeout_inscripcion`` (1 s en el
            # arnés) para que WAIT_PLAYER2 venza y SEND_FAILURE
            # alcance a publicar el FAILURE antes de cancelar.
            await asyncio.sleep(1.5)
        finally:
            await detener_tareas(tareas)

        avisos = sala.buscar(accion="join-timeout", emisor=tablero.nick)
        assert len(avisos) == 1
        aviso = avisos[0]
        assert aviso.performativa == PERFORMATIVA_FAILURE
        assert aviso.cuerpo.get("reason") == "no opponent"
        assert aviso.destino == nick_jugador
        assert aviso.valido, aviso.errores
