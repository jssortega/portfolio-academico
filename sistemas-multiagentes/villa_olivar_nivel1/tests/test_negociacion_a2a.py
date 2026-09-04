"""
Tests de negociación Contract Net A2A — Villa Olivar (Nivel 3).

Verifican el flujo de convocatoria (CFP), recepción de propuestas,
selección de ganador y adjudicación entre la Centralita y los especialistas.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web

from agentes.agente_centralita import AgenteCentralita
from agentes.base_agente_a2a import EspecificacionAgente, METODO_TASKS_SEND
from contrato.tipos import EstadoTask

@pytest.fixture
def espec_centralita() -> EspecificacionAgente:
    return EspecificacionAgente(
        identificador="centralita_test",
        rol="centralita",
        visibilidad="publico",
        puerto=8110,
        host="127.0.0.1",
        modulo="agentes.agente_centralita",
        clase="AgenteCentralita",
        parametros={
            "modelo": "mock-model",
            "privados": {
                "policia": "http://127.0.0.1:8140"
            },
            "publicos": {
                "bomberos": "http://127.0.0.1:8120"
            }
        }
    )

@pytest.fixture
async def especialista_mock(aiohttp_server):
    """Servidor mock que actúa como un especialista respondiendo a CFP."""
    async def handler_a2a(request):
        cuerpo = await request.json()
        id_rpc = cuerpo.get("id")
        params = cuerpo.get("params", {})
        datos = params.get("message", {}).get("parts", [{}])[0].get("data", {})
        
        # Si es un CFP, devolvemos una propuesta
        if datos.get("type") == "cfp":
            # Devolvemos una propuesta ficticia
            return web.json_response({
                "jsonrpc": "2.0",
                "id": id_rpc,
                "result": {
                    "id": params.get("id"),
                    "status": {"state": "completed"},
                    "artifacts": [
                        {
                            "parts": [
                                {
                                    "type": "data",
                                    "data": {
                                        "tipo_mensaje": "propuesta",
                                        "id_emergencia": datos.get("id_emergencia"),
                                        "agente_origen": "bomberos",
                                        "tiempo_estimado_min": 10,
                                        "recursos_disponibles": ["Bomba 1"]
                                    }
                                }
                            ]
                        }
                    ]
                }
            })
        
        # Si es una asignación (assign), devolvemos un informe de actuación
        if datos.get("type") == "assign":
             return web.json_response({
                "jsonrpc": "2.0",
                "id": id_rpc,
                "result": {
                    "id": params.get("id"),
                    "status": {"state": "completed"},
                    "artifacts": [
                        {
                            "parts": [
                                {
                                    "type": "data",
                                    "data": {
                                        "tipo_mensaje": "informe_actuacion",
                                        "id_emergencia": datos.get("id_emergencia"),
                                        "rol": "bomberos",
                                        "completado": True,
                                        "estado": "finalizado",
                                        "detalle": "Intervención realizada con éxito.",
                                        "acciones_realizadas": ["Extinción de incendio"],
                                        "recursos_empleados": ["Bomba 1"]
                                    }
                                }
                            ]
                        }
                    ]
                }
            })

        return web.json_response({"jsonrpc": "2.0", "id": id_rpc, "result": {"ok": True}})

    app = web.Application()
    app.router.add_post("/", handler_a2a)
    return await aiohttp_server(app)

@pytest.mark.asyncio
async def test_contract_net_a2a(espec_centralita, especialista_mock, aiohttp_client) -> None:
    """Hito 4 - Escenario 1-4: Flujo completo de Contract Net A2A."""
    # Ajustamos la URL del especialista en la especificación para que apunte al mock
    url_mock = f"http://{especialista_mock.host}:{especialista_mock.port}"
    espec_centralita.parametros["publicos"]["bomberos"] = url_mock
    
    agente = AgenteCentralita(espec_centralita)
    cliente = await aiohttp_client(agente._construir_aplicacion())
    
    id_emergencia = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "method": METODO_TASKS_SEND,
        "params": {
            "id": "task-cn-001",
            "message": {
                "role": "user",
                "parts": [{"type": "data", "data": {"id_emergencia": id_emergencia, "texto": "Incendio en almacén"}}]
            }
        },
        "id": 1
    }

    # Mockeamos el LLM para que elija a bomberos
    with patch.object(AgenteCentralita, "_invocar_adk", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "prioridad": "alta",
            "destinatarios": ["bomberos"],
            "tipo_emergencia": "incendio",
            "resumen": "Test Contract Net"
        })
        
        resp = await cliente.post("/", json=payload)
        assert resp.status == 200
        datos = await resp.json()
        
        assert datos["result"]["status"]["state"] == EstadoTask.COMPLETED.value
        informe = datos["result"]["artifacts"][0]["parts"][0]["data"]
        
        # Verificar que el informe contiene la respuesta del especialista mock
        assert any(inf["rol"] == "bomberos" for inf in informe["informes_especialistas"])
        assert informe["id_emergencia"] == id_emergencia
