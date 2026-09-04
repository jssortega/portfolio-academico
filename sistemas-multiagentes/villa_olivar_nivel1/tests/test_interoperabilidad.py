"""
Tests de interoperabilidad A2A — Villa Olivar (Nivel 3, Hito 5).

Verifican la cooperación cruzada entre grupos mediante el registro central,
la delegación de subtareas a agentes externos y la robustez ante fallos.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
import httpx
from aiohttp import web

from agentes.agente_centralita import AgenteCentralita
from agentes.base_agente_a2a import EspecificacionAgente, METODO_TASKS_SEND
from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask


@pytest.fixture
def espec_centralita_hito5() -> EspecificacionAgente:
    """Especificación para Centralita con registro central configurado."""
    return EspecificacionAgente(
        identificador="centralita_hito5",
        rol="centralita",
        visibilidad="publico",
        puerto=8110,
        host="127.0.0.1",
        modulo="agentes.agente_centralita",
        clase="AgenteCentralita",
        parametros={
            "modelo": "mock-model",
            "registro_central": "http://sinbad2.ujaen.es",
            "privados": {
                "policia": "http://127.0.0.1:8140"
            },
            "publicos": {
                "bomberos": "http://127.0.0.1:8120"
            }
        }
    )


@pytest.fixture
async def cliente_hito5(aiohttp_client, espec_centralita_hito5):
    """Cliente HTTP para la Centralita del Hito 5."""
    agente = AgenteCentralita(espec_centralita_hito5)
    app = agente._construir_aplicacion()
    app["agente"] = agente
    return await aiohttp_client(app)


@pytest.mark.asyncio
async def test_consulta_agente_externo(cliente_hito5) -> None:
    """Hito 5 - Escenario 5: Descubrimiento por rol en el registro central."""
    agente = cliente_hito5.server.app["agente"]
    
    # Mockeamos la respuesta del registro central
    agentes_externos = [
        {
            "id_agente": "agente_externo_1",
            "rol": "sanitario",
            "url": "http://grupo001:8002",
            "visibilidad": "publico"
        }
    ]
    
    from unittest.mock import MagicMock
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = agentes_externos
    mock_resp.raise_for_status.return_value = None
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        
        urls = await agente._consultar_registro_central("sanitario")
        
        assert "http://grupo001:8002" in urls
        assert mock_get.called
        assert "sinbad2.ujaen.es" in str(mock_get.call_args[0][0])


@pytest.mark.asyncio
async def test_timeout_agente_no_disponible(cliente_hito5) -> None:
    """Hito 5 - Escenario 9: Indisponibilidad transitoria de la pareja externa."""
    id_emergencia = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "method": METODO_TASKS_SEND,
        "params": {
            "id": "task-timeout-ext",
            "message": {
                "role": "user",
                "parts": [{"type": "data", "data": {"id_emergencia": id_emergencia, "texto": "Emergencia sanitaria externa"}}]
            }
        },
        "id": 100
    }
    
    agente = cliente_hito5.server.app["agente"]
    
    # 1. Mockeamos el LLM para que pida un sanitario (que es externo en espec_centralita_hito5)
    with patch.object(AgenteCentralita, "_invocar_adk", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "prioridad": "media",
            "destinatarios": ["sanitario"],
            "tipo_emergencia": "accidente_trafico",
            "resumen": "test timeout"
        })
        
        # 2. Mockeamos el registro para que devuelva un grupo externo
        with patch.object(AgenteCentralita, "_consultar_registro_central", new_callable=AsyncMock) as mock_reg:
            mock_reg.return_value = ["http://grupo-lejano:8000"]
            
            # 3. Mockeamos el post a ese grupo para que lance un timeout
            with patch("httpx.AsyncClient.post", side_effect=httpx.ReadTimeout("Timeout simulado")):
                resp = await cliente_hito5.post("/", json=payload)
                assert resp.status == 200
                datos = await resp.json()
                
                # El informe debe completarse (o ser parcial) pero no romper el agente
                assert "result" in datos
                result = datos["result"]
                assert result["status"]["state"] == EstadoTask.COMPLETED.value
                
                informe = result["artifacts"][0]["parts"][0]["data"]
                # No debe haber informes de especialistas porque el único falló por timeout
                assert len(informe["informes_especialistas"]) == 0
                assert informe["estado_final"] == "no_resuelta"


@pytest.mark.asyncio
async def test_no_cooperacion_innecesaria(cliente_hito5) -> None:
    """Hito 5 - Escenario 10: Sin cooperación cuando no hace falta."""
    id_emergencia = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "method": METODO_TASKS_SEND,
        "params": {
            "id": "task-no-coop",
            "message": {
                "role": "user",
                "parts": [{"type": "data", "data": {"id_emergencia": id_emergencia, "texto": "Incendio en la cocina"}}]
            }
        },
        "id": 101
    }

    agente = cliente_hito5.server.app["agente"]

    # Mockeamos el LLM para que pida Bomberos (publico propio en espec_centralita_hito5)
    with patch.object(AgenteCentralita, "_invocar_adk", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "prioridad": "baja",
            "destinatarios": ["bomberos"],
            "tipo_emergencia": "incendio",
            "resumen": "test no coop"
        })

        # Mockeamos el registro central para verificar que NO se llama
        with patch.object(AgenteCentralita, "_consultar_registro_central", new_callable=AsyncMock) as mock_reg:
            # También mockeamos el envío a bomberos
            from contrato.informe_actuacion import InformeActuacion
            mock_inf = InformeActuacion(rol="bomberos", completado=True)
            
            with patch.object(AgenteCentralita, "_enviar_task_a_especialista", new_callable=AsyncMock, return_value=mock_inf):
                resp = await cliente_hito5.post("/", json=payload)
                assert resp.status == 200
                
                # Verificamos que NO se ha consultado el registro central
                assert not mock_reg.called
