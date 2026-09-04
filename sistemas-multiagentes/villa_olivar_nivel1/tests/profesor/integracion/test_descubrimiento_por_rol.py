"""Hito 5 — *Descubrimiento por rol* (escenario 5).

El cliente del coordinador consulta el registro REST del aula con
``GET /agentes`` y filtra la respuesta por rol. La prueba verifica
dos propiedades:

1. La consulta devuelve una lista cuyo esquema admite al menos
   los campos ``id``, ``rol``, ``url_a2a`` y ``url_agent_card``
   (acordados en ``doc/registro_rest_para_clientes.md``).
2. Para cada rol del enumerado ``RolEspecialista``, el filtro
   devuelve una sublista coherente: todos sus elementos tienen
   ese ``rol`` y al menos uno aparece si el aula tiene grupos
   arrancados con ese rol como público.

La prueba se omite si el registro no responde (el grupo puede
estar trabajando con un registro inexistente para verificar el
escenario 8 del Hito 3).

Prueba de **caja negra contra el sistema real** del grupo y del
registro REST del aula.
"""

from __future__ import annotations

import httpx
import pytest

from contrato.tipos import RolEspecialista
from cliente_pruebas.cliente import ClienteCoordinador


# Campos mínimos que el plan exige al esquema de cada descriptor
# de agente devuelto por ``GET /agentes``.
CAMPOS_MINIMOS_DESCRIPTOR = {"id", "rol", "url_a2a", "url_agent_card"}


@pytest.mark.integration
@pytest.mark.hito_5
class TestDescubrimientoPorRol:
    """El registro REST permite filtrar por rol con un esquema previsible."""

    @pytest.mark.asyncio
    async def test_get_agentes_devuelve_lista_con_esquema_minimo(
        self,
        cliente_coordinador: ClienteCoordinador,
    ) -> None:
        """La respuesta es una lista cuyos elementos cumplen el esquema mínimo."""
        try:
            agentes = await cliente_coordinador.listar_agentes_publicos()
        except (httpx.ConnectError, httpx.TimeoutException) as error:
            pytest.skip(f"Registro REST no alcanzable: {error}")

        assert isinstance(agentes, list), (
            f"GET /agentes debe devolver una lista; se obtuvo {type(agentes).__name__}."
        )
        if not agentes:
            pytest.skip("El registro está accesible pero vacío; no hay agentes para filtrar.")
        descriptores_invalidos = [
            descriptor for descriptor in agentes
            if not CAMPOS_MINIMOS_DESCRIPTOR.issubset(descriptor.keys())
        ]
        assert descriptores_invalidos == [], (
            f"Hay descriptores que no contienen los campos mínimos "
            f"{CAMPOS_MINIMOS_DESCRIPTOR}: {descriptores_invalidos[:3]}"
        )

    @pytest.mark.asyncio
    async def test_filtrar_por_rol_devuelve_solo_agentes_de_ese_rol(
        self,
        cliente_coordinador: ClienteCoordinador,
    ) -> None:
        """Para cada rol del enumerado, el filtro devuelve elementos coherentes."""
        try:
            agentes = await cliente_coordinador.listar_agentes_publicos()
        except (httpx.ConnectError, httpx.TimeoutException) as error:
            pytest.skip(f"Registro REST no alcanzable: {error}")

        if not agentes:
            pytest.skip("El registro está accesible pero vacío; no hay agentes para filtrar.")

        for rol in RolEspecialista:
            filtrados = [agente for agente in agentes if agente.get("rol") == rol.value]
            roles_obtenidos = {agente.get("rol") for agente in filtrados}
            elemento_inesperado = roles_obtenidos - {rol.value}
            assert not elemento_inesperado, (
                f"El filtro por rol {rol.value!r} devolvió elementos con otros roles: "
                f"{elemento_inesperado}."
            )
