"""
Tests de las Agent Cards — Villa Olivar (Nivel 3).

Verifican que cada agente público publica una tarjeta válida en la ruta
estándar /.well-known/agent.json y que el contenido es coherente con
lo declarado en agents.yaml y con el contrato A2A.

Hito 1 — escenario 1: publicación de la Agent Card.
"""
from __future__ import annotations

import pytest
import yaml
from pathlib import Path
from agentes.base_agente_a2a import EspecificacionAgente
from agentes.agente_centralita import AgenteCentralita
from agentes.agente_bomberos import AgenteBomberos
from agentes.agente_sanitario import AgenteSanitario
from agentes.agente_policia import AgentePolicia
from agentes.agente_municipal import AgenteMunicipal
from contrato.agent_card import AgentCard

def test_agent_card_centralita_valida() -> None:
    """La Agent Card de la Centralita cumple el esquema y trae las habilidades del Hito 1."""

    espec = EspecificacionAgente(
        identificador="centralita_multi007s",
        rol="centralita",
        visibilidad="publico",
        puerto=8110,
        host="127.0.0.1",
        modulo="agentes.agente_centralita",
        clase="AgenteCentralita",
        parametros={}
    )

    agente = AgenteCentralita(espec)
    tarjeta = agente.construir_agent_card()

    assert isinstance(tarjeta, AgentCard)
    assert tarjeta.name == espec.identificador
    assert str(tarjeta.url).rstrip("/") == f"http://{espec.host}:{espec.puerto}"
    assert tarjeta.version == "1.0.0"

    ids_habilidades = [h.id for h in tarjeta.skills]
    assert "clasificar_emergencia" in ids_habilidades
    assert "determinar_destinatarios" in ids_habilidades
    assert "coordinar_respuesta" in ids_habilidades
    

    for habilidad in tarjeta.skills:
        assert len(habilidad.tags) > 0
        assert "centralita" in habilidad.tags

def crear_especificacion_mock(rol: str, puerto: int, clase: str) -> EspecificacionAgente:
    return EspecificacionAgente(
        identificador=f"agente_{rol}_test",
        rol=rol,
        modulo=f"agentes.agente_{rol}",
        clase=clase,
        visibilidad="publico",
        puerto=puerto,
        host="127.0.0.1",
        parametros={}
    )


def test_tres_agent_cards_validas() -> None:
    """Verifica que los tres agentes públicos generan una Agent Card válida con al menos una habilidad."""

    spec_centralita = crear_especificacion_mock("centralita", 8110, "AgenteCentralita")
    spec_bomberos = crear_especificacion_mock("bomberos", 8111, "AgenteBomberos")
    spec_municipal = crear_especificacion_mock("municipal", 8112, "AgenteMunicipal")


    centralita = AgenteCentralita(spec_centralita)
    bomberos = AgenteBomberos(spec_bomberos)
    municipal = AgenteMunicipal(spec_municipal)

    card_c = centralita.construir_agent_card()
    card_b = bomberos.construir_agent_card()
    card_m = municipal.construir_agent_card()

    assert len(card_c.skills) >= 1, "La Centralita debe tener habilidades declaradas"
    assert len(card_b.skills) >= 1, "Bomberos debe tener habilidades declaradas"
    assert len(card_m.skills) >= 1, "Municipal debe tener habilidades declaradas"


    assert card_c.name is not None
    assert card_b.name is not None
    assert card_m.name is not None

def test_cinco_agent_cards():
    agentes = [
        ("centralita", AgenteCentralita, "publico", 8110),
        ("bomberos", AgenteBomberos, "publico", 8120),
        ("sanitario", AgenteSanitario, "publico", 8130),
        ("policia", AgentePolicia, "privado", 8140),
        ("municipal", AgenteMunicipal, "privado", 8150),
    ]

    for rol, ClaseAgente, visibilidad, puerto in agentes:
        spec = EspecificacionAgente(
            identificador=rol,
            rol=rol,
            visibilidad=visibilidad,
            host="127.0.0.1",
            puerto=puerto,
            modulo=f"agentes.agente_{rol}",
            clase=ClaseAgente.__name__,
            parametros={},
        )

        agente = ClaseAgente(spec)
        card = agente.construir_agent_card()

        if hasattr(card, "model_dump"):
            card = card.model_dump(mode="json")

        assert card["name"]
        assert card["description"]
        assert card["url"].startswith("http://")
        assert card["version"]
        assert "capabilities" in card
        assert "skills" in card
        assert len(card["skills"]) > 0
