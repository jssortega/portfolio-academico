# Escenarios obligatorios para los tests del grupo

La serie de validación de `tests/profesor/` cubre el **contrato
externo** del sistema en caja negra y se ejecuta el día del examen. Es necesaria
pero no suficiente: por construcción, no puede entrar en los
componentes internos del grupo. Por eso cada grupo debe **escribir
sus propios tests** sobre su código fuente, organizados en dos
categorías:

- **Unitarios** del grupo: funciones de dominio, validadores
  Pydantic propios, lógica de selección, etc. Se ejecutan sin
  red, sin LLM real (con mocks o dobles) y sin agentes
  arrancados. Cada uno verifica una unidad pequeña aislada.
- **Integración** del grupo: varios componentes del propio grupo
  trabajando juntos (Centralita + un especialista, factoría +
  registro local, Contract Net entre dos unidades del mismo rol,
  etc.). Pueden requerir arrancar parte del sistema, pero **no**
  dependen del Coordinador del profesor.

Las **pruebas de despliegue** son las que ejecuta el Coordinador
del profesor el día del examen sobre el sistema arrancado en el
aula. El grupo no las escribe: ya están en `tests/profesor/` y
basta con que las pase contra su propio sistema.

Este documento no fija los tests concretos —cada grupo elige
nombres, estructura y aserciones—, pero **sí enumera los
escenarios mínimos que debe cubrir** para considerar razonable la
cobertura. Un grupo puede cubrir cada escenario con uno o varios
tests; lo que no puede es dejar un escenario sin cubrir.

Los escenarios están organizados por hito (siguiendo el modelo de
`doc/HITOS_EVALUACION.md` de `desarrollo-nivel3`). Cada uno
indica la **propiedad** que debe quedar verificada y la
**evidencia** que el test recoge.

---

## Hito 1 — Infraestructura A2A y primer agente

### 1.1. Tests unitarios obligatorios

| # | Escenario | Propiedad verificada | Evidencia |
|---|-----------|----------------------|-----------|
| U1.1 | Clasificación determinista por la `FunctionTool` | La función de Nivel 2 que clasifica una alerta devuelve el `TipoEmergencia` correcto para textos representativos de cada categoría (incendio, accidente, derrame, inundación, derrumbe, otro). | Llamada directa a la `FunctionTool` con texto fijo; aserción sobre el valor devuelto. |
| U1.2 | Asignación determinista de prioridad | La función de prioridad devuelve `Prioridad.CRITICA / ALTA / MEDIA / BAJA` según las reglas declarativas del grupo (palabras clave, presencia de víctimas, etc.). | Al menos un test por nivel de prioridad declarado. |
| U1.3 | Esquema de la Agent Card | La Agent Card que la Centralita publica cumple el modelo Pydantic `contrato.agent_card.AgentCard`: campos obligatorios, `skills` no vacío y tipos correctos. | Instanciación de `AgentCard.model_validate` sobre el diccionario que la Centralita publica. |
| U1.4 | Entrada degenerada rechazada en validación | La construcción de `AlertaEmergencia` con `texto=""` o `texto="?"` lanza `pydantic.ValidationError`. | Test con `pytest.raises(ValidationError)`. |
| U1.5 | Lectura de configuración sin literales | La función que carga `config/config.yaml` devuelve el perfil activo correcto y respeta los valores del fichero (mockeado). Una URL distinta en el YAML produce una URL distinta en el agente. | Test que sustituye el YAML por uno temporal y comprueba la URL resultante. |

### 1.2. Tests de integración obligatorios

| # | Escenario | Propiedad verificada | Evidencia |
|---|-----------|----------------------|-----------|
| I1.1 | Flujo `tasks/send` → `completed` intra-componente | El `AgentExecutor` + `LlmAgent` + `FunctionTool` de la Centralita procesan una alerta sencilla y devuelven `EstadoTask.COMPLETED` con un informe coherente. | Test que arranca solo la Centralita (sin especialistas), envía una Task con `httpx` y comprueba la respuesta. |
| I1.2 | Persistencia de la Task entre `send` y `get` | Un `tasks/get` posterior con el mismo `taskId` devuelve la misma Task con historial. | Dos llamadas HTTP secuenciales contra la Centralita arrancada. |
| I1.3 | Tolerancia a entrada degenerada | Una Task con texto degenerado se cierra como `failed` con mensaje descriptivo; la Centralita queda operativa para la siguiente Task. | Tres peticiones consecutivas: degenerada → válida → válida. |
| I1.4 | Lote de 10 peticiones secuenciales | La latencia de la décima petición no se degrada de forma anómala respecto a la primera (cota razonable: ≤ 3×). | Bucle de 10 envíos midiendo `time.monotonic()`. |

---

## Hito 2 — Tres agentes con comunicación

### 2.1. Tests unitarios obligatorios

| # | Escenario | Propiedad verificada | Evidencia |
|---|-----------|----------------------|-----------|
| U2.1 | Mapeo tipo → especialista | La lógica de filtrado devuelve el conjunto correcto de roles convocables para cada `TipoEmergencia` (sin invocar agentes; función pura). | Tests parametrizados por tipo. |
| U2.2 | Coherencia con la decisión de visibilidad | La lógica respeta `config/agents.yaml`: a un público se le envía como Task A2A; a un privado se le invoca por el mecanismo interno declarado. | Test que sustituye `agents.yaml` por uno temporal y comprueba el camino elegido. |
| U2.3 | `InformeActuacion` válido | La función que compone el informe parcial de cada especialista cumple `contrato.informe_actuacion.InformeActuacion`. | `InformeActuacion.model_validate` sobre el diccionario producido. |
| U2.4 | Rechazo de DataPart inválido | La capa de entrada del especialista (antes de invocar al LLM) rechaza con `failed` un DataPart sin `texto` o con tipos incorrectos. | Test sobre la función de validación con `ValidationError`. |

### 2.2. Tests de integración obligatorios

| # | Escenario | Propiedad verificada | Evidencia |
|---|-----------|----------------------|-----------|
| I2.1 | Centralita ↔ especialista público (un rol) | Una alerta cuyo tipo se resuelve con un único rol se traduce en una Task A2A real al especialista; la respuesta agregada contiene su contribución. | Centralita y un especialista arrancados; envío externo. |
| I2.2 | Cadena de dos especialistas | Una alerta que requiere dos roles produce dos Tasks A2A consecutivas; el informe final contiene contribuciones de ambos. | Centralita y dos especialistas arrancados. |
| I2.3 | Especialista no relevante no es invocado | Una alerta sin víctimas no produce Task A2A hacia el sanitario; la traza lo refleja por ausencia. | Verificación sobre el `InformeResolucion` o las trazas del grupo. |
| I2.4 | Fallo localizado de un especialista | Cuando un especialista responde `failed`, la Centralita lo refleja en el informe agregado y continúa con el resto sin colgarse. | Provocar el fallo en el especialista (texto controlado o flag interno). |

---

## Hito 3 — Cinco agentes con coordinación completa

### 3.1. Tests unitarios obligatorios

| # | Escenario | Propiedad verificada | Evidencia |
|---|-----------|----------------------|-----------|
| U3.1 | Esquema del `InformeResolucion` agregado | La función agregadora de la Centralita produce un `InformeResolucion` que valida con el modelo Pydantic compartido. | `InformeResolucion.model_validate` sobre el agregado. |
| U3.2 | Coherencia clasificación ↔ envío (función pura) | Para cada `TipoEmergencia`, la lista de roles convocables (públicos + privados) es la esperada según las reglas del grupo. | Tabla de verdad declarativa. |
| U3.3 | Traza con los cinco roles | La función que construye `traza_participacion` para un escenario integral incluye eventos de los cinco roles con la visibilidad correcta. | Test sobre la función generadora, sin red. |

### 3.2. Tests de integración obligatorios

| # | Escenario | Propiedad verificada | Evidencia |
|---|-----------|----------------------|-----------|
| I3.1 | Escenario integral 5 roles intra-grupo | Una alerta compuesta procesada por el sistema completo arrancado intra-grupo produce un `InformeResolucion` con los cuatro especialistas y la Centralita en la traza. | Sistema completo arrancado; envío externo único. |
| I3.2 | Escenario con solo dos roles | Una alerta de robo con herido convoca solo a Sanitario y Policía; los otros dos no aparecen en el informe. | Sistema completo; aserción negativa sobre roles ausentes. |
| I3.3 | Privado indispensable | Una alerta que requiere uno de los privados del grupo produce un evento `visibilidad=privado` en la traza del informe. | Sistema completo; el privado debe haber intervenido. |
| I3.4 | Sesiones concurrentes | Dos alertas enviadas casi simultáneamente producen dos `taskId` distintos y sus historiales no se entremezclan. | Lanzar dos `tasks/send` con `asyncio.gather`. |
| I3.5 | Resolución sin acceso al registro central | Apuntando `REGISTRO_REST_URL` a un endpoint inexistente, los escenarios A intra-grupo siguen completándose. | Arrancar el grupo apuntando a un registro caído; ejecutar una alerta intra-grupo. |

---

## Hito 4 — Contract Net y respuesta al coordinador

### 4.1. Tests unitarios obligatorios

| # | Escenario | Propiedad verificada | Evidencia |
|---|-----------|----------------------|-----------|
| U4.1 | Selección razonada del ganador | Dada una lista de propuestas (estructuras Pydantic con tiempo/coste/cobertura), la función de selección elige la propuesta correcta según el criterio declarado del grupo. | Test parametrizado con propuestas sintéticas. |
| U4.2 | Esquema de los mensajes CNP | Los mensajes CFP, propuesta y asignación se validan con los modelos Pydantic correspondientes (si el grupo los define) o cumplen el esquema acordado en la memoria. | Test sobre los modelos. |
| U4.3 | Transición de estados de Task | La máquina de estados interna respeta `submitted → working → completed/failed/input-required`; las transiciones inválidas se rechazan. | Test sobre la función de transición pura. |
| U4.4 | Detección de datos incompletos | La función que decide si una alerta requiere `input-required` devuelve `True` cuando falta un campo esencial (según los criterios del grupo) y `False` cuando la alerta es completa. | Tabla de verdad sobre alertas sintéticas. |

### 4.2. Tests de integración obligatorios

| # | Escenario | Propiedad verificada | Evidencia |
|---|-----------|----------------------|-----------|
| I4.1 | CFP completo entre unidades del mismo rol | La Centralita emite CFP, recibe ≥ 2 propuestas distintas, asigna la subtarea al ganador y notifica al perdedor. La traza incluye `convocar_cnp`, `recibir_propuesta`, `asignar_subtarea`, `notificar_no_asignacion`. | Sistema arrancado con al menos dos unidades del mismo rol; envío y verificación de la traza. |
| I4.2 | Asignación al ganador y notificación al perdedor | El ganador ejecuta la subtarea (evento `intervenir_*`); el perdedor recibe una notificación explícita. | Aserciones sobre la traza. |
| I4.3 | Reintento ante fallo del ganador | Si el ganador inicial falla, la Centralita reintenta con la segunda mejor propuesta; el informe final refleja el reintento (segundo `asignar_subtarea` a agente distinto o evento `reintentar`). | Forzar el fallo de la primera unidad ganadora. |
| I4.4 | `input-required` y reanudación | Una alerta incompleta produce `input-required` con mensaje accionable; un `tasks/send` con el complemento lleva la Task a `completed`. | Dos envíos secuenciales con el mismo `taskId`. |
| I4.5 | Tasks concurrentes | Dos Tasks emitidas simultáneamente se procesan en paralelo sin interferencias entre sus historiales. | `asyncio.gather` con dos alertas distintas. |

---

## Hito 5 — Interoperabilidad y cascada

### 5.1. Tests unitarios obligatorios

| # | Escenario | Propiedad verificada | Evidencia |
|---|-----------|----------------------|-----------|
| U5.1 | Filtrado de `GET /agentes` por rol | La función que filtra el resultado del registro devuelve solo los agentes del rol pedido; descarta los del propio grupo. | Test sobre la función con una lista sintética. |
| U5.2 | Selección entre varios proveedores externos | Dado un conjunto de candidatos del mismo rol, la función de selección elige uno según el criterio declarado (orden, latencia previa, *round-robin*…) de forma reproducible. | Test parametrizado. |
| U5.3 | Respaldo ante indisponibilidad | La lógica de respaldo (tiempo de espera agotado → siguiente candidato) avanza al siguiente proveedor; si la lista se agota, marca la subtarea como fallida con motivo. | Test sobre la función con dobles del cliente HTTP. |
| U5.4 | Metadata mínima en Agent Card | El validador del grupo rechaza una Agent Card sin `description`, sin `tags` o con `skills` mal formadas. | `pytest.raises(ValueError)` o equivalente. |

### 5.2. Tests de integración obligatorios

| # | Escenario | Propiedad verificada | Evidencia |
|---|-----------|----------------------|-----------|
| I5.1 | Alta y baja en un registro local | Al arrancar, el agente público se inscribe en un registro REST local (Docker); al apagarse, se desinscribe. | Arrancar el agente, consultar `GET /agentes`, apagarlo, volver a consultar. |
| I5.2 | Señal de vida sostenida | Tras un periodo prolongado sin reiniciar, el agente sigue apareciendo en el registro. | Consultas periódicas durante varios minutos. |
| I5.3 | Cooperación con un grupo simulado | Arrancando un doble A2A externo (otro proceso o test fixture) que responde como un especialista de otro grupo, la Centralita lo descubre vía el registro local y delega correctamente. | Sistema del grupo + doble externo; aserción sobre el informe. |
| I5.4 | Sin tráfico al registro en modalidad A | Un escenario intra-grupo no genera consultas a `GET /agentes`. Comprobable instrumentando el registro local (contador de accesos). | Registro local instrumentado durante un escenario A. |
| I5.5 | Invocación inversa entrante | Un cliente externo invoca al especialista público del grupo en nombre de "otro grupo"; el especialista procesa la petición con normalidad y marca `grupo_externo` en la traza. | Cliente de prueba que se hace pasar por otro grupo. |

---

## Hito 6 — Excelencia

### 6.1. Tests unitarios obligatorios

| # | Escenario | Propiedad verificada | Evidencia |
|---|-----------|----------------------|-----------|
| U6.1 | Validación de peticiones malformadas | La función de validación de la entrada rechaza JSON malformado, esquemas desconocidos y tipos incorrectos antes de invocar al LLM. | Tests con cargas útiles sintéticas. |
| U6.2 | Conmutación de perfil LLM | La función que selecciona el cliente LLM devuelve la instancia correcta según `llm.perfil_activo` del YAML. | Test que sustituye el YAML. |
| U6.3 | Respuesta de error con esquema fijo | El cuerpo que el grupo emite ante una Task `failed` cumple el esquema acordado (mensaje no vacío, código si lo hubiera). | Validación del cuerpo serializado. |

### 6.2. Tests de integración obligatorios

| # | Escenario | Propiedad verificada | Evidencia |
|---|-----------|----------------------|-----------|
| I6.1 | Resistencia a peticiones malformadas | Tras varias peticiones inválidas, la siguiente petición válida procesa con normalidad. | Bucle de peticiones malformadas + petición válida. |
| I6.2 | Transmisión continua SSE | Una Task abierta con `tasks/sendSubscribe` emite al menos un evento `working` antes del `completed`. | Lectura del flujo SSE. |
| I6.3 | Reintento ante cuota agotada del LLM | Si el LLM devuelve `429`, la estrategia declarada del grupo se aplica (reintento, conmutación, degradación con informe parcial). | Doble del LLM que devuelve `429`. |

---

## Cómo organizar estos tests en el proyecto

El grupo es libre de elegir la estructura. Una distribución razonable:

```
tests/
├── unidad/             # Tests U1.x ... U6.x
│   ├── test_clasificacion.py
│   ├── test_prioridad.py
│   ├── test_agregador_informe.py
│   └── ...
├── integracion/        # Tests I1.x ... I6.x
│   ├── test_centralita_tasks_send.py
│   ├── test_centralita_envia_a_especialista.py
│   ├── test_contract_net_extremo_a_extremo.py
│   └── ...
└── profesor/           # YA INCLUIDO: serie de validación del Coordinador del profesor (no modificar)
    ├── modelos/
    ├── cliente_pruebas/
    └── integracion/
```

Cada test debe nombrarse en español siguiendo la convención de la
asignatura: `test_descripcion_de_lo_que_verifica`.

---

## Criterio de cobertura razonable

Para considerar la cobertura del grupo **razonable**, todos los
escenarios marcados arriba como obligatorios para los hitos a los
que aspira deben quedar cubiertos. Es decir:

- Aspirar a Hito 3 → cubrir todos los escenarios de H1, H2 y H3.
- Aspirar a Hito 5 → cubrir además los de H4 y H5.
- Aspirar a Hito 6 (nota 10) → cubrir además los de H6.

Cada escenario obligatorio puede materializarse en **uno o varios
tests** del grupo. Lo evaluable es que el escenario quede
verificado, no el número de tests escritos para ello. Saltar un
escenario obligatorio del hito al que se aspira reduce
proporcionalmente la nota del bloque del 20 % de calidad de
código y documentación.
