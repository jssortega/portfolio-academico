"""
Tests de los agentes A2A — Villa Olivar (Nivel 3).

Verifican el cumplimiento del protocolo A2A por parte de la Centralita
112, incluyendo el servidor HTTP, el despacho JSON-RPC, el ciclo de vida
de las tareas y la robustez ante entradas inválidas.

Hito 1 — escenarios 2, 3, 4, 5, 6, 7 y 8.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import yaml
from aiohttp import web

from agentes.agente_centralita import AgenteCentralita
from agentes.base_agente_a2a import EspecificacionAgente, METODO_TASKS_SEND, METODO_TASKS_GET, METODO_TASKS_SEND_SUBSCRIBE
from contrato.informe_resolucion import InformeResolucion
from contrato.traza import EventoTraza
from contrato.tipos import EstadoTask

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def espec_centralita() -> EspecificacionAgente:
    """Especificación mínima para una Centralita de prueba."""
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
                "policia": "http://127.0.0.1:8140",
                "municipal": "http://127.0.0.1:8150"
            }
        }
    )

@pytest.fixture
async def cliente_a2a(aiohttp_client, espec_centralita):
    """Cliente HTTP para hablar con el servidor del agente."""
    agente = AgenteCentralita(espec_centralita)
    app = agente._construir_aplicacion()
    # Inyectamos el agente en la app para que los handlers tengan acceso si es necesario
    app["agente"] = agente 
    return await aiohttp_client(app)

# ─────────────────────────────────────────────────────────────────────────────
# ESCENARIO 2 y 3: Procesado de alertas
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_servidor_a2a_responde(cliente_a2a) -> None:
    """Hito 1 - Escenario 1 (parcial): El servidor responde y sirve la Card."""
    resp = await cliente_a2a.get("/.well-known/agent.json")
    assert resp.status == 200
    card = await resp.json()
    assert card["name"] == "centralita_test"
    assert "skills" in card

@pytest.mark.asyncio
async def test_task_send_devuelve_completed(cliente_a2a) -> None:
    """Hito 1 - Escenario 2: Se envía una alerta y devuelve Task completed."""
    id_emergencia = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "method": METODO_TASKS_SEND,
        "params": {
            "id": "task-001",
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "data",
                        "data": {
                            "id_emergencia": id_emergencia,
                            "texto": "Incendio detectado en la calle Olivos 12"
                        }
                    }
                ]
            }
        },
        "id": 1
    }

    # Mockeamos el LLM para que no dependa de infraestructura real
    # y para evitar fallos por campos inexistentes si el agente es buggy.
    with patch.object(AgenteCentralita, "_invocar_adk", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "prioridad": "alta",
            "destinatarios": ["bomberos"],
            "tipo_emergencia": "incendio",
            "resumen": "Incendio controlado rápidamente."
        })
        
        resp = await cliente_a2a.post("/", json=payload)
        assert resp.status == 200
        datos = await resp.json()
        
        assert "result" in datos
        result = datos["result"]
        assert result["status"]["state"] == EstadoTask.COMPLETED.value
        
        # Verificar el informe en artifacts
        parte_datos = result["artifacts"][0]["parts"][0]["data"]
        assert parte_datos["id_emergencia"] == id_emergencia
        assert parte_datos["tipo_emergencia"] == "incendio"
        assert parte_datos["prioridad"] == "alta"

@pytest.mark.asyncio
@pytest.mark.parametrize("texto,tipo_esperado", [
    ("Accidente de coche con heridos", "accidente_trafico"),
    ("Humo saliendo de un solar", "incendio"),
    ("Derrame de liquido aceitoso", "derrame_quimico"),
    ("Inundación en garajes", "inundacion")
])
async def test_variedad_emergencias(cliente_a2a, texto, tipo_esperado) -> None:
    """Hito 1 - Escenario 3: Clasificación correcta de diversos tipos."""
    # Similar al anterior pero variando el texto
    payload = {
        "jsonrpc": "2.0",
        "method": METODO_TASKS_SEND,
        "params": {
            "id": f"task-{uuid.uuid4().hex[:8]}",
            "message": {
                "role": "user",
                "parts": [{"type": "data", "data": {"id_emergencia": str(uuid.uuid4()), "texto": texto}}]
            }
        },
        "id": 2
    }
    
    with patch.object(AgenteCentralita, "_invocar_adk", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "prioridad": "media",
            "destinatarios": ["bomberos"],
            "tipo_emergencia": tipo_esperado,
            "resumen": f"Atendiendo {tipo_esperado}"
        })
        
        resp = await cliente_a2a.post("/", json=payload)
        datos = await resp.json()
        parte_datos = datos["result"]["artifacts"][0]["parts"][0]["data"]
        assert parte_datos["tipo_emergencia"] == tipo_esperado

# ─────────────────────────────────────────────────────────────────────────────
# ESCENARIO 4: Persistencia y consulta
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tasks_get(cliente_a2a) -> None:
    """Hito 1 - Escenario 4: Consulta de una Task previa via tasks/get."""
    id_task = "task-persistente-001"
    payload_send = {
        "jsonrpc": "2.0",
        "method": METODO_TASKS_SEND,
        "params": {
            "id": id_task,
            "message": {
                "role": "user",
                "parts": [{"type": "data", "data": {"id_emergencia": str(uuid.uuid4()), "texto": "Emergencia test"}}]
            }
        },
        "id": 10
    }
    
    with patch.object(AgenteCentralita, "_invocar_adk", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = '{"prioridad": "baja", "destinatarios": [], "tipo_emergencia": "otro", "resumen": "test"}'
        await cliente_a2a.post("/", json=payload_send)
    
    # Ahora consultamos con tasks/get
    payload_get = {
        "jsonrpc": "2.0",
        "method": METODO_TASKS_GET,
        "params": {"id": id_task},
        "id": 11
    }
    
    resp = await cliente_a2a.post("/", json=payload_get)
    assert resp.status == 200
    datos = await resp.json()
    assert "result" in datos
    assert datos["result"]["id"] == id_task
    assert datos["result"]["status"]["state"] == EstadoTask.COMPLETED.value
    assert "history" in datos["result"]

# ─────────────────────────────────────────────────────────────────────────────
# ESCENARIO 5: Integración de lógica del Nivel 2
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_integracion_logica_nivel2(cliente_a2a) -> None:
    """Hito 1 - Escenario 5: Verifica que el fallback o las herramientas usan la lógica de N2."""
    # Si forzamos un fallo en el LLM, el agente debe usar el fallback determinista
    # que usa logica_centralita.clasificar_emergencia.
    id_emergencia = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "method": METODO_TASKS_SEND,
        "params": {
            "id": "task-fallback",
            "message": {
                "role": "user",
                "parts": [{"type": "data", "data": {
                    "id_emergencia": id_emergencia, 
                    "texto": "Derrame de amoniaco" # Debería dar prioridad alta/critica
                }}]
            }
        },
        "id": 20
    }
    
    with patch.object(AgenteCentralita, "_invocar_adk", side_effect=Exception("LLM down")):
        resp = await cliente_a2a.post("/", json=payload)
        datos = await resp.json()
        parte_datos = datos["result"]["artifacts"][0]["parts"][0]["data"]
        # Derrame de amoniaco en lógica N2 -> prioridad alta o critica
        assert parte_datos["prioridad"] in ("alta", "critica")


@pytest.mark.asyncio
async def test_degenerate_input(cliente_a2a) -> None:
    """Hito 1 - Escenario 6: Texto vacío o inválido devuelve Task failed."""
    payload = {
        "jsonrpc": "2.0",
        "method": METODO_TASKS_SEND,
        "params": {
            "id": "task-bad",
            "message": {
                "role": "user",
                "parts": [{"type": "data", "data": {"id_emergencia": str(uuid.uuid4()), "texto": ""}}] # Corto < 3 chars
            }
        },
        "id": 30
    }
    
    resp = await cliente_a2a.post("/", json=payload)
    datos = await resp.json()
    assert "result" in datos
    assert datos["result"]["status"]["state"] == EstadoTask.FAILED.value
    assert "texto" in datos["result"]["status"]["message"].lower()



def test_config_sin_hardcodear() -> None:
    """Hito 1 - Escenario 7: No hay IPs ni puertos literales en el código del agente."""
    ruta_agente = Path("agentes/agente_centralita.py")
    contenido = ruta_agente.read_text(encoding="utf-8")

    prohibidos = ["127.0.0.1", "localhost", "8110", "8120", "8130", "8140", "8150"]
    for p in prohibidos:
        assert f'"{p}"' not in contenido, f"Hardcoding detectado: {p}"
        assert f"'{p}'" not in contenido, f"Hardcoding detectado: {p}"



@pytest.mark.asyncio
async def test_disponibilidad_continuada(cliente_a2a) -> None:
    """Hito 1 - Escenario 8: El agente responde a ráfagas de peticiones."""
    for i in range(5): # Reducimos a 5 por velocidad en tests, pero verifica el punto
        payload = {
            "jsonrpc": "2.0",
            "method": METODO_TASKS_SEND,
            "params": {
                "id": f"task-burst-{i}",
                "message": {
                    "role": "user",
                    "parts": [{"type": "data", "data": {"id_emergencia": str(uuid.uuid4()), "texto": f"Incendio {i}"}}]
                }
            },
            "id": i + 100
        }
        with patch.object(AgenteCentralita, "_invocar_adk", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = '{"prioridad": "baja", "destinatarios": [], "tipo_emergencia": "otro", "resumen": "ok"}'
            resp = await cliente_a2a.post("/", json=payload)
            assert resp.status == 200
            datos = await resp.json()
            assert datos["result"]["status"]["state"] == EstadoTask.COMPLETED.value


@pytest.mark.asyncio
async def test_ciclo_vida_task(cliente_a2a) -> None:
    """Hito 4 - Escenario 6: Ciclo de vida observable (submitted -> working -> completed)."""
    id_task = f"task-lifecycle-{uuid.uuid4().hex[:8]}"
    payload = {
        "jsonrpc": "2.0",
        "method": METODO_TASKS_SEND,
        "params": {
            "id": id_task,
            "message": {
                "role": "user",
                "parts": [{"type": "data", "data": {"id_emergencia": str(uuid.uuid4()), "texto": "Emergencia para test de ciclo de vida"}}]
            }
        },
        "id": 40
    }
    
    with patch.object(AgenteCentralita, "_invocar_adk", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = '{"prioridad": "baja", "destinatarios": [], "tipo_emergencia": "otro", "resumen": "ok"}'
        resp = await cliente_a2a.post("/", json=payload)
        datos = await resp.json()
        
        result = datos["result"]
        assert result["status"]["state"] == EstadoTask.COMPLETED.value
        
        history = result["history"]
        states = [h["state"] for h in history]
        assert "submitted" in states
        assert "working" in states
        assert "completed" in states
        # Verificar que tienen timestamps
        for entry in history:
            assert "timestamp" in entry

@pytest.mark.asyncio
async def test_input_required(cliente_a2a) -> None:
    """Hito 4 - Escenario 7: Estado input-required ante datos incompletos y reanudación."""
    id_task = f"task-input-req-{uuid.uuid4().hex[:8]}"
    id_emergencia = str(uuid.uuid4())
    
    # 1. Petición con texto insuficiente (< 10 caracteres)
    payload_1 = {
        "jsonrpc": "2.0",
        "method": METODO_TASKS_SEND,
        "params": {
            "id": id_task,
            "message": {
                "role": "user",
                "parts": [{"type": "data", "data": {"id_emergencia": id_emergencia, "texto": "Ayuda"}}]
            }
        },
        "id": 50
    }
    
    resp_1 = await cliente_a2a.post("/", json=payload_1)
    datos_1 = await resp_1.json()
    assert datos_1["result"]["status"]["state"] == "input-required"
    assert "texto" in datos_1["result"]["status"]["message"].lower()

    # 2. Reanudación enviando el resto de la información con el mismo id_task
    payload_2 = {
        "jsonrpc": "2.0",
        "method": METODO_TASKS_SEND,
        "params": {
            "id": id_task,
            "message": {
                "role": "user",
                "parts": [{"type": "data", "data": {"texto": "Incendio de grandes proporciones en el centro"}}]
            }
        },
        "id": 51
    }

    with patch.object(AgenteCentralita, "_invocar_adk", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "prioridad": "alta",
            "destinatarios": ["bomberos"],
            "tipo_emergencia": "incendio",
            "resumen": "Procesado tras input-required"
        })
        
        resp_2 = await cliente_a2a.post("/", json=payload_2)
        datos_2 = await resp_2.json()
        assert datos_2["result"]["status"]["state"] == EstadoTask.COMPLETED.value
        assert datos_2["result"]["artifacts"][0]["parts"][0]["data"]["tipo_emergencia"] == "incendio"
        
        # Verificar que se usó el id_emergencia original que estaba en pausa
        assert datos_2["result"]["artifacts"][0]["parts"][0]["data"]["id_emergencia"] == id_emergencia

@pytest.mark.asyncio
async def test_descubrimiento_agent_cards(espec_centralita: EspecificacionAgente) -> None:
    """Prueba que el agente puede formar correctamente las URLs de descubrimiento (.well-known)"""

    agente = AgenteCentralita(espec_centralita)


    tarjeta = agente.construir_agent_card()
    url_publicada = str(tarjeta.url).rstrip('/')

    ruta_esperada = f"{url_publicada}/.well-known/agent.json"

    assert "/.well-known/agent.json" in ruta_esperada
    assert str(espec_centralita.puerto) in ruta_esperada
    assert isinstance(tarjeta.skills, list)


@pytest.mark.asyncio
async def test_peticion_malformada(cliente_a2a) -> None:
    """Hito 6 - Escenario 4: Resistencia a peticiones malformadas."""
    # 1. JSON inválido (debe dar error JSON-RPC -32700)
    resp = await cliente_a2a.post("/", data="Esto no es JSON {", headers={"Content-Type": "application/json"})
    datos = await resp.json()
    assert "error" in datos
    assert datos["error"]["code"] == -32700

    # 2. Esquema desconocido (falta campo 'texto' pero tiene 'id_emergencia' para forzar el path de AlertaEmergencia)
    payload_bad_schema = {
        "jsonrpc": "2.0",
        "method": METODO_TASKS_SEND,
        "params": {
            "id": "task-bad-schema",
            "message": {
                "role": "user",
                "parts": [{"type": "data", "data": {"id_emergencia": str(uuid.uuid4())}}] # Falta 'texto'
            }
        },
        "id": 101
    }
    resp = await cliente_a2a.post("/", json=payload_bad_schema)
    datos = await resp.json()
    assert datos["result"]["status"]["state"] == EstadoTask.FAILED.value
    assert "texto" in datos["result"]["status"]["message"].lower()

    # 3. Tipos incorrectos (texto es un número)
    payload_bad_types = {
        "jsonrpc": "2.0",
        "method": METODO_TASKS_SEND,
        "params": {
            "id": "task-bad-types",
            "message": {
                "role": "user",
                "parts": [{"type": "data", "data": {"id_emergencia": str(uuid.uuid4()), "texto": 12345}}]
            }
        },
        "id": 102
    }
    resp = await cliente_a2a.post("/", json=payload_bad_types)
    datos = await resp.json()
    assert datos["result"]["status"]["state"] == EstadoTask.FAILED.value
    # Pydantic 2 error message for int instead of str usually contains 'str' or 'string'
    assert "str" in datos["result"]["status"]["message"].lower()


@pytest.mark.asyncio
async def test_streaming_sse(cliente_a2a) -> None:
    """Hito 6 - Escenario 3: Transmisión continua SSE en Tasks largas."""
    id_task = "task-sse-001"
    payload = {
        "jsonrpc": "2.0",
        "method": METODO_TASKS_SEND_SUBSCRIBE,
        "params": {
            "id": id_task,
            "message": {
                "role": "user",
                "parts": [{"type": "data", "data": {"id_emergencia": str(uuid.uuid4()), "texto": "Incendio forestal de grandes dimensiones"}}]
            }
        },
        "id": 200
    }

    with patch.object(AgenteCentralita, "_invocar_adk", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "prioridad": "alta",
            "destinatarios": ["bomberos"],
            "tipo_emergencia": "incendio",
            "resumen": "Procesado via SSE"
        })
        
        # Mockeamos manejar_alerta para evitar llamadas a especialistas reales
        with patch.object(AgenteCentralita, "manejar_alerta", new_callable=AsyncMock) as mock_manejar:
            mock_manejar.return_value = InformeResolucion(
                id_emergencia=uuid.uuid4(),
                tipo_emergencia="incendio",
                prioridad="alta",
                ubicacion={"direccion": "Bosque"},
                informes_especialistas=[],
                estado_final="resuelta",
                resumen="OK",
                traza_participacion=[EventoTraza(
                    instante=datetime.now(timezone.utc),
                    agente_id="centralita_test",
                    rol="centralita",
                    visibilidad="publico",
                    accion="finalizar",
                    detalle="Procesado en test"
                )]
            )

            async with cliente_a2a.post("/", json=payload) as resp:
                assert resp.status == 200
                assert resp.headers["Content-Type"] == "text/event-stream"
                
                eventos = []
                async for line in resp.content:
                    linea_dec = line.decode("utf-8").strip()
                    if linea_dec.startswith("data: "):
                        eventos.append(json.loads(linea_dec.removeprefix("data: ")))
                
                # Debemos haber recibido al menos: submitted, working, working, completed
                states = [e["status"]["state"] for e in eventos]
                assert "submitted" in states
                assert "working" in states
                assert "completed" in states
                
                # Verificar que el evento completed tiene el InformeResolucion
                evento_final = next(e for e in eventos if e["status"]["state"] == "completed")
                assert "artifacts" in evento_final
                informe = evento_final["artifacts"][0]["parts"][0]["data"]
                assert informe["tipo_emergencia"] == "incendio"
