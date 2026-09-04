import pytest
from logica import logica_bomberos
import inspect
import typing

#Mensajes de prueba
ALERTA_CORRECTA = {
    "tipo_mensaje": "alerta_emergencia",
    "id_emergencia": "INC-2026-001",
    "tipo_emergencia": "derrame_quimico",
    "ubicacion": {"direccion": "Av. Constitución 42"},
    "prioridad": "alta",
    "descripcion": "Derrame de amoniaco en la calzada",
    "marca_temporal": "2026-03-06T10:00:00Z"
}

ALERTA_INCOMPLETA = {
    "tipo_mensaje": "alerta_emergencia",
    "prioridad": "alta"
}

def test_modulo_existe_y_tiene_funcion_publica():
    """
        Comprueba que el módulo existe y tiene la función principal.
    """
    # 1. Verifica que la función existe en el módulo
    assert hasattr(logica_bomberos, 'procesar_alerta'), "La función procesar_alerta_incendio no existe."

    # 2. Verifica que la función se puede ejecutar
    assert callable(logica_bomberos.procesar_alerta), "procesar_alerta_incendio debe ser una función."


def test_procesar_alerta_devuelve_informe():
    """
    Comprueba que al recibir una alerta, devuelve el informe_actuacion.
    """
    resultado = logica_bomberos.procesar_alerta(ALERTA_CORRECTA)

    informe = resultado.get("informe_centralita", {})

    # Verifica las claves obligatorias según tu ontología
    claves_esperadas = ["tipo_mensaje", "id_emergencia", "agente_origen", "estado", "detalle", "marca_temporal"]
    for clave in claves_esperadas:
        assert clave in informe, f"Falta la clave '{clave}' en el informe devuelto."

    assert informe["tipo_mensaje"] == "informe_actuacion"


def test_procesar_alerta_estado_inicial():
    """
    Comprueba que el estado inicial devuelto es 'recibido' o 'en_camino'.
    """
    resultado = logica_bomberos.procesar_alerta(ALERTA_CORRECTA)
    informe = resultado.get("informe_centralita", {})

    assert informe["estado"] in ["recibido", "en_camino"], "El estado inicial no es válido."


def test_procesar_alerta_con_datos_incompletos():
    """
    Comprueba que si faltan datos al mensaje y no devuelve una excepción
    """
    # Llamamos a la función con datos incompletos
    resultado = logica_bomberos.procesar_alerta(ALERTA_INCOMPLETA)
    informe = resultado.get("informe_centralita", {})

    assert informe.get("estado") == "requiere_apoyo", "El estado debe ser 'requiere_apoyo' si faltan datos críticos."



def obtener_objetos_publicos():
    objetos = []
    for nombre, objeto in inspect.getmembers(logica_bomberos):
        es_publico = not nombre.startswith("_")
        es_propio = getattr(objeto, "__module__", "") == logica_bomberos.__name__
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
    datos_alerta = {"id_emergencia": "INC-123", "tipo_emergencia": "derrame_quimico", "descripcion": "amoniaco"}
    res = logica_bomberos.procesar_alerta(datos_alerta)
    assert res["evaluacion"]["sustancia"] == "amoniaco"
    assert res["recursos_municipal"]["accion_solicitada"] == "cortar_gas"

    res_fin = logica_bomberos.finalizar_intervencion("INC-123")
    assert res_fin["estado"] == "finalizado"

def test_cobertura_casos_limite():
    res = logica_bomberos.procesar_alerta({})
    assert res["informe_centralita"]["estado"] == "requiere_apoyo"

    res_quimico = logica_bomberos.evaluar_riesgo_quimico("nada")
    assert res_quimico["sustancia"] == "desconocida"

    res_incendio = logica_bomberos.evaluar_incendio("nada")
    assert res_incendio["tipo"] == "desconocido"