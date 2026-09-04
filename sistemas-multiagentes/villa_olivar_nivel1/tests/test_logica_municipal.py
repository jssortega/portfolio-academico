from logica import logica_municipal
from logica.logica_municipal import *
import pytest
import inspect
import typing


def test_modulo_existe_y_tiene_funcion_publica():
    #existe
    assert callable(procesar_alerta_municipal)

def test_procesar_alerta_devuelve_informe():
    #hay diccionario con las claves
    datos_ejemplo = {"tipo_emergencia": "derrame_quimico", "ubicacion": "Avda. Madrid"}
    
    resultado = procesar_alerta_municipal(datos_ejemplo)
    
    assert isinstance(resultado, dict)
    assert "informe_centralita" in resultado
    
    informe = resultado["informe_centralita"]
    assert "agente_origen" in informe  
    assert "estado" in informe

def test_procesar_alerta_estado_inicial():
    resultado = procesar_alerta_municipal({})
  
    estado_actual = resultado["informe_centralita"]["estado"]

    estados_validos = ["recibido", "en_camino", "esperando_ordenes"]
    assert estado_actual in estados_validos

def test_procesar_alerta_con_datos_incompletos():
    #dccionario datos incompletos
    try:
        procesar_alerta_municipal({})
    except Exception as e:
        pytest.fail(f"La función lanzó una excepción con datos vacíos: {e}")

def obtener_objetos_publicos():
    objetos = []
    for nombre, objeto in inspect.getmembers(logica_municipal):
        es_publico = not nombre.startswith("_")
        es_propio = getattr(objeto, "__module__", "") == logica_municipal.__name__
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
    alerta = {"id_emergencia": "INC-123", "tipo_emergencia": "derrame_quimico"}
    res = logica_municipal.procesar_alerta_municipal(alerta)
    assert res["informe_centralita"]["detalle"] != ""

    solicitud = {"accion_solicitada": "cortar_gas", "id_emergencia": "INC-123"}
    res_sol = logica_municipal.procesar_solicitud_municipal(solicitud)
    assert res_sol["aceptada"] is True

def test_cobertura_casos_limite():
    res = logica_municipal.procesar_alerta_municipal({})
    assert res["informe_centralita"]["id_emergencia"] == "DESCONOCIDO"

    res_sol = logica_municipal.procesar_solicitud_municipal({"accion_solicitada": "limpiar_calle"})
    assert isinstance(res_sol["aceptada"], bool)