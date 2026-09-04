"""
Test de integracion del llm

Autor(es): Paula Torres Berrios (ptb00006)
Cristina Silva Ungo (csu00002)
"""


import asyncio
import importlib
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


import pytest
import yaml
from spade_llm import LLMAgent


from agentes.base_agente_llm import AgenteVillaOlivarLLM
from agentes.agente_municipal import AgenteMunicipal


from ontologia.modelos_compartidos import (
   ConsultaEstado,
   EstadoAgente,
   InformeResolucion,
   Prioridad,
   TipoEmergencia,
)




ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
CONFIG_PATH = ROOT / "config.yaml"


ROLES = ["centralita", "bomberos", "sanitario", "policia", "municipal"]


CLASES_AGENTES = {
   "centralita": ("agentes.agente_centralita", "AgenteCentralita"),
   "bomberos":   ("agentes.agente_bomberos",   "AgenteBomberos"),
   "sanitario":  ("agentes.agente_sanitario",  "AgenteSanitario"),
   "policia":    ("agentes.agente_policia",     "AgentePolicia"),
   "municipal":  ("agentes.agente_municipal",   "AgenteMunicipal"),
}








class TestHito1:


   def test_config_llm_existe(self) -> None:
       """config.yaml contiene la sección perfiles_llm con al menos el perfil local."""
       assert CONFIG_PATH.exists(), (
           f"No se encontró config.yaml en {CONFIG_PATH}."
       )
       with open(CONFIG_PATH, encoding="utf-8") as f:
           config = yaml.safe_load(f)


       assert "perfiles_llm" in config, (
           "config.yaml no contiene la clave 'perfiles_llm'."
       )
       assert "local" in config["perfiles_llm"], (
           "La sección 'perfiles_llm' no contiene el perfil 'local'."
       )
       perfil_local = config["perfiles_llm"]["local"]
       assert "modelo" in perfil_local, (
           "El perfil 'local' no tiene la clave 'modelo'."
       )
       modelo = perfil_local["modelo"]
       assert not modelo.startswith("ollama/"), (
           f"El campo 'modelo' no debe incluir el prefijo 'ollama/'. "
           f"Encontrado: '{modelo}'. LLMProvider.create_ollama() lo añade internamente."
       )


   def test_clase_base_hereda_llmagent(self) -> None:
       """AgenteVillaOlivarLLM es subclase de LLMAgent."""
       from agentes.base_agente_llm import AgenteVillaOlivarLLM
       assert issubclass(AgenteVillaOlivarLLM, LLMAgent), (
           "AgenteVillaOlivarLLM debe heredar de LLMAgent."
       )


   def test_prompt_centralita_existe(self) -> None:
       """El fichero prompts/centralita.txt existe y no está vacío."""
       ruta = PROMPTS_DIR / "centralita.txt"
       assert ruta.exists(), f"No se encontró {ruta}."
       contenido = ruta.read_text(encoding="utf-8").strip()
       assert len(contenido) > 0, "prompts/centralita.txt existe pero está vacío."


   def test_modelos_pydantic_importables(self) -> None:
       """Los modelos Pydantic de ontologia/modelos_compartidos.py son importables."""
       try:
           from ontologia.modelos_compartidos import (
               DatosEmergencia,
               RespuestaAgente,
               InformeResolucion,
               ConsultaEstado,
               EstadoAgente,
           )
       except ImportError as exc:
           pytest.fail(f"No se pudieron importar los modelos Pydantic: {exc}")


   def test_logica_sin_dependencias_spade_ni_llm(self) -> None:
       """Los módulos logica/ no importan spade, spade_llm, ollama ni litellm."""
       ruta_logica = ROOT / "logica"
       imports_prohibidos = ("import spade", "import spade_llm", "import ollama", "import litellm")
       violaciones: dict = {}
       for fichero in ruta_logica.glob("*.py"):
           if fichero.name == "__init__.py":
               continue
           contenido = fichero.read_text(encoding="utf-8")
           encontrados = [imp for imp in imports_prohibidos if imp in contenido]
           if encontrados:
               violaciones[fichero.name] = encontrados
       assert not violaciones, (
           f"Módulos de logica/ con imports prohibidos: {violaciones}"
       )






class TestHito2:




   def test_tres_agentes_arrancan_con_llm(self) -> None:
       """Al menos tres agentes son subclases de AgenteVillaOlivarLLM."""
       from agentes.base_agente_llm import AgenteVillaOlivarLLM


       agentes_migrados = []
       for rol, (modulo_nombre, clase_nombre) in CLASES_AGENTES.items():
           try:
               modulo = importlib.import_module(modulo_nombre)
               cls = getattr(modulo, clase_nombre)
               if issubclass(cls, AgenteVillaOlivarLLM):
                   agentes_migrados.append(rol)
           except (ImportError, AttributeError, TypeError):
               pass


       assert len(agentes_migrados) >= 3, (
           f"Solo {len(agentes_migrados)} agente(s) heredan de AgenteVillaOlivarLLM: "
           f"{agentes_migrados}. El Hito 2 requiere al menos 3."
       )


   def test_agente_usa_llm_para_clasificar(self) -> None:
       """Tras importar utils, LLMAgent tiene el método llm_chat inyectado."""
       try:
           import utils  # noqa: F401 — inyecta llm_chat() como efecto secundario
       except ImportError:
           pytest.skip("utils.py no disponible")


       assert hasattr(LLMAgent, "llm_chat"), (
           "llm_chat() no está disponible en LLMAgent. "
           "Verifica que utils.py inyecta el método correctamente."
       )
       assert inspect.iscoroutinefunction(LLMAgent.llm_chat), (
           "llm_chat() debe ser async."
       )


   def test_tres_modulos_herramientas_operativos(self) -> None:
       """Al menos tres módulos de herramientas exportan FunctionTool válidas."""
       from google.adk.tools import FunctionTool


       roles_tres = ["centralita", "bomberos", "sanitario"]
       errores = []
       for rol in roles_tres:
           mod_nombre, lista_nombre = (
               f"herramientas.herramientas_{rol}", f"herramientas_{rol}"
           )
           try:
               modulo = importlib.import_module(mod_nombre)
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






class TestHito3:




   @pytest.mark.parametrize("rol", ROLES)
   def test_prompt_existe_y_no_esta_vacio(self, rol: str) -> None:
       """Cada fichero prompts/{rol}.txt existe y tiene contenido."""
       ruta = PROMPTS_DIR / f"{rol}.txt"
       assert ruta.exists(), f"Falta prompts/{rol}.txt."
       assert len(ruta.read_text(encoding="utf-8").strip()) > 0, (
           f"prompts/{rol}.txt está vacío."
       )


   def test_cinco_prompts_existen(self) -> None:
       """Prueba de conjunto: los cinco prompts existen y no están vacíos."""
       faltantes = [r for r in ROLES if not (PROMPTS_DIR / f"{r}.txt").exists()]
       assert faltantes == [], f"Faltan los siguientes prompts: {faltantes}"


   @pytest.mark.parametrize("rol", ROLES)
   def test_prompt_contiene_rol_o_eres(self, rol: str) -> None:
       """El prompt de cada agente menciona su rol o la palabra 'eres'."""
       ruta = PROMPTS_DIR / f"{rol}.txt"
       if not ruta.exists():
           pytest.skip(f"Prompt '{ruta}' no existe todavía.")
       contenido = ruta.read_text(encoding="utf-8").lower()
       assert rol in contenido or "eres" in contenido, (
           f"El prompt de '{rol}' debería mencionar el rol del agente."
       )


   @pytest.mark.parametrize("rol", ROLES)
   def test_prompt_menciona_json(self, rol: str) -> None:
       """El prompt fuerza salida JSON (debe contener la palabra 'json')."""
       ruta = PROMPTS_DIR / f"{rol}.txt"
       if not ruta.exists():
           pytest.skip(f"Prompt '{ruta}' no existe todavía.")
       contenido = ruta.read_text(encoding="utf-8")
       assert "json" in contenido.lower(), (
           f"El prompt de '{rol}' debería incluir instrucciones de salida JSON."
       )


   @pytest.mark.parametrize("rol", ROLES)
   def test_agente_hereda_de_llmagent(self, rol: str) -> None:
       """Cada agente hereda (directa o indirectamente) de LLMAgent."""
       modulo_nombre, clase_nombre = CLASES_AGENTES[rol]
       try:
           modulo = importlib.import_module(modulo_nombre)
       except ImportError as exc:
           pytest.skip(f"No se pudo importar '{modulo_nombre}': {exc}")
       clase = getattr(modulo, clase_nombre)
       assert issubclass(clase, LLMAgent), (
           f"{clase_nombre} no hereda de LLMAgent."
       )


   @pytest.mark.parametrize("rol", ROLES)
   def test_agente_tiene_metodo_setup(self, rol: str) -> None:
       """Cada agente implementa setup() para registrar herramientas ADK."""
       modulo_nombre, clase_nombre = CLASES_AGENTES[rol]
       try:
           modulo = importlib.import_module(modulo_nombre)
       except ImportError as exc:
           pytest.skip(f"No se pudo importar '{modulo_nombre}': {exc}")
       clase = getattr(modulo, clase_nombre)
       assert hasattr(clase, "setup"), f"{clase_nombre} no tiene método setup()."


   @pytest.mark.parametrize("rol", ROLES)
   def test_agente_hereda_llm_chat(self, rol: str) -> None:
       """Cada agente especialista expone llm_chat() por herencia tras importar utils."""
       try:
           import utils  # noqa: F401
       except ImportError:
           pytest.skip("utils.py no disponible")
       modulo_nombre, clase_nombre = CLASES_AGENTES[rol]
       try:
           modulo = importlib.import_module(modulo_nombre)
       except ImportError as exc:
           pytest.skip(f"No se pudo importar '{modulo_nombre}': {exc}")
       clase = getattr(modulo, clase_nombre)
       assert hasattr(clase, "llm_chat"), (
           f"{clase_nombre} no tiene llm_chat(). "
           "Asegúrate de que utils.py se importa antes."
       )


   def test_cinco_modulos_herramientas(self) -> None:
       """Los cinco módulos de herramientas exportan al menos 2 FunctionTool."""
       from google.adk.tools import FunctionTool


       errores = []
       for rol in ROLES:
           mod_nombre = f"herramientas.herramientas_{rol}"
           lista_nombre = f"herramientas_{rol}"
           try:
               modulo = importlib.import_module(mod_nombre)
               lista = getattr(modulo, lista_nombre, [])
               if len(lista) < 2:
                   errores.append(f"{rol}: tiene {len(lista)} herramienta(s), se necesitan 2+")
               elif not all(isinstance(h, FunctionTool) for h in lista):
                   errores.append(f"{rol}: contiene elementos que no son FunctionTool")
           except ImportError as exc:
               errores.append(f"{rol}: {exc}")
       assert errores == [], (
           "Fallos en módulos de herramientas (Hito 3):\n  " + "\n  ".join(errores)
       )








class TestRespuestaLlmParseablePydantic:
   """La respuesta del LLM de la Centralita se puede parsear con InformeResolucion."""


   def _informe_ejemplo(self) -> str:
       informe = InformeResolucion(
           id_emergencia="INC-2026-001",
           tipo_emergencia=TipoEmergencia("derrame_quimico"),
           prioridad=Prioridad("alta"),
           estado_final="cerrado",
           resumen="Derrame de amoniaco resuelto.",
           agentes_participantes=["bomberos", "sanitario", "policia", "municipal"],
           acciones_realizadas=["Evaluación de riesgo", "Perímetro establecido"],
       )
       return informe.model_dump_json()


   def test_respuesta_llm_parseable_pydantic(self) -> None:
       """Un JSON bien formado se parsea correctamente con InformeResolucion."""
       json_str = self._informe_ejemplo()
       informe = InformeResolucion.model_validate_json(json_str)
       assert informe.id_emergencia == "INC-2026-001"
       assert informe.estado_final == "cerrado"


   def test_informe_resolucion_campos_obligatorios(self) -> None:
       """InformeResolucion exige id_emergencia, tipo_emergencia, prioridad y estado_final."""
       import json as _json
       datos = _json.loads(self._informe_ejemplo())
       for campo in ("id_emergencia", "tipo_emergencia", "prioridad", "estado_final"):
           datos_sin_campo = {k: v for k, v in datos.items() if k != campo}
           with pytest.raises(Exception):
               InformeResolucion.model_validate(datos_sin_campo)


   def test_informe_json_con_backticks_se_puede_limpiar(self) -> None:
       """El código de la Centralita puede limpiar backticks markdown de la respuesta del LLM."""
       json_str = self._informe_ejemplo()
       respuesta_llm = f"```json\n{json_str}\n```"
       limpio = (
           respuesta_llm.strip()
           .removeprefix("```json")
           .removeprefix("```")
           .removesuffix("```")
           .strip()
       )
       informe = InformeResolucion.model_validate_json(limpio)
       assert informe.estado_final == "cerrado"


   def test_json_invalido_no_parseable(self) -> None:
       """Un JSON malformado lanza excepción al parsearlo."""
       json_invalido = '{"id_emergencia": "INC-001", "incompleto": true'
       with pytest.raises(Exception):
           InformeResolucion.model_validate_json(json_invalido)


   def test_estado_agente_parseable(self) -> None:
       """EstadoAgente se construye y serializa correctamente."""
       estado = EstadoAgente(
           agente="bomberos_multi007s@localhost",
           estado="operativo",
           emergencia_actual=None,
           detalle="Sin emergencia activa",
       )
       recuperado = EstadoAgente.model_validate_json(estado.model_dump_json())
       assert recuperado.estado == "operativo"


   def test_consulta_estado_parseable(self) -> None:
       """ConsultaEstado se puede validar desde JSON."""
       consulta = ConsultaEstado(


           agente_destino="bomberos@localhost",
           marca_temporal=datetime.now(timezone.utc),
       )
       recuperado = ConsultaEstado.model_validate_json(consulta.model_dump_json())
       assert recuperado.agente_destino == "bomberos@localhost"


   @pytest.mark.asyncio
   async def test_llm_chat_seguro_devuelve_none_en_timeout(self) -> None:
       """_llm_chat_seguro() devuelve None si llm_chat supera el timeout."""
       from agentes.agente_centralita import AgenteCentralita


       with patch("agentes.base_agente_llm.AgenteVillaOlivarLLM._cargar_prompt",
                  return_value="prompt de prueba"), \
            patch("agentes.base_agente_llm.AgenteVillaOlivarLLM._crear_proveedor",
                  return_value=MagicMock()):
           try:
               centralita = AgenteCentralita(
                   jid="centralita_test@localhost", password="pass"
               )
           except Exception:
               pytest.skip("No se pudo instanciar AgenteCentralita en modo offline.")


       async def llm_colgado(_consulta: str) -> str:
           await asyncio.sleep(9999)
           return ""


       centralita.llm_chat = llm_colgado
       resultado = await centralita._llm_chat_seguro("consulta", timeout=1)
       assert resultado is None, (
           "_llm_chat_seguro() debería devolver None cuando llm_chat supera el timeout."
       )


   @pytest.mark.asyncio
   async def test_llm_chat_seguro_devuelve_none_en_excepcion(self) -> None:
       """_llm_chat_seguro() devuelve None si llm_chat lanza una excepción."""
       from agentes.agente_centralita import AgenteCentralita


       with patch("agentes.base_agente_llm.AgenteVillaOlivarLLM._cargar_prompt",
                  return_value="prompt de prueba"), \
            patch("agentes.base_agente_llm.AgenteVillaOlivarLLM._crear_proveedor",
                  return_value=MagicMock()):
           try:
               centralita = AgenteCentralita(
                   jid="centralita_test@localhost", password="pass"
               )
           except Exception:
               pytest.skip("No se pudo instanciar AgenteCentralita en modo offline.")


       async def llm_falla(_consulta: str) -> str:
           raise RuntimeError("Error simulado del LLM")


       centralita.llm_chat = llm_falla
       resultado = await centralita._llm_chat_seguro("consulta", timeout=5)
       assert resultado is None








class TestBehavioursNoBloquantes:
   """Un agente puede recibir y procesar mensajes mientras el LLM responde."""


   def test_llm_chat_es_coroutine(self) -> None:
       """llm_chat() es async, no bloquea el event loop de SPADE."""
       try:
           import utils  # noqa: F401
       except ImportError:
           pytest.skip("utils.py no disponible")
       assert hasattr(LLMAgent, "llm_chat"), "llm_chat() no está en LLMAgent."
       assert inspect.iscoroutinefunction(LLMAgent.llm_chat), (
           "llm_chat() debe ser async."
       )


   def test_llm_chat_seguro_es_coroutine(self) -> None:
       """_llm_chat_seguro() de la Centralita es async."""
       from agentes.agente_centralita import AgenteCentralita
       assert inspect.iscoroutinefunction(AgenteCentralita._llm_chat_seguro), (
           "_llm_chat_seguro() debe ser async."
       )


   @pytest.mark.asyncio
   async def test_dos_llamadas_llm_no_se_bloquean_mutuamente(self) -> None:
       """Dos llamadas concurrentes a llm_chat() simulado se completan en paralelo."""
       async def llm_simulado(retardo: float, respuesta: str) -> str:
           await asyncio.sleep(retardo)
           return respuesta


       res1, res2 = await asyncio.gather(
           asyncio.create_task(llm_simulado(0.05, "respuesta_1")),
           asyncio.create_task(llm_simulado(0.05, "respuesta_2")),
       )
       assert res1 == "respuesta_1"
       assert res2 == "respuesta_2"


   def test_behaviours_centralita_usan_await(self) -> None:
       """El código fuente de AgenteCentralita contiene await y llm_chat."""
       ruta = ROOT / "agentes" / "agente_centralita.py"
       if not ruta.exists():
           pytest.skip("agentes/agente_centralita.py no encontrado.")
       fuente = ruta.read_text(encoding="utf-8")
       assert "await" in fuente and "llm_chat" in fuente, (
           "AgenteCentralita debería usar 'await ... llm_chat()' en sus behaviours."
       )


   @pytest.mark.parametrize("rol", ["bomberos", "sanitario", "policia", "municipal"])
   def test_agentes_especialistas_usan_await_llm_chat(self, rol: str) -> None:
       """Los agentes especialistas usan await y llm_chat() en sus behaviours."""
       ruta = ROOT / "agentes" / f"agente_{rol}.py"
       if not ruta.exists():
           pytest.skip(f"agentes/agente_{rol}.py no encontrado.")
       fuente = ruta.read_text(encoding="utf-8")
       assert "llm_chat" in fuente, f"agente_{rol}.py debería usar llm_chat()."
       assert "await" in fuente, f"agente_{rol}.py debería usar 'await'."


   def test_run_behaviours_son_async(self) -> None:
       """Los métodos run() de los behaviours de la Centralita son coroutines."""
       try:
           from agentes.agente_centralita import AgenteCentralita
       except ImportError as exc:
           pytest.skip(f"No se pudo importar AgenteCentralita: {exc}")


       for behaviour_nombre in ("EscucharSupervisor", "EscucharInformes"):
           behaviour_cls = getattr(AgenteCentralita, behaviour_nombre, None)
           if behaviour_cls is None:
               continue
           assert inspect.iscoroutinefunction(behaviour_cls.run), (
               f"AgenteCentralita.{behaviour_nombre}.run() debe ser async."
           )


   def test_clase_base_setup_es_async(self) -> None:
       """AgenteVillaOlivarLLM.setup() es async (requerido por SPADE)."""
       from agentes.base_agente_llm import AgenteVillaOlivarLLM
       assert inspect.iscoroutinefunction(AgenteVillaOlivarLLM.setup), (
           "AgenteVillaOlivarLLM.setup() debe ser async."
       )


   def test_responder_supervisor_behaviour_run_es_async(self) -> None:
       """ResponderSupervisorBehaviour.run() es async."""
       from agentes.base_agente_llm import ResponderSupervisorBehaviour
       assert inspect.iscoroutinefunction(ResponderSupervisorBehaviour.run), (
           "ResponderSupervisorBehaviour.run() debe ser async."
       )


   @pytest.mark.asyncio
   async def test_tolerancia_llm_timeout(self):
       """Verifica que el agente gestiona un timeout del LLM """
       with patch("spade_llm.LLMProvider.get_llm_response", new_callable=AsyncMock) as mock_get:
           mock_get.side_effect = asyncio.TimeoutError


           config_local = {"proveedor": "ollama", "modelo": "llama3.2:3b"}
           agente = AgenteVillaOlivarLLM("test@localhost", "password", rol="municipal", config_llm=config_local)


           with pytest.raises(asyncio.TimeoutError):
               await agente.ask_llm("Hola")




   def test_tolerancia_json_invalido(self):
       """Verifica la gestión de respuestas basura del LLM """
       respuesta_corrupta = '{"id": "INC-001", "estado_final": "cerrado", "resumen": ...'  # JSON incompleto


       from pydantic import ValidationError
       with pytest.raises(ValidationError):
           InformeResolucion.model_validate_json(respuesta_corrupta)


   def test_typing_hints_presentes(self):
       """Verifica que se usan Type Hints en métodos clave (Requisito 6.6)."""


       sig = inspect.signature(AgenteVillaOlivarLLM.__init__)
       assert sig.parameters['config_llm'].annotation != inspect._empty, "Falta el tipo en config_llm"


       sig_setup = inspect.signature(AgenteMunicipal.setup)
       assert sig_setup.return_annotation is not inspect._empty, "Falta el tipo de retorno en setup()"


   def test_docstrings_completos(self):
       """Verifica que todas las clases tienen documentación descriptiva."""
       assert AgenteVillaOlivarLLM.__doc__ is not None, "Falta docstring en AgenteVillaOlivarLLM"
       assert len(AgenteVillaOlivarLLM.__doc__) > 20, "El docstring es demasiado corto"
       assert AgenteMunicipal.__doc__ is not None, "Falta docstring en AgenteMunicipal"


   def test_ausencia_hardcoding_total(self):
       """Verifica que no hay URLs ni puertos fijos en NINGÚN agente."""
       import os
       ruta_agentes = "agentes/"
       prohibidos = ["11434", "localhost:5222", "http://localhost"]


       archivos = [f for f in os.listdir(ruta_agentes) if f.endswith(".py")]


       for nombre_fichero in archivos:
           ruta_completa = os.path.join(ruta_agentes, nombre_fichero)
           with open(ruta_completa, 'r', encoding='utf-8') as f:
               contenido = f.read()
               for cadena in prohibidos:


                   assert f'"{cadena}"' not in contenido, f"Hardcoding detectado en {nombre_fichero}: {cadena}"
                   assert f"'{cadena}'" not in contenido, f"Hardcoding detectado en {nombre_fichero}: {cadena}"


   @pytest.mark.asyncio
   async def test_robustez_timeout_infraestructura(self):
       """Verifica que la infraestructura base gestiona timeouts de Ollama."""
       from unittest.mock import AsyncMock, patch
       import asyncio


       with patch("spade_llm.LLMProvider.get_llm_response", new_callable=AsyncMock) as mock_get:
           mock_get.side_effect = asyncio.TimeoutError


           config_local = {"proveedor": "ollama", "modelo": "llama3.2:3b"}
           agente = AgenteVillaOlivarLLM("base@localhost", "pass", rol="municipal", config_llm=config_local)


           with pytest.raises(asyncio.TimeoutError):
               await agente.ask_llm("test")


   def test_validacion_pydantic_informe_cierre(self):
       """Verifica que el InformeResolucion final cumple estrictamente la ontología."""
       from ontologia.modelos_compartidos import InformeResolucion
       from datetime import datetime


       datos = {
           "id_emergencia": "INC-2026-999",
           "tipo_emergencia": "incendio",
           "prioridad": "alta",
           "estado_final": "resuelto",
           "resumen": "Intervención finalizada con éxito",
           "agentes_participantes": ["bomberos@localhost", "policia@localhost"],
           "acciones_realizadas": ["extinción", "perímetro"],
           "marca_temporal": datetime.now()
       }


       informe = InformeResolucion(**datos)
       assert informe.id_emergencia == "INC-2026-999"
       assert "extinción" in informe.acciones_realizadas