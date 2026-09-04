import pytest
import asyncio
from aiohttp import web

# Importamos tu agente y los handlers web
from agentes.agente_tablero import AgenteTablero
from web.tablero_handlers import game_state_handler, game_page_handler


@pytest.fixture
def mock_agent():
    """Crea una instancia simulada del agente tablero con una partida a medias."""
    agente = AgenteTablero("tablero_web@test", "secret")
    agente.tablero = ["X", "O", "X", " ", " ", " ", " ", " ", " "]
    agente.jugadores_partida = {"X": "jugador1@localhost", "O": "jugador2@localhost"}
    agente.turno_actual = "O"
    agente.estado_partida = "playing"
    agente.resultado_final = None
    agente.ganador_final = None
    agente.historial = [
        {"turn": 1, "symbol": "X", "position": 0},
        {"turn": 2, "symbol": "O", "position": 1},
        {"turn": 3, "symbol": "X", "position": 2}
    ]
    return agente


@pytest.fixture
async def cli(aiohttp_client, mock_agent):
    """Crea un servidor aiohttp de prueba con los handlers de SPADE montados."""
    app = web.Application()
    # SPADE inyecta siempre el objeto agente dentro de la request de la web
    app["agent"] = mock_agent

    # Registramos las rutas
    app.router.add_get("/game/state", game_state_handler)
    app.router.add_get("/game", game_page_handler)

    # Arrancamos el cliente simulado
    return await aiohttp_client(app)


# =====================================================================
# TESTS DEL ENDPOINT JSON (/game/state)
# =====================================================================

async def test_game_state_json_estructura_y_campos(cli):
    """Verifica que devuelve HTTP 200, Content-Type JSON y contiene todos los campos obligatorios."""
    resp = await cli.get("/game/state")
    assert resp.status == 200
    assert "application/json" in resp.headers["Content-Type"]

    data = await resp.json()

    # Comprueba que existen los campos requeridos (usando tus claves en inglés)
    for campo in ["board", "players", "current_turn", "status", "history"]:
        assert campo in data, f"Falta el campo obligatorio: {campo}"


async def test_game_state_json_valores_validos(cli):
    """El campo tablero es una matriz o lista de 9, y estado_partida es válido."""
    resp = await cli.get("/game/state")
    data = await resp.json()

    # El tablero es una estructura válida de 9 elementos
    assert isinstance(data["board"], list)
    assert len(data["board"]) == 9

    # El estado es "waiting", "playing" o "finished"
    assert data["status"] in ["waiting", "playing", "finished"]


async def test_game_state_finished_tiene_ganador(cli, mock_agent):
    """En estado 'finished', el campo ganador existe."""
    # Modificamos el estado del agente simulado a terminada
    mock_agent.estado_partida = "finished"
    mock_agent.ganador_final = "X"
    mock_agent.resultado_final = "victoria"

    resp = await cli.get("/game/state")
    data = await resp.json()

    assert data["status"] == "finished"
    assert "winner" in data
    assert data["winner"] == "X"


# =====================================================================
# TESTS DEL ENDPOINT HTML (/game)
# =====================================================================

async def test_game_page_html_basico(cli):
    """Devuelve HTTP 200 con Content-Type: text/html."""
    resp = await cli.get("/game")
    assert resp.status == 200
    assert "text/html" in resp.headers["Content-Type"]


async def test_game_page_html_contenido(cli):
    """Comprueba que el HTML tiene los contenedores para renderizar los datos."""
    resp = await cli.get("/game")
    html = await resp.text()

    # Comprueba que existen los contenedores para los jugadores
    assert "player-x-card" in html, "Falta el contenedor para el jugador X"
    assert "player-o-card" in html, "Falta el contenedor para el jugador O"

    # Comprueba que existe el contenedor para el indicador de turno
    assert "turn-card" in html, "Falta el contenedor para el indicador de turno"

    # Comprueba que existe la sección de historial
    assert "history-panel" in html, "Falta el contenedor para el historial"

    # Comprueba que existe la rejilla del tablero
    assert "board-grid" in html, "Falta el contenedor de la rejilla del tablero"


# =====================================================================
# TESTS DE ROBUSTEZ
# =====================================================================

async def test_ruta_inexistente_404(cli):
    """Una ruta inexistente devuelve 404, no 500."""
    resp = await cli.get("/ruta/que/no/existe")
    assert resp.status == 404


async def test_peticiones_concurrentes_simultaneas(cli):
    """Peticiones concurrentes (10 simultáneas) responden correctamente."""
    # Lanzamos 10 peticiones GET de golpe al endpoint JSON usando asyncio.gather
    tareas = [cli.get("/game/state") for _ in range(10)]
    respuestas = await asyncio.gather(*tareas)

    # Comprobamos que todas las 10 han respondido correctamente con HTTP 200
    for resp in respuestas:
        assert resp.status == 200