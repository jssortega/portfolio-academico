"""
Lógica Bomberos — Villa Olivar (Nivel 1).

Autor: Jesús Ortega Castillo (joc00023@ujaen.es)
Grupo: multi007s
"""

from datetime import datetime
from logica.logica_general import *

# Tipo de residuos que ha podido derramarse
RIESGOS_QUIMICOS = {
    "amoniaco": {"nivel": "urgente", "radio": "500m", "necesita_gas": True},
    "cloro": {"nivel": "inmediata", "radio": "1000m", "necesita_gas": False},
    "gasolina": {"nivel": "normal", "radio": "100m", "necesita_gas": True},
}

RIESGOS_INCENDIO = {
    "casa": {"nivel": "inmediata", "radio": "100m", "necesita_gas": True},
    "bosque": {"nivel": "urgente",   "radio": "1000m", "necesita_gas": False},
    "fabrica": {"nivel": "normal", "radio": "500m", "necesita_gas": True},
}



def evaluar_riesgo_quimico(descripcion: str) -> dict:
    """Metodo que procesa el caso de que haya sido un derrame_quimico"""
    descripcion_normalizada = descripcion.lower()

    for sustancia, datos in RIESGOS_QUIMICOS.items():
        if sustancia in descripcion_normalizada:
            printColor(f"[Bomberos] Evaluando riesgo: sustancia={sustancia} -> nivel={datos['nivel']}, radio={datos['radio']}","rojo")
            return {"sustancia": sustancia, **datos}

    return {
        "sustancia": "desconocida",
        "nivel": "medio",
        "radio": "200m",
        "necesita_gas": False,
    }


def evaluar_incendio(descripcion: str) -> dict:

    """Metodo que procesa el caso de que haya sido un incendio"""
    descripcion_normalizada = descripcion.lower()

    sinonimos_incendio = {
        "casa": ["casa", "vivienda", "piso", "edificio"],
        "bosque": ["bosque", "forestal", "monte", "pinar", "zona arbolada"],
        "fabrica": ["fabrica", "fábrica", "nave industrial", "industria"],
    }

    for tipo, sinonimos in sinonimos_incendio.items():
        for sinonimo in sinonimos:
            if sinonimo in descripcion_normalizada:
                datos = RIESGOS_INCENDIO[tipo]
                printColor(f"[Bomberos] Evaluando riesgo: lugar={tipo} -> nivel={datos['nivel']}, radio={datos['radio']}","rojo")
                return {"tipo": tipo, **datos}

    return {
        "tipo": "desconocido",
        "nivel": "medio",
        "radio": "200m",
        "necesita_gas": False,
    }



def procesar_alerta(datos_alerta: dict) -> dict:
    """Metodo que procesa la alerta recibida"""
    id_emergencia = datos_alerta.get("id_emergencia")
    texto_original = datos_alerta.get("texto", "")
    texto = texto_original.lower()

    tipo = datos_alerta.get("tipo_emergencia")

    if not tipo:
        if any(p in texto for p in ["derrame", "fuga", "químico", "quimico", "cloro", "amoniaco", "gasolina"]):
            tipo = "derrame_quimico"
        elif any(p in texto for p in ["derrumbe", "colapso", "atrapado", "escombros"]):
            tipo = "derrumbe"
        elif any(p in texto for p in ["incendio", "fuego", "humo", "llamas", "explosion", "explosión"]):
            tipo = "incendio"
        else:
            tipo = "otro"

    if tipo == "derrame_quimico":
        evaluacion = evaluar_riesgo_quimico(texto_original)
    elif tipo == "incendio":
        evaluacion = evaluar_incendio(texto_original)
    elif tipo == "derrumbe":
        evaluacion = {
            "tipo": "derrumbe",
            "nivel": "urgente",
            "radio": "300m",
            "necesita_gas": False,
        }
    else:
        evaluacion = {
            "tipo": "desconocido",
            "nivel": "medio",
            "radio": "200m",
            "necesita_gas": False,
        }

    prioridad = datos_alerta.get("prioridad")
    if not prioridad:
        nivel = str(evaluacion.get("nivel", "")).lower()

        if nivel == "inmediata":
            prioridad = "critica"
        elif nivel == "urgente":
            prioridad = "alta"
        else:
            prioridad = "media"

    acciones = []
    recursos = ["dotación de bomberos"]

    if tipo == "incendio":
        acciones.append("Evaluación del foco del incendio.")
        acciones.append("Despliegue de equipo de extinción.")
        acciones.append("Comprobación de propagación de humo y llamas.")

    elif tipo == "derrame_quimico":
        acciones.append("Evaluación de riesgo químico.")
        acciones.append("Aislamiento preventivo de la zona afectada.")
        acciones.append("Preparación de equipo NBQR.")

    elif tipo == "derrumbe":
        acciones.append("Evaluación estructural inicial.")
        acciones.append("Búsqueda de posibles personas atrapadas.")
        acciones.append("Aseguramiento de la zona de intervención.")

    else:
        acciones.append("Evaluación preventiva desde el área de Bomberos.")

    radio = evaluacion.get("radio", "200m")
    recursos.append(f"perímetro de seguridad recomendado de {radio}")

    if evaluacion.get("necesita_gas"):
        recursos.append("corte de gas recomendado")

    observaciones = (
        f"Bomberos ha evaluado la emergencia como '{tipo}', "
        f"con nivel interno '{evaluacion.get('nivel', 'medio')}' "
        f"y prioridad '{prioridad}'."
    )

    return {
        "id_emergencia": id_emergencia,
        "tipo_emergencia": tipo,
        "prioridad": prioridad,
        "evaluacion": evaluacion,
        "completado": True,
        "acciones_realizadas": acciones,
        "recursos_empleados": recursos,
        "observaciones": observaciones,
    }



def finalizar_intervencion(id_emergencia: str) -> dict:
    """Metodo para cuando se finaliza la intervención"""
    return {
        "tipo_mensaje": "informe_actuacion",
        "id_emergencia": id_emergencia,
        "agente_origen": "bomberos",
        "estado": "finalizado",
        "detalle": "Sustancia neutralizada y zona segura.",
        "marca_temporal": datetime.now().isoformat(),

    }
