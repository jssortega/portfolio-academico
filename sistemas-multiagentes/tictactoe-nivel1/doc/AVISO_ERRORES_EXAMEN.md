# Utilidades del modo examen para los agentes del alumno

El material del examen incluye **dos utilidades** que dejan a los
agentes del alumno preparados para dos momentos puntuales de la
prueba, sin que el alumno tenga que escribir lógica nueva. Las dos
residen en `utils.py`:

| Momento | Qué ocurre | Utilidad | Carácter |
|---------|-----------|----------|----------|
| **Inicio** | Los agentes arrancan antes de que el supervisor exista; el servidor rechaza la unión a la sala con un error. | `registrar_aviso_errores_examen` | Recomendado: hace visible un error que de otro modo aparece como un tiempo de espera sin causa. |
| **Fin** | El profesor detiene el supervisor; este expulsa a los agentes y destruye la sala. | `registrar_cierre_ordenado_examen` | **Opcional**: detiene los agentes con `stop()` cuando llega la presencia de cierre. |

Cuando el alumno arranca sus agentes con el `main.py` de la rama
del examen, la factoría `crear_agente()` deja las dos utilidades
**instaladas automáticamente**, sin que haya que añadir ninguna
línea a los agentes. La sección «Fin del examen» de este documento
describe la utilidad de cierre y cómo integrarla a mano para los
alumnos que prefieran no usar la factoría.

## Aviso del error amigable (inicio del examen)

Cuando los agentes se arrancan en modo examen **antes** de que el
supervisor del profesor esté activo, el servidor rechaza la unión a la
sala y devuelve un mensaje explicativo con la marca `[Examen]`. Esta
parte explica cómo conseguir que ese mensaje **aparezca en la
consola** en lugar de quedar como un *tiempo de espera agotado
(timeout)* silencioso.


## En resumen

| Forma de arranque de los agentes | Qué hay que hacer |
|---------------------------|----------------------|
| Con el `main.py` del examen (caso habitual) | **Nada.** El aviso ya está instalado. |
| Lanzando los agentes de forma manual, sin la factoría | Una línea en el `setup()` de cada agente (véase «Caso B»). |

El fundamento se expone al final, en «¿Por qué hace falta?». Para un
uso directo, basta con los pasos siguientes.


## Caso A — Uso del `main.py` del examen (recomendado)

**No es necesario hacer nada ni escribir ninguna línea.** El lanzador
crea los agentes con la factoría `crear_agente()` de `utils.py`, y esa
factoría deja el aviso instalado automáticamente en cada agente.

Para comprobarlo, se arranca el sistema en modo examen sin que el
supervisor esté activo:

```bash
python main.py
```

Si la sala todavía no existe, aparecerá en la consola el mensaje
descrito en «Qué se ve cuando funciona».


## Caso B — Arranque de los agentes sin la factoría

Solo cuando los agentes se lanzan de forma manual (sin pasar por
`crear_agente()`) es necesario registrar el aviso manualmente. Son
**dos pasos**, sin escribir lógica nueva:

1. **Importar la función** al principio del fichero del agente:

   ```python
   from utils import registrar_aviso_errores_examen
   ```

2. **Invocarla una vez en el `setup()`** del agente, justo después de
   registrar el complemento (*plugin*) MUC y **antes** de la unión
   (*join*) a la sala:

   ```python
   async def setup(self):
       self.client.register_plugin("xep_0045")

       # Deja el agente preparado para mostrar el mensaje del modo examen.
       registrar_aviso_errores_examen(self, self.SALA_MUC)

       # ... a continuación, la unión MUC habitual ...
   ```

El orden es relevante: si la sala rechaza la unión, el servidor
responde de inmediato, por lo que el manejador debe estar registrado
**antes** de la unión.

> **No deben combinarse los dos casos.** Al usar el `main.py` del
> examen, el aviso ya está puesto: no es necesario —ni conveniente—
> añadir además la línea del Caso B, pues el mensaje se registraría
> dos veces.

El parámetro que se pasa a la función es el JID completo de la sala a
la que el agente intenta unirse. Se obtiene del atributo empleado para
la unión (`self.SALA_MUC` en los agentes del curso) o de la
configuración (`config_xmpp["sala_muc_completa"]`, que el lanzador ya
construye con el componente y la sala correctos del modo examen).

Se dispone de un agente de ejemplo mínimo, con la línea ya puesta y
comentada, en `doc/ejemplo_agente_con_aviso_examen.py`.


## Qué se ve cuando funciona

En lugar de un tiempo de espera agotado sin causa aparente, en la
consola aparece un error como este:

```
ERROR utils — El servidor rechazó la unión a la sala
'examen@examen.sinbad2.ujaen.es' (condición XMPP: not-allowed).
[Examen] No puedes crear ni unirte a la sala 'examen'. Solo el
supervisor del profesor (administrador del servidor) está autorizado a
crear salas en este servidor mientras dura el modo examen. Espera a
que el profesor arranque su supervisor (python supervisor_main.py
--modo examen) y vuelve a lanzar tus agentes.
```

Si el servidor devuelve el error pero —por cualquier motivo— no
incluye el `<text>` explicativo, el aviso registra al menos la
condición XMPP (`not-allowed`, `item-not-found`, `forbidden`…), de modo
que siempre se dispone de un diagnóstico.


## ¿Por qué hace falta?

En el modo examen, el componente MUC dedicado del servidor de la
asignatura (`examen.<dominio>`) tiene la directiva
`restrict_room_creation = "admin"`: **solo el supervisor del profesor
puede crear las salas**. Si los agentes del alumno arrancan **antes**
que el supervisor, su intento de unirse a la sala recibe un error de
presencia con una condición XMPP estándar (`item-not-found`,
`not-allowed` o `forbidden`).

Para que ese error no resulte críptico, el servidor incorpora el
módulo `mod_examen_friendly_error`, que **añade al error un elemento
`<text>`** con la marca `[Examen]` y una explicación en español.

El problema es que ese mensaje **solo se percibe si el agente lo
escucha**. El mecanismo consta de dos mitades:

| Mitad | Responsable | Estado |
|-------|-------------|--------|
| Inyectar el `<text>` explicativo en el error | Servidor (`mod_examen_friendly_error`) | Ya desplegado |
| Recibir el error de presencia y **mostrar** ese `<text>` | El agente del alumno | Lo cubre el material de apoyo |

Si el agente se une a la sala «a ciegas» —envía la presencia de unión
y no registra ningún manejador para el evento `presence_error`—, la
*stanza* de error llega al cliente XMPP pero se descarta en silencio.
El agente solo percibe un tiempo de espera agotado sin causa aparente,
fácil de confundir con un fallo de credenciales, de red o del propio
código.

Para evitarlo, el material de apoyo incluye en `utils.py` la función
`registrar_aviso_errores_examen`, que registra ese manejador. Y la
factoría `crear_agente()` la invoca automáticamente en el momento
adecuado del ciclo de vida del agente (el punto de enganche, *hook*,
posterior a la conexión y anterior al `setup()`), de modo que en el
flujo normal del examen no es necesario hacer nada.


## Fin del examen — cierre ordenado de los agentes (utilidad opcional)

Cuando el profesor detiene su Agente Supervisor al terminar la prueba,
este realiza una limpieza ordenada: **expulsa** a los agentes de las
salas del examen y **destruye** dichas salas, de modo que la siguiente
ejecución del supervisor parta de salas nuevas, sin ocupantes ni estado
residual.

Esa limpieza **no pretende provocar fallos** en los agentes del
alumno. Pero si los agentes no detectan que el examen ha terminado:

- los comportamientos que esperan mensajes de la sala quedarían
  **esperando indefinidamente** algo que ya no va a llegar;
- los que intenten **enviar a la sala** o consultar la lista de
  contactos (*roster*) MUC tras la expulsión recibirían errores del
  servidor que, si no se gestionan, provocan una **finalización
  abrupta** por excepción;
- y, en cualquier caso, el agente SPADE **no se detendría por sí
  solo**: quedaría activo sin función.

Para evitarlo, `utils.py` incluye la utilidad
`registrar_cierre_ordenado_examen`. El servidor comunica el fin del
examen con una presencia `unavailable` que lleva un código de estado
MUC: **307** (expulsión de la sala) o **332** (la sala ha sido
destruida). La utilidad escucha esas presencias y, cuando reconoce que
es **el propio** agente el que sale de la sala del examen, registra un
mensaje informativo y detiene el agente con `agente.stop()` — una
**finalización ordenada**.

> **No es obligatoria.** El alumno puede prescindir de ella y
> detener sus agentes manualmente con `Ctrl+C` al terminar la
> prueba. Esta sección describe las dos formas de integrarla por si
> se desea hacerlo. La superación del examen no depende de su uso.

### Forma A — Usar el `main.py` de la rama del examen

Es la vía por defecto. `main.py` instancia cada agente con la
factoría `crear_agente()` de `utils.py`, y esa factoría deja
`registrar_cierre_ordenado_examen` instalada automáticamente. El
alumno **no añade ninguna línea**.

### Forma B — Registrar la utilidad a mano en el `setup()`

Pensada para alumnos que arranquen sus agentes fuera de
`crear_agente` (por ejemplo, con un script propio que instancie
las clases directamente). Los **esqueletos didácticos** que
acompañan a esta rama —`agentes/agente_tablero.py` y
`agentes/agente_jugador.py`— contienen el patrón ya escrito y
comentado. Resumido:

```python
from utils import (
    registrar_aviso_errores_examen,
    registrar_cierre_ordenado_examen,
    unirse_a_sala_muc,
)


class AgenteTablero(Agent):
    async def setup(self) -> None:
        sala_muc = self.config_xmpp["sala_muc_completa"]

        # 1. Plugin MUC.
        self.client.register_plugin("xep_0045")

        # 2. Aviso del rechazo del servidor antes del examen
        #    (recomendado): hace visible el mensaje '[Examen]' en
        #    la consola si la sala todavía no existe.
        registrar_aviso_errores_examen(self, sala_muc)

        # 3. Utilidad de cierre ordenado (OPCIONAL): detiene el
        #    agente cuando el supervisor expulsa a los ocupantes
        #    (código MUC 307) o destruye la sala (332).
        registrar_cierre_ordenado_examen(self, sala_muc)

        # 4. Join a la sala con el nick único asignado por la
        #    utilidad de generación de agentes.
        unirse_a_sala_muc(self, sala_muc)

        # 5. ... resto del setup del alumno (behaviours, etc.) ...
```

El orden es relevante:

- El aviso debe registrarse **antes** del join, porque el rechazo
  llega de inmediato cuando la sala no existe.
- La utilidad de cierre puede registrarse antes o después del
  join, pero por consistencia conviene hacerlo en el mismo bloque.

> **No conviene combinar las dos formas.** Si los agentes los
> crea `crear_agente` (Forma A), las utilidades ya están
> registradas. Registrar de nuevo en `setup()` produce una doble
> inscripción del manejador: SPADE tolera la duplicación, pero
> es preferible elegir una sola vía.

### Qué se ve cuando funciona

Al detener el supervisor, en la consola de los agentes aparece un
mensaje como este, y el agente se detiene a continuación:

```
INFO utils — Fin del examen: el supervisor ha destruido la sala del
examen. El agente 'jugador_demo@sinbad2.ujaen.es' se detiene de forma
ordenada.
```


## Resumen

- Al arrancar con el `main.py` del examen, las dos utilidades
  (aviso de inicio y cierre ordenado) quedan **instaladas
  automáticamente**: no hay que añadir nada al código del alumno.
- La utilidad de cierre es **opcional**. Si se omite, basta con
  parar los agentes con `Ctrl+C` cuando termine la prueba.
- Para integrarla a mano (alumnos que no usen `crear_agente`), el
  patrón aparece comentado en los esqueletos didácticos
  `agentes/agente_tablero.py` y `agentes/agente_jugador.py` de
  esta rama.
- Toda la lógica reside en `utils.py`, junto a `crear_agente`,
  `arrancar_agente`, `comprobar_supervisor_activo`,
  `unirse_a_sala_muc` y las funciones de carga de configuración.
- Para la operativa completa del modo examen (submodalidades,
  `alumno.submodo`, `alumno.pc`, `alumno.nick_tablero`,
  `alumno.nick_jugador`, sonda del supervisor, etc.), véase
  [`INSTRUCCIONES_EXAMEN_ALUMNO.md`](INSTRUCCIONES_EXAMEN_ALUMNO.md).
