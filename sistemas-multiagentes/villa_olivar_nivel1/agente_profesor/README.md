# Agente supervisor del profesor — Villa Olivar (Nivel 2)

**Paquete:** `agente_profesor/`

**Asignatura:** Sistemas Multiagente — Grado en Ingeniería Informática

**Universidad de Jaén — Departamento de Informática**

**Curso:** 2025-2026

**Rama de desarrollo:** `agente-profesor-emergencias`

---

## 1. Propósito

El agente `profesor_emergencias` es el **banco de pruebas** que el
profesor utiliza para corregir las entregas del Nivel 2. Inyecta
incidentes a la Centralita de cada grupo, recoge los informes de
resolución y expone una interfaz web (panel) que permite revisar
en tiempo real o a posteriori el comportamiento de cada grupo.

Este documento describe la **implementación actual** del agente, su
**funcionamiento** y las **pruebas** que se pueden realizar sobre él.
La parte conceptual (papel en el sistema, principios rectores,
protocolos FIPA-ACL, autómata) vive en
[`docs/agente_profesor/diseno_inicial.md`](../docs/agente_profesor/diseno_inicial.md).
El contrato observable que los grupos usan para escribir sus tests
está en
[`docs/agente_profesor/caracteristicas_para_tests_grupo.md`](../docs/agente_profesor/caracteristicas_para_tests_grupo.md).

---

## 2. Estado de la implementación

La implementación actual cubre **el agente completo**: arranque,
panel web sobre SQLite y los cuatro comportamientos (en inglés
*behaviours*) de SPADE: inyección, recepción, vigilancia de plazos
(*timeouts*) y sondeo de estados.
La inyección puede ser **automática** —según el bloque `inyeccion`
de `config_profesor.yaml`— o **manual** desde el botón "Inyectar
incidente" del panel.

| Pieza                                            | Estado     |
|--------------------------------------------------|------------|
| Configuración centralizada                       | ✅ Implementada |
| Autómata de seguimiento (memoria)                | ✅ Implementado |
| Catálogo determinista de escenarios              | ✅ Implementado |
| Persistencia SQLite multi-ejecución              | ✅ Implementada |
| Sembrado automático con demo                     | ✅ Implementado |
| Panel web (HTML + CSS + JS)                      | ✅ Implementado |
| API JSON estable (`/supervisor/api/*`)           | ✅ Implementada |
| Eventos enviados por el servidor (*Server-Sent Events*, SSE) en vivo | ✅ Implementados |
| Selector de ejecuciones históricas               | ✅ Implementado |
| Exportación CSV                                  | ✅ Implementada |
| Botón Finalizar con cierre limpio                | ✅ Implementado |
| Comportamiento (*behaviour*) de inyección de incidentes | ✅ Implementado |
| Comportamiento (*behaviour*) de recepción de respuestas | ✅ Implementado |
| Comportamiento (*behaviour*) de vigilancia de plazos    | ✅ Implementado |
| Sondeo periódico `ConsultaEstado`                | ✅ Implementado |
| Formulario "Inyectar incidente" con catálogo     | ✅ Implementado |
| `/supervisor/api/escenarios` (lista del catálogo)| ✅ Implementado |
| Almacén transitorio para histórico tras cierre   | ✅ Implementado |
| Conjunto de pruebas automáticas (142 pruebas)    | ✅ Implementado |

---

## 3. Estructura de ficheros

```
agente_profesor/
├── README.md                           Este documento
├── __init__.py
├── agente_supervisor.py                Clase SupervisorEmergencias(Agent)
├── seguimientos.py                     Dataclass Seguimiento + autómata
├── escenarios.py                       Catálogo determinista (UUID v5)
├── config_profesor.yaml                Configuración del supervisor
├── persistencia/
│   ├── __init__.py
│   ├── almacen_supervisor.py           AlmacenSupervisor (SQLite)
│   └── semilla_demo.py                 Sembrado de ejecución demo
└── web/
    ├── __init__.py
    ├── handlers.py                     Manejadores HTTP/SSE/CSV (*handlers*)
    ├── templates/
    │   └── supervisor.html             Plantilla del panel
    └── static/
        ├── supervisor.css              Tema oscuro/claro WCAG AA
        └── supervisor.js               SSE + pestañas + ventana de detalle + selector

profesor_main.py                        Lanzador independiente (raíz)
data/supervisor.db                      BD SQLite (creada al arrancar)
```

---

## 4. Configuración

Toda la configuración del supervisor vive en
`agente_profesor/config_profesor.yaml`. Los datos de conexión XMPP se
reaprovechan del `config.yaml` raíz del proyecto.

```yaml
identidad:
  usuario: "profesor_emergencias"
  contrasena: "profesor_emergencias_pass"

web:
  puerto: 10100
  host: "0.0.0.0"
  abrir_navegador: true
  auth_usuario: ""        # HTTP Basic opcional
  auth_contrasena: ""

persistencia:
  ruta_db: "data/supervisor.db"
  descripcion_sesion: ""

timeouts:
  agree_segundos: 5       # request → agree
  informe_segundos: 180   # agree → inform (margen para inferencia LLM)
  consulta_estado_segundos: 2

inyeccion:
  intervalo_segundos: 30
  automatica: false       # se gobierna desde el panel

grupos: []                # lista vacía → modo consulta usa la demo

modo_arranque: "consulta"
```

Ningún campo de los anteriores está fijado en el código:
cambiar el puerto, los plazos (*timeouts*) o la base de datos no
requiere tocar Python.

### 4.1. Escenarios de uso

El supervisor está pensado para ejecutarse en **dos contextos
distintos**, ambos cubiertos por el mismo binario y la misma
configuración: lo único que cambia es la lista `grupos:` del
`config_profesor.yaml`.

#### Escenario A — Alumno autoevaluándose

Cada grupo de prácticas integra el supervisor dentro de **su propio
proyecto** mientras desarrolla. El objetivo es verificar que su
Centralita acepta las inyecciones del supervisor, responde con
`agree` a tiempo, emite un `InformeResolucion` válido antes del
plazo (*timeout*) y contesta correctamente a las consultas de estado.

Lo único que el grupo debe hacer es **poner su propio identificador**
en `grupos:`, sin tocar nada más:

```yaml
grupos:
  - id: "miGrupo"
    nombre: "Equipo de pruebas"
    jid_centralita: "centralita_miGrupo@localhost"
```

El JID debe coincidir con el que la Centralita del grupo utiliza
en el servidor XMPP (Prosody local). El supervisor arranca con:

```bash
python profesor_main.py --modo activo
```

Y el grupo abre `http://localhost:10100/supervisor` para ver en
tiempo real cómo su sistema gestiona los incidentes inyectados.
Esta es la forma natural de **probar las validaciones que el grupo
ya tiene implementadas** sin depender de la sesión de corrección.

#### Escenario B — Profesor corrigiendo en el laboratorio

El profesor arranca un único supervisor frente a **todos los grupos**
de la sesión. Declara cada grupo a evaluar, con su `id`, `nombre`
y el `jid_centralita` con el que ese grupo registró su Centralita
en el servidor XMPP del laboratorio:

```yaml
grupos:
  - id: "fenix"
    nombre: "Equipo Fénix"
    jid_centralita: "centralita_fenix@localhost"
  - id: "olivar42"
    nombre: "Equipo Olivar 42"
    jid_centralita: "centralita_olivar42@localhost"
  - id: "quercus"
    nombre: "Equipo Quercus"
    jid_centralita: "centralita_quercus@localhost"
```

A partir de ahí arranca con `--modo activo` y el panel muestra
una columna por grupo en la barra lateral. Las inyecciones se
distribuyen entre los grupos declarados, los seguimientos se
persisten en SQLite (una ejecución por sesión) y el profesor puede
revisar **a posteriori** cualquier sesión anterior desde el selector
de la cabecera.

#### Diferencias clave entre ambos escenarios

| Aspecto                          | Escenario A (alumno)         | Escenario B (profesor)             |
|----------------------------------|------------------------------|------------------------------------|
| Nº de grupos en `grupos:`        | Uno (el suyo)                | Varios (todos los de la sesión)    |
| Servidor XMPP                    | Prosody local del grupo      | Prosody del laboratorio            |
| Objetivo                         | Validar la propia Centralita | Corregir múltiples entregas        |
| Modo de arranque típico          | `activo`                     | `activo`                           |
| `descripcion_sesion` recomendada | `"autoevaluacion"`           | `"correccion-YYYY-MM-DD"`          |
| Frecuencia de uso                | Durante todo el desarrollo   | Una vez por sesión de corrección   |

En ambos escenarios el resto del fichero (`identidad`, `web`,
`persistencia`, `timeouts`, `inyeccion`, `modo_arranque`) se
mantiene idéntico. Solo cambia `grupos:`.

---

## 5. Modos de ejecución

### 5.1. Modo `consulta` (por defecto)

```bash
python profesor_main.py
# o explícitamente:
python profesor_main.py --modo consulta
```

- **No conecta a XMPP.** Arranca un servidor aiohttp ligero contra la
  BD SQLite del supervisor.
- Si la BD está vacía, se **siembra automáticamente** una ejecución
  demo con 6 seguimientos en estados terminales variados
  (`RESUELTO`, `TIMEOUT`, `FALLIDO`, `ACEPTADO`) repartidos en dos
  grupos ficticios (`g04-fenix`, `g11-olivar42`).
- El navegador se abre solo en `http://localhost:10100/supervisor`.
- El selector de cabecera "Ejecución" lista todas las ejecuciones
  almacenadas; el panel selecciona automáticamente la más reciente.

### 5.2. Modo `activo`

```bash
python profesor_main.py --modo activo
```

- Conecta al servidor XMPP indicado por `perfil_xmpp_activo` del
  `config.yaml` raíz (`local`, `servidor`, …).
- Crea una **nueva ejecución** en la base de datos; cada `request`
  enviado o `inform` recibido se persiste automáticamente.
- Enlaza los cuatro comportamientos (*behaviours*): inyector,
  receptor, vigilante y sondeo. El inyector arranca en modo
  automático o manual según `inyeccion.automatica` del YAML; el
  resto siempre activos.
- El panel refleja en tiempo real, mediante eventos del servidor
  (*Server-Sent Events*, SSE), los seguimientos que generan las
  inyecciones y los `EstadoAgente` que llegan del sondeo periódico.

### 5.3. Argumentos de la línea de órdenes

| Argumento                  | Valor por defecto                      | Descripción |
|----------------------------|----------------------------------------|-------------|
| `--modo`                   | `consulta`                             | `consulta` o `activo` |
| `--config`                 | `config.yaml`                          | Configuración XMPP del proyecto |
| `--config-profesor`        | `agente_profesor/config_profesor.yaml` | Configuración específica |
| `--puerto`                 | `10100`                                | Puerto del panel |
| `--no-abrir-navegador`     | `false`                                | No abrir el navegador |

---

## 6. Panel web

El panel se sirve en `http://localhost:10100/supervisor` y se
inspira en el supervisor del proyecto `TicTacToe`.

### 6.1. Estructura visual

- **Cabecera fija** con el JID del supervisor, el modo activo
  (etiqueta superior), un punto verde/gris/rojo (en vivo / histórico
  / finalizado), reloj `HH:MM:SS`, contadores globales, **selector
  de ejecución**, **botón Finalizar** y **conmutador de tema
  diurno/nocturno**.
- **Barra lateral** con los grupos bajo prueba más una entrada
  "Vista general". Cada grupo muestra contadores
  `X segs · X OK · X KO`.
- **Panel principal** con seis tarjetas de métricas (totales,
  resueltos, en error, en curso, mediana de latencias) y cuatro
  pestañas: **Seguimientos · Estados de agentes · Resumen · Registro**.
- **Ventana de detalle** al pulsar una fila de la tabla de
  seguimientos, con la línea temporal, el `InformeResolucion`
  recibido (presentado como ficha legible) y el mensaje de error si el
  estado terminal fue de fallo.
- **Capa superpuesta** (en inglés *overlay*) de finalización que
  aparece tras pulsar Finalizar para dejar claro que el servidor ha
  cerrado.

### 6.2. Eventos en tiempo real (*Server-Sent Events*, SSE)

`/supervisor/api/stream` envía eventos:

| Tipo            | Cuándo se emite                                            |
|-----------------|-------------------------------------------------------------|
| `state`         | Conexión inicial — contenido completo del estado.           |
| `seguimiento`   | Cada vez que un seguimiento cambia de estado o se crea.     |
| `log`           | Cada nuevo evento del registro cronológico.                 |
| `cierre`        | Al pulsar Finalizar; el cliente cierra su `EventSource`.    |

El cliente cierra la conexión SSE cuando:

- el usuario selecciona una ejecución histórica (no hay flujo en vivo),
- el usuario pulsa Finalizar (capa superpuesta y punto rojo),
- el servidor envía un evento `cierre`.

### 6.3. Puntos de acceso (*endpoints*) HTTP

| Método | Ruta                                              | Descripción |
|--------|---------------------------------------------------|-------------|
| GET    | `/supervisor`                                     | Panel HTML |
| GET    | `/supervisor/api/state`                           | Estado en vivo |
| GET    | `/supervisor/api/seguimientos`                    | Lista en vivo |
| GET    | `/supervisor/api/seguimientos/{id}`               | Detalle en vivo |
| GET    | `/supervisor/api/resumen`                         | Métricas en vivo |
| GET    | `/supervisor/api/ejecuciones`                     | Listado histórico |
| GET    | `/supervisor/api/ejecuciones/{id}`                | Detalle histórico |
| GET    | `/supervisor/api/escenarios`                      | Catálogo del formulario de inyección |
| GET    | `/supervisor/api/stream`                          | SSE en tiempo real |
| GET    | `/supervisor/api/csv/{seguimientos\|resumen\|log}`| CSV en vivo |
| GET    | `/supervisor/api/ejecuciones/{id}/csv/{tipo}`     | CSV histórico |
| POST   | `/supervisor/api/inyectar`                        | Inyección manual desde el panel |
| POST   | `/supervisor/api/finalizar`                       | Cierre ordenado |
| GET    | `/supervisor/static/...`                          | CSS/JS |

Las consultas históricas (`/api/ejecuciones[/...]` y los CSV
asociados) usan el auxiliar `_almacen_lectura`, que abre una
conexión SQLite **transitoria** si el almacén principal ya se cerró
tras pulsar Finalizar. Esto permite seguir consultando la sesión
recién finalizada sin reiniciar el supervisor.

El esquema de respuesta es estable y forma parte del contrato
público del supervisor (ver `caracteristicas_para_tests_grupo.md` §7.6).

---

## 7. Persistencia SQLite

### 7.1. Esquema

```
ejecuciones      (id, modo, inicio, fin, descripcion)
grupos           (ejecucion_id, grupo_id, nombre, jid_centralita, descripcion)
seguimientos     (ejecucion_id, id_emergencia, grupo, jid_destino,
                  tipo_emergencia, prioridad, descripcion, estado,
                  instante_creacion, instante_envio, instante_agree,
                  instante_informe, latencia_agree_ms,
                  latencia_informe_ms, error, informe_json, eventos_json)
log_eventos      (id, ejecucion_id, ts, tipo, origen, detalle)
```

Los `informe_json` y `eventos_json` son JSON serializados en línea.
El esquema se crea de forma idempotente al abrir la BD.

### 7.2. Ciclo de vida

- **Modo activo:** `setup()` del agente llama a `crear_ejecucion()`,
  cada `registrar_seguimiento()` y `registrar_evento()` persiste en
  la BD, y `detener()` llama a `finalizar_ejecucion()` + `cerrar()`.
- **Modo consulta:** se abre la BD en lectura, no se crea ninguna
  ejecución nueva, y el almacén se cierra al finalizar.
- **Sembrado:** `sembrar_demo_si_vacio()` solo escribe si la tabla
  `ejecuciones` está vacía. Es seguro llamarla en cada arranque.

### 7.3. Borrar la BD para reiniciar

```bash
rm data/supervisor.db
python profesor_main.py            # vuelve a sembrar la demo
```

---

## 8. Pruebas manuales

### 8.1. Validar que la interfaz arranca y muestra datos

```bash
rm -f data/supervisor.db
python profesor_main.py --modo consulta --no-abrir-navegador
```

Salida esperada (resumida):

```
Almacén SQLite abierto en data/supervisor.db
Ejecución #1 sembrada (6 seguimientos, 12 eventos)
BD vacía → sembrada con ejecución demo (6 seguimientos, 2 grupos)
Modo CONSULTA — panel disponible en http://localhost:10100/supervisor
```

Abrir manualmente `http://localhost:10100/supervisor`. Comprobar:

- El selector de cabecera muestra "En vivo" + la ejecución de muestra.
- La barra lateral lista los dos grupos de muestra con sus contadores.
- La pestaña **Seguimientos** muestra una tabla con 6 filas.
- Pulsar una fila abre la ventana de detalle con la línea de tiempo y la ficha del informe de resolución.
- Las pestañas **Resumen** y **Registro** se rellenan con datos coherentes.
- Cambiar el conmutador de tema diurno/nocturno persiste tras recarga.

### 8.2. Validar que el botón Finalizar funciona

Estando el servidor en marcha, pulsar **⏹ Finalizar** en la cabecera.
Aparece un `confirm()`; tras aceptar:

- El botón se deshabilita (`Finalizando…`).
- El punto de la cabecera pasa a rojo.
- Aparece la capa superpuesta «Supervisor finalizado».
- El proceso termina en ≤ 3 s.
- El puerto queda liberado.

Verificar desde otra terminal:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:10100/supervisor
# debería devolver 000 (puerto cerrado)
```

### 8.3. Validar API con curl

```bash
# Estado actual
curl -s http://localhost:10100/supervisor/api/state | jq .

# Listado de ejecuciones
curl -s http://localhost:10100/supervisor/api/ejecuciones | jq .

# Detalle de la ejecución #1
curl -s http://localhost:10100/supervisor/api/ejecuciones/1 | jq '.resumen'

# Exportar CSV
curl -s http://localhost:10100/supervisor/api/csv/seguimientos > segs.csv
curl -s http://localhost:10100/supervisor/api/ejecuciones/1/csv/log > log_e1.csv

# Finalizar
curl -s -X POST http://localhost:10100/supervisor/api/finalizar
```

### 8.4. Validar eventos del servidor (SSE)

```bash
curl -N http://localhost:10100/supervisor/api/stream
```

Debe imprimirse de inmediato un evento `state` con todo el JSON, y
a partir de ahí líneas `: keepalive` cada 15 s. Tras un `POST
/api/finalizar` desde otra terminal aparece un evento `cierre` y la
conexión se cierra.

### 8.5. Validar persistencia y modo activo

Con Prosody arrancado en Docker:

```bash
docker compose up -d xmpp
python profesor_main.py --modo activo --no-abrir-navegador
```

Salida esperada:

```
Modo ACTIVO — perfil XMPP 'local' (servidor: localhost:5222)
Ejecución #N creada (modo=activo, grupos=0)
Supervisor arrancado (JID: profesor_emergencias@localhost) — panel en http://localhost:10100/supervisor
```

Detener con Ctrl+C; abrir el panel en modo consulta:

```bash
python profesor_main.py --modo consulta --no-abrir-navegador
```

El selector de ejecuciones debe mostrar tanto la ejecución demo (#1)
como la nueva (#N) con su modo "activo".

---

## 9. Pruebas automáticas

El conjunto de pruebas reside en `tests/agente_profesor/` y cubre
**142 pruebas** sin SPADE, sin servidor XMPP y sin red. Tarda menos
de medio segundo:

```bash
pytest tests/agente_profesor/ -v
# 142 passed in 0.36s
```

Resumen por fichero:

| Fichero                          |  Nº de pruebas | Componente |
|----------------------------------|---------------:|------------|
| `test_seguimientos.py`           | 32             | Autómata `Seguimiento` (transiciones, latencias, serialización) |
| `test_escenarios.py`             | 17             | Catálogo determinista, modo demostración, UUID v5 reproducibles |
| `test_almacen_supervisor.py`     | 21             | Persistencia SQLite (ciclo de vida, aislamiento, sembrado) |
| `test_inyector.py`               | 11             | `InyectorIncidentesBehaviour` (manual + rotación cíclica, *round-robin*) |
| `test_receptor.py`               | 11             | `ReceptorRespuestasBehaviour` (5 performativas + huérfanos) |
| `test_vigilante.py`              |  6             | `VigilanteTimeoutsBehaviour` (plazos de `agree` e `informe`) |
| `test_sondeo.py`                 |  6             | `SondeoEstadoBehaviour` + `procesar_estado_agente_recibido` |
| `test_handlers.py`               | 32             | Manejadores (*handlers*) HTTP (`/api/state`, CSV, ejecuciones, inyectar, escenarios, autenticación, `_almacen_lectura`) |
| `test_agente_supervisor.py`      |  9             | `registrar_seguimiento`, `registrar_evento`, `inyectar_manualmente` |

Patrón común para los comportamientos (*behaviours*): simulador
`AgenteSupervisorSimulado` en `conftest.py` y `AsyncMock` para los
métodos `send`/`receive`. Las pruebas HTTP usan el cliente de
pruebas de `pytest-aiohttp` (incluido en `requirements.txt`).

Documentación detallada del conjunto de pruebas en
[`docs/agente_profesor/testing_profesor.md`](../docs/agente_profesor/testing_profesor.md).
Ficha técnica de cada comportamiento en
[`docs/agente_profesor/behaviours_profesor.md`](../docs/agente_profesor/behaviours_profesor.md).

---

## 10. Trabajo opcional pendiente

La primera etapa (panel + persistencia), la segunda (comportamientos
SPADE + inyección manual + sondeo) y la tercera (formulario de
inyección + pruebas automáticas) están **implementadas**.

Mejoras opcionales identificadas pero no críticas para la
corrección:

1. Añadir en la pestaña **Estados de agentes** un indicador de
   "obsolescencia" (verde/ámbar/rojo) según la antigüedad de la
   última respuesta de sondeo.
2. Permitir filtrar la lista de seguimientos por grupo y por estado
   directamente desde la cabecera de la tabla (hoy se filtra
   pulsando un grupo en la barra lateral).
3. Pruebas de integración con SPADE real (una `Centralita`
   simulada y un supervisor en modo activo): pruebas rápidas de
   validación (en inglés *smoke tests*) que cubran el protocolo de
   extremo a extremo. Análogas a las 23 pruebas de integración del
   supervisor de TicTacToe.

---

*Documento del agente supervisor del profesor — Villa Olivar — Nivel 2*
