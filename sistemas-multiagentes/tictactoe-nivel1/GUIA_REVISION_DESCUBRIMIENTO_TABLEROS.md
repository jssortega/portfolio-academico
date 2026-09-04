# Revisión del descubrimiento de tableros — deficiencias y mejoras

**Asignatura:** Sistemas Multiagente — Grado en Ingeniería Informática

**Universidad de Jaén** — Departamento de Informática

---

> **Dónde están los archivos auxiliares.**
>
> Esta guía vive en la rama principal del proyecto para facilitar su
> consulta, pero las **dos baterías de pruebas** que se describen
> (`tests/test_descubrimiento_tableros.py` y
> `tests/test_integracion_descubrimiento_y_juego.py`), los **scripts
> auxiliares** (`scripts/comprobar_jid_visible_en_muc.py`,
> `scripts/diagnosticar_sala_muc.py`, `scripts/limpiar_salas_muc.py`),
> el **agente supervisor del profesor** y el **componente MUC
> semi-anónimo de pruebas** (campo `servicio_muc_pruebas` del
> `config/config.yaml`) viven en la rama
> **`feature/agente-supervisor`**.
>
> Para ejecutar las pruebas o usar los scripts, sitúate primero en
> esa rama:
>
> ```bash
> git checkout feature/agente-supervisor
> ```
>
> Si solo quieres consultar el código de las pruebas sin descargarlo,
> puedes navegarlo en GitLab/GitHub seleccionando la rama
> `feature/agente-supervisor` en el selector del navegador de
> archivos.
>
> El **análisis de las deficiencias** (apartados 1 a 7) y la
> **versión robusta propuesta** son válidos sea cual sea la rama: no
> dependen de archivos auxiliares y se pueden aplicar al código del
> Agente Jugador del alumno directamente.
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

Un alumno entregó la siguiente versión del comportamiento periódico
(en SPADE, un `PeriodicBehaviour`) que descubre tableros en la sala
MUC. La traza de error que enviaba arrancaba con un `AttributeError`
y el contenido del comportamiento era este:

```python
class DescubrirTablero(PeriodicBehaviour):

    async def run(self):
        muc = self.agent.client.plugin['xep_0045']

        # Consultar la lista de agentes en la MUC
        nicks = muc.get_roster(self.agent.SALA_MUC)

        nuevo_diccionario = {}
        for nick in nicks:

            if nick.split("_")[0] == "tablero" and \
                    muc.get_jid_property(
                        self.agent.SALA_MUC, nick, "status",
                    ) == "waiting":

                nuevo_diccionario[nick] = {
                    "tipo_agente": nick.split("_")[0],
                    "jid_real": muc.get_jid_property(
                        self.agent.SALA_MUC, nick, "jid",
                    ).split("/")[0],
                }

        self.agent.listaTablerosMuc = nuevo_diccionario
```

El código **funciona en el caso ideal** (sala no anónima, tablero
con su presencia ya publicada como `waiting`) pero acumula varias
deficiencias que se van haciendo visibles a medida que se prueba en
condiciones reales: en torneo, en una sala recién creada, contra otros servidores XMPP. Esta guía las
analiza una a una y propone una versión defensiva.

El fichero `tests/test_descubrimiento_tableros.py` (rama
`feature/agente-supervisor`) acompaña a esta guía: ejecuta el
código del alumno y la versión propuesta sobre los mismos
escenarios, y deja constancia con comprobaciones (sentencias
`assert`) concretas del comportamiento de cada uno.

> **Lectura recomendada previa:**
> [`GUIA_DESCUBRIMIENTO_MUC.md`](GUIA_DESCUBRIMIENTO_MUC.md), que
> explica el anonimato de las salas MUC y el porqué de las distintas
> visibilidades del JID real en una sala XMPP.


## Resumen de las deficiencias detectadas

| #   | Deficiencia                                                  | Gravedad     |
|-----|--------------------------------------------------------------|--------------|
| 1   | Sin defensa frente a `None` en `get_jid_property(...,'jid')` | **GRAVE**    |
| 2   | Carrera con `status="waiting"` en el primer ciclo            | Media        |
| 3   | Reescribir el diccionario en cada ciclo borra el histórico   | Media        |
| 4   | `nick.split("_")[0]` poco expresivo                          | Baja         |
| 5   | Mezcla descubrimiento MUC con envío al JID real              | Baja         |
| 6   | Sin manejo de excepciones de borde                           | Media        |
| 7   | Tableros fantasma no se limpian                              | Media        |

Las deficiencias 1, 2 y 3 son las que debes corregir **antes del
día del examen**.


## Deficiencia 1 — Sin defensa frente a `None` (GRAVE)

```python
"jid_real": muc.get_jid_property(
    self.agent.SALA_MUC, nick, "jid",
).split("/")[0],
```

`get_jid_property` puede devolver `None` perfectamente legítimo: la
documentación de slixmpp lo dice y el código fuente lo confirma. La
biblioteca **no** garantiza que la propiedad pedida exista. En
particular:

- Si la sala MUC es semi-anónima (configuración por defecto de
  Prosody), un ocupante que no sea administrador ni propietario
  (`admin` ni `owner`) **nunca** ve el atributo `<item jid="…"/>`
  en los anuncios de presencia del resto. La propiedad `jid` queda
  sin establecer y `get_jid_property(..., 'jid')` devuelve `None`.
- Si el anuncio de presencia se procesó parcialmente o el ocupante
  todavía no ha enviado uno completo, también puede devolver `None`.

Encadenar `.split` directamente sobre el resultado convierte
cualquiera de estos casos en un `AttributeError` que rompe la
ejecución del comportamiento periódico.

**Mejora aplicable.** Compruebas el `None` antes de manipular y, si
no tienes JID real, te quedas con el JID MUC del ocupante
(`sala/apodo`), que el servicio MUC entrega como intermediario. No
necesitas el JID real para enviarle un mensaje a otro ocupante.

```python
jid_propiedad = muc.get_jid_property(SALA_MUC, nick, "jid")
if jid_propiedad is None:
    jid_destino = f"{SALA_MUC}/{nick}"          # JID MUC del ocupante
else:
    cadena_jid = str(jid_propiedad)
    if "/" in cadena_jid:
        jid_destino = cadena_jid.split("/")[0]
    else:
        jid_destino = cadena_jid
```

> **Importante didáctico.** Esta corrección encaja con la directriz
> general de la asignatura: *no devolver `None` ni propagarlo cuando
> hay un valor del dominio razonable*. El JID MUC del ocupante
> (`sala/apodo`) **siempre existe**, así que es el valor por defecto
> natural cuando el JID real no está disponible.


## Deficiencia 2 — Carrera con `status="waiting"` (MEDIA)

```python
muc.get_jid_property(SALA_MUC, nick, "status") == "waiting"
```

El campo `status` solo está en el diccionario interno de slixmpp
**si el ocupante ha enviado un anuncio de presencia con
`<status>waiting</status>` después de haber entrado en la sala**.
El anuncio inicial de entrada no lo incluye: el tablero envía dos
anuncios seguidos, uno de unión a la sala (sin `status`) y otro
después de ejecutar su `setup()` con `status="waiting"`.

Si la primera vuelta del comportamiento periódico cae entre ambos
anuncios, `get_jid_property(..., "status")` devuelve `None` y la
comparación `== "waiting"` falla. **El tablero queda fuera del
diccionario en esa vuelta**. Como el comportamiento es periódico,
la siguiente vuelta lo recoge — pero introduce un retraso oculto
en el descubrimiento equivalente al periodo del comportamiento
(5 s por defecto), que se nota especialmente cuando el jugador y
el tablero arrancan casi a la vez.

**Mejora aplicable.** Hay dos enfoques complementarios:

1. **Descubrimiento reactivo** (el preferido): registrar un
   manejador de eventos de presencia
   (`self.client.add_event_handler("presence", ...)`, en jerga
   slixmpp un *handler*) que actualice `self.agent.listaTablerosMuc`
   cada vez que llega un anuncio de presencia con
   `<status>waiting</status>`. Esto elimina la ventana de carrera y
   deja el comportamiento periódico solo como verificación
   esporádica. Es lo que hace el agente supervisor del profesor en
   `agentes/agente_supervisor.py`, método `_on_presencia_muc`
   (rama `feature/agente-supervisor`).

2. **Reducir el periodo del comportamiento** durante el examen
   (`intervalo_busqueda_muc: 2`), que limita la ventana de
   descubrimiento perdido.


## Deficiencia 3 — Reescribir el diccionario borra el histórico (MEDIA)

```python
nuevo_diccionario = {}
for nick in nicks:
    ...
self.agent.listaTablerosMuc = nuevo_diccionario
```

Cada vuelta **sustituye por completo** la lista de tableros
conocidos. Consecuencia: si el jugador ya envió un `REQUEST join` a
un tablero y está esperando respuesta, en la siguiente vuelta
reescribes la entrada y otro comportamiento del jugador la vuelve a
ver como "candidato nuevo", repitiendo el `REQUEST join`. Resultado:
el mismo tablero recibe varias inscripciones y el jugador puede
acabar con varias entradas duplicadas para una misma partida.

**Mejora aplicable.** Mantener tres conjuntos lógicos:

```python
self.agent.tableros_descubiertos = {}      # apodo -> jid_destino
self.agent.tableros_solicitados = set()    # apodos ya intentados
self.agent.tableros_resueltos = set()      # apodos con resultado final
```

En el descubrimiento periódico, *fusionas* sin sobreescribir ni
borrar entradas que estén en `solicitados` o `resueltos`. Cuando
otro comportamiento vaya a inscribirse, comprueba estos conjuntos
para no duplicar la solicitud. Y cuando termine la partida (aceptada
o rechazada), añade el apodo a `resueltos` para no volver a
intentarlo si reaparece en `waiting`.


## Deficiencia 4 — `nick.split("_")[0]` poco expresivo (BAJA)

```python
if nick.split("_")[0] == "tablero" and ...:
    ...
    "tipo_agente": nick.split("_")[0],
```

Aparte de invocar `split` dos veces sobre el mismo valor, el
patrón cuesta de leer. La intención queda más clara con
`startswith`:

```python
if nick.startswith("tablero_") and ...:
```

Adicionalmente, `tipo_agente: nick.split("_")[0]` es información
redundante: la presencia de la entrada en este diccionario ya
implica que es un tablero. Puedes eliminar el campo.


## Deficiencia 5 — Mezcla descubrimiento MUC con envío al JID real (BAJA)

El comentario que dejaste en el código es revelador:

> *Se ha quitado la barra de atrás (p.e. /3534546) que hacía SPADE
> porque parece que no funciona con eso*

Has descubierto empíricamente que enviar a un JID con recurso
específico (`tablero_mesa1@dominio/3534546`) no funciona, y como
solución has guardado solo la parte sin recurso, llamada en jerga
XMPP **bare JID** (`tablero_mesa1@dominio`). Funciona porque el
servidor XMPP, ante un mensaje a un JID sin recurso, lo entrega al
recurso conectado de mayor prioridad.

Pero hay una opción más limpia y conceptualmente más coherente
con el descubrimiento por sala MUC: **enviar al JID MUC del
ocupante** (`sala@conference.dominio/apodo`). El servicio MUC
actúa de intermediario y entrega el mensaje al ocupante actualmente
conectado bajo ese apodo, sin que tú tengas que conocer el JID
real ni preocuparte por su recurso.

**Mejora aplicable.** Guarda como destino del envío el JID MUC
del ocupante. Si más adelante necesitas el JID real (por ejemplo
para registrarlo en un fichero), úsalo solo cuando esté disponible
y no hagas depender el envío de él.


## Deficiencia 6 — Sin manejo de excepciones (MEDIA)

Si por cualquier motivo (slixmpp en estado raro, ocupante a medio
unirse, anuncio de presencia mal formado de un agente externo en
torneo) una de las llamadas a `get_jid_property` lanza una
excepción no esperada, el comportamiento periódico se interrumpe.
SPADE lo arranca de nuevo en la siguiente vuelta, pero la traza
original queda oculta y nunca llegas a saber qué falló.

**Mejora aplicable.** Un `try/except` defensivo con
`logger.exception` en el cuerpo del bucle: el ciclo continúa con
los demás ocupantes aunque uno falle, y el registro de eventos
(en jerga, el *log*) retiene la traza completa para diagnóstico.

```python
import logging
logger = logging.getLogger(__name__)

for nick in nicks:
    try:
        # ... lógica de descubrimiento de un nick ...
    except Exception:  # noqa: BLE001
        logger.exception(
            "Error procesando ocupante '%s' en %s", nick, SALA_MUC,
        )
        continue
```


## Deficiencia 7 — Tableros fantasma no se limpian (MEDIA)

Si un tablero pierde la conexión sin enviar un anuncio de salida
(`unavailable`), slixmpp puede mantenerlo en su lista interna de
ocupantes (`get_roster`) durante un rato. Tu jugador seguirá
intentando inscribirse en él. Combinado con la deficiencia 3
(reescritura total del diccionario), **el tablero fantasma vuelve
a aparecer "como nuevo" en cada vuelta** y el jugador entra en un
bucle de reintentos.

**Mejora aplicable.** Establecer un tiempo de espera (en jerga,
*timeout*) entre el descubrimiento y la respuesta: si tras N
segundos el `REQUEST join` enviado a un tablero no ha recibido
`AGREE` ni `REFUSE`, se marca el tablero como `resuelto-timeout` y
no se reintenta. Combinado con la mejora de la deficiencia 3, el
bucle queda cerrado.


## Versión robusta propuesta

Aplicando las mejoras 1, 4 y 6 (las que tocan la lógica del propio
comportamiento; las otras viven en módulos colaboradores), el
`DescubrirTablero` queda así:

```python
import logging

logger = logging.getLogger(__name__)


class DescubrirTablero(PeriodicBehaviour):

    async def run(self):
        muc = self.agent.client.plugin["xep_0045"]
        sala_muc = self.agent.SALA_MUC

        nicks = muc.get_roster(sala_muc)
        descubiertos = {}

        for nick in nicks:
            try:
                if not nick.startswith("tablero_"):
                    continue

                estado = muc.get_jid_property(sala_muc, nick, "status")
                if estado != "waiting":
                    continue

                jid_propiedad = muc.get_jid_property(
                    sala_muc, nick, "jid",
                )
                if jid_propiedad is None:
                    # Sala semi-anónima o presencia incompleta:
                    # usamos el JID MUC del ocupante como destino.
                    jid_destino = f"{sala_muc}/{nick}"
                else:
                    cadena_jid = str(jid_propiedad)
                    if "/" in cadena_jid:
                        jid_destino = cadena_jid.split("/")[0]
                    else:
                        jid_destino = cadena_jid

                descubiertos[nick] = {"jid_destino": jid_destino}
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Error procesando ocupante '%s' en %s",
                    nick, sala_muc,
                )
                continue

        # Fusionamos con los tableros ya conocidos en lugar de
        # sustituir el diccionario completo. La lógica de
        # 'no reintentar' se mantiene en otros conjuntos.
        for nick, datos in descubiertos.items():
            self.agent.listaTablerosMuc.setdefault(nick, datos)
```

Cambios respecto al código original:

- `nick.startswith("tablero_")` es más expresivo que `split("_")[0] == "tablero"`.
- Variable explícita `estado` para separar la consulta del filtro.
- Bloque `if jid_propiedad is None` que tolera salas semi-anónimas.
- Variable explícita `jid_destino` con punto de retorno único por iteración.
- `try/except` defensivo con `logger.exception`.
- Fusión con `setdefault` en lugar de sustitución total.


## Cómo verificar tus cambios — los dos bloques de pruebas asociadas

Esta guía viene con dos bloques de pruebas complementarias. La
primera es rápida y funciona sin red; la segunda arranca agentes
reales contra el servidor XMPP. Pasa las dos antes de dar por buena
tu implementación.

### Bloque 1 — Pruebas unitarias (rápidas, sin red)

> Recuerda: este archivo de pruebas vive en la rama
> `feature/agente-supervisor`. Cambia a esa rama con
> `git checkout feature/agente-supervisor` antes de ejecutarlo.

`tests/test_descubrimiento_tableros.py` contiene 14 pruebas
organizadas en tres clases. Usan un imitador (en inglés *mock*,
llamado en el código `FakeMUC`) que reemplaza al módulo `xep_0045`
de slixmpp. Cada prueba deja constancia, con sentencias `assert`,
del comportamiento del código del alumno y de la versión robusta
ante el mismo escenario:

```
TestCodigoAlumno
  - test_funciona_con_sala_no_anonima_y_status_publicado
  - test_revienta_si_la_sala_es_semi_anonima             ← deficiencia 1
  - test_descarta_tablero_que_aun_no_publico_status      ← deficiencia 2
  - test_descarta_tablero_con_status_distinto_de_waiting
  - test_filtra_apodos_que_no_son_tablero
  - test_split_sobre_apodo_sin_guion_no_explota          ← deficiencia 4
  - test_reescribe_diccionario_en_cada_ciclo             ← deficiencia 3

TestCodigoRobusto
  - test_funciona_con_sala_no_anonima
  - test_no_revienta_con_sala_semi_anonima               ← deficiencia 1 corregida
  - test_descarta_tablero_sin_status_publicado
  - test_filtra_apodos_que_no_son_tablero
  - test_jid_sin_recurso_se_devuelve_tal_cual

TestComparativaAlumnoVsRobusto
  - test_sala_semi_anonima_alumno_revienta_robusto_descubre
  - test_unico_tablero_oculto_arruina_descubrimiento_alumno
```

Ejecución:

```bash
pytest tests/test_descubrimiento_tableros.py -v
```

Tarda menos de 50 ms en total.

**Cómo usarlo en tu propio código.** Copia las funciones
`descubrir_alumno` y `descubrir_robusto` del fichero de pruebas y
adáptalas al `run()` de tu comportamiento. Después escribe tus
propias pruebas (puedes reutilizar `FakeMUC`) que verifiquen los
escenarios particulares de tu implementación.

### Bloque 2 — Prueba de integración (agentes reales, requiere XMPP)

> Recuerda: este archivo de pruebas vive en la rama
> `feature/agente-supervisor`. Cambia a esa rama con
> `git checkout feature/agente-supervisor` antes de ejecutarlo.

`tests/test_integracion_descubrimiento_y_juego.py` arranca dos
agentes SPADE reales contra el servidor XMPP del perfil activo y
verifica el flujo completo de un mini-juego. Es la **prueba de
aceptación** del patrón de comunicación anónimo: si pasa, demuestra
que el descubrimiento, la inscripción y un turno de partida
funcionan de extremo a extremo enviando los mensajes al JID MUC del
ocupante (`sala/apodo`), sin depender del JID real.

**Qué cubre la prueba.** Tres etapas, en orden:

1. **Descubrimiento.** Un `JugadorSimulado` se une a la sala MUC y
   ejecuta el descubrimiento periódico defensivo. Localiza al
   `TableroSimulado` y resuelve su `jid_destino` aplicando la
   versión robusta: si la sala revela el JID real, lo usa; si no,
   construye `f"{sala_muc}/{nick}"`.

2. **Inscripción según el protocolo FIPA Request** (README §4.1).
   El jugador envía `REQUEST {"action": "join"}` con los datos de
   cabecera (en jerga FIPA-ACL, *metadata*) canónicos:
   `ontology="tictactoe"`, `performative="request"`,
   `conversation-id="join"` y un identificador único de hilo de
   conversación (campo `thread`). El tablero responde con
   `AGREE {"action": "join-accepted", "symbol": "X"}`.

3. **Un turno según el protocolo FIPA Contract Net** (README §4.2).
   El tablero envía `CFP {"action": "turn", "active_symbol": "X"}`
   con el `thread` de la partida. El jugador responde
   `PROPOSE {"action": "move", "position": 4}` (posición central).
   El tablero confirma con `ACCEPT_PROPOSAL` y la prueba verifica
   que la posición recibida coincide.

Los `TableroSimulado` y `JugadorSimulado` son **agentes mínimos
escritos solo para la prueba**: no implementan ninguna máquina de
estados (en jerga SPADE, *FSM*) ni gestionan varios jugadores ni
varias partidas a la vez. Su único objetivo es ejercitar los
protocolos del README en condiciones controladas. Por simplicidad
usan un solo jugador (no se simula el oponente), con lo que se
omite la fase de `game-start` que requiere dos jugadores
inscritos.

**Ejecución.** Necesitas el servidor XMPP del perfil activo
arrancado y accesible. La prueba se ejecuta una vez por cada
componente MUC declarado en el perfil XMPP activo (en jerga de
pytest, está *parametrizada*). En el perfil `servidor` esto se
traduce en dos casos:

- `[no_anonimo]` → `servicio_muc` (`conference.sinbad2.ujaen.es`)
- `[semi_anonimo]` → `servicio_muc_pruebas` (`pruebas.sinbad2.ujaen.es`)

```bash
# Ejecución por defecto: ambos casos en una sola orden
pytest tests/test_integracion_descubrimiento_y_juego.py -v
```

Salida esperada (~35 s):

```
tests/test_integracion_descubrimiento_y_juego.py::test_…[no_anonimo] PASSED
tests/test_integracion_descubrimiento_y_juego.py::test_…[semi_anonimo] PASSED
```

**Por qué los dos casos son importantes:** el caso `no_anonimo`
valida el caso ideal (la sala te revela el JID real y tu código
lo usa). El caso `semi_anonimo` valida el caso defensivo: en
`pruebas.sinbad2.ujaen.es` el servidor **no envía** el atributo
`<item jid="…"/>` al jugador, así que `get_jid_property(...,"jid")`
devuelve `None`. Solo el patrón con tolerancia a `None` y un valor
alternativo (en jerga, *fallback*) al JID MUC del ocupante
(`sala/apodo`) sigue funcionando ahí. Si tu implementación pasa
los dos casos, demuestra estar lista para cualquier configuración
estándar de servidor XMPP, incluida la peor.

**Ejecución de un solo caso.** Para iterar sobre uno concreto sin
ejecutar el otro, usa la opción `-k` de pytest:

```bash
pytest tests/test_integracion_descubrimiento_y_juego.py -v \
    -k "no_anonimo"
pytest tests/test_integracion_descubrimiento_y_juego.py -v \
    -k "semi_anonimo"
```

**Ejecución contra un componente arbitrario.** Si quieres apuntar
la prueba a un componente MUC distinto sin tocar el `config.yaml`,
define la variable de entorno `SSMMAA_SERVICIO_MUC_TEST`. Cuando
está definida, **sustituye** los dos casos anteriores por uno solo
contra ese servicio:

```bash
SSMMAA_SERVICIO_MUC_TEST=conference.otro.servidor.es \
    pytest tests/test_integracion_descubrimiento_y_juego.py -v
```

**Ejecución cómoda dentro de la suite global.** El módulo lleva la
etiqueta (en pytest, *mark*) `integration` aplicada al fichero
entero. Eso permite separar fácilmente las pruebas con servidor de
las pruebas rápidas sin tener que recordar nombres de archivo:

```bash
# Solo las pruebas rápidas, sin red
pytest tests/ -m "not integration" -v

# Solo las pruebas que requieren servidor XMPP
pytest tests/ -m integration -v

# Todas a la vez (comportamiento por defecto, sigue funcionando)
pytest tests/ -v
```

Adicionalmente, el módulo comprueba al cargarse si el servidor del
perfil activo responde por TCP (mediante `pytest.mark.skipif`). Si
no responde, los dos casos se marcan como omitidos en lugar de
fallar con un error de conexión, así que `pytest tests/` siempre
es seguro aunque no tengas Prosody arrancado. Los detalles del
mecanismo se documentan en `tests/README.md`.

**Diagnóstico previo del modo de un componente.** Antes (o después)
de lanzar la prueba puedes confirmar manualmente cómo se está
comportando un componente concreto con el script de comprobación:

```bash
# Verifica que el componente principal sigue siendo no anónimo
python scripts/comprobar_jid_visible_en_muc.py --esperar no_anonima

# Verifica que el componente de pruebas sigue siendo semi-anónimo
python scripts/comprobar_jid_visible_en_muc.py --usar-pruebas \
    --esperar semi_anonima

# Apuntar a cualquier otro componente arbitrario
python scripts/comprobar_jid_visible_en_muc.py \
    --servicio-muc otro.componente.servidor.es
```

El script clasifica la sala observada como `no_anonima`,
`semi_anonima`, `anonima` o `inesperado`. Con `--esperar X` compara
con tu hipótesis y devuelve el código de salida correspondiente.

**Cómo extender la prueba a tu implementación.** La prueba usa
agentes simulados, pero los protocolos son los del README de la
asignatura. Puedes copiar el `JugadorSimulado` y reemplazar tu
`AgenteJugador` por él como banco de pruebas, o al revés:
sustituir el `TableroSimulado` por tu `AgenteTablero` para
verificar que el protocolo de inscripción y el primer turno
casan. La prueba ejecuta una sola partida, así que para probar
varias inscripciones consecutivas debes adaptarla.

**Si la prueba falla.** La salida indica en qué etapa falló:

| Si falla en…                              | Causa probable                                                                                                              |
|------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| `evento_tablero_descubierto.wait()`      | El descubrimiento no encuentra al tablero. Revisa el filtro `startswith("tablero_")` y la lectura del campo `status`.       |
| `evento_inscripcion_aceptada.wait()`     | El `REQUEST` no llega al tablero, o sus datos de cabecera (campo `conversation-id`) no coinciden con la plantilla esperada. |
| `evento_movimiento_recibido.wait()`      | El `CFP` no llega al jugador, o el filtrado por hilo de conversación (`thread`) no funciona.                                |
| Excepción de conexión inicial             | El servidor XMPP no es accesible o la cuenta no se autoregistra. Comprueba `config.yaml` y la conexión de red.              |


## Lista de comprobación

Antes de dar por cerrada la versión final del descubrimiento de
tableros:

- [ ] No queda ningún `.split` directo sobre el resultado de
      `get_jid_property`.
- [ ] El código tolera `get_jid_property(..., "jid")` devolviendo
      `None` y construye un destino válido (`sala/apodo`) sin lanzar
      excepción.
- [ ] El bucle de descubrimiento está envuelto en un `try/except`
      con registro de la traza para evitar que un fallo aislado
      interrumpa el procesado de los demás ocupantes.
- [ ] `nick.split("_")[0]` se ha sustituido por
      `nick.startswith("tablero_")` y el campo redundante
      `tipo_agente` se ha eliminado del diccionario de salida.
- [ ] El descubrimiento ya no sustituye el diccionario completo en
      cada vuelta; los tableros con inscripción en curso o ya
      resueltos no se reescriben.
- [ ] El comportamiento se ha probado contra al menos dos variantes
      de sala MUC (no anónima y semi-anónima) usando el script
      `scripts/diagnosticar_sala_muc.py` para confirmar el modo de
      anonimato real.
- [ ] La batería de pruebas unitarias
      `tests/test_descubrimiento_tableros.py` sigue pasando con tu
      nueva versión (14 pruebas).
- [ ] La prueba de integración
      `tests/test_integracion_descubrimiento_y_juego.py` pasa contra
      el servidor XMPP del perfil activo (1 prueba, ~20 s).
- [ ] (Opcional, recomendado) La prueba de integración pasa también
      contra el componente MUC semi-anónimo de pruebas
      (`SSMMAA_SERVICIO_MUC_TEST=pruebas.<dominio>` en el entorno).


## Referencias

Recordatorio: salvo el primer enlace y los recursos externos al final,
todos los archivos listados aquí viven en la rama
`feature/agente-supervisor`.

- [`GUIA_DESCUBRIMIENTO_MUC.md`](GUIA_DESCUBRIMIENTO_MUC.md) — guía
  base sobre anonimato MUC y patrón de descubrimiento defensivo
  (rama principal).
- `tests/test_descubrimiento_tableros.py` — pruebas unitarias que
  acompañan a este documento.
- `tests/test_integracion_descubrimiento_y_juego.py` — prueba
  de integración con agentes SPADE reales.
- `agentes/agente_supervisor.py`, método `_on_presencia_muc` —
  ejemplo de descubrimiento reactivo robusto sobre anuncios de
  presencia (en jerga XMPP, *stanzas* de presencia).
- XEP-0045 — Multi-User Chat: <https://xmpp.org/extensions/xep-0045.html>
- Documentación de slixmpp `XEP_0045.get_jid_property`:
  <https://slixmpp.readthedocs.io/en/latest/api/plugins/xep_0045.html>
