# -*- coding: utf-8 -*-
"""
Tests del cliente del registro REST (descubrimiento/cliente_registro.py).

Cubren:
  - Generación y persistencia del token con permisos 0600.
  - Reutilización del token entre instancias.
  - Construcción correcta de URLs con namespace /proyectos/{proyecto}/.
  - Envío del token en el body del alta y en Authorization Bearer en
    heartbeat y baja.
  - Manejo de errores (alta fallida, baja sobre id ya purgado).

Las pruebas usan httpx.MockTransport para simular respuestas del servicio
sin levantarlo realmente; un test de integración separado contra sinbad2
o contra un contenedor local es responsabilidad de §6.5 del plan.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest

from descubrimiento.cliente_registro import (
    ClienteRegistro,
    ErrorRegistro,
    AgenteNoRegistrado,
    PERMISOS_FICHERO_TOKEN,
)


URL_BASE: str = "http://registro.test:8020"
PROYECTO: str = "villa-olivar"
NOMBRE: str = "centralita"
URL_A2A: str = "http://192.168.1.99:8110"
URL_AGENT_CARD: str = "http://192.168.1.99:8110/.well-known/agent.json"


def _instalar_transporte(cliente: ClienteRegistro, manejador) -> None:
    """Sustituye el AsyncClient interno por uno con MockTransport."""
    cliente._http = httpx.AsyncClient(
        base_url=URL_BASE,
        transport=httpx.MockTransport(manejador),
        timeout=5,
    )


# ─── Persistencia del token ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_token_se_genera_la_primera_vez(tmp_path: Path) -> None:
    cliente = ClienteRegistro(
        base_url=URL_BASE, proyecto=PROYECTO, nombre_agente=NOMBRE,
        directorio_tokens=tmp_path,
    )
    token = cliente._token_persistente()
    fichero = tmp_path / f"{NOMBRE}.token"
    assert fichero.is_file()
    assert fichero.read_text(encoding="utf-8").strip() == token
    assert len(token) >= 32


@pytest.mark.asyncio
async def test_token_persistido_tiene_permisos_0600(tmp_path: Path) -> None:
    cliente = ClienteRegistro(
        base_url=URL_BASE, proyecto=PROYECTO, nombre_agente=NOMBRE,
        directorio_tokens=tmp_path,
    )
    cliente._token_persistente()
    fichero = tmp_path / f"{NOMBRE}.token"
    modo = os.stat(fichero).st_mode & 0o777
    assert modo == PERMISOS_FICHERO_TOKEN, f"esperaba 0o600, obtuve {oct(modo)}"


@pytest.mark.asyncio
async def test_token_se_reutiliza_entre_instancias(tmp_path: Path) -> None:
    cliente_a = ClienteRegistro(
        base_url=URL_BASE, proyecto=PROYECTO, nombre_agente=NOMBRE,
        directorio_tokens=tmp_path,
    )
    token_a = cliente_a._token_persistente()
    cliente_b = ClienteRegistro(
        base_url=URL_BASE, proyecto=PROYECTO, nombre_agente=NOMBRE,
        directorio_tokens=tmp_path,
    )
    token_b = cliente_b._token_persistente()
    assert token_a == token_b


@pytest.mark.asyncio
async def test_tokens_distintos_para_agentes_distintos(tmp_path: Path) -> None:
    a = ClienteRegistro(
        URL_BASE, PROYECTO, "centralita", directorio_tokens=tmp_path,
    )
    b = ClienteRegistro(
        URL_BASE, PROYECTO, "bomberos", directorio_tokens=tmp_path,
    )
    assert a._token_persistente() != b._token_persistente()


# ─── Construcción de URLs y envío del token ─────────────────────────────────

@pytest.mark.asyncio
async def test_alta_envia_token_en_body_y_url_con_namespace(tmp_path: Path) -> None:
    cuerpos: list[dict] = []
    rutas: list[str] = []

    def manejador(peticion: httpx.Request) -> httpx.Response:
        rutas.append(peticion.url.path)
        cuerpos.append(json.loads(peticion.content.decode("utf-8")))
        respuesta = {
            "id": "g1.centralita",
            "grupo": "g1",
            "rol": "centralita",
            "url_a2a": URL_A2A,
            "url_agent_card": URL_AGENT_CARD,
            "alta": "2026-05-06T15:00:00Z",
            "ultimo_heartbeat": "2026-05-06T15:00:00Z",
        }
        return httpx.Response(201, json=respuesta)

    cliente = ClienteRegistro(
        URL_BASE, PROYECTO, NOMBRE, directorio_tokens=tmp_path,
    )
    _instalar_transporte(cliente, manejador)

    registro = await cliente.alta(
        grupo="g1", rol="centralita",
        url_a2a=URL_A2A, url_agent_card=URL_AGENT_CARD,
    )
    await cliente.aclose()

    assert rutas == [f"/proyectos/{PROYECTO}/agentes"]
    assert "token" in cuerpos[0]
    assert len(cuerpos[0]["token"]) >= 32
    assert registro["id"] == "g1.centralita"
    assert cliente._id_registrado == "g1.centralita"


@pytest.mark.asyncio
async def test_heartbeat_envia_authorization_bearer(tmp_path: Path) -> None:
    cabeceras: list[str] = []
    rutas: list[str] = []

    def manejador(peticion: httpx.Request) -> httpx.Response:
        rutas.append(peticion.url.path)
        cabeceras.append(peticion.headers.get("Authorization", ""))
        if peticion.method == "POST" and peticion.url.path.endswith("/agentes"):
            return httpx.Response(201, json={
                "id": "g1.centralita", "grupo": "g1", "rol": "centralita",
                "url_a2a": URL_A2A, "url_agent_card": URL_AGENT_CARD,
                "alta": "2026-05-06T15:00:00Z",
                "ultimo_heartbeat": "2026-05-06T15:00:00Z",
            })
        return httpx.Response(204)

    cliente = ClienteRegistro(
        URL_BASE, PROYECTO, NOMBRE, directorio_tokens=tmp_path,
    )
    _instalar_transporte(cliente, manejador)

    await cliente.alta(
        grupo="g1", rol="centralita",
        url_a2a=URL_A2A, url_agent_card=URL_AGENT_CARD,
    )
    await cliente.heartbeat()
    await cliente.aclose()

    # El alta no envía Authorization (el token va en el body).
    # El heartbeat sí debe enviarlo, con el formato Bearer correcto.
    assert cabeceras[0] == ""
    assert cabeceras[1].startswith("Bearer ")
    assert len(cabeceras[1]) > len("Bearer ") + 20
    assert rutas[1] == f"/proyectos/{PROYECTO}/agentes/id/g1.centralita/heartbeat"


@pytest.mark.asyncio
async def test_baja_envia_authorization_y_libera_id(tmp_path: Path) -> None:
    rutas: list[tuple[str, str]] = []

    def manejador(peticion: httpx.Request) -> httpx.Response:
        rutas.append((peticion.method, peticion.url.path))
        if peticion.method == "POST":
            return httpx.Response(201, json={
                "id": "g1.centralita", "grupo": "g1", "rol": "centralita",
                "url_a2a": URL_A2A, "url_agent_card": URL_AGENT_CARD,
                "alta": "2026-05-06T15:00:00Z",
                "ultimo_heartbeat": "2026-05-06T15:00:00Z",
            })
        return httpx.Response(204)

    cliente = ClienteRegistro(
        URL_BASE, PROYECTO, NOMBRE, directorio_tokens=tmp_path,
    )
    _instalar_transporte(cliente, manejador)

    await cliente.alta(
        grupo="g1", rol="centralita",
        url_a2a=URL_A2A, url_agent_card=URL_AGENT_CARD,
    )
    await cliente.baja()
    await cliente.aclose()

    assert ("DELETE", f"/proyectos/{PROYECTO}/agentes/id/g1.centralita") in rutas
    assert cliente._id_registrado is None


@pytest.mark.asyncio
async def test_descubrir_pega_a_la_url_correcta(tmp_path: Path) -> None:
    rutas: list[str] = []

    def manejador(peticion: httpx.Request) -> httpx.Response:
        rutas.append(peticion.url.path)
        return httpx.Response(200, json=[])

    cliente = ClienteRegistro(
        URL_BASE, PROYECTO, NOMBRE, directorio_tokens=tmp_path,
    )
    _instalar_transporte(cliente, manejador)

    lista = await cliente.descubrir(rol="bomberos")
    await cliente.aclose()

    assert rutas == [f"/proyectos/{PROYECTO}/agentes/bomberos"]
    assert lista == []


# ─── Errores ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_heartbeat_sin_alta_lanza(tmp_path: Path) -> None:
    cliente = ClienteRegistro(
        URL_BASE, PROYECTO, NOMBRE, directorio_tokens=tmp_path,
    )
    _instalar_transporte(cliente, lambda req: httpx.Response(204))
    with pytest.raises(AgenteNoRegistrado):
        await cliente.heartbeat()
    await cliente.aclose()


@pytest.mark.asyncio
async def test_alta_fallida_lanza_error_registro(tmp_path: Path) -> None:
    def manejador(_: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"detail": "rol inválido"})

    cliente = ClienteRegistro(
        URL_BASE, PROYECTO, NOMBRE, directorio_tokens=tmp_path,
    )
    _instalar_transporte(cliente, manejador)
    with pytest.raises(ErrorRegistro):
        await cliente.alta(
            grupo="g1", rol="rol_inventado",
            url_a2a=URL_A2A, url_agent_card=URL_AGENT_CARD,
        )
    await cliente.aclose()


@pytest.mark.asyncio
async def test_baja_acepta_404_como_exito_silencioso(tmp_path: Path) -> None:
    """Si la entrada ya caducó por TTL, baja() no debe lanzar."""
    def manejador(peticion: httpx.Request) -> httpx.Response:
        if peticion.method == "POST":
            return httpx.Response(201, json={
                "id": "g1.centralita", "grupo": "g1", "rol": "centralita",
                "url_a2a": URL_A2A, "url_agent_card": URL_AGENT_CARD,
                "alta": "2026-05-06T15:00:00Z",
                "ultimo_heartbeat": "2026-05-06T15:00:00Z",
            })
        return httpx.Response(404, json={"detail": "no existe"})

    cliente = ClienteRegistro(
        URL_BASE, PROYECTO, NOMBRE, directorio_tokens=tmp_path,
    )
    _instalar_transporte(cliente, manejador)
    await cliente.alta(
        grupo="g1", rol="centralita",
        url_a2a=URL_A2A, url_agent_card=URL_AGENT_CARD,
    )
    await cliente.baja()  # no debe lanzar pese al 404
    await cliente.aclose()


@pytest.mark.asyncio
async def test_async_context_manager_cierra_cliente(tmp_path: Path) -> None:
    async with ClienteRegistro(
        URL_BASE, PROYECTO, NOMBRE, directorio_tokens=tmp_path,
    ) as cliente:
        _instalar_transporte(cliente, lambda req: httpx.Response(200, json=[]))
        await cliente.descubrir(rol="bomberos")
        cliente_http = cliente._http
        assert cliente_http is not None
    # Tras salir del with, el cliente HTTP debe estar cerrado.
    assert cliente._http is None
