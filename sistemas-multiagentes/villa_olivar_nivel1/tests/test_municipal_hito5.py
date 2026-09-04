"""
Tests del Hito 5 — Servicios Municipales Villa Olivar (Nivel 2).

Autor(es): Cristina Silva (csu0002@ujaen.es)
Grupo: multi007s
"""

from pathlib import Path
import pytest

RUTA_RAIZ = Path(__file__).resolve().parent.parent
RUTA_PROMPTS = RUTA_RAIZ / "prompts"


class TestHito5Municipal:
    """Pruebas del Hito 5 para el agente Servicios Municipales."""

    def test_prompt_municipal_contiene_ejemplos(self) -> None:
        """prompts/municipal.txt existe y contiene al menos un ejemplo few-shot.

        AVISO: el fichero actual no tiene ejemplos entrada/salida explícitos.
        Añade al final un bloque 'Ejemplo:' con entrada y salida JSON.
        """
        ruta = RUTA_PROMPTS / "municipal.txt"
        assert ruta.exists(), "No se encuentra prompts/municipal.txt"
        contenido = ruta.read_text(encoding="utf-8")
        assert len(contenido.strip()) > 0, "prompts/municipal.txt está vacío."
        tiene_ejemplo = (
            "Ejemplo" in contenido
            or "ejemplo" in contenido
            or "Entrada" in contenido
            or "Salida" in contenido
        )
        assert tiene_ejemplo, (
            "prompts/municipal.txt no contiene ejemplos few-shot. "
            "Añade al final un bloque 'Ejemplo:' con par entrada/salida JSON."
        )

    def test_prompt_municipal_contiene_estrategia(self) -> None:
        """prompts/municipal.txt documenta la estrategia de prompting."""
        ruta = RUTA_PROMPTS / "municipal.txt"
        assert ruta.exists()
        contenido = ruta.read_text(encoding="utf-8")
        tiene_estrategia = (
            "Estrategia" in contenido
            or "estrategia" in contenido
            or contenido.strip().startswith("#")
        )
        assert tiene_estrategia, (
            "prompts/municipal.txt debe incluir un comentario con la estrategia. "
            "Añade al inicio: '# Estrategia de prompting: ...'"
        )

    def test_herramientas_municipal_cubren_dos_tipos(self) -> None:
        """Las herramientas de Municipal cubren alerta directa y solicitud externa."""
        from logica.logica_municipal import (
            procesar_alerta_municipal,
            procesar_solicitud_municipal,
        )

        # Tipo 1: alerta directa de derrame químico
        alerta = {
            "id_emergencia": "INC-2026-TEST-M01",
            "tipo_emergencia": "derrame_quimico",
        }
        resultado = procesar_alerta_municipal(alerta)
        assert resultado["evaluacion"]["nivel"] == "urgente"
        assert resultado["evaluacion"]["accion"] == "limpieza"
        assert resultado["informe_centralita"]["agente_origen"] == "municipal"

        # Tipo 2: solicitud de corte de gas de Bomberos
        solicitud = {
            "id_emergencia": "INC-2026-TEST-M01",
            "solicitante": "bomberos",
            "destinatario": "municipal",
            "accion_solicitada": "cortar_gas",
        }
        respuesta = procesar_solicitud_municipal(solicitud)
        assert respuesta["aceptada"] is True
        assert respuesta["tipo_mensaje"] == "respuesta_recurso"

    def test_escenario_alternativo_municipal_incendio(self) -> None:
        """Municipal procesa una alerta de incendio como escenario alternativo."""
        from logica.logica_municipal import procesar_alerta_municipal

        alerta = {
            "id_emergencia": "INC-2026-TEST-M02",
            "tipo_emergencia": "incendio",
        }
        resultado = procesar_alerta_municipal(alerta)
        assert resultado["evaluacion"]["nivel"] == "urgente"
        assert resultado["evaluacion"]["accion"] == "reparacion"
        assert resultado["informe_centralita"]["estado"] == "en_camino"

    def test_escenario_alternativo_municipal_accidente_trafico(self) -> None:
        """Municipal procesa una alerta de accidente de tráfico."""
        from logica.logica_municipal import procesar_alerta_municipal

        alerta = {
            "id_emergencia": "INC-2026-TEST-M03",
            "tipo_emergencia": "accidente_trafico",
        }
        resultado = procesar_alerta_municipal(alerta)
        assert resultado["evaluacion"] is not None
        assert resultado["informe_centralita"]["agente_origen"] == "municipal"
        assert resultado["evaluacion"]["necesita_policia"] is True

    def test_municipal_solicitud_corte_gas(self) -> None:
        """Municipal acepta y ejecuta una solicitud de corte de gas."""
        from logica.logica_municipal import procesar_solicitud_municipal

        solicitud = {
            "accion_solicitada": "cortar_gas",
            "id_emergencia": "INC-2026-TEST-M04",
            "solicitante": "bomberos",
        }
        resultado = procesar_solicitud_municipal(solicitud)
        assert resultado["aceptada"] is True
        assert "cortar_gas" in resultado["detalle"]

    def test_municipal_solicitud_limpieza(self) -> None:
        """Municipal acepta una solicitud genérica de limpieza."""
        from logica.logica_municipal import procesar_solicitud_municipal

        solicitud = {"accion_solicitada": "limpieza_calzada"}
        resultado = procesar_solicitud_municipal(solicitud)
        assert resultado["aceptada"] is True
        assert resultado["tipo_mensaje"] == "respuesta_recurso"

    def test_functiontools_municipal_invocables(self) -> None:
        """Las FunctionTool de Municipal son instancias válidas e invocables."""
        from google.adk.tools import FunctionTool
        from herramientas.herramientas_municipal import (
            herramientas_municipal,
            herramienta_procesar_alerta_municipal,
            herramienta_procesar_solicitud_municipal,
        )

        assert len(herramientas_municipal) >= 2
        for herr in herramientas_municipal:
            assert isinstance(herr, FunctionTool)

        resultado = herramienta_procesar_alerta_municipal.func({
            "id_emergencia": "TEST",
            "tipo_emergencia": "incendio",
        })
        assert resultado["informe_centralita"]["agente_origen"] == "municipal"

        respuesta = herramienta_procesar_solicitud_municipal.func({
            "accion_solicitada": "cortar_gas",
        })
        assert respuesta["aceptada"] is True