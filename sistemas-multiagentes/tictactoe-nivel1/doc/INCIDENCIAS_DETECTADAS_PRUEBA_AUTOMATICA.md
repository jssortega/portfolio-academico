# Incidencias detectadas en la prueba automática — rama `examen-ssmmaa`

Esta guía recoge las incidencias observadas al ejecutar los agentes de
los alumnos durante la prueba automática del examen. Algunas **impiden
que el sistema llegue siquiera a crear los agentes o a jugar una
partida**: el lanzador no consigue arrancar, o los tableros fallan en
cuanto arrancan. Otras permiten que el sistema arranque, pero
comprometen su funcionamiento interno: el código rechaza su propio
entorno de simulación, un comportamiento se interrumpe durante el
intercambio de mensajes, o un protocolo de comunicación —el
descubrimiento de tableros, el informe de partidas— no funciona como
se espera. En todos los casos el resultado es el mismo: el supervisor
no obtiene un registro fiable de las partidas y la entrega no puede
evaluarse.

Conviene leer estas incidencias junto con la guía
[`INTEGRACION_AGENTES_ALUMNO.md`](INTEGRACION_AGENTES_ALUMNO.md). La
rama del examen aporta una **infraestructura** —`main.py`, `utils.py`,
`config/` y `ontologia/`— que se integra **sin modificar**: las pruebas
asumen que se mantiene intacta. El alumno aporta sus agentes
(`agentes/agente_tablero.py` y `agentes/agente_jugador.py`) y los
módulos auxiliares que estos importan. La mayoría de estas incidencias
surge de no respetar esa frontera, y su corrección **nunca** consiste
en modificar la infraestructura del profesor.

Como el resto de guías de esta rama, este documento **no contiene
código para copiar**. Para cada incidencia describe *qué se observa*,
*por qué ocurre*, *cómo localizarla en el propio proyecto* y *qué tipo
de corrección la resuelve*. El objetivo es que cada alumno reconozca su
caso y lo repare por sus propios medios: comprender la incidencia forma
parte de la evaluación.

La mayoría de estas incidencias aparece en los primeros segundos de
ejecución; alguna surge algo más tarde, al enviarse los primeros
mensajes. Por eso la recomendación general es **arrancar el sistema
completo y leer con atención el registro de principio a fin** antes de
dar por terminada la entrega.


## Incidencia 1 — Un atributo de configuración que el agente nunca crea

### Síntoma

En el registro del agente tablero aparece un mensaje equivalente a:

> Error en EstadoInscripcion: 'AgenteTablero' object has no attribute
> 'config_sistema'

El tablero no llega a aceptar jugadores. En consecuencia, ninguna
partida empieza y el supervisor no recibe ningún informe.

### Causa

Un comportamiento del tablero —el del estado de inscripción— lee un
dato a través de `self.agent`: un atributo con la configuración del
sistema. El lanzador `main.py`, que es infraestructura del profesor,
inyecta en cada agente el perfil de conexión y los parámetros propios
del agente; **no** inyecta ningún atributo con la configuración del
bloque `sistema`. Por tanto, cualquier otro atributo que un
comportamiento espere encontrar en `self.agent` debe haberlo creado el
propio agente.

La incidencia se produce cuando el agente tablero no inicializa ese
atributo en su constructor. El comportamiento intenta leerlo, el
atributo no existe, y la ejecución se interrumpe. Es habitual que el
agente jugador sí lo inicialice y el tablero no: esa **asimetría**
dentro del propio código del alumno es la causa.

### Cómo localizarla

Hay que revisar el constructor (`__init__`) de las dos clases de agente
y comparar cómo tratan ese atributo: con frecuencia el jugador lo
inicializa y el tablero no. La regla de comprobación: todo atributo que
los comportamientos lean de `self.agent`, y que no sea el perfil de
conexión ni los parámetros del agente, debe estar creado por el propio
agente, porque el lanzador no lo proporciona.

### Cómo corregirla

El agente debe inicializar ese atributo él mismo, en su constructor,
con un valor por defecto razonable —tal y como ya hace, probablemente,
el otro agente del proyecto—. No debe esperarse que `main.py` lo
proporcione: `main.py` es infraestructura del profesor, se integra sin
modificar e inyecta únicamente el perfil de conexión y los parámetros
del agente. La corrección, por tanto, está siempre en el código del
agente, nunca en el lanzador.


## Incidencia 2 — Se importa una función que no existe

### Síntoma

El sistema no llega a arrancar. En cuanto el lanzador intenta importar
las clases de los agentes, se detiene con un mensaje equivalente a:

> cannot import name '<nombre_de_funcion>' from 'utils'

Ningún agente se crea.

### Causa

Varios comportamientos importan desde el módulo `utils` una función
auxiliar que ese módulo no define. `utils.py` es infraestructura del
profesor: contiene la factoría de agentes y se integra **sin
modificar**. Las funciones auxiliares propias del alumno —registro de
mensajes, ayudas varias— no residen en `utils.py`, sino en los módulos
que el alumno añade junto a sus agentes.

La incidencia aparece cuando el alumno escribe una función auxiliar
propia pero la importa desde `utils` —donde no está— en lugar de
hacerlo desde su propio módulo; o bien cuando esa función se invoca en
varios comportamientos pero nunca se llegó a definir.

### Cómo localizarla

El mensaje de error indica el nombre que no se encuentra y el módulo
desde el que se intenta importar. Si ese módulo es `utils` —u otro
fichero de infraestructura— y la función es una ayuda propia del
alumno, la importación apunta al lugar equivocado. Conviene revisar
todos los comportamientos que invocan esa función para confirmar que se
trata de código del alumno y para entender qué se espera de ella.

### Cómo corregirla

Las funciones auxiliares propias deben residir en un módulo del alumno,
uno de los que acompañan a la carpeta `agentes/`. La corrección
consiste en definir la función en un módulo propio —de forma coherente
con cómo la invocan los comportamientos— y hacer que todas las
importaciones apunten a ese módulo. **No** debe añadirse la función a
`utils.py`: ese fichero es infraestructura del profesor, se integra
intacto, y modificarlo rompe la coherencia con las pruebas, que asumen
su contenido.


## Incidencia 3 — La modalidad del examen no se resuelve con su submodalidad

### Síntoma

El sistema se detiene al generar los agentes, con un mensaje
equivalente a:

> Modalidad 'examen' no definida en agents.yaml. Modalidades
> disponibles: ['laboratorio', 'torneo', 'examen_grupo',
> 'examen_individual']

No se crea ningún agente.

### Causa

El examen tiene dos submodalidades —grupo e individual—. La
infraestructura del profesor está preparada para ello: el fichero
`config/agents.yaml` define las entradas `examen_grupo` y
`examen_individual`, y el módulo `config/configuracion.py` combina la
modalidad `examen` con la submodalidad declarada por el alumno para
formar la clave correcta antes de consultar `agents.yaml`.

La incidencia aparece cuando el proyecto del alumno **no tiene
integrada la versión vigente de `config/`**: conserva un
`configuracion.py` —o un `agents.yaml`— anterior a la separación en
submodalidades. Ese código antiguo busca en `agents.yaml` una entrada
llamada `examen` por sí sola, que ya no existe, y se detiene. El propio
mensaje lo pone de manifiesto: las entradas disponibles llevan el
sufijo de la submodalidad.

### Cómo localizarla

La lista de modalidades disponibles que muestra el mensaje de error
contiene `examen_grupo` y `examen_individual`, pero no `examen`. Esa es
la señal de que la carpeta `config/` del proyecto está desactualizada:
la versión vigente que aporta la rama del examen ya resuelve la
submodalidad.

### Cómo corregirla

`config/` es infraestructura del profesor y se integra sin modificar.
La corrección consiste en **integrar la versión vigente de `config/`**
—`configuracion.py` y `agents.yaml`— que aporta la rama del examen, en
sustitución de cualquier copia antigua. No se trata de parchear el
código antiguo, sino de adoptar el actual, que ya compone la clave
`examen_<submodo>` correctamente.


## Incidencia 4 — El constructor del agente no acepta los parámetros de la factoría

### Síntoma

Al arrancar, cada intento de crear un agente falla con un mensaje
equivalente a:

> Error al arrancar agente '...': AgenteTablero.__init__() got an
> unexpected keyword argument 'port'

—y el equivalente para el agente jugador—. Ningún agente se crea.

### Causa

Los agentes se crean mediante la factoría `crear_agente` de `utils.py`,
que invoca el constructor con la firma de SPADE 4.x: `jid`, `password`,
`port` y `verify_security`. El contrato de integración es explícito: si
el alumno redefine `__init__` en su clase de agente, debe aceptar esa
misma firma; si no lo redefine, hereda el de `Agent` y la condición se
cumple por sí sola.

La incidencia aparece cuando el alumno redefine `__init__` con una
firma más estrecha —por ejemplo, sin `port`—. Cuando la factoría le
pasa el puerto, el constructor encuentra un argumento que no declara y
la llamada se rechaza.

### Cómo localizarla

El mensaje nombra el argumento sobrante (`port`) y la clase afectada.
Hay que comparar la firma del `__init__` redefinido por el alumno con
la firma de SPADE 4.x que la factoría utiliza: `jid`, `password`,
`port` y `verify_security`.

### Cómo corregirla

Caben dos soluciones, ambas en el código del alumno
(`agentes/agente_tablero.py` y `agentes/agente_jugador.py`). La más
sencilla: no redefinir `__init__` y heredar el de `Agent`. Si el agente
necesita un constructor propio, este debe aceptar la firma completa de
SPADE 4.x y propagarla a la clase base, de modo que admita `port` y
cualquier otro parámetro de conexión. El contrato de integración recoge
esta condición; conviene consultar la guía
[`INTEGRACION_AGENTES_ALUMNO.md`](INTEGRACION_AGENTES_ALUMNO.md).


## Incidencia 5 — Se asigna al cuerpo de un mensaje un valor que no es texto

### Síntoma

Con el sistema ya en marcha, un comportamiento se detiene con un
mensaje equivalente a:

> TypeError: 'body' MUST be a string

Suele ser el comportamiento que responde al supervisor con el informe
de la partida: al interrumpirse, el supervisor no recibe ese informe y
la partida no consta como evaluada.

### Causa

SPADE exige que el cuerpo de un mensaje (`body`) sea una **cadena de
texto**. La ontología del proyecto (`ontologia/ontologia.py`,
infraestructura del profesor) ofrece los constructores `crear_cuerpo_*`:
cada uno **empareja** la performativa FIPA-ACL con el cuerpo del
mensaje y devuelve ambos juntos. El cuerpo es texto; la estructura que
lo empareja con la performativa, no.

La incidencia aparece cuando el alumno asigna a `body` el resultado
completo de uno de esos constructores —la estructura que empareja
performativa y cuerpo— en lugar de extraer de él solo el cuerpo.
Asignar a `body` cualquier valor que no sea una cadena de texto produce
el mismo error.

### Cómo localizarla

La traza de error señala la línea exacta donde se asigna el `body`.
Hay que comprobar de dónde procede el valor: si es el resultado de un
constructor `crear_cuerpo_*`, se está usando entero cuando solo se
necesitaba su campo de cuerpo. Resulta útil comparar con los puntos del
agente donde un constructor de la ontología se usa correctamente: ahí
se verá que del resultado se toman por separado la performativa —para
la metadata— y el cuerpo —para `body`—.

### Cómo corregirla

De lo que devuelve un constructor `crear_cuerpo_*` hay que tomar cada
parte por su sitio: la performativa, para la metadata del mensaje; el
cuerpo —que ya es una cadena de texto—, para `body`. La ontología es
infraestructura del profesor y se utiliza, no se modifica: la
corrección está en cómo el agente del alumno aprovecha lo que esos
constructores devuelven.


## Incidencia 6 — Una comprobación que rechaza el entorno de simulación

### Síntoma

En modalidad `examen`, el sistema se detiene en cuanto arranca. El
mensaje procede del propio `main.py` del proyecto y es equivalente a:

> La modalidad 'examen' debe ejecutarse contra el servidor de la
> asignatura..., pero el perfil XMPP activo es 'local'

No se crea ningún agente.

### Causa

El mensaje procede de una comprobación situada en `main.py`. `main.py`
es infraestructura del profesor y se integra sin modificar; la versión
vigente que aporta la rama del examen admite tanto el servidor oficial
como el perfil `local` de simulación, porque `local` es un entorno
previsto y documentado para ensayar el examen antes de la prueba.

La incidencia aparece cuando el proyecto del alumno **conserva un
`main.py` anterior** a esa previsión, que solo admite el perfil
`servidor` y aborta ante cualquier otro. Al ejecutarse en el entorno de
simulación, ese `main.py` desactualizado rechaza el perfil `local` y
detiene el sistema.

### Cómo localizarla

El mensaje no procede de una biblioteca, sino del propio `main.py` del
proyecto. Si ese `main.py` aborta cuando la modalidad es `examen` y el
perfil es `local`, se trata de una versión anterior a la actual: la
versión vigente no impone esa restricción.

### Cómo corregirla

`main.py` es infraestructura del profesor y se integra sin modificar.
La corrección consiste en **integrar la versión vigente de `main.py`**
que aporta la rama del examen, en sustitución de la copia antigua. No
se trata de editar la comprobación del `main.py` desactualizado, sino
de adoptar el `main.py` actual, que ya contempla el perfil `local`.


## Incidencia 7 — El tablero rechaza el informe de una partida que sí ha finalizado

### Síntoma

El supervisor registra contra el tablero una incidencia de tipo
**error** equivalente a:

> El tablero rechazó la solicitud de informe (motivo: partida no
> finalizada) en el primer intento y sin haber entregado ningún
> informe previo

El sistema arranca y juega partidas, pero algunas partidas terminadas
se quedan **sin informe**: el supervisor las solicita y el tablero las
rechaza, pese a que la partida sí había finalizado.

### Causa

Cuando un tablero anuncia —mediante su presencia— que una partida ha
finalizado, el supervisor le solicita el informe de esa partida; el
tablero debe responder con el informe (`INFORM`). El rechazo
(`REFUSE`, motivo «no finalizada») solo está previsto para una partida
que **realmente** no ha terminado.

La incidencia aparece cuando el comportamiento del tablero que atiende
esa solicitud no es lo bastante robusto. Los patrones habituales:

- **Solo conserva la última partida**: el tablero guarda únicamente el
  informe de la partida más reciente. Si dos partidas terminan entre
  dos solicitudes del supervisor, la anterior ya no se puede informar.
- **Responde una sola vez**: el tablero marca cada informe como «ya
  enviado» y, ante una segunda solicitud de esa misma partida,
  responde con un rechazo en lugar de volver a enviar el informe.
- **Da por entregado un envío que pudo perderse**: el tablero marca el
  informe como enviado sin tener constancia de que el supervisor lo
  recibió.

Bajo carga del servidor las solicitudes del supervisor pueden llegar
con retraso o repetirse —el supervisor reintenta cuando no recibe
respuesta a tiempo—; cualquiera de esos patrones hace entonces que el
tablero rechace una solicitud legítima. El motivo «partida no
finalizada» es además **engañoso**: la partida sí terminó; el tablero
emite un rechazo genérico mal etiquetado.

### Cómo localizarla

Hay que revisar el comportamiento del tablero que atiende la solicitud
`game-report` del supervisor y comprobar tres cosas: si conserva el
informe de **todas** las partidas finalizadas o solo el de la última;
si puede responder **más de una vez** a la misma solicitud; y si
distingue de verdad entre una partida no finalizada y una partida
finalizada cuyo informe ya envió. Un comportamiento que solo responde
una vez, o solo sobre la partida más reciente, es la causa.

### Cómo corregirla

El comportamiento que atiende el `game-report` debe ser **idempotente
y completo**:

- Conservar de forma recuperable el informe de **cada** partida
  finalizada, no solo el de la última.
- Responder **siempre** con el `INFORM` a una solicitud sobre una
  partida finalizada: reenviar un informe ya entregado es inofensivo y
  es lo que el supervisor espera; una solicitud repetida nunca debe
  producir un rechazo.
- Reservar el rechazo **exclusivamente** para una partida que aún no
  ha terminado.

El tablero anuncia el fin de una partida con su presencia; a partir de
ese instante debe ser capaz de informar de ella de forma fiable,
tantas veces como se le pregunte.


## Incidencia 8 — El jugador no descubre de forma fiable los tableros disponibles

### Síntoma

El supervisor registra advertencias de inactividad: un tablero que
permanece en estado `waiting` sin progresar y jugadores que nunca
aparecen en ningún informe de partida. El sistema arranca y algunas
partidas se juegan, pero **uno o varios tableros no llegan a reunir
dos jugadores** y se quedan detenidos, mientras varios jugadores no
entran en ninguna partida —pese a que en la sala hay jugadores de
sobra para llenar todos los tableros—.

### Causa

Cada jugador descubre en la sala MUC los tableros disponibles y se
inscribe en ellos. El censo de ocupantes de la sala MUC es la fuente
fiable de qué tableros existen. La incidencia aparece cuando el
jugador, tras obtener del censo la lista de tableros, **añade una
segunda condición** antes de inscribirse: exige que una consulta
aparte —sobre la presencia de ese tablero— devuelva un contacto en un
estado determinado.

El censo de la sala y el subsistema de presencia son **dos canales
distintos**. El registro de presencia de un ocupante concreto se
puebla de forma **asíncrona**, a medida que llega —si llega— la
notificación de presencia de ese ocupante. Si todavía no se ha
poblado, la consulta no devuelve nada y el jugador **descarta en
silencio** un tablero que está presente en la sala y esperando
jugadores: no le envía la solicitud de inscripción, no deja constancia
y no lo reintenta. El resultado es que cada jugador acaba con una
**vista parcial y congelada** de los tableros: algunos tableros no
reciben inscripciones suficientes y se quedan detenidos, y algunos
jugadores no llegan a jugar ninguna partida. La abundancia de
jugadores no corrige el problema: un tablero disponible al que el
código ha hecho invisible nunca recibe la inscripción.

### Cómo localizarla

Hay que revisar el comportamiento del jugador encargado de buscar
tablero. Conviene comprobar dos cosas: si obtiene la lista de tableros
del **censo de la sala MUC**; y si, antes de inscribirse, exige además
**alguna condición obtenida por otra vía** (una consulta de presencia,
el estado de un contacto, etc.). Si la inscripción depende de algo
distinto del censo de la sala —y ese algo es un canal aparte que se
actualiza de forma asíncrona—, ese filtro adicional es la causa. En el
registro, el síntoma es un tablero que figura en la sala y permanece
en `waiting` mientras solo recibe solicitudes de un jugador, o de
ninguno, al tiempo que otros tableros sí juegan.

### Cómo corregirla

El censo de ocupantes de la sala MUC es la fuente de verdad fiable de
qué tableros existen. El jugador debe **intentar la inscripción
directamente** sobre los tableros de ese censo y dejar que sea **el
propio tablero quien responda**: acepta la inscripción si tiene plaza,
o la rechaza si está lleno o ya jugando. La respuesta del tablero es
la autoridad sobre su disponibilidad. El jugador no debe condicionar
la inscripción a una consulta aparte que se puebla de forma asíncrona
y que puede hacer invisible un tablero perfectamente disponible.


## Una lección común

Estas incidencias son distintas, pero comparten una misma raíz: **el
código del alumno no encaja con lo que la rama del examen espera de
él**, ya sea con la infraestructura que debe integrar o con los
protocolos por los que se comunica.

La rama del examen aporta una infraestructura —`main.py`, `utils.py`,
`config/` y `ontologia/`— que se integra **sin modificar**: las pruebas
asumen que se mantiene intacta. El alumno aporta sus agentes
(`agentes/agente_tablero.py` y `agentes/agente_jugador.py`) y los
módulos auxiliares que estos importan, y es responsable de que esos
agentes respeten los protocolos de la ontología. Cada incidencia surge
de romper ese encaje en algún punto:

- El agente depende de un atributo que la infraestructura no inyecta,
  en lugar de crearlo él mismo (Incidencia 1).
- Una función auxiliar propia se importa desde un módulo de
  infraestructura, donde no está, en lugar de desde un módulo del
  alumno (Incidencia 2).
- Se conserva una copia antigua de `config/` en lugar de integrar la
  versión vigente (Incidencia 3).
- El constructor del agente no respeta la firma que la factoría de la
  infraestructura utiliza (Incidencia 4).
- Se aprovecha mal lo que devuelven los constructores de la ontología
  (Incidencia 5).
- Se conserva una copia antigua de `main.py` en lugar de integrar la
  versión vigente (Incidencia 6).
- El comportamiento que atiende el protocolo de informe rechaza
  solicitudes legítimas de partidas ya finalizadas (Incidencia 7).
- El jugador no descubre de forma fiable los tableros disponibles y
  deja sin inscripciones a tableros que sí podrían jugar (Incidencia 8).

Dos reglas evitan todas ellas. Primera: la infraestructura del profesor
se integra **en su versión vigente y sin modificar**; si algo de ella
parece que hay que cambiar, casi siempre lo que falta es integrar su
versión actual. Segunda: el código del alumno debe **respetar el
contrato** que la rama del examen define —qué atributos se inyectan en
el agente, qué firma tiene la factoría, qué devuelven los constructores
de la ontología y cómo deben responder los agentes a cada protocolo—.
La guía [`INTEGRACION_AGENTES_ALUMNO.md`](INTEGRACION_AGENTES_ALUMNO.md)
detalla ese contrato.

Conviene además recordar que el sistema se evalúa **bajo carga**:
varios agentes comparten el servidor, los mensajes se retrasan y las
solicitudes pueden repetirse. Un comportamiento correcto en una prueba
aislada puede fallar en cuanto el entorno se satura. Por eso, antes de
entregar, conviene arrancar el sistema completo —a ser posible con
varios agentes a la vez— y leer el registro de principio a fin: la
mayoría de estas incidencias se manifiesta en los primeros segundos;
la del protocolo de informe, algo más tarde, cuando las partidas
empiezan a terminar.
