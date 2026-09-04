# Carpeta `agentes/` — Ubicación de los agentes del alumno

## Qué se espera

El lanzador (`main.py`) carga dinámicamente dos clases mediante
`importlib`. Para que la prueba de examen funcione, esta carpeta debe
contener los dos ficheros del alumno:

| Fichero                     | Clase           | Módulo                   |
|-----------------------------|-----------------|--------------------------|
| `agentes/agente_jugador.py` | `AgenteJugador` | `agentes.agente_jugador` |
| `agentes/agente_tablero.py` | `AgenteTablero` | `agentes.agente_tablero` |

Ambas clases son las que el alumno ha desarrollado durante el
curso. El lanzador del examen emplea **el mismo contrato** que los
torneos previos (mismos behaviours, misma forma de inyección de la
configuración), de modo que **no es necesario adaptarlas** al modo
examen.


## Implementación de referencia publicada por el profesor

La rama del examen incluye en esta carpeta una **implementación de
referencia** completa de cada una de las dos clases:

- `agente_tablero.py`: arbitra una partida real intercambiando los
  mensajes FIPA-ACL de la ontología (registro, partida e informe).
- `agente_jugador.py`: se inscribe, recibe su símbolo y juega la
  partida con la estrategia posicional de nivel 1.
- `reglas_juego.py`: lógica pura del tres en raya (validar, aplicar,
  detectar línea, evaluar resultado), compartida por ambos agentes.

A diferencia de un esqueleto, esta implementación **resuelve
correctamente los tres protocolos** y supera la serie de pruebas de
la rama. Su finalidad es doble:

1. Servir de **referencia** del comportamiento que esperan las
   pruebas de `tests/` (protocolos de la ontología, factoría y JID).
2. Servir de **punto de partida**: el alumno puede conservar el
   protocolo ya resuelto y sustituir solo la **estrategia** de
   elección de casilla, o reemplazar por completo los dos ficheros
   por sus propios agentes.

En ambos casos debe respetarse el **contrato de integración**
descrito en
[`doc/INTEGRACION_AGENTES_ALUMNO.md`](../doc/INTEGRACION_AGENTES_ALUMNO.md):
ese documento explica cómo enlazar los agentes del alumno en la rama
y cómo verificarlos con el arnés de simulación.


## Mínimo que debe aportar el alumno al examen

- `agentes/agente_jugador.py` con la clase `AgenteJugador` (subclase
  de `spade.agent.Agent`).
- `agentes/agente_tablero.py` con la clase `AgenteTablero` (subclase
  de `spade.agent.Agent`).
- Cualquier módulo auxiliar que importen sus agentes (estrategia,
  behaviours, ontología, interfaz web, etc.) en sus carpetas
  habituales.


## Acceso a la configuración inyectada por `main.py`

`main.py` inyecta en cada agente, antes de arrancarlo:

- `agente.config_xmpp` — perfil XMPP resuelto, con
  `sala_muc_completa` ya canonizada según `alumno.submodo`.
- `agente.config_parametros` — diccionario con los parámetros
  específicos del agente:
  - `id_tablero` y `puerto_web` (solo tableros).
  - `nivel_estrategia` y `max_partidas` (solo jugadores).
  - `nick_muc` — nick único asignado por la utilidad de generación
    de agentes; se usa al unirse a la sala MUC.
- `agente.config_llm` — perfil LLM resuelto (None si la
  estrategia no usa modelo de lenguaje).

El alumno utiliza estos atributos en su `setup()`:

```python
async def setup(self) -> None:
    sala_muc = self.config_xmpp["sala_muc_completa"]
    nick_propio = self.config_parametros["nick_muc"]
    # ...
```


## Recordatorios de estilo (consistentes con el resto del curso)

- Todo en español: comentarios, docstrings, mensajes de log.
- Docstrings en formato Google Style en toda clase pública.
- Anotaciones de tipo (*typing hints*) en parámetros y retornos.
- Los agentes SPADE son asíncronos: todo en `async/await`.
- No escribir directamente en el código URL, puertos ni JID: leerlos
  de la configuración centralizada (véase `config/`).
