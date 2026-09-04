# Integración de los agentes del alumno en la rama del examen

Esta guía explica cómo **enlazar** los agentes que el alumno ha
desarrollado durante el curso —`AgenteTablero` y `AgenteJugador`— en
la rama del examen (`examen-ssmmaa`), de forma que superen la serie
de pruebas de protocolo que acompaña a la rama.

Mientras el alumno no integre sus agentes, la rama contiene una
**implementación de referencia** ya completa: los ficheros
`agentes/agente_tablero.py` y `agentes/agente_jugador.py` resuelven
correctamente los tres protocolos de la ontología. El alumno puede
partir de ellos o sustituirlos por los suyos; en ambos casos debe
respetar el **contrato de integración** que se describe aquí.


## 1. La cadena de integración

El trabajo del alumno y la rama del examen se unen en un punto: la
carpeta `agentes/`. El lanzador `main.py` carga dinámicamente dos
clases desde dos módulos fijos:

| Fichero                     | Clase           | Módulo                   |
|-----------------------------|-----------------|--------------------------|
| `agentes/agente_tablero.py` | `AgenteTablero` | `agentes.agente_tablero` |
| `agentes/agente_jugador.py` | `AgenteJugador` | `agentes.agente_jugador` |

Integrar los agentes consiste en colocar en esos dos ficheros las
clases del alumno (o partir de las de referencia y ampliarlas). El
resto de la infraestructura de la rama —`ontologia/`, `utils.py`,
`config/`, `main.py`— **no se modifica**: es material del profesor y
las pruebas asumen que se mantiene intacto.


## 2. El contrato de integración

Para que las pruebas reconozcan y ejerciten los agentes del alumno,
estos deben cumplir seis condiciones. Las dos primeras se refieren a
la **forma** de las clases; las cuatro restantes, a su
**comportamiento**.

### 2.1. Las clases y su construcción

1. **Dos clases con nombre fijo.** `agentes/agente_tablero.py` debe
   definir `AgenteTablero` y `agentes/agente_jugador.py` debe definir
   `AgenteJugador`. Ambas son subclases de `spade.agent.Agent`.

2. **Constructor compatible con la factoría.** El agente se crea con
   `utils.crear_agente`, que invoca el constructor con la firma de
   SPADE 4.x (`jid`, `password`, `port`, `verify_security`). Si el
   alumno no define `__init__`, hereda el de `Agent` y la condición
   se cumple sola. Si lo define, debe aceptar esa misma firma.

### 2.2. El comportamiento de los agentes

3. **La configuración se lee, no se fija.** `main.py` inyecta en cada
   agente, antes de arrancarlo, dos atributos:

   - `config_xmpp` — perfil XMPP resuelto. Contiene
     `sala_muc_completa`, el JID de la sala del examen ya canonizado.
   - `config_parametros` — parámetros propios del agente, entre
     ellos `nick_muc`, el nick único con el que debe unirse a la
     sala.

   El agente lee de ahí toda la configuración. **Nunca** escribe en
   el código JID, dominios, puertos ni nombres de sala literales.

4. **Los comportamientos se registran en `setup()`.** El `setup()`
   del agente registra el plugin MUC, se une a la sala con
   `unirse_a_sala_muc` y registra sus comportamientos con
   `self.add_behaviour(...)`. Las pruebas capturan esos
   comportamientos para ejercitarlos.

5. **La comunicación usa la ontología.** Los cuerpos de los mensajes
   se construyen con los constructores `crear_cuerpo_*` de
   `ontologia/ontologia.py`, que emparejan cada acción con su
   performativa FIPA-ACL y validan el cuerpo contra el esquema. El
   agente fija además la metadata (`ontology`, `performative`,
   `conversation-id`, `thread`) de cada mensaje.

6. **La identidad dentro de la sala es el nick.** En una sala MUC, el
   remitente de un mensaje es `sala@servicio/nick`, no el JID del
   agente. El agente identifica a los demás por su **nick** (el
   recurso del JID de ocupante) y les escribe a `sala@servicio/nick`
   para los mensajes privados, o difunde a `sala@servicio` con
   `type=groupchat` para los mensajes a toda la sala. Compárese
   siempre contra el nick, nunca contra `nombre@dominio`.

Las condiciones 3 y 6 son la causa más frecuente de fallo en el
examen; se explican con más detalle en
[`PROBLEMAS_FRECUENTES_EXAMEN.md`](PROBLEMAS_FRECUENTES_EXAMEN.md).


## 3. Los tres protocolos de la ontología

Los agentes intercambian mensajes en tres protocolos sucesivos. Cada
acción de la ontología lleva aparejada una performativa FIPA-ACL
fija (la columna «Performativa»).

### 3.1. Protocolo de registro en el tablero

| Acción          | Performativa     | Sentido                    |
|-----------------|------------------|----------------------------|
| `join`          | REQUEST          | Jugador → Tablero          |
| `join-accepted` | AGREE            | Tablero → Jugador (símbolo)|
| `join-refused`  | REFUSE           | Tablero → Jugador (mesa llena) |
| `join-timeout`  | FAILURE          | Tablero → Jugador (sin rival) |

El jugador difunde un `join` a la sala. El tablero le asigna un
símbolo (`X` al primero, `O` al segundo) y responde `join-accepted`;
si la mesa ya está completa responde `join-refused`; si no llega un
segundo jugador, avisa al primero con `join-timeout`.

### 3.2. Protocolo de juego de las partidas

| Acción        | Performativa      | Sentido                       |
|---------------|-------------------|-------------------------------|
| `game-start`  | INFORM            | Tablero → cada jugador        |
| `turn`        | CFP               | Tablero → ambos jugadores     |
| `move`        | PROPOSE           | Jugador → Tablero (propuesta) |
| `move`        | ACCEPT_PROPOSAL   | Tablero → sala (confirmación) |
| `turn-result` | INFORM            | Jugador → Tablero (acuse)     |
| `game-over`   | REJECT_PROPOSAL   | Tablero → sala (partida abortada) |

El tablero anuncia el inicio con `game-start`, convoca cada turno con
`turn` y confirma cada jugada válida con `move`. El jugador propone
su casilla con `move` y, tras la confirmación, comunica el desenlace
del turno con `turn-result`. Si una jugada es ilegal o un jugador no
responde a tiempo, el tablero aborta la partida con `game-over`.

### 3.3. Protocolo de informe de las partidas

| Acción        | Performativa | Sentido                          |
|---------------|--------------|----------------------------------|
| `game-report` | REQUEST      | Supervisor → Tablero (solicitud) |
| `game-report` | INFORM       | Tablero → Supervisor (informe)   |
| `game-report` | REFUSE       | Tablero → Supervisor (en curso)  |

El supervisor del profesor solicita el informe de una partida con un
`game-report`. El tablero responde con el informe completo
(`INFORM`) si la partida ya terminó, o con un `REFUSE` y la razón
`not-finished` si sigue en curso. Por ello el tablero necesita un
comportamiento **independiente** que atienda esta solicitud en
paralelo a la partida.

La secuencia completa y los campos de cada mensaje están en la
implementación de referencia (`agentes/agente_tablero.py` y
`agentes/agente_jugador.py`) y en el esquema
`ontologia/ontologia_tictactoe.schema.json`.


## 4. Cómo se verifican los agentes

Las pruebas no necesitan ningún servidor XMPP: ejercitan los agentes
del alumno como una **caja negra** sobre una sala MUC simulada en
memoria. El arnés de simulación (`tests/simuladores/`) hace tres
cosas:

1. Crea el agente del alumno con la factoría `crear_agente` —la
   misma cadena que usa `main.py`—.
2. Le inyecta la configuración (`config_xmpp`, `config_parametros`,
   `config_sistema`, `config_llm`) y sustituye el cliente XMPP y el
   panel web por dobles de prueba, para que `setup()` se ejecute por
   completo sin abrir ninguna conexión de red ni ningún puerto.
3. Conecta los comportamientos del agente a la sala simulada y le
   enfrenta a un **simulador del agente contrario** (un tablero, un
   jugador o el supervisor) que reproduce el comportamiento
   esperado.

Después, la prueba comprueba que los mensajes producidos por el
agente del alumno cumplen la ontología: performativa correcta,
cuerpo válido según el esquema, `conversation-id` e hilo adecuados.

Los ficheros de prueba son:

| Fichero                          | Verifica                         |
|----------------------------------|----------------------------------|
| `tests/test_protocolo_registro.py` | El protocolo de registro (`join`). |
| `tests/test_protocolo_partida.py`  | El protocolo de juego (`turn`/`move`). |
| `tests/test_protocolo_informe.py`  | El protocolo de informe (`game-report`). |
| `tests/test_factoria_jid.py`       | El uso de la factoría y de los JID/nick. |

> **El arnés tolera la forma habitual de los agentes del curso.**
> Acepta que el `setup()` arranque el panel web, que `add_behaviour`
> reciba la plantilla con la palabra clave `template` de SPADE, y que
> el agente lea parámetros de configuración que un `config.yaml`
> antiguo no traiga. Su objetivo es ejecutar el `setup()` real del
> agente para poder ejercitar su comportamiento; el contrato que sí
> debe cumplirse es el de la sección 2.

> **Las pruebas del perfil LLM son condicionales.** La estrategia de
> nivel 4 (LLM) es opcional. Las cinco pruebas del perfil LLM de
> `test_configuracion_examen.py` solo se evalúan si `config.yaml`
> declara el nivel 4 en `alumno.niveles_estrategia`; en caso
> contrario se omiten y no cuentan como incidencia.


## 5. Pasos para integrar los agentes

1. **Activar la rama del examen** (véase
   [`INSTRUCCIONES_EXAMEN_ALUMNO.md`](INSTRUCCIONES_EXAMEN_ALUMNO.md)).

2. **Colocar los agentes del alumno** en `agentes/agente_tablero.py`
   y `agentes/agente_jugador.py`. Hay dos opciones:

   - *Partir de la referencia*: conservar los ficheros de la rama y
     sustituir solo la **estrategia** de elección de casilla (la
     función `elegir_posicion` de `agentes/reglas_juego.py`, o la
     llamada a ella en el jugador) por la del alumno.
   - *Aportar los agentes propios*: reemplazar por completo los dos
     ficheros, respetando el contrato de la sección 2.

3. **Añadir los módulos auxiliares** que importen los agentes
   (estrategia, behaviours propios, interfaz web…) en sus carpetas
   habituales. No modificar `ontologia/`, `utils.py` ni `config/`.

4. **Comprobar la configuración**:

   ```bash
   python scripts/verificar_configuracion.py
   ```

5. **Ejecutar la serie de pruebas** (véase la sección 6). Las cuatro
   pruebas de protocolo y factoría deben pasar.

6. **Arrancar el sistema** para una comprobación final:

   ```bash
   python main.py
   ```


## 6. Ejecutar las pruebas

```bash
# Toda la serie de validación de la rama
pytest tests/ -v

# Solo las pruebas de protocolo y factoría
pytest tests/test_protocolo_registro.py tests/test_protocolo_partida.py \
       tests/test_protocolo_informe.py tests/test_factoria_jid.py -v
```

Conviene ejecutar primero `test_factoria_jid.py`: si la factoría o
los JID se usan mal, las pruebas de protocolo también fallarán, y la
causa real estará en la integración, no en el protocolo.


## 7. Diagnóstico de fallos frecuentes

| Prueba que falla | Causa probable | Solución |
|------------------|----------------|----------|
| `test_factoria_jid` :: `test_crear_agente_admite_las_clases_del_alumno` | El constructor del agente tiene una firma incompatible con la factoría. | No redefinir `__init__`, o aceptar `jid, password, port, verify_security`. |
| `test_factoria_jid` :: `test_agente_se_une_…_con_el_nick_de_la_config` | El agente se une a la sala con un nick fijo. | Unirse con `unirse_a_sala_muc(self, sala)` sin el argumento `nick`. |
| `test_factoria_jid` :: `test_…_dirige_…_por_nick` | El agente compara o direcciona por el JID del agente. | Identificar y direccionar por el **nick** (recurso de `msg.sender`). |
| `test_protocolo_registro` | El `join` no es REQUEST, le falta `conversation-id`/`thread`, o el tablero no asigna bien los símbolos. | Construir los mensajes con `crear_cuerpo_join`/`crear_cuerpo_join_accepted`. |
| `test_protocolo_partida` | Falta el `game-start`, el `turn` no es CFP, o la confirmación del `move` no es ACCEPT_PROPOSAL. | Usar `crear_cuerpo_game_start`, `crear_cuerpo_turn`, `crear_cuerpo_move_confirmado`. |
| `test_protocolo_informe` | El tablero no atiende el `game-report` mientras juega, o responde con la performativa equivocada. | Registrar un comportamiento aparte para el informe; usar `crear_cuerpo_game_report` / `crear_cuerpo_game_report_refused`. |
| Un escenario «se queda bloqueado» (timeout del escenario) | El agente espera un mensaje que nunca llega porque filtra mal por acción, nick o hilo. | Revisar los filtros de `receive`; comparar con la implementación de referencia. |


## 8. Recursos

- [`PROBLEMAS_FRECUENTES_EXAMEN.md`](PROBLEMAS_FRECUENTES_EXAMEN.md) —
  El JID frente al nick y el uso de la factoría.
- [`INSTRUCCIONES_EXAMEN_ALUMNO.md`](INSTRUCCIONES_EXAMEN_ALUMNO.md) —
  Preparación de la rama del examen.
- `ontologia/ontologia.py` — Constructores y validador de la ontología.
- `agentes/agente_tablero.py`, `agentes/agente_jugador.py` —
  Implementación de referencia de los tres protocolos.
- `tests/simuladores/` — Arnés de simulación y oráculos del
  comportamiento esperado.
- `tests/README.md` — Serie de validación completa de la rama.
