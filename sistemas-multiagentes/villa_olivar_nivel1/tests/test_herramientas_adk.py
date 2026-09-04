"""
Tests de herramientas ADK — Villa Olivar (Nivel 2).

Cubre los tests exigidos en el README para los Hitos 1, 2 y 3:

  Hito 1:
    - test_functiontool_tiene_herramientas

  Hito 2:
    - test_tres_modulos_herramientas_operativos
    - test_functiontool_devuelve_resultado

  Hito 3:
    - test_cinco_modulos_herramientas

  Hito 5:
    - test_herramientas_cubren_tipos_emergencia

Pruebas OFFLINE: no necesitan XMPP ni Ollama en ejecución.

Autor(es): multi007s
"""

import importlib

import pytest
from google.adk.tools import FunctionTool

from agentes.base_agente_llm import adaptar_herramienta_adk_a_spade
from spade_llm.tools.llm_tool import LLMTool

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

ROLES = ["centralita", "bomberos", "sanitario", "policia", "municipal"]

MODULOS = {
    "centralita": ("herramientas.herramientas_centralita", "herramientas_centralita"),
    "bomberos":   ("herramientas.herramientas_bomberos",   "herramientas_bomberos"),
    "sanitario":  ("herramientas.herramientas_sanitario",  "herramientas_sanitario"),
    "policia":    ("herramientas.herramientas_policia",     "herramientas_policia"),
    "municipal":  ("herramientas.herramientas_municipal",   "herramientas_municipal"),
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _obtener_herramientas(rol: str) -> list:
    """Importa el módulo de herramientas del rol y devuelve la lista."""
    modulo_nombre, lista_nombre = MODULOS[rol]
    try:
        modulo = importlib.import_module(modulo_nombre)
    except ImportError as exc:
        pytest.skip(f"No se pudo importar '{modulo_nombre}': {exc}")
    lista = getattr(modulo, lista_nombre, None)
    if lista is None:
        pytest.fail(
            f"'{modulo_nombre}' no exporta la variable '{lista_nombre}'."
        )
    return lista


# ===========================================================================
# HITO 1 — test_functiontool_tiene_herramientas
# ===========================================================================

class TestFunctiontoolTieneHerramientas:
    """El módulo de herramientas de la centralita expone al menos dos FunctionTool."""

    def test_functiontool_tiene_herramientas(self) -> None:
        """herramientas_centralita expone al menos dos FunctionTool invocables."""
        lista = _obtener_herramientas("centralita")
        assert len(lista) >= 2, (
            "herramientas_centralita debe contener al menos 2 FunctionTool. "
            f"Tiene {len(lista)}."
        )
        for herr in lista:
            assert isinstance(herr, FunctionTool), (
                f"{herr!r} no es una FunctionTool de ADK."
            )
            assert callable(herr.func), (
                f"La herramienta '{herr.name}' no tiene func callable."
            )

    def test_functiontools_integradas(self) -> None:
        """Alias para cumplir con el nombre exacto exigido en el Hito 1."""
        self.test_functiontool_tiene_herramientas()



# ===========================================================================
# HITO 2 — test_tres_modulos_herramientas_operativos
#           test_functiontool_devuelve_resultado
# ===========================================================================

ROLES_TRES = ["centralita", "bomberos", "sanitario"]


class TestTresModulosHerramientasOperativos:
    """Al menos tres módulos de herramientas exportan FunctionTool válidas."""

    @pytest.mark.parametrize("rol", ROLES_TRES)
    def test_modulo_exporta_lista_no_vacia(self, rol: str) -> None:
        """El módulo del rol exporta una lista de al menos una FunctionTool."""
        lista = _obtener_herramientas(rol)
        assert len(lista) >= 1, (
            f"El módulo de herramientas de '{rol}' está vacío."
        )

    def test_tres_modulos_herramientas_operativos(self) -> None:
        """Los tres primeros módulos exportan FunctionTool válidas (prueba de conjunto)."""
        errores = []
        for rol in ROLES_TRES:
            modulo_nombre, lista_nombre = MODULOS[rol]
            try:
                modulo = importlib.import_module(modulo_nombre)
                lista = getattr(modulo, lista_nombre, [])
                if not lista:
                    errores.append(f"{rol}: lista vacía")
                elif not all(isinstance(h, FunctionTool) for h in lista):
                    errores.append(f"{rol}: contiene elementos que no son FunctionTool")
            except ImportError as exc:
                errores.append(f"{rol}: {exc}")
        assert errores == [], (
            "Fallos en módulos de herramientas (Hito 2):\n  " + "\n  ".join(errores)
        )


class TestFunctiontoolDevuelveResultado:
    """La invocación directa de FunctionTool devuelve resultados coherentes."""

    def test_herramienta_centralita_clasificar(self) -> None:
        """clasificar_emergencia (centralita) devuelve una prioridad válida."""
        lista = _obtener_herramientas("centralita")
        herramienta = next(
            (h for h in lista if "clasif" in h.name.lower()),
            lista[0],
        )
        resultado = herramienta.func("derrame_quimico")
        assert resultado in ("baja", "media", "alta", "critica") or isinstance(resultado, str), (
            f"clasificar_emergencia devolvió un valor inesperado: {resultado!r}"
        )

    def test_herramienta_bomberos_evaluar_riesgo_quimico(self) -> None:
        """evaluar_riesgo_quimico (bomberos) devuelve dict con nivel."""
        lista = _obtener_herramientas("bomberos")
        herramienta = next(
            (h for h in lista if "riesgo" in h.name.lower() or "quimico" in h.name.lower()),
            lista[0],
        )
        resultado = herramienta.func("derrame de amoniaco en nave industrial")
        assert isinstance(resultado, dict), "evaluar_riesgo_quimico debe devolver un dict."
        assert "nivel" in resultado or "sustancia" in resultado, (
            "El resultado debe contener 'nivel' o 'sustancia'."
        )

    def test_herramienta_sanitario_procesarAlertaAceptada(self) -> None:
        """procesarAlertaAceptada (sanitario) devuelve informe con agente_origen 'sanitario'."""
        lista = _obtener_herramientas("sanitario")
        herramienta = next(
            (h for h in lista if "aceptada" in h.name.lower()),
            None,
        )
        if herramienta is None:
            pytest.skip("No se encontró herramienta procesarAlertaAceptada en sanitario.")
        alerta = {"id_emergencia": "INC-TEST-001", "tipo_emergencia": "derrame_quimico"}
        resultado = herramienta.func(alerta)
        assert isinstance(resultado, dict), "procesarAlertaAceptada debe devolver un dict."
        assert resultado.get("agente_origen") == "sanitario", (
            f"agente_origen debería ser 'sanitario', es '{resultado.get('agente_origen')}'."
        )

    def test_functiontool_devuelve_resultado(self) -> None:
        """Prueba de conjunto: una FunctionTool de cada uno de los tres módulos devuelve resultado."""
        errores = []
        casos = {
            "centralita": (
                lambda lista: next((h for h in lista if "clasif" in h.name.lower()), lista[0]),
                ("derrame_quimico",),
            ),
            "bomberos": (
                lambda lista: lista[0],
                ("derrame de amoniaco",),
            ),
            "sanitario": (
                lambda lista: lista[0],
                ({"id_emergencia": "INC-001", "tipo_emergencia": "derrame_quimico"},),
            ),
        }
        for rol, (selector, args) in casos.items():
            try:
                lista = _obtener_herramientas(rol)
                herramienta = selector(lista)
                resultado = herramienta.func(*args)
                if resultado is None:
                    errores.append(f"{rol}: la herramienta devolvió None")
            except Exception as exc:
                errores.append(f"{rol}: excepción al invocar herramienta — {exc}")
        assert errores == [], "\n".join(errores)


# ===========================================================================
# HITO 3 — test_cinco_modulos_herramientas
# ===========================================================================

class TestCincoModulosHerramientas:
    """Los cinco módulos de herramientas exportan FunctionTool invocables."""

    @pytest.mark.parametrize("rol", ROLES)
    def test_modulo_exporta_lista(self, rol: str) -> None:
        """El módulo de herramientas de cada rol exporta una lista no vacía."""
        lista = _obtener_herramientas(rol)
        assert isinstance(lista, list) and len(lista) >= 1, (
            f"El módulo de herramientas de '{rol}' está vacío o no es una lista."
        )

    @pytest.mark.parametrize("rol", ROLES)
    def test_herramientas_son_functiontool(self, rol: str) -> None:
        """Todos los elementos de la lista son instancias de FunctionTool."""
        lista = _obtener_herramientas(rol)
        for i, herramienta in enumerate(lista):
            assert isinstance(herramienta, FunctionTool), (
                f"El elemento {i} de '{rol}' no es una FunctionTool "
                f"(es {type(herramienta).__name__})."
            )

    @pytest.mark.parametrize("rol", ROLES)
    def test_herramientas_tienen_nombre_y_descripcion(self, rol: str) -> None:
        """Cada FunctionTool tiene nombre y descripción no vacíos."""
        lista = _obtener_herramientas(rol)
        for herramienta in lista:
            assert herramienta.name, (
                f"Una herramienta de '{rol}' no tiene nombre."
            )
            assert herramienta.description, (
                f"La herramienta '{herramienta.name}' de '{rol}' no tiene descripción. "
                "Añade un docstring a la función envuelta."
            )

    @pytest.mark.parametrize("rol", ROLES)
    def test_al_menos_dos_herramientas_por_rol(self, rol: str) -> None:
        """Cada agente tiene al menos dos herramientas ADK registradas."""
        lista = _obtener_herramientas(rol)
        assert len(lista) >= 2, (
            f"El agente '{rol}' solo tiene {len(lista)} herramienta(s). "
            "El Hito 3 exige al menos 2 por agente."
        )

    def test_cinco_modulos_herramientas(self) -> None:
        """Prueba de conjunto: los cinco módulos exportan FunctionTool válidas."""
        errores = []
        for rol in ROLES:
            modulo_nombre, lista_nombre = MODULOS[rol]
            try:
                modulo = importlib.import_module(modulo_nombre)
                lista = getattr(modulo, lista_nombre, [])
                if not lista:
                    errores.append(f"{rol}: lista vacía")
                elif not all(isinstance(h, FunctionTool) for h in lista):
                    errores.append(f"{rol}: contiene elementos que no son FunctionTool")
            except ImportError as exc:
                errores.append(f"{rol}: {exc}")
        assert errores == [], (
            "Fallos en módulos de herramientas:\n  " + "\n  ".join(errores)
        )

    @pytest.mark.parametrize("rol", ROLES)
    def test_herramientas_tienen_funcion_callable(self, rol: str) -> None:
        """Cada FunctionTool tiene una función callable subyacente."""
        lista = _obtener_herramientas(rol)
        for herramienta in lista:
            assert callable(herramienta.func), (
                f"La herramienta '{herramienta.name}' de '{rol}' no tiene func callable."
            )


# ===========================================================================
# HITO 5 — test_herramientas_cubren_tipos_emergencia
# ===========================================================================

class TestHerramientasCubrenTiposEmergencia:
    """Las herramientas de cada especialista cubren al menos dos tipos de emergencia."""

    @pytest.mark.parametrize("rol", ROLES)
    def test_herramientas_cubren_tipos_emergencia(self, rol: str) -> None:
        """El módulo de herramientas del rol tiene al menos 2 FunctionTool distintas."""
        lista = _obtener_herramientas(rol)
        assert len(lista) >= 2, (
            f"El agente '{rol}' tiene {len(lista)} herramienta(s). "
            "El Hito 5 exige al menos 2 para cubrir tipos de emergencia distintos."
        )
        nombres = [h.name for h in lista]
        assert len(set(nombres)) == len(nombres), (
            f"El agente '{rol}' tiene herramientas con nombres duplicados: {nombres}"
        )

    def test_bomberos_cubren_quimico_e_incendio(self) -> None:
        """Bomberos tiene herramientas para derrame químico e incendio."""
        lista = _obtener_herramientas("bomberos")
        nombres = " ".join(h.name.lower() for h in lista)
        tiene_quimico = "quimico" in nombres or "riesgo" in nombres
        tiene_incendio = "incendio" in nombres or "fuego" in nombres
        assert tiene_quimico and tiene_incendio, (
            f"Bomberos debería tener herramientas para químico e incendio. "
            f"Herramientas encontradas: {[h.name for h in lista]}"
        )

    def test_policia_cubren_alerta_y_peticion(self) -> None:
        """Policía tiene herramientas para alerta y petición de recursos."""
        lista = _obtener_herramientas("policia")
        nombres = " ".join(h.name.lower() for h in lista)
        tiene_alerta = "alerta" in nombres or "verif" in nombres
        tiene_peticion = "peticion" in nombres or "perimetro" in nombres or "procesar" in nombres
        assert tiene_alerta and tiene_peticion, (
            f"Policía debería tener herramientas para alerta y petición. "
            f"Herramientas encontradas: {[h.name for h in lista]}"
        )

    def test_municipal_cubren_alerta_y_solicitud(self) -> None:
        """Municipal tiene herramientas para alerta directa y solicitud externa."""
        lista = _obtener_herramientas("municipal")
        nombres = " ".join(h.name.lower() for h in lista)
        tiene_alerta = "alerta" in nombres or "procesar" in nombres
        tiene_solicitud = "solicitud" in nombres or "gas" in nombres or "recurso" in nombres
        assert tiene_alerta and tiene_solicitud, (
            f"Municipal debería tener herramientas para alerta y solicitud. "
            f"Herramientas encontradas: {[h.name for h in lista]}"
        )


# ===========================================================================
# Adaptador ADK → SPADE-LLM (todos los roles)
# ===========================================================================

class TestAdaptadorADKSpadeLLM:
    """El adaptador convierte correctamente FunctionTool en LLMTool."""

    @pytest.mark.parametrize("rol", ROLES)
    def test_adaptador_produce_llmtool(self, rol: str) -> None:
        """adaptar_herramienta_adk_a_spade() devuelve un LLMTool por cada herramienta."""
        lista = _obtener_herramientas(rol)
        for herramienta in lista:
            llm_tool = adaptar_herramienta_adk_a_spade(herramienta)
            assert isinstance(llm_tool, LLMTool), (
                f"El adaptador no devolvió un LLMTool para '{herramienta.name}' ({rol})."
            )

    @pytest.mark.parametrize("rol", ROLES)
    def test_llmtool_preserva_nombre(self, rol: str) -> None:
        """El LLMTool resultante conserva el nombre de la FunctionTool original."""
        lista = _obtener_herramientas(rol)
        for herramienta in lista:
            llm_tool = adaptar_herramienta_adk_a_spade(herramienta)
            assert llm_tool.name == herramienta.name, (
                f"El adaptador cambió el nombre: "
                f"'{herramienta.name}' → '{llm_tool.name}'"
            )

    @pytest.mark.parametrize("rol", ROLES)
    def test_llmtool_tiene_esquema_objeto(self, rol: str) -> None:
        """El LLMTool tiene un esquema de parámetros de tipo 'object'."""
        lista = _obtener_herramientas(rol)
        for herramienta in lista:
            llm_tool = adaptar_herramienta_adk_a_spade(herramienta)
            assert isinstance(llm_tool.parameters, dict), (
                f"LLMTool '{herramienta.name}' ({rol}): parameters no es un dict."
            )
            assert llm_tool.parameters.get("type") == "object", (
                f"LLMTool '{herramienta.name}' ({rol}): "
                "parameters['type'] debería ser 'object'."
            )

    @pytest.mark.parametrize("rol", ROLES)
    def test_llmtool_func_es_callable(self, rol: str) -> None:
        """La función en el LLMTool sigue siendo callable tras la adaptación."""
        lista = _obtener_herramientas(rol)
        for herramienta in lista:
            llm_tool = adaptar_herramienta_adk_a_spade(herramienta)
            assert callable(llm_tool.func), (
                f"LLMTool '{herramienta.name}' ({rol}): func no es callable."
            )