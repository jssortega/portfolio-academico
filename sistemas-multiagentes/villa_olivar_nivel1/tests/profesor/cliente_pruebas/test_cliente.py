"""Pruebas unitarias del cliente A2A del coordinador del profesor.

Validan la lógica del cliente con accesorios (*fixtures*) que
interceptan las llamadas HTTP mediante un transporte de prueba de
`httpx`. No se conecta contra ningún sistema real: corresponden al
nivel **N1** de la verificación por niveles descrita en
`doc/PLAN_PRUEBAS.md` § 4.5.

La estrategia consiste en proporcionar un `httpx.MockTransport` que
recibe la petición, la inspecciona y devuelve una respuesta
predefinida. De esta forma se valida que el cliente:

1. Construye correctamente la URL de la Agent Card.
2. Compone peticiones JSON-RPC 2.0 con la estructura prevista.
3. Traduce la respuesta a `RespuestaTask` con el estado y, cuando
   procede, el `InformeResolucion` parseado.
4. Lanza errores claros ante respuestas HTTP no satisfactorias o
   cuerpos malformados.
"""

import json
from typing import Any

import httpx
from uuid import UUID

import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask, Prioridad, TipoEmergencia
from cliente_pruebas.cliente import RUTA_AGENT_CARD, ClienteCoordinador


URL_BASE_CENTRALITA = "http://192.168.1.11:8110"
URL_REGISTRO_FALSO = "http://servidor-de-prueba.invalid:8020"
IDENTIFICADOR_TASK_PRUEBA = "task-prueba-001"

# UUID estable usado en los tests del envío de alertas. El modelo
# Pydantic ``AlertaEmergencia`` exige ``id_emergencia`` como
# correlador entre la alerta enviada y el informe que devuelve la
# Centralita; al fijar el UUID aquí evitamos la dependencia de
# ``uuid4()`` en cada test y los hacemos reproducibles.
ID_EMERGENCIA_PRUEBA: UUID = UUID("12345678-1234-5678-1234-567812345678")


def _agent_card_centralita_falsa() -> dict[str, Any]:
    """Cuerpo JSON de una Agent Card mínima válida para la Centralita."""
    cuerpo = {
        "name": "centralita_villa_olivar",
        "description": "Centralita 112 del grupo de prueba.",
        "url": URL_BASE_CENTRALITA,
        "version": "1.0.0",
        "skills": [
            {
                "id": "clasificar_emergencia",
                "name": "Clasificación de emergencias",
                "description": "Determina tipo y prioridad de la alerta.",
                "tags": ["emergencia"],
            },
        ],
    }
    return cuerpo


def _respuesta_jsonrpc_completed_con_informe() -> dict[str, Any]:
    """Cuerpo JSON-RPC que simula una Task completada con informe agregado.

    El cuerpo cumple el esquema actual de
    :class:`contrato.informe_resolucion.InformeResolucion`:
    ``id_emergencia`` (correlador con la alerta) y
    ``traza_participacion`` con al menos un evento son
    obligatorios. El ``EventoTraza`` mínimo lleva los seis campos
    del modelo Pydantic (``instante``, ``agente_id``, ``rol``,
    ``visibilidad``, ``accion``, ``detalle``).
    """
    cuerpo = {
        "jsonrpc": "2.0",
        "id": IDENTIFICADOR_TASK_PRUEBA,
        "result": {
            "id": IDENTIFICADOR_TASK_PRUEBA,
            "status": {"state": EstadoTask.COMPLETED.value},
            "artifacts": [
                {
                    "parts": [
                        {
                            "type": "data",
                            "data": {
                                "id_emergencia": str(ID_EMERGENCIA_PRUEBA),
                                "tipo_emergencia": TipoEmergencia.INCENDIO.value,
                                "prioridad": Prioridad.ALTA.value,
                                "informes_especialistas": [],
                                "estado_final": "resuelta",
                                "resumen": "Incendio extinguido en 45 minutos.",
                                "traza_participacion": [
                                    {
                                        "instante": "2026-05-16T17:32:11Z",
                                        "agente_id": "centralita-falsa",
                                        "rol": "centralita",
                                        "visibilidad": "publico",
                                        "accion": "recibir_alerta",
                                        "detalle": "alerta recibida",
                                    },
                                ],
                            },
                        },
                    ],
                },
            ],
        },
    }
    return cuerpo


def _respuesta_jsonrpc_failed() -> dict[str, Any]:
    """Cuerpo JSON-RPC que simula una Task fallida con mensaje de error."""
    cuerpo = {
        "jsonrpc": "2.0",
        "id": IDENTIFICADOR_TASK_PRUEBA,
        "result": {
            "id": IDENTIFICADOR_TASK_PRUEBA,
            "status": {
                "state": EstadoTask.FAILED.value,
                "message": "Petición malformada: falta el campo `texto`.",
            },
        },
    }
    return cuerpo


@pytest.mark.hito_1
class TestLecturaAgentCard:
    """Pruebas del método `leer_agent_card`."""

    @pytest.mark.asyncio
    async def test_descarga_y_valida_la_agent_card_en_la_ruta_estandar(self) -> None:
        """El cliente solicita `/.well-known/agent.json` y valida el JSON devuelto."""
        peticiones_capturadas: list[httpx.Request] = []

        def manejador(peticion: httpx.Request) -> httpx.Response:
            peticiones_capturadas.append(peticion)
            return httpx.Response(200, json=_agent_card_centralita_falsa())

        transporte = httpx.MockTransport(manejador)
        async with httpx.AsyncClient(transport=transporte) as cliente_http:
            cliente = ClienteCoordinador(cliente_http=cliente_http)
            agent_card = await cliente.leer_agent_card(URL_BASE_CENTRALITA)

        assert agent_card.name == "centralita_villa_olivar"
        assert len(peticiones_capturadas) == 1
        assert peticiones_capturadas[0].url.path == RUTA_AGENT_CARD

    @pytest.mark.asyncio
    async def test_propaga_un_error_http_si_la_card_no_esta_disponible(self) -> None:
        """Una respuesta 404 debe propagarse como `httpx.HTTPStatusError`."""

        def manejador(_: httpx.Request) -> httpx.Response:
            return httpx.Response(404, text="No encontrada.")

        transporte = httpx.MockTransport(manejador)
        async with httpx.AsyncClient(transport=transporte) as cliente_http:
            cliente = ClienteCoordinador(cliente_http=cliente_http)
            with pytest.raises(httpx.HTTPStatusError):
                await cliente.leer_agent_card(URL_BASE_CENTRALITA)


@pytest.mark.hito_5
class TestListarAgentesPublicos:
    """Pruebas del método `listar_agentes_publicos`."""

    @pytest.mark.asyncio
    async def test_consulta_el_catalogo_del_proyecto_y_aplana_por_rol(self) -> None:
        """El cliente consulta ``/proyectos/<proyecto>/agentes`` y aplana la respuesta.

        El registro REST namespacea por proyecto y devuelve un
        objeto ``{rol: [descriptor, ...]}``. El cliente debe
        consultar la ruta correcta y aplanar el catálogo a una
        lista de descriptores con el campo ``rol`` añadido.
        """
        peticiones_capturadas: list[httpx.Request] = []

        def manejador(peticion: httpx.Request) -> httpx.Response:
            peticiones_capturadas.append(peticion)
            return httpx.Response(
                200,
                json={
                    "centralita": [
                        {
                            "id": "centralita_grupo_1",
                            "grupo": "g01",
                            "url_a2a": "http://192.168.1.11:8110",
                            "url_agent_card": "http://192.168.1.11:8110/.well-known/agent.json",
                        },
                    ],
                    "bomberos": [],
                    "sanitario": [],
                    "policia": [],
                    "municipal": [],
                },
            )

        transporte = httpx.MockTransport(manejador)
        async with httpx.AsyncClient(transport=transporte) as cliente_http:
            cliente = ClienteCoordinador(
                cliente_http=cliente_http,
                url_registro=URL_REGISTRO_FALSO,
            )
            agentes = await cliente.listar_agentes_publicos()

        assert len(agentes) == 1
        assert agentes[0]["rol"] == "centralita"
        assert peticiones_capturadas[0].url.path == "/proyectos/villa-olivar/agentes"

    @pytest.mark.asyncio
    async def test_lanza_value_error_si_no_se_configuro_la_url_del_registro(self) -> None:
        """Sin URL del registro, las operaciones de descubrimiento son inviables."""
        async with httpx.AsyncClient() as cliente_http:
            cliente = ClienteCoordinador(cliente_http=cliente_http)
            with pytest.raises(ValueError):
                await cliente.listar_agentes_publicos()


@pytest.mark.hito_4
class TestEnvioDeAlertas:
    """Pruebas del método `enviar_alerta`."""

    @pytest.mark.asyncio
    async def test_construye_una_peticion_jsonrpc_2_con_metodo_tasks_send(self) -> None:
        """La petición enviada respeta el formato JSON-RPC 2.0 del protocolo A2A."""
        peticiones_capturadas: list[dict[str, Any]] = []

        def manejador(peticion: httpx.Request) -> httpx.Response:
            peticiones_capturadas.append(json.loads(peticion.read()))
            return httpx.Response(200, json=_respuesta_jsonrpc_completed_con_informe())

        transporte = httpx.MockTransport(manejador)
        async with httpx.AsyncClient(transport=transporte) as cliente_http:
            cliente = ClienteCoordinador(cliente_http=cliente_http)
            alerta = AlertaEmergencia(
                id_emergencia=ID_EMERGENCIA_PRUEBA,
                texto="Incendio en almacén con humo denso.",
            )
            respuesta = await cliente.enviar_alerta(
                url_centralita=URL_BASE_CENTRALITA,
                alerta=alerta,
                identificador_task=IDENTIFICADOR_TASK_PRUEBA,
            )

        assert respuesta.estado is EstadoTask.COMPLETED
        assert respuesta.task_id == IDENTIFICADOR_TASK_PRUEBA
        peticion_enviada = peticiones_capturadas[0]
        assert peticion_enviada["jsonrpc"] == "2.0"
        assert peticion_enviada["method"] == "tasks/send"
        assert peticion_enviada["id"] == IDENTIFICADOR_TASK_PRUEBA
        partes = peticion_enviada["params"]["message"]["parts"]
        assert partes[0]["type"] == "data"
        assert partes[0]["data"]["texto"].startswith("Incendio")

    @pytest.mark.asyncio
    async def test_devuelve_el_informe_de_resolucion_parseado_si_la_task_termina_completed(
        self,
    ) -> None:
        """Cuando la Task termina `completed`, el informe se traduce al modelo Pydantic."""

        def manejador(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=_respuesta_jsonrpc_completed_con_informe())

        transporte = httpx.MockTransport(manejador)
        async with httpx.AsyncClient(transport=transporte) as cliente_http:
            cliente = ClienteCoordinador(cliente_http=cliente_http)
            alerta = AlertaEmergencia(
                id_emergencia=ID_EMERGENCIA_PRUEBA,
                texto="Inundación en garaje subterráneo.",
            )
            respuesta = await cliente.enviar_alerta(
                url_centralita=URL_BASE_CENTRALITA,
                alerta=alerta,
                identificador_task=IDENTIFICADOR_TASK_PRUEBA,
            )

        assert respuesta.informe is not None
        assert respuesta.informe.tipo_emergencia is TipoEmergencia.INCENDIO
        assert respuesta.informe.prioridad is Prioridad.ALTA

    @pytest.mark.asyncio
    async def test_recoge_el_mensaje_de_error_si_la_task_termina_failed(self) -> None:
        """Cuando la Task termina `failed`, el cliente recoge el mensaje descriptivo."""

        def manejador(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=_respuesta_jsonrpc_failed())

        transporte = httpx.MockTransport(manejador)
        async with httpx.AsyncClient(transport=transporte) as cliente_http:
            cliente = ClienteCoordinador(cliente_http=cliente_http)
            alerta = AlertaEmergencia(
                id_emergencia=ID_EMERGENCIA_PRUEBA,
                texto="Texto de prueba",
            )
            respuesta = await cliente.enviar_alerta(
                url_centralita=URL_BASE_CENTRALITA,
                alerta=alerta,
                identificador_task=IDENTIFICADOR_TASK_PRUEBA,
            )

        assert respuesta.estado is EstadoTask.FAILED
        assert respuesta.informe is None
        assert respuesta.mensaje_error is not None
        assert "malformada" in respuesta.mensaje_error
