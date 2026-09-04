import json
from datetime import datetime
from logica.logica_general import *

def _obtener_dict(entrada: object) -> dict:
    """Convierte una entrada tipo dict o msg.body en un diccionario."""
    if isinstance(entrada, dict):
        return entrada

    if hasattr(entrada, "body"):
        return json.loads(entrada.body)

    return {}

def verificarAlerta(msg: object) -> bool:
    """Verifica si la alerta recibida tiene el formato y los datos esperados."""
    datosAlerta = _obtener_dict(msg)

    datosEsperados = {
        "id_emergencia",
        "texto",
    }

    if datosEsperados.issubset(datosAlerta.keys()):
        return True

    return False

def texto_es_suficiente(texto: str) -> bool:
    """Comprueba si el texto tiene una longitud mínima para ser procesado."""
    return len(texto.strip()) >= 10

def generar_propuesta(alerta: dict) -> dict:
    """Genera una propuesta para el Contract Net."""
    # Lógica simple: tiempo estimado basado en la prioridad (si existe)
    prioridad = alerta.get("prioridad", "media")
    tiempos = {"baja": 15, "media": 10, "alta": 5, "critica": 3}
    
    return {
        "tipo_mensaje": "propuesta",
        "id_emergencia": alerta.get("id_emergencia", "DESCONOCIDO"),
        "agente_origen": "policia",
        "tiempo_estimado_min": tiempos.get(prioridad, 10),
        "recursos_disponibles": ["Patrulla Z-1", "Unidad Tráfico"],
        "coste": 100,
        "marca_temporal": datetime.now().isoformat(),
    }

def procesarAlertaAceptada(datosAlerta: dict, agente: object = None) -> dict:
    """Procesa una alerta que ha sido aceptada y prepara el informe de actuación."""
    informe_actuacion = {
        "tipo_mensaje": "informe_actuacion",
        "id_emergencia": datosAlerta.get("id_emergencia", "DESCONOCIDO"),
        "agente_origen": "policia",
        "estado": "recibido",
        "detalle": "Policia preparada para salir hacia la emergencia",
        "recursos_desplegados": 2,
        "marca_temporal": datetime.now().isoformat(),
    }

    if agente is not None:
        agente.calleEmergencia = datosAlerta.get("ubicacion", {}).get(
            "direccion", "Desconocida"
        )

    return informe_actuacion

def procesarAlertaRechazada(msg: object) -> dict:
    """Procesa el caso en el que la alerta es rechazada por falta de datos."""
    datosAlerta = _obtener_dict(msg)

    return {
        "tipo_mensaje": "informe_actuacion",
        "id_emergencia": datosAlerta.get("id_emergencia", "DESCONOCIDO"),
        "agente_origen": "policia",
        "estado": "requiere_apoyo",
        "detalle": "La alerta está incompleta",
        "recursos_desplegados": 0,
        "marca_temporal": datetime.now().isoformat(),
    }

def verificarPeticion(msg: object) -> bool:
    """Verifica si la petición de recursos tiene todos los datos necesarios."""
    datosPeticion = _obtener_dict(msg)

    datosEsperados = {
        "tipo_mensaje",
        "id_emergencia",
        "solicitante",
        "destinatario",
        "accion_solicitada",
        "parametros",
        "urgencia",
    }

    if datosEsperados.issubset(datosPeticion.keys()):
        printColor(
            f"[POLICIA] Solicitud {datosPeticion['accion_solicitada']} "
            f"recibida de {datosPeticion['solicitante']}",
            "azul",
        )
        return True

    return False

def procesarPeticionAceptada(contenidoPeticion: dict, agente: object = None) -> dict:
    """Procesa una petición aceptada dependiendo de la acción solicitada."""
    tipoPeticion = contenidoPeticion.get("accion_solicitada")

    if tipoPeticion == "establecer_perimetro":
        radio = contenidoPeticion.get("parametros", {}).get("radio_metros", 0)

        respuestaPeticion = {
            "tipo_mensaje": "respuesta_recurso",
            "id_emergencia": contenidoPeticion.get("id_emergencia", "DESCONOCIDO"),
            "solicitante_original": contenidoPeticion.get("solicitante", "desconocido"),
            "accion_solicitada": tipoPeticion,
            "aceptada": True,
            "tiempo_estimado_minutos": 5,
            "marca_temporal": datetime.now().isoformat(),
        }

        if agente is not None:
            agente.radioPerimetro = radio
            agente.estado = f"actuando (perimetro {agente.radioPerimetro} establecido)"
            calle = getattr(agente, "calleEmergencia", "ubicación desconocida")
            printColor(
                f"[POLICIA] Estableciendo perímetro de {agente.radioPerimetro} en {calle}",
                "azul",
            )

        return respuestaPeticion

    if tipoPeticion == "zona_segura":
        respuestaPeticion = {
            "tipo_mensaje": "respuesta_recurso",
            "id_emergencia": contenidoPeticion.get("id_emergencia", "DESCONOCIDO"),
            "solicitante_original": contenidoPeticion.get("solicitante", "desconocido"),
            "accion_solicitada": tipoPeticion,
            "aceptada": True,
            "tiempo_estimado_minutos": 5,
            "marca_temporal": datetime.now().isoformat(),
        }

        if agente is not None:
            agente.radioPerimetro = 0
            agente.estado = "finalizado (perímetro quitado)"

        return respuestaPeticion

    return {}

def procesarPeticionRechazada(peticion: object) -> dict:
    """Genera una respuesta de rechazo cuando la petición no tiene un formato correcto."""
    contenidoPeticion = _obtener_dict(peticion)

    return {
        "tipo_mensaje": "respuesta_recurso",
        "id_emergencia": contenidoPeticion.get("id_emergencia", "DESCONOCIDO"),
        "solicitante_original": contenidoPeticion.get("solicitante", "desconocido"),
        "accion_solicitada": contenidoPeticion.get("accion_solicitada", "desconocido"),
        "aceptada": False,
        "motivo": "El formato del mensaje no es correcto",
        "tiempo_estimado_minutos": 0,
        "marca_temporal": datetime.now().isoformat(),
    }