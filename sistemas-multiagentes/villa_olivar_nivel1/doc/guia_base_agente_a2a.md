# Guía de uso de `agentes/base_agente_a2a.py`

## Cómo construir los cinco agentes A2A del Nivel 3 sobre la clase base común

Esta guía describe cómo **derivar los cinco agentes** del sistema
Villa Olivar (Centralita, Bomberos, Sanitario, Policía y Servicios
Municipales) de la clase base `BaseAgenteA2A` de la rama
`desarrollo-nivel3`, de modo que **procesen correctamente las
tareas A2A** que les envía el supervisor del profesor y otras
Centralitas.

La clase base ya está completa: aporta el transporte HTTP y el
despacho del protocolo. El trabajo del grupo es **escribir las
cinco subclases**, una por agente. La guía también fija las
convenciones de nombres y firmas que hacen que, llegado el examen,
la adaptación al esqueleto alternativo `factoria.AgenteA2A` de la
rama `examen-alumno` sea **mecánica**: cambiar la clase base y poco
más. Ese camino corto está descrito en
[`doc/GUIA_FACTORIA_NIVEL3.md`](GUIA_FACTORIA_NIVEL3.md) de la rama
`examen-alumno`.

---

## 1. Papel de la clase base en la arquitectura

`BaseAgenteA2A` ocupa el lugar marcado en el §4.2 de
[`ARQUITECTURA.md`](ARQUITECTURA.md): la **composición de
transporte y despacho** común a los cinco agentes.

![Arquitectura interna de un agente del Nivel 3](img/arquitectura_nivel3_capas.svg)

La frontera de responsabilidades es estricta:

- `BaseAgenteA2A` cubre las **dos capas superiores** —Transporte y
  Despacho—: arranca el servidor HTTP, interpreta la envoltura
  JSON-RPC, encamina los métodos del protocolo, valida la entrada
  contra el contrato y compone la `Task` de respuesta.
- Cada **subclase concreta** aporta las **dos capas inferiores**
  —Razonamiento y Dominio—: construye su `LlmAgent` de ADK con sus
  `FunctionTool` y su instrucción de sistema, e implementa el
  método que resuelve la alerta.

Esta separación es la razón por la que la migración a la factoría
del examen es trivial: si el grupo respeta la frontera
(Transporte/Despacho en la base, Razonamiento/Dominio en la
subclase), basta sustituir la clase base para cambiar de
infraestructura sin tocar la lógica del agente.

> **Aviso importante sobre el transporte.** A diferencia de lo que
> se hizo en el Guión 9, la clase base **no usa la clase
> `A2AStarletteApplication` de `a2a-sdk`**. El motivo se explica en
> el §4.1 y es la causa de que el agente del Guión 9, tal cual, no
> aceptaría las tareas del supervisor del Nivel 3. La base monta el
> servidor con `aiohttp` y despacha el protocolo con código propio,
> igual que la factoría `factoria.AgenteA2A` del examen.

---

## 2. Qué te da la base y qué escribes tú

### 2.1. Lo que la base ya resuelve (no hay que tocarlo)

La clase `BaseAgenteA2A` se ocupa, sin que el grupo escriba nada,
de:

- Arrancar un servidor `aiohttp` en el `host:puerto` declarado en
  `agents.yaml` y apagarlo ordenadamente.
- Publicar la tarjeta de agente (Agent Card) en
  `GET /.well-known/agent.json`.
- Atender `POST /` y **despachar** entre `tasks/send`,
  `tasks/get`, `tasks/sendSubscribe` y los manejadores adicionales
  que registre la subclase.
- Interpretar la envoltura JSON-RPC y devolver los códigos de
  error `-32700`, `-32600` y `-32601` cuando proceda.
- Localizar la `AlertaEmergencia` en la `Part` de datos del
  mensaje y **validarla** contra
  `contrato.alerta_emergencia.AlertaEmergencia`.
- Invocar `manejar_alerta(alerta)` con la alerta ya validada.
- Envolver el `InformeResolucion` devuelto en una `Task` con
  estado `completed` y su artefacto de datos.
- Traducir **cualquier excepción no controlada** de la subclase a
  una `Task` con estado `failed` y un mensaje descriptivo.

### 2.2. Lo que aporta cada subclase

Cada agente concreto (Centralita, Bomberos, …) escribe:

1. Su `__init__`, que invoca al de la base con
   `super().__init__(especificacion)` y construye el `LlmAgent`
   específico del rol (sus `FunctionTool` y su prompt).
2. El método
   `async def manejar_alerta(self, alerta: AlertaEmergencia) -> InformeResolucion`,
   que es **el único punto de entrada funcional** del agente.
3. Opcionalmente, una sobreescritura de `construir_agent_card`
   para enriquecer las habilidades publicadas.
4. Opcionalmente, manejadores para métodos JSON-RPC ajenos al
   núcleo A2A (Contract Net, Hito 4 — véase §8).
5. Opcionalmente, una sobreescritura de `arrancar` / `detener`
   para inscribirse en el registro REST si el agente es público
   (§9).

Todo lo demás (servidor, despacho, traducción de la `Task`,
respuesta JSON-RPC) lo pone la base.

---

## 3. Convenciones que preservan la migración futura

La rama `examen-alumno` impone unos nombres y firmas en su
factoría. Si tus subclases los respetan, **el día del examen solo
cambiarás la línea de la clase base**. Las convenciones
obligatorias son:

| Pieza                            | Convención obligatoria                                                           |
|----------------------------------|----------------------------------------------------------------------------------|
| Clase base                       | `BaseAgenteA2A` (esta rama) o `factoria.AgenteA2A` (rama del examen)            |
| Método de entrada del agente     | `async def manejar_alerta(self, alerta: AlertaEmergencia) -> InformeResolucion` |
| Tipo de la entrada               | Instancia validada de `contrato.alerta_emergencia.AlertaEmergencia`             |
| Tipo de la salida                | Instancia validada de `contrato.informe_resolucion.InformeResolucion`          |
| Configuración por agente         | Se inyecta como `EspecificacionAgente` leída de `agents.yaml`                   |
| Registro de manejadores extra    | `self.registrar_handler("contract_net/cfp", self._handler_cfp)`                 |
| Composición de la Agent Card     | `def construir_agent_card(self) -> AgentCard` (la subclase la sobrescribe)      |
| Ciclo de vida                    | `async def arrancar(self)` y `async def detener(self)`, con `await super().…`   |

> **Importante.** Dentro de la subclase, **nunca devuelvas un
> `dict`** desde `manejar_alerta`: devuelve una instancia del
> modelo Pydantic `InformeResolucion`. La validación impide que un
> campo mal escrito viaje al supervisor y se contabilice como
> tarea inválida.

`BaseAgenteA2A` y `factoria.AgenteA2A` ofrecen a la subclase
**exactamente la misma interfaz** (`manejar_alerta`,
`construir_agent_card`, `registrar_handler`, `arrancar`,
`detener`, atributo `especificacion`). Esa es la garantía de que
el cuerpo de tus cinco agentes no cambia al migrar.

---

## 4. La arquitectura del transporte: aiohttp y despacho propio

Aunque la subclase no necesita tocar el transporte, conviene
comprenderlo: es lo que distingue a este proyecto del Guión 9 y la
causa de la duda más frecuente del Nivel 3.

### 4.1. Por qué la base no usa `A2AStarletteApplication`

El protocolo A2A ha tenido dos generaciones de nombres de método
para una misma operación —enviar una tarea a un agente—:

| Generación del protocolo | Enviar una tarea | Enviar con transmisión continua (*streaming*) |
|--------------------------|------------------|-----------------------------------------------|
| A2A inicial (heredada)   | `tasks/send`     | `tasks/sendSubscribe`                         |
| A2A vigente              | `message/send`   | `message/stream`                              |

El **supervisor del profesor** y el contrato del Nivel 3
([`contrato_supervisor_nivel3.md`](contrato_supervisor_nivel3.md)
§3 y §5) emplean la generación heredada: envían `tasks/send`. En
cambio, la clase `A2AStarletteApplication` de `a2a-sdk` 0.3.x
—la que se usó en el Guión 9— implementa la generación vigente y
**solo reconoce `message/send`**.

La consecuencia es decisiva. `A2AStarletteApplication` examina el
campo `method` de la envoltura JSON-RPC y, si no lo encuentra en
su tabla interna, responde con el error `-32601` («método no
encontrado») **antes de invocar ningún manejador**. Es decir: un
agente montado sobre `A2AStarletteApplication` rechazaría todas
las tareas del supervisor, por muy bien escrito que estuviese el
resto del código. Personalizar el manejador no lo arregla: el
rechazo ocurre una capa más arriba.

Por eso `BaseAgenteA2A` **construye el servidor con `aiohttp` y
despacha el protocolo con código propio**. Es la misma decisión
que toma la factoría `factoria.AgenteA2A` del examen. El catálogo
de causas por las que un agente «no acepta tareas» está en
[`doc/resolucion_a2a_porque_no_acepta_tareas.md`](resolucion_a2a_porque_no_acepta_tareas.md)
de la rama `examen-alumno`.

### 4.2. Las dos rutas del agente

El método `_construir_aplicacion` de la base declara una
`web.Application` de `aiohttp` con exactamente dos rutas:

- `GET /.well-known/agent.json` → sirve la tarjeta de agente.
- `POST /` → extremo (*endpoint*) JSON-RPC del protocolo A2A.

El extremo JSON-RPC es la raíz (`/`). La tarjeta de agente
publica esa misma URL en su campo `url`, de modo que cualquier
cliente que descubra al agente sepa adónde enviar las tareas.

### 4.3. El despacho de métodos JSON-RPC

El corazón del transporte es `_manejar_post_jsonrpc`. Su trabajo
es el que en el Guión 9 hacía `A2AStarletteApplication`:

1. Interpreta el cuerpo de la petición como JSON. Si no es JSON
   válido → error `-32700`.
2. Lee el campo `method`. Si falta → error `-32600`.
3. Encamina el método hacia su procesador:
   - `tasks/send` → `_procesar_tasks_send`.
   - `tasks/get` → `_procesar_tasks_get`.
   - `tasks/sendSubscribe` → `_procesar_tasks_send_subscribe`.
   - un método registrado con `registrar_handler` → su manejador.
   - cualquier otro → error `-32601`.

Los **códigos de error normalizados** de JSON-RPC 2.0 que el
agente puede devolver son:

| Código   | Significado            | Cuándo lo emite la base                                  |
|----------|------------------------|----------------------------------------------------------|
| `-32700` | JSON mal formado       | El cuerpo de la petición no es JSON válido               |
| `-32600` | Petición inválida      | Falta el campo `method` en la envoltura                  |
| `-32601` | Método no encontrado   | El `method` no es ninguno de los reconocidos             |
| `-32000` | Error del servidor     | Excepción no controlada de un manejador registrado       |

Un `tasks/send` que llega bien pero cuya alerta no valida, o cuyo
`manejar_alerta` lanza una excepción, **no produce un objeto
`error`**: produce una `Task` con estado `failed` dentro de
`result` (la petición se atendió; lo que falló es la tarea).

### 4.4. El viaje de un `tasks/send` hasta `manejar_alerta`

Este es el recorrido completo del mensaje del supervisor, que la
base implementa íntegramente:

1. El supervisor envía `POST /` con la envoltura JSON-RPC
   (`method: "tasks/send"`, `params.message.parts[0].type:
   "data"`).
2. `_manejar_post_jsonrpc` valida la envoltura y encamina el
   método hacia `_procesar_tasks_send`.
3. `_extraer_datos_alerta` localiza la `Part` de tipo `data` del
   mensaje y devuelve su contenido.
4. La base valida ese contenido contra `AlertaEmergencia`. Si no
   valida → `Task` con estado `failed`.
5. La base invoca `await self.manejar_alerta(alerta)`.
6. La respuesta se empaqueta:
   - Éxito → `Task` con `status: completed` y un artefacto de
     datos con el `InformeResolucion` serializado.
   - Excepción no controlada → `Task` con `status: failed` y el
     mensaje de la excepción.
7. El supervisor recibe la `Task` final como respuesta JSON-RPC.

Lo único que la subclase aporta a este flujo es el **paso 5**;
todo lo demás vive en la base.

### 4.5. La tarjeta de agente por código

La tarjeta de agente **no se mantiene como un fichero JSON
suelto**. El método `construir_agent_card` de la base la compone
en código a partir de la `EspecificacionAgente`, de modo que
cambiar el host o el puerto en `agents.yaml` baste sin tocar nada
más. La implementación por defecto publica una habilidad mínima;
una subclase la sobrescribe para declarar las habilidades reales
de su rol (§6).

---

## 5. Adaptación desde el Guión 9

El Guión 9 (`Lecturas/nivel 3/guion9-a2a-adk-ollama`) construyó un
agente A2A + ADK + Ollama completo y en funcionamiento. El Nivel 3
**reutiliza casi todo lo que allí se aprendió**; lo que cambia es
solo la envoltura de transporte. Esta sección hace explícita la
correspondencia para que el grupo entienda qué adapta y qué
conserva.

### 5.1. Correspondencia pieza a pieza

| En el Guión 9                                                        | En este proyecto (Nivel 3)                                                |
|----------------------------------------------------------------------|---------------------------------------------------------------------------|
| `construir_aplicacion()` ensambla `A2AStarletteApplication` + `DefaultRequestHandler` (`src/agente_inteligente/a2a_server.py`) | `BaseAgenteA2A` monta el servidor con `aiohttp` y despacho propio; ya está hecho |
| Método JSON-RPC `message/send`                                       | Método JSON-RPC `tasks/send`                                              |
| `AgenteInteligenteExecutor(AgentExecutor)` con `execute()` y `cancel()` (`src/agente_inteligente/executor.py`) | `manejar_alerta(alerta)` en cada subclase                                 |
| `execute()` extrae el texto de `context.message.parts` (un `TextPart`) | La base extrae la `AlertaEmergencia` de la `Part` de datos                |
| `event_queue.enqueue_event(mensaje)` para devolver la respuesta      | `return InformeResolucion(...)` desde `manejar_alerta`                    |
| `crear_agent_card()` (`src/agente_inteligente/agent_card.py`)        | `construir_agent_card()` en la base, sobrescribible por la subclase        |
| `Runner` de ADK, `LlmAgent`, `InMemorySessionService`               | **Se conservan intactos**, dentro de `manejar_alerta`                     |

### 5.2. Lo que cambia y lo que NO cambia

**Cambia** solo la capa de transporte:

- En el Guión 9, ensamblabas el servidor con `a2a-sdk`. Aquí el
  servidor ya viene montado en `BaseAgenteA2A`; no escribes
  `A2AStarletteApplication` ni `DefaultRequestHandler` ni
  `AgentExecutor` ni arrancas `uvicorn`.
- En el Guión 9, el cliente hablaba `message/send`. El supervisor
  del Nivel 3 habla `tasks/send`; la base ya lo despacha.

**No cambia** la capa de razonamiento:

- El `LlmAgent` de ADK, sus `FunctionTool`, la instrucción de
  sistema y el `Runner` que recorre los eventos del modelo son
  **el mismo código** que escribiste en el Guión 9 y en el
  Nivel 2. Ese código se traslada, sin modificar, al interior de
  `manejar_alerta`.

En resumen: del Guión 9 **se tira el andamiaje de `a2a-sdk` y se
conserva todo el razonamiento de ADK**. La adaptación consiste en
mover la llamada al `Runner` de ADK desde el `execute()` del
`AgentExecutor` hasta el `manejar_alerta` de la subclase.

---

## 6. Crear un especialista — ejemplo Bomberos

Con la base ya operativa, **cada especialista cabe en una clase
corta**. El agente concreto no toca el servidor ni el despacho:
solo aporta su `LlmAgent` y su `manejar_alerta`.

```python
# agentes/agente_bomberos.py
from agentes.base_agente_a2a import BaseAgenteA2A, EspecificacionAgente
from contrato.alerta_emergencia import AlertaEmergencia
from contrato.informe_actuacion import InformeActuacion
from contrato.informe_resolucion import InformeResolucion

from google.adk.agents import LlmAgent
from herramientas.herramientas_bomberos import herramientas_bomberos


class AgenteBomberos(BaseAgenteA2A):
    """Especialista de extinción y rescate."""

    def __init__(self, especificacion: EspecificacionAgente) -> None:
        # La base prepara el transporte.
        super().__init__(especificacion)
        # La subclase prepara el razonamiento. Este LlmAgent es,
        # salvo el rol, el mismo que se montó en el Guión 9.
        self._llm = LlmAgent(
            name="bomberos_villa_olivar",
            instruction=self._leer_prompt("bomberos"),
            tools=herramientas_bomberos(),
            model=self._configurar_modelo(),
        )

    async def manejar_alerta(
        self,
        alerta: AlertaEmergencia,
    ) -> InformeResolucion:
        # 1. El LlmAgent decide la actuación a partir de la alerta
        #    y de sus FunctionTool. La invocación al Runner de ADK
        #    es la misma que se aprendió en el Guión 9.
        actuacion: InformeActuacion = await self._razonar(alerta)
        # 2. Devolver SIEMPRE un InformeResolucion validado: nunca
        #    un dict. Si la salida del LLM no es conforme, Pydantic
        #    lo detecta aquí y la base lo traducirá a `failed`.
        return InformeResolucion(
            id_emergencia=alerta.id_emergencia,
            estado_final="resuelta",
            informes_especialistas=[actuacion],
        )
```

Observaciones para que la migración al examen sea trivial:

- **No hay** `if __name__ == "__main__":` ni `uvicorn.run(...)` ni
  `A2AStarletteApplication` en esta clase. El arranque lo orquesta
  `main.py` a partir de `agents.yaml`.
- La capa de razonamiento (`_razonar`, `_configurar_modelo`,
  `_leer_prompt`) es **código propio del grupo, reutilizado del
  Nivel 2 y del Guión 9**. No pertenece a la base de transporte;
  vive en la subclase o en un módulo auxiliar que la subclase
  importe. Para el detalle de cómo se invoca el `Runner` de ADK,
  consulta `src/agente_inteligente/executor.py` del Guión 9.
- La salida es **una instancia** de `InformeResolucion`, no un
  `dict`. Devolver un diccionario «que parece» un informe es la
  primera causa de fallos en los tests del profesor.

---

## 7. Crear la Centralita — orquestación de especialistas

La Centralita es **ligeramente distinta**: su `manejar_alerta` no
resuelve la emergencia por sí sola; clasifica la alerta y reparte
subtareas entre los especialistas correspondientes (propios y, en
los Hitos 5-6, de otros grupos).

```python
# agentes/agente_centralita.py
from agentes.base_agente_a2a import BaseAgenteA2A, EspecificacionAgente
from contrato.alerta_emergencia import AlertaEmergencia
from contrato.informe_resolucion import InformeResolucion
from cliente_pruebas.cliente_a2a import ClienteA2A


class AgenteCentralita(BaseAgenteA2A):
    """Coordinador del grupo: recibe alertas y distribuye subtareas."""

    def __init__(self, especificacion: EspecificacionAgente) -> None:
        super().__init__(especificacion)
        # Las URL de los especialistas privados se declaran en el
        # bloque `parametros` del agente en agents.yaml, de modo
        # que cambiar de perfil de red no obligue a tocar código.
        self._privados: dict[str, str] = especificacion.parametros.get(
            "privados", {},
        )
        self._clasificador = self._construir_clasificador()

    async def manejar_alerta(
        self,
        alerta: AlertaEmergencia,
    ) -> InformeResolucion:
        # 1. Clasificar con el LlmAgent (mismo código del Nivel 2).
        especialistas = await self._clasificar(alerta)

        # 2. Convocar a cada especialista por A2A. ClienteA2A envía
        #    un `tasks/send` a la URL del especialista: es el mismo
        #    protocolo que el supervisor usa contra esta Centralita.
        informes = []
        for rol in especialistas:
            url = self._url_para_rol(rol)
            async with ClienteA2A(url_base=url) as cliente:
                respuesta = await cliente.enviar_tarea(alerta=alerta)
                informes.append(respuesta.informe_actuacion)

        # 3. Agregar y devolver el InformeResolucion único.
        return InformeResolucion(
            id_emergencia=alerta.id_emergencia,
            estado_final="resuelta",
            informes_especialistas=informes,
        )

    def _url_para_rol(self, rol: str) -> str:
        # Privados: URL inyectada por agents.yaml. Públicos del
        # grupo o de otros grupos: descubrir en el registro REST.
        url = self._privados.get(rol, "")
        if not url:
            url = self._descubrir_publico(rol)
        return url
```

El bloque correspondiente en `agents.yaml` declara las URL
privadas en `parametros`:

```yaml
agentes:
  - identificador: "centralita"
    rol: "centralita"
    visibilidad: "publico"
    modulo: "agentes.agente_centralita"
    clase: "AgenteCentralita"
    host: "0.0.0.0"
    puerto: 8110
    activo: true
    parametros:
      privados:
        policia:   "http://localhost:8140"
        municipal: "http://localhost:8150"
```

---

## 8. Métodos JSON-RPC extra: Contract Net (Hito 4)

Contract Net añade `contract_net/cfp` (*Call For Proposal*) y
`contract_net/award` (adjudicación). En lugar de modificar el
despacho de la base, se usa el **registro de manejadores** que la
base ofrece. Una subclase registra sus manejadores en el
`__init__`:

```python
class AgenteBomberos(BaseAgenteA2A):

    def __init__(self, especificacion: EspecificacionAgente) -> None:
        super().__init__(especificacion)
        # ... construcción del LlmAgent ...
        self.registrar_handler("contract_net/cfp", self._handler_cfp)
        self.registrar_handler("contract_net/award", self._handler_award)

    async def _handler_cfp(self, params: dict) -> dict:
        propuesta = await self._evaluar_cfp(params)
        return {"propuesta": propuesta.model_dump()}

    async def _handler_award(self, params: dict) -> dict:
        await self._aceptar_award(params)
        return {"aceptado": True}
```

La base se encarga de interpretar el JSON-RPC, extraer `params`,
invocar al manejador, envolver el `result` en la respuesta y
traducir cualquier excepción del manejador a un error `-32000`.
Esta misma firma (`registrar_handler(metodo, manejador)`) es la
que expone la factoría del examen: los manejadores de Contract Net
se migran sin cambios.

---

## 9. Ciclo de vida: inscripción REST y señal de vida

Los métodos `arrancar` y `detener` de la base ejecutan el ciclo
HTTP (levantar y apagar el servidor `aiohttp`). La inscripción de
un agente público en el registro REST de Villa Olivar **no es
automática**: se incorpora sobrescribiendo estos métodos en la
subclase, con la regla del `super()` al principio (alta tras
arrancar el HTTP) y al final (baja tras parar el HTTP):

```python
class AgenteCentralita(BaseAgenteA2A):

    async def arrancar(self) -> None:
        await super().arrancar()
        if self.especificacion.visibilidad == "publico":
            await self._registrar_en_directorio()
            self._tarea_latido = asyncio.create_task(self._latir())

    async def detener(self) -> None:
        if self.especificacion.visibilidad == "publico":
            self._tarea_latido.cancel()
            await self._darse_de_baja()
        await super().detener()
```

Los métodos `_registrar_en_directorio`, `_latir` (la *señal de
vida*, en inglés *heartbeat*) y `_darse_de_baja` se apoyan en el
cliente del registro de [`descubrimiento/`](../descubrimiento) y
encapsulan las peticiones REST descritas en
[`registro_rest_para_clientes.md`](registro_rest_para_clientes.md).

---

## 10. Streaming SSE (Hito 6)

El método `tasks/sendSubscribe` exige una respuesta **Server-Sent
Events (SSE)** con eventos parciales de progreso y un evento
final. La base deja `_procesar_tasks_send_subscribe` como **punto
de extensión**: por defecto responde `-32601`. El grupo que aspire
al Hito 6 sobrescribe ese método en su subclase para emitir SSE
(las cabeceras están en la constante `CABECERAS_SSE` de la base).

La subclase sigue exponiendo **el mismo** `manejar_alerta`: el
contrato no cambia. El día del examen, el supervisor decide si
invoca `tasks/send` o `tasks/sendSubscribe`, y el agente responde
igual de bien con el mismo cuerpo de método de dominio.

---

## 11. Convenciones que garantizan la migración trivial al examen

Resumen accionable. Si tus cinco subclases cumplen estos siete
puntos, **la rama del examen solo te pedirá cambiar la clase
base**:

1. La subclase **deriva de `BaseAgenteA2A`** (esta rama) o de
   `factoria.AgenteA2A` (rama del examen). El resto del cuerpo es
   idéntico.
2. El método de entrada se llama **siempre**
   `async def manejar_alerta(self, alerta: AlertaEmergencia) -> InformeResolucion`.
3. La entrada es una instancia validada de `AlertaEmergencia` y la
   salida una instancia validada de `InformeResolucion`. **Nunca**
   un `dict`.
4. El `__init__` recibe una `EspecificacionAgente` y llama a
   `super().__init__(especificacion)` antes de construir su
   `LlmAgent`.
5. Los métodos JSON-RPC extra (Contract Net) se registran con
   `self.registrar_handler(metodo, manejador)` desde el `__init__`.
6. El ciclo de vida usa `arrancar` / `detener` con `super()` y
   condiciona la inscripción REST a
   `self.especificacion.visibilidad == "publico"`.
7. El arranque del agente está en `main.py` a partir de
   `agents.yaml`. **Ningún** módulo de `agentes/` contiene
   `if __name__ == "__main__":`, `uvicorn.run(...)` ni
   `A2AStarletteApplication`.

---

## 12. Errores frecuentes

- **Reintroducir `A2AStarletteApplication`.** Si una subclase
  vuelve a montar el servidor con `a2a-sdk` «como en el Guión 9»,
  el agente dejará de reconocer `tasks/send` y rechazará todas las
  tareas del supervisor con `-32601`. El transporte ya lo pone la
  base; la subclase no monta servidores.
- **Devolver un `dict` desde `manejar_alerta`.** La validación
  Pydantic es lo único que separa al agente de generar un
  `InformeResolucion` malformado. Si devuelves un `dict`, el
  supervisor lo marcará como tarea inválida.
- **Construir la Agent Card cargando un JSON suelto.** Cualquier
  cambio en `agents.yaml` (puerto, host, descripción) obligaría a
  editar también el JSON, y la `url` de la tarjeta acabaría
  difiriendo de la registrada. Sobrescribe `construir_agent_card`
  y compón la tarjeta en código.
- **Arrancar `uvicorn` dentro del módulo del agente.** Invalida
  la orquestación de `main.py` e impide cambiar la clase base por
  la del examen sin reescribir el agente.
- **Omitir la inscripción REST en agentes públicos.** Si la
  sobreescritura de `arrancar` prescinde de
  `_registrar_en_directorio`, el supervisor no descubre al agente
  y los Hitos 5-6 fallan sistemáticamente.
- **Construir el `LlmAgent` en la base.** El razonamiento es
  responsabilidad de la subclase. Si lo metes en `BaseAgenteA2A`,
  rompes la simetría con la factoría del examen y la migración
  deja de ser mecánica.

---

## 13. Lectura complementaria

- [`AGENTES_A2A.md`](AGENTES_A2A.md) — Fichas funcionales de los
  cinco agentes (responsabilidades, herramientas, instrucciones,
  flujos).
- [`ARQUITECTURA.md`](ARQUITECTURA.md) — Composición por capas
  (§4.2), perfiles de modelo de lenguaje (§5.3) y modelo de
  despliegue.
- [`PROTOCOLO_A2A.md`](PROTOCOLO_A2A.md) — Ciclo de vida de la
  `Task`, operaciones JSON-RPC, Agent Card y SSE.
- [`contrato_supervisor_nivel3.md`](contrato_supervisor_nivel3.md)
  — Modelos Pydantic vinculantes (`AlertaEmergencia`,
  `InformeResolucion`, `InformeActuacion`, `AgentCard`).
- [`registro_rest_para_clientes.md`](registro_rest_para_clientes.md)
  — Extremos del registro REST, *autotoken* y perfiles
  `local` / `servidor`.
- [`HITOS_EVALUACION.md`](HITOS_EVALUACION.md) — Criterios
  observables por hito.
- **Guión 9** (`Lecturas/nivel 3/guion9-a2a-adk-ollama`) — La
  implementación de referencia del agente A2A + ADK: el ensamblaje
  con `a2a-sdk` (`src/agente_inteligente/a2a_server.py`), el
  ejecutor (`src/agente_inteligente/executor.py`) y la nota de
  versión del SDK (`docs/version_a2a_sdk.md`). Su capa de
  razonamiento de ADK se reutiliza intacta en el Nivel 3 (§5).

En la rama `examen-alumno`, la guía complementaria es
[`GUIA_FACTORIA_NIVEL3.md`](GUIA_FACTORIA_NIVEL3.md): describe
cómo el mismo agente, escrito según las convenciones de esta guía,
se migra al esqueleto `factoria.AgenteA2A` con el cambio de una
sola línea por agente.

---

*Sistemas Multiagente — Grado en Ingeniería Informática —
Universidad de Jaén — Curso 2025-2026*
