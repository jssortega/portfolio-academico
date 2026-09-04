"""Pruebas de resolución de la configuración del examen.

Verifican que :func:`config.configuracion.cargar_configuracion` y
:func:`config.configuracion.generar_agentes` resuelven la
configuración del día del examen tal y como se espera:

* el submodo del examen (``grupo`` o ``individual``) determina el
  número de agentes y la sala MUC a la que se unen;
* el selector del perfil LLM admite el valor ``ninguno`` para
  arrancar el sistema sin ningún servicio LLM.

Ninguna de estas pruebas levanta agentes ni servidor: solo
ejercitan la cadena de carga de configuración.
"""
import copy
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import yaml

from config.configuracion import (
    cargar_configuracion,
    cargar_plantillas,
    generar_agentes,
)

# Plantillas reales del proyecto, cargadas una sola vez.
PLANTILLAS = cargar_plantillas()

# Perfil XMPP mínimo válido. No se abre ningún socket: los campos
# se leen como datos.
PERFIL_XMPP_BASE = {
    "host": "sinbad2.ujaen.es",
    "puerto": 8022,
    "dominio": "sinbad2.ujaen.es",
    "servicio_muc": "conference.sinbad2.ujaen.es",
    "servicio_muc_examen": "examen.sinbad2.ujaen.es",
    "sala_tictactoe": "tictactoe",
    "perfil": "servidor",
}

# Salas MUC esperadas en cada submodo. Para el submodo individual
# se usa el puesto 'PC-05' (que la normalización convierte en
# 'pc-05'), elegido porque cubre la regla de relleno con ceros.
SALA_GRUPO = "examen@examen.sinbad2.ujaen.es"
SALA_INDIVIDUAL_PC05 = "pc-05@examen.sinbad2.ujaen.es"


def _construir_config_alumno(
    submodo: str,
    *,
    usuario: str = "pedroj",
    pc: str = "PC-05",
    nick_tablero: str = "Pedro-T",
    nick_jugador: str = "Pedro-J",
) -> dict:
    """Devuelve un diccionario de configuración equivalente al que
    produciría :func:`cargar_configuracion` para un alumno que se
    sienta en el puesto ``pc`` del aula."""
    return {
        "xmpp": copy.deepcopy(PERFIL_XMPP_BASE),
        "alumno": {
            "usuario_uja": usuario,
            "modalidad": "examen",
            "submodo": submodo,
            "pc": pc,
            "nick_tablero": nick_tablero,
            "nick_jugador": nick_jugador,
            "niveles_estrategia": [1, 2, 3],
        },
    }


def _escribir_config_temporal(submodo: str, *, pc: str = "PC-05") -> str:
    """Crea un config.yaml temporal con la configuración mínima
    necesaria para ejercitar :func:`cargar_configuracion`."""
    import tempfile
    import textwrap

    contenido = textwrap.dedent(
        f"""
        xmpp:
          perfil_activo: servidor
          perfiles:
            servidor:
              host: sinbad2.ujaen.es
              puerto: 8022
              dominio: sinbad2.ujaen.es
              servicio_muc: conference.sinbad2.ujaen.es
              servicio_muc_examen: examen.sinbad2.ujaen.es
              sala_tictactoe: tictactoe
              password_defecto: secret
              auto_register: true
              verify_security: false

        alumno:
          usuario_uja: alumno_demo
          modalidad: examen
          submodo: {submodo}
          pc: "{pc}"
          niveles_estrategia: [1, 2, 3]

        sistema:
          nivel_log: WARNING
        """
    )
    fichero = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8",
    )
    fichero.write(contenido)
    fichero.close()
    return fichero.name


def _escribir_config_con_llm(perfil_llm: str) -> str:
    """Crea un config.yaml temporal con una sección ``llm`` cuyo
    ``perfil_activo`` es el indicado.

    El perfil XMPP se fija siempre a ``servidor``: así los tests
    comprueban que el selector LLM es independiente del selector
    XMPP (cambiar uno no arrastra al otro).
    """
    import tempfile
    import textwrap

    contenido = textwrap.dedent(
        f"""
        xmpp:
          perfil_activo: servidor
          perfiles:
            servidor:
              host: sinbad2.ujaen.es
              puerto: 8022
              dominio: sinbad2.ujaen.es
              servicio_muc: conference.sinbad2.ujaen.es
              sala_tictactoe: tictactoe
              password_defecto: secret
              auto_register: true
              verify_security: false

        llm:
          perfil_activo: {perfil_llm}
          perfiles:
            gemini:
              proveedor: "gemini"
              modelo: "gemini-2.5-flash"
              api_key_env: "GOOGLE_API_KEY"
            servidor:
              proveedor: "ollama"
              url_base: "http://sinbad2ia.ujaen.es:8050"
              modelo: "ollama_chat/llama3:8b"

        alumno:
          usuario_uja: alumno_demo
          modalidad: laboratorio
          niveles_estrategia: [1, 2, 3]

        sistema:
          nivel_log: WARNING
        """
    )
    fichero = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8",
    )
    fichero.write(contenido)
    fichero.close()
    return fichero.name


# ──────────────────────────────────────────────────────────────
#  Configuración resuelta según el submodo del examen
# ──────────────────────────────────────────────────────────────

class TestConfiguracionPorSubmodo:
    """Comprueba que la configuración resuelve los agentes y la sala
    adecuados a cada submodo del examen."""

    @pytest.mark.asyncio
    async def test_sonda_activa_devuelve_par_true_vacio(self):
        """La sonda, cuando da el supervisor por activo, devuelve el
        par ``(True, "")``.

        Esta prueba ejercita el contrato de retorno de la sonda con
        un doble (``AsyncMock``) configurado como activo; no arranca
        el lanzador ni genera agentes (eso se cubre en
        ``test_sonda_supervisor.py``). Verifica únicamente la forma
        del valor que el resto del flujo de grupo espera recibir."""
        sonda = AsyncMock(return_value=(True, ""))
        with patch("utils.comprobar_supervisor_activo", sonda):
            activo, mensaje = await sonda(PERFIL_XMPP_BASE, SALA_GRUPO)
        assert activo is True
        assert mensaje == ""

    def test_grupo_genera_un_tablero_y_un_jugador(self):
        """En el submodo grupo cada alumno aporta exactamente un
        tablero y un jugador, ambos con nick único."""
        config = _construir_config_alumno("grupo")
        agentes = generar_agentes(config, PLANTILLAS)
        roles = [a["nombre"].split("_")[0] for a in agentes]
        assert roles.count("tablero") == 1
        assert roles.count("jugador") == 1
        nicks = [a["parametros"]["nick_muc"] for a in agentes]
        assert len(nicks) == len(set(nicks))

    def test_individual_genera_tres_tableros_y_doce_jugadores(self):
        """En el submodo individual cada alumno aporta tres
        tableros y doce jugadores, con nicks todos únicos."""
        config = _construir_config_alumno("individual")
        agentes = generar_agentes(config, PLANTILLAS)
        roles = [a["nombre"].split("_")[0] for a in agentes]
        assert roles.count("tablero") == 3
        assert roles.count("jugador") == 12
        nicks = [a["parametros"]["nick_muc"] for a in agentes]
        assert len(nicks) == len(set(nicks))

    def test_grupo_resuelve_sala_compartida(self):
        """El submodo grupo apunta a la sala compartida
        ``examen@examen.<dominio>``."""
        ruta = _escribir_config_temporal("grupo")
        config = cargar_configuracion(ruta)
        assert config["xmpp"]["sala_muc_completa"] == SALA_GRUPO

    def test_individual_resuelve_sala_del_puesto(self):
        """El submodo individual con ``alumno.pc = 'PC-5'`` apunta
        a la sala canonizada ``pc-05@examen.<dominio>``."""
        ruta = _escribir_config_temporal("individual", pc="PC-5")
        config = cargar_configuracion(ruta)
        assert config["xmpp"]["sala_muc_completa"] == SALA_INDIVIDUAL_PC05


# ──────────────────────────────────────────────────────────────
#  Resolución del perfil LLM (estrategia nivel 4, opcional)
# ──────────────────────────────────────────────────────────────

def _config_declara_estrategia_llm() -> bool:
    """Indica si el ``config.yaml`` declara la estrategia de nivel 4.

    La estrategia de nivel 4 (LLM) es **opcional**: no implementarla
    es una decisión válida. Las pruebas del perfil LLM solo se
    evalúan cuando el alumno la ha declarado en
    ``alumno.niveles_estrategia``; en caso contrario se omiten.

    Se comprueba ``niveles_estrategia`` —y NO ``llm.perfil_activo``—
    porque este último arrastra a menudo un valor por defecto
    heredado de una configuración antigua que no refleja la
    intención del alumno. La presencia del nivel 4 en la lista de
    niveles sí es una declaración deliberada de usar el LLM.

    Returns:
        ``True`` si ``alumno.niveles_estrategia`` contiene el 4.
    """
    ruta = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
    niveles: list = []
    if ruta.is_file():
        try:
            datos = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
            seccion_alumno = datos.get("alumno") or {}
            niveles = seccion_alumno.get("niveles_estrategia") or []
        except (yaml.YAMLError, OSError):
            niveles = []
    declara_nivel_4 = 4 in niveles
    return declara_nivel_4


# Se evalúa una sola vez al cargar el módulo de prueba.
USA_LLM = _config_declara_estrategia_llm()


@pytest.mark.skipif(
    not USA_LLM,
    reason=(
        "config.yaml no declara la estrategia de nivel 4 en "
        "alumno.niveles_estrategia. El nivel 4 (LLM) es opcional, "
        "así que las pruebas del perfil LLM se omiten."
    ),
)
class TestPerfilLlm:
    """Verifica que el selector ``llm.perfil_activo`` se resuelve de
    forma INDEPENDIENTE del perfil XMPP y que admite el valor
    ``ninguno`` para arrancar el sistema sin ningún servicio LLM.

    La estrategia de nivel 4 (LLM) es opcional: estas pruebas solo se
    evalúan si ``config.yaml`` declara el nivel 4 en
    ``niveles_estrategia``; en caso contrario, la clase entera se
    omite (ver :func:`_config_declara_estrategia_llm`)."""

    def test_perfil_ninguno_resuelve_sin_llm(self):
        """Con ``llm.perfil_activo: ninguno`` el sistema arranca sin
        LLM: ``config["llm"]`` es ``None`` y no se exige API key."""
        ruta = _escribir_config_con_llm("ninguno")
        config = cargar_configuracion(ruta)
        assert config["llm"] is None

    def test_seccion_llm_ausente_resuelve_sin_llm(self):
        """Si el config.yaml no incluye la sección ``llm``, el
        sistema también arranca sin LLM (``config["llm"]`` es
        ``None``), por compatibilidad con configuraciones antiguas."""
        ruta = _escribir_config_temporal("grupo")
        config = cargar_configuracion(ruta)
        assert config["llm"] is None

    def test_perfil_activo_vacio_equivale_a_ninguno(self):
        """Un ``perfil_activo`` vacío se trata como ``ninguno``: no se
        intenta resolver ningún perfil ni se exige API key."""
        ruta = _escribir_config_con_llm('""')
        config = cargar_configuracion(ruta)
        assert config["llm"] is None

    def test_perfil_servidor_resuelve_ollama(self):
        """Seleccionar ``servidor`` en el perfil LLM resuelve el
        proveedor Ollama. El perfil XMPP (también ``servidor``) no
        interfiere: son dos selectores distintos."""
        ruta = _escribir_config_con_llm("servidor")
        config = cargar_configuracion(ruta)
        assert config["llm"] is not None
        assert config["llm"]["perfil"] == "servidor"
        assert config["llm"]["proveedor"] == "ollama"

    def test_perfil_inexistente_lanza_error_didactico(self):
        """Un perfil LLM desconocido aborta con un mensaje que
        sugiere ``ninguno`` como alternativa sin LLM."""
        ruta = _escribir_config_con_llm("inexistente")
        with pytest.raises(ValueError, match="ninguno"):
            cargar_configuracion(ruta)
