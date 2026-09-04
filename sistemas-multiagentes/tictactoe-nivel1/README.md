# Tic-Tac-Toe Multiagente — Rama de examen del alumno

**Asignatura:** Sistemas Multiagente (SSMMAA) — Grado en Ingeniería
Informática

**Universidad de Jaén** — Departamento de Informática

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
___

Esta rama (`examen-alumno`) contiene
la **infraestructura común** que el alumno debe incorporar a su
propio repositorio para automatizar la prueba de examen: lanzador
(`main.py`), utilidades (`utils.py`), módulo de configuración
(`config/configuracion.py`), plantillas (`config/agents.yaml`),
descripción de la sala (`config/sala_examen.yaml`), script de
verificación visual (`scripts/verificar_configuracion.py`), la
ontología del sistema (`ontologia/`) y la serie de pruebas
(`tests/`).

El alumno aporta sus propias clases `AgenteJugador` y
`AgenteTablero` —partiendo, si quiere, de la implementación de
referencia de la rama— y conserva sus `behaviours/`, su
`estrategia/`, su `web/` y cualquier otra dependencia del proyecto
del curso. El enlace de los agentes se detalla en
[`doc/INTEGRACION_AGENTES_ALUMNO.md`](doc/INTEGRACION_AGENTES_ALUMNO.md).

> **Para el día del examen, el profesor lanza un único Agente
> Supervisor en la configuración de **servidor**.** El alumno **no** necesita
> ningún supervisor en su máquina. Sus agentes solo se unen a la
> sala MUC que el profesor ya ha creado. Si arrancan antes de que el
> supervisor exista, el lanzador detecta esa situación mediante una
> sonda XEP-0030 al servidor, registra el motivo una vez y aborta
> sin crear ningún agente — para no saturar el log del servidor con
> rechazos repetidos.


## 1. Nombre fijo de la rama de examen

El alumno crea en su repositorio una **rama de examen** llamada
exactamente:

```
examen-ssmmaa
```

El nombre **no es libre**: debe ser idéntico en el repositorio de
todos los alumnos. Es una convención común de la asignatura, por dos
motivos:

- Permite localizar la rama de examen de forma uniforme en todos los
  repositorios, sin negociar un nombre distinto con cada alumno.
- Un nombre genérico (`examen`, `examen-final`, etc.) podría
  colisionar con ramas de otras asignaturas que comparten
  infraestructura.

> Cualquier otro nombre (`examen-dia-X`, `examen-2026`, etc.) no se
> tendrá en cuenta. Si el alumno desea conservar varias variantes
> locales, debe asegurarse de que la rama definitiva publicada a
> `origin` lleva exactamente este nombre.

## 2. Procedimiento de creación de la rama (resumen)

Desde el repositorio propio del alumno, partiendo de la rama de
trabajo que contiene los agentes finales:

```bash
# Añadir el repositorio del profesor como remoto adicional
# (una sola vez)
git remote add profesor <url-de-este-repo>
git fetch profesor examen-alumno

# Crear la rama de examen partiendo del trabajo final del alumno
git checkout main                # o la rama de desarrollo habitual
git pull
git checkout -b examen-ssmmaa

# Incorporar los ficheros de infraestructura desde la rama del
# profesor (no se sobrescribe nada de los agentes ni del resto del
# código del alumno)
git checkout profesor/examen-alumno -- \
    main.py \
    utils.py \
    config/configuracion.py \
    config/agents.yaml \
    config/sala_examen.yaml \
    scripts/verificar_configuracion.py \
    ontologia/ \
    agentes/reglas_juego.py \
    tests/

# config/config.yaml se incorpora aparte porque contiene el bloque
# 'alumno' que el estudiante personaliza con su usuario UJA y, si
# procede, su nick y el puesto del aula
git checkout profesor/examen-alumno -- config/config.yaml
$EDITOR config/config.yaml       # ajustar bloque 'alumno' (sección 4)

git add main.py utils.py config/ ontologia/ agentes/reglas_juego.py tests/
git commit -m "Infraestructura del examen SSMMAA"
git push -u origin examen-ssmmaa
```

El procedimiento completo, paso a paso, está en
[`doc/INSTRUCCIONES_EXAMEN_ALUMNO.md`](doc/INSTRUCCIONES_EXAMEN_ALUMNO.md).


## 3. Ficheros que el alumno trae de esta rama

| Fichero del profesor                       | Función |
|--------------------------------------------|---------|
| `main.py`                                  | Lanza los agentes del alumno. Comprueba con una sonda que el supervisor está activo antes de crear nada. |
| `utils.py`                                 | Funciones comunes: carga de configuración, factoría `crear_agente`, `unirse_a_sala_muc`, `comprobar_supervisor_activo`, utilidad de cierre ordenado. |
| `config/configuracion.py`                  | Lector de los dos YAML. Aplica la normalización de la sala según submodalidad y deriva nicks únicos por agente. |
| `config/agents.yaml`                       | Plantillas de tablero y jugador (clase, módulo, parámetros base). No se edita. |
| `config/sala_examen.yaml`                  | Identificador de la sala MUC oficial del examen. No se edita. |
| `config/config.yaml`                       | Único fichero con personalización del alumno: bloque `alumno`. |
| `scripts/verificar_configuracion.py`       | Imprime por consola la sala normalizada y los nicks que se generarán, sin conectar con el servidor. |
| `ontologia/`                               | Ontología del sistema: constructores y validador de los mensajes FIPA-ACL. No se edita. |
| `agentes/reglas_juego.py`                  | Lógica pura del tres en raya, compartida por el tablero y el jugador de referencia. |
| `tests/`                                   | Serie de validación de la rama, incluido el arnés de simulación de los agentes del alumno. |

| Fichero del alumno                              | Cómo se aporta |
|-------------------------------------------------|----------------|
| `agentes/agente_jugador.py` (`AgenteJugador`)   | El alumno copia su clase del proyecto del curso, o parte de la implementación de referencia. |
| `agentes/agente_tablero.py` (`AgenteTablero`)   | El alumno copia su clase del proyecto del curso, o parte de la implementación de referencia. |
| `agentes/` auxiliares, `behaviours/`, `estrategia/`, `web/`, etc. | El alumno los conserva sin alteraciones. |

> La rama del profesor incluye, dentro de `agentes/`, una
> **implementación de referencia** de `AgenteTablero` y
> `AgenteJugador` que resuelve correctamente los tres protocolos de
> la ontología (registro, partida e informe) y supera la serie de
> pruebas. El alumno puede partir de ella y sustituir solo su
> estrategia, o reemplazarla por completo por sus propias clases. El
> procedimiento de enlace y el contrato que deben cumplir los
> agentes están en
> [`doc/INTEGRACION_AGENTES_ALUMNO.md`](doc/INTEGRACION_AGENTES_ALUMNO.md).


## 4. Configuración (`config/config.yaml`)

El alumno solo edita el bloque `alumno`. Todos los campos están
documentados con comentarios en el propio YAML.

```yaml
alumno:
  usuario_uja: <usuario_uja>          # parte local del JID del alumno
  nick_tablero: ""                    # opcional: nick base de los tableros
  nick_jugador: ""                    # opcional: nick base de los jugadores
  modalidad: examen                   # 'examen' el día de la prueba
  submodo: <grupo|individual>         # el profesor anuncia cuál
  pc: PC-NN                           # solo si submodo=individual
  niveles_estrategia: [<niveles>]     # niveles a probar (1, 2, 3, 4)
```

| Campo | Obligatorio | Significado |
|-------|-------------|-------------|
| `usuario_uja` | sí | Parte local del JID del alumno (`<usuario_uja>@sinbad2.ujaen.es`). |
| `nick_tablero` | no | Nick base de los tableros en la sala MUC. Si está vacío, se usa `usuario_uja`. La utilidad de creación añade un sufijo `-NN` único por tablero. |
| `nick_jugador` | no | Nick base de los jugadores. Igual que el anterior, con sufijo `-n<L>-NN` que incluye el nivel de estrategia. |
| `modalidad` | sí | Para la prueba debe valer `examen`. Las modalidades `laboratorio` y `torneo` se conservan para uso en clase. |
| `submodo` | sí en `examen` | `grupo` (sala única `examen@examen.<dominio>`) o `individual` (sala por puesto `<pc>@examen.<dominio>`). |
| `pc` | sí en `individual` | Identificador del puesto del aula (`PC-01`…`PC-30`). El lanzador lo canoniza, por lo que `PC-5`, `pc-05`, `PC_5` o `pc 5` resuelven todos a `pc-05`. |
| `niveles_estrategia` | sí | Lista de niveles que jugarán los jugadores generados. En `examen` individual los doce jugadores se reparten uniformemente entre los niveles indicados. |

**El alumno no debe modificar `xmpp.servicio_muc` ni
`xmpp.sala_tictactoe`.** El lanzador detecta `modalidad: examen` y
redirige el componente MUC y el nombre de la sala automáticamente
según `submodo`.


## 5. Verificación visual antes del examen

Antes de cualquier conexión real, el script

```bash
python scripts/verificar_configuracion.py
```

imprime por consola la sala MUC destino, el nombre del puesto
canonizado y la tabla completa de agentes que `main.py` creará, con
el nick único asignado a cada uno y un aviso si dos coincidieran.
El alumno puede comprobar así, sin red, que sus campos del bloque
`alumno` producen exactamente lo que espera.


## 6. Utilidad de finalización del examen (opcional)

`utils.py` ofrece la función `registrar_cierre_ordenado_examen`,
que detiene un agente cuando el supervisor del profesor expulsa a
los ocupantes (código MUC 307) o destruye la sala (código MUC 332)
al terminar la prueba. Sin ella, los agentes quedarían esperando
mensajes que ya no van a llegar o fallarían al enviar a una sala
inexistente.

Se ofrece de **dos formas equivalentes**; el alumno elige una:

- **Automática.** Cuando los agentes se crean con la factoría
  `crear_agente` de `utils.py` (lo que hace `main.py` por defecto),
  la utilidad **queda instalada sin intervención del alumno**. No
  hay nada que escribir. Es el comportamiento normal de la rama.
- **Manual.** Si el alumno prefiere arrancar sus agentes fuera de
  `crear_agente`, puede registrar la utilidad en el `setup()` de
  cada clase. La implementación de referencia
  `agentes/agente_tablero.py` y `agentes/agente_jugador.py`
  contiene la integración explícita y comentada:

  ```python
  from utils import (
      registrar_cierre_ordenado_examen,
      unirse_a_sala_muc,
  )

  async def setup(self) -> None:
      sala_muc = self.config_xmpp["sala_muc_completa"]
      self.client.register_plugin("xep_0045")

      # OPCIONAL: detección del cierre del examen por el supervisor.
      registrar_cierre_ordenado_examen(self, sala_muc)

      unirse_a_sala_muc(self, sala_muc)
      # ... resto del setup del alumno ...
  ```

La utilidad **no es obligatoria** para superar el examen: un alumno
que prefiera detener sus agentes con `Ctrl+C` al terminar puede
omitirla por completo. Los detalles, incluido el mensaje que aparece
en consola al activarse, están en
[`doc/AVISO_ERRORES_EXAMEN.md`](doc/AVISO_ERRORES_EXAMEN.md).


## 7. Ejecución el día del examen

```bash
git checkout examen-ssmmaa
# (Solo si la estrategia usa LLM, nivel 4) Seleccionar el perfil LLM
# en config/config.yaml: llm.perfil_activo = gemini | servidor
# (por defecto es "ninguno" y el sistema arranca sin LLM). Si se
# elige "gemini", exportar además la clave personal de AI Studio:
export GOOGLE_API_KEY="<clave_personal_de_AI_Studio>"
python main.py
```

`main.py` registra al arrancar:

1. La sala MUC destino normalizada (lo que el alumno ya vio con
   `verificar_configuracion.py`).
2. El resultado de la sonda del supervisor. Si la sala no existe,
   aborta con código 7 y un mensaje que incluye la marca `[Examen]`
   enviada por el servidor.
3. La creación de cada agente con su JID y su nick MUC.

Cuando el profesor anuncie el fin del examen, basta con `Ctrl+C`.
Si el alumno ha integrado la utilidad opcional de finalización, sus
agentes se habrán detenido por sí mismos al recibir la presencia de
cierre del supervisor.


## 8. Recursos

- [`doc/INSTRUCCIONES_EXAMEN_ALUMNO.md`](doc/INSTRUCCIONES_EXAMEN_ALUMNO.md) —
  Guía paso a paso para crear y publicar la rama `examen-ssmmaa`.
- [`doc/INTEGRACION_AGENTES_ALUMNO.md`](doc/INTEGRACION_AGENTES_ALUMNO.md) —
  Cómo enlazar los agentes del alumno en la rama, el contrato que
  deben cumplir y cómo verificarlos con la serie de pruebas.
- [`doc/PROBLEMAS_FRECUENTES_EXAMEN.md`](doc/PROBLEMAS_FRECUENTES_EXAMEN.md) —
  El JID frente al nick y el uso correcto de la factoría.
- [`doc/AVISO_ERRORES_EXAMEN.md`](doc/AVISO_ERRORES_EXAMEN.md) —
  Aviso del rechazo del servidor antes del examen y utilidad de
  finalización.
- `agentes/agente_tablero.py`, `agentes/agente_jugador.py` —
  Implementación de referencia de los tres protocolos de la ontología.
- `tests/README.md` — Serie de validación de la rama.
- <https://aistudio.google.com/apikey> — Clave gratuita de Google
  AI Studio para los alumnos con estrategia de nivel 4.
- [`LICENSE`](LICENSE) — Licencia del repositorio.
