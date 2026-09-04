import importlib
import json
import inspect
import pytest
from spade.message import Message
from logica.logica_policia import *
from agentes.agente_policia import AgentePolicia
from logica import logica_policia
import typing


class DummyMsg:
    def __init__(self, body_dict):
        self.body = json.dumps(body_dict)


class DummyAgente:
    pass


def test_logica_policia_tiene_funcion_publica():
    try:
        modulo = importlib.import_module("logica.logica_policia")
    except ModuleNotFoundError:
        assert False, "El módulo logica_policia.py no existe"

    funciones_publicas = [
        nombre for nombre, obj in inspect.getmembers(modulo, inspect.isfunction)
        if not nombre.startswith("_")
    ]

    assert len(funciones_publicas) > 0, "logica_policia.py no tiene funciones públicas"


def test_procesar_alerta_devuelve_informe():
    contenido_alerta = {
        "tipo_mensaje": "alerta_emergencia",
        "id_emergencia": "INC-2026-042",
        "tipo_emergencia": "incendio",
        "ubicacion": {
            "direccion": "Calle Olivar 123",
            "coordenadas": {"latitud": 40.7128, "longitud": -74.0060}
        },
        "prioridad": "alta",
        "descripcion": "Incendio en un edificio de oficinas, humo visible en la planta baja.",
        "marca_temporal": "2026-03-06T14:30:00Z"
    }

    policia = DummyAgente()

    msg = Message()
    msg.body = json.dumps(contenido_alerta)

    informe = None

    alertaValida = verificarAlerta(msg)
    if alertaValida:
        # procesarAlertaAceptada espera un dict, no un string JSON
        informe = procesarAlertaAceptada(json.loads(msg.body), policia)
    else:
        informe = procesarAlertaRechazada(msg)

    assert isinstance(informe, dict), "El resultado debe ser un diccionario"

    claves_esperadas = {"tipo_mensaje", "id_emergencia", "agente_origen", "estado", "detalle", "recursos_desplegados", "marca_temporal"}
    assert claves_esperadas.issubset(informe.keys()), \
        f"Faltan claves en el informe: {claves_esperadas - informe.keys()}"


def test_procesar_alerta_estado_inicial():
    contenido_alerta = {
        "tipo_mensaje": "alerta_emergencia",
        "id_emergencia": "INC-2026-042",
        "tipo_emergencia": "incendio",
        "ubicacion": {
            "direccion": "Calle Olivar 123",
            "coordenadas": {"latitud": 40.7128, "longitud": -74.0060}
        },
        "prioridad": "alta",
        "descripcion": "Incendio en un edificio de oficinas, humo visible en la planta baja.",
        "marca_temporal": "2026-03-06T14:30:00Z"
    }

    policia = DummyAgente()

    msg = Message()
    msg.body = json.dumps(contenido_alerta)

    informe = None

    alertaValida = verificarAlerta(msg)
    if alertaValida:
        informe = procesarAlertaAceptada(json.loads(msg.body), policia)
    else:
        informe = procesarAlertaRechazada(msg)

    assert informe["estado"] in ("recibido", "en_camino"), \
        "El estado inicial debe ser 'recibido' o 'en_camino'"


def test_procesar_alerta_con_datos_incompletos():
    contenido_alerta = {
        "tipo_mensaje": "alerta_emergencia",
        "id_emergencia": "INC-2026-042",
        # falta tipo_emergencia — alerta incompleta
        "ubicacion": {
            "direccion": "Calle Olivar 123",
            "coordenadas": {"latitud": 40.7128, "longitud": -74.0060}
        },
        "prioridad": "alta",
        "descripcion": "Incendio en un edificio de oficinas, humo visible en la planta baja.",
        "marca_temporal": "2026-03-06T14:30:00Z"
    }

    policia = DummyAgente()

    msg = Message()
    msg.body = json.dumps(contenido_alerta)

    informe = None

    alertaValida = verificarAlerta(msg)
    if alertaValida:
        informe = procesarAlertaAceptada(json.loads(msg.body), policia)
    else:
        informe = procesarAlertaRechazada(msg)

    assert informe["estado"] == "requiere_apoyo", \
        "El estado debe ser 'requiere_apoyo' cuando haya datos incompletos"


def obtener_objetos_publicos():
    objetos = []
    for nombre, objeto in inspect.getmembers(logica_policia):
        es_publico = not nombre.startswith("_")
        es_propio = getattr(objeto, "__module__", "") == logica_policia.__name__
        if es_publico and es_propio and (inspect.isfunction(objeto) or inspect.isclass(objeto)):
            objetos.append((nombre, objeto))
    return objetos

def test_typing_hints_presentes():
    objetos = obtener_objetos_publicos()
    for nombre, objeto in objetos:
        if inspect.isfunction(objeto):
            hints = typing.get_type_hints(objeto)
            firma = inspect.signature(objeto)
            for nombre_param in firma.parameters:
                if nombre_param not in ['self', 'cls']:
                    assert nombre_param in hints
            assert 'return' in hints

def test_docstrings_presentes():
    objetos = obtener_objetos_publicos()
    for nombre, objeto in objetos:
        doc = inspect.getdoc(objeto)
        assert doc is not None and str(doc).strip() != ""

def test_cobertura_caminos_correctos():
    msg_valido = DummyMsg({
        "tipo_mensaje": "req", "id_emergencia": "INC-1", "tipo_emergencia": "robo",
        "ubicacion": {"direccion": "Calle 1"}, "prioridad": "alta",
        "descripcion": "robo", "marca_temporal": "ahora"
    })
    assert logica_policia.verificarAlerta(msg_valido) is True

    agente = DummyAgente()
    res_aceptada = logica_policia.procesarAlertaAceptada(json.loads(msg_valido.body), agente)
    assert res_aceptada["estado"] == "recibido"
    assert getattr(agente, "calleEmergencia", None) == "Calle 1"

    msg_peticion = DummyMsg({
        "tipo_mensaje": "req", "id_emergencia": "INC-1", "solicitante": "bomberos",
        "destinatario": "policia", "accion_solicitada": "establecer_perimetro",
        "parametros": {"radio_metros": 100}, "urgencia": "alta"
    })
    assert logica_policia.verificarPeticion(msg_peticion) is True

    res_pet = logica_policia.procesarPeticionAceptada(json.loads(msg_peticion.body), agente)
    assert res_pet["aceptada"] is True
    assert getattr(agente, "radioPerimetro", None) == 100

def test_cobertura_casos_limite():
    msg_invalido = DummyMsg({"id_emergencia": "1"})
    assert logica_policia.verificarAlerta(msg_invalido) is False

    res_rechazo = logica_policia.procesarAlertaRechazada(msg_invalido)
    assert res_rechazo["estado"] == "requiere_apoyo"

    assert logica_policia.verificarPeticion(msg_invalido) is False

    res_pet_rechazo = logica_policia.procesarPeticionRechazada(msg_invalido)
    assert res_pet_rechazo["aceptada"] is False