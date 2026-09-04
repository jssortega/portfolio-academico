# Carpeta `tests/` — Serie de validación de la rama de examen del alumno

## Propósito

Esta carpeta contiene la serie de validación de la rama
`examen-ssmmaa`. Cubre dos planos:

1. **La infraestructura común** de la rama —lanzador, utilidades,
   generación de agentes, normalización de salas y sonda del
   supervisor—, que debe comportarse como cabe esperar antes del
   día del examen.
2. **Los agentes del alumno** —`AgenteTablero` y `AgenteJugador`—,
   cuya conformidad con los tres protocolos de la ontología
   (registro, partida e informe) y cuyo uso correcto de la factoría
   y de los JID se verifican como una caja negra sobre una sala MUC
   simulada.

La serie sirve también de contrato de regresión: cualquier
modificación posterior debe seguir pasándola.

Todas las pruebas se ejecutan con `pytest`. Ninguna requiere un
servidor XMPP real: las de protocolo usan el arnés de simulación de
`tests/simuladores/`. La etiqueta `integration` queda registrada en
`pytest.ini` para los tests con XMPP que se añadan en el futuro.

## Ficheros de prueba

### Conformidad de los agentes del alumno

Verifican que `AgenteTablero` y `AgenteJugador` cumplen los
protocolos de la ontología y se integran bien en la rama. Usan el
arnés de simulación de `tests/simuladores/` (sala MUC en memoria y
oráculos del agente contrario). Se documentan en
[`doc/INTEGRACION_AGENTES_ALUMNO.md`](../doc/INTEGRACION_AGENTES_ALUMNO.md).

| Fichero | Componente verificado |
|---------|-----------------------|
| `test_protocolo_registro.py` | Protocolo de registro (`join`): el jugador difunde una solicitud válida y el tablero responde con `join-accepted`, `join-refused` o `join-timeout`. |
| `test_protocolo_partida.py` | Protocolo de juego (`turn`/`move`): `game-start`, convocatoria de turnos, confirmación de jugadas, abortos por jugada inválida o timeout y partida completa entre agentes reales. |
| `test_protocolo_informe.py` | Protocolo de informe (`game-report`): el tablero responde `INFORM` con el informe tras la partida y `REFUSE` mientras sigue en curso. |
| `test_factoria_jid.py` | Uso de la factoría `crear_agente` y de los JID/nick: el agente toma el JID del perfil activo, se une con su `nick_muc` y direcciona por nick. |

### Infraestructura común de la rama

| Fichero | Componente verificado |
|---------|-----------------------|
| `test_generacion_agentes.py` | Generación automática de agentes para las cuatro combinaciones modalidad/submodo (`laboratorio`, `torneo`, `examen` + `grupo`, `examen` + `individual`). |
| `test_normalizacion_salas.py` | Canonización del nombre de la sala MUC (`normalizar_nombre_sala`): `PC-5`, `pc-05`, `PC_5`, `pc 5`… se resuelven a una forma común. |
| `test_nicks_alumno.py` | Generación de nicks únicos en la sala MUC: fallback a `usuario_uja`, sufijos `-NN` y `-n<L>-NN`, unicidad por submodo. |
| `test_cierre_ordenado_examen.py` | Utilidad `registrar_cierre_ordenado_examen`: códigos de estado MUC y decisión de fin del examen (110 + 307 o 332). |
| `test_configuracion_examen.py` | Resolución de la configuración del examen: agentes y sala por submodo, y selector del perfil LLM. Las pruebas del perfil LLM solo se evalúan si `config.yaml` declara el nivel 4 en `alumno.niveles_estrategia`; en caso contrario se omiten (el nivel 4 es opcional). |
| `test_sonda_supervisor.py` | Sonda `comprobar_supervisor_activo` (XEP-0030 mockeada) e integración con `main.arrancar_sistema`. |

## Orden de ejecución recomendado

```bash
# 1. Toda la serie de validación (rápida, todo mockeado)
pytest tests/ -v

# 2. Solo un fichero, durante el desarrollo de una funcionalidad
pytest tests/test_protocolo_registro.py -v

# 3. Reservado para tests con XMPP real (no incluidos todavía):
pytest tests/ -m integration -v
pytest tests/ -m "not integration" -v
```

Lanzar `pytest tests/` siempre es seguro: las pruebas con etiqueta
`integration` se omiten cuando no hay un servidor accesible, pero
ahora mismo no hay ninguna en la rama.

## Tabla resumen y tratamiento de errores

El fichero [`conftest.py`](conftest.py) añade hooks de pytest que
mejoran la lectura de la salida cuando la serie es grande:

- **La sesión no se aborta ante un fallo.** Cada prueba se
  pre-registra como `PEND` (pendiente); si la sesión se
  interrumpe (`Ctrl+C`, error de colección, aborto del intérprete),
  las pruebas que no llegaron a ejecutarse quedan reflejadas en
  lugar de desaparecer.
- **Tabla resumen por bloques.** Al final de la sesión se imprime
  una tabla con una fila por bloque (cada fichero de prueba) y
  columnas que suman las pruebas **correctas**, las que han tenido
  **incidencia** (fallos, errores de accesorio o pruebas no
  ejecutadas) y las **omitidas**. Una fila `TOTAL` agrega toda la
  serie y se cierra con un veredicto de una línea.
- **Indicaciones de corrección.** Si hay incidencias, debajo de la
  tabla se detalla cada prueba problemática con su motivo y una
  lista de pasos concretos para diagnosticarla y resolverla
  (módulo no encontrado, puerto ocupado, autenticación XMPP
  fallida, timeout, etc.).

El formato de la tabla es uniforme en todo el material de la
asignatura, de modo que ejecutar `pytest` ofrece siempre la misma
experiencia de lectura.


## Etiqueta `integration` para separar las pruebas con servidor

El marcador `integration` está registrado en `pytest.ini` para que
se pueda usar sin avisos de "unknown mark". Se reserva a las
pruebas que arranquen agentes SPADE reales contra el servidor
XMPP del perfil activo. Cuando se añadan, deberán:

- Llevar `pytestmark = pytest.mark.integration` aplicado al
  módulo entero.
- Incluir una condición `pytest.mark.skipif` que compruebe si el
  servidor XMPP del perfil activo acepta conexiones TCP en su
  puerto. Si no responde, las pruebas se marcan como **omitidas**
  en lugar de fallar con un error de conexión, para que
  `pytest tests/` siga siendo seguro fuera de la red UJA.


## Recordatorios de estilo

- Toda prueba tiene un nombre y un docstring **descriptivos en
  español**.
- Las pruebas se agrupan en clases (`TestComponente`) que reflejan
  el componente o la propiedad que se verifica.
- `pytest.mark.asyncio` para las pruebas asíncronas (`asyncio_mode
  = auto` ya está en `pytest.ini`, pero la marca explícita es
  recomendable cuando el método es async dentro de una clase).
- `pytest.mark.parametrize` cuando aporte claridad (variantes
  válidas o submodalidades).
- Las pruebas de integración futuras deben tener un timeout
  explícito para no quedar bloqueadas si un agente no responde, y
  llevar la etiqueta `integration`.
- Toda la convención sigue las pautas globales de la asignatura
  (UTF-8, líneas ≤ 100 caracteres, sin `break`, retorno único)
  declaradas en los `CLAUDE.md` del repositorio.