# Instrucciones para el alumno — Prueba de examen

Esta guía describe paso a paso cómo el alumno prepara su entorno y
lanza sus agentes el día de la prueba de examen de la asignatura
**Sistemas Multiagente (SSMMAA)**.

> **Resumen.** El alumno crea en su propio repositorio una
> rama llamada exactamente `examen-ssmmaa`, copia a esa rama la
> infraestructura común (lanzador, utilidades, módulo de
> configuración, plantillas y script de verificación) que el
> profesor publica en `examen-alumno`, ajusta el bloque `alumno` de
> `config/config.yaml`, conserva sus propias clases `AgenteJugador`
> y `AgenteTablero` del curso y, el día del examen, ejecuta
> `python main.py` cuando el profesor lo indique.


## 1. Requisitos previos

| Herramienta  | Versión mínima |
|--------------|---------------:|
| Python       | 3.12 — verificada como compatible con SPADE 4.x. |
| Cuenta XMPP  | `<usuario_uja>@sinbad2.ujaen.es` (la cuenta institucional de la asignatura). |
| Conectividad | Red de la Universidad de Jaén o conexión VPN (para alcanzar `sinbad2.ujaen.es`). |

Comprobación rápida de conectividad:

```bash
nc -zv sinbad2.ujaen.es 8022
```

Si la respuesta es distinta de `succeeded`, debe encontrarse en la
red de la UJA o establecer la conexión VPN antes de continuar.


## 2. Nombre fijo de la rama de examen

El alumno crea una rama llamada **exactamente** `examen-ssmmaa`. El
nombre no es libre: es una convención común de la asignatura, idéntica
en el repositorio de todos los alumnos, que permite localizar la rama
de examen de forma uniforme. Un nombre genérico podría además
colisionar con ramas de otras asignaturas que comparten
infraestructura.

> **Si se publica con otro nombre (`examen-2026`, `examen-dia-X`,
> `examen-final`, etc.), la rama no se tendrá en cuenta el día del
> examen.** El alumno puede tener tantas variantes locales como
> quiera, pero la rama publicada a `origin` debe llamarse
> exactamente `examen-ssmmaa`.

> **No debe usarse `git merge profesor/examen-alumno`.** Esa rama
> contiene únicamente la infraestructura mínima del examen: una
> fusión directa eliminaría de la copia local del alumno los
> ficheros que aquí no aparecen (`ontologia/`, `behaviours/`,
> `estrategia/`, `web/`, las pruebas propias, etc.) o produciría
> conflictos *modify/delete*. El procedimiento de la sección 3
> incorpora únicamente los ficheros de infraestructura, sin alterar
> el resto del proyecto del alumno.


## 3. Crear y publicar la rama `examen-ssmmaa`

### 3.1. Preparar el repositorio remoto del profesor

Una sola vez en el repositorio del alumno:

```bash
git remote add profesor <url-del-repo-del-profesor>
git fetch profesor examen-alumno
```

> En los ejemplos posteriores se utiliza `profesor` como nombre del
> remoto. Si se ha añadido con otro nombre, debe sustituirse en las
> órdenes correspondientes.

### 3.2. Crear la rama partiendo del trabajo final del alumno

Posiciónese en la rama de desarrollo habitual del alumno (`main`,
`develop`, etc.), compruebe que no hay cambios sin confirmar
(`git status` debe indicar un directorio de trabajo limpio) y cree
la rama del examen:

```bash
git checkout main                  # o la rama de trabajo del alumno
git pull
git checkout -b examen-ssmmaa
```

La nueva rama parte del código del alumno sin alteración: el
contenido de `ontologia/`, `behaviours/`, `estrategia/`, `web/` y
demás carpetas se conserva íntegro.

### 3.3. Incorporar la infraestructura del examen

Sobre la rama recién creada, traer únicamente los ficheros de
infraestructura del profesor. Estos ficheros **deben sustituir** a
los homólogos del alumno (si existían) porque contienen la sonda
del supervisor, la generación automática de nicks únicos y la
canonización del nombre de sala que el sistema necesita.

```bash
git checkout profesor/examen-alumno -- \
    main.py \
    utils.py \
    config/configuracion.py \
    config/agents.yaml \
    config/sala_examen.yaml \
    scripts/verificar_configuracion.py
```

`config/config.yaml` se trata aparte porque contiene el bloque
`alumno` que el estudiante personaliza:

```bash
git checkout profesor/examen-alumno -- config/config.yaml
```

A continuación se edita ese fichero (sección 4) para fijar el
usuario UJA del alumno, los nicks que prefiera y, en su caso, el
puesto del aula. Una vez ajustado:

```bash
git add main.py utils.py config/ scripts/verificar_configuracion.py
git commit -m "Infraestructura del examen SSMMAA"
git push -u origin examen-ssmmaa
```

> **Ficheros que NO deben incorporarse de `profesor/examen-alumno`**:
> el `README.md`, las dependencias (`requirements.txt`), los
> esqueletos didácticos de `agentes/`, las pruebas y la documentación
> del profesor. El alumno conserva los suyos.

### 3.4. Mantener los agentes propios

Los ficheros del alumno `agentes/agente_jugador.py` y
`agentes/agente_tablero.py` permanecen sin cambios: contienen las
clases `AgenteJugador` y `AgenteTablero` que el alumno ha
desarrollado durante el curso. El lanzador del examen las
importará dinámicamente con `importlib`.

> **Si el alumno usa su propio lanzador en lugar de `python main.py`
> de esta rama**, sigue siendo **obligatorio** canonizar el nombre
> de la sala MUC con `normalizar_nombre_sala` antes de hacer `join`,
> porque el supervisor del profesor utiliza esa misma función para
> crear las salas. El resto de utilidades (cierre ordenado, factoría
> `crear_agente`) son opcionales. La vía recomendada para evitar
> problemas es arrancar con `python main.py` de esta rama. Detalle
> en la sección 6.

> Si el alumno NO dispone aún de sus propias clases —por ejemplo,
> porque está creando la rama por primera vez— puede traer los
> **esqueletos didácticos** del profesor como punto de partida:
>
> ```bash
> git checkout profesor/examen-alumno -- \
>     agentes/agente_tablero.py \
>     agentes/agente_jugador.py
> ```
>
> Estos esqueletos simulan una secuencia de mensajes sin reglas de
> decisión y ilustran cómo integrar las utilidades de
> `utils.py`. **Deben sustituirse** por las clases reales del
> alumno antes del examen oficial.


## 4. Configurar el bloque `alumno` de `config/config.yaml`

Es el único fichero del repositorio donde el alumno introduce datos
propios. Todos los campos están documentados con comentarios en el
propio YAML.

```yaml
alumno:
  usuario_uja: <usuario_uja>          # ← obligatorio
  nick_tablero: ""                    # ← opcional
  nick_jugador: ""                    # ← opcional
  modalidad: examen                   # ← obligatorio
  submodo: <grupo|individual>         # ← el profesor anuncia cuál
  pc: PC-NN                           # ← solo si submodo=individual
  niveles_estrategia: [<niveles>]     # ← obligatorio
```

### 4.1. Detalle de cada campo

| Campo | Obligatorio | Significado |
|-------|-------------|-------------|
| `usuario_uja` | sí | Parte local del JID del alumno; identifica la cuenta XMPP institucional (`<usuario_uja>@sinbad2.ujaen.es`). |
| `nick_tablero` | no | Nick base que se mostrará en la sala MUC para los agentes tablero del alumno. Si está vacío o ausente, el lanzador usa `usuario_uja` como nick base. |
| `nick_jugador` | no | Nick base de los jugadores del alumno. Misma regla de fallback que `nick_tablero`. |
| `modalidad` | sí | Vale `examen` el día de la prueba. Las modalidades `laboratorio` y `torneo` se mantienen para uso interno durante el curso. |
| `submodo` | sí en `examen` | `grupo` (sala única `examen@examen.<dominio>` compartida por todos los alumnos) o `individual` (sala por puesto `<pc>@examen.<dominio>`). El profesor lo anuncia. |
| `pc` | sí en `individual` | Identificador del puesto del aula. Cualquier escritura (`PC-5`, `pc-05`, `PC_5`, `pc 5`) se canoniza a `pc-05`; se recomienda el formato estándar `PC-NN`. |
| `niveles_estrategia` | sí | Lista de niveles de estrategia que jugarán los jugadores del alumno. En `examen` individual los 12 jugadores se reparten uniformemente entre los niveles indicados (por ejemplo `[1, 2, 3]` produce 4 jugadores de cada nivel). En `examen` grupo se usa solo el primer nivel. |

### 4.2. Nicks únicos en la sala MUC

Cada agente recibe en `parametros["nick_muc"]` un nick **derivado
del nick base con un sufijo único**, calculado por
`config.configuracion.generar_agentes`:

| Rol | Patrón | Ejemplo (con `nick_jugador: "Pedro-J"`) |
|-----|--------|------------------------------------------|
| Tablero | `<nick_base>-NN`   | `Pedro-T-01`, `Pedro-T-02`, `Pedro-T-03` |
| Jugador | `<nick_base>-n<L>-NN` | `Pedro-J-n1-01`, `Pedro-J-n2-03`, ...     |

El sufijo `n<L>` del jugador indica el nivel de estrategia que
ejecuta, de modo que el nivel de cada jugador queda reflejado en su
propio nick dentro de la sala.

### 4.3. Campos que NO se editan

El alumno **no debe** tocar `xmpp.servicio_muc` ni
`xmpp.sala_tictactoe` del perfil `servidor`. El lanzador detecta
`modalidad: examen` y reescribe esos campos automáticamente para
apuntar a `examen.<dominio>` y a la sala adecuada del submodo
(`examen` para grupo, `<pc>` para individual).

### 4.4. Submodalidades en una tabla

| Submodalidad | `submodo` | `pc` | Sala MUC resultante | Agentes del alumno |
|--------------|-----------|------|---------------------|---------------------|
| Grupo (sala compartida) | `grupo` | (ignorado) | `examen@examen.<dominio>` | 1 tablero + 1 jugador |
| Individual (por puesto) | `individual` | `PC-NN` | `<pc>@examen.<dominio>` | 3 tableros + 12 jugadores |

En las dos submodalidades, el supervisor del profesor debe estar
arrancado **antes** que los agentes del alumno. La sonda del
lanzador lo comprueba con una consulta XEP-0030 (servicio de
descubrimiento) y aborta con código de salida 7 si la sala todavía
no existe.


## 5. Verificación visual antes del examen

Antes de cualquier conexión XMPP, el alumno puede comprobar el
efecto de sus campos del bloque `alumno` con el script

```bash
python scripts/verificar_configuracion.py
```

El script lee `config/config.yaml`, aplica la normalización del
nombre de sala y la derivación de nicks, y muestra una tabla:

```
══════════════════════════════════════════════════════════════════════════════
  Verificación de la configuración del alumno
══════════════════════════════════════════════════════════════════════════════
  Usuario UJA          : pedroj
  Modalidad            : examen
  Submodalidad         : individual
  Puesto escrito       : 'PC-5'  →  normalizado: 'pc-05'
  Componente MUC       : examen.sinbad2.ujaen.es
  Sala MUC destino     : pc-05@examen.sinbad2.ujaen.es
──────────────────────────────────────────────────────────────────────────────
Nombre del agente                     Rol       Nick MUC
────────────────────────────────────────────────────────────────────────────
tablero_pedroj_01                     Tablero   Pedro-T-01
...
jugador_pedroj_n3_04                  Jugador   Pedro-J-n3-04
────────────────────────────────────────────────────────────────────────────
  Total: 15 agentes (3 tableros, 12 jugadores)
  ✓ Todos los nicks son únicos.
══════════════════════════════════════════════════════════════════════════════
```

Si en la última línea apareciera `⚠ ATENCIÓN: hay nicks
duplicados`, el alumno debe revisar el bloque `alumno`: dos
agentes con el mismo nick serían rechazados por el servidor MUC.


## 6. Utilidades de la rama del profesor

Esta rama publica en `utils.py` y `config/configuracion.py` un
conjunto de funciones auxiliares pensadas para el día del examen.
Una de ellas es **obligatoria** para que los agentes se unan a la
sala correcta; el resto puede quedar bajo la responsabilidad del
alumno.

> **Recomendación.** Arrancar el sistema con `python main.py` de
> esta rama. El lanzador integra todas las utilidades sin esfuerzo
> adicional —la obligatoria queda aplicada por `cargar_configuracion`
> y las opcionales por la factoría `crear_agente`— y es la vía
> aconsejada para evitar problemas el día del examen.

### 6.1. Normalización del nombre de sala (OBLIGATORIA)

La función `config.configuracion.normalizar_nombre_sala` canoniza
el nombre de la sala MUC a una forma común (`pc-05`, `examen`, …).
El supervisor del profesor utiliza **exactamente la misma función**
para construir los nombres de las salas que crea. Si el alumno no
canoniza el nombre, el JID al que su agente intenta unirse no
coincide con el JID de la sala creada por el supervisor y el
servidor lo rechaza como sala inexistente.

**No es opcional bajo ninguna circunstancia.** El alumno puede
escribir `PC-5`, `pc5` o `PC_05` en `alumno.pc`, pero el supervisor
habrá creado la sala con el nombre `pc-05`; sin la normalización
los dos lados nunca convergen al mismo JID.

- Con `python main.py` de esta rama, la normalización ya está
  aplicada por `cargar_configuracion`: el campo
  `xmpp.sala_muc_completa` que reciben los agentes contiene el JID
  canonizado y listo para hacer `join`.
- Si el alumno usa su propio lanzador o instancia los agentes desde
  un script propio, **debe** invocar `normalizar_nombre_sala`
  antes de construir el JID de la sala:

  ```python
  from config.configuracion import normalizar_nombre_sala

  nombre_sala = normalizar_nombre_sala(config["alumno"]["pc"])
  sala_jid = f"{nombre_sala}@{config['xmpp']['servicio_muc_examen']}"
  ```

### 6.2. Cierre ordenado al terminar el examen (opcional)

Cuando el profesor detiene su Agente Supervisor al terminar la
prueba, este realiza una limpieza ordenada: **expulsa** a los
agentes del alumno de las salas del examen y **destruye** dichas
salas. El servidor avisa de ello con una presencia `unavailable`
que lleva el código MUC 307 (expulsión) o 332 (sala destruida).

`utils.py` ofrece la función `registrar_cierre_ordenado_examen` que
escucha esa presencia y, cuando reconoce que es el propio agente el
que sale de la sala, **detiene el agente con `agente.stop()`**. Sin
ella, los agentes podrían quedar esperando mensajes que ya no van a
llegar o fallar al enviar a una sala inexistente.

**No es obligatorio integrarla** para superar la prueba. El alumno
puede detener sus agentes manualmente con `Ctrl+C` al terminar.
Pero si se desea, hay dos formas equivalentes:

#### 6.2.1. Automática (caso habitual)

`main.py` crea cada agente con la factoría `crear_agente` de
`utils.py`, y esa factoría deja la utilidad **instalada
automáticamente** en el ciclo de vida del agente. No hay que
escribir ninguna línea. Es el comportamiento por defecto si el
alumno usa `python main.py` sin más.

#### 6.2.2. Manual (referencia para alumnos que no usen la factoría)

Si el alumno prefiere arrancar sus agentes fuera de `crear_agente`
—por ejemplo, porque instancia las clases directamente desde un
script propio—, puede registrar la utilidad en el `setup()` del
agente. Los **esqueletos didácticos** que el profesor publica en
esta rama (`agentes/agente_tablero.py` y `agentes/agente_jugador.py`,
visibles con `git show profesor/examen-alumno:agentes/agente_tablero.py`
si el alumno ya los ha sustituido por sus propias clases) muestran
el patrón:

```python
from config.configuracion import normalizar_nombre_sala
from utils import (
    registrar_cierre_ordenado_examen,
    unirse_a_sala_muc,
)


class AgenteTablero(Agent):
    async def setup(self) -> None:
        # 0. Normalización del nombre de sala — OBLIGATORIA.
        #    Si se confía en 'sala_muc_completa' calculado por el
        #    lanzador de esta rama, este paso ya está hecho. Si el
        #    alumno construye el JID por su cuenta, debe canonizar
        #    el nombre con normalizar_nombre_sala (sección 6.1).
        sala_muc = self.config_xmpp["sala_muc_completa"]

        # 1. Plugin MUC (XEP-0045).
        self.client.register_plugin("xep_0045")

        # 2. Utilidad de cierre ordenado: detiene el agente cuando
        #    el supervisor expulsa a los ocupantes (código MUC 307)
        #    o destruye la sala (código 332). Debe registrarse
        #    ANTES del join para no perder presencias relevantes.
        registrar_cierre_ordenado_examen(self, sala_muc)

        # 3. Join a la sala con el nick único asignado.
        unirse_a_sala_muc(self, sala_muc)

        # 4. ... resto del setup del alumno ...
```

Detalles operativos, el mensaje que aparece en consola al activarse
y el aviso del rechazo de inicio (la otra utilidad disponible en
`utils.py`) se documentan en
[`AVISO_ERRORES_EXAMEN.md`](AVISO_ERRORES_EXAMEN.md).

> **No conviene combinar las dos formas.** Si `main.py` ya invoca
> `crear_agente`, el manejador está instalado: registrarlo de nuevo
> en `setup()` simplemente añade una inscripción duplicada. SPADE
> tolera la duplicación, pero es preferible elegir una vía.


## 7. Procedimiento durante el examen

1. **Comprobar la conectividad** con el servidor de la asignatura:

   ```bash
   nc -zv sinbad2.ujaen.es 8022
   ```

2. **Activar la rama del examen**:

   ```bash
   git checkout examen-ssmmaa
   ```

3. **En estrategia de nivel 4**, seleccionar el perfil LLM en
   `config/config.yaml`: el campo `llm.perfil_activo` vale
   `ninguno` por defecto (el sistema arranca sin LLM); para usar
   un LLM hay que cambiarlo a `gemini` o a `servidor`. Si se elige
   `gemini`, exportar además la clave de Google AI Studio en la
   terminal desde la que se lanzará `main.py`:

   ```bash
   export GOOGLE_API_KEY="<clave_personal>"
   ```

   Si la estrategia solo usa los niveles 1 a 3, dejar
   `llm.perfil_activo` en `ninguno`: no hace falta ninguna clave.

4. **Esperar la señal de inicio del profesor.** El profesor anuncia
   cuándo su supervisor está activo y la sala del examen existe.

5. **Lanzar los agentes**:

   ```bash
   python main.py
   ```

   El lanzador emite en consola tres cosas relevantes:

   - La sala MUC destino (con el nombre ya normalizado).
   - El resultado de la sonda del supervisor.
   - Para cada agente creado: su JID, su nick MUC y sus parámetros.

6. **Detener la ejecución** con `Ctrl+C` cuando el profesor lo
   indique. Si se ha integrado la utilidad opcional de
   finalización, los agentes ya se habrán detenido por sí mismos al
   recibir la presencia de cierre del supervisor.


## 8. Si se arranca antes que el supervisor

Si se ejecuta `python main.py` antes de que el supervisor del
profesor esté activo, la sonda XEP-0030 detecta que la sala no
existe y el lanzador aborta con código de salida 7. En consola
aparece un mensaje del tipo:

```
[CRITICAL] main — El supervisor del examen NO está activo: la
sala MUC 'examen@examen.sinbad2.ujaen.es' aún no está creada en el
servidor. condición XMPP 'item-not-found'. [Examen] Espera a que
el supervisor del profesor cree la sala.
  Espera a que el profesor arranque su supervisor y vuelve a
  lanzar 'python main.py'. No se crea ningún agente para no saturar
  el log del servidor con rechazos repetidos.
```

Procedimiento:

1. Esperar la señal del profesor.
2. Volver a ejecutar `python main.py`.

Este aborto temprano es **intencionado**: sin él, cada agente
intentaría unirse en paralelo y el log se llenaría con 15
rechazos idénticos antes de que nada útil llegara a ocurrir.


## 9. Diagnóstico de errores frecuentes

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| `Connection refused` al puerto 8022 | Equipo fuera de la red UJA o VPN inactiva. | Establecer la VPN y reintentar. |
| `No module named 'agentes.agente_jugador'` | Falta el fichero del agente. | Asegurar que `agentes/agente_jugador.py` existe y contiene la clase `AgenteJugador`. |
| El lanzador aborta con salida 7 y marca `[Examen]` | El supervisor del profesor no ha arrancado todavía. | Esperar la señal del profesor y reintentar. |
| `not-authorized` o `auth failure` | Contraseña XMPP incorrecta. | Verificar `password_defecto` en `config/config.yaml` o usar la cuenta UJA real. |
| El script de verificación avisa de nicks duplicados | El bloque `alumno` produce colisión. | Revisar `nick_tablero` / `nick_jugador` y volver a ejecutar `scripts/verificar_configuracion.py`. |
| `GOOGLE_API_KEY no definida` (solo nivel 4) | Variable de entorno sin exportar. | Ejecutar `export GOOGLE_API_KEY="..."` en la misma terminal antes de `python main.py`. |


## 10. Listas de verificación

### Víspera del examen

- [ ] Repositorio del alumno clonado y entorno virtual creado.
- [ ] `pip install -r requirements.txt` finalizado sin errores.
- [ ] Existe la rama `examen-ssmmaa` y está publicada en `origin`.
- [ ] Los ficheros `main.py`, `utils.py`, `config/configuracion.py`,
      `config/agents.yaml`, `config/sala_examen.yaml` y
      `scripts/verificar_configuracion.py` proceden de
      `profesor/examen-alumno`.
- [ ] `agentes/agente_jugador.py` y `agentes/agente_tablero.py`
      contienen las clases del alumno.
- [ ] `alumno.usuario_uja` correctamente cumplimentado en
      `config/config.yaml`.
- [ ] `python scripts/verificar_configuracion.py` muestra la sala y
      los nicks esperados sin avisos.
- [ ] `nc -zv sinbad2.ujaen.es 8022` devuelve `succeeded`.
- [ ] (Solo nivel 4) Hay clave de Google AI Studio en la cuenta del
      alumno y se ha probado `export GOOGLE_API_KEY=...` en una
      terminal al menos una vez.

### Día del examen

- [ ] `nc -zv sinbad2.ujaen.es 8022` devuelve `succeeded`.
- [ ] `git branch --show-current` indica `examen-ssmmaa`.
- [ ] `alumno.submodo` y, en su caso, `alumno.pc` coinciden con la
      submodalidad anunciada por el profesor.
- [ ] (Solo nivel 4) `GOOGLE_API_KEY` exportada en la terminal
      desde la que se ejecutará `python main.py`.
- [ ] Recibida la señal de inicio del profesor.
- [ ] `python main.py` registra "Supervisor activo" y procede a
      crear los agentes.


## 11. Recursos

- [`README.md`](../README.md) — Resumen general de la rama.
- [`AVISO_ERRORES_EXAMEN.md`](AVISO_ERRORES_EXAMEN.md) — Aviso del
  rechazo del servidor antes del examen y utilidad de finalización.
- [`PROBLEMAS_FRECUENTES_EXAMEN.md`](PROBLEMAS_FRECUENTES_EXAMEN.md) —
  Problemas recurrentes de integración: el JID en el intercambio de
  mensajes, el nick en la sala MUC y el uso de la factoría.
- `agentes/agente_tablero.py`, `agentes/agente_jugador.py` —
  Esqueletos didácticos del profesor (referencia del patrón de
  integración).
- <https://aistudio.google.com/apikey> — Clave gratuita de Google
  AI Studio (necesaria solo si se elige el perfil LLM `gemini`
  para la estrategia de nivel 4).
