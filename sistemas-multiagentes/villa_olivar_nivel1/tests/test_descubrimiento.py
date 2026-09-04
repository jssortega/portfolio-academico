import pytest
from descubrimiento.df_utils import *
from agentes.agente_bomberos import *
from agentes.agente_policia import *
from agentes.agente_centralita import *
from descubrimiento.agente_df import *


import pytest
import json
import asyncio

pytestmark = pytest.mark.asyncio

async def test_registro_servicio():
    policia = AgentePolicia("policia@localhost", "password")
    df = AgenteDF("df_multi007s@localhost", "df_multi007s_pass")

    await df.start(auto_register=True)
    await policia.start()

    await asyncio.sleep(50)  # dar tiempo a registro / behaviours

    print(f"::::::::::::REGISTRO {df.directorio}")

    assert "policia" in df.directorio, "No se ha registrado correctamente el agente en el DF"

    assert policia.respuestaDF.get_metadata("performative") == "inform", "El mensaje no coincide con el estado del DF"

    await policia.stop()
    await df.stop()


async def test_busqueda_servicio_existente():
    policia = AgentePolicia("policia@localhost", "password")
    df = AgenteDF("df_multi007s@localhost", "df_multi007s_pass")
    centralita = AgenteCentralita("centralita@localhost", "password")

    await df.start(auto_register=True)
    await policia.start()
    await centralita.start()

    await asyncio.sleep(50)  # dar tiempo a registro / behaviours
    
    assert ['policia@localhost'] in centralita.agentesEncontrados, "No se ha encontrado el agente registrado"

    await policia.stop()
    await df.stop()
    await centralita.stop()


async def test_busqueda_servicio_inexistente():
    df = AgenteDF("df_multi007s@localhost", "df_multi007s_pass")
    centralita = AgenteCentralita("centralita@localhost", "password")

    await df.start(auto_register=True)
    await centralita.start()

    await asyncio.sleep(50)  # dar tiempo a registro / behaviours
    
    assert len(centralita.agentesEncontrados) == 0, "Se han encontrado agentes, cuando no hay ninguno activo"

    await df.stop()
    await centralita.stop()


async def test_tolerancia_agente_ausente():
    df = AgenteDF("df_multi007s@localhost", "df_multi007s_pass")
    centralita = AgenteCentralita("centralita@localhost", "password")

    await df.start(auto_register=True)
    await centralita.start()

    await asyncio.sleep(50)  # dar tiempo a registro / behaviours
    
    assert len(centralita.agentesEncontrados) == 0, "Se han encontrado agentes, cuando no hay ninguno activo"

    await df.stop()
    await centralita.stop()