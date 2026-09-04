"""
Clase base LLM para los agentes del sistema de emergencias — Villa Olivar (Nivel 2).



Autor(es): Cristina Silva (csu0002@ujaen.es)
           Paula Torres (ptb0006@uajen.es)
Grupo: multi007s
"""


import logging
from pathlib import Path
from typing import Optional


import yaml
from google.adk.tools import FunctionTool
from spade.behaviour import CyclicBehaviour
from spade.template import Template
from spade_llm import LLMAgent, LLMProvider
from spade_llm.tools.llm_tool import LLMTool


from ontologia.modelos_compartidos import ConsultaEstado, EstadoAgente


logger = logging.getLogger(__name__)




ONTOLOGIA_SUPERVISOR = "emergencias-villaolivar"


def _tipo_adk_a_json(tipo_adk) -> str:
   """Convierte el tipo de parámetro ADK al string de JSON Schema.
   """

   if isinstance(tipo_adk, str):
       return tipo_adk.lower()

   nombre = getattr(tipo_adk, "name", str(tipo_adk)).upper()
   mapa = {
       "STRING":  "string",
       "NUMBER":  "number",
       "INTEGER": "integer",
       "BOOLEAN": "boolean",
       "ARRAY":   "array",
       "OBJECT":  "object",
   }

   return mapa.get(nombre, "string")




def adaptar_herramienta_adk_a_spade(herramienta_adk: FunctionTool) -> LLMTool:
   """Convierte una FunctionTool de ADK en un LLMTool de SPADE-LLM.

   """
   nombre = herramienta_adk.name
   descripcion = herramienta_adk.description or f"Herramienta {nombre}"
   funcion_original = herramienta_adk.func

   esquema_raw = getattr(herramienta_adk, "parameters", None)


   if esquema_raw is None:

       esquema_json = {"type": "object", "properties": {}}


   elif isinstance(esquema_raw, dict):

       esquema_json = esquema_raw
   else:

       try:
           propiedades_raw = getattr(esquema_raw, "properties", {}) or {}
           propiedades = {}
           for campo, info in propiedades_raw.items():
               tipo_str = _tipo_adk_a_json(getattr(info, "type", "string"))
               desc = getattr(info, "description", "")
               propiedades[campo] = {"type": tipo_str, "description": desc}


           requeridos = list(getattr(esquema_raw, "required", []) or [])
           esquema_json = {"type": "object", "properties": propiedades}
           if requeridos:
               esquema_json["required"] = requeridos


       except Exception as exc:
           logger.warning(
               "No se pudo convertir el esquema de '%s': %s. Usando esquema vacío.",
               nombre, exc,
           )
           esquema_json = {"type": "object", "properties": {}}


   return LLMTool(
       name=nombre,
       description=descripcion,
       parameters=esquema_json,
       func=funcion_original,
   )






class ResponderSupervisorBehaviour(CyclicBehaviour):
   """Behaviour cíclico que responde al protocolo FIPA-Query del supervisor.
   """
   async def run(self) -> None:
       mensaje = await self.receive(timeout=10)
       if mensaje is None:
           return

       try:
           ConsultaEstado.model_validate_json(mensaje.body)
       except Exception as exc:
           logger.warning(
               "[%s] ConsultaEstado no parseable: %s. Respondiendo de todas formas.",
               getattr(self.agent, "rol", "agente"), exc,
           )


       estado_str = getattr(self.agent, "estadoEmergencia", "operativo")
       emergencia_actual = getattr(self.agent, "id_emergencia_activa", None) or None


       estado = EstadoAgente(
           agente=str(self.agent.jid),
           estado=estado_str,
           emergencia_actual=emergencia_actual,
           detalle=(
               f"Gestionando {emergencia_actual}"
               if emergencia_actual
               else "Sin emergencia activa"
           ),
       )
       respuesta = mensaje.make_reply()
       respuesta.set_metadata("performative", "inform")
       respuesta.set_metadata("ontology", ONTOLOGIA_SUPERVISOR)
       respuesta.set_metadata("protocol", "fipa-query")
       respuesta.set_metadata("language", "application/json")
       conv_id = mensaje.get_metadata("conversation-id")
       if conv_id:
           respuesta.set_metadata("conversation-id", conv_id)
       if mensaje.id:
           respuesta.set_metadata("in_reply_to", str(mensaje.id))


       respuesta.body = estado.model_dump_json()
       await self.send(respuesta)


       logger.info(
           "[%s] EstadoAgente enviado: %s",
           getattr(self.agent, "rol", "agente"), estado_str,
       )


class AgenteVillaOlivarLLM(LLMAgent):
   """Clase base para todos los agentes LLM del sistema Villa Olivar.
   """
   def __init__(
       self,
       jid: str,
       password: str,
       rol: str,
       config_path: str = "config.yaml",
       config_llm: Optional[dict] = None,
       *args,
       **kwargs,
   ) -> None:

       self.rol = rol
       self.config = self._cargar_config(config_path)
       cfg = config_llm if config_llm is not None else self.config.get("perfiles_llm", {}).get(self.config.get("perfil_llm_activo", "local"), {})

       prompt_sistema = self._cargar_prompt(rol)
       proveedor = self._crear_proveedor(cfg)

       self.estadoEmergencia: str = "operativo"
       self.id_emergencia_activa: str = ""
       super().__init__(
           jid=jid,
           password=password,
           provider=proveedor,
           system_prompt=prompt_sistema,
           *args,
           **kwargs,
       )

   @staticmethod
   def _cargar_config(config_path: str) -> dict:
       """Lee el fichero de configuración completo."""
       try:
           with open(config_path, "r", encoding="utf-8") as f:
               return yaml.safe_load(f)
       except Exception as exc:
           logger.warning("No se pudo leer config (%s). Usando vacía.", exc)
           return {}

   @staticmethod
   def _cargar_config_llm(config_path: str) -> dict:
       """Lee el perfil LLM activo de config.yaml."""
       config = AgenteVillaOlivarLLM._cargar_config(config_path)
       perfil_activo = config.get("perfil_llm_activo", "local")
       return config.get("perfiles_llm", {}).get(perfil_activo, {})


   @staticmethod
   def _cargar_prompt(rol: str) -> str:
       """Lee prompts/{rol}.txt.
       """
       ruta = Path(f"prompts/{rol}.txt")
       if not ruta.exists():
           raise FileNotFoundError(
               f"[AgenteVillaOlivarLLM] No se encontró el prompt para '{rol}' "
               f"en '{ruta}'. Crea el fichero antes de arrancar el agente."
           )
       return ruta.read_text(encoding="utf-8")


   @staticmethod
   def _crear_proveedor(config_llm: dict) -> LLMProvider:
       """Crea el LLMProvider según la configuración.


       """
       proveedor_tipo = config_llm.get("proveedor", "ollama")
       modelo = config_llm.get("modelo", "llama3.2:3b")


       if proveedor_tipo == "gemini":
           import os
           api_key_env = config_llm.get("api_key_env", "GOOGLE_API_KEY")
           api_key = os.environ.get(api_key_env, "")
           if not api_key:
               logger.warning(
                   "Variable %s no definida. Gemini fallará sin API key.", api_key_env
               )
           return LLMProvider.create_openai(
               model=f"gemini/{modelo}",
               api_key=api_key,
               base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
           )
       else:

           return LLMProvider.create_ollama(model=modelo)


   def registrar_herramientas_adk(self, herramientas: list) -> None:
       """Convierte y registra FunctionTools de ADK en el agente.
       """
       llm_tools = [adaptar_herramienta_adk_a_spade(h) for h in herramientas]

       if not hasattr(self, "tools") or self.tools is None:
           self.tools = []


       self.tools.extend(llm_tools)
       logger.info(
           "[%s] %d herramienta(s) registrada(s): %s",
           self.rol, len(llm_tools), [t.name for t in llm_tools],
       )




   async def ask_llm(self, consulta: str) -> str:
       """Envía una consulta al LLM y devuelve la respuesta como string.
       """
       return await self.llm_chat(consulta)


   async def setup(self) -> None:
       """Registra el behaviour de consulta de estado del supervisor.
       """
       tmpl_query = Template()
       tmpl_query.set_metadata("performative", "query-ref")
       tmpl_query.set_metadata("ontology", ONTOLOGIA_SUPERVISOR)


       self.add_behaviour(ResponderSupervisorBehaviour(), tmpl_query)
       logger.info("[%s] Behaviour de consulta de estado registrado.", self.rol)


