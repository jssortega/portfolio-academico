"""
Tests del Hito 5 — Sanitario Villa Olivar (Nivel 2).

Autor(es): Cristina Silva (csu0002@ujaen.es)
Grupo: multi007s
"""

from pathlib import Path
import pytest

RUTA_RAIZ = Path(__file__).resolve().parent.parent
RUTA_PROMPTS = RUTA_RAIZ / "prompts"


class TestHito5Sanitario:
    """Pruebas del Hito 5 para el agente Sanitario."""

    def test_prompt_sanitario_contiene_ejemplos(self) -> None:
        """prompts/sanitario.txt existe y contiene al menos un ejemplo few-shot."""
        ruta = RUTA_PROMPTS / "sanitario.txt"
        assert ruta.exists(), "No se encuentra prompts/sanitario.txt"
        contenido = ruta.read_text(encoding="utf-8")
        assert len(contenido.strip()) > 0, "prompts/sanitario.txt está vacío."
        tiene_ejemplo = (
            "Ejemplo" in contenido
            or "ejemplo" in contenido
            or "Entrada" in contenido
            or "Salida" in contenido
        )
        assert tiene_ejemplo, (
            "prompts/sanitario.txt no contiene ejemplos few-shot."
        )

    def test_prompt_sanitario_contiene_estrategia(self) -> None:
        """prompts/sanitario.txt documenta la estrategia de prompting.

        AVISO: el fichero actual no empieza con '#' ni menciona 'estrategia'.
        Añade al inicio: '# Estrategia de prompting: ...'
        """
        ruta = RUTA_PROMPTS / "sanitario.txt"
        assert ruta.exists()
        contenido = ruta.read_text(encoding="utf-8")
        tiene_estrategia = (
            "Estrategia" in contenido
            or "estrategia" in contenido
            or contenido.strip().startswith("#")
        )
        assert tiene_estrategia, (
            "prompts/sanitario.txt debe incluir un comentario con la estrategia. "
            "Añade al inicio: '# Estrategia de prompting: ...'"
        )

    def test_herramientas_sanitario_cubren_dos_tipos(self) -> None:
        """Las herramientas de Sanitario cubren alerta válida e inválida."""
        from logica.logica_sanitario import (
            verificarAlerta,
            procesarAlertaAceptada,
            procesarAlertaRechazada,
        )

        # Flujo 1: alerta válida
        alerta_valida = {
            "tipo_mensaje": "alerta_emergencia",
            "id_emergencia": "INC-2026-TEST-S01",
            "tipo_emergencia": "derrame_quimico",
            "ubicacion": {"direccion": "Av. Industrial 5"},
            "prioridad": "alta",
            "descripcion": "Derrame de cloro con heridos.",
            "marca_temporal": "2026-01-01T10:00:00Z",
        }
        assert verificarAlerta(alerta_valida) is True
        informe = procesarAlertaAceptada(alerta_valida)
        assert informe["agente_origen"] == "sanitario"
        assert informe["estado"] == "recibido"

        # Flujo 2: alerta inválida
        alerta_invalida = {"tipo_mensaje": "alerta_emergencia"}
        assert verificarAlerta(alerta_invalida) is False
        rechazo = procesarAlertaRechazada(alerta_invalida)
        assert rechazo["estado"] == "requiere_apoyo"

    def test_escenario_alternativo_sanitario_accidente_trafico(self) -> None:
        """Sanitario procesa una alerta de accidente de tráfico correctamente."""
        from logica.logica_sanitario import verificarAlerta, procesarAlertaAceptada

        alerta = {
            "tipo_mensaje": "alerta_emergencia",
            "id_emergencia": "INC-2026-TEST-S02",
            "tipo_emergencia": "accidente_trafico",
            "ubicacion": {"direccion": "A-44 km 23"},
            "prioridad": "alta",
            "descripcion": "Colisión múltiple con 4 heridos graves.",
            "marca_temporal": "2026-01-01T11:00:00Z",
        }
        assert verificarAlerta(alerta) is True
        informe = procesarAlertaAceptada(alerta)
        assert informe["tipo_mensaje"] == "informe_actuacion"
        assert informe["agente_origen"] == "sanitario"
        assert informe["id_emergencia"] == "INC-2026-TEST-S02"
        assert informe["recursos_desplegados"] > 0

    def test_escenario_alternativo_sanitario_incendio(self) -> None:
        """Sanitario procesa una alerta de incendio correctamente."""
        from logica.logica_sanitario import verificarAlerta, procesarAlertaAceptada

        alerta = {
            "tipo_mensaje": "alerta_emergencia",
            "id_emergencia": "INC-2026-TEST-S03",
            "tipo_emergencia": "incendio",
            "ubicacion": {"direccion": "Calle Mayor 5"},
            "prioridad": "alta",
            "descripcion": "Incendio en edificio residencial con 2 personas atrapadas.",
            "marca_temporal": "2026-01-01T12:00:00Z",
        }
        assert verificarAlerta(alerta) is True
        informe = procesarAlertaAceptada(alerta)
        assert informe["estado"] == "recibido"

    def test_atender_heridos_sanitario(self) -> None:
        """atenderHeridos genera un informe de triaje con estado finalizado."""
        from logica.logica_sanitario import atenderHeridos

        alerta = {
            "id_emergencia": "INC-2026-TEST-S04",
            "tipo_emergencia": "accidente_trafico",
        }
        resultado = atenderHeridos(alerta)
        assert resultado["tipo_mensaje"] == "informe_actuacion"
        assert resultado["agente_origen"] == "sanitario"
        assert resultado["estado"] == "finalizado"
        assert resultado["id_emergencia"] == "INC-2026-TEST-S04"

    def test_functiontools_sanitario_invocables(self) -> None:
        """Las FunctionTool de Sanitario son instancias válidas."""
        from google.adk.tools import FunctionTool
        from herramientas.herramientas_sanitario import herramientas_sanitario

        assert len(herramientas_sanitario) >= 2
        for herr in herramientas_sanitario:
            assert isinstance(herr, FunctionTool)