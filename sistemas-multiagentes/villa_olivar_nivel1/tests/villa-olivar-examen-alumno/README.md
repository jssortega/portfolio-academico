# Examen del Nivel 3 — Material del alumno (Villa Olivar)

**Asignatura:** Sistemas Multiagente — Grado en Ingeniería
Informática

**Universidad de Jaén** — Departamento de Informática

**Proyecto:** Villa Olivar — Coordinación de Emergencias (Nivel 3,
A2A sobre HTTP)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

---

> ## ⚠ Esta rama determina la nota del proyecto
>
> La nota final del Nivel 3 se construye sobre **dos evidencias
> complementarias** que el grupo prepara sobre esta misma rama:
>
> 1. **La sesión presencial del examen.** El día del examen el
>    grupo arranca su sistema en el aula, demuestra su
>    funcionamiento ante el profesor y puede aún realizar
>    **modificaciones en directo** que se vean en la sesión. Lo
>    observado se incorpora a la nota.
> 2. **La evaluación automática posterior.** Tras la sesión, el
>    Coordinador del profesor ejecuta sobre el repositorio del
>    grupo —en el estado en que quedó al cierre del examen— la
>    **serie de validación** que está aquí (`tests/profesor/`). El
>    resultado de esa evaluación es la segunda evidencia.
>
> Las dos evidencias se combinan para fijar la nota final del
> proyecto. Por eso no es una rama que convenga preparar con
> prisa la víspera del examen:
>
> - **Tómate el tiempo necesario** para integrar bien los modelos
>   del contrato, adaptar los agentes a la factoría y depurar las
>   incidencias con la pila Docker en casa.
> - **Ejecuta la serie de validación del profesor con frecuencia** durante el
>   desarrollo (cada cambio significativo) en lugar de dejarla
>   para el final: cada test que pasa documenta una propiedad ya
>   garantizada.
> - **Escribe los tests del propio grupo** (los enumerados en
>   [`doc/ESCENARIOS_TESTS_OBLIGATORIOS.md`](doc/ESCENARIOS_TESTS_OBLIGATORIOS.md))
>   en paralelo con la implementación, no a posteriori.
> - **Verifica antes de la sesión** que el sistema arranca limpio
>   en el modo Docker desde una clonación nueva del repositorio.
>
> Lo que el profesor evalúa después del aula es exactamente lo
> que el grupo puede comprobar en casa con esta rama. No hay
> sorpresas: el contrato está fijado, los tests son los que son
> y los escenarios obligatorios están enumerados. La nota
> automática depende de cuántos escenarios y cuántos tests del
> profesor estén pasando cuando se ejecute la evaluación; lo
> demostrado en vivo durante la sesión la complementa.

---

## 1. Qué es esta rama

Esta rama reúne **todo lo que el alumno necesita** para preparar
la entrega del Nivel 3 del proyecto Villa Olivar y para
verificar su propio sistema con las mismas pruebas que el
Coordinador del profesor usará el día del examen.

Contiene:

- **`contrato/`** — Modelos Pydantic del contrato externo del
  proyecto: `AgentCard`, `AlertaEmergencia`, `InformeActuacion`,
  `InformeResolucion`, `EventoTraza`, etc.
- **`tests/profesor/`** — 118 tests pytest (62 unitarios del
  contrato, 7 unitarios del cliente A2A y 49 de integración en
  caja negra) que verifican el cumplimiento del contrato. Son
  los mismos tests que el Coordinador del profesor ejecutará el
  día del examen; el alumno los hereda y no los modifica. **No
  sustituyen** a los tests que el grupo debe escribir sobre su
  propio código (ver §4).
- **`factoria/`** — Clase base `AgenteA2A` y lanzador
  homogéneo. Garantiza que todos los grupos arranquen sus
  agentes con la misma estructura externa, condición necesaria
  para que el Coordinador del profesor pueda evaluarlos a todos
  con la misma serie de validación.
- **`config/`** — Toda la configuración del alumno vive aquí.
  El directorio contiene dos ficheros, con roles distintos:
  - `config.yaml` (**configuración activa**, se edita
    in-situ): perfiles `local`/`servidor` (red, capa A2A, LLM)
    y, al final, el **bloque `evaluacion:` comentado** con el
    mapa rol → URL que las pruebas del profesor leen. El
    alumno descomenta y ajusta ese bloque antes de lanzar la
    serie de validación.
  - `agents.yaml.ejemplo` (**plantilla**, se copia a
    `agents.yaml` y se ajusta): declaración homogénea de los
    cinco agentes (Centralita + 2 públicos + 2 privados).
- **`cliente_pruebas/cliente.py`** — Cliente A2A asíncrono que las
  pruebas usan internamente.
- **`doc/`** — Toda la documentación que afecta al alumno (los
  documentos que describen el diseño del lado del profesor viven
  en la rama `coordinador-profesor`, no aquí):
  - [`doc/PREPARACION_EXAMEN_ALUMNO.md`](doc/PREPARACION_EXAMEN_ALUMNO.md)
  - [`doc/PRUEBAS_PREVIAS_AL_EXAMEN.md`](doc/PRUEBAS_PREVIAS_AL_EXAMEN.md)
  - [`doc/ESCENARIOS_TESTS_OBLIGATORIOS.md`](doc/ESCENARIOS_TESTS_OBLIGATORIOS.md)
  - [`doc/MODO_DOCKER.md`](doc/MODO_DOCKER.md)
  - [`doc/GUIA_FACTORIA_NIVEL3.md`](doc/GUIA_FACTORIA_NIVEL3.md)
    — *guía de adaptación con el mínimo cambio posible*: cómo
    apoyarse en `factoria.AgenteA2A` para implementar los seis
    hitos del Nivel 3 reutilizando la lógica, las herramientas y
    los prompts que ya se tienen en `desarrollo-nivel3`. Incluye
    la comparativa "antes/después" lado a lado de un especialista
    y de la Centralita.
  - [`doc/resolucion_a2a_porque_no_acepta_tareas.md`](doc/resolucion_a2a_porque_no_acepta_tareas.md)
    — *error común durante la implementación*: el agente publica
    su Agent Card y responde a `curl`, pero rechaza las tareas
    A2A (`tasks/send`). Recorre el cuerpo JSON-RPC mínimo, las
    siete causas más frecuentes y la tabla de códigos de error.

Esta rama y la rama hermana `coordinador-profesor` se publican
**simultáneamente** en la última sesión de prácticas. Las dos
contienen los mismos tests, los mismos modelos Pydantic y el
mismo cliente A2A; lo que cambia entre ellas es:

- En `coordinador-profesor`: el lanzador `coordinador_main.py`
  y la lista del aula `config/config.yaml` con los grupos a
  evaluar.
- En `examen-alumno` (esta rama): la factoría `factoria/`, el
  lanzador `main.py`, la configuración del alumno
  (`config/config.yaml` activo y la plantilla
  `config/agents.yaml.ejemplo`) y la documentación específica
  del alumno.

---

## 2. Procedimiento recomendado

El alumno debería seguir estos cinco pasos, en este orden:

1. **Leer**
   [`doc/PREPARACION_EXAMEN_ALUMNO.md`](doc/PREPARACION_EXAMEN_ALUMNO.md)
   para entender qué fusionar en su `desarrollo-nivel3` y qué
   debe respetar del contrato externo.

2. **Preparar el modo Docker** siguiendo
   [`doc/MODO_DOCKER.md`](doc/MODO_DOCKER.md) para tener un
   registro REST y un LLM locales antes de tocar nada del
   sistema multiagente.

3. **Adaptar sus agentes a la factoría**: cada agente del Nivel 2
   se convierte en una subclase de `factoria.AgenteA2A` que
   implementa `manejar_alerta` y, opcionalmente, registra
   handlers Contract Net adicionales.

4. **Escribir los tests del propio grupo** que cubran los
   escenarios obligatorios enumerados en
   [`doc/ESCENARIOS_TESTS_OBLIGATORIOS.md`](doc/ESCENARIOS_TESTS_OBLIGATORIOS.md).
   No son los tests del profesor (que ya están en
   `tests/profesor/`), sino tests sobre el código interno del
   grupo: validan unidades pequeñas con mocks y combinaciones
   de componentes propios. La lista de escenarios no es
   opcional: cada hito al que el grupo aspire fija un mínimo
   exigible.

5. **Ejecutar la serie de validación del profesor** con la
   frecuencia que considere oportuna, siguiendo
   [`doc/PRUEBAS_PREVIAS_AL_EXAMEN.md`](doc/PRUEBAS_PREVIAS_AL_EXAMEN.md).
   El objetivo es llegar al examen con la mayor parte de los
   tests en verde.

---

## 3. Arranque rápido

### 3.1. Instalación

Se asume que el grupo ya trabaja en un **entorno virtual
Python** activo (heredado del Nivel 2 o creado para esta
rama). Con el entorno activado:

```bash
pip install -r requirements.txt
```

Si no se dispone aún de un entorno virtual, crear y activar
uno antes de la instalación:

```bash
# Solo si no hay entorno virtual previo:
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate           # Windows
```

### 3.2. Preparar la configuración

El alumno parte de los dos ficheros existentes en `config/`:

1. **`config/agents.yaml`** se crea copiando la plantilla y
   ajustando los puertos, módulos y clases concretas de los
   agentes del grupo:

   ```bash
   cp config/agents.yaml.ejemplo config/agents.yaml
   ```

2. **`config/config.yaml`** se edita in-situ para descomentar
   el bloque `evaluacion:` al final del fichero y ajustar las
   URL si los puertos difieren del ejemplo (por defecto, los
   del rango 81xx documentado en el propio fichero). El perfil
   de red activo (`red.perfil_activo`) se cambia también aquí
   para alternar entre `local` (Docker) y `servidor` (aula).

### 3.3. Levantar la infraestructura local

Consultar [`doc/MODO_DOCKER.md`](doc/MODO_DOCKER.md). Resumen:

```bash
git clone https://gitlab.com/ssmmaa/infraestructurassmmaa/ssmmaa-infraestructura.git
cd ssmmaa-infraestructura && make build && make up && make pull-modelo
```

### 3.4. Arrancar el sistema multiagente

Desde la raíz de esta rama:

```bash
python main.py
```

### 3.5. Lanzar la serie de validación del profesor en otra terminal

```bash
pytest tests/profesor/integracion/ -v
```

### 3.6. Lanzar los tests del propio grupo

Los tests que el grupo escribe sobre su código (unitarios y de
integración) viven en `tests/unidad/` y `tests/integracion/`
(o donde el grupo prefiera, siempre que `pytest` los encuentre):

```bash
pytest tests/unidad/ tests/integracion/ -v
```

---

## 4. Tests obligatorios del propio grupo

Los tests de `tests/profesor/` validan el **contrato externo** y
son necesarios pero no suficientes. El grupo **debe escribir sus
propios tests** sobre su código interno, organizados en dos
categorías:

- **Unitarios** del grupo: funciones de dominio, validadores,
  lógica de selección Contract Net, agregación de informes…
  Sin red, sin LLM real, sin agentes arrancados.
- **Integración** del grupo: combinaciones de componentes
  propios (Centralita + un especialista, factoría + registro
  local, CNP entre dos unidades del mismo rol). No dependen
  del Coordinador del profesor.

La lista concreta de escenarios mínimos exigibles, organizada
por hito, está en
[`doc/ESCENARIOS_TESTS_OBLIGATORIOS.md`](doc/ESCENARIOS_TESTS_OBLIGATORIOS.md).
Saltar un escenario obligatorio del hito al que se aspira
reduce proporcionalmente la nota del bloque de calidad de
código y documentación.

Las **pruebas de despliegue** son las que ejecuta el
Coordinador del profesor el día del examen: ya están en
`tests/profesor/` y el grupo no las escribe.

---

## 5. Lo que NO se debe modificar

Tres elementos forman parte del contrato y no se pueden alterar
sin romper la compatibilidad con el Coordinador del profesor:

- **`contrato/`** — Modelos Pydantic. Añadir campos opcionales
  está bien; cambiar los obligatorios rompe la entrega.
- **`tests/profesor/`** — Los mismos tests que ejecutará el
  profesor. Modificarlos o comentarlos no aumenta la nota.
- **`factoria/agente_a2a.py`** — La firma del extremo HTTP y el
  esquema de la Agent Card. La factoría está diseñada para
  extenderse por composición (sobrescribir
  `manejar_alerta`, registrar handlers, ampliar la Agent Card),
  no para modificarse. En particular, el extremo JSON-RPC se
  atiende en **`POST /` y en `POST /a2a`** (el mismo manejador en
  ambas rutas, para ser verificable por el coordinador y por el
  supervisor del profesor); no elimines ninguna de las dos rutas.
  El detalle está en `doc/GUIA_FACTORIA_NIVEL3.md`, §2.1.

Todo lo demás (`config/agents.yaml`, el bloque `evaluacion`
de `config/config.yaml`, las clases concretas de `agentes/`,
los prompts, las `FunctionTool`) es del grupo.

---

## 6. Rama hermana del profesor

La rama `coordinador-profesor` contiene el lanzador
`coordinador_main.py` con el que el profesor ejecuta esta misma
serie de validación contra los grupos del aula el día del examen. El alumno
no necesita acceder a ella para preparar la entrega: todo lo
relevante está duplicado aquí.

---

## 7. Documentación complementaria

Toda la documentación dirigida al alumno vive en `doc/`:

- [`doc/PREPARACION_EXAMEN_ALUMNO.md`](doc/PREPARACION_EXAMEN_ALUMNO.md)
- [`doc/ESCENARIOS_TESTS_OBLIGATORIOS.md`](doc/ESCENARIOS_TESTS_OBLIGATORIOS.md)
- [`doc/PRUEBAS_PREVIAS_AL_EXAMEN.md`](doc/PRUEBAS_PREVIAS_AL_EXAMEN.md)
- [`doc/MODO_DOCKER.md`](doc/MODO_DOCKER.md)
- [`doc/GUIA_FACTORIA_NIVEL3.md`](doc/GUIA_FACTORIA_NIVEL3.md)
  — **adaptación al Nivel 3 con el mínimo cambio posible**.
  Explica cómo apoyarse en `factoria.AgenteA2A` para cumplir los
  seis hitos del Nivel 3 reutilizando lo que el grupo ya tiene en
  `desarrollo-nivel3` (lógica, herramientas, prompts, ontología,
  cliente del registro REST). Incluye la receta del diff mínimo
  por agente, comparativa "antes/después" para un especialista y
  para la Centralita, integración LLM (Gemini/Ollama), Contract
  Net (Hito 4), cooperación cruzada (Hitos 5-6), inscripción REST
  y el mapeo Hito a Hito de "qué tienes que escribir tú".
- [`doc/resolucion_a2a_porque_no_acepta_tareas.md`](doc/resolucion_a2a_porque_no_acepta_tareas.md)
  — **errores comunes en la implementación A2A**: qué hacer
  cuando el agente acepta `curl` sobre el Agent Card pero
  rechaza las tareas `tasks/send`. Catálogo de las siete causas
  más frecuentes (envoltura JSON-RPC, URL del Agent Card,
  cabeceras, nombre del método, estructura de `parts`,
  validación Pydantic del cuerpo, handler no registrado) y
  procedimiento de depuración paso a paso.

El **diseño detallado** del bloque del 25 % (plan exhaustivo de
pruebas, guía de integración del lado del profesor, etc.) vive
en la rama `coordinador-profesor`. El alumno no necesita
consultarlo para preparar la entrega: los tests son la
especificación operativa que debe cumplir.
