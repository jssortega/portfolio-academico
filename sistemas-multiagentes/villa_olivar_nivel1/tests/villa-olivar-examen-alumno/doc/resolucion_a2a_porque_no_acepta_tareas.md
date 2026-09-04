# El agente acepta peticiones `curl` pero no acepta tareas A2A

## 1. Diagnóstico inicial

"Acepta peticiones `curl` pero no acepta tareas" casi siempre
significa lo mismo:

- El agente publica su **Agent Card** en `/.well-known/agent.json` y
  el `curl` que lo descarga responde con `200 OK`.
- El método **`tasks/send`** del protocolo A2A —el que arranca una
  tarea— **no está bien implementado** o **el cliente no lo está
  invocando como exige el protocolo**.

Antes de entrar en causas concretas, conviene recordar que A2A es
JSON-RPC 2.0 sobre HTTP. Cualquier petición que arranque una tarea
debe llevar la envoltura JSON-RPC completa, no solo el cuerpo del
dominio (la `AlertaEmergencia`, en nuestro caso).

## 2. El cuerpo mínimo de una petición correcta

Esta es la plantilla que tiene que enviarse al endpoint A2A del
agente:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tasks/send",
  "params": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "sessionId": "9e0c0f5a-5b8b-4f3c-a3b2-3a8d2b7e9c11",
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "data",
          "data": {
            "id_emergencia": "e-001",
            "tipo_emergencia": "INCENDIO",
            "prioridad": "ALTA",
            "ubicacion": {
              "direccion": "Calle del Olivar, 14"
            },
            "descripcion": "Humo denso en la planta baja."
          }
        }
      ]
    }
  }
}
```

El `curl` equivalente:

```bash
curl -v -X POST http://localhost:9001/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tasks/send",
    "params": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "sessionId": "9e0c0f5a-5b8b-4f3c-a3b2-3a8d2b7e9c11",
      "message": {
        "role": "user",
        "parts": [
          {
            "type": "data",
            "data": {
              "id_emergencia": "e-001",
              "tipo_emergencia": "INCENDIO",
              "prioridad": "ALTA",
              "ubicacion": { "direccion": "Calle del Olivar, 14" },
              "descripcion": "Humo denso en la planta baja."
            }
          }
        ]
      }
    }
  }'
```

Si el agente responde con `200 OK` y un JSON-RPC del tipo
`{"jsonrpc":"2.0","id":1,"result":{...task...}}`, la tarea se aceptó.
Si responde con un objeto `error`, el campo `error.code` ya identifica
la causa (tabla de la sección 5 de esta guía).

### 2.1. Ejemplo de respuesta correcta

Cuando el agente acepta la tarea y la procesa hasta el final, la
respuesta sigue la forma canónica de JSON-RPC: la envoltura es la
misma de la petición (`jsonrpc`, `id`) y el campo `result` contiene
el objeto Task con su estado final y los artefactos producidos.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "sessionId": "9e0c0f5a-5b8b-4f3c-a3b2-3a8d2b7e9c11",
    "status": {
      "state": "completed",
      "timestamp": "2026-05-17T22:41:08+02:00"
    },
    "history": [
      {
        "role": "user",
        "parts": [
          {
            "type": "data",
            "data": {
              "id_emergencia": "e-001",
              "tipo_emergencia": "INCENDIO",
              "prioridad": "ALTA",
              "ubicacion": { "direccion": "Calle del Olivar, 14" },
              "descripcion": "Humo denso en la planta baja."
            }
          }
        ]
      }
    ],
    "artifacts": [
      {
        "name": "informe_resolucion",
        "parts": [
          {
            "type": "data",
            "data": {
              "id_emergencia": "e-001",
              "estado_final": "RESUELTA",
              "traza": [
                {
                  "rol": "bomberos",
                  "accion": "desplegar_camion",
                  "detalle": "Camión 12 enviado a Calle del Olivar",
                  "visibilidad": "publico"
                },
                {
                  "rol": "bomberos",
                  "accion": "informe_final",
                  "detalle": "Foco controlado, sin víctimas.",
                  "visibilidad": "publico"
                }
              ]
            }
          }
        ]
      }
    ]
  }
}
```

Tres elementos a comprobar en una respuesta correcta:

- **`result.id` y `result.sessionId`** coinciden con los enviados en
  la petición. Si el agente devuelve otros identificadores, está
  ignorando los del cliente y eso suele complicar el seguimiento
  posterior con `tasks/get`.
- **`result.status.state`** toma uno de los valores del ciclo de vida
  A2A: `submitted`, `working`, `input-required`, `completed`,
  `canceled` o `failed`. Una tarea sin estado o con un valor fuera de
  esa lista es una señal de implementación incompleta en el agente.
- **`result.artifacts`** contiene los productos de la tarea. En el
  ejemplo, el `InformeResolucion` viaja como `part` de tipo `data`
  dentro de un artefacto llamado `informe_resolucion`. Si el agente
  procesa la tarea pero no devuelve artefactos, el cliente no tiene
  nada útil que mostrar.

Para tareas largas el campo `result.status.state` será `working` (o
`submitted`) en la respuesta inicial y la resolución llegará después
por `tasks/get` o por `tasks/sendSubscribe` (streaming con SSE). Eso
es una conversación de varias peticiones, no un problema.

## 3. Caso concreto: enviar una alerta a la Centralita

El protocolo A2A se ve mejor sobre el caso real de la práctica del
Nivel 3. La **Centralita** de un grupo de Villa Olivar es el agente
público al que el supervisor del profesor envía las
``AlertaEmergencia``: la recibe, decide qué especialistas tienen que
intervenir (bomberos, sanitario, policía, municipal) y devuelve un
``InformeResolucion`` cuando la emergencia termina.

Veamos los tres pasos que recorre el supervisor del profesor (o el
``curl`` de un alumno durante una prueba manual) para que la
Centralita acepte la tarea.

### 3.1. Paso 1: descubrir la Centralita por su Agent Card

El registro REST del aula publica un descriptor con la URL del agente
``centralita`` de cada grupo. Llegados ahí, el cliente lee la Agent
Card del agente:

```bash
curl -s http://localhost:9000/.well-known/agent.json | jq .
```

Respuesta típica:

```json
{
  "name": "centralita_fenix",
  "description": "Centralita 112 del grupo Fénix",
  "version": "0.1.0",
  "url": "http://localhost:9000/",
  "defaultInputModes": ["application/json"],
  "defaultOutputModes": ["application/json"],
  "capabilities": { "streaming": true },
  "skills": [
    {
      "id": "resolver_emergencia",
      "name": "Resolver emergencia",
      "description": "Coordina la resolución de una alerta del 112",
      "tags": ["emergencias", "coordinacion"],
      "inputModes": ["application/json"],
      "outputModes": ["application/json"]
    }
  ]
}
```

El campo decisivo es ``url``: es el endpoint al que se enviará el
``tasks/send``. En el ejemplo, ``http://localhost:9000/``.

### 3.2. Paso 2: enviar la `AlertaEmergencia` con `tasks/send`

La envoltura JSON-RPC es la misma que vimos en la sección 2; lo que
varía es el cuerpo del dominio dentro de ``params.message.parts[0].data``,
que ahora es exactamente la ``AlertaEmergencia`` validada por Pydantic
en el paquete ``contrato/`` del proyecto:

```bash
curl -v -X POST http://localhost:9000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 42,
    "method": "tasks/send",
    "params": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "sessionId": "9e0c0f5a-5b8b-4f3c-a3b2-3a8d2b7e9c11",
      "message": {
        "role": "user",
        "parts": [
          {
            "type": "data",
            "data": {
              "id_emergencia": "e-fenix-001",
              "tipo_emergencia": "INCENDIO",
              "prioridad": "ALTA",
              "ubicacion": {
                "direccion": "Calle del Olivar, 14, Villa Olivar"
              },
              "descripcion": "Humo denso en la planta baja y posible víctima atrapada en el primer piso."
            }
          }
        ]
      }
    }
  }'
```

Tres detalles que distinguen este caso del genérico:

- **``id_emergencia``** es el identificador de la emergencia en el
  dominio del proyecto. No debe confundirse con ``params.id``
  (identificador A2A de la tarea) ni con ``sessionId``
  (identificador de la sesión A2A). Los tres viajan en la misma
  petición y cumplen funciones distintas.
- **``ubicacion``** es un objeto con ``direccion`` obligatoria y
  ``coordenadas`` opcional (``{lat, lon}``). Pasarla como cadena
  desnuda (``"Calle del Olivar, 14"``) provoca el error de
  validación de la causa 4.6.
- **``tipo_emergencia``** y **``prioridad``** son enumerados en
  mayúsculas (``INCENDIO``, ``ALTA``); cualquier otra escritura
  dispara la causa 4.6.

### 3.3. Paso 3: leer el `InformeResolucion` que devuelve

Si la Centralita acepta y resuelve la tarea, la respuesta lleva el
``InformeResolucion`` como artefacto:

```json
{
  "jsonrpc": "2.0",
  "id": 42,
  "result": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "sessionId": "9e0c0f5a-5b8b-4f3c-a3b2-3a8d2b7e9c11",
    "status": {
      "state": "completed",
      "timestamp": "2026-05-17T22:48:13+02:00"
    },
    "artifacts": [
      {
        "name": "informe_resolucion",
        "parts": [
          {
            "type": "data",
            "data": {
              "id_emergencia": "e-fenix-001",
              "estado_final": "RESUELTA",
              "traza": [
                {
                  "rol": "centralita",
                  "accion": "clasificar_alerta",
                  "detalle": "Incendio con víctima → bomberos + sanitario",
                  "visibilidad": "publico"
                },
                {
                  "rol": "bomberos",
                  "accion": "desplegar_camion",
                  "detalle": "Camión 12 enviado a Calle del Olivar, 14",
                  "visibilidad": "publico"
                },
                {
                  "rol": "sanitario",
                  "accion": "rescate_victima",
                  "detalle": "Víctima evacuada al hospital provincial",
                  "visibilidad": "publico"
                },
                {
                  "rol": "centralita",
                  "accion": "informe_final",
                  "detalle": "Foco controlado, víctima estable.",
                  "visibilidad": "publico"
                }
              ]
            }
          }
        ]
      }
    ]
  }
}
```

Notas sobre la respuesta de la Centralita:

- **La traza incluye al menos un evento de la propia centralita**
  (``clasificar_alerta`` o equivalente) y los eventos de cada
  especialista que ha intervenido. Una traza solo con eventos de la
  Centralita es un síntoma de que la coordinación con los
  especialistas no se ha producido.
- **``estado_final``** ha de ser uno de los valores aceptados por
  el contrato (``RESUELTA``, ``RESUELTA_PARCIAL``, ``NO_RESUELTA``).
  El supervisor del profesor descarta como inválida cualquier
  respuesta con un valor fuera de ese conjunto.
- **El ``id_emergencia`` debe coincidir con el de la petición**.
  Si la Centralita devuelve uno distinto, el supervisor no puede
  asociar el informe con el seguimiento abierto y lo registra como
  huérfano.

### 3.4. Si la Centralita no acepta la alerta

Antes de tocar el código de la Centralita, conviene aislar dónde
falla. Tres pruebas en este orden:

1. **`curl` al Agent Card**. Si esto no responde, el agente ni
   siquiera está sirviendo HTTP: el problema es de arranque, no de
   A2A.
2. **`curl` mínimo de la sección 2** contra la ``url`` declarada por
   la Agent Card. Si esto falla, es un problema A2A general (causas
   4.1 a 4.7 del catálogo siguiente).
3. **`curl` con la ``AlertaEmergencia`` real** de la sección 3.2. Si
   esto es lo único que falla, el problema vive en la validación del
   dominio o en la lógica interna de la Centralita.

## 4. Las siete causas más frecuentes, ordenadas por probabilidad

### 4.1. Envoltura JSON-RPC ausente o mal formada

El error más habitual: el grupo manda directamente el cuerpo del
dominio sin envolverlo en la estructura JSON-RPC.

Petición **incorrecta** (lo que el alumno suele probar primero):

```json
{
  "id_emergencia": "e-001",
  "tipo_emergencia": "INCENDIO",
  "prioridad": "ALTA",
  "descripcion": "Humo denso"
}
```

Respuesta del agente:

```json
{
  "jsonrpc": "2.0",
  "id": null,
  "error": {
    "code": -32600,
    "message": "Invalid request"
  }
}
```

**Cómo se arregla**: añadir `jsonrpc`, `id`, `method` y mover el cuerpo
del dominio dentro de `params.message.parts[0].data`.

### 4.2. La URL del POST no coincide con la del Agent Card

El Agent Card publica el endpoint A2A en el campo `url`. Si el grupo
hace `POST` a otra ruta (por ejemplo `/` o `/api/tasks`) en lugar de
la que declara su propia Agent Card, no hay handler que escuche.

Ejemplo de Agent Card:

```json
{
  "name": "bomberos_fenix",
  "version": "0.1.0",
  "url": "http://localhost:9001/a2a",
  "capabilities": { "streaming": false },
  "skills": [ ... ]
}
```

En este caso el `POST` debe ir a `http://localhost:9001/a2a`, no a
`http://localhost:9001/`. Síntoma: `404 Not Found` o `200 OK` con
contenido inesperado (la página por defecto del servidor).

### 4.3. Falta la cabecera `Content-Type`

Sin `Content-Type: application/json`, el servidor (aiohttp, FastAPI,
uvicorn...) no interpreta el cuerpo como JSON y el handler ve un
`request.json` vacío.

```bash
# Incorrecto
curl -X POST http://localhost:9001/a2a -d '{"jsonrpc": "2.0", ...}'

# Correcto
curl -X POST http://localhost:9001/a2a \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", ...}'
```

Respuesta típica: `415 Unsupported Media Type` o un JSON-RPC con
`error.code = -32700 (parse error)`.

### 4.4. El nombre del método no es exactamente `tasks/send`

El protocolo A2A es estricto. Variantes que **no** funcionan:

- `tasks.send`
- `task/send`
- `send_task`
- `sendTask`

Respuesta del agente:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found"
  }
}
```

### 4.5. Los `parts` del mensaje están mal construidos

Cada elemento de `message.parts` necesita un campo `type` que indica
qué tipo de contenido transporta. Los valores aceptados son `"text"`,
`"data"` y `"file"`.

Petición **incorrecta**:

```json
{
  "parts": [
    { "data": { "id_emergencia": "e-001" } }
  ]
}
```

Petición **correcta**:

```json
{
  "parts": [
    {
      "type": "data",
      "data": { "id_emergencia": "e-001" }
    }
  ]
}
```

Para enviar texto plano:

```json
{
  "parts": [
    { "type": "text", "text": "Incendio en la planta baja." }
  ]
}
```

### 4.6. El cuerpo del dominio no valida contra el contrato Pydantic

Si el agente receptor reconstruye el modelo `AlertaEmergencia` con
Pydantic y faltan campos obligatorios o los tipos no encajan, devuelve
un error JSON-RPC con `code = -32602 (Invalid params)`.

Ejemplo de campo obligatorio omitido (`ubicacion`):

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "validation_errors": [
        {
          "loc": ["params", "message", "parts", 0, "data", "ubicacion"],
          "msg": "field required",
          "type": "value_error.missing"
        }
      ]
    }
  }
}
```

Otros errores frecuentes de validación:

- `prioridad` en minúsculas (`"alta"`) cuando el enumerado del
  contrato espera mayúsculas (`"ALTA"`).
- `tipo_emergencia` con un valor no contemplado en el enumerado.
- `ubicacion` como cadena en lugar de objeto `{ "direccion": "..." }`.
- `id_emergencia` con un formato distinto al exigido (UUID, prefijo
  alfanumérico...).

### 4.7. El handler `tasks/send` no está registrado en el servidor

El servidor escucha y la Agent Card responde, pero el dispatcher
JSON-RPC no tiene un mapeo para `tasks/send`. Síntoma: respuesta
`-32601 Method not found` aunque el cuerpo esté perfectamente formado.

Ejemplo con `python-jsonrpcserver` (o equivalente):

```python
# Incorrecto: solo se registra la lectura de la Agent Card.
@method
def get_agent_card():
    return AGENT_CARD

# Correcto: además, se registra el método tasks/send.
@method(name="tasks/send")
async def tasks_send(id: str, sessionId: str, message: dict) -> dict:
    alerta = AlertaEmergencia.model_validate(
        message["parts"][0]["data"],
    )
    informe = await procesar_alerta(alerta)
    return {
        "id": id,
        "sessionId": sessionId,
        "status": {"state": "completed"},
        "artifacts": [
            {
                "name": "informe_resolucion",
                "parts": [
                    {"type": "data", "data": informe.model_dump()},
                ],
            },
        ],
    }
```

## 5. Tabla de códigos JSON-RPC y qué hacer

Cuando el agente responde con un objeto `error`, el campo
`error.code` indica la causa antes de mirar el cuerpo:

| Código    | Significado            | Acción recomendada |
|-----------|------------------------|--------------------|
| `-32700`  | Parse error            | Comprobar la cabecera `Content-Type: application/json` y que el cuerpo es JSON válido (sin comas finales, sin comillas simples). |
| `-32600`  | Invalid request        | Falta la envoltura JSON-RPC. Revisar que el cuerpo lleva `jsonrpc`, `id`, `method` y `params`. |
| `-32601`  | Method not found       | El nombre del método no es exactamente `tasks/send`, o el handler no está registrado. |
| `-32602`  | Invalid params         | Validación Pydantic del cuerpo del dominio: faltan campos o los tipos no encajan. Mirar `error.data.validation_errors` si lo expone. |
| `-32603`  | Internal error         | Excepción no capturada en el handler. Revisar el log del servidor (`uvicorn`, `aiohttp.access`) en el momento de la petición. |

## 6. Lista de verificación

1. **El `curl` exacto** que están lanzando, copiado tal cual, con el
   flag `-v` para ver cabeceras y URL final.
2. **La respuesta completa del servidor**: línea de estado HTTP
   (`HTTP/1.1 200 OK` o el código que devuelva) y el cuerpo. Si es
   un objeto `error` JSON-RPC, basta con su contenido íntegro.
3. **El `agent.json`** que sirven en `/.well-known/agent.json`,
   especialmente el campo `url`.
4. **El extracto del log del servidor** correspondiente al instante
   de la petición fallida (qué método se invocó, qué excepción saltó,
   si saltó alguna).

## 7. Procedimiento de depuración paso a paso

1. **Comprobar la Agent Card.**

   ```bash
   curl -s http://localhost:9001/.well-known/agent.json | jq .
   ```

   Anotar el valor del campo `url`. Será el endpoint A2A.

2. **Lanzar el `curl` mínimo de la sección 2** contra ese endpoint
   y conservar la respuesta.

3. **Si la respuesta es un `error.code`**, consultar la tabla de la
   sección 4 y aplicar la acción recomendada.

4. **Si la respuesta es un `result` pero la tarea no progresa**,
   el envío fue correcto y el problema vive más adentro
   (procesamiento asíncrono, cola, integración con SPADE, llamada al
   modelo de lenguaje...). Eso ya no es un problema de A2A.

5. **Si la respuesta es un código HTTP `4xx` o `5xx` sin cuerpo
   JSON-RPC**, el problema está antes del dispatcher JSON-RPC
   (ruta inexistente, middleware bloqueando, cabecera ausente).
   Revisar primero las causas 3.2 y 3.3 de esta guía.

## 8. Recordatorios útiles

- **El protocolo A2A no perdona pequeñas diferencias** en los nombres
  (`tasks/send`, no `task/send`). Cuando algo no funciona y el cuerpo
  parece correcto, comprobar literalmente el método.
- **Pydantic informa con detalle de qué campo falla**: si el agente
  reenvía el `validation_errors` dentro de `error.data`, el grupo no
  necesita adivinar; ya tiene el campo y el motivo.
- **El log del servidor es la mejor fuente de verdad** para
  diferenciar entre "el cliente envió mal" y "el servidor falló al
  procesar". Acostumbrar al grupo a abrirlo en una segunda terminal.
- **Si usan algún SDK A2A oficial** (por ejemplo el de Google), el
  SDK envuelve el JSON-RPC por dentro. Comparar lo que el SDK manda
  por la red (con `--log-level DEBUG`) contra el `curl` manual revela
  inmediatamente diferencias de envoltura o de nombres.
