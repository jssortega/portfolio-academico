from datetime import datetime
import uuid
from typing import Any


def procesar_alerta_municipal(datos_alerta: dict) -> dict:
    id_emergencia = datos_alerta.get("id_emergencia", "DESCONOCIDO")
    tipo = datos_alerta.get("tipo_emergencia", "generica").lower()

    urgencia = "urgente" if "quimico" in tipo or "incendio" in tipo else "normal"
    necesita_policia = True if "calle" in tipo or "accidente" in tipo else False

    evaluacion = {
        "nivel": urgencia,
        "accion": "limpieza" if "quimico" in tipo else "reparacion",
        "necesita_policia": necesita_policia
    }

    informe_centralita = {
        "tipo_mensaje": "informe_actuacion",
        "id_emergencia": id_emergencia,
        "agente_origen": "municipal",
        "estado": "en_camino",
        "detalle": f"Brigada municipal activada para {evaluacion['accion']}.",
        "marca_temporal": datetime.now().isoformat()
    }

    recursos_policia = None
    if necesita_policia:
        recursos_policia = {
            "tipo_mensaje": "solicitud_recurso",
            "id_emergencia": id_emergencia,
            "solicitante": "municipal",
            "destinatario": "policia",
            "accion_solicitada": "cortar_calle",
            "parametros": {"motivo": "seguridad_operarios"},
            "urgencia": urgencia,
            "marca_temporal": datetime.now().isoformat()
        }

    return {
        "evaluacion": evaluacion,
        "informe_centralita": informe_centralita,
        "recursos_policia": recursos_policia,
        "recursos_bomberos": None
    }


def procesar_solicitud_municipal(datos_solicitud: dict) -> dict:
    accion = datos_solicitud.get("accion_solicitada", "")
    return {
        "aceptada": True,
        "detalle": f"Acción '{accion}' ejecutada por Servicios Municipales.",
        "tipo_mensaje": "respuesta_recurso"
    }


def finalizar_intervencion_municipal(id_emergencia: str) -> dict:
    return {
        "id_emergencia": id_emergencia,
        "agente_origen": "municipal",
        "estado": "finalizado",
        "detalle": "Intervención de mantenimiento y limpieza completada de manera segura.",
        "marca_temporal": datetime.now().isoformat()
    }



def generar_propuestas_municipal(subtarea: dict) -> list[dict]:
    """
    Genera dos propuestas estructuradas y distintas procedentes de dos
    unidades operativas internas (Brigada Centro y Brigada Norte).
    """
    id_subtarea = subtarea.get("id_subtarea", str(uuid.uuid4()))
    tipo_accion = subtarea.get("accion", "reparacion_infraestructura")

    propuesta_alfa = {
        "id_propuesta": f"prop-mun-alfa-{id_subtarea[:6]}",
        "unidad": "Brigada Municipal Centro",
        "tiempo_estimado_minutos": 12,
        "recursos_desplegados": ["Furgón de intervención rápida", "3 operarios especialistas"],
        "coste_estimado": 350.0,
        "cobertura": "alta",
        "detalle": f"Despliegue inmediato para {tipo_accion} desde base central."
    }

    propuesta_beta = {
        "id_propuesta": f"prop-mun-beta-{id_subtarea[:6]}",
        "unidad": "Brigada Municipal Norte",
        "tiempo_estimado_minutos": 22,
        "recursos_desplegados": ["Camión grúa ligero", "2 operarios"],
        "coste_estimado": 190.0,
        "cobertura": "media",
        "detalle": f"Unidad disponible en sector norte lista para actuar en {tipo_accion}."
    }

    texto_alerta = str(subtarea.get("texto", "")).lower()

    if "victima" in texto_alerta or "herido" in texto_alerta or tipo_accion == "soporte_medico_leve":
        propuesta_alfa["recursos_desplegados"].append("1 Técnico de Emergencias (Apoyo)")
        propuesta_alfa["coste_estimado"] += 50.0
        propuesta_beta["detalle"] += " Incluye botiquín de soporte logístico."

    return [propuesta_alfa, propuesta_beta]


def evaluar_resultado_ejecucion(id_propuesta: str, forzar_fallo: bool = False) -> dict:
    """
    Determina las acciones realizadas y los recursos empleados finales.
    Permite simular fallos localizados para probar reintentos en Centralita.
    """
    if forzar_fallo:
        return {
            "completado": False,
            "motivo_fallo": "Avería mecánica en el vehículo de la brigada municipal durante el trayecto.",
            "acciones_realizadas": [],
            "recursos_empleados": []
        }

    if "alfa" in id_propuesta:
        return {
            "completado": True,
            "acciones_realizadas": ["Acordonamiento de zona segura", "Reparación exprés de desperfecto en calzada"],
            "recursos_empleados": ["Furgón de intervención rápida", "3 operarios especialistas"],
            "observaciones": "Intervención ejecutada con éxito en tiempo récord por Brigada Centro."
        }
    else:
        return {
            "completado": True,
            "acciones_realizadas": ["Limpieza perimetral", "Colocación de señalización provisional"],
            "recursos_empleados": ["Camión grúa ligero", "2 operarios"],
            "observaciones": "Intervención de soporte completada por Brigada Norte."
        }