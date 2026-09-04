# Guía de uso de la factoría para implementar el Nivel 3

Esta guía está pensada para el alumno que está **implementando
la rama `desarrollo-nivel3`** del proyecto Villa Olivar y quiere
usar la factoría `factoria.AgenteA2A` (provista en esta rama
`examen-alumno`) como atajo para llegar a los hitos con el
mínimo de código nuevo posible.

La idea es sencilla: **la factoría sustituye al esqueleto
`agentes/base_agente_a2a.py`** que pide el Nivel 3 y reemplaza
toda la composición `LlmAgent` + `AgentExecutor` +
`A2AStarletteApplication` por una clase base ya escrita y
cerrada. El alumno conserva casi todo lo que ya tenía del Nivel
2 (lógica de dominio, `FunctionTool` de ADK, prompts, ontología)
y solo reescribe la fachada de cada agente.

---

## 1. Qué se reutiliza intacto desde `desarrollo-nivel3`

| Carpeta de `desarrollo-nivel3` | Acción en `examen-alumno` |
|--------------------------------|---------------------------|
| `logica/` (funciones puras de dominio) | **Reutilizar tal cual.** Son funciones sin acoplamiento con SPADE, ADK ni A2A. |
| `herramientas/` (`FunctionTool` ADK que envuelven la lógica) | **Reutilizar tal cual.** La factoría no impone cómo se llama al LLM; se sigue usando ADK desde dentro del agente. |
| `prompts/` (instrucciones de sistema por rol) | **Reutilizar tal cual.** El prompt es independiente del transporte. |
| `ontologia/` (esquema JSON, modelos Pydantic propios) | **Reutilizar tal cual** si los agentes los siguen necesitando, junto al `contrato/` oficial. |
| `descubrimiento/descubrimiento_a2a.py` (cliente REST del registro) | **Reutilizar tal cual.** El alta, baja y *heartbeat* del Nivel 3 siguen sirviendo. |
| `config.yaml` raíz del Nivel 3 (perfiles A2A/LLM, lista de agentes) | **Migrar los valores** a `config/config.yaml` y `config/agents.yaml` de esta rama. No se copia el fichero entero; se trasladan los campos. |
| `agent_cards/*.json` (tres tarjetas redactadas a mano) | **Descartar.** La factoría publica la Agent Card automáticamente; el grupo enriquece `skills` por código sobrescribiendo `construir_agent_card`. |
| `agentes/base_agente_a2a.py` (esqueleto provisto por el Nivel 3) | **Borrar.** Su papel lo asume `factoria.AgenteA2A`. |
| `agentes/agente_*.py` (los cinco agentes A2A) | **Reescribir mínimamente** según §3. Solo cambian la clase base y el método de entrada; el cuerpo (LLM + tools + lógica) se conserva. |

El cambio neto, contado en código que el alumno escribe a mano,
es **mucho menor que en el esqueleto original**: la factoría
absorbe la composición ADK + A2A SDK, la publicación de la Agent
Card y la traducción de excepciones.

---

## 2. Lo que la factoría te hace gratis

Por cada agente concreto, la factoría ya se ocupa de:

- Servidor `aiohttp` que escucha en el `host:puerto` declarado
  en `agents.yaml`.
- Publicar la Agent Card en `GET /.well-known/agent.json` con
  el esquema del `contrato.agent_card.AgentCard`.
- Atender el extremo JSON-RPC en **`POST /` y, además, en `POST /a2a`**
  (mismo manejador; ver §2.1) y despachar entre `tasks/send`, `tasks/get`,
  `tasks/sendSubscribe` y los handlers personalizados que
  registres (Contract Net).
- Parsear la envoltura JSON-RPC y devolver `-32700`/`-32600`/`-32601`
  según corresponda si está mal formada.
- Localizar el `DataPart` del mensaje y validarlo contra
  `contrato.alerta_emergencia.AlertaEmergencia` con Pydantic.
- Llamar a tu `manejar_alerta(alerta)` con la `AlertaEmergencia`
  ya validada.
- Envolver el `InformeResolucion` que devuelves en una `Task`
  con estado `completed` y artefacto `data`.
- Traducir cualquier excepción no controlada de tu código a una
  `Task` con estado `failed` y el mensaje de la excepción.
- Apagar el servidor ordenadamente en `Ctrl+C`.

Equivalentemente, lo que **deja de ser tu trabajo** respecto al
esqueleto original del Nivel 3: no hay `A2AStarletteApplication`
que construir, no hay `DefaultRequestHandler` que enchufar, no
hay `AgentExecutor` que escribir y no hay `uvicorn` que arrancar
por agente. Tampoco hay tarjetas JSON sueltas que mantener.

### 2.1. El extremo A2A se atiende en `/` y en `/a2a`

La factoría registra el **mismo** manejador JSON-RPC en **dos rutas**:

- **`POST /`** — la raíz, ruta histórica que usa el cliente del coordinador.
- **`POST /a2a`** — la ruta que fija el contrato del supervisor del profesor
  (`url_a2a` registrada en el directorio **+ `/a2a`**).

Ambas rutas se comportan **igual**: aceptan la misma envoltura JSON-RPC
(`tasks/send`, `tasks/get`, `tasks/sendSubscribe`), invocan tu
`manejar_alerta` y devuelven la misma `Task`. El alias es **aditivo y
compatible hacia atrás**: la raíz sigue funcionando como antes y, además, tu
agente queda accesible por la convención `/a2a`. Así, **el mismo sistema es
verificable por las dos herramientas del profesor** (el coordinador, que envía
a la raíz, y el supervisor, que añade `/a2a`) sin que tengas que elegir una.

**Qué implica para tu solución:**

- **No tienes que hacer nada**: tu Centralita y tus especialistas públicos
  responden en ambas rutas automáticamente al heredar de `AgenteA2A`.
- En el **registro REST** se publica la `url_a2a` **base** (`http://host:puerto`,
  sin sufijo). Quien consume el directorio (coordinador o supervisor) decide a
  qué ruta enviar; tu agente atiende las dos.
- Si **delegas** en otro agente (cooperación del Hito 5), envía la subtarea a la
  `url_a2a` que te devuelve el registro. Tanto la raíz como `/a2a` son válidas;
  si el otro agente sigue esta factoría, ambas responden igual.
- **No cambies `_construir_aplicacion` para quitar ninguna de las dos rutas**:
  eliminar `/` rompería al coordinador y eliminar `/a2a`, al supervisor.

---

## 3. La regla del mínimo cambio: receta por agente

Para cada uno de los cinco agentes del Nivel 3, **el diff
mínimo** respecto a la versión ADK consiste en:

1. Cambiar la clase base: de la antigua `BaseAgenteA2A` (la
   skeletal del Nivel 3) a `factoria.AgenteA2A`.
2. Renombrar el método de entrada al nombre que pide la
   factoría: `manejar_alerta(self, alerta: AlertaEmergencia) -> InformeResolucion`.
3. Asegurarse de que el cuerpo devuelve una instancia
   **validada** de `InformeResolucion` (no un dict).
4. Quitar todo el código de bootstrap A2A SDK del propio agente
   (si lo tenías inline): construcción de `A2AStarletteApplication`,
   `AgentExecutor`, `uvicorn.run`, etc. Eso ya no es asunto del
   agente.
5. Dejar el resto **igual**: la llamada al `LlmAgent`, las
   `FunctionTool`, el prompt, las funciones de `logica/`.

Esos cinco pasos son lo único que separa tu código del Nivel 2
(o tu intento incompleto del Nivel 3) de un agente conforme con
el contrato del examen.

---

## 4. Antes y después: especialista típico

### 4.1. Antes (esqueleto del Nivel 3 con `a2a-sdk`)

```python
# agentes/agente_bomberos.py — VERSIÓN del Nivel 3 esqueletal
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
import uvicorn

from google.adk.agents import LlmAgent
from herramientas.tools_bomberos import herramientas_bomberos


class BomberosExecutor(AgentExecutor):

    def __init__(self) -> None:
        self._llm = LlmAgent(
            name="bomberos",
            tools=herramientas_bomberos(),
            instruction=open("prompts/bomberos.txt").read(),
        )

    async def execute(self, context: RequestContext, queue: EventQueue) -> None:
        datos = context.message.parts[0].root.data
        respuesta = await self._llm.run_async(datos)
        # ... mapear `respuesta` a Task events, encolar
        # TaskArtifactUpdateEvent + TaskStatusUpdateEvent ...

    async def cancel(self, context, queue) -> None:
        raise UnsupportedOperationError()


def construir_app():
    handler = DefaultRequestHandler(
        agent_executor=BomberosExecutor(),
        task_store=InMemoryTaskStore(),
    )
    return A2AStarletteApplication(
        agent_card=cargar_agent_card_json("agent_cards/card_bomberos.json"),
        http_handler=handler,
    ).build()


if __name__ == "__main__":
    uvicorn.run(construir_app(), host="0.0.0.0", port=8120)
```

Esto es, aproximadamente, lo que pide el Nivel 3 escribir **por
cada uno de los cinco agentes**. La parte específica del rol
Bomberos (su `LlmAgent`, sus `FunctionTool`, su prompt) ocupa
unas pocas líneas; el resto es andamiaje A2A.

### 4.2. Después (con la factoría)

```python
# agentes/bomberos.py — VERSIÓN con la factoría
from factoria import AgenteA2A
from contrato.alerta_emergencia import AlertaEmergencia
from contrato.informe_resolucion import InformeResolucion
from contrato.informe_actuacion import InformeActuacion

from google.adk.agents import LlmAgent
from herramientas.tools_bomberos import herramientas_bomberos


class Bomberos(AgenteA2A):

    def __init__(self, especificacion):
        super().__init__(especificacion)
        self._llm = LlmAgent(
            name="bomberos",
            tools=herramientas_bomberos(),
            instruction=open("prompts/bomberos.txt").read(),
        )

    async def manejar_alerta(
        self,
        alerta: AlertaEmergencia,
    ) -> InformeResolucion:
        actuacion: InformeActuacion = await self._invocar_llm(alerta)
        informe = InformeResolucion(
            id_emergencia=alerta.id_emergencia,
            estado_final="resuelta",
            informes_especialistas=[actuacion],
        )
        return informe

    async def _invocar_llm(self, alerta: AlertaEmergencia) -> InformeActuacion:
        # Reutiliza exactamente la misma llamada al LlmAgent que
        # tenías en el Nivel 2; solo se cambia el envoltorio.
        ...
```

Todo el andamiaje A2A (servidor, dispatcher, Agent Card,
arranque uvicorn) ha desaparecido. La parte ADK (LlmAgent,
tools, prompts) se conserva intacta. El alumno escribe **una
clase** y un método.

El lanzador `main.py` lo arranca leyendo `config/agents.yaml`,
así que tampoco hay que escribir un bloque `if __name__ == "__main__"`
por agente.

---

## 5. Antes y después: Centralita

La Centralita es ligeramente distinta porque, además de atender
alertas del coordinador, tiene que **convocar a sus
especialistas**. La parte de coordinación se queda igual; la
fachada cambia.

```python
# agentes/centralita.py — VERSIÓN con la factoría
from factoria import AgenteA2A
from contrato.alerta_emergencia import AlertaEmergencia
from contrato.informe_resolucion import InformeResolucion
from cliente_pruebas.cliente import ClienteA2A


class Centralita(AgenteA2A):

    def __init__(self, especificacion):
        super().__init__(especificacion)
        # `parametros` viene del bloque correspondiente en
        # agents.yaml; ahí declaras las URL internas de los
        # especialistas privados.
        self._privados: dict[str, str] = especificacion.parametros.get(
            "privados", {},
        )
        # Mantén tu LlmAgent de clasificación tal como lo tenías.
        self._clasificador = self._construir_clasificador()

    async def manejar_alerta(
        self,
        alerta: AlertaEmergencia,
    ) -> InformeResolucion:
        # 1. Clasificar (mismo código que ya tenías en N2/N3).
        especialistas = await self._clasificador.run_async(alerta)

        # 2. Convocar a cada especialista por A2A.
        informes = []
        for rol in especialistas:
            url = self._url_para_rol(rol)
            async with ClienteA2A(url_base=url) as cliente:
                resp = await cliente.enviar_tarea(alerta=alerta)
                informes.append(resp.informe)

        # 3. Agregar y devolver.
        return InformeResolucion(
            id_emergencia=alerta.id_emergencia,
            estado_final="resuelta",
            informes_especialistas=[i.actuacion for i in informes],
        )

    def _url_para_rol(self, rol: str) -> str:
        # Privados: URL inyectada por agents.yaml.
        # Públicos del grupo: misma técnica, o descubrir en el
        # registro REST si prefieres centralizar (ver §8).
        if rol in self._privados:
            return self._privados[rol]
        return self._descubrir_publico(rol)
```

### 5.1. Inyección de las URL privadas

Las URL de los especialistas privados se declaran en el bloque
`parametros` de la Centralita en `config/agents.yaml`. Cambiar
de perfil de red (local → aula) solo obliga a editar el YAML, no
el código:

```yaml
- identificador: "centralita-grupo"
  rol: "centralita"
  visibilidad: "publico"
  puerto: 8110
  modulo: "agentes.centralita"
  clase: "Centralita"
  activo: true
  parametros:
    privados:
      policia:   "http://localhost:8140"
      municipal: "http://localhost:8150"
```

---

## 6. Integrar el LLM (Gemini / Ollama)

El acceso al LLM **no cambia respecto al Nivel 2/3**: sigues
construyendo `LlmAgent` con sus tools y su prompt en el
`__init__` del agente. La factoría no se mete con el modelo.

El perfil activo se elige en `config/config.yaml` (`llm.perfil_activo`).
Cargas el bloque correspondiente en el `__init__` del agente y
lo pasas al `LlmAgent` exactamente como ya lo hacías. Si llevas
la carga del YAML a una pequeña utilidad en `agentes/_config.py`,
los cinco agentes la comparten sin duplicación.

---

## 7. Contract Net (Hito 4) sin tocar la factoría

Contract Net añade métodos JSON-RPC nuevos
(`contract_net/cfp`, `contract_net/award`). La factoría soporta
**handlers personalizados** para cualquier método no incluido en
el núcleo A2A. Se registran una sola vez en el `__init__` del
agente:

```python
class Bomberos(AgenteA2A):

    def __init__(self, especificacion):
        super().__init__(especificacion)
        self.registrar_handler("contract_net/cfp", self._handler_cfp)
        self.registrar_handler("contract_net/award", self._handler_award)

    async def _handler_cfp(self, params: dict) -> dict:
        propuesta = await self._evaluar_cfp(params)
        return {"propuesta": propuesta}

    async def _handler_award(self, params: dict) -> dict:
        await self._aceptar_award(params)
        return {"aceptado": True}
```

La factoría:

- Recibe la petición, parsea el JSON-RPC, extrae `params`.
- Llama a tu handler con `params` ya deserializado.
- Envuelve tu `result` en la respuesta JSON-RPC.
- Si tu handler lanza, traduce a `error.code = -32000` con el
  mensaje del fallo (HTTP 500).

No hay que tocar nada de `factoria/agente_a2a.py`. La lógica de
negociación es 100 % tuya.

---

## 8. Cooperación cruzada (Hitos 5 y 6)

El día del examen el coordinador del profesor lanzará escenarios
que requieren un rol **que tu grupo mantiene privado**. La
Centralita debe entonces:

1. Consultar el registro REST y descubrir qué grupo expone ese
   rol como público (reutiliza `descubrimiento/descubrimiento_a2a.py`
   tal como lo escribiste en `desarrollo-nivel3`).
2. Leer la Agent Card de ese agente para confirmar URL y skills.
3. Enviarle la subtarea con el `ClienteA2A` del §5.

La factoría no implementa esta lógica porque depende del cliente
REST del grupo. Lo que sí te da hecho es **todo lo demás** (el
extremo HTTP de tu Centralita por el que llega la alerta y el
cliente A2A para enviar la delegación), de modo que el código
nuevo se limita al descubrimiento y a la decisión de a quién
delegar.

---

## 9. Inscripción en el registro REST y *heartbeat*

La factoría **no inscribe automáticamente** al agente en el
registro REST: la política de alta, *heartbeat* y baja es
responsabilidad del grupo. Esto es deliberado, porque depende de
qué hayas implementado en `descubrimiento/descubrimiento_a2a.py`
durante el Nivel 3.

El patrón canónico es enganchar el alta al `arrancar` del agente
y la baja al `detener`, sobrescribiendo los métodos de la
factoría con un `super()` al principio (o al final):

```python
class Bomberos(AgenteA2A):

    async def arrancar(self) -> None:
        await super().arrancar()
        if self.especificacion.visibilidad == "publico":
            await self._registrar_en_directorio()
            self._tarea_heartbeat = asyncio.create_task(self._latir())

    async def detener(self) -> None:
        if self.especificacion.visibilidad == "publico":
            self._tarea_heartbeat.cancel()
            await self._darse_de_baja()
        await super().detener()
```

Los métodos `_registrar_en_directorio`, `_latir` y
`_darse_de_baja` son las mismas funciones que ya tienes en
`descubrimiento/descubrimiento_a2a.py`; solo se llaman desde el
ciclo de vida del agente.

> **Identificador del agente en el registro.** Al procesar el alta,
> el registro REST asigna a cada agente el identificador
> `«{grupo}.{rol}»` (por ejemplo, `grupo1.bomberos`) y lo devuelve en
> el cuerpo de la respuesta. Ese identificador, **no** el `agente_id`
> interno del grupo, es el que debes usar en las rutas de la señal de
> vida (`POST /proyectos/{proyecto}/agentes/id/{id}/heartbeat`) y de la
> baja (`DELETE /proyectos/{proyecto}/agentes/id/{id}`), autenticadas
> con la cabecera `Authorization: Bearer <token>` (el mismo token que
> entregaste en el alta). Como el identificador se compone de grupo y
> rol, dos despliegues simultáneos del mismo grupo compartirían
> identificador y se solaparían en el registro; en el aula no ocurre
> porque cada grupo es único.

---

## 10. Mapeo Hito por Hito con la factoría

| Hito                | Objetivo (resumen del Nivel 3) | Diff que tienes que escribir tú |
|---------------------|--------------------------------|--------------------------------|
| **1**&nbsp;(nota&nbsp;5)  | Centralita arranca, publica Agent Card y responde `tasks/send`. | Una subclase de `AgenteA2A` que devuelve un `InformeResolucion` trivial desde `manejar_alerta`. Agent Card y servidor los pone la factoría. |
| **2**&nbsp;(nota&nbsp;6)  | Centralita descubre tarjetas y envía subtareas a especialistas. | Lectura del bloque `parametros.privados` del `agents.yaml` y un `ClienteA2A` para invocarlos. |
| **3**&nbsp;(nota&nbsp;7)  | Sistema completo: escenario de emergencia coordinado de principio a fin. | Mover la lógica completa de `manejar_alerta` (clasificar + distribuir + agregar) reutilizando el `LlmAgent` y los prompts del Nivel 2. |
| **4**&nbsp;(nota&nbsp;8)  | Contract Net y `input-required`. | Dos `registrar_handler` (`contract_net/cfp` y `contract_net/award`); sobrescribir `_procesar_tasks_get` si quieres exponer `input-required`. |
| **5**&nbsp;(nota&nbsp;9)  | Interoperabilidad cruzada vía registro central. | Reutilizar tu `descubrimiento/descubrimiento_a2a.py` desde la Centralita y delegar con `ClienteA2A`. |
| **6**&nbsp;(nota&nbsp;10) | Sistema robusto, SSE estable, perfil servidor. | Sobrescribir `_procesar_tasks_send_subscribe` para emitir SSE; pasar la serie completa de `tests/profesor/`. |

Cada hito es **acumulativo**: lo que funciona en el Hito 3 debe
seguir funcionando cuando llegues al Hito 5.

---

## 11. Procedimiento de adaptación, paso a paso

1. **Crear la rama de trabajo personal** sobre `examen-alumno`.
2. **Traer los módulos reutilizables** desde `desarrollo-nivel3`
   con `git checkout desarrollo-nivel3 -- <ruta>` (la receta
   completa está en
   [`PREPARACION_EXAMEN_ALUMNO.md`](PREPARACION_EXAMEN_ALUMNO.md) §3):

   ```bash
   git checkout desarrollo-nivel3 -- logica/
   git checkout desarrollo-nivel3 -- herramientas/
   git checkout desarrollo-nivel3 -- prompts/
   git checkout desarrollo-nivel3 -- ontologia/
   git checkout desarrollo-nivel3 -- descubrimiento/
   ```
3. **Crear los cinco módulos** de `agentes/` (uno por rol)
   siguiendo el esqueleto del §4 / §5.
4. **Copiar y ajustar** `config/agents.yaml.ejemplo` → `config/agents.yaml`
   con los puertos del grupo y los dos especialistas que serán
   públicos.
5. **Editar `config/config.yaml`** descomentando el bloque
   `evaluacion:` y dejando `red.perfil_activo: "local"` durante
   el desarrollo en casa.
6. **Arrancar** la pila Docker (ver [`MODO_DOCKER.md`](MODO_DOCKER.md))
   y el sistema:

   ```bash
   python main.py
   ```
7. **Probar contra la serie de validación del profesor** en otra
   terminal:

   ```bash
   pytest tests/profesor/integracion/ -v
   ```
8. **Iterar hito a hito**: no avanzar al siguiente hasta que los
   tests del actual estén en verde.

---

## 12. Errores frecuentes durante la adaptación

- **Heredar de `DefaultRequestHandler` de `a2a-sdk`** en lugar de
  `factoria.AgenteA2A`. Trampa muy común: el SDK de Google y la
  factoría de esta rama son **dos rutas alternativas para hablar
  A2A**; no componen entre sí. En esta rama, la única ruta
  soportada es la factoría. Diagnóstico completo en
  [`resolucion_a2a_porque_no_acepta_tareas.md`](resolucion_a2a_porque_no_acepta_tareas.md).
- **Modificar `factoria/agente_a2a.py`** para "adaptarla" a tu
  agente. La factoría se **extiende** (subclase, handlers,
  `construir_agent_card`), no se reescribe. Cualquier cambio en
  la forma del cuerpo de respuesta o en la Agent Card rompe el
  contrato externo y los tests del profesor dejan de aplicar.
- **Devolver un `dict` en lugar de un `InformeResolucion`** desde
  `manejar_alerta`. La factoría no infiere tipos: si el retorno
  no es una instancia validada del modelo del contrato, el
  coordinador la marcará como inválida.
- **Cargar las tarjetas JSON sueltas del Nivel 3** (`agent_cards/*.json`).
  Sobran: la factoría compone la Agent Card desde la
  `EspecificacionAgente`. Si quieres habilidades específicas,
  sobrescribe `construir_agent_card`.
- **Olvidar la inscripción en el registro REST.** Sin alta, los
  agentes públicos no son descubribles ni por el coordinador ni
  por otras Centralitas. Los escenarios de cooperación cruzada
  (Hitos 5-6) caen sistemáticamente.

---

## 13. Lectura complementaria

- [`PREPARACION_EXAMEN_ALUMNO.md`](PREPARACION_EXAMEN_ALUMNO.md)
  — Procedimiento general de incorporación selectiva desde
  `desarrollo-nivel3` (qué traer y qué no, cómo no fusionar
  ramas).
- [`ESCENARIOS_TESTS_OBLIGATORIOS.md`](ESCENARIOS_TESTS_OBLIGATORIOS.md)
  — Tests que el propio grupo debe escribir, organizados por
  hito.
- [`PRUEBAS_PREVIAS_AL_EXAMEN.md`](PRUEBAS_PREVIAS_AL_EXAMEN.md)
  — Cómo ejecutar la serie de validación del profesor en casa.
- [`MODO_DOCKER.md`](MODO_DOCKER.md) — Infraestructura local
  (registro REST + Ollama) sin la que el `main.py` no levanta.
- [`resolucion_a2a_porque_no_acepta_tareas.md`](resolucion_a2a_porque_no_acepta_tareas.md)
  — Depuración del extremo A2A cuando el agente acepta `curl`
  pero rechaza las tareas.

En la rama `desarrollo-nivel3` siguen siendo útiles, como
referencia conceptual, `doc/ARQUITECTURA.md` (§4.2 — composición
interna del agente A2A), `doc/PROTOCOLO_A2A.md` (ciclo de vida
de la `Task`, JSON-RPC) y `doc/HITOS_EVALUACION.md` (qué se
exige en cada hito).

---

*Sistemas Multiagente — Grado en Ingeniería Informática —
Universidad de Jaén — Curso 2025-2026*
