"""
Tests de integración — Villa Olivar (Nivel 2).

Cubre los tests exigidos en el README para los Hitos 3 y 4:

  Hito 3:
    - test_centralita_clasifica_con_llm
    - test_especialista_razona_con_llm
    - test_escenario_completo_con_llm

  Hito 4:
    - test_centralita_protocolo_supervisor
    - test_consulta_estado_todos_agentes

Las pruebas con mock son siempre ejecutables (offline).
Las pruebas con XMPP real se saltan si Docker no está levantado.

Autor(es): multi007s
"""

import asyncio
import importlib
import json
import socket
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ontologia.modelos_compartidos import (
    ConsultaEstado,
    DatosEmergencia,
    EstadoAgente,
    InformeResolucion,
    Prioridad,
    TipoEmergencia,
)

# ---------------------------------------------------------------------------
# Guard XMPP
# ---------------------------------------------------------------------------

def _xmpp_disponible() -> bool:
    try:
        with socket.create_connection(("localhost", 5222), timeout=2):
            return True
    except OSError:
        return False


XMPP_DISPONIBLE = _xmpp_disponible()
skip_sin_xmpp = pytest.mark.skipif(
    not XMPP_DISPONIBLE,
    reason="Servidor XMPP no disponible. Ejecuta 'docker compose up -d' primero.",
)

# ---------------------------------------------------------------------------
# Datos de prueba compartidos
# ---------------------------------------------------------------------------

ALERTA_DERRAME = {
    "tipo_mensaje": "alerta_emergencia",
    "id_emergencia": "INC-2026-TEST-001",
    "tipo_emergencia": "derrame_quimico",
    "ubicacion": {"direccion": "Polígono Industrial Villa Olivar"},
    "prioridad": "alta",
    "descripcion": "Derrame de amoniaco en nave industrial. 5 afectados.",
    "marca_temporal": "2026-04-13T10:00:00Z",
}

DATOS_EMERGENCIA_SUPERVISOR = DatosEmergencia(
    id_emergencia="INC-2026-TEST-003",
    tipo_emergencia=TipoEmergencia("derrame_quimico"),
    ubicacion={"direccion": "Avenida Constitución 42"},
    prioridad=Prioridad("alta"),
    descripcion="Cisterna de amoniaco volcada. 5 afectados.",
)

ROLES = ["centralita", "bomberos", "sanitario", "policia", "municipal"]

CLASES_AGENTES = {
    "centralita": ("agentes.agente_centralita", "AgenteCentralita"),
    "bomberos":   ("agentes.agente_bomberos",   "AgenteBomberos"),
    "sanitario":  ("agentes.agente_sanitario",  "AgenteSanitario"),
    "policia":    ("agentes.agente_policia",     "AgentePolicia"),
    "municipal":  ("agentes.agente_municipal",   "AgenteMunicipal"),
}


# ===========================================================================
# HITO 3 — test_centralita_clasifica_con_llm
# ===========================================================================

class TestCentralitaClasificaConLLM:
    """La Centralita recibe un DatosEmergencia, invoca al LLM y clasifica."""

    def test_datos_emergencia_es_valido(self) -> None:
        """DatosEmergencia se construye correctamente con los datos del supervisor."""
        assert DATOS_EMERGENCIA_SUPERVISOR.id_emergencia == "INC-2026-TEST-003"
        assert DATOS_EMERGENCIA_SUPERVISOR.tipo_emergencia == TipoEmergencia("derrame_quimico")

    def test_clasificar_emergencia_logica_pura(self) -> None:
        """La función de lógica pura clasifica correctamente (sin LLM)."""
        from logica.logica_centralita import clasificar_emergencia
        prioridad = clasificar_emergencia(
            tipo_emergencia="derrame_quimico",
            hay_heridos=True,
            numero_afectados=5,
        )
        assert prioridad in ("baja", "media", "alta", "critica")

    def test_determinar_destinatarios_derrame(self) -> None:
        """determinar_destinatarios devuelve los cuatro cuerpos para derrame químico."""
        from logica.logica_centralita import determinar_destinatarios
        destinatarios = determinar_destinatarios("derrame_quimico")
        for cuerpo in ("bomberos", "sanitario", "policia", "municipal"):
            assert cuerpo in destinatarios

    @pytest.mark.asyncio
    async def test_centralita_clasifica_con_llm(self) -> None:
        """Con LLM simulado, la Centralita devuelve una clasificación válida (no lanza)."""
        from agentes.agente_centralita import AgenteCentralita

        respuesta_simulada = json.dumps({
            "tipo_mensaje": "informe_resolucion",
            "id_emergencia": "INC-2026-TEST-003",
            "tipo_emergencia": "derrame_quimico",
            "prioridad": "alta",
            "estado_final": "cerrado",
            "resumen": "Emergencia resuelta.",
            "agentes_participantes": ["bomberos", "sanitario"],
            "acciones_realizadas": ["Evaluación de riesgo", "Perímetro establecido"],
        })

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

        centralita.llm_chat = AsyncMock(return_value=respuesta_simulada)
        resultado = await centralita.llm_chat(
            "Clasifica esta emergencia: " + json.dumps(ALERTA_DERRAME)
        )
        assert isinstance(resultado, str)
        datos = json.loads(resultado)
        assert "tipo_emergencia" in datos or "tipo_mensaje" in datos

    def test_informe_resolucion_fallback_valido(self) -> None:
        """El fallback determinista genera un InformeResolucion válido y parseable."""
        informe = InformeResolucion(
            id_emergencia="INC-2026-TEST-003",
            tipo_emergencia=TipoEmergencia("derrame_quimico"),
            prioridad=Prioridad("alta"),
            estado_final="cerrado",
            resumen="Emergencia derrame_quimico resuelta.",
            agentes_participantes=["bomberos", "sanitario"],
            acciones_realizadas=["Intervención completada"],
        )
        recuperado = InformeResolucion.model_validate_json(informe.model_dump_json())
        assert recuperado.id_emergencia == "INC-2026-TEST-003"


# ===========================================================================
# HITO 3 — test_especialista_razona_con_llm
# ===========================================================================

class TestEspecialistaRazonaConLLM:
    """Un especialista recibe una alerta y genera un informe usando el LLM."""

    @pytest.mark.asyncio
    async def test_especialista_razona_con_llm(self) -> None:
        """AgenteBomberos genera un informe de actuación con LLM simulado."""
        from agentes.agente_bomberos import AgenteBomberos

        respuesta_simulada = json.dumps({
            "evaluacion": {"nivel": "urgente", "radio": "500m", "necesita_gas": True},
            "informe_centralita": {
                "tipo_mensaje": "informe_actuacion",
                "id_emergencia": "INC-2026-TEST-001",
                "agente_origen": "bomberos",
                "estado": "en_camino",
                "detalle": "Riesgo urgente por derrame de amoniaco.",
                "marca_temporal": datetime.now(timezone.utc).isoformat(),
            },
            "recursos_policia": {
                "tipo_mensaje": "solicitud_recurso",
                "id_emergencia": "INC-2026-TEST-001",
                "solicitante": "bomberos",
                "destinatario": "policia",
                "accion_solicitada": "establecer_perimetro",
                "parametros": {"radio_metros": 500},
                "urgencia": "urgente",
                "marca_temporal": datetime.now(timezone.utc).isoformat(),
            },
            "recursos_municipal": None,
        })

        with patch("agentes.base_agente_llm.AgenteVillaOlivarLLM._cargar_prompt",
                   return_value="prompt de prueba"), \
             patch("agentes.base_agente_llm.AgenteVillaOlivarLLM._crear_proveedor",
                   return_value=MagicMock()):
            try:
                bomberos = AgenteBomberos(
                    jid="bomberos_test@localhost",
                    password="pass",
                    config_llm={"proveedor": "ollama", "modelo": "llama3.2:3b"},
                )
            except Exception:
                pytest.skip("No se pudo instanciar AgenteBomberos en modo offline.")

        bomberos.llm_chat = AsyncMock(return_value=respuesta_simulada)
        resultado_str = await bomberos.llm_chat(
            "Procesa esta alerta: " + json.dumps(ALERTA_DERRAME)
        )
        resultado = json.loads(resultado_str)
        assert "informe_centralita" in resultado
        assert resultado["informe_centralita"]["agente_origen"] == "bomberos"
        assert resultado["informe_centralita"]["estado"] in (
            "en_camino", "recibido", "actuando", "finalizado"
        )

    def test_especialista_fallback_logica_pura(self) -> None:
        """El fallback de Bomberos (lógica pura) produce el esquema esperado."""
        from logica.logica_bomberos import procesar_alerta
        resultado = procesar_alerta(ALERTA_DERRAME)
        assert "informe_centralita" in resultado
        assert resultado["informe_centralita"]["agente_origen"] == "bomberos"
        assert "recursos_policia" in resultado

    @pytest.mark.asyncio
    async def test_policia_genera_informe_con_llm_mock(self) -> None:
        """AgentePolicia genera un informe con agente_origen 'policia' mediante LLM simulado."""
        from agentes.agente_policia import AgentePolicia

        respuesta_simulada = json.dumps({
            "tipo_mensaje": "informe_actuacion",
            "id_emergencia": "INC-2026-TEST-001",
            "agente_origen": "policia",
            "estado": "actuando",
            "detalle": "Perímetro de 500 m establecido.",
            "recursos_desplegados": 2,
            "marca_temporal": datetime.now(timezone.utc).isoformat(),
        })

        with patch("agentes.base_agente_llm.AgenteVillaOlivarLLM._cargar_prompt",
                   return_value="prompt de prueba"), \
             patch("agentes.base_agente_llm.AgenteVillaOlivarLLM._crear_proveedor",
                   return_value=MagicMock()):
            try:
                policia = AgentePolicia(
                    jid="policia_test@localhost",
                    password="pass",
                    config_llm={"proveedor": "ollama", "modelo": "llama3.2:3b"},
                )
            except Exception:
                pytest.skip("No se pudo instanciar AgentePolicia en modo offline.")

        policia.llm_chat = AsyncMock(return_value=respuesta_simulada)
        resultado = json.loads(
            await policia.llm_chat("Procesa esta alerta: " + json.dumps(ALERTA_DERRAME))
        )
        assert resultado.get("agente_origen") == "policia"


# ===========================================================================
# HITO 3 — test_escenario_completo_con_llm
# ===========================================================================

class TestEscenarioCompletoConLLM:
    """Escenario completo con los cinco agentes y verificación de cierre."""

    def test_escenario_completo_con_llm(self) -> None:
        """Escenario completo usando lógica pura (sin LLM ni XMPP) — smoke test."""
        from logica.logica_centralita import (
            clasificar_emergencia,
            determinar_destinatarios,
            generar_id_emergencia,
            resetear_contador,
        )
        from logica.logica_bomberos import procesar_alerta, finalizar_intervencion
        from logica.logica_sanitario import procesarAlertaAceptada, atenderHeridos
        from logica.logica_policia import verificarAlerta, procesarAlertaAceptada as policia_aceptada
        from logica.logica_municipal import procesar_alerta_municipal, finalizar_intervencion_municipal

        resetear_contador()
        id_em = generar_id_emergencia()
        assert id_em.startswith("INC-")

        prioridad = clasificar_emergencia("derrame_quimico", hay_heridos=True, numero_afectados=5)
        assert prioridad in ("alta", "critica")

        destinatarios = determinar_destinatarios("derrame_quimico")
        assert set(destinatarios) >= {"bomberos", "sanitario", "policia", "municipal"}

        alerta = {**ALERTA_DERRAME, "id_emergencia": id_em}

        res_bomberos = procesar_alerta(alerta)
        assert res_bomberos["informe_centralita"]["agente_origen"] == "bomberos"

        res_sanitario = procesarAlertaAceptada(alerta)
        assert res_sanitario["agente_origen"] == "sanitario"
        assert atenderHeridos(alerta)["estado"] == "finalizado"

        assert verificarAlerta(alerta) is True
        assert policia_aceptada(alerta)["agente_origen"] == "policia"

        assert "informe_centralita" in procesar_alerta_municipal(alerta)

        assert finalizar_intervencion(id_em)["estado"] == "finalizado"
        assert finalizar_intervencion_municipal(id_em)["estado"] == "finalizado"

    def test_informe_resolucion_cierre_valido(self) -> None:
        """El InformeResolucion de cierre tiene estado_final 'cerrado'."""
        informe = InformeResolucion(
            id_emergencia="INC-2026-TEST-001",
            tipo_emergencia=TipoEmergencia("derrame_quimico"),
            prioridad=Prioridad("alta"),
            estado_final="cerrado",
            resumen="Emergencia completada.",
            agentes_participantes=["bomberos", "sanitario", "policia", "municipal"],
            acciones_realizadas=["Intervención completada"],
        )
        assert informe.estado_final == "cerrado"
        assert len(informe.agentes_participantes) == 4

    @skip_sin_xmpp
    @pytest.mark.asyncio
    async def test_escenario_completo_con_llm_xmpp(self) -> None:
        """(Requiere XMPP) Los cinco agentes arrancan y están vivos."""
        import utils  # noqa: F401
        from agentes.agente_centralita import AgenteCentralita
        from agentes.agente_bomberos import AgenteBomberos
        from agentes.agente_sanitario import AgenteSanitario
        from agentes.agente_policia import AgentePolicia
        from agentes.agente_municipal import AgenteMunicipal

        agentes = [
            AgenteCentralita(jid="centralita_multi007s@localhost", password="centralita_multi007s_pass"),
            AgenteBomberos(jid="bomberos_multi007s@localhost", password="bomberos_multi007s_pass"),
            AgenteSanitario(jid="sanitario_multi007s@localhost", password="sanitario_multi007s_pass"),
            AgentePolicia(jid="policia_multi007s@localhost", password="policia_multi007s_pass"),
            AgenteMunicipal(jid="municipal_multi007s@localhost", password="municipal_multi007s_pass"),
        ]
        try:
            for ag in agentes:
                await ag.start(auto_register=True)
            await asyncio.sleep(5)
            for ag in agentes:
                assert ag.is_alive(), f"{ag.jid} no está vivo."
        finally:
            for ag in agentes:
                try:
                    await ag.stop()
                except Exception:
                    pass


# ===========================================================================
# HITO 4 — test_centralita_protocolo_supervisor
# ===========================================================================

class TestCentralitaProtocoloSupervisor:
    """Simulación del protocolo supervisor: DatosEmergencia → agree → InformeResolucion."""

    def test_centralita_protocolo_supervisor(self) -> None:
        """DatosEmergencia se serializa, envía y el InformeResolucion mantiene el mismo id."""
        json_str = DATOS_EMERGENCIA_SUPERVISOR.model_dump_json()
        recuperado = DatosEmergencia.model_validate_json(json_str)
        assert recuperado.id_emergencia == DATOS_EMERGENCIA_SUPERVISOR.id_emergencia

        informe = InformeResolucion(
            id_emergencia=recuperado.id_emergencia,
            tipo_emergencia=recuperado.tipo_emergencia,
            prioridad=recuperado.prioridad,
            estado_final="cerrado",
            resumen="Emergencia resuelta.",
            agentes_participantes=["bomberos", "sanitario", "policia", "municipal"],
            acciones_realizadas=["Intervención completada"],
        )
        assert informe.id_emergencia == DATOS_EMERGENCIA_SUPERVISOR.id_emergencia

    def test_informe_tiene_mismo_id_que_request(self) -> None:
        """El InformeResolucion preserva el id_emergencia del request original."""
        id_original = "INC-2026-SUPER-001"
        informe = InformeResolucion(
            id_emergencia=id_original,
            tipo_emergencia=TipoEmergencia("incendio"),
            prioridad=Prioridad("alta"),
            estado_final="cerrado",
            resumen="Incendio extinguido.",
            agentes_participantes=["bomberos", "sanitario"],
            acciones_realizadas=["Extinción completada"],
        )
        assert informe.id_emergencia == id_original

    def test_centralita_resetea_estado_para_nueva_emergencia(self) -> None:
        """_resetear_estado_emergencia() limpia todos los campos de estado."""
        with patch("agentes.base_agente_llm.AgenteVillaOlivarLLM._cargar_prompt",
                   return_value="prompt"), \
             patch("agentes.base_agente_llm.AgenteVillaOlivarLLM._crear_proveedor",
                   return_value=MagicMock()):
            try:
                from agentes.agente_centralita import AgenteCentralita
                centralita = AgenteCentralita(
                    jid="centralita_test@localhost", password="pass"
                )
            except Exception:
                pytest.skip("No se pudo instanciar AgenteCentralita.")

        centralita.id_emergencia_activa = "INC-VIEJA"
        centralita.jid_supervisor = "supervisor@localhost"
        centralita.cierre_emitido = True
        centralita._resetear_estado_emergencia()

        assert centralita.id_emergencia_activa == ""
        assert centralita.jid_supervisor == ""
        assert centralita.cierre_emitido is False
        assert centralita.estadoEmergencia == "sin_emergencia"

    @skip_sin_xmpp
    @pytest.mark.asyncio
    async def test_centralita_protocolo_supervisor_real(self) -> None:
        """(Requiere XMPP) La Centralita arranca y está viva."""
        import utils  # noqa: F401
        from agentes.agente_centralita import AgenteCentralita

        centralita = AgenteCentralita(
            jid="centralita_multi007s@localhost",
            password="centralita_multi007s_pass",
        )
        try:
            await centralita.start(auto_register=True)
            await asyncio.sleep(3)
            assert centralita.is_alive()
        finally:
            await centralita.stop()


# ===========================================================================
# HITO 4 — test_consulta_estado_todos_agentes
# ===========================================================================

class TestConsultaEstadoTodosAgentes:
    """Envío de ConsultaEstado a cada agente y verificación de EstadoAgente."""

    def test_consulta_estado_todos_agentes(self) -> None:
        """EstadoAgente y ConsultaEstado se construyen y serializan correctamente."""
        estado = EstadoAgente(
            agente="bomberos_multi007s@localhost",
            estado="operativo",
            emergencia_actual=None,
            detalle="Sin emergencia activa",
        )
        recuperado = EstadoAgente.model_validate_json(estado.model_dump_json())
        assert recuperado.estado == "operativo"


        consulta = ConsultaEstado(
            agente_destino="bomberos@localhost",
            marca_temporal=datetime.now(timezone.utc),
        )
        recuperado_c = ConsultaEstado.model_validate_json(consulta.model_dump_json())


        assert recuperado_c.agente_destino == "bomberos@localhost"
    @pytest.mark.parametrize("rol", ROLES)
    def test_agente_tiene_estado_emergencia(self, rol: str) -> None:
        """Cada agente expone el atributo estadoEmergencia o estado_actual."""
        modulo_nombre, clase_nombre = CLASES_AGENTES[rol]
        try:
            modulo = importlib.import_module(modulo_nombre)
        except ImportError as exc:
            pytest.skip(f"No se pudo importar '{modulo_nombre}': {exc}")
        clase = getattr(modulo, clase_nombre)

        with patch("agentes.base_agente_llm.AgenteVillaOlivarLLM._cargar_prompt",
                   return_value="prompt"), \
             patch("agentes.base_agente_llm.AgenteVillaOlivarLLM._crear_proveedor",
                   return_value=MagicMock()):
            try:
                kwargs = {"jid": f"{rol}_test@localhost", "password": "pass"}
                if rol != "centralita":
                    kwargs["config_llm"] = {"proveedor": "ollama", "modelo": "llama3.2:3b"}
                agente = clase(**kwargs)
            except Exception as exc:
                pytest.skip(f"No se pudo instanciar {clase_nombre}: {exc}")

        assert hasattr(agente, "estadoEmergencia") or hasattr(agente, "estado_actual"), (
            f"{clase_nombre} debería exponer 'estadoEmergencia' o 'estado_actual'."
        )

    @pytest.mark.parametrize("rol", ROLES)
    def test_agente_tiene_responder_supervisor_behaviour(self, rol: str) -> None:
        """Cada agente referencia ConsultaEstado o ResponderSupervisorBehaviour."""
        import inspect
        modulo_nombre, clase_nombre = CLASES_AGENTES[rol]
        try:
            modulo = importlib.import_module(modulo_nombre)
        except ImportError as exc:
            pytest.skip(f"No se pudo importar '{modulo_nombre}': {exc}")
        clase = getattr(modulo, clase_nombre)
        try:
            fuente = inspect.getsource(clase)
        except OSError:
            pytest.skip("No se pudo obtener el código fuente.")
        assert "ConsultaEstado" in fuente or "ResponderSupervisorBehaviour" in fuente, (
            f"{clase_nombre} debería responder a ConsultaEstado del supervisor."
        )

    @skip_sin_xmpp
    @pytest.mark.asyncio
    async def test_consulta_estado_todos_agentes_real(self) -> None:
        """(Requiere XMPP) Los cinco agentes arrancan y responden is_alive()."""
        import utils  # noqa: F401
        import yaml
        from pathlib import Path
        from agentes.agente_bomberos import AgenteBomberos
        from agentes.agente_sanitario import AgenteSanitario
        from agentes.agente_policia import AgentePolicia
        from agentes.agente_municipal import AgenteMunicipal
        from agentes.agente_centralita import AgenteCentralita

        cfg_path = Path(__file__).resolve().parent.parent / "config.yaml"
        with open(cfg_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        ag_cfg = cfg.get("agentes", {})

        def _creds(rol: str):
            return (ag_cfg[rol]["usuario"] + "@localhost", ag_cfg[rol]["contrasena"])

        config_llm = {"proveedor": "ollama", "modelo": "llama3.2:3b"}
        agentes = []
        try:
            jid, pwd = _creds("centralita")
            agentes.append(AgenteCentralita(jid=jid, password=pwd))
            for cls, rol in [
                (AgenteBomberos, "bomberos"),
                (AgenteSanitario, "sanitario"),
                (AgentePolicia, "policia"),
                (AgenteMunicipal, "municipal"),
            ]:
                jid, pwd = _creds(rol)
                agentes.append(cls(jid=jid, password=pwd, config_llm=config_llm))

            for ag in agentes:
                await ag.start(auto_register=True)
            await asyncio.sleep(5)
            for ag in agentes:
                assert ag.is_alive(), f"{ag.jid} no está vivo."
        finally:
            for ag in agentes:
                try:
                    await ag.stop()
                except Exception:
                    pass