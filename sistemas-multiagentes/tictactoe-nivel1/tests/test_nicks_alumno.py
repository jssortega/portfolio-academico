"""Pruebas de la generación de nicks MUC para los agentes del alumno.

Verifican que el lanzador del alumno produce un nick único por
agente dentro de la sala MUC, y que dicho nick se deriva del bloque
``alumno`` de ``config.yaml`` con las siguientes reglas:

- Si ``alumno.nick_tablero`` o ``alumno.nick_jugador`` están
  definidos, se usan como nick base del rol correspondiente.
- Si alguno de esos campos está vacío o ausente, se cae a
  ``alumno.usuario_uja``.
- En cualquier caso, la utilidad de generación añade un sufijo
  único por agente (``-NN`` para los tableros, ``-n<L>-NN`` para
  los jugadores) para que dentro de la sala MUC no coincidan dos
  ocupantes con el mismo nick.

No requieren servidor XMPP: todo se calcula en memoria a partir de
los diccionarios de configuración.
"""
import copy

import pytest

from config.configuracion import (
    _calcular_nick_base,
    cargar_plantillas,
    construir_nick_jugador,
    construir_nick_tablero,
    generar_agentes,
)


# Las plantillas reales del proyecto se leen una sola vez por
# eficiencia. Cualquier prueba que necesite mutar parámetros usa
# 'copy.deepcopy' para no contaminar el resto.
PLANTILLAS = cargar_plantillas()


# Perfil XMPP mínimo necesario para que 'generar_agentes' considere
# la configuración válida. No se conecta a ningún servidor: los
# campos se leen como datos, sin abrir socket.
_PERFIL_XMPP = {
    "host": "sinbad2.ujaen.es",
    "puerto": 8022,
    "dominio": "sinbad2.ujaen.es",
    "servicio_muc": "conference.sinbad2.ujaen.es",
    "servicio_muc_examen": "examen.sinbad2.ujaen.es",
    "sala_tictactoe": "tictactoe",
    "perfil": "servidor",
}


def _config_examen_individual(
    usuario: str = "pedroj",
    *,
    nick_tablero: str | None = None,
    nick_jugador: str | None = None,
    niveles: list[int] | None = None,
) -> dict:
    """Construye una configuración del modo examen INDIVIDUAL.

    Genera 3 tableros y 12 jugadores (la combinación que más estira
    la unicidad del nick dentro de un mismo alumno).

    Args:
        usuario: Usuario UJA del alumno.
        nick_tablero: Nick base para los tableros; ``None`` para
            omitir el campo, simulando un alumno que no lo ha
            definido.
        nick_jugador: Nick base para los jugadores; ``None`` para
            omitir el campo.
        niveles: Lista de niveles de estrategia (default: 1, 2, 3).

    Returns:
        Diccionario de configuración apto para
        ``generar_agentes``.
    """
    seccion_alumno = {
        "usuario_uja": usuario,
        "modalidad": "examen",
        "submodo": "individual",
        "pc": "PC-01",
        "niveles_estrategia": niveles or [1, 2, 3],
    }
    if nick_tablero is not None:
        seccion_alumno["nick_tablero"] = nick_tablero
    if nick_jugador is not None:
        seccion_alumno["nick_jugador"] = nick_jugador
    return {
        "xmpp": copy.deepcopy(_PERFIL_XMPP),
        "alumno": seccion_alumno,
    }


class TestCalcularNickBase:
    """Verifica la regla de elección del nick base por rol."""

    def test_usa_nick_tablero_si_esta_definido(self):
        """Si ``alumno.nick_tablero`` no está vacío, se usa."""
        seccion = {"usuario_uja": "pedroj", "nick_tablero": "PedroT"}
        assert _calcular_nick_base(seccion, "tablero") == "PedroT"

    def test_usa_nick_jugador_si_esta_definido(self):
        """Si ``alumno.nick_jugador`` no está vacío, se usa."""
        seccion = {"usuario_uja": "pedroj", "nick_jugador": "PedroJ"}
        assert _calcular_nick_base(seccion, "jugador") == "PedroJ"

    def test_recorta_espacios_del_nick(self):
        """Los espacios del extremo no deben acabar en el nick: el
        servidor MUC los aceptaría pero el resultado visual sería
        confuso en el panel del supervisor."""
        seccion = {"usuario_uja": "pedroj", "nick_tablero": "  PedroT  "}
        assert _calcular_nick_base(seccion, "tablero") == "PedroT"

    def test_cae_a_usuario_uja_cuando_nick_esta_vacio(self):
        """Si el campo del nick existe pero está vacío, se usa el
        usuario UJA. Es el caso del config.yaml de plantilla."""
        seccion = {"usuario_uja": "alumno_demo", "nick_tablero": ""}
        assert _calcular_nick_base(seccion, "tablero") == "alumno_demo"

    def test_cae_a_usuario_uja_cuando_nick_esta_ausente(self):
        """Si el campo del nick no aparece, se usa el usuario UJA.
        Cubre la compatibilidad con config.yaml antiguos."""
        seccion = {"usuario_uja": "alumno_demo"}
        assert _calcular_nick_base(seccion, "jugador") == "alumno_demo"

    def test_independencia_entre_roles(self):
        """El nick de tablero no debe afectar al de jugador y
        viceversa: cada rol tiene su propia regla de elección."""
        seccion = {
            "usuario_uja": "alumno_x",
            "nick_tablero": "T_alumno",
        }
        assert _calcular_nick_base(seccion, "tablero") == "T_alumno"
        assert _calcular_nick_base(seccion, "jugador") == "alumno_x"


class TestConstruirNickTablero:
    """Verifica la composición del nick definitivo de un tablero."""

    def test_anade_sufijo_indice_a_partir_de_uno(self):
        """El índice ``0`` produce ``-01`` para que el alumno y el
        profesor lean el orden empezando en 1. La factoría toma el
        ``nick_base`` tal cual y le añade exclusivamente el sufijo
        de orden: no antepone ningún prefijo de rol al nick MUC. El
        rol se reconoce por el localpart del JID, que sí lleva el
        prefijo ``tablero_`` / ``jugador_`` (esa parte se construye
        en :func:`generar_agentes`)."""
        assert construir_nick_tablero("Pedro", 0) == "Pedro-01"
        assert construir_nick_tablero("Pedro", 1) == "Pedro-02"

    def test_rellena_con_cero_para_un_digito(self):
        """Mantiene la anchura mínima de dos dígitos para que las
        columnas se alineen visualmente en el panel."""
        assert construir_nick_tablero("Pedro", 8) == "Pedro-09"

    def test_admite_dos_digitos_sin_truncar(self):
        """El rellenado mínimo no debe limitar el número máximo."""
        assert construir_nick_tablero("Pedro", 99) == "Pedro-100"


class TestConstruirNickJugador:
    """Verifica la composición del nick definitivo de un jugador."""

    def test_incluye_nivel_y_indice(self):
        """El sufijo es ``-n<nivel>-NN`` para que el panel del
        supervisor distinga estrategias de un vistazo. La factoría
        no antepone el prefijo de rol al nick MUC: el rol del agente
        se reconoce por el localpart del JID, no por el nick."""
        assert (
            construir_nick_jugador("Pedro", 2, 0) == "Pedro-n2-01"
        )
        assert (
            construir_nick_jugador("Pedro", 3, 11) == "Pedro-n3-12"
        )

    def test_independiente_del_indice_de_tablero(self):
        """Los índices de tablero y jugador son contadores
        distintos: dos agentes con el mismo índice numérico deben
        producir nicks distintos por su rol."""
        nick_t = construir_nick_tablero("Pedro", 0)
        nick_j = construir_nick_jugador("Pedro", 1, 0)
        assert nick_t != nick_j


class TestGenerarAgentesConNick:
    """Verifica que ``generar_agentes`` propaga el nick a cada agente
    en ``parametros["nick_muc"]`` y que dichos nicks son únicos."""

    def test_inyecta_nick_muc_en_cada_agente(self):
        """Todos los agentes generados deben llevar el campo
        ``nick_muc`` en sus parámetros, sin excepción."""
        config = _config_examen_individual()
        agentes = generar_agentes(config, PLANTILLAS)
        for agente in agentes:
            assert "nick_muc" in agente["parametros"]
            assert agente["parametros"]["nick_muc"]

    def test_nicks_unicos_dentro_de_la_sala(self):
        """Las 15 instancias del examen individual deben tener nicks
        distintos entre sí. Si dos coincidieran, el servidor MUC
        rechazaría al segundo con la condición ``conflict``."""
        config = _config_examen_individual()
        agentes = generar_agentes(config, PLANTILLAS)
        nicks = [a["parametros"]["nick_muc"] for a in agentes]
        assert len(nicks) == len(set(nicks))

    def test_usa_nick_personalizado_cuando_se_define(self):
        """Los nicks generados parten del ``nick_base`` que el
        alumno haya indicado en cada rol y le añaden únicamente el
        sufijo de orden: la factoría no antepone el prefijo de rol
        al nick MUC. El rol se reconoce por el localpart del JID
        (``agente["nombre"]``), que sí mantiene el prefijo
        ``tablero_`` / ``jugador_``."""
        config = _config_examen_individual(
            nick_tablero="Pedro-T",
            nick_jugador="Pedro-J",
        )
        agentes = generar_agentes(config, PLANTILLAS)
        for agente in agentes:
            nick = agente["parametros"]["nick_muc"]
            if agente["nombre"].startswith("tablero_"):
                assert nick.startswith("Pedro-T-")
            elif agente["nombre"].startswith("jugador_"):
                assert nick.startswith("Pedro-J-n")

    def test_cae_a_usuario_uja_cuando_no_hay_nick(self):
        """Sin nicks personalizados, el usuario UJA es el nick
        base. Es el caso del config.yaml por defecto del alumno
        que no quiere personalizar."""
        config = _config_examen_individual(
            usuario="alumno_demo",
            nick_tablero="",
            nick_jugador=None,
        )
        agentes = generar_agentes(config, PLANTILLAS)
        for agente in agentes:
            nick = agente["parametros"]["nick_muc"]
            # Sin personalizar, el nick base es el ``usuario_uja``.
            # La factoría NO antepone el prefijo de rol al nick MUC;
            # el rol se reconoce por el localpart del JID.
            if agente["nombre"].startswith("tablero_"):
                assert nick.startswith("alumno_demo-")
            elif agente["nombre"].startswith("jugador_"):
                assert nick.startswith("alumno_demo-")

    def test_los_tableros_no_repiten_nick_entre_ellos(self):
        """Los 3 tableros del examen individual deben llevar
        sufijos -01, -02 y -03 en orden sobre el mismo ``nick_base``
        (la factoría no antepone prefijo de rol al nick MUC)."""
        config = _config_examen_individual(nick_tablero="Pedro-T")
        agentes = generar_agentes(config, PLANTILLAS)
        nicks_tableros = [
            a["parametros"]["nick_muc"]
            for a in agentes if a["nombre"].startswith("tablero_")
        ]
        assert nicks_tableros == [
            "Pedro-T-01",
            "Pedro-T-02",
            "Pedro-T-03",
        ]

    def test_los_jugadores_distinguen_nivel_e_indice(self):
        """Los 12 jugadores se reparten entre los 3 niveles con
        cuatro por nivel y nicks ``<base>-nL-NN`` (sin prefijo de
        rol; el rol se reconoce por el localpart del JID)."""
        config = _config_examen_individual(nick_jugador="Pedro-J")
        agentes = generar_agentes(config, PLANTILLAS)
        nicks_jugadores = [
            a["parametros"]["nick_muc"]
            for a in agentes if a["nombre"].startswith("jugador_")
        ]
        # Niveles 1, 2 y 3 con cuatro jugadores cada uno.
        esperados = [
            f"Pedro-J-n{nivel}-{i:02d}"
            for nivel in (1, 2, 3)
            for i in range(1, 5)
        ]
        assert nicks_jugadores == esperados


class TestGenerarAgentesGrupo:
    """En el submodo ``grupo`` solo se crea un tablero y un jugador,
    pero la regla del nick debe seguir aplicándose."""

    def test_grupo_aplica_el_nick(self):
        """El único agente de cada rol también recibe el sufijo de
        orden, manteniendo la misma convención en todos los modos.
        La factoría no antepone el prefijo de rol al nick MUC: el
        rol se reconoce por el localpart del JID."""
        config = {
            "xmpp": copy.deepcopy(_PERFIL_XMPP),
            "alumno": {
                "usuario_uja": "alumno_x",
                "modalidad": "examen",
                "submodo": "grupo",
                "nick_tablero": "AlumnoX-T",
                "nick_jugador": "AlumnoX-J",
                "niveles_estrategia": [2],
            },
        }
        agentes = generar_agentes(config, PLANTILLAS)
        nicks = sorted(a["parametros"]["nick_muc"] for a in agentes)
        assert nicks == [
            "AlumnoX-J-n2-01",
            "AlumnoX-T-01",
        ]
