# Verificación de los protocolos del supervisor del profesor

> **A quién va dirigido este documento:** a los grupos del Nivel 2
> que integran su sistema multiagente con el **agente supervisor
> del profesor**. El supervisor utiliza dos protocolos distintos
> contra los agentes del grupo:
>
> - **Protocolo 1 — Inyección de incidentes** (FIPA-Request). El
>   supervisor envía un `request` con un `DatosEmergencia` a la
>   Centralita; el grupo debe responder con un `agree` y, cuando
>   da por cerrada la emergencia, con un `inform` que contiene un
>   `InformeResolucion`.
> - **Protocolo 2 — Sondeo de estado** (FIPA-Query). El supervisor
>   envía periódicamente un `query-ref` con un `ConsultaEstado` a
>   cualquiera de los cinco roles; el agente debe responder con un
>   `inform` que contiene un `EstadoAgente`.
>
> El contrato textual completo está en
> [`docs/contrato_supervisor.md`](docs/contrato_supervisor.md).
> Este documento añade una **guía paso a paso de comprobaciones**
> para detectar pronto los errores más frecuentes que aparecen al
> implementar cada protocolo.
>
> **Tiempo estimado:** entre 30 y 45 minutos la primera vez (los
> dos protocolos juntos); entre 5 y 10 minutos en las siguientes
> ejecuciones.

---

## 0. Antes de empezar — comprobaciones previas

Antes de tocar el código de la centralita o de los demás agentes,
asegúrate de que:

1. La pila Docker (`ssmmaa-infraestructura`) está levantada y las
   pruebas `pytest tests/test_conexion_xmpp.py -v` pasan.
2. Tu copia local de `desarrollo-nivel2` tiene la **última**
   versión de `ontologia/modelos_compartidos.py`. El campo
   `ubicacion` debe ser un **objeto** `Ubicacion`, **no** una
   cadena. Comprueba con:

   ```bash
   grep "ubicacion:" ontologia/modelos_compartidos.py
   ```

   Debes ver:

   ```python
       ubicacion: Ubicacion = Field(description="Ubicación del incidente")
   ```

   Si ves `ubicacion: str = ...`, haz `git pull` y actualiza tu
   rama.

---

## 1. Resumen de los dos protocolos

Repaso compacto de las dos conversaciones que el supervisor
mantiene con los agentes del grupo. Las tablas siguientes son la
referencia rápida; los detalles están en
`docs/contrato_supervisor.md`.

### 1.1 — Protocolo 1: inyección de un incidente

```
Supervisor   →  request (DatosEmergencia)         →  Centralita
Centralita   →  agree                              →  Supervisor
Centralita   →  inform (InformeResolucion)         →  Supervisor
```

| Cabecera          | Valor                                  |
|-------------------|----------------------------------------|
| `performative`    | `request`                              |
| `protocol`        | `fipa-request`                         |
| `ontology`        | `emergencias-villaolivar`              |
| `language`        | `json-pydantic`                        |
| `conversation_id` | UUID generado por el supervisor (≡ `id_emergencia`) |

Cuerpo (JSON UTF-8):

```json
{
  "tipo_mensaje": "alerta_emergencia",
  "id_emergencia": "2efae4fb-ef5e-5920-989d-957b9a511bff",
  "tipo_emergencia": "incendio",
  "prioridad": "alta",
  "ubicacion": {
    "direccion": "Calle Mayor 14, Villa Olivar",
    "coordenadas": null
  },
  "descripcion": "Humo denso en planta segunda, vecinos evacuados.",
  "marca_temporal": "2026-04-30T17:32:11.142000"
}
```

### 1.2 — Protocolo 2: sondeo de estado

```
Supervisor   →  query-ref (ConsultaEstado)        →  Cualquier agente
Cualquier    →  inform (EstadoAgente)              →  Supervisor
```

| Cabecera          | Valor                                  |
|-------------------|----------------------------------------|
| `performative`    | `query-ref`                            |
| `protocol`        | `fipa-query`                           |
| `ontology`        | `emergencias-villaolivar`              |
| `language`        | `json-pydantic`                        |
| `conversation_id` | UUID generado por el supervisor (distinto en cada sondeo) |

Cuerpo (JSON UTF-8):

```json
{
  "tipo_mensaje": "consulta_estado",
  "agente_destino": "bomberos@grupo.localhost",
  "marca_temporal": "2026-04-30T17:32:50.000000"
}
```

Cada uno de los **cinco roles** (Centralita, Bomberos, Sanitario,
Policía y Municipal) debe atender este protocolo. La forma natural
de implementarlo es centralizarlo en una clase base común, para
que todos los agentes hereden la misma respuesta.

### 1.3 — Errores frecuentes (comunes a los dos protocolos)

1. Olvidar `ontology=emergencias-villaolivar` en la respuesta. El
   supervisor filtra los mensajes por esa marca y descarta sin
   aviso todo lo que no la lleve.
2. Olvidar `language=json-pydantic`. Aunque el supervisor sea
   tolerante, es la convención del contrato.
3. Construir un `Message` de SPADE desde cero en vez de usar
   `msg.make_reply()`. El método `make_reply()` ya copia el
   destinatario, el `conversation_id` y el `in_reply_to`; así no
   se pierde la correlación entre la pregunta y la respuesta.
4. Serializar el cuerpo a mano con `json.dumps(modelo.dict())` en
   lugar de usar `modelo.model_dump_json()`. El primero pierde
   matices de Pydantic (enumerados, fechas) y suele dejar campos
   en un formato distinto al esperado.

---

## 2. Verificación del Protocolo 1 (inyección)

### 2.1 — Importar los modelos correctos

En la Centralita, importa **siempre** desde la ontología
compartida. **No** redefinas `DatosEmergencia` localmente.

```python
from ontologia.modelos_compartidos import (
    DatosEmergencia, Ubicacion, Coordenadas,
    TipoEmergencia, Prioridad,
)
```

**Comprobación rápida:** abre un `python` y ejecuta:

```python
>>> from ontologia.modelos_compartidos import DatosEmergencia, Ubicacion
>>> DatosEmergencia.model_fields["ubicacion"].annotation
<class 'ontologia.modelos_compartidos.Ubicacion'>
```

Si te aparece `<class 'str'>`, tu rama está desactualizada (vuelve
a §0).

### 2.2 — Interpretar el cuerpo con Pydantic, no con `jsonschema`

La forma idiomática y recomendada es:

```python
async def run(self):
    msg = await self.receive(timeout=30)
    if msg is None:
        return
    try:
        alerta = DatosEmergencia.model_validate_json(msg.body)
    except ValidationError as exc:
        # Cuerpo no interpretable: responder con refuse y registrar.
        ...
        return
    # A partir de aquí, ``alerta.ubicacion.direccion``, etc.
```

**¿Por qué no `jsonschema.validate(json.loads(msg.body), DatosEmergencia.model_json_schema())`?**

Esa fórmula tiene tres problemas que confunden a los alumnos:

1. `model_json_schema()` marca como obligatorios campos que en
   realidad tienen `default_factory` en Pydantic (por ejemplo
   `marca_temporal`). Si el supervisor no incluyera ese campo en
   el JSON, `jsonschema` rechazaría el mensaje aunque Pydantic sí
   lo aceptase.
2. `jsonschema` no convierte los enumerados a `TipoEmergencia` o
   `Prioridad`; te quedas con cadenas sueltas. Pydantic sí lo
   hace.
3. `jsonschema` no construye los submodelos (`Ubicacion`,
   `Coordenadas`); tendrías que acceder a
   `data["ubicacion"]["direccion"]` en vez de a
   `alerta.ubicacion.direccion`.

`model_validate_json` resuelve los tres problemas a la vez.

### 2.3 — Acceder a la ubicación correctamente

```python
direccion: str = alerta.ubicacion.direccion
coords: Optional[Coordenadas] = alerta.ubicacion.coordenadas

if coords is not None:
    print(f"({coords.latitud}, {coords.longitud})")
```

**Errores típicos a evitar:**

```python
# ❌ Trata ubicacion como cadena
print(alerta.ubicacion.upper())

# ❌ Asume que las coordenadas siempre vienen
lat = alerta.ubicacion.coordenadas.latitud  # AttributeError si es None
```

### 2.4 — Responder con `agree` (Mensaje 2)

El supervisor espera tu `agree` antes de un plazo (configurable;
por defecto, pocos segundos). Construye la respuesta así:

```python
respuesta = msg.make_reply()
respuesta.set_metadata("performative", "agree")
respuesta.set_metadata("protocol", "fipa-request")
respuesta.set_metadata("ontology", "emergencias-villaolivar")
respuesta.set_metadata("language", "json-pydantic")
# ``conversation_id`` ya viene puesto por make_reply().
respuesta.body = json.dumps({
    "tipo_mensaje": "agree",
    "id_emergencia": alerta.id_emergencia,
})
await self.send(respuesta)
```

**Comprobación:** desde el panel del supervisor (en
`http://localhost:8081/supervisor`, modo activo), tu seguimiento
debe pasar de `ENVIADO` a `ACEPTADO` en menos de un segundo.

### 2.5 — Responder con `inform` y `InformeResolucion` (Mensaje 3)

Cuando el grupo da por cerrada la emergencia:

```python
from ontologia.modelos_compartidos import InformeResolucion

informe = InformeResolucion(
    id_emergencia=alerta.id_emergencia,
    tipo_emergencia=alerta.tipo_emergencia,
    prioridad=alerta.prioridad,
    estado_final="resuelto",
    resumen="Incendio extinguido sin víctimas.",
    agentes_participantes=["centralita@...", "bomberos@..."],
    acciones_realizadas=["evaluar_riesgo", "enfriamiento"],
)
respuesta = msg.make_reply()
respuesta.set_metadata("performative", "inform")
respuesta.set_metadata("protocol", "fipa-request")
respuesta.set_metadata("ontology", "emergencias-villaolivar")
respuesta.set_metadata("language", "json-pydantic")
respuesta.body = informe.model_dump_json()
await self.send(respuesta)
```

**Comprobación:** el seguimiento del panel pasa a `RESUELTO` y los
campos `agentes_participantes` y `acciones_realizadas` aparecen
poblados.

---

## 3. Verificación del Protocolo 2 (sondeo de estado)

Esta sección guía a los grupos por la implementación del segundo
protocolo, con el mismo nivel de detalle que el anterior.

### 3.1 — Por qué importa este protocolo

El supervisor usa la pestaña **«Estados de agentes»** del panel
para que el profesor vea, durante la corrección, qué agentes
están vivos y en qué estado se encuentran. Esa pestaña se
alimenta periódicamente del Protocolo 2: cada cierto tiempo (15
segundos por defecto) el supervisor envía un `query-ref` a cada
uno de los cinco roles del grupo y espera un `inform` con el
estado actual.

Si un agente del grupo no responde a este protocolo:

- Su fila no aparece en la pestaña.
- El profesor concluye que el agente está caído o mal
  configurado, aunque internamente esté trabajando.
- El supervisor registra avisos «Consulta caducada» en su propio
  registro a partir del segundo ciclo sin respuesta.

Por tanto, **los cinco roles deben atender el sondeo**, no solo
la Centralita.

### 3.2 — Los cinco roles que deben responder

El supervisor construye los identificadores de destino con la
convención `<rol>_<id_grupo>@<dominio>`. Los cinco roles
esperados son:

| Rol         | JID de ejemplo (grupo `fenix`)         |
|-------------|----------------------------------------|
| Centralita  | `centralita_fenix@localhost`           |
| Bomberos    | `bomberos_fenix@localhost`             |
| Sanitario   | `sanitario_fenix@localhost`            |
| Policía     | `policia_fenix@localhost`              |
| Municipal   | `municipal_fenix@localhost`            |

Si el grupo usa otra convención de nombres, el sondeo no llegará
a los agentes. La forma sensata de adaptarse es **respetar la
convención**, no tratar de cambiarla en el supervisor.

### 3.3 — Reconocer un mensaje de sondeo

Lo que distingue al sondeo de la inyección son **dos cabeceras**:

- `performative` vale `query-ref` (en la inyección vale
  `request`).
- `protocol` vale `fipa-query` (en la inyección vale
  `fipa-request`).

La estrategia recomendada es **separar los comportamientos**: un
comportamiento del agente filtra mensajes con `query-ref` y otro
filtra mensajes con `request`. Así cada uno se ocupa de un único
protocolo y el código queda más legible.

```python
from spade.template import Template

plantilla_sondeo = Template()
plantilla_sondeo.set_metadata("performative", "query-ref")
plantilla_sondeo.set_metadata("ontology", "emergencias-villaolivar")
self.add_behaviour(ResponderSondeoBehaviour(), plantilla_sondeo)
```

### 3.4 — Interpretar el cuerpo con `ConsultaEstado`

Igual que en el Protocolo 1, conviene usar Pydantic para
construir el modelo:

```python
from ontologia.modelos_compartidos import ConsultaEstado

async def run(self):
    msg = await self.receive(timeout=30)
    if msg is None:
        return
    try:
        consulta = ConsultaEstado.model_validate_json(msg.body)
    except ValidationError:
        # Cuerpo no interpretable: lo más sensato es ignorarlo.
        # El supervisor lo dará por caducado en su propia poda.
        return
    # ``consulta.agente_destino`` indica a qué rol va dirigido.
```

**Cuidado:** `agente_destino` es solo informativo. La verdadera
ruta del mensaje viene en la cabecera SPADE `to`. No filtres por
`agente_destino` para decidir si responder; si el mensaje te ha
llegado, te ha llegado a ti.

### 3.5 — Construir la respuesta `EstadoAgente`

El cuerpo de la respuesta debe ser un `EstadoAgente` válido. Los
cuatro campos que el grupo debe rellenar son:

| Campo                | Tipo            | Valor sugerido                                   |
|----------------------|-----------------|--------------------------------------------------|
| `agente`             | cadena          | `str(self.agent.jid)` — el JID propio.           |
| `estado`             | cadena          | Una palabra acordada por el grupo: `libre`, `ocupado`, `esperando_recurso`, etc. |
| `emergencia_actual`  | cadena o nulo   | El `id_emergencia` que está atendiendo, o `None` si está libre. |
| `detalle`            | cadena          | Texto descriptivo opcional. Si no aplica, `""`. |

```python
from ontologia.modelos_compartidos import EstadoAgente

estado = EstadoAgente(
    agente=str(self.agent.jid),
    estado="libre",
    emergencia_actual=None,
    detalle="",
)
```

**Buenas prácticas pedagógicas:**

- Mantén el conjunto de valores del campo `estado` **acotado y
  documentado** dentro de tu grupo (por ejemplo, en una
  constante `ESTADOS_VALIDOS = {"libre", "ocupado",
  "esperando_recurso"}`). Inventarse valores nuevos en cada
  respuesta hace ilegible la pestaña del panel.
- Si el agente está atendiendo una emergencia concreta, refleja
  su `id_emergencia` en `emergencia_actual`; el panel lo
  muestra y permite al profesor ver de un vistazo qué agentes
  están liberados y cuáles están ocupados.

### 3.6 — Enviar la respuesta `inform`

Igual que en el Protocolo 1, conviene partir de
`msg.make_reply()` para que el `conversation_id` y el
`in_reply_to` se preserven automáticamente:

```python
reply = msg.make_reply()
reply.set_metadata("performative", "inform")
reply.set_metadata("protocol", "fipa-query")
reply.set_metadata("ontology", "emergencias-villaolivar")
reply.set_metadata("language", "json-pydantic")
reply.body = estado.model_dump_json()
await self.send(reply)
```

**Plazo:** la respuesta debe llegar en menos de **2 segundos**
desde la recepción del `query-ref` (es el plazo
`timeout_consulta_estado` del contrato). Si tu agente tarda más,
el supervisor da la consulta por caducada y la entrada se borra
del estado interno hasta el siguiente sondeo.

### 3.7 — Errores típicos del Protocolo 2

| Error | Síntoma en el panel | Cómo detectarlo |
|-------|---------------------|-----------------|
| Olvidar `protocol=fipa-query` en la respuesta | El supervisor procesa el `inform` pero no lo correlaciona con el sondeo abierto | Imprime las cabeceras antes de `await self.send(reply)` |
| Construir el mensaje sin `make_reply()` | El supervisor descarta el `inform` (no encuentra el `conversation_id`) | Compara `msg.thread` y `reply.thread` justo antes del envío |
| Solo la Centralita responde al sondeo | La pestaña «Estados de agentes» solo muestra una fila por grupo | Levanta un agente concreto y comprueba que su rol aparece tras 15 segundos |
| El campo `estado` no es una cadena | Pydantic rechaza la respuesta y el supervisor descarta el `inform` | Comprueba el tipo del valor antes de pasarlo al modelo |
| Devolver una `marca_temporal` malformada | Pydantic la rechaza, mismo síntoma anterior | Usa `EstadoAgente(...)` sin pasar `marca_temporal`: Pydantic la rellena con `datetime.now()` |

### 3.8 — Comprobación visual desde el panel

Cuando creas que está implementado:

1. Levanta el supervisor del profesor en modo activo.
2. Levanta tu sistema con los cinco agentes del grupo.
3. Abre `http://localhost:8081/supervisor` en el navegador.
4. Pulsa la pestaña **«Estados de agentes»**.
5. Espera entre 15 y 30 segundos. Deberías ver **cinco filas**
   por grupo (una por rol), con el JID, el estado y la latencia
   del último sondeo.

Si tras dos ciclos de sondeo (≈ 30 segundos) algún rol no
aparece, ese agente no está respondiendo correctamente.

---

## 4. Pruebas de auto-verificación

Las dos baterías de pruebas siguientes deben pasar **antes** de
hacer una prueba de integración con el supervisor real. Cubren
los puntos en los que más fallan los grupos al interpretar los
mensajes del supervisor.

### 4.1 — Pruebas del Protocolo 1 (inyección)

Añade este fichero a `tests/`:

```python
# tests/test_inyeccion_supervisor.py
"""Comprobaciones del lado del grupo sobre la deserialización del
mensaje de inyección que envía el agente supervisor del profesor."""
import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from ontologia.modelos_compartidos import (
    Coordenadas,
    DatosEmergencia,
    Prioridad,
    TipoEmergencia,
    Ubicacion,
)


def _cuerpo_canonico() -> dict:
    """Cuerpo equivalente al que emite el supervisor del profesor."""
    return {
        "tipo_mensaje": "alerta_emergencia",
        "id_emergencia": "EM-001",
        "tipo_emergencia": "incendio",
        "prioridad": "alta",
        "ubicacion": {"direccion": "Calle Mayor 14"},
        "descripcion": "Humo denso en planta segunda.",
        "marca_temporal": datetime.now().isoformat(),
    }


def test_deserializacion_canonica_es_aceptada():
    """El cuerpo que emite el supervisor se interpreta sin errores."""
    alerta = DatosEmergencia.model_validate_json(
        json.dumps(_cuerpo_canonico()),
    )
    assert alerta.ubicacion.direccion == "Calle Mayor 14"
    assert alerta.ubicacion.coordenadas is None
    assert alerta.tipo_emergencia is TipoEmergencia.INCENDIO
    assert alerta.prioridad is Prioridad.ALTA


def test_ubicacion_string_plano_es_rechazada():
    """Detecta una rama desactualizada o un cambio incompatible.

    El contrato vigente exige ``ubicacion`` como objeto
    {direccion, coordenadas?}. Si esta prueba se rompe, el grupo
    está leyendo el formato antiguo.
    """
    cuerpo = _cuerpo_canonico()
    cuerpo["ubicacion"] = "Calle Mayor 14"  # formato antiguo
    with pytest.raises(ValidationError):
        DatosEmergencia.model_validate_json(json.dumps(cuerpo))


def test_coordenadas_opcionales_se_interpretan():
    cuerpo = _cuerpo_canonico()
    cuerpo["ubicacion"] = {
        "direccion": "Plaza Mayor 1",
        "coordenadas": {"latitud": 37.78, "longitud": -3.79},
    }
    alerta = DatosEmergencia.model_validate_json(json.dumps(cuerpo))
    assert alerta.ubicacion.coordenadas is not None
    assert alerta.ubicacion.coordenadas.latitud == pytest.approx(37.78)


def test_enum_invalido_es_rechazado():
    """Si el supervisor enviara un tipo no contemplado, debe fallar."""
    cuerpo = _cuerpo_canonico()
    cuerpo["tipo_emergencia"] = "categoria_inventada"
    with pytest.raises(ValidationError):
        DatosEmergencia.model_validate_json(json.dumps(cuerpo))


def test_id_emergencia_es_obligatorio():
    cuerpo = _cuerpo_canonico()
    del cuerpo["id_emergencia"]
    with pytest.raises(ValidationError):
        DatosEmergencia.model_validate_json(json.dumps(cuerpo))
```

Ejecuta:

```bash
pytest tests/test_inyeccion_supervisor.py -v
```

Las cinco pruebas deben pasar **antes** de hacer la prueba de
integración con el supervisor real.

### 4.2 — Pruebas del Protocolo 2 (sondeo)

Añade este fichero a `tests/`:

```python
# tests/test_sondeo_supervisor.py
"""Comprobaciones del lado del grupo sobre el protocolo de sondeo
de estado que envía el agente supervisor del profesor."""
import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from ontologia.modelos_compartidos import (
    ConsultaEstado,
    EstadoAgente,
)


def _consulta_canonica(jid_destino: str = "bomberos@grupo.localhost") -> dict:
    """Cuerpo equivalente al que emite el supervisor en cada sondeo."""
    return {
        "tipo_mensaje": "consulta_estado",
        "agente_destino": jid_destino,
        "marca_temporal": datetime.now().isoformat(),
    }


def test_consulta_canonica_se_interpreta_sin_errores():
    """El ``ConsultaEstado`` que llega del supervisor se parsea bien."""
    consulta = ConsultaEstado.model_validate_json(
        json.dumps(_consulta_canonica()),
    )
    assert consulta.tipo_mensaje == "consulta_estado"
    assert consulta.agente_destino == "bomberos@grupo.localhost"


def test_consulta_sin_agente_destino_es_rechazada():
    """El campo ``agente_destino`` es obligatorio en el contrato."""
    cuerpo = _consulta_canonica()
    del cuerpo["agente_destino"]
    with pytest.raises(ValidationError):
        ConsultaEstado.model_validate_json(json.dumps(cuerpo))


def test_estado_agente_minimo_es_aceptado():
    """Una respuesta mínima (solo ``agente`` y ``estado``) es válida.

    Los demás campos tienen valores por defecto en Pydantic
    (``emergencia_actual=None``, ``detalle=""``,
    ``marca_temporal=datetime.now()``).
    """
    estado = EstadoAgente(
        agente="bomberos_fenix@localhost",
        estado="libre",
    )
    assert estado.emergencia_actual is None
    assert estado.detalle == ""

    # El JSON serializado debe ser interpretable de vuelta.
    de_vuelta = EstadoAgente.model_validate_json(estado.model_dump_json())
    assert de_vuelta.agente == "bomberos_fenix@localhost"
    assert de_vuelta.estado == "libre"


def test_estado_agente_con_emergencia_se_serializa():
    """Cuando el agente está ocupado, ``emergencia_actual`` lleva el id."""
    estado = EstadoAgente(
        agente="bomberos_fenix@localhost",
        estado="ocupado",
        emergencia_actual="EM-001",
        detalle="Unidad 2 desplazada al lugar del incendio.",
    )
    payload = json.loads(estado.model_dump_json())
    assert payload["emergencia_actual"] == "EM-001"
    assert payload["detalle"].startswith("Unidad 2")


def test_estado_sin_campo_estado_es_rechazado():
    """El campo ``estado`` es obligatorio."""
    with pytest.raises(ValidationError):
        EstadoAgente(agente="bomberos_fenix@localhost")
```

Ejecuta:

```bash
pytest tests/test_sondeo_supervisor.py -v
```

Las cinco pruebas deben pasar **antes** de probar el sondeo con
el supervisor real corriendo.

---

## 5. Prueba de integración con el supervisor real

Cuando las comprobaciones previas y las pruebas unitarias estén
verdes, llega el momento de probar contra el supervisor real:

1. **Levanta el supervisor del profesor** (lo lanza el profesor
   en clase o en su sesión de corrección; durante el desarrollo,
   los grupos pueden usar la versión de la rama
   `agente-profesor-emergencias` indicada en
   `docs/contrato_supervisor.md`).
2. Arranca tu sistema con los cinco agentes del grupo:

   ```bash
   python main.py
   ```

3. Abre `http://localhost:8081/supervisor` en el navegador.

A partir de aquí puedes probar los dos protocolos de forma
independiente.

### 5.1 — Probar el Protocolo 1 (inyección)

1. Pulsa **«Inyectar incidente»** en la cabecera y selecciona tu
   grupo en el formulario.
2. Observa la línea de tiempo del seguimiento. El recorrido
   normal es:
   `PREPARADO` → `ENVIADO` → `ACEPTADO` → `RESUELTO`.

#### Diagnóstico cuando algo falla

| Síntoma en el panel | Causa probable | Verificación |
|---|---|---|
| El seguimiento se queda en `ENVIADO` | El grupo no envía `agree`, o la cabecera `ontology` está mal | Activa la traza en tu Centralita y comprueba que llega el `request`; revisa §2.4 |
| `TIMEOUT` antes de `RESUELTO` | El grupo no envía `inform` con `InformeResolucion`, o el cuerpo no se interpreta | Mira el registro SSE del panel; suele indicar el campo del modelo que falló |
| `FALLIDO` con error «cuerpo no interpretable» | JSON malformado, o usando una cadena para `ubicacion` | Vuelve a §2.5 y aplica `model_dump_json()` en lugar de armar el dict a mano |
| El supervisor parece ignorarte | Falta `ontology=emergencias-villaolivar` en la respuesta | Imprime las cabeceras antes de `send()` y compáralas con la tabla de §1.1 |

### 5.2 — Probar el Protocolo 2 (sondeo)

1. Pulsa la pestaña **«Estados de agentes»** del panel.
2. Espera entre 15 y 30 segundos (un par de ciclos de sondeo).
3. Comprueba que **aparecen cinco filas** por cada grupo
   declarado en el supervisor: una por rol.

#### Diagnóstico cuando algo falla

| Síntoma en el panel | Causa probable | Verificación |
|---|---|---|
| No aparece ninguna fila aunque tu sistema esté arriba | Los JID de los agentes no siguen la convención `<rol>_<id_grupo>@<dominio>` | Comprueba en el registro del supervisor las consultas que dispara y a qué destino |
| Aparece la Centralita pero no los demás roles | Los demás agentes no atienden el `query-ref` | Busca en cada agente el comportamiento que reciba `performative=query-ref` |
| Una fila aparece y desaparece intermitentemente | El agente responde, pero a veces tarda más de 2 segundos | Mide el tiempo entre la recepción del `query-ref` y el `send()` de la respuesta |
| El estado siempre se queda en `libre` aunque la emergencia esté activa | El agente no actualiza su estado interno cuando empieza a atender una emergencia | Revisa qué estructura interna del agente alimenta el `EstadoAgente.estado` |
| El campo `emergencia_actual` siempre es `null` | Falta enlazar el `id_emergencia` activo con el cuerpo de la respuesta | Cuando empieces a atender un incidente, guarda su id en una variable de instancia y léela aquí |

---

## 6. Lista de comprobación final (antes de entregar)

### Protocolo 1 — inyección

- [ ] `from ontologia.modelos_compartidos import Ubicacion` no
      falla.
- [ ] `DatosEmergencia.model_fields["ubicacion"].annotation` es
      `Ubicacion`, no `str`.
- [ ] El cuerpo del `request` se deserializa con
      `DatosEmergencia.model_validate_json(msg.body)`.
- [ ] El `agree` y el `inform` usan `msg.make_reply()` y se
      mandan con `ontology=emergencias-villaolivar`.
- [ ] El `InformeResolucion` se serializa con
      `informe.model_dump_json()`, no con
      `json.dumps(informe.dict())`.
- [ ] `pytest tests/test_inyeccion_supervisor.py -v` pasa al
      100 %.
- [ ] El seguimiento de un incidente inyectado llega a
      `RESUELTO` en el panel del supervisor.

### Protocolo 2 — sondeo

- [ ] Los cinco agentes (Centralita, Bomberos, Sanitario,
      Policía y Municipal) tienen un comportamiento que filtra
      `performative=query-ref`.
- [ ] La respuesta usa `msg.make_reply()` y lleva
      `performative=inform`, `protocol=fipa-query`,
      `ontology=emergencias-villaolivar` y
      `language=json-pydantic`.
- [ ] El cuerpo de la respuesta se construye con la clase
      `EstadoAgente` y se serializa con `model_dump_json()`.
- [ ] El campo `agente` lleva el JID propio
      (`str(self.agent.jid)`).
- [ ] Cuando el agente está atendiendo una emergencia,
      `emergencia_actual` lleva el `id_emergencia` y `estado`
      no es `"libre"`.
- [ ] `pytest tests/test_sondeo_supervisor.py -v` pasa al
      100 %.
- [ ] La pestaña **«Estados de agentes»** del panel muestra una
      fila por cada uno de los cinco roles del grupo, con
      latencia inferior a 2 segundos.
