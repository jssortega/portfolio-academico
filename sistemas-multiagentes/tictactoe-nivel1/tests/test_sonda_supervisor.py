"""Pruebas de la sonda que comprueba si el supervisor del examen
está activo antes de crear los agentes del alumno.

Verifican el comportamiento de :func:`utils.comprobar_supervisor_activo`
y la reacción de ``main.arrancar_sistema`` cuando la sonda concluye
que la sala MUC del examen NO existe:

- Cuando la consulta disco#info se resuelve sin error, la sonda
  devuelve ``(True, "")`` y el lanzador continúa.
- Cuando la consulta lanza un error con un ``iq`` que incluye
  ``condition`` y ``text`` (caso del módulo
  ``mod_examen_friendly_error`` del Prosody), la sonda devuelve
  ``(False, mensaje)`` con el motivo extraído.
- Cuando la consulta se queda sin respuesta, la sonda devuelve
  ``(False, "sin respuesta ...")`` con la causa explícita.
- Cuando la sonda devuelve ``False`` desde ``main.arrancar_sistema``
  con modalidad ``examen``, el lanzador llama a ``sys.exit`` con
  el código de salida específico y no llega a generar agentes.

Los tests sustituyen las primitivas de utils que tocan XMPP (``crear_agente``
y ``arrancar_agente``) por mocks ligeros: no se conecta con ningún
servidor real.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import main as lanzador_alumno
import utils


# Perfil XMPP mínimo válido para que las funciones lo acepten. No
# se abre socket en ninguna prueba: los datos solo se leen.
PERFIL_XMPP = {
    "host": "sinbad2.ujaen.es",
    "puerto": 8022,
    "dominio": "sinbad2.ujaen.es",
    "servicio_muc_examen": "examen.sinbad2.ujaen.es",
    "auto_register": True,
    "password_defecto": "secret",
    "verify_security": False,
    "perfil": "servidor",
}

SALA_EXAMEN = "examen@examen.sinbad2.ujaen.es"


def _construir_iq_con_error(condicion: str, texto: str) -> MagicMock:
    """Construye un IQ falso con la forma que slixmpp usa cuando el
    servidor responde con un error a la consulta disco#info.

    ``IqError.iq["error"]["condition"]`` y ``["text"]`` son las
    rutas reales del wrapper de slixmpp. El mock las imita para
    que ``_extraer_error_disco`` extraiga la información sin
    cambios.
    """
    iq = MagicMock()
    iq.__getitem__.side_effect = lambda clave: (
        {
            "error": {
                "condition": condicion,
                "text": texto,
            },
        }[clave]
    )
    return iq


def _crear_agente_sonda_mock(get_info_async_mock: AsyncMock) -> MagicMock:
    """Construye un agente falso con la API mínima que la sonda usa.

    Reproduce ``agente.client["xep_0030"].get_info`` como el
    AsyncMock recibido (sea para devolver éxito o lanzar excepción)
    y ``agente.stop`` como AsyncMock que registra la limpieza.
    """
    agente = MagicMock()
    agente.client = MagicMock()
    agente.client.__getitem__.return_value = MagicMock(
        get_info=get_info_async_mock,
    )
    agente.stop = AsyncMock()
    return agente


class TestComprobarSupervisorActivo:
    """Verifica la sonda :func:`utils.comprobar_supervisor_activo` en
    sus cuatro situaciones relevantes: respuesta correcta del
    servidor, error de IQ con texto explicativo, ausencia de
    respuesta (timeout) y robustez ante un fallo del ``stop`` del
    agente sonda."""

    @pytest.mark.asyncio
    async def test_devuelve_true_cuando_disco_responde(self):
        """Si la sala MUC existe, ``get_info`` se resuelve sin
        excepción y la sonda devuelve ``(True, "")``."""
        get_info_ok = AsyncMock(return_value=MagicMock())
        agente = _crear_agente_sonda_mock(get_info_ok)

        with patch.object(utils, "crear_agente", return_value=agente), \
                patch.object(
                    utils, "arrancar_agente", new_callable=AsyncMock,
                ):
            activo, mensaje = await utils.comprobar_supervisor_activo(
                PERFIL_XMPP, SALA_EXAMEN,
            )

        assert activo is True
        assert mensaje == ""
        # La sonda debe siempre apagar al agente temporal.
        agente.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_extrae_condicion_y_texto_del_servidor(self):
        """Si el servidor responde con error, la sonda devuelve
        ``(False, mensaje)`` con la condición XMPP y el texto
        explicativo que el módulo ``mod_examen_friendly_error``
        haya añadido."""

        class _ErrorIqFalso(Exception):
            """Imitación de slixmpp.exceptions.IqError sin acoplar
            al tipo concreto: lo importante es la presencia del
            atributo ``iq``."""

            def __init__(self, iq):
                super().__init__("error iq")
                self.iq = iq

        iq_error = _construir_iq_con_error(
            condicion="item-not-found",
            texto=(
                "[Examen] El supervisor todavía no ha creado la "
                "sala del examen. Espera al profesor."
            ),
        )
        get_info_falla = AsyncMock(side_effect=_ErrorIqFalso(iq_error))
        agente = _crear_agente_sonda_mock(get_info_falla)

        with patch.object(utils, "crear_agente", return_value=agente), \
                patch.object(
                    utils, "arrancar_agente", new_callable=AsyncMock,
                ):
            activo, mensaje = await utils.comprobar_supervisor_activo(
                PERFIL_XMPP, SALA_EXAMEN,
            )

        assert activo is False
        assert "item-not-found" in mensaje
        assert "[Examen]" in mensaje
        agente.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_informa_de_la_ausencia_de_respuesta(self):
        """Si la consulta disco#info no responde en el plazo
        indicado, la sonda devuelve ``(False, "sin respuesta ...")``."""

        async def _get_info_lento(*_args, **_kwargs):
            await asyncio.sleep(10)

        get_info_lento = AsyncMock(side_effect=_get_info_lento)
        agente = _crear_agente_sonda_mock(get_info_lento)

        with patch.object(utils, "crear_agente", return_value=agente), \
                patch.object(
                    utils, "arrancar_agente", new_callable=AsyncMock,
                ):
            activo, mensaje = await utils.comprobar_supervisor_activo(
                PERFIL_XMPP, SALA_EXAMEN, timeout=0.1,
            )

        assert activo is False
        assert "sin respuesta" in mensaje
        agente.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_propaga_el_fallo_de_stop(self):
        """Una excepción de ``stop`` no debe propagarse: la sonda
        debe devolver siempre la pareja ``(activo, mensaje)`` para
        que el lanzador pueda decidir."""
        get_info_ok = AsyncMock(return_value=MagicMock())
        agente = _crear_agente_sonda_mock(get_info_ok)
        agente.stop = AsyncMock(side_effect=RuntimeError("fallo de stop"))

        with patch.object(utils, "crear_agente", return_value=agente), \
                patch.object(
                    utils, "arrancar_agente", new_callable=AsyncMock,
                ):
            activo, mensaje = await utils.comprobar_supervisor_activo(
                PERFIL_XMPP, SALA_EXAMEN,
            )

        assert activo is True
        assert mensaje == ""


class TestSondaIntegradaEnMain:
    """Verifica la integración de la sonda en ``main.arrancar_sistema``:
    debe invocarse en modalidad ``examen`` y abortar el lanzador con
    el código adecuado si la sala no existe, y debe omitirse fuera
    de la modalidad examen."""

    @pytest.mark.asyncio
    async def test_aborta_si_supervisor_no_esta_activo(self):
        """En modalidad ``examen``, si la sonda devuelve
        ``False``, el lanzador llama a ``sys.exit`` con
        ``CODIGO_SALIDA_SUPERVISOR_INACTIVO`` y NO crea ningún
        agente."""
        # Configuración mínima válida (modalidad examen, submodo
        # grupo) que ``arrancar_sistema`` puede consumir sin lanzar
        # agentes.
        config_falsa = {
            "xmpp": {
                **PERFIL_XMPP,
                "sala_muc_completa": SALA_EXAMEN,
                "servicio_muc": "examen.sinbad2.ujaen.es",
                "sala_tictactoe": "examen",
            },
            "llm": None,
            "sistema": {"nivel_log": "WARNING"},
            "alumno": {
                "usuario_uja": "alumno_demo",
                "modalidad": "examen",
                "submodo": "grupo",
                "niveles_estrategia": [1],
            },
        }
        sonda_falsa = AsyncMock(
            return_value=(
                False, "item-not-found. [Examen] sin supervisor",
            ),
        )

        with patch.object(
            lanzador_alumno, "cargar_configuracion",
            return_value=config_falsa,
        ), patch.object(
            lanzador_alumno, "comprobar_supervisor_activo", sonda_falsa,
        ), pytest.raises(SystemExit) as info:
            await lanzador_alumno.arrancar_sistema(
                "irrelevante.yaml",
                "irrelevante_agents.yaml",
                "irrelevante_torneos.yaml",
            )

        sonda_falsa.assert_awaited_once_with(
            config_falsa["xmpp"], SALA_EXAMEN,
        )
        assert info.value.code == (
            lanzador_alumno.CODIGO_SALIDA_SUPERVISOR_INACTIVO
        )

    @pytest.mark.asyncio
    async def test_no_se_lanza_fuera_del_modo_examen(self):
        """Cuando la modalidad no es ``examen``, la sonda no se
        invoca: el modo laboratorio no depende del supervisor del
        profesor."""
        config_lab = {
            "xmpp": {
                **PERFIL_XMPP,
                "sala_muc_completa": (
                    "tictactoe@conference.sinbad2.ujaen.es"
                ),
                "servicio_muc": "conference.sinbad2.ujaen.es",
                "sala_tictactoe": "tictactoe",
            },
            "llm": None,
            "sistema": {"nivel_log": "WARNING"},
            "alumno": {
                "usuario_uja": "alumno_demo",
                "modalidad": "laboratorio",
                "niveles_estrategia": [1],
            },
        }
        sonda_falsa = AsyncMock(
            return_value=(False, "no debería llamarse"),
        )

        # Cortocircuitamos las funciones que ya tienen sus propias
        # pruebas para que el test se centre en una sola condición.
        plantillas_vacias = {
            "modalidades": {"laboratorio": {
                "num_tableros": 0, "num_jugadores": 0,
            }},
            "plantilla_tablero": {
                "clase": "X", "modulo": "y", "parametros": {},
            },
            "plantilla_jugador": {
                "clase": "X", "modulo": "y", "parametros": {},
            },
        }

        with patch.object(
            lanzador_alumno, "cargar_configuracion",
            return_value=config_lab,
        ), patch.object(
            lanzador_alumno, "comprobar_supervisor_activo", sonda_falsa,
        ), patch.object(
            lanzador_alumno, "cargar_plantillas",
            return_value=plantillas_vacias,
        ), patch.object(
            lanzador_alumno, "cargar_torneos", return_value=[],
        ), patch.object(
            lanzador_alumno, "crear_salas_torneos",
            new_callable=AsyncMock, return_value={},
        ):
            # Sin agentes generados, ``arrancar_sistema`` registra
            # una advertencia y retorna sin abrir el bucle de
            # espera. Si la sonda se invocara aquí, el test
            # fallaría por ``assert_not_awaited``.
            await lanzador_alumno.arrancar_sistema(
                "irrelevante.yaml",
                "irrelevante_agents.yaml",
                "irrelevante_torneos.yaml",
            )

        sonda_falsa.assert_not_awaited()
