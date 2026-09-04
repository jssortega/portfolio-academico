"""Pruebas unitarias del cierre ordenado del modo examen.

Cuando el Agente Supervisor del profesor se detiene, expulsa a los
ocupantes de las salas del examen y destruye dichas salas. El servidor
avisa de ello a cada agente del alumno con una presencia ``unavailable``
que lleva un código de estado MUC: 307 (expulsado) o 332 (sala
destruida). La utilidad ``registrar_cierre_ordenado_examen`` deja al
agente preparado para detectar esa señal y finalizar de forma ordenada
(``agente.stop()``), en lugar de quedarse esperando mensajes que ya no
llegarán o fallar al enviar a una sala que ya no existe.

Estas pruebas verifican la lógica de detección (funciones puras) sin
necesidad de un servidor XMPP ni de un agente real.
"""
import xml.etree.ElementTree as ET
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from utils import (
    CODIGO_MUC_AUTOPRESENCIA,
    CODIGO_MUC_EXPULSADO,
    CODIGO_MUC_SALA_DESTRUIDA,
    _es_fin_de_examen,
    _extraer_codigos_estado_muc,
    registrar_cierre_ordenado_examen,
)

_NS_MUC_USER = "http://jabber.org/protocol/muc#user"


def _presencia_simulada(*codigos: str, con_elemento_x: bool = True):
    """Construye un objeto presencia simulado con un elemento
    ``muc#user`` que contiene los códigos de estado indicados.

    Reproduce solo el atributo ``xml`` (un árbol ElementTree), que es
    lo único que ``_extraer_codigos_estado_muc`` consulta. Así la
    prueba no necesita construir una stanza real de slixmpp.
    """
    raiz = ET.Element("{jabber:client}presence")
    if con_elemento_x:
        elemento_x = ET.SubElement(raiz, f"{{{_NS_MUC_USER}}}x")
        for codigo in codigos:
            ET.SubElement(
                elemento_x, f"{{{_NS_MUC_USER}}}status", {"code": codigo},
            )
    return SimpleNamespace(xml=raiz)


class TestExtraerCodigosEstadoMuc:
    """Verifica la extracción de los códigos ``<status>`` del elemento
    ``muc#user`` de una presencia."""

    def test_extrae_varios_codigos(self):
        """Devuelve todos los códigos presentes en el elemento x."""
        presencia = _presencia_simulada(
            CODIGO_MUC_AUTOPRESENCIA, CODIGO_MUC_EXPULSADO,
        )
        assert _extraer_codigos_estado_muc(presencia) == {"110", "307"}

    def test_extrae_codigo_unico(self):
        """Una presencia con un solo código devuelve un conjunto de
        un elemento."""
        presencia = _presencia_simulada(CODIGO_MUC_SALA_DESTRUIDA)
        assert _extraer_codigos_estado_muc(presencia) == {"332"}

    def test_sin_elemento_x_devuelve_conjunto_vacio(self):
        """Una presencia sin elemento ``muc#user`` no tiene códigos."""
        presencia = _presencia_simulada(con_elemento_x=False)
        assert _extraer_codigos_estado_muc(presencia) == set()

    def test_elemento_x_sin_status_devuelve_conjunto_vacio(self):
        """Un elemento ``muc#user`` sin ``<status>`` da conjunto vacío."""
        presencia = _presencia_simulada()
        assert _extraer_codigos_estado_muc(presencia) == set()


class TestEsFinDeExamen:
    """Verifica la decisión de si unos códigos de estado MUC indican
    que el examen ha terminado para este agente."""

    @pytest.mark.parametrize(
        "codigos",
        [
            {"110", "307"},          # autopresencia + expulsado
            {"110", "332"},          # autopresencia + sala destruida
            {"110", "307", "100"},   # con códigos adicionales irrelevantes
        ],
    )
    def test_fin_de_examen_detectado(self, codigos):
        """La propia presencia (110) saliendo por expulsión (307) o
        destrucción (332) sí es fin de examen."""
        assert _es_fin_de_examen(codigos) is True

    @pytest.mark.parametrize(
        "codigos",
        [
            {"307"},                 # expulsado, pero NO es autopresencia
            {"332"},                 # sala destruida, pero NO autopresencia
            {"110"},                 # autopresencia, pero salida normal
            {"110", "100"},          # autopresencia + código irrelevante
            set(),                   # sin códigos
        ],
    )
    def test_no_es_fin_de_examen(self, codigos):
        """Sin el código de autopresencia (110), o sin expulsión ni
        destrucción, NO se considera fin de examen."""
        assert _es_fin_de_examen(codigos) is False

    def test_salida_de_otro_ocupante_no_detiene_al_agente(self):
        """Una presencia de expulsión SIN el código 110 corresponde a
        la salida de OTRO ocupante, no a la de este agente: no debe
        interpretarse como fin de examen."""
        assert _es_fin_de_examen({"307"}) is False


class TestRegistroDelManejador:
    """Verifica que la utilidad registra el manejador de presencia en
    el cliente XMPP del agente."""

    def test_registra_manejador_de_presencia(self):
        """``registrar_cierre_ordenado_examen`` añade un manejador del
        evento ``presence`` al cliente del agente."""
        agente = SimpleNamespace(client=MagicMock(), jid="jugador@x")
        registrar_cierre_ordenado_examen(
            agente, "pc-05@examen.sinbad2.ujaen.es",
        )
        agente.client.add_event_handler.assert_called_once()
        evento = agente.client.add_event_handler.call_args[0][0]
        assert evento == "presence"
