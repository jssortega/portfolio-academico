"""
Tests del Hito 5 — Policía Villa Olivar (Nivel 2).

Autor(es): Cristina Silva (csu0002@ujaen.es)
Grupo: multi007s
"""

from pathlib import Path
import pytest

RUTA_RAIZ = Path(__file__).resolve().parent.parent
RUTA_PROMPTS = RUTA_RAIZ / "prompts"


class TestHito5Policia:
    """Pruebas del Hito 5 para el agente Policía."""

    def test_prompt_policia_contiene_ejemplos(self) -> None:
        """prompts/policia.txt existe y contiene al menos un ejemplo few-shot."""
        ruta = RUTA_PROMPTS / "policia.txt"
        assert ruta.exists(), "No se encuentra prompts/policia.txt"
        contenido = ruta.read_text(encoding="utf-8")
        assert len(contenido.strip()) > 0, "prompts/policia.txt está vacío."
        tiene_ejemplo = (
            "Ejemplo" in contenido
            or "ejemplo" in contenido
            or "ENTRADA" in contenido
            or "SALIDA" in contenido
        )
        assert tiene_ejemplo, (
            "prompts/policia.txt no contiene ejemplos few-shot."
        )

    def test_prompt_policia_contiene_estrategia(self) -> None:
        """prompts/policia.txt documenta la estrategia de prompting."""
        ruta = RUTA_PROMPTS / "policia.txt"
        assert ruta.exists()
        contenido = ruta.read_text(encoding="utf-8")
        tiene_estrategia = (
            "Estrategia" in contenido
            or "estrategia" in contenido
            or contenido.strip().startswith("#")
        )
        assert tiene_estrategia, (
            "prompts/policia.txt debe incluir un comentario con la estrategia."
        )

    def test_herramientas_policia_cubren_dos_tipos(self) -> None:
        """Las herramientas de Policía cubren alerta válida e inválida."""
        from logica.logica_policia import verificarAlerta, procesarAlertaAceptada

        alerta = {
            "tipo_mensaje": "alerta_emergencia",
            "id_emergencia": "INC-2026-TEST-P01",
            "tipo_emergencia": "derrame_quimico",
            "ubicacion": {"direccion": "Av. Constitución 42"},
            "prioridad": "alta",
            "descripcion": "Derrame de amoniaco.",
            "marca_temporal": "2026-01-01T10:00:00Z",
        }
        assert verificarAlerta(alerta) is True
        informe = procesarAlertaAceptada(alerta)
        assert informe["agente_origen"] == "policia"
        assert informe["estado"] == "recibido"

    def test_escenario_alternativo_policia_accidente_trafico(self) -> None:
        """Policía procesa una alerta de accidente de tráfico."""
        from logica.logica_policia import verificarAlerta, procesarAlertaAceptada

        alerta = {
            "tipo_mensaje": "alerta_emergencia",
            "id_emergencia": "INC-2026-TEST-P02",
            "tipo_emergencia": "accidente_trafico",
            "ubicacion": {"direccion": "A-44 km 23"},
            "prioridad": "alta",
            "descripcion": "Colisión múltiple, carretera cortada.",
            "marca_temporal": "2026-01-01T11:00:00Z",
        }
        assert verificarAlerta(alerta) is True
        informe = procesarAlertaAceptada(alerta)
        assert informe["tipo_mensaje"] == "informe_actuacion"
        assert informe["id_emergencia"] == "INC-2026-TEST-P02"
        assert informe["recursos_desplegados"] > 0

    def test_escenario_alternativo_policia_incendio(self) -> None:
        """Policía procesa una alerta de incendio."""
        from logica.logica_policia import verificarAlerta, procesarAlertaAceptada

        alerta = {
            "tipo_mensaje": "alerta_emergencia",
            "id_emergencia": "INC-2026-TEST-P03",
            "tipo_emergencia": "incendio",
            "ubicacion": {"direccion": "Calle Mayor 5"},
            "prioridad": "critica",
            "descripcion": "Incendio en edificio residencial.",
            "marca_temporal": "2026-01-01T12:00:00Z",
        }
        assert verificarAlerta(alerta) is True
        informe = procesarAlertaAceptada(alerta)
        assert informe["estado"] == "recibido"

    def test_policia_alerta_invalida(self) -> None:
        """Policía rechaza correctamente una alerta con datos faltantes."""
        from logica.logica_policia import verificarAlerta, procesarAlertaRechazada

        alerta_invalida = {"tipo_mensaje": "alerta_emergencia"}
        assert verificarAlerta(alerta_invalida) is False
        rechazo = procesarAlertaRechazada(alerta_invalida)
        assert rechazo["agente_origen"] == "policia"
        assert rechazo["estado"] == "requiere_apoyo"

    def test_policia_peticion_perimetro(self) -> None:
        """Policía procesa correctamente una petición de establecer perímetro."""
        from logica.logica_policia import verificarPeticion, procesarPeticionAceptada

        peticion = {
            "tipo_mensaje": "solicitud_recurso",
            "id_emergencia": "INC-2026-TEST-P04",
            "solicitante": "bomberos",
            "destinatario": "policia",
            "accion_solicitada": "establecer_perimetro",
            "parametros": {"radio_metros": 500},
            "urgencia": "urgente",
        }
        assert verificarPeticion(peticion) is True
        respuesta = procesarPeticionAceptada(peticion)
        assert respuesta["aceptada"] is True
        assert respuesta["accion_solicitada"] == "establecer_perimetro"

    def test_policia_peticion_invalida(self) -> None:
        """Policía rechaza una petición de recursos con formato incorrecto."""
        from logica.logica_policia import verificarPeticion, procesarPeticionRechazada

        peticion_invalida = {"tipo_mensaje": "solicitud_recurso"}
        assert verificarPeticion(peticion_invalida) is False
        rechazo = procesarPeticionRechazada(peticion_invalida)
        assert rechazo["aceptada"] is False

    def test_functiontools_policia_invocables(self) -> None:
        """Las FunctionTool de Policía son instancias válidas."""
        from google.adk.tools import FunctionTool
        from herramientas.herramientas_policia import herramientas_policia

        assert len(herramientas_policia) >= 2
        for herr in herramientas_policia:
            assert isinstance(herr, FunctionTool)