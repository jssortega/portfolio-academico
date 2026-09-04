"""Pruebas unitarias del modelo `AgentCard`.

Cubren el escenario 1 del Hito 1 («publicación de la Agent Card»)
descrito en `doc/HITOS_EVALUACION.md` y los requisitos de metadata
mínima del Hito 5 (escenario 11). La validación se aplica al JSON
que el agente publica en `/.well-known/agent.json`.
"""

import pytest
from pydantic import ValidationError

from contrato.agent_card import AgentCard, Capacidades, Habilidad


def _construir_habilidad_de_clasificacion() -> Habilidad:
    """Construye una habilidad típica de la Centralita 112 para reutilizar en pruebas."""
    habilidad = Habilidad(
        id="clasificar_emergencia",
        name="Clasificación de emergencias",
        description="Determina el tipo y la prioridad de una alerta entrante.",
        tags=["emergencia", "clasificacion", "triaje"],
    )
    return habilidad


@pytest.mark.hito_1
class TestAgentCardMinima:
    """Pruebas de la Agent Card en su forma mínima admisible."""

    def test_admite_la_card_minima_con_una_habilidad(self) -> None:
        """Una Agent Card con los campos obligatorios y una habilidad debe validarse."""
        card = AgentCard(
            name="centralita_villa_olivar",
            description="Centralita 112 del sistema de emergencias del grupo.",
            url="http://192.168.1.11:8110",
            version="1.0.0",
            skills=[_construir_habilidad_de_clasificacion()],
        )
        assert card.name == "centralita_villa_olivar"
        assert card.skills[0].id == "clasificar_emergencia"

    def test_rechaza_una_card_sin_ninguna_habilidad(self) -> None:
        """Una lista vacía de habilidades viola el contrato del proyecto."""
        with pytest.raises(ValidationError):
            AgentCard(
                name="bomberos_grupo_5",
                description="Especialista bomberos.",
                url="http://192.168.1.12:8120",
                version="1.0.0",
                skills=[],
            )

    def test_rechaza_una_card_con_url_invalida(self) -> None:
        """La URL debe ser un identificador HTTP válido, no una cadena cualquiera."""
        with pytest.raises(ValidationError):
            AgentCard(
                name="sanitario_grupo_7",
                description="Especialista sanitario.",
                url="esto-no-es-una-url",
                version="1.0.0",
                skills=[_construir_habilidad_de_clasificacion()],
            )


@pytest.mark.hito_1
class TestCapacidades:
    """Pruebas de la sección `capabilities` de la Agent Card."""

    def test_admite_la_capacidad_de_transmision_continua_activada(self) -> None:
        """Un agente puede declarar `streaming=True` para anunciar SSE."""
        capacidades = Capacidades(streaming=True, pushNotifications=False)
        assert capacidades.streaming is True

    def test_capacidades_predeterminadas_son_todas_falsas(self) -> None:
        """Si la card omite `capabilities`, todas las capacidades son `False`."""
        capacidades = Capacidades()
        assert capacidades.streaming is False
        assert capacidades.pushNotifications is False


@pytest.mark.hito_5
class TestHabilidadesMetadata:
    """Pruebas de la metadata mínima de las habilidades para el descubrimiento entre grupos."""

    def test_una_habilidad_sin_etiquetas_es_admisible_pero_pobre(self) -> None:
        """Una habilidad sin etiquetas valida, aunque dificulta el filtrado por rol."""
        habilidad = Habilidad(
            id="atender_emergencia",
            name="Atender emergencia",
            description="Atiende cualquier tipo de emergencia.",
        )
        assert habilidad.tags == []

    def test_rechaza_un_identificador_vacio(self) -> None:
        """El identificador debe ser una cadena no vacía para ser distinguible."""
        with pytest.raises(ValidationError):
            Habilidad(
                id="",
                name="Habilidad sin identificador",
                description="Descripción.",
            )

    def test_acepta_etiquetas_semanticas_para_filtrar_por_rol(self) -> None:
        """Las etiquetas viajan en orden y pueden contener identificadores de rol."""
        habilidad = Habilidad(
            id="extincion_incendio",
            name="Extinción de incendios",
            description="Apaga incendios y previene su propagación.",
            tags=["bomberos", "incendio", "rescate"],
        )
        assert "bomberos" in habilidad.tags


@pytest.mark.hito_1
class TestAgentCardSerializacion:
    """Pruebas de la serialización idempotente de la Agent Card."""

    def test_se_serializa_y_se_recompone_sin_perdida(self) -> None:
        """`model_dump(mode='json') -> model_validate` debe ser idempotente."""
        original = AgentCard(
            name="policia_grupo_3",
            description="Especialista policía.",
            url="http://192.168.1.13:8130",
            version="1.2.3",
            capabilities=Capacidades(streaming=True),
            skills=[_construir_habilidad_de_clasificacion()],
            defaultInputModes=["application/json"],
            defaultOutputModes=["application/json", "text/plain"],
        )
        cuerpo_json = original.model_dump(mode="json")
        recompuesto = AgentCard.model_validate(cuerpo_json)
        assert recompuesto == original

    def test_admite_campos_extra_silenciosamente(self) -> None:
        """Un campo no contemplado por el contrato no rompe la validación."""
        cuerpo = {
            "name": "servicios_municipales_grupo_1",
            "description": "Especialista de servicios municipales.",
            "url": "http://192.168.1.14:8140",
            "version": "0.9.0",
            "skills": [
                {
                    "id": "cortar_suministros",
                    "name": "Corte de suministros",
                    "description": "Corte temporal del suministro afectado.",
                },
            ],
            "campo_extra_grupo": "info no contemplada en el contrato",
        }
        card = AgentCard.model_validate(cuerpo)
        assert card.name.startswith("servicios_municipales")
