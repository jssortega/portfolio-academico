"""Pruebas de la generación automática de agentes por modalidad.

Verifican que ``config.configuracion.generar_agentes`` produce el
conjunto correcto de tableros y jugadores para cada combinación de
``alumno.modalidad`` y ``alumno.submodo``, y que el perfil XMPP queda
configurado para apuntar al componente y la sala que corresponden:

- ``laboratorio``                 → 4 tableros + 12 jugadores en el
                                    componente general.
- ``torneo``                      → 1 tablero  +  1 jugador  en el
                                    componente general.
- ``examen`` + ``grupo``          → 1 tablero  +  1 jugador  en
                                    ``examen@examen.<dominio>``.
- ``examen`` + ``individual``     → 3 tableros + 12 jugadores en
                                    ``<pc>@examen.<dominio>``.

Adicionalmente se verifica que las dos reglas de error explícitas
funcionan:

- ``submodo=individual`` sin ``alumno.pc`` lanza ``ValueError``.
- ``submodo`` con un valor no reconocido lanza ``ValueError``.

Y que la distribución de niveles de estrategia entre jugadores es
uniforme cuando el modo lo requiere (laboratorio y examen
individual) y se queda con el primer nivel cuando solo hay un
jugador (torneo y examen grupo).
"""
import copy

import pytest

from config.configuracion import (
    _aplicar_modo_examen_a_perfil,
    _resolver_clave_modalidad,
    cargar_plantillas,
    generar_agentes,
)


# ── Plantillas reales del proyecto, cargadas una sola vez ──────
PLANTILLAS = cargar_plantillas()

# ── Helpers ────────────────────────────────────────────────────

PERFIL_BASE = {
    "host": "sinbad2.ujaen.es",
    "puerto": 8022,
    "dominio": "sinbad2.ujaen.es",
    "servicio_muc": "conference.sinbad2.ujaen.es",
    "servicio_muc_examen": "examen.sinbad2.ujaen.es",
    "sala_tictactoe": "tictactoe",
    "perfil": "servidor",
}


def _construir_config(
    modalidad: str,
    *,
    submodo: str | None = None,
    pc: str | None = None,
    niveles: list[int] | None = None,
    usuario: str = "alumno_demo",
) -> dict:
    """Construye un dict 'config' equivalente al que devolvería
    ``cargar_configuracion`` para los parámetros indicados.

    Aplica también ``_aplicar_modo_examen_a_perfil`` para que el
    perfil XMPP refleje los cambios derivados de la modalidad,
    igual que hace ``cargar_configuracion``.
    """
    config = {
        "xmpp": copy.deepcopy(PERFIL_BASE),
        "alumno": {
            "usuario_uja": usuario,
            "modalidad": modalidad,
            "niveles_estrategia": niveles or [1, 2, 3],
        },
    }
    if submodo is not None:
        config["alumno"]["submodo"] = submodo
    if pc is not None:
        config["alumno"]["pc"] = pc

    _aplicar_modo_examen_a_perfil(config["xmpp"], config["alumno"])
    return config


def _contar(agentes: list[dict], prefijo: str) -> int:
    """Cuenta agentes cuyo nombre empieza por ``prefijo_``."""
    return sum(1 for a in agentes if a["nombre"].startswith(f"{prefijo}_"))


# ═══════════════════════════════════════════════════════════════════
#  Modalidad LABORATORIO — 4 tableros + 12 jugadores
# ═══════════════════════════════════════════════════════════════════

class TestModalidadLaboratorio:
    """En laboratorio se generan 4 tableros y 12 jugadores; los
    jugadores se reparten uniformemente entre los niveles
    indicados."""

    def test_genera_4_tableros_y_12_jugadores(self):
        config = _construir_config("laboratorio")
        agentes = generar_agentes(config, PLANTILLAS)
        assert _contar(agentes, "tablero") == 4
        assert _contar(agentes, "jugador") == 12

    def test_jugadores_se_reparten_uniformemente_entre_3_niveles(self):
        config = _construir_config(
            "laboratorio", niveles=[1, 2, 3],
        )
        agentes = generar_agentes(config, PLANTILLAS)
        # 12 jugadores entre 3 niveles → 4 jugadores por nivel
        for nivel in (1, 2, 3):
            jugadores_nivel = [
                a for a in agentes
                if a["nombre"].startswith(f"jugador_alumno_demo_n{nivel}_")
            ]
            assert len(jugadores_nivel) == 4, (
                f"Se esperaban 4 jugadores con nivel {nivel}, "
                f"se encontraron {len(jugadores_nivel)}"
            )

    def test_no_redirige_servicio_muc(self):
        """Laboratorio no modifica el componente MUC del perfil."""
        config = _construir_config("laboratorio")
        assert config["xmpp"]["servicio_muc"] == "conference.sinbad2.ujaen.es"
        assert config["xmpp"]["sala_tictactoe"] == "tictactoe"


# ═══════════════════════════════════════════════════════════════════
#  Modalidad TORNEO — 1 tablero + 1 jugador con primer nivel
# ═══════════════════════════════════════════════════════════════════

class TestModalidadTorneo:
    """En torneo se genera un único tablero y un único jugador
    (con el primer nivel de la lista)."""

    def test_genera_1_tablero_y_1_jugador(self):
        config = _construir_config("torneo")
        agentes = generar_agentes(config, PLANTILLAS)
        assert _contar(agentes, "tablero") == 1
        assert _contar(agentes, "jugador") == 1

    def test_jugador_unico_usa_primer_nivel_de_la_lista(self):
        config = _construir_config("torneo", niveles=[3, 1, 2])
        agentes = generar_agentes(config, PLANTILLAS)
        jugador = next(
            a for a in agentes if a["nombre"].startswith("jugador_")
        )
        # El nombre incluye el sufijo 'n<nivel>' antes del índice.
        assert "_n3_" in jugador["nombre"]
        assert jugador["parametros"]["nivel_estrategia"] == 3

    def test_no_redirige_servicio_muc(self):
        config = _construir_config("torneo")
        assert config["xmpp"]["servicio_muc"] == "conference.sinbad2.ujaen.es"
        assert config["xmpp"]["sala_tictactoe"] == "tictactoe"


# ═══════════════════════════════════════════════════════════════════
#  Modalidad EXAMEN — submodo GRUPO — 1+1 en sala 'examen'
# ═══════════════════════════════════════════════════════════════════

class TestModalidadExamenGrupo:
    """En 'examen' + 'grupo' la topología es 1+1, igual que torneo,
    pero la sala es 'examen' en el componente dedicado del examen."""

    def test_genera_1_tablero_y_1_jugador(self):
        config = _construir_config("examen", submodo="grupo")
        agentes = generar_agentes(config, PLANTILLAS)
        assert _contar(agentes, "tablero") == 1
        assert _contar(agentes, "jugador") == 1

    def test_redirige_servicio_muc_al_componente_dedicado(self):
        config = _construir_config("examen", submodo="grupo")
        assert config["xmpp"]["servicio_muc"] == "examen.sinbad2.ujaen.es"

    def test_apunta_a_sala_local_examen(self):
        config = _construir_config("examen", submodo="grupo")
        assert config["xmpp"]["sala_tictactoe"] == "examen"

    def test_jugador_unico_usa_primer_nivel_de_la_lista(self):
        config = _construir_config(
            "examen", submodo="grupo", niveles=[2, 1, 3],
        )
        agentes = generar_agentes(config, PLANTILLAS)
        jugador = next(
            a for a in agentes if a["nombre"].startswith("jugador_")
        )
        assert "_n2_" in jugador["nombre"]

    def test_clave_resuelta_es_examen_grupo(self):
        config = _construir_config("examen", submodo="grupo")
        assert _resolver_clave_modalidad(config["alumno"]) == "examen_grupo"


# ═══════════════════════════════════════════════════════════════════
#  Modalidad EXAMEN — submodo INDIVIDUAL — 3+12 en sala PC-NN
# ═══════════════════════════════════════════════════════════════════

class TestModalidadExamenIndividual:
    """En 'examen' + 'individual' la topología es 3 tableros + 12
    jugadores y la sala es la asociada al puesto del aula."""

    def test_genera_3_tableros_y_12_jugadores(self):
        config = _construir_config(
            "examen", submodo="individual", pc="PC-05",
        )
        agentes = generar_agentes(config, PLANTILLAS)
        assert _contar(agentes, "tablero") == 3
        assert _contar(agentes, "jugador") == 12

    def test_redirige_servicio_muc_al_componente_dedicado(self):
        config = _construir_config(
            "examen", submodo="individual", pc="PC-05",
        )
        assert config["xmpp"]["servicio_muc"] == "examen.sinbad2.ujaen.es"

    def test_apunta_a_sala_pc_del_alumno(self):
        """La sala local debe ser el valor de ``alumno.pc`` canonizado
        con la forma común (``normalizar_nombre_sala``): así coincide
        con la sala que crea el supervisor."""
        config = _construir_config(
            "examen", submodo="individual", pc="PC-17",
        )
        assert config["xmpp"]["sala_tictactoe"] == "pc-17"

    def test_jid_completo_apunta_a_pc_del_alumno(self):
        config = _construir_config(
            "examen", submodo="individual", pc="PC-23",
        )
        sala_jid = (
            f"{config['xmpp']['sala_tictactoe']}@"
            f"{config['xmpp']['servicio_muc']}"
        )
        assert sala_jid == "pc-23@examen.sinbad2.ujaen.es"

    def test_jugadores_se_reparten_uniformemente_entre_3_niveles(self):
        config = _construir_config(
            "examen", submodo="individual", pc="PC-01",
            niveles=[1, 2, 3],
        )
        agentes = generar_agentes(config, PLANTILLAS)
        # 12 jugadores entre 3 niveles → 4 jugadores por nivel,
        # como en laboratorio.
        for nivel in (1, 2, 3):
            jugadores_nivel = [
                a for a in agentes
                if a["nombre"].startswith(f"jugador_alumno_demo_n{nivel}_")
            ]
            assert len(jugadores_nivel) == 4

    def test_clave_resuelta_es_examen_individual(self):
        config = _construir_config(
            "examen", submodo="individual", pc="PC-02",
        )
        assert _resolver_clave_modalidad(config["alumno"]) == "examen_individual"

    def test_pc_se_canoniza_a_la_forma_comun(self):
        """``alumno.pc`` se canoniza con ``normalizar_nombre_sala``,
        la forma común que también usa el supervisor. Distintas formas
        de escribir el mismo puesto producen el mismo nombre de sala,
        de modo que el alumno no es rechazado por el servidor por una
        discrepancia de escritura en su ``config.yaml``."""
        for pc in ("PC-05", "pc-05", "pc5", "PC_5", " pc 5 "):
            config = _construir_config(
                "examen", submodo="individual", pc=pc,
            )
            assert config["xmpp"]["sala_tictactoe"] == "pc-05", (
                f"El puesto escrito como '{pc}' debería canonizar a "
                f"'pc-05'"
            )

    def test_pc_admite_numeracion_de_tres_cifras(self):
        """La canonización conserva los puestos con tres o más cifras
        (por ejemplo ``PC-100``); solo rellena con cero los de una."""
        config = _construir_config(
            "examen", submodo="individual", pc="PC-100",
        )
        assert config["xmpp"]["sala_tictactoe"] == "pc-100"


# ═══════════════════════════════════════════════════════════════════
#  Casos de error explícitos
# ═══════════════════════════════════════════════════════════════════

class TestValidacionEntradas:
    """El generador rechaza configuraciones incompatibles con un
    mensaje útil para el alumno."""

    def test_examen_individual_sin_pc_lanza_value_error(self):
        with pytest.raises(ValueError, match="alumno.pc"):
            _construir_config("examen", submodo="individual", pc="")

    def test_examen_submodo_desconocido_lanza_value_error(self):
        with pytest.raises(ValueError, match="submodo"):
            _construir_config("examen", submodo="pareja", pc="PC-01")

    def test_modalidad_sin_entrada_en_agents_yaml_lanza_value_error(self):
        """Si por error el alumno escribe una modalidad inexistente,
        el generador debe avisar con la lista de modalidades
        disponibles."""
        config = _construir_config("torneo")  # base válida
        config["alumno"]["modalidad"] = "ronda_extra"  # desconocida
        with pytest.raises(ValueError, match="Modalidades disponibles"):
            generar_agentes(config, PLANTILLAS)

    def test_falta_usuario_uja_lanza_value_error(self):
        config = _construir_config("torneo", usuario="")
        with pytest.raises(ValueError, match="usuario_uja"):
            generar_agentes(config, PLANTILLAS)


# ═══════════════════════════════════════════════════════════════════
#  Cobertura de la cabecera de ficheros agents.yaml
# ═══════════════════════════════════════════════════════════════════

class TestPlantillasYaml:
    """Verifica la coherencia entre los modos esperados por la
    documentación y los efectivamente declarados en agents.yaml."""

    def test_agents_yaml_declara_los_cuatro_modos(self):
        modalidades = PLANTILLAS["modalidades"]
        for clave in ("laboratorio", "torneo", "examen_grupo", "examen_individual"):
            assert clave in modalidades, (
                f"Falta '{clave}' en config/agents.yaml"
            )

    def test_examen_individual_declara_3_tableros_y_12_jugadores(self):
        cant = PLANTILLAS["modalidades"]["examen_individual"]
        assert cant["num_tableros"] == 3
        assert cant["num_jugadores"] == 12

    def test_examen_grupo_declara_1_tablero_y_1_jugador(self):
        cant = PLANTILLAS["modalidades"]["examen_grupo"]
        assert cant["num_tableros"] == 1
        assert cant["num_jugadores"] == 1
