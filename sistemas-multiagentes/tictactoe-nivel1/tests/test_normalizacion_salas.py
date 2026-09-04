"""Pruebas unitarias de la canonización de nombres de sala MUC.

``normalizar_nombre_sala`` es la función común que usan tanto los
agentes del alumno como el Agente Supervisor del profesor para
resolver el nombre de la sala MUC. Estas pruebas verifican que las
distintas formas en que un nombre de sala puede escribirse en un
fichero de configuración —mayúsculas, espacios, separadores, ceros a
la izquierda— se canonizan todas a una misma forma común. Así, escriba
el alumno ``PC-5``, ``pc-05`` o ``PC_5`` en su ``config.yaml``, su
agente construye exactamente el mismo JID que el supervisor usó para
crear la sala, y el servidor no lo rechaza por una discrepancia de
escritura en la configuración.
"""
import pytest

from config.configuracion import normalizar_nombre_sala


class TestCanonizacionPuestos:
    """Las distintas formas de escribir un mismo puesto del aula se
    canonizan todas a la forma común ``pc-NN``."""

    # Cada grupo reúne formas distintas de escribir el MISMO puesto;
    # todas deben canonizarse al valor esperado.
    @pytest.mark.parametrize(
        "variantes, esperado",
        [
            (
                ["PC-05", "pc-05", "Pc-05", "pc05", "PC-5", "pc-5",
                 "PC_05", "PC_5", "pc 5", " PC-05 ", "  pc5  ",
                 "pc-005"],
                "pc-05",
            ),
            (
                ["PC-30", "pc-30", "pc30", "PC_30", "pc 30", " pc-30 "],
                "pc-30",
            ),
            (
                ["PC-1", "pc1", "PC-01", "pc-001", " pc-1 ", "PC_1"],
                "pc-01",
            ),
        ],
    )
    def test_variantes_de_puesto_canonizan_a_forma_comun(
        self, variantes, esperado,
    ):
        """Todas las formas de escribir un puesto producen el mismo
        nombre canónico ``pc-NN``."""
        obtenidos = {normalizar_nombre_sala(v) for v in variantes}
        assert obtenidos == {esperado}, (
            f"Las variantes {variantes} deberían canonizar todas a "
            f"'{esperado}', pero se obtuvo {obtenidos}"
        )

    @pytest.mark.parametrize(
        "nombre, esperado",
        [
            ("PC-01", "pc-01"),
            ("PC-09", "pc-09"),
            ("PC-10", "pc-10"),
            ("PC-30", "pc-30"),
            ("pc7", "pc-07"),
            ("PC-100", "pc-100"),
        ],
    )
    def test_numero_de_puesto_relleno_a_dos_digitos(
        self, nombre, esperado,
    ):
        """El número de puesto se rellena a dos dígitos como mínimo;
        los puestos con tres o más cifras se conservan completos."""
        assert normalizar_nombre_sala(nombre) == esperado


class TestCanonizacionOtrosNombres:
    """Tratamiento de los nombres de sala que no son puestos del aula
    (la sala ``examen`` del submodo grupo, salas de laboratorio…)."""

    @pytest.mark.parametrize(
        "nombre, esperado",
        [
            ("examen", "examen"),
            ("EXAMEN", "examen"),
            (" Examen ", "examen"),
            ("torneo_lab", "torneo_lab"),
            ("Torneo_Lab", "torneo_lab"),
            ("sala_pc01", "sala_pc01"),
        ],
    )
    def test_nombres_no_puesto_solo_minusculas_y_recorte(
        self, nombre, esperado,
    ):
        """Los nombres que no son un puesto del aula se canonizan solo
        a minúsculas y sin espacios sobrantes; el formato ``pc-NN`` no
        se les aplica."""
        assert normalizar_nombre_sala(nombre) == esperado


class TestPropiedadesGenerales:
    """Propiedades que la canonización debe cumplir siempre."""

    @pytest.mark.parametrize(
        "nombre",
        ["PC-05", "pc 7", "examen", " EXAMEN ", "torneo_lab", "PC_30"],
    )
    def test_idempotencia(self, nombre):
        """Canonizar un nombre ya canónico no lo cambia: aplicar la
        función dos veces da el mismo resultado que aplicarla una
        sola vez."""
        una_vez = normalizar_nombre_sala(nombre)
        dos_veces = normalizar_nombre_sala(una_vez)
        assert una_vez == dos_veces

    @pytest.mark.parametrize(
        "nombre",
        ["PC-05", "examen", "torneo_lab", "PC-30", " Pc_7 "],
    )
    def test_resultado_listo_para_usar_como_localpart(self, nombre):
        """El resultado nunca contiene mayúsculas ni espacios en los
        extremos: es directamente usable como localpart de un JID."""
        resultado = normalizar_nombre_sala(nombre)
        assert resultado == resultado.lower()
        assert resultado == resultado.strip()
