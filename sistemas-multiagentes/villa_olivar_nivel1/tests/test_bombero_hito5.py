"""
Tests del Hito 5 — Bomberos Villa Olivar (Nivel 2).

Autor(es): Cristina Silva (csu0002@ujaen.es)
Grupo: multi007s
"""

from pathlib import Path
import pytest

RUTA_RAIZ = Path(__file__).resolve().parent.parent
RUTA_PROMPTS = RUTA_RAIZ / "prompts"


class TestHito5Bomberos:
    """Pruebas del Hito 5 para el agente Bomberos."""

    def test_prompt_bomberos_contiene_ejemplos(self) -> None:
        """prompts/bomberos.txt existe y contiene al menos un ejemplo few-shot."""
        ruta = RUTA_PROMPTS / "bomberos.txt"
        assert ruta.exists(), "No se encuentra prompts/bomberos.txt"
        contenido = ruta.read_text(encoding="utf-8")
        assert len(contenido.strip()) > 0, "prompts/bomberos.txt está vacío."
        tiene_ejemplo = (
            "Ejemplo" in contenido
            or "ejemplo" in contenido
            or "Entrada" in contenido
            or "Salida" in contenido
        )
        assert tiene_ejemplo, (
            "prompts/bomberos.txt no contiene ejemplos few-shot. "
            "Añade al menos un par entrada/salida."
        )

    def test_prompt_bomberos_contiene_estrategia(self) -> None:
        """prompts/bomberos.txt documenta la estrategia de prompting."""
        ruta = RUTA_PROMPTS / "bomberos.txt"
        assert ruta.exists()
        contenido = ruta.read_text(encoding="utf-8")
        tiene_estrategia = (
            "Estrategia" in contenido
            or "estrategia" in contenido
            or contenido.strip().startswith("#")
        )
        assert tiene_estrategia, (
            "prompts/bomberos.txt debe incluir un comentario con la estrategia."
        )

    def test_herramientas_bomberos_cubren_dos_tipos(self) -> None:
        """Las herramientas de Bomberos cubren derrame_quimico e incendio."""
        from logica.logica_bomberos import evaluar_riesgo_quimico, evaluar_incendio

        resultado_quimico = evaluar_riesgo_quimico("derrame de amoniaco en nave industrial")
        assert resultado_quimico.get("nivel") in ("normal", "urgente", "inmediata", "medio")
        assert resultado_quimico.get("sustancia") == "amoniaco"

        resultado_incendio = evaluar_incendio("incendio forestal en zona de bosque")
        assert resultado_incendio.get("nivel") in ("normal", "urgente", "inmediata", "medio")
        assert resultado_incendio.get("tipo") == "bosque"

    def test_escenario_alternativo_bomberos_incendio_casa(self) -> None:
        """Bomberos procesa correctamente un incendio en vivienda."""
        from logica.logica_bomberos import evaluar_incendio

        resultado = evaluar_incendio("incendio en vivienda del centro")
        assert resultado.get("tipo") == "casa"
        assert resultado.get("nivel") == "inmediata"
        assert resultado.get("radio") == "100m"
        assert resultado.get("necesita_gas") is True

    def test_escenario_alternativo_bomberos_incendio_fabrica(self) -> None:
        """Bomberos procesa correctamente un incendio en fábrica."""
        from logica.logica_bomberos import evaluar_incendio

        resultado = evaluar_incendio("incendio en nave industrial zona norte")
        assert resultado.get("tipo") == "fabrica"
        assert resultado.get("nivel") == "normal"
        assert resultado.get("radio") == "500m"
        assert resultado.get("necesita_gas") is True

    def test_escenario_alternativo_bomberos_incendio_forestal(self) -> None:
        """Bomberos reconoce sinónimos de bosque: forestal, monte, pinar."""
        from logica.logica_bomberos import evaluar_incendio

        for descripcion in [
            "incendio forestal en pinar",
            "fuego en monte cercano al pueblo",
            "zona arbolada en llamas",
        ]:
            resultado = evaluar_incendio(descripcion)
            assert resultado.get("tipo") == "bosque", (
                f"Para '{descripcion}' esperaba tipo='bosque', "
                f"obtuvo '{resultado.get('tipo')}'"
            )

    def test_procesar_alerta_bomberos_incendio_completo(self) -> None:
        """procesar_alerta maneja una alerta de incendio forestal de principio a fin."""
        from logica.logica_bomberos import procesar_alerta

        alerta = {
            "id_emergencia": "INC-2026-TEST-B01",
            "tipo_emergencia": "incendio",
            "descripcion": "Incendio forestal en zona boscosa al norte del municipio.",
            "ubicacion": {"direccion": "Camino del Monte km 3"},
            "prioridad": "critica",
        }
        resultado = procesar_alerta(alerta)

        assert "evaluacion" in resultado
        assert "informe_centralita" in resultado
        assert "recursos_policia" in resultado
        assert resultado["evaluacion"].get("tipo") == "bosque"
        assert resultado["informe_centralita"]["agente_origen"] == "bomberos"
        assert resultado["informe_centralita"]["estado"] == "en_camino"
        assert resultado["recursos_policia"]["accion_solicitada"] == "establecer_perimetro"
        assert resultado.get("recursos_municipal") is None

    def test_procesar_alerta_bomberos_quimico_con_corte_gas(self) -> None:
        """procesar_alerta de derrame químico genera solicitud de corte de gas."""
        from logica.logica_bomberos import procesar_alerta

        alerta = {
            "id_emergencia": "INC-2026-TEST-B02",
            "tipo_emergencia": "derrame_quimico",
            "descripcion": "Derrame de amoniaco en planta química.",
            "ubicacion": {"direccion": "Polígono Industrial Norte"},
            "prioridad": "alta",
        }
        resultado = procesar_alerta(alerta)

        assert resultado["evaluacion"].get("sustancia") == "amoniaco"
        assert resultado["recursos_municipal"] is not None
        assert resultado["recursos_municipal"]["accion_solicitada"] == "cortar_gas"

    def test_functiontools_bomberos_invocables(self) -> None:
        """Las FunctionTool de Bomberos son instancias válidas e invocables."""
        from google.adk.tools import FunctionTool
        from herramientas.herramientas_bomberos import herramientas_bomberos

        assert len(herramientas_bomberos) >= 2
        for herr in herramientas_bomberos:
            assert isinstance(herr, FunctionTool)

    def test_finalizar_intervencion_bomberos(self) -> None:
        """finalizar_intervencion devuelve un informe con estado finalizado."""
        from logica.logica_bomberos import finalizar_intervencion

        resultado = finalizar_intervencion("INC-2026-TEST-B03")
        assert resultado["tipo_mensaje"] == "informe_actuacion"
        assert resultado["agente_origen"] == "bomberos"
        assert resultado["estado"] == "finalizado"
        assert resultado["id_emergencia"] == "INC-2026-TEST-B03"