"""
Agente Policía - Villa Olivar (Nivel 3 - A2A).

Autor(es): Francisco Javier González Rodríguez (fjgr0029@red.ujaen.es)
Grupo: multi007s
"""

import json
import logging
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from aiohttp import web
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from pydantic import ValidationError

from agentes.base_agente_a2a import (
    BaseAgenteA2A, 
    EspecificacionAgente, 
    VERSION_JSONRPC,
    TIPO_PARTE_DATOS,
    HTTP_ERROR_SERVIDOR,
    CODIGO_ERROR_SERVIDOR
)
from factoria import AgenteA2A
from contrato.alerta_emergencia import AlertaEmergencia
from contrato.agent_card import AgentCard, Habilidad
from contrato.informe_resolucion import InformeResolucion
from contrato.informe_actuacion import InformeActuacion
from contrato.tipos import RolEspecialista, EstadoFinal, TipoEmergencia, Prioridad, EstadoTask
from contrato.traza import EventoTraza, RolAgente, VisibilidadAgente
from herramientas.herramientas_policia import herramientas_policia
from logica.logica_policia import (
    procesarAlertaAceptada,
    texto_es_suficiente,
    generar_propuesta,
)
from logica.logica_general import printColor

logger = logging.getLogger(__name__)

_LLM_TIMEOUT_SEGUNDOS = 5

class AgentePolicia(AgenteA2A):
    """Agente Policía A2A con razonamiento LLM y soporte para Contract Net."""

    def __init__(self, especificacion: EspecificacionAgente) -> None:
        super().__init__(especificacion)

        self.estado_actual = "libre"
        
        # Historial de Tasks para responder a tasks/get (Hito 4)
        self._historial_tasks: dict[str, dict[str, Any]] = {}
        
        # Alertas en estado input-required para ser reanudadas (Hito 4)
        self._tasks_input_required: dict[str, dict[str, Any]] = {}

        # Inicializamos el razonador LLM ADK
        nombre_llm = f"{self.especificacion.identificador}_llm".replace("-", "_")

        self._llm_agent = LlmAgent(
            name=nombre_llm,
            instruction=self._leer_prompt(),
            tools=herramientas_policia,
            model=self._configurar_modelo(),
        )
        self._session_service = InMemorySessionService()

    def _configurar_modelo(self) -> str:
        """Obtiene el modelo LLM desde la especificación."""
        perfil_llm = self.especificacion.parametros.get("llm", {})
        modelo = perfil_llm.get("modelo", "gemini-1.5-flash-lite")
        proveedor = perfil_llm.get("proveedor", "gemini")
        if proveedor == "gemini" and not modelo.startswith("gemini/"):
            return f"gemini/{modelo}"
        return modelo

    def _leer_prompt(self) -> str:
        """Lee el prompt del agente Policía."""
        try:
            with open("prompts/policia.txt", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "Eres el agente Policía de Villa Olivar. Gestiona perímetros y tráfico."

    def construir_agent_card(self) -> AgentCard:
        """Publica la Agent Card de Policía."""
        habilidades = [
            Habilidad(
                id="establecer_perimetro",
                name="Establecimiento de perímetro",
                description=(
                    "Define y establece un perímetro de seguridad alrededor de la "
                    "zona de emergencia, con puntos de control de acceso."
                ),
                tags=["seguridad", "perimetro", "control", "acceso"],
            ),
            Habilidad(
                id="gestionar_trafico",
                name="Gestión de tráfico",
                description=(
                    "Planifica desvíos de tráfico, rutas alternativas y carriles de "
                    "emergencia para facilitar el acceso de vehículos de emergencia."
                ),
                tags=["trafico", "desvio", "ruta", "emergencia"],
            ),
            Habilidad(
                id="coordinar_evacuacion_civil",
                name="Evacuación civil",
                description=(
                    "Coordina la evacuación de civiles de la zona afectada: puntos "
                    "de reunión, rutas de evacuación y recuento de personas."
                ),
                tags=["evacuacion", "civiles", "reunion", "seguridad"],
            ),
        ]

        return AgentCard(
            name=self.especificacion.identificador,
            description=(
                "Agente especialista en seguridad pública: establecimiento de "
                "perímetros, control de accesos, gestión de tráfico y protección de la zona de emergencia."
            ),
            url=self._url_publica(),
            version="1.0.0",
            skills=habilidades,
        )

    async def _procesar_tasks_send(self, parametros: dict[str, Any], id_jsonrpc: Any) -> web.Response:
        """Override para gestionar el ciclo de vida, historial, input-required y Contract Net."""
        id_task = parametros.get("id") or str(uuid.uuid4())
        datos = self._extraer_datos_alerta(parametros)
        
        # Reanudación de task en input-required
        if id_task in self._tasks_input_required:
            datos_viejos = self._tasks_input_required.pop(id_task)
            datos = {**datos_viejos, **{k: v for k, v in datos.items() if v}}
            parametros["message"]["parts"][0]["data"] = datos
            logger.info("[POLICIA] Reanudando Task %s desde input-required", id_task)

        # Registro inicial en historial
        ahora = datetime.now(timezone.utc).isoformat()
        self._historial_tasks[id_task] = {
            "id": id_task,
            "status": {"state": EstadoTask.SUBMITTED.value, "timestamp": ahora},
            "history": [{"state": EstadoTask.SUBMITTED.value, "timestamp": ahora}],
        }

        # Transición a WORKING
        ahora_w = datetime.now(timezone.utc).isoformat()
        self._historial_tasks[id_task]["status"] = {"state": EstadoTask.WORKING.value, "timestamp": ahora_w}
        self._historial_tasks[id_task]["history"].append({"state": EstadoTask.WORKING.value, "timestamp": ahora_w})

        tipo_msg = datos.get("type", "alerta")
        
        if tipo_msg == "cfp":
            # Hito 4: Responder a convocatoria de propuesta
            propuesta = generar_propuesta(datos)
            cuerpo = self._cuerpo_jsonrpc_completed_custom(id_jsonrpc, id_task, propuesta)
            self._finalizar_task_historial(id_task, cuerpo["result"])
            return web.json_response(cuerpo)
        
        if tipo_msg == "reject":
            # Hito 4: Notificación de rechazo de propuesta
            cuerpo = self._cuerpo_jsonrpc_completed_custom(id_jsonrpc, id_task, {"mensaje": "Rechazo de propuesta recibido"})
            self._finalizar_task_historial(id_task, cuerpo["result"])
            return web.json_response(cuerpo)

        # Alerta normal o asignación ('assign')
        try:
            alerta = AlertaEmergencia.model_validate(datos)
        except ValidationError as exc:
            cuerpo = self._cuerpo_jsonrpc_failed(id_jsonrpc, id_task, str(exc))
        else:
            try:
                # Comprobación de input-required (Hito 4)
                if not texto_es_suficiente(alerta.texto):
                    raise ValueError("input-required:Descripción demasiado breve para actuar.")

                informe = await self.manejar_alerta(alerta)
                cuerpo = self._cuerpo_jsonrpc_completed(id_jsonrpc, id_task, informe)
            except ValueError as exc:
                msg_exc = str(exc)
                if msg_exc.startswith("input-required:"):
                    motivo = msg_exc.replace("input-required:", "")
                    cuerpo = self._cuerpo_jsonrpc_input_required_custom(id_jsonrpc, id_task, motivo)
                    self._tasks_input_required[id_task] = datos
                else:
                    cuerpo = self._cuerpo_jsonrpc_failed(id_jsonrpc, id_task, msg_exc)
            except Exception as exc:
                cuerpo = self._cuerpo_jsonrpc_failed(id_jsonrpc, id_task, str(exc))

        self._finalizar_task_historial(id_task, cuerpo.get("result", {}))
        return web.json_response(cuerpo)

    async def _procesar_tasks_get(self, parametros: dict[str, Any], id_jsonrpc: Any) -> web.Response:
        """Override para devolver el historial de la Task (Hito 4)."""
        id_task = parametros.get("id")
        if id_task in self._historial_tasks:
            return web.json_response({
                "jsonrpc": VERSION_JSONRPC,
                "id": id_jsonrpc,
                "result": self._historial_tasks[id_task]
            })
        return self._respuesta_error(id_jsonrpc, CODIGO_ERROR_SERVIDOR, f"Task {id_task} no encontrada", HTTP_ERROR_SERVIDOR)

    def _finalizar_task_historial(self, id_task: str, result: dict) -> None:
        """Actualiza el historial con el resultado final."""
        if id_task in self._historial_tasks:
            self._historial_tasks[id_task].update(result)
            ahora = datetime.now(timezone.utc).isoformat()
            self._historial_tasks[id_task]["status"]["timestamp"] = ahora
            # Aseguramos que el historial refleje la última transición
            estado = result.get("status", {}).get("state")
            if estado:
                self._historial_tasks[id_task]["history"].append({"state": estado, "timestamp": ahora})

    def _cuerpo_jsonrpc_completed_custom(self, id_jsonrpc: Any, id_task: str, data: dict) -> dict:
        """Versión personalizada de completed para datos que no son InformeResolucion."""
        return {
            "jsonrpc": VERSION_JSONRPC,
            "id": id_jsonrpc,
            "result": {
                "id": id_task,
                "status": {"state": EstadoTask.COMPLETED.value},
                "artifacts": [{"parts": [{"type": TIPO_PARTE_DATOS, "data": data}]}]
            }
        }

    def _cuerpo_jsonrpc_input_required_custom(self, id_jsonrpc: Any, id_task: str, motivo: str) -> dict:
        """Cuerpo para el estado input-required."""
        return {
            "jsonrpc": VERSION_JSONRPC,
            "id": id_jsonrpc,
            "result": {
                "id": id_task,
                "status": {"state": EstadoTask.INPUT_REQUIRED.value, "message": motivo}
            }
        }

    async def manejar_alerta(self, alerta: AlertaEmergencia) -> InformeResolucion:
        """Procesa una alerta y devuelve el informe de resolución."""
        printColor(f"[POLICIA] Procesando alerta: {alerta.id_emergencia}", "azul")
        self.estado_actual = "ocupado"

        traza = [
            self._crear_evento_traza(
                accion="recibir_alerta",
                detalle=f"Policía recibe subtarea: {alerta.texto[:80]}",
            )
        ]

        consulta = (
            f"ID emergencia: {alerta.id_emergencia}\n"
            f"Texto: {alerta.texto}\n"
            f"Ubicación: {alerta.ubicacion.direccion if alerta.ubicacion else 'desconocida'}\n\n"
            "Evalúa la situación como Policía. Usa herramientas si es necesario. "
            "Devuelve SOLO JSON con: acciones_realizadas, recursos_empleados, observaciones, completado."
        )

        try:
            respuesta_llm = await asyncio.wait_for(
                self._invocar_adk(consulta),
                timeout=_LLM_TIMEOUT_SEGUNDOS,
            )
            datos_informe = self._parsear_respuesta_llm(respuesta_llm)
        except Exception as exc:
            logger.warning("[POLICIA] Fallo LLM: %s. Usando fallback.", exc)
            datos_informe = procesarAlertaAceptada(json.loads(alerta.model_dump_json()), self)

        informe_actuacion = InformeActuacion(
            rol=RolEspecialista.POLICIA,
            completado=datos_informe.get("completado", True),
            acciones_realizadas=datos_informe.get("acciones_realizadas", ["Perímetro asegurado."]),
            recursos_empleados=datos_informe.get("recursos_empleados", ["Patrulla de policía"]),
            observaciones=datos_informe.get("observaciones", "Intervención policial completada.")
        )

        traza.append(
            self._crear_evento_traza(
                accion="emitir_informe",
                detalle="Policía emite informe de actuación.",
            )
        )

        self.estado_actual = "libre"
        printColor(f"[POLICIA] Alerta {alerta.id_emergencia} resuelta.", "azul")

        return InformeResolucion(
            id_emergencia=alerta.id_emergencia,
            tipo_emergencia=TipoEmergencia.OTRO,
            prioridad=Prioridad.MEDIA,
            ubicacion=alerta.ubicacion,
            informes_especialistas=[informe_actuacion],
            estado_final=EstadoFinal.RESUELTA,
            resumen="La policía ha establecido un perímetro de seguridad.",
            traza_participacion=traza
        )

    def _crear_evento_traza(self, accion: str, detalle: str) -> EventoTraza:
        visibilidad = (
            VisibilidadAgente.PUBLICO
            if self.especificacion.visibilidad == "publico"
            else VisibilidadAgente.PRIVADO
        )
        return EventoTraza(
            instante=datetime.now(timezone.utc),
            agente_id=self.especificacion.identificador,
            rol=RolAgente.POLICIA,
            visibilidad=visibilidad,
            accion=accion,
            detalle=detalle,
        )

    async def _invocar_adk(self, consulta: str) -> str:
        import uuid
        session_id = f"policia_{uuid.uuid4().hex}"
        app_name = "policia_villa_olivar"
        
        await self._session_service.create_session(
            app_name=app_name,
            user_id="centralita",
            session_id=session_id,
        )

        runner = Runner(
            agent=self._llm_agent,
            app_name=app_name,
            session_service=self._session_service,
        )

        contenido = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=consulta)],
        )

        texto_respuesta = ""
        async for evento in runner.run_async(
            user_id="centralita",
            session_id=session_id,
            new_message=contenido,
        ):
            if evento.is_final_response() and evento.content and evento.content.parts:
                texto_respuesta = evento.content.parts[0].text or ""
                break
        return texto_respuesta

    def _parsear_respuesta_llm(self, respuesta: str) -> dict:
        limpio = (
            respuesta.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        return json.loads(limpio)
