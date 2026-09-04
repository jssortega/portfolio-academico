"""
Agente Bomberos — Villa Olivar (Nivel 3 - Agente A2A).

Autor: Jesús Ortega Castillo (joc00023@ujaen.es)
Grupo: multi007s
"""
from __future__ import annotations

from herramientas.herramientas_bomberos import herramientas_bomberos
from logica.logica_bomberos import procesar_alerta, finalizar_intervencion
from logica.logica_general import *
import json
import asyncio
from datetime import datetime, timezone

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from agentes.base_agente_a2a import BaseAgenteA2A, EspecificacionAgente

from factoria import AgenteA2A

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.agent_card import AgentCard, Habilidad
from contrato.informe_actuacion import InformeActuacion
from contrato.informe_resolucion import InformeResolucion
from contrato.tipos import EstadoFinal, Prioridad, RolEspecialista, TipoEmergencia
from contrato.traza import EventoTraza, RolAgente, VisibilidadAgente

from herramientas.herramientas_bomberos import herramientas_bomberos
from logica.logica_bomberos import procesar_alerta, finalizar_intervencion

from descubrimiento.cliente_registro import ClienteRegistro, ErrorRegistro

logger = logging.getLogger(__name__)

_LLM_TIMEOUT_SEGUNDOS = 5
_APP_NAME = "bomberos_villa_olivar"

class AgenteBomberos(AgenteA2A):
    """Agente bombero"""

    def __init__(self, especificacion: EspecificacionAgente) -> None:
        super().__init__(especificacion)

        self.estado_actual = "libre"
        self.id_emergencia_activa = None
        self.detalle_estado = "Agente Bomberos disponible."
        self._cliente_registro: ClienteRegistro | None = None

        self._llm_agent = LlmAgent(
            name=_APP_NAME,
            instruction=self._leer_prompt(),
            tools=herramientas_bomberos,
            model=self._configurar_modelo(),
        )

        self._session_service = InMemorySessionService()

        self._cfp_activos: dict[str, list[dict[str, Any]]] = {}
        self._awards_recibidos: dict[str, dict[str, Any]] = {}
        self._rechazos_recibidos: list[dict[str, Any]] = []

        self.registrar_handler("contract_net/cfp", self._handler_cfp)
        self.registrar_handler("contract_net/award", self._handler_award)
        self.registrar_handler("contract_net/reject", self._handler_reject)

        self._registrado_en_rest = False
        self._tarea_reintento_registro: asyncio.Task | None = None

    def _configurar_modelo(self) -> str:
        """Obtiene el modelo LLM desde la especificación inyectada por main.py."""
        perfil_llm = self.especificacion.parametros.get("llm", {})

        modelo = perfil_llm.get("modelo", "ollama/llama3.2:3b")
        proveedor = perfil_llm.get("proveedor", "ollama")

        if proveedor == "ollama" and not modelo.startswith("ollama/"):
            return f"ollama/{modelo}"

        if proveedor in ("google", "gemini") and modelo.startswith("gemini/"):
            return modelo.replace("gemini/", "", 1)

        return modelo

    def _leer_prompt(self) -> str:
        """Devuelve el prompt del agente Bomberos."""
        prompt_externo = self.especificacion.parametros.get("prompt_instruccion")
        if prompt_externo:
            return prompt_externo

        return (
            "Eres el agente Bomberos del sistema Villa Olivar. "
            "Tu función es evaluar incendios, derrames químicos, humo, explosiones, "
            "rescates y riesgos estructurales. "
            "Debes usar tus herramientas ADK cuando sea útil. "
            "Devuelve SOLO un JSON válido con esta estructura: "
            "{"
            "\"acciones_realizadas\": [\"...\"], "
            "\"recursos_empleados\": [\"...\"], "
            "\"observaciones\": \"...\", "
            "\"completado\": true"
            "}"
        )

    def construir_agent_card(self) -> AgentCard:
        """Publica la Agent Card de Bomberos."""

        habilidades = [
            Habilidad(
                id="evaluar_riesgo_incendio",
                name="Evaluar riesgo de incendio",
                description=(
                    "Evalúa incendios en viviendas, edificios, zonas forestales "
                    "o instalaciones industriales, determinando riesgo, radio de "
                    "seguridad y recursos necesarios."
                ),
                tags=["bomberos", "incendio", "riesgo"],
            ),
            Habilidad(
                id="evaluar_riesgo_quimico",
                name="Evaluar riesgo químico",
                description=(
                    "Evalúa derrames o fugas de sustancias peligrosas como amoniaco, "
                    "cloro o gasolina, proponiendo radio de seguridad y medidas de contención."
                ),
                tags=["bomberos", "derrame_quimico", "nbqr"],
            ),
            Habilidad(
                id="planificar_intervencion",
                name="Planificar intervención de Bomberos",
                description=(
                    "Planifica la actuación de Bomberos, recursos desplegados, "
                    "acciones de extinción, contención o rescate."
                ),
                tags=["bomberos", "intervencion", "rescate"],
            ),
            Habilidad(
                id="negociacion_contract_net",
                name="Negociación Contract Net",
                description=(
                    "Responde a convocatorias CFP de la Centralita con propuestas "
                    "estructuradas de unidades de Bomberos y acepta adjudicaciones."
                ),
                tags=["bomberos", "contract_net", "cfp", "award"],
            ),
        ]

        return AgentCard(
            name=self.especificacion.identificador,
            description=(
                "Agente Bomberos del sistema Villa Olivar. Especialista en "
                "incendios, derrames químicos, explosiones, humo, rescates "
                "y control de zonas peligrosas."
            ),
            url=self._url_publica(),
            version="1.0.0",
            skills=habilidades,
        )

    async def manejar_alerta(self, alerta: AlertaEmergencia) -> InformeResolucion:
        """Procesa una alerta A2A y devuelve un InformeResolucion válido."""

        logger.info(
            "[Bomberos] Procesando alerta %s | texto: %.80s",
            alerta.id_emergencia,
            alerta.texto,
        )

        self.estado_actual = "ocupado"
        self.id_emergencia_activa = alerta.id_emergencia
        self.detalle_estado = f"Procesando emergencia {alerta.id_emergencia}"

        grupo_externo = alerta.coordinacion[0] if alerta.coordinacion else None

        traza = [
            self._crear_evento_traza(
                accion="recibir_alerta",
                detalle=f"Bomberos recibe subtarea: {alerta.texto[:80]}",
                grupo_externo=grupo_externo,
            )
        ]

        try:
            resultado = await self._procesar_con_llm(alerta)
        except Exception as exc:
            logger.warning(
                "[Bomberos] Fallo en LLM para %s: %s. Usando fallback.",
                alerta.id_emergencia,
                exc,
            )
            resultado = self._fallback_determinista(alerta)

        informe_actuacion = self._crear_informe_actuacion(resultado)

        traza.append(
            self._crear_evento_traza(
                accion="emitir_informe",
                detalle="Bomberos emite informe de actuación para Centralita.",
                grupo_externo=grupo_externo,
            )
        )

        tipo_emergencia = self._inferir_tipo_emergencia(alerta.texto)
        prioridad = self._inferir_prioridad(resultado)

        self.estado_actual = "libre"
        self.id_emergencia_activa = None
        self.detalle_estado = "Agente Bomberos disponible."

        return InformeResolucion(
            id_emergencia=alerta.id_emergencia,
            tipo_emergencia=tipo_emergencia,
            prioridad=prioridad,
            ubicacion=alerta.ubicacion,
            informes_especialistas=[informe_actuacion],
            estado_final=EstadoFinal.RESUELTA,
            resumen="Bomberos ha evaluado la emergencia y ha generado su informe de actuación.",
            traza_participacion=traza,
        )

    def _crear_evento_traza(self,accion: str,detalle: str,grupo_externo: str | None = None,) -> EventoTraza:
        """Crea un evento de traza para Bomberos."""

        visibilidad = (
            VisibilidadAgente.PUBLICO
            if self.especificacion.visibilidad == "publico"
            else VisibilidadAgente.PRIVADO
        )

        return EventoTraza(
            instante=datetime.now(timezone.utc),
            agente_id=self.especificacion.identificador,
            rol=RolAgente.BOMBEROS,
            visibilidad=visibilidad,
            accion=accion,
            detalle=detalle,
            grupo_externo=grupo_externo,
        )

    async def _procesar_con_llm(self, alerta: AlertaEmergencia) -> dict[str, Any]:
        """Procesa la alerta con ADK + herramientas."""

        consulta = (
            f"ID emergencia: {alerta.id_emergencia}\n"
            f"Texto: {alerta.texto}\n"
            f"Ubicación: {alerta.ubicacion.direccion if alerta.ubicacion else 'desconocida'}\n\n"
            "Evalúa la situación desde el rol de Bomberos. "
            "Usa herramientas si procede. "
            "Devuelve SOLO JSON con: "
            "acciones_realizadas, recursos_empleados, observaciones, completado."
        )

        respuesta = await asyncio.wait_for(
            self._invocar_adk(consulta),
            timeout=_LLM_TIMEOUT_SEGUNDOS,
        )

        return self._parsear_respuesta_llm(respuesta)

    async def _invocar_adk(self, consulta: str) -> str:
        """Ejecuta el LlmAgent de ADK con una sesión nueva."""

        import uuid

        session_id = f"bomberos_{uuid.uuid4().hex}"

        await self._session_service.create_session(
            app_name=_APP_NAME,
            user_id="centralita",
            session_id=session_id,
        )

        runner = Runner(
            agent=self._llm_agent,
            app_name=_APP_NAME,
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

    def _parsear_respuesta_llm(self, respuesta: str) -> dict[str, Any]:
        """Parsea el JSON devuelto por el LLM."""

        limpio = (
            respuesta.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )

        datos = json.loads(limpio)

        if not isinstance(datos.get("acciones_realizadas"), list):
            raise ValueError("El LLM no devolvió acciones_realizadas como lista.")

        if not isinstance(datos.get("recursos_empleados"), list):
            raise ValueError("El LLM no devolvió recursos_empleados como lista.")

        return datos

    def _fallback_determinista(self, alerta: AlertaEmergencia) -> dict[str, Any]:
        """Procesa la alerta con la lógica local si falla el LLM."""

        datos_alerta = {
            "id_emergencia": str(alerta.id_emergencia),
            "texto": alerta.texto,
            "ubicacion": (
                alerta.ubicacion.model_dump(mode="json")
                if alerta.ubicacion
                else None
            ),
        }

        return procesar_alerta(datos_alerta)

    def _crear_informe_actuacion(self, resultado: dict[str, Any]) -> InformeActuacion:
        """Convierte el resultado de la lógica/LLM en InformeActuacion."""

        return InformeActuacion(
            rol=RolEspecialista.BOMBEROS,
            completado=bool(resultado.get("completado", True)),
            acciones_realizadas=resultado.get("acciones_realizadas") or [
                "Evaluación inicial realizada por Bomberos."
            ],
            recursos_empleados=resultado.get("recursos_empleados") or [
                "dotación de bomberos"
            ],
            observaciones=resultado.get(
                "observaciones",
                "Bomberos ha procesado la emergencia correctamente.",
            ),
        )

    def _inferir_tipo_emergencia(self, texto: str) -> TipoEmergencia:
        """Devuelve un TipoEmergencia válido para el contrato."""

        texto = (texto or "").lower()

        if any(p in texto for p in ["derrame", "fuga", "químico", "quimico", "cloro", "amoniaco", "gasolina"]):
            return TipoEmergencia.DERRAME_QUIMICO

        if any(p in texto for p in ["derrumbe", "colapso", "atrapado", "escombros"]):
            return TipoEmergencia.DERRUMBE

        if any(p in texto for p in ["incendio", "fuego", "humo", "llamas", "explosion", "explosión"]):
            return TipoEmergencia.INCENDIO

        return TipoEmergencia.OTRO

    def _inferir_prioridad(self, resultado: dict[str, Any]) -> Prioridad:
        """Devuelve una Prioridad válida para el contrato."""

        prioridad = str(resultado.get("prioridad", "media")).lower()

        if prioridad == "critica":
            return Prioridad.CRITICA

        if prioridad == "alta":
            return Prioridad.ALTA

        if prioridad == "baja":
            return Prioridad.BAJA

        return Prioridad.MEDIA

    async def _handler_cfp(self, params: dict) -> dict:
        """
        Responde a una Call For Proposals de Contract Net.

        La Centralita llama a este método cuando quiere comparar varias
        unidades de Bomberos antes de adjudicar una subtarea.
        """

        id_cfp = str(
            params.get("id_cfp")
            or params.get("id")
            or f"cfp_bomberos_{datetime.now(timezone.utc).timestamp()}"
        )

        datos = params.get("datos", {})
        if not isinstance(datos, dict):
            datos = {}

        texto = (
            params.get("texto")
            or params.get("descripcion")
            or datos.get("texto")
            or datos.get("descripcion")
            or ""
        )

        if not texto:
            texto = "Intervención de Bomberos solicitada por Centralita."

        tipo = self._inferir_tipo_emergencia(texto)

        propuestas = self._generar_propuestas_bomberos(
            id_cfp=id_cfp,
            texto=texto,
            tipo=tipo,
        )

        self._cfp_activos[id_cfp] = propuestas

        logger.info(
            "[Bomberos] CFP recibido %s. Propuestas generadas: %s",
            id_cfp,
            len(propuestas),
        )

        return {
            "aceptado": True,
            "id_cfp": id_cfp,
            "rol": "bomberos",
            "criterio_recomendado": "menor_tiempo_estimado",
            "propuestas": propuestas,
            "propuesta": propuestas[0],
        }

    def _generar_propuestas_bomberos(
        self,
        id_cfp: str,
        texto: str,
        tipo: TipoEmergencia,
    ) -> list[dict[str, Any]]:
        """Genera propuestas deterministas de unidades de Bomberos."""

        if tipo == TipoEmergencia.DERRAME_QUIMICO:
            return [
                {
                    "id_propuesta": f"{id_cfp}-nbqr_1",
                    "unidad": "unidad_nbqr_1",
                    "rol": "bomberos",
                    "tiempo_estimado_min": 8,
                    "coste": 4,
                    "cobertura": 95,
                    "recursos": ["equipo NBQR", "trajes de protección", "material de contención"],
                    "acciones": [
                        "Evaluar sustancia peligrosa.",
                        "Aislar la zona afectada.",
                        "Contener el derrame químico.",
                    ],
                    "observaciones": f"Propuesta especializada para derrame químico: {texto[:80]}",
                },
                {
                    "id_propuesta": f"{id_cfp}-bomba_1",
                    "unidad": "bomba_1",
                    "rol": "bomberos",
                    "tiempo_estimado_min": 5,
                    "coste": 2,
                    "cobertura": 60,
                    "recursos": ["camión bomba", "equipo de primera intervención"],
                    "acciones": [
                        "Asegurar acceso inicial.",
                        "Apoyar el aislamiento preventivo.",
                    ],
                    "observaciones": "Respuesta rápida, pero con menor cobertura NBQR.",
                },
            ]

        if tipo == TipoEmergencia.DERRUMBE:
            return [
                {
                    "id_propuesta": f"{id_cfp}-rescate_1",
                    "unidad": "unidad_rescate_1",
                    "rol": "bomberos",
                    "tiempo_estimado_min": 7,
                    "coste": 4,
                    "cobertura": 90,
                    "recursos": ["equipo de rescate", "material de apuntalamiento"],
                    "acciones": [
                        "Evaluar estabilidad estructural.",
                        "Buscar posibles personas atrapadas.",
                        "Asegurar zona de intervención.",
                    ],
                    "observaciones": f"Propuesta de rescate estructural: {texto[:80]}",
                },
                {
                    "id_propuesta": f"{id_cfp}-bomba_2",
                    "unidad": "bomba_2",
                    "rol": "bomberos",
                    "tiempo_estimado_min": 4,
                    "coste": 2,
                    "cobertura": 55,
                    "recursos": ["dotación ligera de bomberos"],
                    "acciones": [
                        "Realizar evaluación inicial.",
                        "Balizar zona hasta llegada de rescate.",
                    ],
                    "observaciones": "Respuesta rápida de primera valoración.",
                },
            ]

        return [
            {
                "id_propuesta": f"{id_cfp}-bomba_1",
                "unidad": "bomba_1",
                "rol": "bomberos",
                "tiempo_estimado_min": 6,
                "coste": 3,
                "cobertura": 85,
                "recursos": ["camión bomba", "equipo de extinción", "equipo de respiración"],
                "acciones": [
                    "Evaluar foco del incendio.",
                    "Desplegar equipo de extinción.",
                    "Controlar propagación de humo y llamas.",
                ],
                "observaciones": f"Propuesta principal para incendio/intervención: {texto[:80]}",
            },
            {
                "id_propuesta": f"{id_cfp}-cisterna_1",
                "unidad": "cisterna_1",
                "rol": "bomberos",
                "tiempo_estimado_min": 10,
                "coste": 4,
                "cobertura": 95,
                "recursos": ["camión cisterna", "equipo de apoyo hidráulico"],
                "acciones": [
                    "Aportar agua adicional.",
                    "Apoyar extinción prolongada.",
                    "Evitar reignición.",
                ],
                "observaciones": "Mayor cobertura, pero llegada más lenta.",
            },
        ]

    async def _handler_award(self, params: dict) -> dict:
        """Recibe la adjudicación de una propuesta ganadora."""

        id_cfp = str(params.get("id_cfp") or params.get("id") or "")
        id_propuesta = str(params.get("id_propuesta") or "")

        propuesta = self._buscar_propuesta(id_cfp, id_propuesta)

        if propuesta is None:
            propuesta = params.get("propuesta")

        if not isinstance(propuesta, dict):
            return {
                "aceptado": False,
                "id_cfp": id_cfp,
                "motivo": "No se encontró la propuesta adjudicada.",
            }

        self._awards_recibidos[id_cfp] = propuesta
        self.estado_actual = "ocupado"
        self.detalle_estado = (
            f"Ejecutando propuesta adjudicada {propuesta.get('id_propuesta')}"
        )

        logger.info(
            "[Bomberos] Award recibido para CFP %s: %s",
            id_cfp,
            propuesta.get("id_propuesta"),
        )

        resultado = {
            "completado": True,
            "acciones_realizadas": propuesta.get("acciones", [
                "Intervención de Bomberos ejecutada."
            ]),
            "recursos_empleados": propuesta.get("recursos", [
                propuesta.get("unidad", "dotación de bomberos")
            ]),
            "observaciones": (
                "Bomberos acepta y ejecuta la propuesta adjudicada: "
                f"{propuesta.get('id_propuesta')}"
            ),
        }

        self.estado_actual = "libre"
        self.detalle_estado = "Agente Bomberos disponible."

        return {
            "aceptado": True,
            "id_cfp": id_cfp,
            "rol": "bomberos",
            "propuesta_adjudicada": propuesta,
            "resultado": resultado,
        }

    async def _handler_reject(self, params: dict) -> dict:
        """Recibe notificación de que Bomberos no ha ganado el CFP."""

        self._rechazos_recibidos.append(params)

        logger.info(
            "[Bomberos] Propuesta rechazada en Contract Net: %s",
            params,
        )

        return {
            "recibido": True,
            "rol": "bomberos",
            "estado": "rechazo_registrado",
        }

    def _buscar_propuesta(
        self,
        id_cfp: str,
        id_propuesta: str,
    ) -> dict[str, Any] | None:
        """Busca una propuesta previamente generada para un CFP."""

        propuestas = self._cfp_activos.get(id_cfp, [])

        if not propuestas:
            return None

        if not id_propuesta:
            return propuestas[0]

        for propuesta in propuestas:
            if propuesta.get("id_propuesta") == id_propuesta:
                return propuesta

        return None

    async def arrancar(self) -> None:
        """Arranca Bomberos y lo registra en el registro REST."""

        await super().arrancar()

        if self.especificacion.visibilidad != "publico":
            logger.info("[Bomberos] Agente privado: no se registra en REST.")
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
                "[Bomberos] Configuración de registro incompleta. "
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
        """Da de baja Bomberos del registro REST y detiene el servidor A2A."""

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
                logger.info("[Bomberos] Dado de baja del registro REST.")

            except Exception as exc:
                logger.warning(
                    "[Bomberos] Error al darse de baja del registro REST: %s",
                    exc,
                )

            finally:
                await self._cliente_registro.aclose()
                self._cliente_registro = None

        await super().detener()

    async def _intentar_registro_rest(self) -> bool:
        """Intenta registrar Bomberos en el registro REST una vez."""

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

            logger.info("[Bomberos] Registrado en REST como público: %s", url_a2a)
            return True

        except Exception as exc:
            logger.warning("[Bomberos] Registro REST fallido, se reintentará: %s", exc)
            return False

    async def _reintentar_registro_rest(self) -> None:
        """Reintenta el alta REST hasta conseguirla."""

        while not self._registrado_en_rest:
            await asyncio.sleep(10)
            await self._intentar_registro_rest()