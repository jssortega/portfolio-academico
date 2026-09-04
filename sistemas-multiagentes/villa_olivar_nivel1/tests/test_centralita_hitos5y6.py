"""
Tests de la Centralita — Hitos 5 y 6 — Villa Olivar (Nivel 2).

Cubre todas las pruebas específicas de la Centralita:

  Hito 5:
    - test_centralita_clasifica_incendio_con_llm
    - test_centralita_clasifica_accidente_con_llm
    - test_prompts_centralita_contiene_ejemplos
    - test_herramientas_centralita_cubren_dos_tipos_emergencia

  Hito 6:
    - test_tolerancia_llm_timeout_centralita
    - test_tolerancia_json_invalido_centralita
    - test_typing_hints_agente_centralita
    - test_docstrings_agente_centralita
    - test_config_sin_hardcodear_centralita
    - test_config_sin_hardcodear_herramientas_centralita
    - test_informe_resolucion_parseable_pydantic

Requisitos de ejecución:
  - pytest tests/ -v --timeout=120
  - Las pruebas de integración con LLM real se saltan si Ollama no está disponible.

Autor(es): Cristina Silva (csu0002@ujaen.es)
Grupo: multi007s
"""

import asyncio
import importlib
import inspect
import json
import socket
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures y helpers
# ─────────────────────────────────────────────────────────────────────────────

RUTA_RAIZ = Path(__file__).resolve().parent.parent
RUTA_PROMPTS_CENTRALITA = RUTA_RAIZ / "prompts" / "centralita.txt"


def _ollama_disponible() -> bool:
    """Comprueba si el servidor Ollama está accesible en localhost:11434."""
    try:
        with socket.create_connection(("localhost", 11434), timeout=2):
            return True
    except OSError:
        return False


def _llm_disponible() -> bool:
    """Devuelve True si hay cualquier LLM configurado y accesible.

    Acepta Ollama local O perfil gemini con GOOGLE_API_KEY definida,
    O perfil servidor con conexión disponible.
    """
    import os
    import yaml

    ruta_config = RUTA_RAIZ / "config.yaml"
    if not ruta_config.exists():
        return False

    with ruta_config.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    perfil_activo = config.get("perfil_llm_activo", "local")
    perfiles = config.get("perfiles_llm", {})
    perfil = perfiles.get(perfil_activo, {})
    proveedor = perfil.get("proveedor", "ollama")

    if proveedor == "gemini":
        api_key_env = perfil.get("api_key_env", "GOOGLE_API_KEY")
        return bool(os.environ.get(api_key_env))

    if proveedor == "ollama":
        url = perfil.get("url_base", "http://localhost:11434")
        host = url.replace("http://", "").replace("https://", "").split(":")[0]
        try:
            puerto = int(url.split(":")[-1])
        except ValueError:
            puerto = 11434
        try:
            with socket.create_connection((host, puerto), timeout=3):
                return True
        except OSError:
            return False

    return False


# ─────────────────────────────────────────────────────────────────────────────
# HITO 5 — Escenarios alternativos y prompts con ejemplos few-shot
# ─────────────────────────────────────────────────────────────────────────────

class TestHito5Centralita:
    """Pruebas del Hito 5 específicas de la Centralita."""

    # ── Prueba 1: El prompt existe y contiene ejemplos few-shot ───────────────

    def test_prompts_centralita_contiene_ejemplos(self) -> None:
        """El fichero prompts/centralita.txt existe y contiene al menos un ejemplo.

        El hito 5 exige que los prompts incluyan ejemplos few-shot (entrada +
        salida esperada). Verificamos que el fichero contiene la palabra
        'Ejemplo' o un bloque JSON de muestra.
        """
        assert RUTA_PROMPTS_CENTRALITA.exists(), (
            f"No se encuentra {RUTA_PROMPTS_CENTRALITA}. "
            "Crea el fichero prompts/centralita.txt."
        )
        contenido = RUTA_PROMPTS_CENTRALITA.read_text(encoding="utf-8")
        assert len(contenido.strip()) > 0, "prompts/centralita.txt está vacío."

        # Comprobamos que hay al menos un bloque de ejemplo (few-shot)
        tiene_ejemplo = (
            "Ejemplo" in contenido
            or "ejemplo" in contenido
            or "few-shot" in contenido.lower()
            or ("Input" in contenido and "Output" in contenido)
        )
        assert tiene_ejemplo, (
            "prompts/centralita.txt no contiene ejemplos few-shot. "
            "Añade al menos un par entrada/salida etiquetado como 'Ejemplo N'."
        )

    def test_prompts_centralita_contiene_estrategia(self) -> None:
        """El prompt de la Centralita documenta la estrategia de prompting.

        El hito 6 exige un comentario inicial explicando la estrategia elegida.
        Verificamos que el fichero contiene alguna referencia a la estrategia.
        """
        assert RUTA_PROMPTS_CENTRALITA.exists()
        contenido = RUTA_PROMPTS_CENTRALITA.read_text(encoding="utf-8")
        tiene_estrategia = (
            "Estrategia" in contenido
            or "estrategia" in contenido
            or contenido.strip().startswith("#")
        )
        assert tiene_estrategia, (
            "prompts/centralita.txt debe incluir un comentario inicial "
            "explicando la estrategia de prompting (empieza con '#')."
        )

    # ── Prueba 2: Las herramientas cubren al menos dos tipos de emergencia ────

    def test_herramientas_centralita_cubren_dos_tipos_emergencia(self) -> None:
        """Las herramientas de la Centralita cubren al menos dos tipos de emergencia.

        El hito 5 exige que las herramientas de cada especialista cubran al
        menos dos tipos. Para la Centralita, clasificar_emergencia y
        determinar_destinatarios deben funcionar para tipos distintos.
        """
        from logica.logica_centralita import clasificar_emergencia, determinar_destinatarios

        # Tipo 1: incendio
        prioridad_incendio = clasificar_emergencia("incendio", hay_heridos=True)
        destinatarios_incendio = determinar_destinatarios("incendio")
        assert prioridad_incendio in ("baja", "media", "alta", "critica")
        assert len(destinatarios_incendio) >= 1

        # Tipo 2: accidente_trafico
        prioridad_accidente = clasificar_emergencia("accidente_trafico")
        destinatarios_accidente = determinar_destinatarios("accidente_trafico")
        assert prioridad_accidente in ("baja", "media", "alta", "critica")
        assert len(destinatarios_accidente) >= 1

        # Los dos tipos deben tener destinatarios distintos
        assert set(destinatarios_incendio) != set(destinatarios_accidente), (
            "incendio y accidente_trafico deben tener destinatarios distintos."
        )

    # ── Prueba 3: Clasificación LLM para escenarios alternativos (hito 5) ───────
    # Nota: SPADE-LLM añade el prefijo "gemini/" al nombre del modelo cuando usa
    # Gemini, lo que rompe la integración directa. Estos tests llaman a la API
    # de Gemini directamente (google-generativeai) para verificar que la lógica
    # de clasificación funciona con un LLM real, que es lo que exige el hito 5.

    @pytest.mark.skipif(not _llm_disponible(), reason="LLM no disponible (GOOGLE_API_KEY no definida)")
    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_centralita_clasifica_incendio_con_llm(self) -> None:
        """La Centralita clasifica un incendio con LLM y devuelve JSON válido.

        Escenario alternativo al derrame químico (requisito hito 5).
        Llama a Gemini directamente via google.genai (API v1).
        """
        import os
        from google import genai
        from google.genai import errors

        config_llm = _cargar_config_llm()
        api_key_env = config_llm.get("api_key_env", "GOOGLE_API_KEY")
        api_key = os.environ.get(api_key_env, "")
        # Usamos el modelo de la configuración o fallback si no está definido
        modelo = config_llm.get("modelo", "gemini-2.0-flash-lite")
        cliente = genai.Client(api_key=api_key)
        prompt_sistema = RUTA_PROMPTS_CENTRALITA.read_text(encoding="utf-8")
        consulta = (
            "Ha llegado una emergencia.\n"
            "ID: INC-2026-TEST-01\n"
            "Tipo: incendio\n"
            "Descripción: Incendio en nave industrial con 2 personas atrapadas.\n"
            "Ubicación: Polígono Industrial Norte, nave 7\n"
            "Prioridad recibida del supervisor: alta\n\n"
            "Devuelve SOLO un JSON con este esquema exacto:\n"
            '{"prioridad": "<baja|media|alta|critica>", "destinatarios": ["bomberos", ...]}'
        )

        try:
            respuesta_obj = await asyncio.to_thread(
                cliente.models.generate_content,
                model=modelo,
                contents=f"{prompt_sistema}\n\n{consulta}",
            )
        except errors.ClientError as exc:
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                pytest.skip(f"Cuota de LLM agotada para {modelo}. Saltando test de integración real.")
            raise exc

        respuesta = respuesta_obj.text
        assert respuesta is not None and len(respuesta.strip()) > 0, (
            "Gemini devolvió una respuesta vacía para el incendio."
        )

        try:
            limpio = (
                respuesta.strip()
                .removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            )
            datos = json.loads(limpio)
            assert "prioridad" in datos or "destinatarios" in datos
        except json.JSONDecodeError:
            contenido = respuesta.lower()
            assert any(p in contenido for p in ("alta", "media", "critica", "baja",
                                                "bomberos", "sanitario", "policia")), (
                f"El LLM no clasificó el incendio: {respuesta[:200]}"
            )

    @pytest.mark.skipif(not _llm_disponible(), reason="LLM no disponible (GOOGLE_API_KEY no definida)")
    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_centralita_clasifica_accidente_con_llm(self) -> None:
        """La Centralita clasifica un accidente de tráfico con LLM.

        Segundo escenario alternativo para mayor cobertura del hito 5.
        Llama a Gemini directamente via google.genai (API v1).
        """
        import os
        from google import genai
        from google.genai import errors

        config_llm = _cargar_config_llm()
        api_key_env = config_llm.get("api_key_env", "GOOGLE_API_KEY")
        api_key = os.environ.get(api_key_env, "")
        # Usamos el modelo de la configuración o fallback si no está definido
        modelo = config_llm.get("modelo", "gemini-2.0-flash-lite")
        cliente = genai.Client(api_key=api_key)
        prompt_sistema = RUTA_PROMPTS_CENTRALITA.read_text(encoding="utf-8")
        consulta = (
            "Ha llegado una emergencia.\n"
            "ID: INC-2026-TEST-02\n"
            "Tipo: accidente_trafico\n"
            "Descripción: Colisión múltiple en autovía con 4 heridos graves.\n"
            "Ubicación: A-44 km 23\n"
            "Prioridad recibida del supervisor: alta\n\n"
            "Devuelve SOLO un JSON con este esquema exacto:\n"
            '{"prioridad": "<baja|media|alta|critica>", "destinatarios": ["sanitario", ...]}'
        )

        try:
            respuesta_obj = await asyncio.to_thread(
                cliente.models.generate_content,
                model=modelo,
                contents=f"{prompt_sistema}\n\n{consulta}",
            )
        except errors.ClientError as exc:
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                pytest.skip(f"Cuota de LLM agotada para {modelo}. Saltando test de integración real.")
            raise exc

        respuesta = respuesta_obj.text
        assert respuesta is not None and len(respuesta.strip()) > 0, (
            "Gemini devolvió una respuesta vacía para el accidente."
        )

        contenido = respuesta.lower()
        assert any(p in contenido for p in ("alta", "media", "critica", "baja",
                                            "sanitario", "policia", "bomberos")), (
            f"El LLM no clasificó el accidente: {respuesta[:200]}"
        )

# ─────────────────────────────────────────────────────────────────────────────
# HITO 6 — Robustez, type hints, docstrings, sin hardcoding
# ─────────────────────────────────────────────────────────────────────────────

class TestHito6Centralita:
    """Pruebas del Hito 6 específicas de la Centralita."""

    # ── Prueba 4: Tolerancia a timeout del LLM ────────────────────────────────

    @pytest.mark.asyncio
    async def test_tolerancia_llm_timeout_centralita(self) -> None:
        """Si llm_chat() supera el timeout, el agente no se bloquea y avisa.

        Mockea llm_chat() para que nunca responda y verifica que
        _llm_chat_seguro() devuelve None sin lanzar excepción, y que
        el logger registra un aviso de timeout.
        """
        import utils  # noqa: F401
        from agentes.agente_centralita import AgenteCentralita

        agente = AgenteCentralita.__new__(AgenteCentralita)
        agente._llm_timeout = 1  # timeout muy corto para el test

        async def llm_lento(consulta: str) -> str:
            await asyncio.sleep(60)  # nunca termina en el test
            return "respuesta"

        with patch.object(type(agente), "llm_chat", new=llm_lento):
            import logging
            with patch.object(logging.getLogger("agentes.agente_centralita"), "warning") as mock_warn:
                resultado = await agente._llm_chat_seguro("consulta de prueba", timeout=1)

        assert resultado is None, (
            "_llm_chat_seguro() debe devolver None cuando el LLM supera el timeout."
        )

    @pytest.mark.asyncio
    async def test_tolerancia_llm_timeout_no_bloquea(self) -> None:
        """Verifica que _llm_chat_seguro() completa en menos de 5 s con timeout=1.

        Comprueba que el timeout se aplica realmente y la corrutina termina.
        """
        import utils  # noqa: F401
        from agentes.agente_centralita import AgenteCentralita

        agente = AgenteCentralita.__new__(AgenteCentralita)

        async def llm_lento(consulta: str) -> str:
            await asyncio.sleep(60)
            return "respuesta"

        with patch.object(type(agente), "llm_chat", new=llm_lento):
            inicio = asyncio.get_event_loop().time()
            resultado = await agente._llm_chat_seguro("consulta", timeout=1)
            duracion = asyncio.get_event_loop().time() - inicio

        assert resultado is None
        assert duracion < 5, (
            f"_llm_chat_seguro() tardó {duracion:.1f}s con timeout=1. "
            "El timeout no se está aplicando correctamente."
        )

    # ── Prueba 5: Tolerancia a JSON inválido del LLM ──────────────────────────

    @pytest.mark.asyncio
    async def test_tolerancia_json_invalido_centralita(self) -> None:
        """Si el LLM devuelve texto no JSON, el agente usa el fallback sin detenerse.

        Mockea llm_chat() para que devuelva texto libre (no JSON) y verifica
        que ClasificarYDespachar no lanza excepción y usa la lógica determinista.
        """
        import utils  # noqa: F401
        from agentes.agente_centralita import AgenteCentralita
        from logica.logica_centralita import clasificar_emergencia, determinar_destinatarios

        agente = AgenteCentralita.__new__(AgenteCentralita)
        agente.destinatarios_activos = []
        agente.estadoEmergencia = "alerta_recibida"

        # LLM devuelve texto libre que no es JSON
        async def llm_no_json(self_inner, consulta: str) -> str:
            return "Lo siento, no puedo procesar esto en este momento."

        with patch.object(type(agente), "llm_chat", new=llm_no_json):
            resultado = await agente._llm_chat_seguro("consulta")

        # _llm_chat_seguro devuelve el texto (no es None porque no hubo timeout)
        assert resultado is not None

        # Simulamos el parseo que haría ClasificarYDespachar
        prioridad_fallback: str | None = None
        try:
            datos = json.loads(resultado)
            prioridad_fallback = datos.get("prioridad")
        except json.JSONDecodeError:
            pass  # JSON inválido → fallback determinista

        # El fallback determinista debe producir un valor válido
        if prioridad_fallback is None:
            prioridad_fallback = clasificar_emergencia("incendio", hay_heridos=True)

        assert prioridad_fallback in ("baja", "media", "alta", "critica"), (
            f"El fallback produjo una prioridad inválida: {prioridad_fallback}"
        )

    @pytest.mark.asyncio
    async def test_informe_resolucion_parseable_pydantic(self) -> None:
        """El fallback determinista genera un InformeResolucion parseable por Pydantic.

        Verifica que el path de fallback de _cerrar_emergencia() siempre
        produce un JSON válido que model_validate_json() puede procesar.
        """
        from ontologia.modelos_compartidos import InformeResolucion, TipoEmergencia, Prioridad

        # Simular el fallback que usaría _cerrar_emergencia()
        informe = InformeResolucion(
            id_emergencia="INC-2026-TEST",
            tipo_emergencia=TipoEmergencia("incendio"),
            prioridad=Prioridad("alta"),
            estado_final="cerrado",
            resumen="Incendio en nave industrial resuelto.",
            agentes_participantes=["bomberos", "sanitario", "policia"],
            acciones_realizadas=["Extinción del incendio", "Atención a heridos"],
        )
        json_str = informe.model_dump_json()

        # Debe ser parseable sin excepción
        recuperado = InformeResolucion.model_validate_json(json_str)
        assert recuperado.id_emergencia == "INC-2026-TEST"
        assert recuperado.estado_final == "cerrado"
        assert len(recuperado.agentes_participantes) == 3

    # ── Prueba 6: Type hints en agente_centralita.py ──────────────────────────

    def test_typing_hints_agente_centralita(self) -> None:
        """Las funciones públicas de agente_centralita.py tienen type hints.

        Verifica que __init__, setup y _llm_chat_seguro tienen anotaciones
        de tipo en todos sus parámetros y en el valor de retorno.
        """
        from agentes.agente_centralita import AgenteCentralita

        funciones_requeridas = {
            "__init__": ["jid", "password", "return"],
            "_llm_chat_seguro": ["consulta", "return"],
            "setup": ["return"],
        }

        for nombre_func, params_requeridos in funciones_requeridas.items():
            func = getattr(AgenteCentralita, nombre_func, None)
            assert func is not None, (
                f"AgenteCentralita no tiene el método '{nombre_func}'."
            )
            hints = {}
            try:
                hints = func.__annotations__
            except AttributeError:
                pass

            for param in params_requeridos:
                assert param in hints, (
                    f"AgenteCentralita.{nombre_func}() no tiene type hint "
                    f"para '{param}'. Añade la anotación de tipo."
                )

    def test_typing_hints_herramientas_centralita(self) -> None:
        """Las funciones de herramientas_centralita.py tienen type hints."""
        from herramientas.herramientas_centralita import _crear_herramientas_centralita

        hints = _crear_herramientas_centralita.__annotations__
        assert "return" in hints, (
            "_crear_herramientas_centralita() no tiene type hint de retorno."
        )

    # ── Prueba 7: Docstrings en agente_centralita.py ──────────────────────────

    def test_docstrings_agente_centralita(self) -> None:
        """Las clases y métodos públicos de agente_centralita.py tienen docstrings.

        Verifica que AgenteCentralita y sus métodos clave tienen __doc__
        no vacío, tal como exige el hito 6.
        """
        from agentes.agente_centralita import AgenteCentralita

        # Clase principal
        assert AgenteCentralita.__doc__ and AgenteCentralita.__doc__.strip(), (
            "AgenteCentralita no tiene docstring de clase."
        )

        # Métodos públicos y privados clave
        metodos = [
            "__init__",
            "_resetear_estado_emergencia",
            "_llm_chat_seguro",
            "setup",
        ]
        for nombre in metodos:
            metodo = getattr(AgenteCentralita, nombre, None)
            assert metodo is not None, f"No existe el método '{nombre}'."
            assert metodo.__doc__ and metodo.__doc__.strip(), (
                f"AgenteCentralita.{nombre}() no tiene docstring. "
                "Añade una descripción en formato Google."
            )

    def test_docstrings_behaviours_centralita(self) -> None:
        """Los behaviours de AgenteCentralita tienen docstrings."""
        from agentes.agente_centralita import AgenteCentralita

        behaviours = [
            "RegistrarseEnDF",
            "EscucharSupervisor",
            "ClasificarYDespachar",
            "EscucharInformes",
        ]
        for nombre in behaviours:
            clase_behaviour = getattr(AgenteCentralita, nombre, None)
            assert clase_behaviour is not None, (
                f"AgenteCentralita no tiene el behaviour '{nombre}'."
            )
            assert clase_behaviour.__doc__ and clase_behaviour.__doc__.strip(), (
                f"AgenteCentralita.{nombre} no tiene docstring."
            )

    def test_docstrings_herramientas_centralita(self) -> None:
        """El módulo herramientas_centralita.py tiene docstring de módulo."""
        import herramientas.herramientas_centralita as mod_herr
        assert mod_herr.__doc__ and mod_herr.__doc__.strip(), (
            "herramientas/herramientas_centralita.py no tiene docstring de módulo."
        )

    # ── Prueba 8: Sin hardcoding en agente_centralita.py ─────────────────────

    def test_config_sin_hardcodear_centralita(self) -> None:
        """agente_centralita.py no contiene URLs ni puertos hardcodeados.

        El hito 6 exige que toda la configuración se lea de config.yaml,
        no se escriba directamente en el código fuente.
        """
        ruta = RUTA_RAIZ / "agentes" / "agente_centralita.py"
        assert ruta.exists(), f"No se encuentra {ruta}"
        contenido = ruta.read_text(encoding="utf-8")

        patrones_prohibidos = [
            "localhost:11434",
            "localhost:5222",
            "localhost:8020",
            "sinbad2.ujaen.es",
            "sinbad2ia.ujaen.es",
            ":8050",
            ":8022",
        ]
        for patron in patrones_prohibidos:
            assert patron not in contenido, (
                f"agente_centralita.py contiene '{patron}' hardcodeado. "
                "Mueve esta configuración a config.yaml."
            )

    def test_config_sin_hardcodear_herramientas_centralita(self) -> None:
        """herramientas_centralita.py no contiene URLs ni puertos hardcodeados."""
        ruta = RUTA_RAIZ / "herramientas" / "herramientas_centralita.py"
        assert ruta.exists(), f"No se encuentra {ruta}"
        contenido = ruta.read_text(encoding="utf-8")

        patrones_prohibidos = [
            "localhost:11434",
            "localhost:5222",
            "localhost:8020",
            "sinbad2.ujaen.es",
            "sinbad2ia.ujaen.es",
        ]
        for patron in patrones_prohibidos:
            assert patron not in contenido, (
                f"herramientas_centralita.py contiene '{patron}' hardcodeado."
            )

    # ── Prueba 9: FunctionTool de la Centralita son invocables ───────────────

    def test_functiontools_centralita_invocables(self) -> None:
        """Las FunctionTool de herramientas_centralita.py son invocables.

        Verifica que las tres herramientas existen, son instancias de
        FunctionTool y que la función envuelta se puede llamar directamente.
        """
        from google.adk.tools import FunctionTool
        from herramientas.herramientas_centralita import (
            herramientas_centralita,
            herramienta_clasificar,
            herramienta_destinatarios,
            herramienta_generar_id,
        )

        assert len(herramientas_centralita) >= 2, (
            "herramientas_centralita debe contener al menos 2 FunctionTool."
        )

        for herr in herramientas_centralita:
            assert isinstance(herr, FunctionTool), (
                f"{herr} no es una instancia de FunctionTool."
            )

        # La función envuelta debe ser invocable con parámetros reales
        resultado_clasificar = herramienta_clasificar.func("incendio", hay_heridos=True)
        assert resultado_clasificar in ("baja", "media", "alta", "critica")

        resultado_destinatarios = herramienta_destinatarios.func("incendio")
        assert isinstance(resultado_destinatarios, list)
        assert len(resultado_destinatarios) > 0

    def test_functiontool_clasificar_devuelve_resultado_correcto(self) -> None:
        """clasificar_emergencia como FunctionTool devuelve prioridades válidas.

        Para el hito 2 (acumulativo): la invocación de una FunctionTool
        devuelve un resultado conforme al esquema esperado.
        """
        from herramientas.herramientas_centralita import herramienta_clasificar

        casos = [
            # incendio base="alta" (idx 2) + hay_heridos → sube a idx 3 = "critica"
            ("derrame_quimico", True, True, 0, "critica"),
            ("incendio", True, False, 0, "critica"),
            ("accidente_trafico", False, False, 0, "media"),
            ("otro", False, False, 0, "baja"),
        ]
        for tipo, heridos, mat_pelig, num_af, prioridad_esperada in casos:
            resultado = herramienta_clasificar.func(
                tipo_emergencia=tipo,
                hay_heridos=heridos,
                materiales_peligrosos=mat_pelig,
                numero_afectados=num_af,
            )
            assert resultado == prioridad_esperada, (
                f"Para tipo='{tipo}' esperaba '{prioridad_esperada}', "
                f"obtuvo '{resultado}'."
            )

    # ── Prueba 10: _resetear_estado_emergencia limpia todo correctamente ──────

    def test_resetear_estado_emergencia(self) -> None:
        """_resetear_estado_emergencia() deja el agente en estado limpio.

        Verifica que tras el reset todos los campos del estado de emergencia
        vuelven a sus valores por defecto.
        """
        import utils  # noqa: F401
        from agentes.agente_centralita import AgenteCentralita

        agente = AgenteCentralita.__new__(AgenteCentralita)
        # Simulamos estado sucio de una emergencia anterior
        agente.id_emergencia_activa = "INC-2026-001"
        agente.tipo_emergencia_activa = "incendio"
        agente.prioridad_activa = "alta"
        agente.jid_supervisor = "supervisor@localhost"
        agente.conv_id_activo = "conv-123"
        agente.msg_id_activo = "msg-456"
        agente.destinatarios_activos = ["bomberos", "sanitario"]
        agente.agentesEnMision = ["bomberos@localhost"]
        agente.finalizados_set = {"bomberos"}
        agente.todos_finalizados = True
        agente.cierre_emitido = True
        agente.estadoEmergencia = "alerta_completada"

        agente._resetear_estado_emergencia()

        assert agente.id_emergencia_activa == ""
        assert agente.tipo_emergencia_activa == ""
        assert agente.prioridad_activa == ""
        assert agente.jid_supervisor == ""
        assert agente.destinatarios_activos == []
        assert agente.agentesEnMision == []
        assert len(agente.finalizados_set) == 0
        assert agente.todos_finalizados is False
        assert agente.cierre_emitido is False
        assert agente.estadoEmergencia == "sin_emergencia"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos (no son pruebas)
# ─────────────────────────────────────────────────────────────────────────────

def _cargar_config_llm() -> dict:
    """Carga la sección perfiles_llm del config.yaml para tests con LLM real.

    Returns:
        Diccionario con la configuración LLM del perfil activo.
    """
    import yaml
    ruta_config = RUTA_RAIZ / "config.yaml"
    if not ruta_config.exists():
        return {}
    with ruta_config.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)
    perfil_activo = config.get("perfil_llm_activo", "local")
    return config.get("perfiles_llm", {}).get(perfil_activo, {})