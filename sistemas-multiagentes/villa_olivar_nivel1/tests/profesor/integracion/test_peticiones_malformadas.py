"""Hito 6 — *Resistencia a peticiones malformadas* (escenario 4).

Una petición con JSON inválido, esquema desconocido o tipos
incorrectos debe terminar con un cuerpo de error estructurado y,
sobre todo, la Centralita debe seguir operativa para la siguiente
petición válida.

La prueba se realiza enviando bytes inválidos directamente con
``httpx``, sin pasar por el cliente del coordinador (que validaría
la petición en origen y no permitiría reproducir el escenario).

Prueba de **caja negra contra el sistema real** del grupo.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import httpx
import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask
from cliente_pruebas.cliente import ClienteCoordinador


# Códigos HTTP aceptables como respuesta a una petición malformada.
# El plan no exige un código concreto; cualquier error de cliente
# (``4xx``) es válido siempre que el sistema no devuelva ``5xx``
# (que sería un fallo no controlado del servidor).
CODIGOS_HTTP_ACEPTABLES_PARA_MALFORMADA = {400, 404, 405, 415, 422}


@pytest.mark.integration
@pytest.mark.hito_6
class TestPeticionesMalformadas:
    """La Centralita rechaza peticiones malformadas sin dejar de operar."""

    @pytest.mark.asyncio
    async def test_json_invalido_se_rechaza_con_codigo_de_cliente(
        self,
        url_centralita: str,
    ) -> None:
        """Un cuerpo con JSON sintácticamente inválido produce 4xx, no 5xx."""
        cuerpo_invalido = b'{"jsonrpc": "2.0", "method": "tasks/send", '  # JSON truncado
        async with httpx.AsyncClient(timeout=15.0) as cliente_http:
            respuesta = await cliente_http.post(
                url_centralita,
                content=cuerpo_invalido,
                headers={"Content-Type": "application/json"},
            )

        assert 400 <= respuesta.status_code < 500, (
            f"JSON inválido debería producir un código de cliente (4xx); "
            f"obtenido: {respuesta.status_code}; cuerpo: {respuesta.text!r}."
        )

    @pytest.mark.asyncio
    async def test_metodo_jsonrpc_desconocido_se_rechaza(
        self,
        url_centralita: str,
    ) -> None:
        """Un método JSON-RPC no soportado se rechaza con respuesta accionable."""
        peticion = {
            "jsonrpc": "2.0",
            "method": "tasks/inventado_que_no_existe",
            "params": {"foo": "bar"},
            "id": "task-h6-mal-desc",
        }
        async with httpx.AsyncClient(timeout=15.0) as cliente_http:
            respuesta = await cliente_http.post(url_centralita, json=peticion)

        if respuesta.status_code == 200:
            cuerpo = respuesta.json()
            assert "error" in cuerpo, (
                "Un método JSON-RPC desconocido aceptado con 200 debe contener "
                f"un campo `error` en la respuesta; cuerpo: {cuerpo}."
            )
        else:
            assert respuesta.status_code in CODIGOS_HTTP_ACEPTABLES_PARA_MALFORMADA, (
                f"Código HTTP inesperado para método desconocido: "
                f"{respuesta.status_code}; cuerpo: {respuesta.text!r}."
            )

    @pytest.mark.asyncio
    async def test_centralita_sigue_operativa_tras_varias_peticiones_malformadas(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
    ) -> None:
        """Tras varias peticiones malformadas seguidas, una válida procesa con normalidad."""
        peticiones_malformadas = [
            b'{"json',  # JSON truncado
            b'no es json',  # No es JSON
            b'[]',  # JSON-RPC no es una lista al nivel raíz
        ]
        async with httpx.AsyncClient(timeout=15.0) as cliente_http:
            for cuerpo in peticiones_malformadas:
                await cliente_http.post(
                    url_centralita,
                    content=cuerpo,
                    headers={"Content-Type": "application/json"},
                )

        id_emergencia = uuid4()
        identificador_task = f"task-h6-mal-recovery-{id_emergencia.hex[:8]}"
        alerta = AlertaEmergencia(
            id_emergencia=id_emergencia,
            texto="Incendio en almacén; petición válida tras una racha de malformadas.",
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task,
        )

        assert respuesta.estado is EstadoTask.COMPLETED, (
            "Tras varias peticiones malformadas, la Centralita debe procesar "
            f"la siguiente petición válida con normalidad; obtenido: "
            f"{respuesta.estado.value}."
        )
