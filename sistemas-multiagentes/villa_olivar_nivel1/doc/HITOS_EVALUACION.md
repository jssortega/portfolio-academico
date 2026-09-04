# Hitos de Evaluación — Nivel 3

## Criterios de evaluación del proyecto integrador A2A

---

## 1. Componentes de la evaluación del Nivel 3

Este documento describe **cómo se evalúa el proyecto integrador del Nivel 3**:
qué se mide, con qué criterios y en qué orden conviene avanzar para alcanzar
una determinada calificación. La evaluación combina tres componentes
complementarios, cada uno con un peso distinto dentro del Nivel 3:

| Componente | Peso en Nivel 3 | Descripción |
|------------|-----------------|-------------|
| **Puntuación automática (batería de pruebas)** | **70%** | Resultado agregado de tres conjuntos de pruebas (ver desglose) |
| &nbsp;&nbsp;&nbsp;&nbsp;· Pruebas del alumno sobre los escenarios del documento | 25% | Pruebas redactadas por el grupo para verificar los escenarios descritos en este documento |
| &nbsp;&nbsp;&nbsp;&nbsp;· Pruebas del profesor a integrar desde una rama separada | 25% | Pruebas publicadas por el profesor en una rama del repositorio que el grupo debe integrar y hacer pasar |
| &nbsp;&nbsp;&nbsp;&nbsp;· Pruebas no anunciadas ejecutadas el día de la evaluación | 20% | Pruebas reservadas que complementan los últimos hitos; el alumno no las conoce hasta la sesión de evaluación |
| Calidad de código y documentación | 20% | Estructura del código, pruebas, documentación en `doc/` |
| Presentación e innovación | 10% | Presentación de 3-4 minutos por grupo |

El grueso de la nota (70%) procede de la **batería automática** y se reparte
entre tres conjuntos complementarios:

1. **Pruebas del alumno** (25%): cada grupo redacta las pruebas que verifican
   los escenarios descritos en este documento (ver hitos en **§ 3** y resumen
   en **§ 4**). Permiten comprobar que el sistema cumple los requisitos
   funcionales explícitos.
2. **Pruebas integradas desde la rama del profesor** (25%): el profesor
   publica un conjunto de pruebas en una rama del repositorio. El grupo
   debe **fusionar** esa rama en su línea de desarrollo y conseguir que las
   pruebas pasen sobre su implementación. Verifican la compatibilidad con
   el contrato común que comparten todos los grupos.
3. **Pruebas no anunciadas** (20%): el coordinador del profesor ejecuta el
   día de la evaluación una batería adicional, **no conocida por el alumno**,
   que complementa los hitos finales y mide la robustez del sistema ante
   situaciones imprevistas. Sus categorías y umbrales se describen en la
   sección **§ 2**.

El 30% restante se obtiene mediante una revisión cualitativa del código y la
documentación entregados (**§ 6**) y una presentación oral por grupo (**§ 5**).

Para guiar el progreso del proyecto, la sección **§ 3** organiza el trabajo
en seis **hitos acumulativos** asociados a calificaciones de 5 a 10. Cada
hito incorpora los requisitos del anterior y añade nuevas pruebas que deben
superarse; la sección **§ 4** resume esa progresión en una sola tabla.

> **Recomendación:** abordar el proyecto hito a hito y no intentar cubrir
> todos los requisitos en paralelo. El diseño acumulativo está pensado para
> que cada hito deje una versión funcional del sistema sobre la que construir
> el siguiente.

---

## 2. Pruebas no anunciadas ejecutadas por el coordinador

Esta sección desarrolla el tercer bloque de la batería automática descrito
en **§ 1** (20%): las pruebas que el profesor ejecuta el día de la evaluación
y cuyos casos concretos **no se comunican al alumno** con antelación. El
objetivo de este bloque es medir la **robustez** del sistema frente a
escenarios no preparados de antemano y evitar que el grupo ajuste su
implementación a un conjunto fijo de casos conocidos.

Lo que sí se comunica de antemano (y se documenta en este apartado) es:

- **Las categorías de pruebas** y el número de pruebas por categoría.
- **Las métricas** que se calculan en cada categoría y su peso relativo.
- **Los umbrales de calificación** asociados a cada métrica.

Lo que el grupo descubre solo durante la sesión de evaluación es **el
contenido concreto** de cada caso (textos de las consultas, parámetros,
secuencias de eventos).

### 2.1. Recordatorio del modelo de visibilidad

El procedimiento de evaluación se apoya directamente en el modelo de
visibilidad descrito en `doc/AGENTES_A2A.md`. Conviene recordarlo aquí
porque condiciona qué pruebas puede resolver un grupo por sí solo y cuáles
exigen apoyarse en agentes ajenos:

- Cada grupo expone **3 agentes públicos**: la **Centralita 112**
  (obligatoriamente pública en todos los grupos) y **2 especialistas a
  elección del grupo** entre Bomberos, Sanitario, Policía y Servicios
  Municipales.
- Los otros **2 especialistas quedan privados**: **no se exponen en la red
  del aula ni se registran en `sinbad2.ujaen.es`**, de modo que ni el
  coordinador ni las Centralitas de otros grupos pueden invocarlos
  directamente. Cada grupo decide libremente **cómo su propia Centralita
  los localiza e invoca** (por ejemplo, mediante una URL local declarada
  en su configuración interna, una llamada en proceso o cualquier otro
  mecanismo equivalente). Esa decisión es responsabilidad del grupo y
  este documento de evaluación no la prescribe.
- Los agentes públicos se dan de alta en el **registro central** alojado
  en `sinbad2.ujaen.es` con su `IP:puerto` y mantienen una **señal de vida**
  (*heartbeat*)
  mientras están operativos.

La consecuencia directa para la evaluación es que **un grupo no dispone,
por sí solo, de los cuatro roles especialistas como agentes A2A
descubribles**: dos de ellos son privados y solo accesibles a través de
su propia Centralita. Cuando un escenario requiere un rol que el grupo
mantiene privado y que debe ser invocado *desde fuera* del grupo, la
única vía es localizar a un grupo distinto que lo haya declarado público
y delegar en él.

### 2.2. Procedimiento de ejecución

El **coordinador del profesor** es un programa A2A independiente, distinto de
los agentes del grupo, que actúa como cliente externo del sistema. Durante la
sesión de evaluación sigue esta secuencia:

1. **Arranque del sistema del grupo.** El grupo lanza su sistema multiagente
   (`python main.py` o equivalente) **desde uno de los ordenadores del aula**
   (no desde un equipo personal: véase § 2.4) y sobre el **perfil de
   evaluación** acordado para garantizar las mismas condiciones LLM en todos
   los grupos: por defecto **Gemini (Google AI)** —elegido para que todos
   los grupos consuman exactamente el mismo modelo— y, solo si Gemini no
   está disponible durante la sesión, el respaldo es el perfil con
   **Ollama en `sinbad2ia.ujaen.es`**. Los perfiles de Ollama local quedan
   reservados para desarrollo y depuración, no se usan en la prueba.
   Sus tres agentes públicos (Centralita más los dos especialistas
   elegidos) se registran automáticamente en `sinbad2.ujaen.es` con su
   `IP:puerto` y publican su Agent Card en `/.well-known/agent.json`. Los
   dos privados **no se exponen en la red del aula ni se registran en el
   registro central**; cada grupo decide internamente cómo su propia
   Centralita los localiza e invoca.
2. **Descubrimiento por parte del coordinador.** El coordinador localiza la
   Centralita del grupo evaluado consultando el registro central
   (`GET /agentes` en `sinbad2.ujaen.es`) y lee su Agent Card en
   `/.well-known/agent.json`. **El coordinador no inspecciona ni evalúa
   directamente a los agentes privados**: el comportamiento de un privado se
   observa solo de forma indirecta, a través de la respuesta agregada que la
   Centralita devuelve al delegarle subtareas.
3. **Envío de Tasks a la Centralita.** El coordinador entrega cada escenario
   a la Centralita del grupo mediante mensajes A2A (`tasks/send` y, cuando
   proceda, `tasks/sendSubscribe`). Es la Centralita la que decide cómo
   resolverlo: si recurre solo a sus propios agentes (públicos y privados)
   o si necesita delegar parte del trabajo en agentes públicos de otros
   grupos descubiertos en el registro central.
4. **Recolección de resultados.** Para cada Task se registra el tiempo de
   respuesta, el estado final (`completed` / `failed` / `input-required`),
   los agentes consultados (a partir de las trazas devueltas por la
   Centralita) y los campos presentes en el `InformeResolucion`.
5. **Cálculo de la puntuación.** Las métricas se agregan según los pesos de
   cada categoría y los umbrales descritos en los apartados §2.5 a §2.9.
6. **Devolución al grupo.** Tras la sesión, el profesor entrega al grupo el
   log completo de la ejecución y el desglose por métricas, de modo que el
   grupo pueda contrastar la nota obtenida con la evidencia recogida.

### 2.3. Modalidades de prueba según el alcance

Las pruebas no anunciadas se diseñan en **dos modalidades**, deliberadamente
mezcladas durante la sesión, que persiguen objetivos pedagógicos distintos:

| Modalidad | Resolución esperada | Qué demuestra |
|-----------|---------------------|----------------|
| **A — Resolución intra-grupo** | La Centralita resuelve la emergencia recurriendo únicamente a sus propios agentes (públicos y privados). | Que la orquestación interna funciona, que la Centralita sabe encaminar subtareas a los especialistas privados por el mecanismo que el grupo haya elegido y que los dos públicos elegidos cooperan correctamente. |
| **B — Resolución con cooperación cruzada** | El escenario exige un rol especialista que el grupo evaluado mantiene **privado**. La Centralita debe consultar el registro central, descubrir qué otro grupo expone ese rol como público y delegarle la subtarea. | Que la Centralita no presupone que dispone localmente de todos los roles; que sabe usar el registro central; y que es capaz de cooperar con sistemas externos al grupo. |

Implicaciones para la evaluación:

- El coordinador conoce, a partir del `config.yaml` declarado por el grupo,
  cuáles son sus dos privados y cuáles son sus dos públicos. Para forzar la
  modalidad **B**, **selecciona escenarios que requieran precisamente un rol
  privado del grupo evaluado**, de modo que la única respuesta correcta pase
  por la cooperación cruzada.
- La proporción entre modalidades **A** y **B** es desconocida para el grupo
  y puede variar entre sesiones. La modalidad **B** se concentra
  principalmente en las categorías de **completitud** (§2.6) y **precisión**
  (§2.7), y forma parte del núcleo de los **Hitos 5 y 6** (interoperabilidad
  y excelencia).
- Un grupo que no implemente el descubrimiento vía registro central
  resolverá correctamente las pruebas de modalidad **A**, pero fallará
  sistemáticamente las de modalidad **B**. Esa pérdida de puntuación es
  coherente con el sistema de hitos: superar el Hito 5 exige, por
  definición, que la cooperación cruzada esté operativa.

### 2.4. Qué debe garantizar el grupo el día de la evaluación

Para que las pruebas no anunciadas se puedan ejecutar con garantías, el
grupo debe asegurar lo siguiente **antes** de que comience la sesión:

- **Sesión ejecutada en los ordenadores del aula.** La evaluación se
  realiza obligatoriamente sobre los equipos del **laboratorio docente**,
  no sobre ordenadores personales del alumno. La razón es de
  **direccionamiento de red local**: la red interna de cada laboratorio
  está configurada para enrutar únicamente las **IP privadas asignadas a
  sus propios ordenadores**. Solo desde un PC del aula los demás equipos
  del laboratorio (y, por tanto, el coordinador del profesor y las
  Centralitas de otros grupos) pueden alcanzar a los agentes públicos
  del grupo. Un equipo personal —aunque esté conectado a la red del
  aula— no recibe una IP integrada en ese esquema y queda fuera del
  alcance de sus pares durante la prueba.

  El servidor `sinbad2.ujaen.es` **no impone esta restricción**: su
  único papel es el **alta/baja y señal de vida** de los agentes públicos en
  el registro central. La obligación que sí debe respetar el grupo es
  asegurarse de que las **IP que registra coinciden con las del PC del
  aula** sobre el que se ejecutan sus agentes en el momento de la
  prueba, de modo que sean efectivamente accesibles desde el resto del
  laboratorio.
- **Perfil LLM de evaluación activo.** Por defecto, perfil **Gemini
  (Google AI)** con la variable de entorno `GOOGLE_API_KEY` exportada en
  cada terminal donde se arranque un agente; modelo declarado en
  `config.yaml` (recomendado **`gemini/gemini-2.5-flash-lite`** por su
  cuota diaria más holgada —1000 RPD frente a las 250 del modelo
  `flash`—, suficiente para resolver con calidad los escenarios de la
  prueba sin riesgo de agotar el límite durante la sesión). Si Gemini no
  estuviera disponible durante la sesión, el grupo debe poder conmutar al
  perfil de respaldo con Ollama en `sinbad2ia.ujaen.es` cambiando una
  única línea de `config.yaml` y reiniciando los agentes.
- **Centralita y los dos especialistas elegidos como públicos** accesibles
  vía HTTP en la IP del PC del aula, con sus tres Agent Cards verificables
  manualmente desde el navegador o con `curl`.
- **Los dos especialistas privados** operativos y alcanzables por la
  Centralita del propio grupo, **por el mecanismo de comunicación que el
  grupo haya elegido**. La evaluación no exige una forma concreta de
  exposición (URL local, llamada en proceso, cola interna u otra), solo
  que no estén registrados en `sinbad2.ujaen.es` ni accesibles desde
  fuera del grupo.
- **Alta en el registro central** (`sinbad2.ujaen.es`) de los tres agentes
  públicos, con la señal de vida activa. La consulta `GET /agentes` debe
  devolverlos.
- `config.yaml` entregado declara explícitamente qué dos especialistas son
  públicos y qué dos son privados, y la memoria del grupo justifica la
  elección.
- Pruebas de los hitos previos (§ 3) en verde sobre esa misma configuración
  (perfil Gemini y ordenadores del aula), incluyendo escenarios de
  cooperación cruzada para los grupos que aspiren a los Hitos 5 y 6.
- Logs de los agentes (públicos y privados) accesibles para inspección
  posterior si es necesario.

> **Recomendación operativa.** Antes de la sesión de evaluación, ensayar al
> menos una ejecución completa **en el aula** y con el **perfil Gemini
> activo**. Las verificaciones desarrolladas en el ordenador personal del
> alumno o sobre Ollama local no garantizan que el sistema funcione en las
> condiciones reales de la prueba.

> Las pruebas no anunciadas **complementan los últimos hitos** (Hitos 5 y 6
> de § 3). Un grupo que solo haya alcanzado los primeros hitos no se ve
> perjudicado por este bloque más allá de lo que ya refleja su nivel de
> avance: las categorías y modalidades que dependen de funcionalidad no
> implementada se contabilizarán como no superadas, en coherencia con el
> resto del sistema de evaluación.

### 2.5. Consultas de latencia (20 pruebas)

Peticiones simples que miden el tiempo de respuesta:

| Métrica | Descripción | Peso |
|---------|-------------|------|
| Tiempo medio de respuesta | Media de las 20 consultas | Alto |
| Percentil 95 | Tiempo por debajo del cual están el 95% de las respuestas | Medio |
| Tasa de éxito | Porcentaje de consultas que reciben respuesta válida | Alto |

**Umbrales de referencia:**

| Calificación | Tiempo medio | P95 | Tasa de éxito |
|-------------|-------------|-----|---------------|
| Excelente | < 15 s | < 30 s | > 95% |
| Bueno | < 30 s | < 60 s | > 85% |
| Aceptable | < 60 s | < 120 s | > 70% |
| Insuficiente | > 60 s | > 120 s | < 70% |

> **Nota sobre los umbrales.** La evaluación tiene **carácter docente**:
> el objetivo es comprobar que el alumno ha adquirido las competencias
> básicas de desarrollo de un sistema multiagente sobre A2A, no exigirle
> rendimiento de producción. Estos umbrales se han fijado de forma
> deliberadamente **conservadora**, suponiendo que la implementación
> incorpora el coste de un LLM remoto (Gemini), varias indirecciones
> A2A y, en la modalidad B, una llamada adicional a un agente público
> de otro grupo. La optimización fina del rendimiento queda fuera del
> alcance de la asignatura y se desarrolla con la experiencia
> profesional posterior; aun así, una implementación claramente
> ineficiente se reflejará en los percentiles y en la tasa de éxito.

### 2.6. Consultas de completitud (15 pruebas)

Escenarios que requieren coordinación con especialistas:

| Métrica | Descripción | Peso |
|---------|-------------|------|
| Campos presentes | Porcentaje de campos obligatorios de `InformeResolucion` presentes | Alto |
| Agentes participantes | Verificación de que se contactaron los especialistas relevantes | Alto |
| Coherencia | Las respuestas de los especialistas son coherentes con el tipo de emergencia | Medio |

### 2.7. Consultas de precisión (10 pruebas)

Escenarios específicos donde se evalúa la calidad de la respuesta:

| Métrica | Descripción | Peso |
|---------|-------------|------|
| Clasificación correcta | El tipo de emergencia se clasifica correctamente | Alto |
| Prioridad adecuada | La prioridad asignada es razonable | Medio |
| Especialistas correctos | Los especialistas contactados son los relevantes para el tipo de emergencia | Alto |

### 2.8. Peticiones malformadas (5 pruebas)

Verifican el manejo de errores:

| Métrica | Descripción | Peso |
|---------|-------------|------|
| Estabilidad del agente | El agente permanece operativo y atiende peticiones posteriores tras recibir una petición malformada | Alto |
| Task failed | El agente devuelve un Task con estado `failed` y mensaje descriptivo | Medio |
| Registro de error | El agente registra el error en sus logs | Bajo |

### 2.9. Negociación competitiva (3 pruebas)

Contract Net entre agentes:

| Métrica | Descripción | Peso |
|---------|-------------|------|
| Propuesta válida | El agente responde con una propuesta estructurada | Alto |
| Comparación de propuestas | La Centralita selecciona la mejor propuesta | Alto |
| Ejecución del ganador | El agente seleccionado ejecuta la acción e informa | Medio |

---

## 3. Hitos detallados

> Todos los hitos presuponen el modelo de visibilidad descrito en
> `doc/AGENTES_A2A.md` (resumido en § 2.1): cada grupo expone **la
> Centralita y dos especialistas elegidos** como agentes públicos, y
> mantiene los **otros dos especialistas como privados**. Cada hito
> indica de forma explícita qué parte de ese modelo debe estar
> operativa para alcanzarlo.

Para cada hito, los escenarios listados deben verificarse con **tres tipos
de pruebas complementarias**:

- **Pruebas unitarias.** Aíslan una unidad de código (función, clase o
  módulo) y comprueban su comportamiento sin depender de la red, del LLM
  ni de otros agentes. Cuando una dependencia es inevitable, se sustituye
  por un doble de prueba (*mock*). Son rápidas, deterministas y permiten
  ejecutar la batería completa en segundos.
- **Pruebas de integración.** Verifican la interacción entre componentes
  del mismo grupo: la Centralita con sus especialistas, el despacho A2A
  con el `LlmAgent` y las `FunctionTool`, la serialización A2A con modelos
  Pydantic, etc. Pueden arrancar varios procesos locales y consumir un
  LLM real, pero **no exigen las condiciones de red del aula**.
- **Pruebas de despliegue.** Validan el sistema en las condiciones reales
  de la sesión de evaluación: ordenadores del laboratorio, IP privada del
  aula, registro central de `sinbad2.ujaen.es` operativo, perfil Gemini
  activo y, en la modalidad B, otros grupos accesibles. Son las que
  garantizan el **contrato externo** del grupo y solo pueden ejecutarse
  en el aula.

Cada hito añade un apartado **Clasificación de pruebas** que asigna sus
escenarios a estos tres tipos. Un mismo escenario puede dar lugar a más
de un test pytest si el grupo decide cubrirlo desde varias perspectivas.

### Hito 1 — Infraestructura A2A y primer agente (nota: 5)

**Objetivo:** demostrar que se comprende la infraestructura básica A2A
sobre el agente público obligatorio del grupo, la **Centralita 112**.

**Escenarios a verificar:**

1. **Publicación de la Agent Card.** Al arrancar la Centralita, una
   petición `GET /.well-known/agent.json` devuelve un JSON válido con
   los campos `name`, `url`, `version`, `capabilities` y `skills`
   declarados. El test valida la presencia de los campos obligatorios y
   la coherencia con `config.yaml` (URL declarada == URL servida).
2. **Procesado de una alerta sencilla.** Se envía un `tasks/send` con un
   texto del tipo *"Incendio detectado en la calle Olivos 12"*. La
   Centralita devuelve la Task en estado `completed` con un mensaje
   cuyo contenido identifica al menos el tipo de emergencia
   (`incendio`) y una prioridad razonable.
3. **Variedad de tipos de emergencia.** Repetir el escenario 2 con al
   menos cuatro tipos distintos del catálogo (incendio, accidente de
   tráfico, derrame químico, inundación, derrumbe). Cada uno debe
   clasificarse correctamente, permitiendo verificar que la
   clasificación no está sesgada hacia un único tipo.
4. **Persistencia y consulta posterior.** Conservar el `taskId`
   devuelto y consultar `tasks/get`; debe devolver la misma Task con
   su historial de estados (`submitted → working → completed`).
5. **Integración de la lógica del Nivel 2.** La Centralita usa las
   `FunctionTool` ya implementadas en Nivel 2 (clasificación,
   prioridad). Un test inyecta un texto que requiere invocar la
   herramienta y verifica que el resultado coincide con el cálculo
   determinista de Nivel 2 (la herramienta es la fuente de verdad, no
   el LLM).
6. **Entradas degeneradas tratadas con control.** Una petición con
   texto vacío, ilegible o claramente fuera de dominio devuelve la
   Task en estado `failed` con un mensaje descriptivo, sin caída del
   servidor. Tras una petición degenerada, la siguiente petición válida
   se procesa con normalidad.
7. **Configuración sin literales en el código.** Cambiar el puerto del servidor o
   el modelo LLM en `config.yaml` y reiniciar es suficiente para que la
   Centralita opere con los nuevos valores. Un test puede aplicar el
   cambio sobre una copia, arrancar la Centralita y verificar las
   nuevas URL/modelo en la Agent Card.
8. **Disponibilidad continuada.** Tras un lote de 10 peticiones
   secuenciales, la Centralita sigue respondiendo con normalidad y sin
   degradación de latencia atribuible a fugas de recursos.

**Clasificación de pruebas:**

- **Unitarias** — validación del esquema de la Agent Card, integración
  de las `FunctionTool` de Nivel 2 con doble de prueba del LLM,
  verificación del cálculo determinista de prioridad y clasificación
  (escenarios 1, 3 parcial, 5).
- **Integración** — flujo completo `tasks/send` → despacho →
  `manejar_alerta` → `LlmAgent` → `FunctionTool` → respuesta `completed`; persistencia y
  consulta vía `tasks/get`; tratamiento de entradas degeneradas
  (escenarios 2, 3, 4, 6).
- **Despliegue** — servidor `aiohttp` levantado en la IP del PC del
  aula; `GET /.well-known/agent.json` accesible desde otro PC del
  laboratorio; lote prolongado de peticiones sin degradación; cambio
  de configuración y reinicio (escenarios 1 *en condiciones reales*, 7,
  8).

**Lista de comprobación:**

- [ ] Rama `desarrollo-nivel3` existe con `config.yaml` extendido.
- [ ] Dependencias del Nivel 3 instaladas y verificables (`aiohttp`, `google-adk`).
- [ ] La **Centralita** desplegada como servidor HTTP con `aiohttp` en la
  IP del PC del aula (no solo `localhost`).
- [ ] Agent Card de la Centralita publicada en `/.well-known/agent.json`.
- [ ] El `LlmAgent` de ADK conectado al despacho A2A de la base, parametrizado por el
  perfil LLM activo en `config.yaml` (Gemini para la prueba evaluativa;
  Ollama local o en `sinbad2ia.ujaen.es` para desarrollo).
- [ ] `FunctionTool` del Nivel 2 integradas.
- [ ] La Centralita responde a `tasks/send` con Task `completed`.
- [ ] 5 pruebas nuevas pasan.

**Pruebas requeridas:**

```
tests/test_agent_cards.py::test_agent_card_centralita_valida        PASS
tests/test_agente_a2a.py::test_servidor_a2a_responde                PASS
tests/test_agente_a2a.py::test_task_send_devuelve_completed         PASS
tests/test_herramientas_adk.py::test_functiontools_integradas       PASS
tests/test_logica_centralita.py::test_logica_sin_dependencias       PASS
```

---

### Hito 2 — Tres agentes con comunicación (nota: 6)

**Objetivo:** demostrar comunicación A2A entre los **tres agentes públicos
del grupo** (Centralita más los dos especialistas elegidos como públicos).
A partir de este hito, la decisión de visibilidad ya debe estar reflejada
en `config.yaml`.

**Escenarios a verificar:**

A lo largo de los escenarios, *especialista público A* y *especialista
público B* designan los dos especialistas que el grupo haya declarado
públicos en `config.yaml`. Los tests del grupo deben parametrizarse para
funcionar con cualquiera de las seis combinaciones posibles.

1. **Tres Agent Cards públicas válidas.** Tras arrancar el sistema, las
   tres URL declaradas como públicas en `config.yaml` sirven una Agent
   Card bien formada en `/.well-known/agent.json`. Las tres habilidades
   declaradas en el campo `skills` son coherentes con el rol del agente.
2. **Descubrimiento desde la Centralita.** La Centralita carga las URL
   de sus dos especialistas públicos desde `config.yaml`, descarga sus
   Agent Cards y guarda en memoria una tabla rol → URL para enrutar
   subtareas posteriores. Un test inspecciona ese estado interno o sus
   trazas tras el arranque.
3. **Envío a un único especialista.** Una alerta cuyo tipo se
   resuelve íntegramente con el especialista público A (por ejemplo,
   un incendio cuando A es Bomberos) genera una Task A2A a A; la
   Centralita agrega su respuesta al `InformeResolucion` final sin
   contactar a B.
4. **Envío a dos especialistas en cadena con dependencia.** Una
   alerta que requiere ambos públicos en orden (por ejemplo, *"incendio
   con un trabajador inconsciente"* cuando A=Bomberos y B=Sanitario)
   genera dos Tasks A2A consecutivas: primero a quien actúa antes
   según la dependencia funcional declarada en `AGENTES_A2A.md`,
   después al otro. La respuesta agregada incluye contribuciones de los
   dos.
5. **Envío paralelo cuando no hay dependencia.** Una alerta que
   requiere ambos públicos sin orden estricto produce dos Tasks A2A
   concurrentes; la Centralita agrega ambas respuestas cuando ambas
   completan. El tiempo total es menor que la suma de las latencias
   individuales.
6. **DataPart con modelos Pydantic.** Los `DataPart` que viajan entre
   Centralita y especialista son deserializables a los modelos Pydantic
   acordados (`AlertaEmergencia` en el envío y `InformeActuacion` en la
   respuesta). Un test inyecta una carga útil (*payload*) mal formada y verifica que se
   rechaza con `failed` claro.
7. **Especialista no relevante no es invocado.** Una alerta cuyo tipo
   no corresponde al rol de B no genera Task A2A hacia B (verificable
   por las trazas de la Centralita o por la ausencia de Tasks en el
   especialista). Comprueba que el filtrado de envío funciona.
8. **Fallo controlado de un especialista.** Si el especialista A
   devuelve `failed`, la Centralita lo refleja en el informe final y
   continúa con B si procede; el sistema mantiene su operatividad y atiende peticiones posteriores con normalidad.
9. **Cambio de URL sin recompilar.** Modificar la URL de un especialista
   en `config.yaml` y reiniciar la Centralita basta para que el nuevo
   envío llegue a la nueva ubicación, sin tocar código fuente.

**Clasificación de pruebas:**

- **Unitarias** — lógica de filtrado por tipo de emergencia (qué
  especialista enviar), validación de los modelos Pydantic
  (`AlertaEmergencia`, `InformeActuacion`), rechazo de `DataPart` mal
  formados (escenarios 6, 7).
- **Integración** — descubrimiento de Agent Cards desde `config.yaml`,
  envío a un especialista, envío en cadena con dependencia,
  envío en paralelo, fallo localizado de un especialista
  (escenarios 2, 3, 4, 5, 8).
- **Despliegue** — tres servidores HTTP operativos en la IP del aula,
  tres Agent Cards públicas accesibles, cambio de URL en `config.yaml`
  y reinicio en condiciones reales (escenarios 1, 9).

**Lista de comprobación (acumulativa):**

- [ ] `config.yaml` declara explícitamente qué dos especialistas serán
  públicos y cuáles privados (la elección puede revisarse en hitos
  posteriores).
- [ ] Los **tres agentes públicos** (Centralita más los dos especialistas
  elegidos) desplegados como servidores HTTP en la IP del PC del aula.
- [ ] Tres Agent Cards públicas válidas con sus habilidades (campo `skills`)
  declaradas y accesibles en `/.well-known/agent.json`.
- [ ] La Centralita descubre las Agent Cards de los especialistas a partir
  de las URL declaradas en `config.yaml`.
- [ ] La Centralita envía Tasks A2A a especialistas y recibe respuestas.
- [ ] Los datos se serializan como `DataPart` con modelos Pydantic.
- [ ] 4 pruebas adicionales pasan.

**Pruebas adicionales requeridas:**

```
tests/test_agent_cards.py::test_tres_agent_cards_validas            PASS
tests/test_agente_a2a.py::test_descubrimiento_agent_cards           PASS
tests/test_integracion_a2a.py::test_centralita_envia_task_a_esp.    PASS
tests/test_integracion_a2a.py::test_datapart_con_pydantic           PASS
```

---

### Hito 3 — Cinco agentes con coordinación completa (nota: 7)

**Objetivo:** sistema de emergencias **intra-grupo** completo sobre A2A,
con el reparto 3 públicos / 2 privados ya operativo. Equivale a la
**modalidad A** descrita en § 2.3.

**Escenarios a verificar:**

1. **Sistema completo arrancado.** Tras un arranque limpio, las tres
   Agent Cards públicas son accesibles en la IP del aula y los dos
   privados están operativos según el mecanismo elegido por el grupo.
   Un test del grupo inspecciona ambos estados.
2. **Privados aislados de la red exterior.** Un cliente A2A externo
   intenta invocar a uno de los dos privados con su rol declarado y
   **debe fallar** (no encontrado, conexión rechazada, tiempo de espera
   agotado o equivalente). Los privados solo responden cuando los invoca la
   Centralita propia por el mecanismo elegido.
3. **Escenario integral de los cinco roles.** Una alerta del tipo
   *"Accidente en intersección de la Avenida Principal con dos
   vehículos involucrados, varios heridos, fuga de combustible y vía
   bloqueada"* obliga a la Centralita a enviar a Bomberos (fuga),
   Sanitario (heridos), Policía (perímetro y desvío) y Servicios
   Municipales (señalización y limpieza). Cada uno aporta su informe
   parcial al `InformeResolucion` final, independientemente de su
   visibilidad.
4. **Escenario con sólo dos roles.** Una alerta del tipo *"Robo en
   establecimiento con persona herida"* envía solo a Sanitario y
   Policía y no a Bomberos ni Servicios Municipales. El informe
   refleja que los otros dos no han intervenido.
5. **Escenario donde un privado es indispensable.** Para cualquiera de
   las seis combinaciones posibles de visibilidad, debe existir al
   menos un escenario que obligue a la Centralita a recurrir a un
   especialista privado (ya que dos de los cuatro roles siempre lo
   son). Un test selecciona ese escenario en función de la
   configuración del grupo.
6. **InformeResolucion conforme al esquema.** El informe final agrega
   los campos esperados (`tipo`, `prioridad`, `ubicacion`,
   `especialistas_intervinientes`, `acciones_realizadas`,
   `estado_final`) y se valida frente al modelo Pydantic acordado.
7. **Coherencia entre clasificación y envío.** Los especialistas
   contactados se corresponden con la clasificación efectuada al
   principio: si la Centralita clasifica como `incendio` sin víctimas,
   no debería invocar a Sanitario.
8. **Resolución intra-grupo sin acceso al registro central.** Si el
   registro central de `sinbad2.ujaen.es` está caído o se simula su
   inaccesibilidad (apuntando a un servidor inexistente), los escenarios
   de modalidad A siguen completándose, ya que no requieren agentes
   externos al grupo.
9. **Sesiones concurrentes.** Dos alertas distintas enviadas casi
   simultáneamente a la Centralita producen dos `taskId` distintos y
   sus historiales no se entremezclan. Cada `tasks/get` devuelve el
   estado correcto de su Task.
10. **Latencia interna razonable.** Un escenario de modalidad A
    completo termina dentro de los umbrales conservadores indicados en
    § 2.5; tests del grupo registran tiempo medio y P95 sobre un lote
    de al menos 5 ejecuciones.

**Clasificación de pruebas:**

- **Unitarias** — lógica de orquestación (qué especialistas se
  envían para cada tipo de emergencia), agregación del
  `InformeResolucion`, coherencia clasificación↔envío (escenarios
  6, 7).
- **Integración** — escenario integral de los cinco roles, escenario
  con dos roles, escenario que fuerza un privado, sesiones
  concurrentes, resolución sin acceso al registro central (escenarios
  3, 4, 5, 8, 9).
- **Despliegue** — tres públicos en la IP del aula y dos privados
  aislados desde fuera del grupo, latencia interna conforme a § 2.5
  sobre 5 ejecuciones reales en el aula (escenarios 1, 2, 10).

**Lista de comprobación (acumulativa):**

- [ ] Los **tres agentes públicos** desplegados en la IP del PC del aula
  con sus Agent Cards en `/.well-known/agent.json`.
- [ ] Los **dos agentes privados** operativos y alcanzables únicamente por
  la Centralita del propio grupo. **No** se exponen en la IP del aula ni
  se registran en `sinbad2.ujaen.es`. El mecanismo concreto por el que
  la Centralita los localiza e invoca es decisión del grupo y se
  documenta en la memoria.
- [ ] La Centralita orquesta correctamente a los dos privados (por el
  mecanismo elegido por el grupo) y a los dos públicos a través de la
  IP del aula.
- [ ] Las cinco Agent Cards son válidas y declaran habilidades coherentes
  con el rol del agente (aunque solo las tres públicas sean alcanzables
  desde fuera del grupo).
- [ ] Todos los especialistas procesan peticiones con LLM + FunctionTool.
- [ ] Se ejecuta un escenario completo intra-grupo de principio a fin
  sobre A2A, sin depender de agentes de otros grupos.
- [ ] 3 pruebas adicionales pasan.

**Pruebas adicionales requeridas:**

```
tests/test_agent_cards.py::test_cinco_agent_cards                   PASS
tests/test_integracion_a2a.py::test_escenario_completo_a2a          PASS
tests/test_integracion_a2a.py::test_centralita_coordina_esp.        PASS
```

---

### Hito 4 — Contract Net y respuesta al coordinador (nota: 8)

**Objetivo:** negociación entre agentes del grupo y compatibilidad con el
coordinador del profesor, que entra siempre por la **Centralita pública**
del grupo.

**Escenarios a verificar:**

1. **Convocatoria de propuestas (CFP) entre unidades de un mismo
   especialista.** Para una subtarea con varias unidades posibles
   —por ejemplo, dos camiones de bomberos disponibles para un
   incendio— la Centralita emite una Call for Proposals al especialista,
   que devuelve propuestas estructuradas (tiempo estimado, recursos,
   coste). Un test verifica que se reciben al menos dos propuestas
   distintas para el mismo CFP.
2. **Selección razonada del ganador.** La Centralita elige una propuesta
   aplicando un criterio explícito (el de menor tiempo, el de menor
   coste, el de mayor cobertura). El criterio queda registrado en los
   logs o en el `InformeResolucion` para que un test pueda verificarlo
   de forma determinista.
3. **Asignación al ganador y notificación al perdedor.** El especialista
   ganador recibe la subtarea concreta y la ejecuta; el perdedor recibe
   una notificación de no asignación. Tests separados comprueban ambos
   caminos.
4. **CFP entre roles distintos para la misma subtarea.** Un escenario
   compuesto donde dos especialistas distintos podrían cubrir la misma
   subtarea —p. ej. atender a una víctima leve podría hacerlo Sanitario
   o Servicios Municipales si hay un médico de apoyo— produce
   propuestas comparables y la Centralita elige la más adecuada.
5. **Respuesta al coordinador del profesor con esquema exacto.** Una
   Task con la firma exacta esperada por el coordinador (campos del
   `DataPart`, formato del `InformeResolucion`) se procesa y devuelve
   `completed` con un informe que pasa la validación del esquema.
6. **Ciclo de vida observable.** Para una Task larga, sucesivas
   llamadas a `tasks/get` devuelven los estados intermedios
   `submitted → working → completed` (o `failed`). El historial expone
   los estados anteriores y los timestamps de cada transición.
7. **Estado `input-required` ante datos incompletos.** Una alerta sin
   ubicación, o sin descripción suficiente, hace que la Centralita
   devuelva la Task en estado `input-required` con un mensaje que
   solicita el dato faltante. Un nuevo `tasks/send` con el complemento
   continúa la Task hacia `completed`.
8. **Fallo localizado en un especialista.** Si un especialista
   convocado devuelve `failed`, la Centralita lo refleja en el informe
   y prosigue el resto del envío. La Task global termina en
   `completed` con un informe parcial o en `failed` con motivo, pero
   nunca queda de forma indefinida en un estado intermedio sin
   resolución.
9. **Reintento ante fallo del ganador.** Si el especialista ganador
   del CFP falla durante la ejecución, la Centralita reintenta con la
   segunda mejor propuesta (si la hubo) antes de declarar la subtarea
   como fallida.
10. **Tasks concurrentes del coordinador.** Dos Tasks emitidas
    simultáneamente por el coordinador se procesan en paralelo sin
    interferencias en sus respectivos `taskId`, historiales ni
    informes finales.
11. **Trazabilidad de la cadena CFP.** El informe final permite
    reconstruir, a partir del historial y los registros, qué propuestas
    recibió la Centralita, qué criterio aplicó y qué especialista
    ejecutó la subtarea.

**Clasificación de pruebas:**

- **Unitarias** — lógica de selección de propuestas según criterio
  declarado, transición de estados de Task (`submitted → working →
  completed/failed/input-required`), validación del esquema esperado
  por el coordinador del profesor (escenarios 2, 6, 7 parcial).
- **Integración** — convocatoria de propuestas (CFP) entre la
  Centralita y unidades del mismo rol; CFP entre roles distintos;
  asignación al ganador y notificación al perdedor; reintento ante
  fallo del ganador; manejo de `input-required`; fallo localizado en
  un especialista; trazabilidad de la cadena CFP (escenarios 1, 3, 4,
  7, 8, 9, 11).
- **Despliegue** — respuesta correcta al coordinador del profesor en
  sesión real, Tasks concurrentes emitidas por el coordinador
  (escenarios 5, 10).

**Lista de comprobación (acumulativa):**

- [ ] Patrón Contract Net implementado sobre A2A entre la Centralita y sus
  especialistas (públicos y privados).
- [ ] La Centralita solicita propuestas a sus especialistas, compara y
  asigna la subtarea al ganador.
- [ ] La Centralita responde correctamente al coordinador del profesor
  (`tasks/send` y, cuando proceda, `tasks/sendSubscribe`) con un
  `InformeResolucion` agregado a partir de las respuestas de los
  especialistas.
- [ ] Manejo correcto del ciclo de vida de Tasks (submitted → working →
  completed/failed) tanto en la Centralita como en los especialistas.
- [ ] Estado `input-required` implementado para solicitar más información.
- [ ] 4 pruebas adicionales pasan.

**Pruebas adicionales requeridas:**

```
tests/test_negociacion_a2a.py::test_contract_net_a2a                PASS
tests/test_integracion_a2a.py::test_respuesta_coordinador           PASS
tests/test_agente_a2a.py::test_ciclo_vida_task                      PASS
tests/test_agente_a2a.py::test_input_required                       PASS
```

---

### Hito 5 — Interoperabilidad y cascada (nota: 9)

**Objetivo:** **cooperación cruzada con otros grupos** vía el registro
central y resolución de escenarios que requieren un rol que el grupo
mantiene privado. Equivale a la **modalidad B** descrita en § 2.3.

**Escenarios a verificar:**

1. **Alta en el registro central.** Tras arrancar el sistema, una
   consulta `GET /agentes` a `sinbad2.ujaen.es` devuelve los tres
   públicos del grupo con su `IP:puerto`, rol declarado y URL de la
   Agent Card. El test toma la respuesta del registro y la compara
   con `config.yaml`.
2. **Señal de vida sostenida.** Tras un periodo prolongado sin reiniciar
   (varios minutos), los agentes siguen apareciendo en el registro y
   no han sido caducados por falta de señal de vida.
3. **Baja ordenada al apagar.** Detener el sistema con un apagado
   controlado (Ctrl+C) hace desaparecer del registro a los tres
   agentes en un plazo razonable.
4. **Recuperación tras caída del registro.** Si el registro central
   estuvo caído brevemente al arrancar, los agentes reintentan el
   alta hasta conseguirla y mantienen la señal de vida sin requerir
   intervención manual.
5. **Descubrimiento por rol.** Ante un escenario que necesita un rol
   privado en el grupo evaluado, la Centralita consulta
   `GET /agentes`, filtra por ese rol y obtiene una o varias URL de
   especialistas o Centralitas públicos de otros grupos.
6. **Delegación efectiva entre grupos** (*cross-group*). Para un escenario que requiere
   precisamente un rol que el grupo mantiene privado (por ejemplo,
   *"manifestación con riesgo de altercados, requiere despliegue
   policial extenso"* si Policía es privado en el grupo), la
   Centralita delega la subtarea correspondiente al agente público
   equivalente de otro grupo y agrega su respuesta al
   `InformeResolucion` final. El test supone que existe al menos un
   grupo que expone públicamente ese rol.
7. **Selección entre varios proveedores externos.** Si dos o más
   grupos exponen el mismo rol como público, la Centralita elige uno
   con un criterio explícito (orden de aparición, latencia previa
   medida, turno rotatorio (*round-robin*)…) y registra la decisión.
8. **Cascada multiagente.** Un evento del tipo *"incendio en zona
   industrial con derrame químico y víctimas"* dispara una secuencia
   con al menos tres agentes intervinientes —combinando agentes
   propios (públicos y privados) y públicos de otros grupos cuando
   los roles requeridos son privados en el grupo evaluado—. El
   `InformeResolucion` refleja la secuencia y los grupos
   intervinientes.
9. **Indisponibilidad transitoria de la pareja externa.** Si el agente
   externo elegido no responde dentro del tiempo de espera, la Centralita lo
   registra y reintenta con otro grupo que exponga el mismo rol; si
   ningún otro lo expone, el informe consigna el fallo de forma
   estructurada y la Task global termina en `failed` o `completed`
   parcial, según convención del grupo.
10. **Sin cooperación cuando no hace falta.** Un escenario resoluble
    íntegramente con agentes propios (modalidad A) no debe consultar
    al registro central; comprobable porque no aparece tráfico saliente
    a `sinbad2.ujaen.es` en ese caso.
11. **Metadata mínima en Agent Cards públicas.** Las cards exponen
    `description`, `tags` y `skills` con suficiente detalle para que
    las Centralitas externas puedan filtrarlas sin ambigüedad. Un test
    valida que cada habilidad tiene un identificador único y al menos
    una etiqueta semántica.
12. **Compatibilidad con grupos vecinos.** Una invocación inversa —en
    la que la Centralita del grupo evaluado *recibe* una subtarea de
    otro grupo para un rol que sí es público en ella— se procesa con
    normalidad, sin rechazos por origen externo.

**Clasificación de pruebas:**

- **Unitarias** — lógica de descubrimiento por rol (filtrado del
  resultado de `GET /agentes`), selección entre varios proveedores
  externos según criterio declarado, lógica de respaldo ante
  indisponibilidad (escenarios 5 parcial, 7 parcial, 9 parcial).
- **Integración** — cooperación con un grupo simulado mediante doble
  de prueba A2A externo, cascada multiagente con dobles de prueba,
  invocación inversa entrante (escenarios 8, 12).
- **Despliegue** — alta y baja reales en `sinbad2.ujaen.es`, señal de
  vida sostenida durante una sesión prolongada, recuperación tras
  caída del registro, descubrimiento real de agentes públicos de otros
  grupos, delegación efectiva entre grupos en sesión real,
  comprobación de que los escenarios A no consultan el registro,
  metadata mínima en Agent Cards públicas (escenarios 1, 2, 3, 4, 5,
  6, 7, 9, 10, 11).

**Lista de comprobación (acumulativa):**

- [ ] Los tres agentes públicos del grupo se dan de **alta en el registro
  central** alojado en `sinbad2.ujaen.es` con su `IP:puerto` al arrancar
  y mantienen una **señal de vida** mientras están operativos.
- [ ] Al apagarse, los agentes públicos se dan de **baja** en el registro.
- [ ] La Centralita consulta `GET /agentes` en el registro central para
  descubrir los agentes públicos vigentes de otros grupos.
- [ ] La Centralita selecciona un agente público de otro grupo cuando el
  rol que necesita el escenario es privado en el propio grupo y delega
  en él la subtarea correspondiente vía A2A.
- [ ] Escenario de cascada: eventos propagados entre 3 o más agentes,
  combinando agentes propios (públicos y privados) y públicos de otros
  grupos.
- [ ] Manejo de indisponibilidad de agentes externos (tiempo de espera
  agotado, conmutación de respaldo a otro grupo que exponga el mismo rol).
- [ ] Las tres Agent Cards públicas contienen la metadata suficiente para
  el descubrimiento entre grupos (rol claro en `description` y `tags`,
  habilidades bien identificadas en el campo `skills`).
- [ ] 3 pruebas adicionales pasan.

**Pruebas adicionales requeridas:**

```
tests/test_interoperabilidad.py::test_consulta_agente_externo       PASS
tests/test_interoperabilidad.py::test_timeout_agente_no_disponible  PASS
tests/test_integracion_a2a.py::test_escenario_cascada               PASS
```

---

### Hito 6 — Excelencia (nota: 10)

**Objetivo:** sistema robusto que supera la batería automática completa
del coordinador, incluyendo **tanto la modalidad A (resolución
intra-grupo) como la modalidad B (cooperación cruzada)** descritas en
§ 2.3, y manteniendo además los criterios de calidad del código.

**Escenarios a verificar:**

1. **Batería completa superada.** En una única ejecución de evaluación,
   los tres conjuntos de pruebas automáticas (alumno, profesor en rama,
   no anunciadas) pasan en ambas modalidades A y B con la puntuación
   esperada para nota 10.
2. **Conmutación de perfil LLM.** Cambiar `perfil_activo` de `gemini` a
   `ollama_servidor` en `config.yaml` y reiniciar mantiene el sistema
   funcional: las pruebas de los hitos previos siguen pasando, aunque
   varíe el rendimiento. Un test verifica al menos un escenario
   completo en cada perfil.
3. **Transmisión continua (*streaming*) SSE en Tasks largas.** Una Task abierta con
   `tasks/sendSubscribe` emite eventos intermedios (`working` con
   `artifacts` parciales) durante el procesado, no solo el evento
   final `completed`. El coordinador puede consumir el progreso.
4. **Resistencia a peticiones malformadas.** Una alerta con JSON
   inválido, con un esquema desconocido o con tipos incorrectos
   produce `failed` con mensaje accionable; los logs registran el
   error con contexto y el sistema sigue operativo para la siguiente
   petición.
5. **Cuota de Gemini agotada.** Si Gemini devuelve `429 Quota
   exceeded` durante una petición, la Centralita reintenta con la
   misma petición tras un retraso, conmuta a un modelo alternativo
   declarado en `config.yaml` o degrada con un informe parcial. La
   estrategia adoptada queda documentada en el código y en la memoria.
6. **Caída transitoria del registro central.** Durante una sesión
   prolongada el registro central puede dejar de responder
   momentáneamente. El sistema reintenta con espera exponencial y
   recupera el alta sin acción manual.
7. **Caída de un agente público de otro grupo.** Durante un escenario
   B, el agente externo elegido puede dejar de responder a mitad de
   proceso. La
   Centralita aplica el respaldo descrito en el escenario 9 del
   Hito 5 y deja constancia en el informe.
8. **Sin literales en el código.** Una búsqueda automatizada en el código no
   encuentra IP, puertos, JID, claves de API ni URL del registro
   central. Toda la configuración está en `config.yaml` o en variables
   de entorno; un test ejecuta `grep` sobre el árbol de fuentes y
   declara fallo si encuentra alguno de esos patrones literales en
   código.
9. **Calidad del código.** Los linters configurados por el grupo
   pasan sin advertencias relevantes; las funciones públicas tienen
   *type hints* completos y *docstrings* en español; los nombres de
   tests siguen la convención `test_descripcion_de_lo_que_verifica`.
10. **Documentación reproducible.** Un compañero de otro grupo, sin
    contexto previo, sigue las instrucciones de `README.md` y
    `doc/` y consigue arrancar el sistema completo, ejecutar la
    batería de pruebas y comprender la decisión de visibilidad y el
    mapeo FIPA ↔ A2A.
11. **Latencia dentro de los umbrales.** Sobre las 20 consultas de
    latencia descritas en § 2.5, el tiempo medio y el P95 se sitúan en
    la franja *Excelente* o *Bueno*; la tasa de éxito supera el 95%.

**Clasificación de pruebas:**

- **Unitarias** — verificación automática de ausencia de literales en
  el árbol de fuentes, comprobación de calidad del código (linters,
  anotaciones de tipo, *docstrings*), control de peticiones
  malformadas en la capa de validación (escenarios 4 parcial, 8, 9).
- **Integración** — conmutación entre perfiles LLM, transmisión
  continua SSE, reintentos ante cuota agotada del LLM, respaldo ante
  caída de un agente público de otro grupo simulada con doble de
  prueba (escenarios 2, 3, 5, 7).
- **Despliegue** — batería completa A+B en los ordenadores del aula
  con perfil Gemini activo, latencia dentro de los umbrales de § 2.5
  sobre las 20 consultas reales, recuperación ante caída del registro
  central durante una sesión prolongada, documentación reproducible
  verificada por otro grupo (escenarios 1, 6, 10, 11).

**Lista de comprobación (acumulativa):**

- [ ] Supera la batería automática completa del coordinador en sus dos
  modalidades de prueba (A y B).
- [ ] Funciona con el **perfil de evaluación**: Gemini (Google AI) por
  defecto y conmutación al perfil de respaldo Ollama en
  `sinbad2ia.ujaen.es` mediante un único cambio en `config.yaml`.
- [ ] Transmisión continua SSE (`tasks/sendSubscribe`) implementada en la Centralita.
- [ ] Reintentos y conmutación de respaldo ante indisponibilidad transitoria del
  registro central o de los agentes públicos descubiertos.
- [ ] Código limpio: sin URL ni valores fijados literalmente, anotaciones de tipo (*type hints*) y *docstrings* en español.
- [ ] Documentación completa en `doc/`.
- [ ] 4 pruebas adicionales pasan.

**Pruebas adicionales requeridas:**

```
tests/test_agente_a2a.py::test_peticion_malformada                  PASS
tests/test_agente_a2a.py::test_streaming_sse                        PASS
tests/test_integracion_a2a.py::test_latencia_aceptable              PASS
tests/test_agente_a2a.py::test_config_sin_hardcodear                PASS
```

---

## 4. Resumen de pruebas por hito

| Hito | Nota | Pruebas nuevas | Total acumulado | Escenarios cubiertos | Componentes clave |
|------|------|----------------|-----------------|----------------------|-------------------|
| 1 | 5 | 5 | 5 | 8 | Centralita pública en IP del aula, 1 Agent Card |
| 2 | 6 | +4 | 9 | 9 | 3 públicos comunicándose, visibilidad declarada en `config.yaml` |
| 3 | 7 | +3 | 12 | 10 | 3 públicos + 2 privados, escenario completo intra-grupo (modalidad A) |
| 4 | 8 | +4 | 16 | 11 | Contract Net interno, respuesta al coordinador a través de la Centralita |
| 5 | 9 | +3 | 19 | 12 | Registro central, descubrimiento y delegación entre grupos (modalidad B), cascada |
| 6 | 10 | +4 | 23 | 11 | Batería completa A+B, transmisión continua, robustez, excelencia |

> **Cómo leer las dos columnas de pruebas.** La columna *Pruebas nuevas*
> indica el número mínimo de **tests pytest concretos** cuyos nombres
> aparecen citados en el apartado *"Pruebas adicionales requeridas"* de
> cada hito de § 3. La columna *Escenarios cubiertos* refleja el número
> de escenarios listados en el apartado *"Escenarios a verificar"* del
> mismo hito. Un mismo escenario puede traducirse en **uno o varios
> tests pytest**, según las variantes y aserciones que decida el grupo.
> Para superar el hito es necesario **cubrir todos los escenarios**, no
> únicamente alcanzar la cuenta mínima de tests con nombre fijo.

---

## 5. Presentación final

### 5.1. Formato

- **Duración:** 3-4 minutos por grupo.
- **Formato:** presentación libre (diapositivas, demo en vivo, o
  combinación de ambas).
- **Lugar:** los ordenadores del aula, con el sistema arrancado en las
  mismas condiciones de la prueba automática (perfil Gemini activo,
  agentes públicos registrados en `sinbad2.ujaen.es`). Una demo en vivo
  desde un equipo personal queda excluida por las restricciones de red
  descritas en § 2.4.

### 5.2. Contenido esperado

| Sección | Duración sugerida | Contenido |
|---------|-------------------|-----------|
| Arquitectura | 1 min | Diagrama del sistema con la **decisión de visibilidad del grupo** (qué dos especialistas se han declarado públicos y por qué), papel del registro central, perfil LLM elegido y estructura de capas (`logica/` / `herramientas/` / `agentes/`). |
| Mapeo FIPA ↔ A2A | 1 min | Correspondencias concretas aplicadas a Villa Olivar: actos de habla FIPA realizados como Tasks A2A, Contract Net (red de contratos) implementado sobre `tasks/send`, federación entre grupos como instancia de protocolo de coordinación. |
| Demostración | 1 min | Ejecución en vivo de un escenario de **modalidad A** (intra-grupo, con los cinco agentes propios) y, si el tiempo lo permite, un escenario de **modalidad B** (con delegación entre grupos hacia un agente público de otro grupo). |
| Lecciones | 30 s | Qué fue difícil, qué se aprendió, qué se haría diferente. |

### 5.3. Criterios de evaluación de la presentación

| Criterio | Peso | Descripción |
|----------|------|-------------|
| Claridad | 30% | Explicación comprensible de la arquitectura, de la decisión de visibilidad (3 públicos / 2 privados) y de las decisiones técnicas relevantes (criterio de selección en CFP, mecanismo de invocación de los privados, perfil LLM). |
| Profundidad técnica | 30% | Comprensión del protocolo A2A, de su relación con FIPA, del papel del registro central y de la diferencia entre modalidades A y B. |
| Demostración | 25% | El sistema funciona en vivo en al menos la modalidad A; se valora positivamente añadir una demostración de modalidad B (cooperación cruzada con otro grupo) cuando el tiempo lo permita. |
| Innovación | 15% | Soluciones creativas más allá del enunciado: criterios de selección en CFP, mejoras de robustez, conmutación de respaldo entre proveedores externos, métricas propias, transmisión continua aprovechada pedagógicamente. |

---

## 6. Calidad de código y documentación (20%)

### 6.1. Código

| Criterio | Descripción |
|----------|-------------|
| Separación de capas | `logica/` sin dependencias externas, `herramientas/` con `FunctionTool` reutilizables, `agentes/` con la integración A2A. La lógica de dominio se puede testear sin red ni LLM. |
| Configuración | Todo se lee de `config.yaml` o de variables de entorno: URL, puertos, JIDs, claves de API (`GOOGLE_API_KEY`), URL del registro central, perfil LLM activo. **Cero literales** equivalentes en código. |
| Visibilidad | El reparto **3 públicos / 2 privados** está reflejado en `config.yaml`. Los públicos publican Agent Card y se registran en `sinbad2.ujaen.es`; el mecanismo elegido por el grupo para invocar a los privados está documentado, aislado de la red exterior y limitado a la Centralita propia. |
| Pruebas | Tests redactados según la guía de § 3 (escenarios) y de la rama del profesor (§ 1, bloque del 25%). Convenciones: nombres `test_descripcion_de_lo_que_verifica`, tests asíncronos marcados con `@pytest.mark.asyncio`, separación entre tests unitarios y de integración. |
| Convenciones | Type hints completos en funciones públicas, *docstrings* en español, nombres descriptivos, sin uso de `break`, retorno único por función (CLAUDE.md global). |
| Manejo de errores | Tiempos de espera (*timeouts*) en llamadas LLM y A2A, conmutación de respaldo entre perfiles LLM (Gemini → Ollama servidor) y entre proveedores externos de otros grupos, recuperación ante caídas transitorias del registro central, control de peticiones malformadas sin caída del servidor. |

### 6.2. Documentación

| Criterio | Descripción |
|----------|-------------|
| Completitud | Cubre la evolución Nivel 1 → 2 → 3 y describe el sistema final con su modelo de visibilidad y su integración con el registro central. |
| Coherencia | Narrativa clara que conecta **FIPA → MCP → A2A** e ilustra cuándo se aplica cada modalidad de prueba (A intra-grupo, B entre grupos). |
| Diagramas | Arquitectura de despliegue (públicos en IP del aula vs privados aislados, registro central, coordinador), flujo de datos en un escenario completo y secuencia de un Contract Net interno. |
| Decisiones | Justificación de la **decisión de visibilidad** del grupo, del **criterio de selección** en CFP, del **mecanismo de invocación de los privados** y de la **elección de perfil LLM** (Gemini por defecto, conmutación al respaldo). |
| README de ejecución | Instrucciones reproducibles para arrancar el sistema en los **ordenadores del aula** con perfil Gemini activo y para conmutar al respaldo Ollama servidor con un único cambio de `config.yaml`. |
| Calidad | Redacción académica en español, formato coherente, vocabulario preciso (anglicismos siempre acompañados de su equivalente castellano la primera vez que aparezcan). |

---

*Hitos de evaluación — Proyecto Villa Olivar — Sistemas Multiagente — Universidad de Jaén*
