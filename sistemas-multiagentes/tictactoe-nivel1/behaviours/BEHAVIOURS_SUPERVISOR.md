# Análisis y diseño de los comportamientos del Agente Supervisor

**Módulo:** [`supervisor_behaviours.py`](supervisor_behaviours.py)

**Documentación del agente:** [`doc/DOCUMENTACION_SUPERVISOR.md`](../doc/DOCUMENTACION_SUPERVISOR.md)

---

## Visión general

El agente supervisor utiliza dos comportamientos SPADE y una función
de respuesta a presencia que trabajan de forma coordinada:

1. **MonitorizarMUCBehaviour** se ejecuta periódicamente para registrar
   en el registro de depuración el estado de ocupación de las salas.
2. **La función de respuesta a presencia MUC** (`_on_presencia_muc`) captura en
   tiempo real las stanzas de presencia de las salas MUC para:
   - Mantener actualizada la lista de ocupantes del panel web.
   - Registrar entradas, salidas y cambios de estado de tableros.
   - Detectar tableros con `status="finished"` y crear una instancia
     del tercer componente.
3. **SolicitarInformeFSM** es una máquina de estados que gestiona,
   de principio a fin, la conversación con un tablero concreto para
   obtener su informe de partida. Se crea una instancia independiente
   por cada tablero finalizado, de modo que varias solicitudes pueden
   estar en curso simultáneamente.

A continuación se describe cada componente con su diagrama y su ficha
técnica.

---

## MonitorizarMUCBehaviour

Este comportamiento periódico registra en el registro de depuración un
resumen del número de ocupantes por sala. La lista de ocupantes se
mantiene actualizada en tiempo real mediante la función de respuesta a
presencia MUC (`_on_presencia_muc`), por lo que este comportamiento solo
proporciona un latido periódico para el registro. **No** detecta tableros
finalizados ni actualiza ocupantes: ambas tareas se delegan en la función
de respuesta a presencia MUC.

![Diagrama de actividad: MonitorizarMUCBehaviour](../doc/svg/behaviour-monitorizar-muc.svg)

| Campo | Descripción |
|-------|-------------|
| **Agente** | Ag. Supervisor (`supervisor@{dominio}`) |
| **Tipo** | `PeriodicBehaviour` — se ejecuta cada `intervalo_consulta` segundos (por defecto 10) |
| **Inicio** | Se registra en `setup()` del agente. Se activa automáticamente cuando el agente arranca. No utiliza plantilla de filtrado porque no recibe mensajes. |
| **Secuencia** | 1) Para cada sala de `salas_muc`, leer `ocupantes_por_sala[sala_id]` → 2) Registrar en el registro de depuración el número de ocupantes |
| **Finalización** | No finaliza (es periódico). Si se necesita una parada ordenada, se invoca `self.kill()` desde el agente o al recibir la señal de parada. |
| **Acción principal** | Registrar un resumen periódico del estado de ocupación de las salas. La actualización de ocupantes y la detección de tableros finalizados se realizan en la función de respuesta a presencia MUC `_on_presencia_muc`. |
| **Excepciones** | Ninguna: la lectura del diccionario `ocupantes_por_sala` no puede fallar. |

---

## SolicitarInformeFSM

Cuando la función de respuesta a presencia MUC detecta que un tablero
ha pasado al estado «finalizado», crea una instancia de este
comportamiento para gestionar toda la conversación con ese tablero.
Se ha modelado como una **máquina de estados finitos**
(`FSMBehaviour` de SPADE) porque el protocolo FIPA-Request tiene
varias fases claramente diferenciadas y múltiples caminos posibles
(el tablero puede aceptar, rechazar o no responder). Cada estado
del FSM se corresponde con un paso del protocolo descrito en la
[documentación del supervisor](../doc/DOCUMENTACION_SUPERVISOR.md#6-protocolo-de-comunicación),
y las transiciones entre estados están determinadas por la
performativa del mensaje recibido o por el agotamiento del tiempo
de espera.

Dado que se crea una instancia independiente por cada tablero,
pueden coexistir varias máquinas de estados ejecutándose en paralelo
sin interferencia entre ellas, ya que cada una filtra únicamente los
mensajes de su propia conversación gracias al campo `thread`.

![Diagrama de estados: SolicitarInformeFSM](../doc/svg/behaviour-solicitar-informe.svg)

| Campo | Descripción |
|-------|-------------|
| **Agente** | Ag. Supervisor (`supervisor@{dominio}`) |
| **Tipo** | `FSMBehaviour` — máquina de estados finitos con 6 estados. Se autodestruye al alcanzar un estado final. |
| **Inicio** | Se crea de forma dinámica por la función de respuesta a presencia MUC `_on_presencia_muc()` cuando detecta un tablero con `status="finished"`. Plantilla de filtrado: `thread={hilo_único}` ∧ `ontology=tictactoe`. Se crea una instancia por cada tablero finalizado. Todos los estados comparten el buzón de mensajes del FSM y un contexto `ctx` con `jid_tablero`, `sala_id`, `hilo` y `mensaje`. El estado `ENVIAR_REQUEST` registra un evento de tipo `solicitud` en el registro al enviar el REQUEST. |
| **Estados** | `ENVIAR_REQUEST` (inicial) — envía la solicitud de informe al tablero. `ESPERAR_RESPUESTA` — espera la primera respuesta (tiempo límite de 10 s) y clasifica según la performativa recibida. `ESPERAR_INFORME` — espera el informe tras recibir un AGREE (tiempo límite de 10 s); un REFUSE no es posible aquí porque el tablero ya aceptó la solicitud. `PROCESAR_INFORME` (final) — valida y almacena el informe (CASO A/A2). `PROCESAR_RECHAZO` (final) — registra la razón del rechazo (CASO B). `REGISTRAR_TIMEOUT` (final) — registra la incidencia en el registro de la sala (CASO C). |
| **Transiciones** | `ENVIAR_REQUEST` → `ESPERAR_RESPUESTA` (siempre). `ESPERAR_RESPUESTA` → `ESPERAR_INFORME` (agree) ∣ `PROCESAR_INFORME` (inform) ∣ `PROCESAR_RECHAZO` (refuse) ∣ `REGISTRAR_TIMEOUT` (tiempo agotado). `ESPERAR_INFORME` → `PROCESAR_INFORME` (inform) ∣ `REGISTRAR_TIMEOUT` (tiempo agotado). |
| **Finalización** | Los estados `PROCESAR_INFORME`, `PROCESAR_RECHAZO` y `REGISTRAR_TIMEOUT` son finales: no indican un estado siguiente, lo que provoca la autodestrucción del FSM (`self.kill()`). |
| **Acción principal** | Modelar el protocolo FIPA-Request completo como una máquina de estados. Cada instancia del FSM es independiente y gestiona un único informe de un tablero concreto. |
| **Excepciones** | **E1 — Tiempo agotado (CASO C):** el tablero no responde en 10 s → el estado `REGISTRAR_TIMEOUT` anota la incidencia en el registro de la sala. **E2 — JSON no válido:** `PROCESAR_INFORME` no puede interpretar el cuerpo del mensaje → se registra el error y no se almacena. **E3 — Validación fallida:** el contenido no cumple el esquema de la ontología → se registra un aviso con los errores de validación. **E4 — Rechazo (CASO B):** `PROCESAR_RECHAZO` registra la razón del rechazo. **E5 — Performativa inesperada:** los estados de espera transicionan a `REGISTRAR_TIMEOUT` como respuesta segura por defecto. |

---

## Función de respuesta a presencia MUC: `_on_presencia_muc`

Este componente no es un comportamiento SPADE, sino una función de
respuesta que el agente registra en el cliente XMPP subyacente
(slixmpp) durante la inicialización. Se invoca automáticamente cada vez que el cliente
recibe una stanza de presencia, y filtra las que provienen de las
salas MUC monitorizadas. El supervisor se une a las salas enviando
stanzas de presencia con namespace MUC (`_unirse_sala_muc`), lo que
garantiza recibir las presencias de todos los ocupantes.

### Responsabilidades

1. **Registro de entradas**: cuando un ocupante nuevo se une a una
   sala, se añade a `ocupantes_por_sala` y se registra un evento
   de tipo `entrada` en el registro.
2. **Registro de salidas**: cuando un ocupante envía presencia
   `unavailable`, se elimina de `ocupantes_por_sala` y se registra
   un evento de tipo `salida`.
3. **Cambios de estado de tableros**: cuando un tablero cambia su
   `status` (por ejemplo, `waiting` → `playing` → `finished`), se
   registra un evento de tipo `presencia` con la transición.
4. **Detección de tableros finalizados**: cuando un tablero cambia a
   `status="finished"`, se crea una instancia de `SolicitarInformeFSM`.

### Eventos registrados en el registro

| Tipo | Cuándo | Detalle |
|------|--------|---------|
| `entrada` | Nuevo ocupante se une a la sala | «Se ha unido a la sala (jugador/tablero)» |
| `salida` | Ocupante abandona la sala | «Se ha desconectado» |
| `presencia` | Tablero cambia de estado | «status: waiting → playing» |
| `solicitud` | Se envía REQUEST game-report | «Solicitado informe de partida» |
| `informe` | Se recibe informe válido | Detalle del resultado |
| `abortada` | Informe de partida abortada | Detalle con motivo |
| `timeout` | Tablero no responde a tiempo | «Sin respuesta tras N s» |

| Campo | Descripción |
|-------|-------------|
| **Agente** | Ag. Supervisor (`supervisor@{dominio}`) |
| **Tipo** | Función de respuesta a evento `presence` del cliente slixmpp — invocada por cada stanza de presencia recibida |
| **Inicio** | Se registra en `setup()` con `self.client.add_event_handler("presence", self._on_presencia_muc)` |
| **Secuencia** | 1) Recibir la stanza de presencia → 2) Extraer sala, nick, tipo, show, status y JID real del item MUC → 3) Filtrar: solo procesar presencias de salas monitorizadas, ignorar el propio nick del supervisor → 4) Si `type="unavailable"`: eliminar ocupante y registrar evento «salida» → 5) Si es nuevo: añadir a ocupantes y registrar evento «entrada» → 6) Si es tablero y su estado cambió: registrar evento «presencia» con la transición → 7) Si es tablero con `status="finished"` y no está en `tableros_consultados`: crear `SolicitarInformeFSM` |
| **Acción principal** | Mantener actualizada la lista de ocupantes en tiempo real, registrar todos los eventos relevantes en el registro y detectar de forma reactiva los tableros finalizados. |
