import json
from datetime import datetime
import random

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
    tiempos = {"baja": 12, "media": 8, "alta": 4, "critica": 2}
    
    return {
        "tipo_mensaje": "propuesta",
        "id_emergencia": alerta.get("id_emergencia", "DESCONOCIDO"),
        "agente_origen": "sanitario",
        "tiempo_estimado_min": tiempos.get(prioridad, 8),
        "recursos_disponibles": ["Ambulancia SVA-1", "Equipo Médico A"],
        "coste": 150,
        "marca_temporal": datetime.now().isoformat(),
    }

def procesarAlertaAceptada(datosAlerta: dict, agente: object = None) -> dict:
    """Genera el informe inicial de actuación cuando el sanitario acepta la alerta."""
    return {
        "tipo_mensaje": "informe_actuacion",
        "id_emergencia": datosAlerta.get("id_emergencia", "DESCONOCIDO"),
        "agente_origen": "sanitario",
        "estado": "recibido",
        "detalle": "Sanitario preparada para salir hacia la emergencia",
        "recursos_desplegados": 5,
        "marca_temporal": datetime.now().isoformat(),
    }

def procesarAlertaRechazada(msg: object) -> dict:
    """Genera un informe solicitando apoyo cuando la alerta no tiene el formato correcto."""
    datosAlerta = _obtener_dict(msg)

    return {
        "tipo_mensaje": "informe_actuacion",
        "id_emergencia": datosAlerta.get("id_emergencia", "DESCONOCIDO"),
        "agente_origen": "sanitario",
        "estado": "requiere_apoyo",
        "detalle": "La alerta está incompleta",
        "recursos_desplegados": 0,
        "marca_temporal": datetime.now().isoformat(),
    }

def atenderHeridos(msg: object) -> dict:
    """Genera heridos aleatorios, realiza el triaje y finaliza la actuación."""
    datosAlerta = _obtener_dict(msg)

    heridosG = random.randint(1, 5)
    heridosL = random.randint(1, 10)

    print(
        f"[SANITARIO] Triaje: {heridosL} heridos leves y {heridosG} "
        "heridos graves. Trasladando al hospital"
    )

    return {
        "tipo_mensaje": "informe_actuacion",
        "id_emergencia": datosAlerta.get("id_emergencia", "DESCONOCIDO"),
        "agente_origen": "sanitario",
        "estado": "finalizado",
        "detalle": "Se ha finalizado la alerta",
        "recursos_desplegados": 0,
        "marca_temporal": datetime.now().isoformat(),
    }