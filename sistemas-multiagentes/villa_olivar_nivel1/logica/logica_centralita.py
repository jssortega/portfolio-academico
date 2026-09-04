"""
Autor(es): Cristina Silva (csu0002@ujaen.es)
Grupo: multi007s

Agente centralita: agente central que contactará con los agentes especialistas
"""

from datetime import datetime, timezone

# Contador de emergencias
_contador_emergencias = 0 #necesario para las pruebas de la centralita: llevar un conteo secuencial



#Vamos a definir mapas con los casos reales posibles y los destinatarios
# Qué cuerpos atienden cada tipo de emergencia
_DESTINATARIOS_POR_TIPO = {
    "derrame_quimico":   ["bomberos", "sanitario", "policia", "municipal"],
    "incendio":          ["bomberos", "sanitario", "policia"],
    "accidente_trafico": ["sanitario", "policia"],
    "inundacion":        ["bomberos", "municipal", "policia"],
    "explosion":         ["bomberos", "sanitario", "policia", "municipal"],
    "otro":              ["bomberos", "sanitario"],
}

# Prioridad base de cada tipo de emergencia
_PRIORIDAD_BASE = {
    "derrame_quimico":   "alta",
    "incendio":          "alta",
    "accidente_trafico": "media",
    "inundacion":        "media",
    "explosion":         "critica",
    "otro":              "baja",
}

# Escala de prioridades de menor a mayor
_NIVELES_PRIORIDAD = ["baja", "media", "alta", "critica"]


def generar_id_emergencia() -> str:
    """Genera un identificador único con formato INC-AAAA-NNN.
    Returns:
        Cadena con formato 'INC-AAAA-NNN', por ejemplo 'INC-2026-001'.
    """
    global _contador_emergencias #para que pueda acceder a la variable fuera de la clase
    _contador_emergencias += 1
    anio = datetime.now(timezone.utc).year #horario actual
    return f"INC-{anio}-{_contador_emergencias:03d}"


def clasificar_emergencia(
    tipo_emergencia: str, #para comprobar en nuestro diccionario
    hay_heridos: bool = False, #por defecto no hay heridos
    materiales_peligrosos: bool = False, #por defecto no habrá
    numero_afectados: int = 0, #esto se podrá incrementar
) -> str:
    """Determina la prioridad de una emergencia según sus características."""
    # Si el tipo no existe en el mapa, usamos prioridad "media" por defecto
    prioridad = _PRIORIDAD_BASE.get(tipo_emergencia, "media")
    indice = _NIVELES_PRIORIDAD.index(prioridad)

    # Agravantes que suben la prioridad
    if materiales_peligrosos or numero_afectados > 10:
        indice = 3  # critica (último nivel)
    elif hay_heridos and indice < 3:
        indice += 1  # sube un nivel

    return _NIVELES_PRIORIDAD[indice]


def determinar_destinatarios(tipo_emergencia: str) -> list:
    """Devuelve la lista de cuerpos que deben recibir la alerta. """
    destinatarios = _DESTINATARIOS_POR_TIPO.get(tipo_emergencia, _DESTINATARIOS_POR_TIPO["otro"])
    return list(destinatarios)


def resetear_contador() -> None:
    """Reinicia el contador de emergencias a cero. Solo se usa en los tests."""
    global _contador_emergencias
    _contador_emergencias = 0