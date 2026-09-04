"""
Todo test tiene el mismo funcionamiento
1ºpreparar datos
2ºejecutar la funcion
3ºComporbar resultado

"""

# Importamos la fecha para poder comprobar el año actual
from datetime import datetime, timezone
import inspect
import typing
from logica import logica_centralita

# Importamos todos los módulos de la lógica
from logica.logica_centralita import (
    clasificar_emergencia,
    determinar_destinatarios,
    generar_id_emergencia,
    resetear_contador
)


def test_clasificar_emergencia_derrame():
    """
    Prueba 1: Un derrame químico debe dar prioridad 'alta' o 'critica'.
    """
    #paso 1: preparamos los datos
    resultado = clasificar_emergencia(
        tipo_emergencia="derrame_quimico",
        hay_heridos=False,
        materiales_peligrosos=True,
        numero_afectados=0
    )

    # 2. Comprobamos con 'assert'. Si lo que sigue es True, el test pasa.
    # Si es False, el test falla y muestra el mensaje.
    assert resultado == "alta" or resultado == "critica", "Fallo: La prioridad no es alta ni crítica"


def test_clasificar_emergencia_accidente_leve():
    """
    Prueba 2: Un accidente leve sin heridos debe dar prioridad 'baja' o 'media'.
    """

    resultado = clasificar_emergencia(
        tipo_emergencia="accidente_trafico",
        hay_heridos=False,
        materiales_peligrosos=False,
        numero_afectados=0
    )

    assert resultado == "baja" or resultado == "media", "Fallo: La prioridad debería ser baja o media"
    #si es true, assert no dice nada, si es falso lanza una excepcion


def test_determinar_destinatarios():
    """
    Prueba 3: Si hay un derrame, los bomberos tienen que ir seguro.
    """

    lista_cuerpos = determinar_destinatarios("derrame_quimico")

    assert "bomberos" in lista_cuerpos, "Fallo: Los bomberos no están en la lista"


def test_generar_id_emergencia_formato():
    """
    Prueba 4: El ID debe tener el formato exacto "INC-AAAA-NNN".
    """
    # IMPORTANTE: Ponemos el contador a 0 o tendremos problemas con los ID.
    resetear_contador()

    # 1. Generamos el ID
    id_generado = generar_id_emergencia()

    # 2. Vamos a partir el texto por los guiones para comprobar cada trozo
    partes = id_generado.split("-")  #Por ejemplo ["INC", "2026", "001"]

    # Comprobación A: Tienen que salir exactamente 3 trozos
    assert len(partes) == 3, "Fallo: El ID no tiene 3 partes separadas por guiones"

    # Comprobación B: El primer trozo debe ser "INC"
    assert partes[0] == "INC", "Fallo: El ID no empieza por INC"

    # Comprobación C: El segundo trozo (año) debe tener 4 letras y ser todo números (isdigit)
    assert len(partes[1]) == 4, "Fallo: El año no tiene 4 cifras"
    assert partes[1].isdigit(), "Fallo: El año contiene letras en vez de números"

    # Comprobación D: El tercer trozo (contador) debe tener 3 letras y ser números
    assert len(partes[2]) == 3, "Fallo: El contador no tiene 3 cifras"
    assert partes[2].isdigit(), "Fallo: El contador contiene letras en vez de números"



def obtener_objetos_publicos():
    objetos = []
    for nombre, objeto in inspect.getmembers(logica_centralita):
        es_publico = not nombre.startswith("_")
        es_propio = getattr(objeto, "__module__", "") == logica_centralita.__name__
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
    logica_centralita.resetear_contador()
    id_emerg = logica_centralita.generar_id_emergencia()
    assert "INC-" in id_emerg
    assert id_emerg.endswith("-001")

    prioridad = logica_centralita.clasificar_emergencia("incendio", hay_heridos=True)
    assert prioridad == "critica"

    dests = logica_centralita.determinar_destinatarios("incendio")
    assert "bomberos" in dests
    assert "sanitario" in dests

def test_cobertura_casos_limite():
    prioridad_desconocida = logica_centralita.clasificar_emergencia("alienigena")
    assert prioridad_desconocida == "media"

    dests_desconocido = logica_centralita.determinar_destinatarios("alienigena")
    assert "bomberos" in dests_desconocido
    assert "sanitario" in dests_desconocido


def test_logica_sin_dependencias():
    """Hito 1: Verifica que el módulo de lógica no importa SPADE, ADK ni LLM."""
    from pathlib import Path
    ruta_logica = Path("logica/logica_centralita.py")
    contenido = ruta_logica.read_text(encoding="utf-8")
    
    prohibidos = ["import spade", "spade_llm", "google.adk", "google.genai"]
    for p in prohibidos:
        assert p not in contenido, f"La lógica no debe depender de {p}"