"""
Agente municipal — Villa Olivar (Nivel 3 - Hito 4)
Autor: Paula Torres Berrios
Grupo: multi007s
"""
import logging
import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

from agentes.base_agente_a2a import BaseAgenteA2A, EspecificacionAgente
from factoria import AgenteA2A
from contrato.agent_card import AgentCard, Habilidad
from contrato.informe_actuacion import InformeActuacion
from contrato.traza import EventoTraza, RolAgente, VisibilidadAgente
from logica.logica_municipal import (
    generar_propuestas_municipal,
    evaluar_resultado_ejecucion,
    procesar_alerta_municipal
)
from contrato.alerta_emergencia import AlertaEmergencia
from contrato.informe_resolucion import InformeResolucion
from contrato.tipos import (
    RolEspecialista,
    EstadoTask,
    EstadoFinal,
    TipoEmergencia,
    Prioridad,
)
from descubrimiento.cliente_registro import ClienteRegistro
logger = logging.getLogger(__name__)

class AgenteMunicipal(AgenteA2A):
    """Agente Municipal de Villa Olivar. Gestiona recursos y licitaciones Contract Net."""

    def __init__(self, especificacion: EspecificacionAgente):
        super().__init__(especificacion)
        self.tasks_memoria: dict[str, dict[str, Any]] = {}
        self.estado_actual = "libre"
        self.id_emergencia_activa = None
        self.detalle_estado = "Agente Municipal disponible."

        self._cliente_registro: ClienteRegistro | None = None
        self._registrado_en_rest = False
        self._tarea_reintento_registro: asyncio.Task | None = None

    def _inicializar_task_memoria(self, task_id: str, payload: dict):
        """Registra una nueva Task en memoria rastreando su ciclo de vida e historial."""
        ahora = datetime.now(timezone.utc).isoformat()
        self.tasks_memoria[task_id] = {
            "id": task_id,
            "estado": EstadoTask.SUBMITTED,
            "payload_inicial": payload,
            "historial_transiciones": [
                {"estado": EstadoTask.SUBMITTED, "timestamp": ahora}
            ],
            "propuestas_enviadas": [],
            "propuesta_ganadora": None,
            "resultado_final": None
        }

    def _cambiar_estado_task(self, task_id: str, nuevo_estado: EstadoTask):
        """Transiciona de estado una Task y añade la marca de tiempo al historial."""
        if task_id in self.tasks_memoria:
            ahora = datetime.now(timezone.utc).isoformat()
            self.tasks_memoria[task_id]["estado"] = nuevo_estado
            self.tasks_memoria[task_id]["historial_transiciones"].append(
                {"estado": nuevo_estado, "timestamp": ahora}
            )
            logger.info(f"[Municipal] Task {task_id} cambia a estado {nuevo_estado}")

    async def rpc_convocar_propuestas(self, task_id: str, subtarea: dict) -> dict:
        """
        Invocado por la Centralita para solicitar licitaciones (CFP).
        Devuelve la lista de propuestas estructuradas.
        """
        logger.info(f"[Municipal] Recibido CFP para Task {task_id}")
        self._inicializar_task_memoria(task_id, subtarea)

      
        texto = subtarea.get("texto", "")
        direccion = subtarea.get("ubicacion", {}).get("direccion", "")

        if not texto or not direccion:
            self._cambiar_estado_task(task_id, EstadoTask.INPUT_REQUIRED)
            return {
                "estado": EstadoTask.INPUT_REQUIRED,
                "mensaje_error": "Falta información crítica (el campo 'texto' o la 'direccion' en la ubicación están vacíos)."
            }

        propuestas = generar_propuestas_municipal(subtarea)
        self.tasks_memoria[task_id]["propuestas_enviadas"] = propuestas

        return {
            "estado": EstadoTask.SUBMITTED,
            "propuestas": propuestas
        }


    async def rpc_notificar_asignacion(self, task_id: str, id_propuesta: str, forzar_fallo: bool = False) -> dict:
        """
        La Centralita notifica que este agente ha ganado el CFP con una propuesta concreta.
        Se cambia la Task a WORKING y se procede a la ejecución simulada.
        """
        if task_id not in self.tasks_memoria:
            return {"error": "Task no encontrada en este especialista"}

        logger.info(f"[Municipal] ¡Hemos ganado la licitación! Propuesta asignada: {id_propuesta}")
        self.tasks_memoria[task_id]["propuesta_ganadora"] = id_propuesta
        self._cambiar_estado_task(task_id, EstadoTask.WORKING)

        await asyncio.sleep(0.5)

        resultado = evaluar_resultado_ejecucion(id_propuesta, forzar_fallo=forzar_fallo)
        self.tasks_memoria[task_id]["resultado_final"] = resultado

        if resultado["completado"]:
            self._cambiar_estado_task(task_id, EstadoTask.COMPLETED)

            informe = InformeActuacion(
                rol=RolEspecialista.MUNICIPAL,
                completado=True,
                acciones_realizadas=resultado["acciones_realizadas"],
                recursos_empleados=resultado["recursos_empleados"],
                observaciones=resultado["observaciones"]
            )
            return {"status": "success", "informe": informe.model_dump(), "estado_task": EstadoTask.COMPLETED}
        else:
            self._cambiar_estado_task(task_id, EstadoTask.FAILED)
            return {
                "status": "failed",
                "motivo": resultado["motivo_fallo"],
                "estado_task": EstadoTask.FAILED
            }

    async def rpc_notificar_rechazo(self, task_id: str, id_propuesta: str) -> dict:
        """
        La Centralita le comunica al agente que ha perdido la licitación para esa propuesta.
        """
        logger.info(f"[Municipal] Licitación rechazada para la propuesta {id_propuesta} de la Task {task_id}")
        if task_id in self.tasks_memoria:
            self._cambiar_estado_task(task_id, EstadoTask.CANCELED)
        return {"status": "acknowledged", "mensaje": "Notificación de no asignación procesada."}

    async def rpc_consultar_historial_task(self, task_id: str) -> dict:
        """
        Permite consultar de forma observable el ciclo de vida e historial de transiciones de una Task.
        """
        task_data = self.tasks_memoria.get(task_id)
        if not task_data:
            return {"error": "Task inexistente"}
        return {
            "taskId": task_id,
            "estado_actual": task_data["estado"],
            "historial": task_data["historial_transiciones"]
        }


    def _crear_evento_traza(self, accion: str, detalle: str) -> EventoTraza:
        visibilidad = (
            VisibilidadAgente.PUBLICO
            if self.especificacion.visibilidad == "publico"
            else VisibilidadAgente.PRIVADO
        )
        return EventoTraza(
            instante=datetime.now(timezone.utc),
            agente_id=self.especificacion.identificador,
            rol=RolAgente.MUNICIPAL,
            visibilidad=visibilidad,
            accion=accion,
            detalle=detalle,
        )


    def construir_agent_card(self) -> AgentCard:
        """
        Sobrescribe la Agent Card base para publicar qué sabe hacer exactamente este agente.
        Añadimos metadata clara para superar el Hito 5 (descubrimiento cruzado).
        """
        tarjeta = super().construir_agent_card()

        tarjeta.description = "Especialista en Servicios Municipales de Villa Olivar. Gestiona limpieza de calzadas, obras de urgencia, mantenimiento de infraestructuras y corte de suministros básicos."
        tarjeta.skills = [
            Habilidad(
                id="cortar_suministros",
                name="Corte de Suministros (Agua/Gas/Luz)",
                description="Capacidad para aislar y cortar agua, luz o gas de forma segura ante fugas o incendios."
            ),
            Habilidad(
                id="despliegue_brigadas",
                name="Brigadas Municipales y Mantenimiento",
                description="Despliegue de cuadrillas para limpieza de calzadas, retirada de escombros y reparaciones estructurales (Contract Net habilitado)."
            )
        ]
        return tarjeta

    async def manejar_alerta(self, alerta: AlertaEmergencia) -> InformeResolucion:
        """Procesa una alerta A2A y devuelve un InformeResolucion válido."""

        logger.info(
            "[Municipal] Procesando alerta %s | texto: %.80s",
            alerta.id_emergencia,
            alerta.texto,
        )

        self.estado_actual = "ocupado"
        self.id_emergencia_activa = alerta.id_emergencia
        self.detalle_estado = f"Procesando emergencia {alerta.id_emergencia}"

        traza = [
            self._crear_evento_traza(
                accion="recibir_alerta",
                detalle=f"Municipal recibe subtarea: {alerta.texto[:80]}",
            )
        ]

        datos_alerta = {
            "id_emergencia": str(alerta.id_emergencia),
            "texto": alerta.texto,
            "ubicacion": (
                alerta.ubicacion.model_dump(mode="json")
                if alerta.ubicacion
                else None
            ),
        }

        try:
            resultado = procesar_alerta_municipal(datos_alerta)
        except Exception as exc:
            logger.warning(
                "[Municipal] Fallo en lógica municipal para %s: %s. Usando fallback.",
                alerta.id_emergencia,
                exc,
            )
            resultado = {}

        informe_actuacion = InformeActuacion(
            rol=RolEspecialista.MUNICIPAL,
            completado=bool(resultado.get("completado", True)),
            acciones_realizadas=resultado.get("acciones_realizadas") or [
                "Evaluación de servicios municipales realizada.",
                "Coordinación de apoyo logístico e infraestructuras.",
            ],
            recursos_empleados=resultado.get("recursos_empleados") or [
                "brigada municipal",
                "equipo de mantenimiento",
            ],
            observaciones=resultado.get(
                "observaciones",
                "Servicios Municipales ha procesado la emergencia correctamente.",
            ),
        )

        traza.append(
            self._crear_evento_traza(
                accion="emitir_informe",
                detalle="Municipal emite informe de actuación para Centralita.",
            )
        )

        self.estado_actual = "libre"
        self.id_emergencia_activa = None
        self.detalle_estado = "Agente Municipal disponible."

        return InformeResolucion(
            id_emergencia=alerta.id_emergencia,
            tipo_emergencia=self._inferir_tipo_emergencia(alerta.texto),
            prioridad=Prioridad.MEDIA,
            ubicacion=alerta.ubicacion,
            informes_especialistas=[informe_actuacion],
            estado_final=EstadoFinal.RESUELTA,
            resumen="Servicios Municipales ha evaluado la emergencia y generado su informe.",
            traza_participacion=traza,
        )

    def _inferir_tipo_emergencia(self, texto: str) -> TipoEmergencia:
        texto = (texto or "").lower()

        if any(p in texto for p in ["inundación", "inundacion", "riada", "agua"]):
            return TipoEmergencia.INUNDACION

        if any(p in texto for p in ["accidente", "choque", "colisión", "colision"]):
            return TipoEmergencia.ACCIDENTE_TRAFICO

        if any(p in texto for p in ["derrumbe", "escombros", "colapso"]):
            return TipoEmergencia.DERRUMBE

        if any(p in texto for p in ["derrame", "químico", "quimico", "gas"]):
            return TipoEmergencia.DERRAME_QUIMICO

        if any(p in texto for p in ["incendio", "fuego", "humo"]):
            return TipoEmergencia.INCENDIO

        return TipoEmergencia.OTRO

    async def arrancar(self) -> None:
        """Arranca Municipal y lo registra en el registro REST."""

        await super().arrancar()

        if self.especificacion.visibilidad != "publico":
            logger.info("[Municipal] Agente privado: no se registra en REST.")
            return

        registro_cfg = self.especificacion.parametros.get("registro", {})

        base_url = registro_cfg.get("base_url")
        proyecto = registro_cfg.get("proyecto")
        heartbeat = int(registro_cfg.get("heartbeat_segundos", 30))
        timeout = int(
            registro_cfg.get(
                "timeout_segundos",
                registro_cfg.get("tiempo_espera_segundos", 5),
            )
        )
        grupo = self.especificacion.parametros.get("grupo", "multi007s")

        if not base_url or not proyecto:
            logger.warning(
                "[Municipal] Configuración de registro incompleta. "
                "El agente arranca, pero no se registra en REST."
            )
            return

        self._cliente_registro = ClienteRegistro(
            base_url=base_url,
            proyecto=proyecto,
            nombre_agente=self.especificacion.identificador,
            heartbeat_segundos=heartbeat,
            timeout_segundos=timeout,
        )

        registrado = await self._intentar_registro_rest()
        if not registrado:
            self._tarea_reintento_registro = asyncio.create_task(
                self._reintentar_registro_rest()
            )

    async def detener(self) -> None:
        """Da de baja Municipal del registro REST y detiene el servidor A2A."""

        if self._tarea_reintento_registro is not None:
            self._tarea_reintento_registro.cancel()
            try:
                await self._tarea_reintento_registro
            except asyncio.CancelledError:
                pass
            self._tarea_reintento_registro = None

        if self._cliente_registro is not None:
            try:
                await self._cliente_registro.parar_heartbeats()
                await self._cliente_registro.baja()
                logger.info("[Municipal] Dado de baja del registro REST.")
            except Exception as exc:
                logger.warning(
                    "[Municipal] Error al darse de baja del registro REST: %s",
                    exc,
                )
            finally:
                await self._cliente_registro.aclose()
                self._cliente_registro = None

        await super().detener()

    async def _intentar_registro_rest(self) -> bool:
        """Intenta registrar Municipal en el registro REST una vez."""

        if self._cliente_registro is None:
            return False

        url_a2a = self._url_publica()
        url_agent_card = f"{url_a2a}/.well-known/agent.json"
        grupo = self.especificacion.parametros.get("grupo", "multi007s")

        try:
            await self._cliente_registro.alta(
                grupo=grupo,
                rol=self.especificacion.rol,
                url_a2a=url_a2a,
                url_agent_card=url_agent_card,
            )
            await self._cliente_registro.arrancar_heartbeats()
            self._registrado_en_rest = True

            logger.info("[Municipal] Registrado en REST como público: %s", url_a2a)
            return True

        except Exception as exc:
            logger.warning("[Municipal] Registro REST fallido, se reintentará: %s", exc)
            return False

    async def _reintentar_registro_rest(self) -> None:
        """Reintenta el alta REST hasta conseguirla."""

        while not self._registrado_en_rest:
            await asyncio.sleep(10)
            await self._intentar_registro_rest()