# Descubrimiento de tableros y jugadores en la sala MUC

**Asignatura:** Sistemas Multiagente — Grado en Ingeniería Informática

**Universidad de Jaén** — Departamento de Informática

---

> **Dónde están los archivos auxiliares.**
>
> Esta guía vive en la rama principal del proyecto para que sea fácil
> de consultar. Sin embargo, los **scripts auxiliares** que se mencionan
> a lo largo del texto (`scripts/comprobar_jid_visible_en_muc.py`,
> `scripts/diagnosticar_sala_muc.py`, `scripts/limpiar_salas_muc.py`),
> el **agente supervisor** del profesor (`agentes/agente_supervisor.py` y
> `behaviours/supervisor_behaviours.py`)
> con sus pruebas asociadas viven en la rama **`feature/agente-supervisor`**.
>
> Para utilizarlos sitúate primero en esa rama:
>
> ```bash
> git checkout feature/agente-supervisor
> ```
>
> Si solo quieres leer la guía complementaria sin descargarla, puedes
> abrirla en GitLab seleccionando la rama
> `feature/agente-supervisor` en el selector de ramas del navegador
> de archivos.
>
> **Sobre la configuración del servidor.** Las salas que se crean en
> los tres modos del proyecto (`laboratorio`, `torneo` y `examen`)
> utilizan **configuración sin anonimato** en el Prosody de la
> asignatura, de modo que el JID real de los ocupantes es visible
> para todos. Aun así, las indicaciones que se dan en este documento
> ayudan a una **codificación robusta** del descubrimiento: el
> código deja de depender de esa configuración concreta y sigue
> funcionando frente a salas semi-anónimas (componente de pruebas,
> Prosody local sin actualizar, servidores XMPP de terceros, etc.).

---

## ¿De qué trata esta guía?

Varios alumnos están viendo, al arrancar su `main.py` en modo
`laboratorio` o `torneo`, una traza de error parecida a esta:

```
ERROR spade.behaviour — Exception running behaviour PeriodicBehaviour/DescubrirTablero:
'NoneType' object has no attribute 'split'

  File "behaviours/behaviours_jugador.py", line 41, in run
    "jid_real": muc.get_jid_property(self.agent.SALA_MUC, nick, "jid").split("/")[0],
                                                                       ^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'split'
```

Aparece **siempre** que un jugador intenta extraer el JID real de un
tablero descubierto en la sala MUC. Este documento explica:

1. Por qué falla, aunque el supervisor del profesor no esté arrancado.
2. Por qué el agente supervisor del profesor sí funciona.
3. Cómo escribir un descubrimiento robusto que no dependa de la
   configuración concreta del servidor XMPP.
4. Qué pasará el día del examen.

Está pensado para que el alumno entienda **el porqué**, no solo para
aplicar la receta.


## 1. Cómo funciona el descubrimiento en una sala MUC

La sala MUC es un mecanismo del estándar XMPP (XEP-0045) que permite
que varios agentes se reúnan bajo un mismo identificador (por ejemplo
`tictactoe@conference.localhost`). Dentro de la sala, cada ocupante
se identifica con un **apodo** (`tablero_mesa1`, `jugador_ana`, ...)
elegido al unirse. Cuando un agente entra o cambia de estado, el
servidor envía un **anuncio de presencia** (en la jerga del estándar,
una *stanza* de presencia) al resto de ocupantes para que todos
sepan quién está dentro.

Ese anuncio incluye un elemento `<item>` con tres datos relevantes:

| Dato          | Qué es                                            | ¿Visible para todos? |
|---------------|---------------------------------------------------|----------------------|
| `affiliation` | Categoría del ocupante en la sala — propietario, administrador, miembro o ninguna (en inglés *affiliation*: `owner`, `admin`, `member`, `none`). | Siempre              |
| `role`        | Rol activo del ocupante — moderador, participante o visitante (en inglés *role*: `moderator`, `participant`, `visitor`). | Siempre              |
| `jid`         | **JID real** del ocupante (`ana@dominio.com`)     | **Depende**          |

El JID real es la dirección XMPP "verdadera" del agente, fuera de la
sala. Y aquí está el matiz que provoca el error: **no siempre se
revela a todo el mundo**.


## 2. Salas anónimas, semi-anónimas y no anónimas

XEP-0045 contempla tres niveles de anonimato para una sala MUC. La
diferencia es **a quién muestra el servidor el JID real** de cada
ocupante:

| Tipo de sala     | El JID real es visible para...                  |
|------------------|-------------------------------------------------|
| No anónima       | Todos los ocupantes                             |
| **Semi-anónima** | **Solo moderadores y administradores**          |
| Anónima          | Nadie (ni siquiera los moderadores)             |

**El valor por defecto de Prosody (y de la mayoría de servidores
XMPP) es "semi-anónima"**. Esto significa que, salvo que se cambie
explícitamente la configuración, un alumno entrando como jugador no
verá el JID real de los demás ocupantes — el campo `<item jid="...">`
sencillamente **no aparece** en los anuncios de presencia que recibe.

Este es el origen del error. La función `get_jid_property` de slixmpp
busca el atributo `jid` del `<item>` y, si no lo encuentra, devuelve
`None`. Si el código del alumno hace directamente `.split("/")` sobre
ese `None`, el programa falla con el error que se ha mostrado al principio
de este documento.


## 3. ¿Por qué el supervisor del profesor sí funciona?

El servidor Prosody de la asignatura está configurado para asignar
automáticamente la categoría de administrador (`admin`) al JID
`supervisor@<dominio>` cada vez que entra en una sala (esto se
controla con la directiva `muc_room_default_admins` del fichero
`prosody.cfg.lua`). Esa categoría le da **dos privilegios** que un
jugador normal no tiene:

1. Ver el JID real de todos los ocupantes (porque las salas son
   semi-anónimas, no anónimas).
2. Reclamar la "propiedad" de la sala como supervisor único (la
   garantía S-02 documentada en `doc/ANALISIS_PROBLEMAS_TORNEO.md`).

Por eso el código del agente supervisor — al que tienes acceso en
`agentes/agente_supervisor.py` (rama `feature/agente-supervisor`) —
puede hacer cosas como:

```python
# Extracto de agente_supervisor.py, líneas 638-647
jid_real = ""
try:
    item_muc = presencia["muc"]["item"]
    if item_muc["jid"]:
        jid_real = str(item_muc["jid"])
except Exception:
    pass

jid_bare = jid_real.split("/")[0] if "/" in jid_real else jid_real
```

Fíjate en dos detalles importantes que conviene imitar:

- **Inicializa `jid_real` a cadena vacía**, no a `None`. Si el
  servidor no envía el atributo, el resto del código se topa con
  `""`, no con `None`, y así se preserva la integridad del agente.
- **Comprueba antes de dividir.** Si la cadena no contiene `/`, no
  llama a `split`; se queda con la cadena tal cual.

Este patrón funciona en cualquier sala (anónima, semi-anónima o no
anónima) **sin necesidad de privilegios especiales**.


## 4. ¿Es realmente imprescindible conocer el JID real?

Esta es la pregunta clave, y la respuesta es **no**.

El protocolo de juego (inscripción, turnos, informe) usa mensajes
directos FIPA-ACL, no mensajes a la sala. Para enviar un mensaje
directo a otro ocupante de la sala MUC tienes **dos opciones
válidas**:

### Opción A — Enviar al JID real

```python
mensaje = Message(to="tablero_mesa1@localhost")
```

Es lo que hace de forma natural el supervisor. **Requiere conocer el
JID real**, y por tanto solo funciona si la sala te lo revela
(supervisor) o si la has configurado como no anónima.

### Opción B — Enviar al JID MUC del ocupante

```python
mensaje = Message(to="tictactoe@conference.localhost/tablero_mesa1")
```

Es decir, `<sala>@<servicio>/<apodo>`. El servicio MUC actúa de
intermediario: recibe tu mensaje, busca en su tabla interna a qué
JID real corresponde ese apodo y se lo entrega. **Funciona en
cualquier tipo de sala**, porque el servidor sí conoce los JIDs
reales aunque no te los revele a ti.

La diferencia práctica para tu agente es que, cuando el destinatario
recibe el mensaje, **el campo `mensaje.sender` también será el JID
MUC** (`tictactoe@.../jugador_ana`), no el JID real. Mientras
respondas con `mensaje.make_reply()` — que copia automáticamente el
remitente y el destinatario, intercambiándolos — la conversación
encaja sin que tú tengas que preocuparte de traducir nada.

> **Conclusión didáctica:** el descubrimiento por sala MUC sirve para
> *encontrarse* (ver quién hay, con qué apodo y en qué estado);
> dialogar con un ocupante concreto se puede hacer perfectamente con
> el JID MUC, sin pedir privilegios al servidor.


## 5. Patrón defensivo recomendado

Cualquiera que sea la opción de envío que elijas, **tu rutina de
descubrimiento debe sobrevivir a una respuesta `None` del servidor**.
Sustituye este código frágil:

```python
# Frágil: revienta si la sala es semi-anónima.
ocupante = {
    "nick": nick,
    "jid_real": muc.get_jid_property(
        self.agent.SALA_MUC, nick, "jid",
    ).split("/")[0],
}
```

Por este patrón robusto:

```python
# Robusto: tolera cualquier configuración de la sala.
SALA_MUC = self.agent.SALA_MUC

jid_propiedad = muc.get_jid_property(SALA_MUC, nick, "jid")

if jid_propiedad is None:
    # Sala semi-anónima: no vemos el JID real, usamos el JID MUC
    # del ocupante. El servicio MUC enrutará nuestros mensajes.
    jid_destino = f"{SALA_MUC}/{nick}"
else:
    # Sala no anónima: tenemos el JID real, eliminamos el recurso
    # para quedarnos con la parte 'usuario@dominio'.
    cadena_jid = str(jid_propiedad)
    if "/" in cadena_jid:
        jid_destino = cadena_jid.split("/")[0]
    else:
        jid_destino = cadena_jid

ocupante = {
    "nick": nick,
    "jid_destino": jid_destino,
}
```

Tres ideas a retener:

1. **Nunca asumas que el servidor enviará un dato opcional.** Las
   tres líneas defensivas (`if jid_propiedad is None`, `if "/" in
   cadena_jid`) cuestan poco y blindan el código.
2. **No mezcles "no encontrado" con `None`.** Si tu código necesita
   un valor por defecto, usa la cadena vacía o un JID derivado del
   apodo, no `None`. Esto encaja con la directriz general de la
   asignatura de no dejar variables a `None` cuando hay un valor del
   dominio significativo.
3. **Recuerda el punto de retorno único.** El bloque `if/else`
   anterior asigna a una variable única `jid_destino` y la usa
   después. Si tu rutina lo necesita, calcula la asignación al
   principio y devuelve `jid_destino` al final del método.


## 6. ¿Y el día del examen?

El componente MUC dedicado al examen (`examen.sinbad2.ujaen.es`,
descrito en `doc/CAMBIOS_RAMA_ALUMNO_MUC_EXAMEN.md`) tiene una regla
distinta para la **creación de salas** — solo el supervisor puede
crearlas — pero **hereda los mismos parámetros de anonimato** que
las salas del componente general. En otras palabras: si tu código
del modo `laboratorio` o `torneo` falla porque asume que ve el JID
real, ese mismo código fallará el día del examen sobre la sala
`examen@examen.sinbad2.ujaen.es`. La causa es la misma: salas
semi-anónimas por defecto.

Para evitar que ningún alumno pueda quedarse atascado el día del
examen por este motivo, el profesor ha ajustado los dos componentes
MUC principales del Prosody de la asignatura para que sus salas se
creen con JIDs visibles para todos los ocupantes (esto es, **no
anónimas**). Un jugador puede leer el JID real de cualquier otro
ocupante sin necesidad de privilegios.

### El componente de pruebas semi-anónimo

Aun así, el servidor expone un **tercer componente MUC dedicado a
pruebas** llamado **`pruebas.sinbad2.ujaen.es`** que mantiene a
propósito la configuración semi-anónima por defecto de Prosody.
Existe únicamente para que verifiques que tu descubrimiento
defensivo funciona también cuando el JID real no es visible. Su
campo en `config/config.yaml` es
`xmpp.perfiles.servidor.servicio_muc_pruebas`.

| Componente                        | Modo         | Para qué sirve                                       |
|-----------------------------------|--------------|------------------------------------------------------|
| `conference.sinbad2.ujaen.es`     | NO ANÓNIMA   | Modos `laboratorio` y `torneo` del día a día.        |
| `examen.sinbad2.ujaen.es`         | NO ANÓNIMA   | Modo `examen` (creación restringida al supervisor).  |
| `pruebas.sinbad2.ujaen.es`        | SEMI-ANÓNIMA | Validación de tu patrón defensivo en condiciones hostiles. |

Para confirmar de un vistazo en qué modo está cada componente puedes
usar el script `scripts/comprobar_jid_visible_en_muc.py`, alojado
en la rama `feature/agente-supervisor` (ver guía
`GUIA_REVISION_DESCUBRIMIENTO_TABLEROS.md` §«Cómo verificar tus
cambios»).

**El alumno debe programar con la versión defensiva** y validarla
contra los dos modos. Por dos motivos:

- Mientras pruebas tu agente en tu propio Prosody local, o contra
  cualquier servidor XMPP de terceros, podrías encontrarte con la
  configuración por defecto (semi-anónima) y volverías al mismo
  error.
- La rúbrica de calidad de código (apartado 12 del README) valora
  manejo de errores, registro de trazas y robustez. Un programa que
  finaliza su ejecución con `AttributeError` ante una respuesta legítima del
  servidor es frágil por construcción, sin que importe que en el
  servidor concreto del examen no llegue a fallar.


## 7. Lista de comprobación

Antes de dar por cerrado el descubrimiento de ocupantes, repasa
estos puntos en el código de tu Agente Jugador (y, si aplica, del
Tablero):

- [ ] Mi rutina de descubrimiento **no llama a `.split` directamente**
      sobre el resultado de `get_jid_property`.
- [ ] Si `get_jid_property(..., "jid")` devuelve `None`, mi código
      construye un JID destino con `f"{SALA_MUC}/{nick}"` y sigue
      adelante sin lanzar excepción.
- [ ] No existe ninguna variable inicializada a `None` cuando hay un
      valor del dominio razonable (cadena vacía, JID derivado del
      apodo, etc.).
- [ ] Cuando envío un `REQUEST` de inscripción al tablero descubierto,
      uso indistintamente el JID real (si lo conozco) o el JID MUC
      (`sala/nick`); ambos son válidos.
- [ ] Cuando recibo una respuesta del tablero, uso `make_reply()` o
      copio explícitamente el `thread` y el `sender` para que la
      conversación se mantenga aunque el remitente fuera un JID MUC.
- [ ] Mi tabla de tableros descubiertos almacena `apodo`, `estado`
      MUC (`waiting`/`playing`/`finished`) y un JID destino
      reutilizable; **no** depende de tener siempre el JID real.
- [ ] He probado el descubrimiento contra mi Prosody local y la
      ejecución no genera `AttributeError` en ningún momento.


## 8. Referencias

- README del proyecto, sección 3.2 («Sala MUC: concepto y flujo»).
- XEP-0045 — Multi-User Chat: <https://xmpp.org/extensions/xep-0045.html>
  (en particular las secciones 7.2.5 «Anonymous Rooms» y 7.5
  «Sending a Message Privately»).
- `agentes/agente_supervisor.py`, método `_on_presencia_muc` (rama
  `feature/agente-supervisor`) — ejemplo de extracción defensiva
  del JID real desde un anuncio de presencia MUC (en jerga XMPP,
  una *stanza* de presencia).
- `doc/CAMBIOS_RAMA_ALUMNO_MUC_EXAMEN.md` — descripción del
  componente MUC dedicado al examen.
- `doc/ANALISIS_PROBLEMAS_TORNEO.md` — análisis general de los
  problemas detectados en el modo torneo y sus mitigaciones.
