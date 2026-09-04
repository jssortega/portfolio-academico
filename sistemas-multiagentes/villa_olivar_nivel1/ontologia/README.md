# Ontología compartida — Villa Olivar

> Esta carpeta contiene los **modelos de datos comunes** que los agentes
> del proyecto utilizan para comunicarse entre sí y, sobre todo, con el
> agente supervisor del profesor. Es un contrato de interfaz, no un
> repositorio de utilidades: los modelos de aquí son **fuente de verdad**
> y cualquier cambio incompatible rompe la corrección automática.

## 1. Por qué existe esta carpeta

El proyecto Villa Olivar es un sistema multi-agente en el que conviven
dos planos de comunicación:

- **Mensajería interna del grupo** — entre Centralita y los cuatro
  especialistas (Bomberos, Sanitario, Policía, Servicios Municipales).
  Su esquema lo define [`esquema_emergencias.json`](esquema_emergencias.json).
- **Frontera supervisor↔grupo** — entre el agente supervisor del
  profesor (que inyecta incidentes y consulta estados) y los agentes
  públicos del grupo. Lo define
  [`esquema_supervisor.json`](esquema_supervisor.json), y los modelos
  Pydantic equivalentes están en
  [`modelos_compartidos.py`](modelos_compartidos.py).

Tener la ontología centralizada permite que:

- Las dos puntas de la frontera (supervisor y grupo) validen los mismos
  campos con las mismas reglas, aunque estén implementadas en lenguajes
  o frameworks distintos.
- Los grupos puedan validar sus mensajes localmente antes de enviarlos.
- La corrección automatizada del profesor se haga sobre un contrato
  estable y comprobable.

## 2. Inventario de la carpeta

```
ontologia/
├── __init__.py                       # marca la carpeta como paquete Python
├── modelos_compartidos.py            # 3 enums + 5 modelos Pydantic (FUENTE DE VERDAD)
├── esquema_emergencias.json          # JSON-Schema de la mensajería intra-grupo
├── esquema_supervisor.json           # JSON-Schema del contrato supervisor↔grupo
└── README.md                         # este documento
```

| Fichero | Para qué sirve | Quién lo usa |
|---------|----------------|--------------|
| [`modelos_compartidos.py`](modelos_compartidos.py) | Modelos Pydantic v2: enums + clases. Es la fuente de verdad del contrato. | Agentes Python del grupo, supervisor del profesor, tests. |
| [`esquema_supervisor.json`](esquema_supervisor.json) | JSON-Schema (Draft-07) del contrato supervisor↔grupo. Replica los modelos Pydantic en formato lenguaje-agnóstico. | Validadores externos, herramientas que no son Python. |
| [`esquema_emergencias.json`](esquema_emergencias.json) | JSON-Schema de la mensajería interna del grupo. Plantilla extendible que cada grupo puede ajustar a sus necesidades. | El propio grupo en su comunicación intra-equipo. |

> ⚠️ **Regla de oro.** Si un cambio modifica `modelos_compartidos.py`,
> hay que verificar inmediatamente que `esquema_supervisor.json` sigue
> coherente — los tests de
> [`tests/test_ontologia/test_interop_supervisor.py`](../tests/test_ontologia/test_interop_supervisor.py)
> lo comprueban automáticamente, pero los grupos deben prestar atención
> al modificar enums o renombrar campos.

## 3. Catálogo completo

### 3.1. Enumeraciones

#### `TipoEmergencia`

Tipos de incidencia que el sistema reconoce. El supervisor inyecta
incidentes etiquetados con uno de estos valores; los agentes del grupo
los interpretan y orquestan la respuesta adecuada.

| Valor | Significado |
|-------|-------------|
| `incendio` | Fuego declarado en edificación o vegetación. |
| `derrame_quimico` | Vertido de sustancia peligrosa. |
| `accidente_trafico` | Colisión, atropello, salida de vía. |
| `inundacion` | Acumulación de agua que requiere achique o rescate. |
| `derrumbe` | Colapso parcial o total de estructura. |
| `otro` | Cualquier otra emergencia no contemplada. |

#### `Prioridad`

Niveles que indican la urgencia del incidente. La Centralita los usa
para ordenar la cola de respuesta.

| Valor | Significado |
|-------|-------------|
| `baja` | Sin riesgo inmediato; respuesta diferida aceptable. |
| `media` | Riesgo moderado; respuesta sin demora. |
| `alta` | Riesgo significativo; respuesta inmediata. |
| `critica` | Riesgo vital o material masivo; máxima prioridad. |

#### `EstadoActuacion`

Estados del ciclo de vida de la actuación de un agente especialista
sobre una emergencia. Los emite cada especialista para informar a la
Centralita y al supervisor.

| Valor | Significado |
|-------|-------------|
| `recibido` | El agente ha recibido la alerta y la ha confirmado. |
| `en_camino` | El recurso se ha desplegado y está desplazándose. |
| `en_escena` | El recurso ha llegado al lugar del incidente. |
| `actuando` | El recurso está ejecutando la respuesta operativa. |
| `finalizado` | La intervención del agente ha terminado con éxito. |
| `requiere_apoyo` | El agente necesita refuerzos para completar la respuesta. |

### 3.2. Modelos Pydantic

Todos los modelos son `BaseModel` de Pydantic v2. Los grupos pueden
extenderlos por herencia (añadir campos internos) pero **no deben
renombrar ni eliminar** los existentes.

#### `DatosEmergencia` — `tipo_mensaje: alerta_emergencia`

Lo que el supervisor envía a la Centralita del grupo con performativa
`request` cuando inyecta un incidente.

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `tipo_mensaje` | str | no (default) | Discriminador, siempre `"alerta_emergencia"`. |
| `id_emergencia` | str | sí | Identificador único del incidente. La Centralita debe replicarlo intacto en su informe final. |
| `tipo_emergencia` | `TipoEmergencia` | sí | Categoría del incidente. |
| `ubicacion` | str | sí | Dirección textual. |
| `prioridad` | `Prioridad` | sí | Urgencia. |
| `descripcion` | str | sí | Texto libre que detalla el incidente. |
| `marca_temporal` | datetime | no (default) | Instante en que se generó la alerta (ISO 8601). |

```python
from ontologia.modelos_compartidos import DatosEmergencia, TipoEmergencia, Prioridad

alerta = DatosEmergencia(
    id_emergencia="EM-2026-001",
    tipo_emergencia=TipoEmergencia.INCENDIO,
    ubicacion="C/ Real 12, Villa Olivar",
    prioridad=Prioridad.ALTA,
    descripcion="Humo visible en planta segunda, edificio residencial.",
)
print(alerta.model_dump_json(indent=2))
```

#### `RespuestaAgente` — `tipo_mensaje: informe_actuacion`

Lo que cada especialista envía a la Centralita para informar de su
estado durante la atención del incidente.

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `tipo_mensaje` | str | no | `"informe_actuacion"`. |
| `id_emergencia` | str | sí | Mismo que el de la alerta. |
| `agente_origen` | str | sí | JID o rol del agente (p.ej. `g1.bomberos`). |
| `estado` | `EstadoActuacion` | sí | Estado actual de la actuación. |
| `detalle` | str | sí | Acciones realizadas en lenguaje natural. |
| `recursos_desplegados` | list[str] | no | Recursos concretos puestos en juego. |
| `marca_temporal` | datetime | no (default) | |

#### `InformeResolucion` — `tipo_mensaje: informe_resolucion`

El **mensaje final** que la Centralita devuelve al supervisor con
performativa `inform` cuando la emergencia se ha resuelto. Es la
salida observable que el corrector evalúa para puntuar el episodio.

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `tipo_mensaje` | str | no | `"informe_resolucion"`. |
| `id_emergencia` | str | sí | Idéntico al original; permite correlación. |
| `tipo_emergencia` | `TipoEmergencia` | sí | |
| `prioridad` | `Prioridad` | sí | |
| `estado_final` | str | sí | P.ej. `"resuelto"`, `"parcialmente_resuelto"`. |
| `resumen` | str | sí | Texto breve. |
| `agentes_participantes` | list[str] | no | JIDs/roles de los participantes. *Pydantic acepta lista vacía pero el supervisor PENALIZA si está vacía* (ver §2.3 del contrato). |
| `acciones_realizadas` | list[str] | no | Misma observación que `agentes_participantes`. |
| `marca_temporal` | datetime | no (default) | |

#### `ConsultaEstado` — `tipo_mensaje: consulta_estado`

Mensaje `query-ref` que el supervisor envía a un agente para preguntar
por su estado interno.

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `tipo_mensaje` | str | no | `"consulta_estado"`. |
| `agente_destino` | str | sí | JID o rol del agente consultado. |
| `marca_temporal` | datetime | no (default) | |

#### `EstadoAgente` — `tipo_mensaje: estado_agente`

Respuesta `inform` con la que el agente responde a la consulta.

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `tipo_mensaje` | str | no | `"estado_agente"`. |
| `agente` | str | sí | JID o rol del agente. |
| `estado` | str | sí | Texto libre del grupo (p.ej. `"libre"`, `"ocupado"`). |
| `emergencia_actual` | str \| None | no | `id_emergencia` que está atendiendo, o `None`. |
| `detalle` | str | no | Información adicional libre. |
| `marca_temporal` | datetime | no (default) | |

## 4. Relación entre los tres ficheros

```
                  ┌──────────────────────────────┐
                  │ modelos_compartidos.py       │ ← FUENTE DE VERDAD
                  │ (Pydantic v2, Python)        │
                  └────────────┬─────────────────┘
                               │ replica fielmente
              ┌────────────────┴─────────────────┐
              ▼                                  ▼
  ┌─────────────────────────┐    ┌──────────────────────────────┐
  │ esquema_supervisor.json │    │ esquema_emergencias.json     │
  │ (JSON-Schema Draft-07)  │    │ (JSON-Schema Draft-07)       │
  │ frontera supervisor ↔   │    │ mensajería intra-grupo;      │
  │ grupo                   │    │ plantilla extendible         │
  └─────────────────────────┘    └──────────────────────────────┘
```

Lectura rápida:

- **Fuente de verdad** del contrato externo: `modelos_compartidos.py`.
  Si hay conflicto entre Pydantic y JSON-Schema, gana Pydantic (y hay
  que actualizar el JSON-Schema).
- **`esquema_supervisor.json`** es la versión externa para validar sin
  Python. Tiene que evolucionar a la par.
- **`esquema_emergencias.json`** es independiente: el grupo lo usa
  internamente para sus propios mensajes. Puede extenderse sin afectar
  al contrato con el supervisor.

## 5. Relación con el servicio REST de registro

El servicio REST de registro (rama `infraestructura-registro-rest`)
gestiona **identidad y localización** de agentes públicos:
`(grupo, rol, url_a2a, url_agent_card, token)`. Sus modelos viven en
`registro/modelos.py` de la rama de infraestructura.

Esos modelos **son ortogonales** a la ontología del dominio: el registro
no conoce el contenido semántico de los mensajes (alertas, informes,
estados); sólo sabe quién está vivo y dónde encontrarlo. Por tanto:

- Cambiar la ontología no afecta al registro REST.
- Cambiar el contrato del registro REST no afecta a la ontología.

La única intersección operacional es que los agentes pueden poblar
`agentes_participantes` del `InformeResolucion` con los `id` que
obtienen al consultar al registro (p.ej. con
`ClienteRegistro.descubrir(rol="bomberos")`); pero eso es uso, no
acoplamiento de esquemas.

## 6. Cómo extender la ontología

**Permitido:**

- Añadir nuevos modelos Pydantic en otro fichero del propio grupo
  (no en `modelos_compartidos.py`) para mensajes internos que no cruzan
  la frontera con el supervisor.
- Heredar de los modelos compartidos para añadir campos privados:
  ```python
  from ontologia.modelos_compartidos import DatosEmergencia

  class DatosEmergenciaConPlanLocal(DatosEmergencia):
      plan_actuacion: str = ""
      recursos_estimados: int = 0
  ```
- Extender `esquema_emergencias.json` con campos adicionales para la
  mensajería interna.

**Prohibido sin acuerdo explícito con el profesor:**

- Renombrar o eliminar campos de los modelos compartidos.
- Cambiar valores de los enums.
- Cambiar el tipo de un campo existente (p.ej. de `str` a `int`).
- Modificar `esquema_supervisor.json` sin su correspondencia en
  `modelos_compartidos.py`.

## 7. Tests asociados

Los tests de la carpeta viven en
[`tests/test_ontologia/`](../tests/test_ontologia/) y cubren:

| Fichero de test | Cobertura |
|-----------------|-----------|
| `test_enumeraciones.py` | Catálogos de los tres enums y comportamiento como string. |
| `test_modelos.py` | Construcción válida, defaults, campos requeridos, round-trip JSON, discriminadores únicos. |
| `test_interop_supervisor.py` | Validación de cada modelo Pydantic contra el JSON-Schema correspondiente; coherencia de los enums entre ambos. |

Ejecutarlos:

```bash
pytest tests/test_ontologia -v
```

Estos tests siguen la propuesta de cobertura mínima descrita en
`docs/ontologia/propuesta_tests_unitarios.md` de la rama
`documentacion-nivel3` (§4 y §5). Los grupos pueden extenderlos con
casos específicos de su dominio.

## 8. Mantenimiento

| Quién | Cuándo edita esta carpeta |
|-------|---------------------------|
| Profesor | Antes de un examen o entrega: ajustes del contrato, nuevos enums, nuevos modelos. |
| Grupo | Sólo `esquema_emergencias.json` para sus extensiones internas; **nunca** `modelos_compartidos.py` ni `esquema_supervisor.json`. |
| Supervisor del profesor | Lo consume tal cual; no modifica nada. |

Cuando el profesor publique un cambio:

1. El grupo hace `git pull` de la rama de documentación o de la rama
   `desarrollo-nivel3` actualizada.
2. Lanza `pytest tests/test_ontologia` para confirmar que sus modelos
   siguen pasando los tests.
3. Si hereda algún modelo compartido, comprueba que sus subclases
   siguen siendo compatibles con la nueva versión.

Más detalles del contrato de fondo (performativas FIPA-ACL, plazos,
criterios de penalización) viven en `docs/contrato_supervisor.md` de
la rama `agente-profesor-emergencias` (también accesible en
`desarrollo-nivel2`).
