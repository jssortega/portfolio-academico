# Problemas frecuentes de integración — rama `examen-ssmmaa`

Esta guía describe dos problemas que se observan de forma repetida
cuando el alumno integra su trabajo en la rama `examen-ssmmaa`. No es
un fragmento de código para copiar: es una explicación de **por qué**
fallan los agentes y de **qué pieza de la infraestructura** resuelve
cada caso. Ambos problemas comparten una misma raíz: prescindir de la
infraestructura que la rama del examen ya proporciona, o usarla de
forma incompleta.


## Problema 1 — El JID en el intercambio de mensajes y el nick en la sala MUC

Durante el examen toda la comunicación discurre dentro de una sala MUC
(*Multi-User Chat*). Alrededor de ese hecho aparecen dos confusiones.

### 1.1. Dentro de una sala MUC, el remitente no es el JID del agente

Cuando un agente envía un mensaje a la sala (`type=groupchat`), la sala
lo redistribuye al resto de ocupantes. Cada agente que lo recibe ve en
`msg.sender` **no** el JID del agente (`nombre@dominio`), sino el JID
de ocupante: `sala@servicio/nick`. El texto situado tras la barra (el
recurso del JID) es el nick; la sala oculta el JID real del agente que
ha hablado.

Error recurrente: el alumno quiere saber quién ha hablado —o dirigir un
turno a un jugador concreto— y entonces:

- compara `msg.sender` con un JID de la forma `jugador_x@dominio`, de
  modo que la comparación nunca coincide; o
- incrusta en el código un JID `nombre@dominio` del destinatario, con
  lo que el mensaje no circula por la sala o no llega a su destino.

Qué hacer: dentro de la sala, la identidad que opera es el **nick**, no
el JID del agente. Para saber quién envió un mensaje, hay que tomar el
recurso de `msg.sender` (el texto posterior a la barra `/`); los
esqueletos didácticos incluyen la función auxiliar `_extraer_nick` con
ese fin exacto. Para dirigirse a un jugador concreto, se difunde el
mensaje a la sala con el nick del destinatario escrito en el cuerpo
—como hacen los esqueletos— o se envía a `sala@servicio/nick`. Nunca a
`nombre@dominio`.

### 1.2. Cada agente necesita un nick distinto en la sala

Una sala MUC exige que cada ocupante tenga un nick único. Si dos
agentes intentan unirse con el mismo nick, el servidor rechaza al
segundo con la condición XMPP `conflict` y ese agente queda fuera de la
sala.

Error recurrente: en el `setup()`, el alumno se une con un nick fijo
—habitualmente su `usuario_uja`— idéntico para todos sus agentes. El
primer agente entra; los demás son rechazados. El síntoma es «solo se
conecta un agente» o «todos los agentes aparecen en la sala con el
mismo nombre».

Qué hacer: no elegir el nick a mano. La infraestructura ya asigna a
cada agente un nick único en `config_parametros["nick_muc"]`
(`generar_agentes` lo construye con los sufijos `-01`, `-n1-02`, …). La
función `unirse_a_sala_muc(self, sala)`, invocada **sin** el argumento
`nick`, utiliza ese campo. Antes del examen,
`python scripts/verificar_configuracion.py` muestra el nick de cada
agente y avisa si hay duplicados.


## Problema 2 — La factoría y la cadena de configuración

La rama del examen proporciona una cadena de tres pasos
—`cargar_configuracion()` → `generar_agentes()` → `crear_agente()`—
orquestada por `main.py`. Cuando el alumno instancia los agentes
directamente, por ejemplo con `AgenteJugador("jugador1@localhost",
"secret")`, rompe esa cadena y se producen dos consecuencias.

### 2.1. Los agentes no se conectan con la sala que les corresponde

`cargar_configuracion()` realiza dos tareas imprescindibles para el
examen que ningún otro paso cubre:

- redirige el componente MUC al componente dedicado del examen
  (`examen.<dominio>`); y
- canoniza el nombre de la sala con `normalizar_nombre_sala` y deja el
  JID completo listo en `xmpp.sala_muc_completa`.

El supervisor del profesor crea las salas aplicando **esa misma**
canonización. Si el alumno no pasa por `cargar_configuracion()`, su
agente intenta unirse a una sala cuyo JID no coincide con el de la sala
creada por el supervisor (`conference.<dominio>` en lugar de
`examen.<dominio>`, o `PC-5` en lugar de `pc-05`), y el servidor lo
rechaza como sala inexistente.

### 2.2. Los nombres de los agentes son incorrectos

`generar_agentes()` compone el nombre de cada agente con un patrón fijo
que incorpora el `usuario_uja`: `tablero_<usuario>_NN` y
`jugador_<usuario>_nL_NN`. Ese patrón es el que permite atribuir cada
agente a la cuenta del alumno que lo ha creado. Si el alumno inventa
los nombres (`jugador1`, `tablero`, …) o incrusta JID literales, su
trabajo no queda atribuido a su usuario; un JID literal, además, puede
apuntar a un servidor equivocado.

Qué hacer: arrancar con `python main.py` de la rama. La factoría
`crear_agente()` construye el JID con `construir_jid` sobre el perfil
XMPP activo e instala las utilidades del modo examen; `main.py` inyecta
en cada agente `config_xmpp` y `config_parametros`, que son
precisamente los atributos que el `setup()` lee como `self.config_xmpp`
y `self.config_parametros`. Un agente instanciado a mano carece de
ellos y falla en el `setup()`. Si el alumno usa su propio lanzador,
este debe reproducir la cadena completa: nunca instanciar la clase con
un JID literal ni inventar los nombres.


## Resumen

| Síntoma | Causa | Pieza que lo resuelve |
|---------|-------|-----------------------|
| Un agente no reconoce quién le habla o dirige mal los turnos. | Compara `msg.sender` con el JID del agente (`nombre@dominio`). | Extraer el nick del recurso de `msg.sender` (`_extraer_nick`). |
| Solo un agente del alumno entra en la sala (condición `conflict`). | Todos los agentes se unen con el mismo nick fijo. | `unirse_a_sala_muc(self, sala)` sin el argumento `nick`. |
| El agente es rechazado porque la sala no existe. | JID de sala sin canonizar o sin redirigir a `examen.<dominio>`. | `cargar_configuracion()` (o `python main.py`). |
| El trabajo del alumno no se atribuye a su usuario. | Nombres de agente inventados o JID literales. | `generar_agentes()` (o `python main.py`). |

La vía segura es arrancar con `python main.py` de la rama: la cadena
`cargar_configuracion` → `generar_agentes` → `crear_agente` resuelve
los cuatro casos sin que el alumno tenga que escribir código.


## Recursos

- [`INSTRUCCIONES_EXAMEN_ALUMNO.md`](INSTRUCCIONES_EXAMEN_ALUMNO.md) —
  Procedimiento completo de preparación de la rama.
- [`AVISO_ERRORES_EXAMEN.md`](AVISO_ERRORES_EXAMEN.md) — Utilidades del
  modo examen instaladas por la factoría.
