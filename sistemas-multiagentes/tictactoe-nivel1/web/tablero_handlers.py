from aiohttp import web
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

async def game_state_handler(request):
    agent = request.app["agent"]
    estado = agent.obtener_estado_web_publico()
    return web.json_response(estado)

async def game_page_handler(request):
    return web.FileResponse(TEMPLATES_DIR / "game.html")