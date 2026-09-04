import pytest

from agentes.agente_jugador import AgenteJugador


@pytest.fixture
def agente_jugador():
    """Crea una instancia del AgenteJugador con un límite de 2 partidas."""
    # 1. Instanciamos solo con JID y password (como exige SPADE por defecto)
    jugador = AgenteJugador("jugador@test", "secret")

    # 2. Le inyectamos manualmente las variables que necesita
    jugador.nivel = 1
    jugador.limite_partidas_simultaneas = 2

    # 3. Inicializamos sus diccionarios
    jugador.partidas_activas = {}
    jugador.partidas_pendientes = {}

    return jugador


def test_filtrado_tableros_muc(agente_jugador) -> None:
    """La lógica de filtrado de tableros en MUC reconoce el prefijo tablero_."""

    # Casos CORRECTOS
    assert agente_jugador.es_tablero_valido("tablero_1") is True
    assert agente_jugador.es_tablero_valido("tablero_alfa") is True

    # Casos INCORRECTOS
    assert agente_jugador.es_tablero_valido("supervisor") is False
    assert agente_jugador.es_tablero_valido("jugador_2") is False
    assert agente_jugador.es_tablero_valido("el_tablero_1") is False


def test_control_limite_partidas(agente_jugador) -> None:
    """La lógica de control de partidas activas respeta el límite configurado."""

    # El fixture crea el agente con límite de 2 partidas
    assert agente_jugador.limite_partidas_simultaneas == 2

    # Caso 0: 0 pendientes, 0 activas -> Debe poder jugar
    assert agente_jugador.puede_jugar_nueva_partida() is True

    # Caso 1: 1 pendiente, 0 activas -> Debe poder jugar (límite 2)
    agente_jugador.partidas_pendientes["tablero_1@localhost"] = {"thread": "hilo1"}
    assert agente_jugador.puede_jugar_nueva_partida() is True

    # Caso 2: 1 pendiente, 1 activa -> TOTAL 2 -> Ya NO debe poder jugar
    agente_jugador.partidas_activas["hilo_partida_2"] = {"tablero": "tablero_2@localhost"}
    assert agente_jugador.puede_jugar_nueva_partida() is False