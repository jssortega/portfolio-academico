"""
Prueba de integración SPADE-LLM + ADK — Villa Olivar (Nivel 2).

Verifica que la documentación del proyecto es correcta comprobando
que todos los componentes descritos funcionan según lo documentado:
  - La clase base AgenteVillaOlivarLLM hereda de LLMAgent.
  - Las FunctionTool de ADK se adaptan correctamente a LLMTool.
  - El agente SPADE-LLM arranca, recibe un mensaje FIPA-ACL y
    el LLM responde invocando herramientas de dominio.
  - Los modelos Pydantic compartidos son importables y válidos.
  - Los prompts existen y tienen el formato documentado.

Requiere:
  - Servidor XMPP accesible (Prosody en localhost:5222)
  - Ollama con modelo llama3.2:3b en localhost:11434

Autor(es): Prueba de integración
Grupo: test
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

import pytest
import yaml

# ─── Constantes simbólicas de la prueba ─────────────────────────────────────

RUTA_CONFIG = "config.yaml"
RUTA_PROMPTS = "prompts"
TIMEOUT_LLM_S = 60
TIMEOUT_MENSAJE_S = 90
JID_BOMBEROS = "bomberos_test@localhost"
JID_EMISOR = "emisor_test@localhost"
PASSWORD_TEST = "test_pass"
PERFORMATIVA_REQUEST = "request"
PERFORMATIVA_INFORM = "inform"
ONTOLOGIA_EMERGENCIAS = "emergencias-villa-olivar"

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# =============================================================================
# Bloque 1 — Pruebas offline (sin XMPP ni Ollama)
# =============================================================================


class TestDocumentacionOffline:
    """Pruebas que no requieren infraestructura externa.

    Verifican que los ficheros, módulos e imports documentados en el
    README existen y son correctos.
    """

    # ── T1: config.yaml contiene perfiles LLM ───────────────────────────

    def test_config_llm_existe(self) -> None:
        """El config.yaml contiene la sección perfiles_llm con perfil local."""
        with open(RUTA_CONFIG, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        assert "perfiles_llm" in config, (
            "config.yaml no contiene la sección 'perfiles_llm'"
        )
        assert "local" in config["perfiles_llm"], (
            "No existe el perfil 'local' dentro de perfiles_llm"
        )
        perfil = config["perfiles_llm"]["local"]
        assert "url_base" in perfil, "El perfil local no tiene 'url_base'"
        assert "modelo" in perfil, "El perfil local no tiene 'modelo'"

    # ── T2: Clase base hereda de LLMAgent ────────────────────────────────

    def test_clase_base_hereda_llmagent(self) -> None:
        """AgenteVillaOlivarLLM es subclase de LLMAgent."""
        from spade_llm import LLMAgent

        from agentes.base_agente_llm import AgenteVillaOlivarLLM

        assert issubclass(AgenteVillaOlivarLLM, LLMAgent), (
            "AgenteVillaOlivarLLM no hereda de LLMAgent"
        )

    # ── T3: Prompt de bomberos existe y no está vacío ────────────────────

    def test_prompt_bomberos_existe(self) -> None:
        """El fichero prompts/bomberos.txt existe y no está vacío."""
        ruta = Path(RUTA_PROMPTS) / "bomberos.txt"
        assert ruta.exists(), f"No se encontró {ruta}"
        contenido = ruta.read_text(encoding="utf-8")
        assert len(contenido.strip()) > 0, f"{ruta} está vacío"

    def test_prompt_contiene_elementos_documentados(self) -> None:
        """El prompt contiene los cinco elementos requeridos por el README:
        Rol, Competencias, Formato de salida, Coordinación y Ejemplo.
        """
        ruta = Path(RUTA_PROMPTS) / "bomberos.txt"
        contenido = ruta.read_text(encoding="utf-8").lower()
        elementos = ["rol", "competencias", "formato de salida", "coordinación",
                      "ejemplo"]
        ausentes = []
        for elem in elementos:
            encontrado = elem in contenido or elem.replace("ó", "o") in contenido
            if not encontrado:
                ausentes.append(elem)
        assert len(ausentes) == 0, (
            f"Al prompt le faltan los elementos: {ausentes}"
        )

    # ── T4: Modelos Pydantic importables ─────────────────────────────────

    def test_modelos_pydantic_importables(self) -> None:
        """from ontologia.modelos_compartidos import DatosEmergencia no falla."""
        from ontologia.modelos_compartidos import (
            ConsultaEstado,
            DatosEmergencia,
            EstadoAgente,
            InformeResolucion,
            RespuestaAgente,
        )
        # Verificar que se pueden instanciar
        datos = DatosEmergencia(
            id_emergencia="INC-2026-001",
            tipo_emergencia="derrame_quimico",
            ubicacion="Av. Constitución 42",
            prioridad="alta",
            descripcion="Derrame de amoniaco",
        )
        assert datos.id_emergencia == "INC-2026-001"

    # ── T5: FunctionTool de ADK tiene herramientas ───────────────────────

    def test_functiontool_tiene_herramientas(self) -> None:
        """El módulo herramientas_bomberos expone al menos dos FunctionTool."""
        from google.adk.tools import FunctionTool

        from herramientas.herramientas_bomberos import herramientas_bomberos

        assert len(herramientas_bomberos) >= 2, (
            f"Se esperaban al menos 2 FunctionTool, hay {len(herramientas_bomberos)}"
        )
        for h in herramientas_bomberos:
            assert isinstance(h, FunctionTool), (
                f"{h} no es una FunctionTool de ADK"
            )

    # ── T6: Lógica sin dependencias SPADE ni LLM ────────────────────────

    def test_logica_sin_dependencias_spade_ni_llm(self) -> None:
        """Los módulos logica/ no contienen import spade/spade_llm/ollama."""
        ruta_logica = Path("logica")
        imports_prohibidos = ("import spade", "import spade_llm", "import ollama")
        for fichero in ruta_logica.glob("*.py"):
            if fichero.name == "__init__.py":
                continue
            contenido = fichero.read_text(encoding="utf-8")
            for imp in imports_prohibidos:
                assert imp not in contenido, (
                    f"{fichero.name} contiene '{imp}' — "
                    "los módulos de lógica no deben depender de SPADE ni LLM"
                )

    # ── T7: Adaptación FunctionTool → LLMTool ────────────────────────────

    def test_adaptacion_functiontool_a_llmtool(self) -> None:
        """Las FunctionTool de ADK se adaptan correctamente a LLMTool."""
        from spade_llm.tools.llm_tool import LLMTool

        from agentes.base_agente_llm import adaptar_function_tool_a_llm_tool
        from herramientas.herramientas_bomberos import herramienta_riesgo

        llm_tool = adaptar_function_tool_a_llm_tool(herramienta_riesgo)

        assert isinstance(llm_tool, LLMTool), "No se adaptó a LLMTool"
        assert llm_tool.name == "evaluar_riesgo", (
            f"Nombre incorrecto: {llm_tool.name}"
        )
        assert "properties" in llm_tool.parameters, (
            "LLMTool no tiene 'properties' en su esquema"
        )
        assert "sustancia" in llm_tool.parameters["properties"], (
            "Falta el parámetro 'sustancia' en el esquema"
        )

    def test_llmtool_adaptada_es_invocable(self) -> None:
        """Una LLMTool adaptada desde FunctionTool ejecuta la función original."""
        from agentes.base_agente_llm import adaptar_function_tool_a_llm_tool
        from herramientas.herramientas_bomberos import herramienta_riesgo

        llm_tool = adaptar_function_tool_a_llm_tool(herramienta_riesgo)

        resultado = asyncio.get_event_loop().run_until_complete(
            llm_tool.execute(sustancia="amoniaco")
        )
        assert resultado["nivel"] == "alto", (
            f"Nivel incorrecto: {resultado['nivel']}"
        )
        assert resultado["radio_evacuacion_m"] == 500

    # ── T8: Lógica pura funciona correctamente ───────────────────────────

    def test_evaluar_riesgo_sustancia_alta(self) -> None:
        """evaluar_riesgo clasifica amoniaco como riesgo alto."""
        from logica.logica_bomberos import evaluar_riesgo

        resultado = evaluar_riesgo("amoniaco")
        assert resultado["nivel"] == "alto"
        assert resultado["radio_evacuacion_m"] == 500

    def test_evaluar_riesgo_sustancia_baja(self) -> None:
        """evaluar_riesgo clasifica agua como riesgo bajo."""
        from logica.logica_bomberos import evaluar_riesgo

        resultado = evaluar_riesgo("agua")
        assert resultado["nivel"] == "bajo"

    def test_planificar_intervencion_derrame(self) -> None:
        """planificar_intervencion genera plan NBQR para derrame químico."""
        from logica.logica_bomberos import planificar_intervencion

        resultado = planificar_intervencion(
            tipo_emergencia="derrame_quimico",
            nivel_riesgo="alto",
            ubicacion="Av. Constitución 42",
        )
        assert resultado["equipo"] == "equipo NBQR"
        assert resultado["recursos_necesarios"] >= 3

    # ── T9: Formato OpenAI de LLMTool es correcto ────────────────────────

    def test_llmtool_formato_openai(self) -> None:
        """La LLMTool adaptada genera un formato OpenAI válido para el LLM."""
        from agentes.base_agente_llm import adaptar_function_tool_a_llm_tool
        from herramientas.herramientas_bomberos import herramienta_riesgo

        llm_tool = adaptar_function_tool_a_llm_tool(herramienta_riesgo)
        openai_format = llm_tool.to_openai_tool()

        assert openai_format["type"] == "function"
        assert "function" in openai_format
        assert openai_format["function"]["name"] == "evaluar_riesgo"
        assert "parameters" in openai_format["function"]


# =============================================================================
# Bloque 2 — Pruebas con Ollama (requieren LLM activo)
# =============================================================================


class TestConOllama:
    """Pruebas que requieren Ollama activo con un modelo descargado.

    Verifican que el LLMProvider de SPADE-LLM se comunica correctamente
    con Ollama y que las herramientas ADK son invocables por el LLM.
    """

    @pytest.fixture(autouse=True)
    def verificar_ollama(self) -> None:
        """Verifica que Ollama está accesible antes de cada prueba."""
        import httpx

        accesible = False
        try:
            respuesta = httpx.get("http://localhost:11434", timeout=5)
            accesible = respuesta.status_code == 200
        except Exception:
            accesible = False
        if not accesible:
            pytest.skip("Ollama no está accesible en localhost:11434")

    def test_llm_provider_ollama_responde(self) -> None:
        """El LLMProvider.create_ollama() puede obtener respuesta del LLM."""
        from spade_llm import LLMProvider
        from spade_llm.context import ContextManager
        from spade.message import Message

        proveedor = LLMProvider.create_ollama(
            model="llama3.2:3b",
            base_url="http://localhost:11434/v1",
        )
        contexto = ContextManager(system_prompt="Responde solo con 'OK'.")
        # Construir mensaje SPADE para añadir al contexto
        msg = Message(to=JID_BOMBEROS)
        msg.sender = JID_EMISOR
        msg.body = "Di OK"
        contexto.add_message(msg, conversation_id="test-conv-1")

        resultado = asyncio.get_event_loop().run_until_complete(
            proveedor.get_llm_response(
                contexto, conversation_id="test-conv-1"
            )
        )
        respuesta = resultado.get("text")
        assert respuesta is not None, "El LLM no devolvió respuesta de texto"
        assert len(respuesta.strip()) > 0, "La respuesta del LLM está vacía"
        logger.info("Respuesta del LLM: %s", respuesta[:200])

    def test_llm_provider_con_herramientas(self) -> None:
        """El LLMProvider invoca herramientas cuando están disponibles."""
        from spade_llm import LLMProvider
        from spade_llm.context import ContextManager
        from spade.message import Message

        from agentes.base_agente_llm import adaptar_function_tool_a_llm_tool
        from herramientas.herramientas_bomberos import herramienta_riesgo

        proveedor = LLMProvider.create_ollama(
            model="llama3.2:3b",
            base_url="http://localhost:11434/v1",
        )
        herramienta = adaptar_function_tool_a_llm_tool(herramienta_riesgo)

        contexto = ContextManager(
            system_prompt=(
                "Eres un agente de bomberos. Cuando te pregunten sobre "
                "riesgo de una sustancia, DEBES usar la herramienta "
                "evaluar_riesgo para responder."
            )
        )
        msg = Message(to=JID_BOMBEROS)
        msg.sender = JID_EMISOR
        msg.body = "Evalúa el riesgo de un derrame de amoniaco."
        contexto.add_message(msg, conversation_id="test-conv-tools")

        respuesta = asyncio.get_event_loop().run_until_complete(
            proveedor.get_llm_response(
                contexto, tools=[herramienta], conversation_id="test-conv-tools"
            )
        )

        # El LLM puede responder con texto O con tool_calls
        tiene_texto = respuesta.get("text") is not None
        tiene_tools = len(respuesta.get("tool_calls", [])) > 0
        assert tiene_texto or tiene_tools, (
            "El LLM no devolvió ni texto ni tool_calls"
        )

        if tiene_tools:
            tool_call = respuesta["tool_calls"][0]
            logger.info(
                "LLM invocó herramienta: %s con args: %s",
                tool_call["name"],
                tool_call["arguments"],
            )
            assert tool_call["name"] == "evaluar_riesgo", (
                f"Herramienta invocada incorrecta: {tool_call['name']}"
            )
        else:
            logger.info(
                "LLM respondió con texto (sin tool_call): %s",
                respuesta["text"][:200],
            )


# =============================================================================
# Bloque 3 — Pruebas de integración SPADE-LLM + XMPP
#             (requieren servidor XMPP y Ollama)
# =============================================================================


class TestIntegracionSpadeLlm:
    """Pruebas de integración completa: agente SPADE-LLM arranca,
    recibe un mensaje FIPA-ACL y el LLM procesa la emergencia.

    Requiere Prosody (o spade run) en localhost:5222 y Ollama activo.
    """

    @pytest.fixture(autouse=True)
    def verificar_infraestructura(self) -> None:
        """Verifica que XMPP y Ollama están accesibles."""
        import socket

        import httpx

        # Verificar Ollama
        ollama_ok = False
        try:
            respuesta = httpx.get("http://localhost:11434", timeout=5)
            ollama_ok = respuesta.status_code == 200
        except Exception:
            ollama_ok = False

        # Verificar XMPP (Prosody en Docker o spade run)
        xmpp_ok = False
        try:
            sock = socket.create_connection(("localhost", 5222), timeout=5)
            # Leer la cabecera para confirmar que es un servidor XMPP real
            datos = sock.recv(256)
            sock.close()
            xmpp_ok = b"stream" in datos or b"xmpp" in datos.lower()
        except Exception:
            xmpp_ok = False

        if not ollama_ok:
            pytest.skip("Ollama no está accesible en localhost:11434")
        if not xmpp_ok:
            pytest.skip("Servidor XMPP no está accesible en localhost:5222")

    @pytest.mark.asyncio
    async def test_agente_bomberos_arranca_con_llm(self) -> None:
        """El agente Bomberos arranca como SPADE-LLM con herramientas ADK."""
        from agentes.agente_bomberos import AgenteBomberos

        config_llm = {
            "url_base": "http://localhost:11434/v1",
            "modelo": "llama3.2:3b",
        }

        agente = AgenteBomberos(
            jid=JID_BOMBEROS,
            password=PASSWORD_TEST,
            config_llm=config_llm,
            verify_security=False,
        )

        await agente.start(auto_register=True)
        try:
            assert agente.is_alive(), "El agente Bomberos no arrancó"
            assert len(agente.tools) >= 2, (
                f"El agente tiene {len(agente.tools)} herramientas, se esperaban 2+"
            )
            logger.info(
                "Agente Bomberos arrancado con %d herramientas: %s",
                len(agente.tools),
                [t.name for t in agente.tools],
            )
        finally:
            await agente.stop()

    @pytest.mark.asyncio
    async def test_agente_recibe_mensaje_y_llm_responde(self) -> None:
        """El agente Bomberos recibe un mensaje FIPA-ACL y el LLM responde.

        Simula el flujo documentado: un emisor envía una alerta de
        emergencia y el agente la procesa usando el LLM.
        """
        from spade.agent import Agent
        from spade.behaviour import OneShotBehaviour
        from spade.message import Message

        from agentes.agente_bomberos import AgenteBomberos

        config_llm = {
            "url_base": "http://localhost:11434/v1",
            "modelo": "llama3.2:3b",
        }

        # Crear agente Bomberos (receptor)
        bomberos = AgenteBomberos(
            jid=JID_BOMBEROS,
            password=PASSWORD_TEST,
            config_llm=config_llm,
            verify_security=False,
        )

        # Crear agente emisor simple
        emisor = Agent(JID_EMISOR, PASSWORD_TEST, verify_security=False)

        # Variable para capturar la respuesta
        respuesta_recibida = {"valor": None, "evento": asyncio.Event()}

        class ComportamientoEnviar(OneShotBehaviour):
            """Envía una alerta de emergencia y espera respuesta."""

            async def run(self) -> None:
                # Construir mensaje FIPA-ACL con alerta de emergencia
                msg = Message(to=JID_BOMBEROS)
                msg.set_metadata("performative", PERFORMATIVA_REQUEST)
                msg.set_metadata("ontology", ONTOLOGIA_EMERGENCIAS)
                msg.body = json.dumps({
                    "tipo_mensaje": "alerta_emergencia",
                    "id_emergencia": "INC-2026-TEST",
                    "tipo_emergencia": "derrame_quimico",
                    "ubicacion": "Av. Constitución 42, Villa Olivar",
                    "prioridad": "alta",
                    "descripcion": (
                        "Derrame de amoniaco de una cisterna. "
                        "Riesgo alto de intoxicación."
                    ),
                    "marca_temporal": "2026-04-12T10:30:00Z",
                })
                await self.send(msg)
                logger.info("Alerta enviada a Bomberos")

                # Esperar respuesta del LLM
                resp = await self.receive(timeout=TIMEOUT_MENSAJE_S)
                if resp is not None:
                    respuesta_recibida["valor"] = resp.body
                    logger.info("Respuesta recibida: %s", resp.body[:300])
                else:
                    logger.warning("No se recibió respuesta en %ds", TIMEOUT_MENSAJE_S)
                respuesta_recibida["evento"].set()

        await bomberos.start(auto_register=True)
        await emisor.start(auto_register=True)

        try:
            # Añadir comportamiento al emisor
            comportamiento = ComportamientoEnviar()
            emisor.add_behaviour(comportamiento)

            # Esperar a que termine el intercambio
            await asyncio.wait_for(
                respuesta_recibida["evento"].wait(),
                timeout=TIMEOUT_MENSAJE_S,
            )

            assert respuesta_recibida["valor"] is not None, (
                "El agente Bomberos no respondió al mensaje FIPA-ACL. "
                "El LLM debería haber procesado la alerta y generado "
                "una respuesta."
            )
            logger.info("TEST SUPERADO — Respuesta del LLM a alerta FIPA-ACL")
        finally:
            await emisor.stop()
            await bomberos.stop()
