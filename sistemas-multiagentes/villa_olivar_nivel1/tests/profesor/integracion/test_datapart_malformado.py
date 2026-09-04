"""Hito 2 — *DataPart con modelos Pydantic* (escenario 6).

La Centralita debe rechazar peticiones cuya carga útil (*payload*)
no cumple el esquema del modelo Pydantic ``AlertaEmergencia``. La
prueba envía DataParts deliberadamente malformados directamente
con ``httpx`` —sin pasar por el cliente del coordinador, porque
este último ya valida en cliente— y verifica que la Centralita
responde con la Task en estado ``failed`` y un mensaje claro,
nunca con ``completed``.

Tras el fallo, una nueva petición válida debe procesarse con
normalidad: el sistema no debe quedar atrapado en un estado
incoherente.

Prueba de **caja negra contra el sistema real** del grupo.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

import httpx
import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask
from cliente_pruebas.cliente import ClienteCoordinador


def _peticion_jsonrpc_tasks_send(
    identificador_task: str,
    datos_alerta: dict[str, Any],
) -> dict[str, Any]:
    """Compone un sobre JSON-RPC con un DataPart arbitrario."""
    peticion = {
        "jsonrpc": "2.0",
        "method": "tasks/send",
        "params": {
            "id": identificador_task,
            "message": {
                "role": "user",
                "parts": [{"type": "data", "data": datos_alerta}],
            },
        },
        "id": identificador_task,
    }
    return peticion


@pytest.mark.integration
@pytest.mark.hito_2
class TestDatapartMalformado:
    """La Centralita rechaza DataParts que no cumplen el esquema Pydantic."""

    @pytest.mark.asyncio
    async def test_datapart_sin_campo_texto_obligatorio_termina_failed(
        self,
        url_centralita: str,
    ) -> None:
        """Una alerta sin ``texto`` viola el contrato y la Task debe terminar `failed`."""
        identificador_task = f"task-h2-mal-1-{uuid4().hex[:8]}"
        # Falta `texto` (obligatorio en el modelo ``AlertaEmergencia``).
        datos_invalidos = {"id_emergencia": str(uuid4())}
        peticion = _peticion_jsonrpc_tasks_send(identificador_task, datos_invalidos)
        async with httpx.AsyncClient(timeout=30.0) as cliente_http:
            respuesta = await cliente_http.post(url_centralita, json=peticion)

        # Aceptamos tanto un cuerpo JSON-RPC con estado `failed`
        # como una respuesta HTTP de error: ambos son formas
        # válidas de rechazar el DataPart malformado.
        if respuesta.status_code == 200:
            cuerpo = respuesta.json()
            estado = cuerpo.get("result", {}).get("status", {}).get("state")
            assert estado in {EstadoTask.FAILED.value, EstadoTask.CANCELED.value}, (
                f"El DataPart malformado terminó con estado {estado!r}, "
                "se esperaba failed o canceled."
            )
        else:
            assert respuesta.status_code in {400, 422}, (
                f"Código HTTP inesperado para DataPart malformado: "
                f"{respuesta.status_code}; respuesta={respuesta.text!r}"
            )

    @pytest.mark.asyncio
    async def test_datapart_con_tipos_incorrectos_termina_failed(
        self,
        url_centralita: str,
    ) -> None:
        """Tipos incorrectos (texto como número, id_emergencia como entero) → failed."""
        identificador_task = f"task-h2-mal-2-{uuid4().hex[:8]}"
        datos_invalidos = {
            "id_emergencia": 42,  # debería ser UUID string
            "texto": 123,  # debería ser string
        }
        peticion = _peticion_jsonrpc_tasks_send(identificador_task, datos_invalidos)
        async with httpx.AsyncClient(timeout=30.0) as cliente_http:
            respuesta = await cliente_http.post(url_centralita, json=peticion)

        if respuesta.status_code == 200:
            cuerpo = respuesta.json()
            estado = cuerpo.get("result", {}).get("status", {}).get("state")
            assert estado in {EstadoTask.FAILED.value, EstadoTask.CANCELED.value}, (
                f"Los tipos incorrectos no se rechazaron: estado={estado!r}."
            )
        else:
            assert respuesta.status_code in {400, 422}

    @pytest.mark.asyncio
    async def test_tras_un_rechazo_la_centralita_sigue_operativa(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
    ) -> None:
        """Tras rechazar un DataPart malformado, una petición válida procesa con normalidad."""
        # Primera petición: claramente malformada.
        identificador_invalido = f"task-h2-mal-3a-{uuid4().hex[:8]}"
        peticion_invalida = _peticion_jsonrpc_tasks_send(
            identificador_invalido,
            {"campo_inexistente": "irrelevante"},
        )
        async with httpx.AsyncClient(timeout=30.0) as cliente_http:
            await cliente_http.post(url_centralita, json=peticion_invalida)

        # Segunda petición: válida; debe terminar `completed`.
        id_emergencia = uuid4()
        identificador_valido = f"task-h2-mal-3b-{id_emergencia.hex[:8]}"
        alerta_valida = AlertaEmergencia(
            id_emergencia=id_emergencia,
            texto="Incendio en almacén tras rechazo de petición previa.",
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta_valida,
            identificador_task=identificador_valido,
        )

        assert respuesta.estado is EstadoTask.COMPLETED, (
            "Tras un rechazo, la Centralita debería procesar la siguiente "
            f"alerta válida con normalidad; estado obtenido: {respuesta.estado.value}."
        )
