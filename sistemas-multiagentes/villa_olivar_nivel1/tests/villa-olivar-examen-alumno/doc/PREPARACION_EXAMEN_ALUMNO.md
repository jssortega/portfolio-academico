# Preparación de la rama `examen-alumno` con el material del Nivel 3

Este documento describe cómo el grupo prepara **esta rama**
(`examen-alumno`) para la sesión del examen, trayendo
selectivamente lo que necesite de su rama `desarrollo-nivel3`
sin fusionar ambas. La rama `desarrollo-nivel3` **queda intacta**:
sigue siendo el espacio donde el grupo puede hacer modificaciones
del proyecto general sin contaminarla con el código y los tests
específicos del examen.

> ## Regla operativa
>
> - `desarrollo-nivel3` → rama de trabajo continuo del grupo. No
>   se mezcla con el material del examen.
> - `examen-alumno` → rama operativa del examen. Aquí viven los
>   tests del profesor, la factoría, los modelos del contrato y
>   los agentes adaptados que se demostrarán y evaluarán. El
>   grupo trae de `desarrollo-nivel3` solo lo que necesite
>   reutilizar.

---

## 1. Qué traes y por qué

| Recurso | Para qué sirve |
|---------|----------------|
| `contrato/` | Modelos Pydantic del contrato externo (Agent Card, AlertaEmergencia, InformeActuacion, InformeResolucion, Traza...). Son la **fuente de verdad**: lo que el Coordinador del profesor enviará y validará el día del examen. |
| `cliente_pruebas/cliente.py` | Cliente A2A asíncrono que las pruebas usan internamente. No es código que el grupo escriba, pero los tests lo importan. |
| `tests/profesor/` | 118 tests con los que el grupo verifica su propio sistema antes del examen (los mismos que ejecutará el profesor). |
| `factoria/` | Clase base `AgenteA2A` que garantiza que todos los grupos arrancan sus agentes con la misma estructura externa (Agent Card en `/.well-known/agent.json`, extremo único `POST /`, JSON-RPC sobre `tasks/send` / `tasks/get` / `tasks/sendSubscribe`). |
| `config/config.yaml` y `config/agents.yaml.ejemplo` | Esquemas de configuración homogéneos para el lanzador `main.py`. |
| `main.py` | Lanzador modelo que el grupo arranca con `python main.py`. |

---

## 2. Calendario

Esta rama se **publica al mismo tiempo** que la rama
`coordinador-profesor`, en la última sesión de prácticas. A
partir de ese momento el grupo dispone del tiempo restante hasta
la entrega para:

1. Cambiar a la rama `examen-alumno` y traer selectivamente de
   `desarrollo-nivel3` los módulos reutilizables (ver §3).
2. Adaptar sus agentes a la factoría (ver §4).
3. Escribir los tests del propio grupo según
   [`ESCENARIOS_TESTS_OBLIGATORIOS.md`](ESCENARIOS_TESTS_OBLIGATORIOS.md).
4. Ejecutar la serie de validación en su equipo (perfil `local`
   en Docker) hasta que pasen los hitos a los que aspira.

Durante todo el proceso, `desarrollo-nivel3` se mantiene
intacta. Si el grupo necesita seguir trabajando en mejoras del
sistema general que no son específicas del examen, lo hace allí
y, cuando proceda, vuelve a traer los archivos puntuales a
`examen-alumno` con la misma técnica del §3.

---

## 3. Incorporación selectiva desde `desarrollo-nivel3`

La rama `examen-alumno` ya trae los componentes específicos del
examen (modelos del contrato, factoría, serie de validación, cliente
A2A, configuración homogénea y lanzador). El grupo solo necesita
sumarle los **módulos reutilizables del Nivel 2/3** que ya tenga
en su `desarrollo-nivel3`.

### 3.1. Qué traer y qué dejar fuera

| Módulo de `desarrollo-nivel3` | Acción en `examen-alumno` |
|-------------------------------|---------------------------|
| `logica/` (funciones puras de dominio) | **Traer tal cual.** Son funciones sin dependencias de SPADE ni ADK. Se reutilizan desde los agentes nuevos como ya se hacía en el Nivel 2. |
| `herramientas/` (FunctionTool de ADK) | **Traer tal cual.** Las `FunctionTool` envuelven la lógica y son utilizables desde las clases que hereden de la factoría. |
| `prompts/` (prompts de sistema) | **Traer tal cual.** El texto del prompt es independiente del transporte. |
| `ontologia/` o esquemas auxiliares propios del grupo | **Traer tal cual** si los agentes los siguen necesitando. |
| `agentes/` (agentes SPADE/SPADE-LLM del Nivel 2) | **No traer directamente.** En su lugar, reescribir cada agente como subclase de `factoria.AgenteA2A` (ver §4), reutilizando la lógica y los prompts. |
| `config.yaml` raíz del Nivel 2 (XMPP, perfiles LLM antiguos) | **No traer.** La configuración de `examen-alumno` ya cubre lo necesario en `config/config.yaml`. Si hay parámetros propios del grupo, copiarlos a mano al fichero nuevo. |
| `tests/` del Nivel 2 | **No traer directamente.** Los tests del Nivel 2 se ejecutaban contra SPADE; aquí ya no aplican. Los tests del grupo en `examen-alumno` se escriben de nuevo según [`ESCENARIOS_TESTS_OBLIGATORIOS.md`](ESCENARIOS_TESTS_OBLIGATORIOS.md), pudiendo reutilizar las funciones puras como referencia. |

### 3.2. Cómo traer los archivos sin fusionar las ramas

Desde la rama `examen-alumno`, con el árbol de trabajo limpio,
se puede traer un directorio (o un fichero suelto) directamente
del último commit de `desarrollo-nivel3` sin fusionar historia:

```bash
git checkout examen-alumno

# Traer carpetas completas desde desarrollo-nivel3 (se quedan
# como modificaciones locales sin tocar la otra rama).
git checkout desarrollo-nivel3 -- logica/
git checkout desarrollo-nivel3 -- herramientas/
git checkout desarrollo-nivel3 -- prompts/

# Verificar y commitear cuando esté listo.
git status
git add logica/ herramientas/ prompts/
git commit -m "Incorporar lógica, herramientas y prompts desde desarrollo-nivel3"
```

Si solo hace falta un fichero concreto, el mismo patrón sirve a
nivel de fichero:

```bash
git checkout desarrollo-nivel3 -- logica/logica_bomberos.py
```

### 3.3. Mantener `desarrollo-nivel3` viva en paralelo

`desarrollo-nivel3` no se modifica por estas operaciones: `git
checkout <rama> -- <ruta>` copia ficheros de esa rama al árbol
de trabajo de la rama actual, pero no toca la rama de origen.
El grupo puede seguir desarrollando allí (mejoras, refactors,
documentación, etc.) y, cuando un cambio sea relevante para el
examen, repetir el `git checkout` selectivo en `examen-alumno`.

> **Aviso.** Si se quiere traer una versión modificada de un
> fichero, hay que asegurarse de que el commit donde está esa
> versión existe en `desarrollo-nivel3` (un `git push` en local
> o `git fetch` desde el remoto, según corresponda) **antes** de
> hacer el `git checkout` selectivo en `examen-alumno`.

### 3.4. Si se trabaja en clones separados

Algunos grupos prefieren tener dos directorios distintos, uno
por rama, en lugar de cambiar de rama en el mismo directorio.
En ese caso, la copia se hace con `cp` desde el clon de
`desarrollo-nivel3` al clon de `examen-alumno`, seguido del
`git add` y el commit en `examen-alumno`. El efecto es el
mismo: `desarrollo-nivel3` queda intacta y `examen-alumno`
recibe solo lo necesario.

---

## 4. Adaptación de los agentes a la factoría

La factoría asume que cada agente del grupo es una **subclase**
de `factoria.AgenteA2A` que vive en su propio módulo. La
adaptación mínima de un agente del Nivel 2 al Nivel 3 es:

```python
# agentes/centralita.py
from factoria import AgenteA2A
from contrato.alerta_emergencia import AlertaEmergencia
from contrato.informe_resolucion import InformeResolucion


class Centralita(AgenteA2A):
    """Centralita 112 del grupo."""

    async def manejar_alerta(
        self, alerta: AlertaEmergencia,
    ) -> InformeResolucion:
        # 1. Clasificar la alerta (LLM + FunctionTool del Nivel 2).
        # 2. Decidir qué especialistas convocar.
        # 3. Enviar subtareas a cada especialista por A2A.
        # 4. Agregar los InformeActuacion en un InformeResolucion.
        # 5. Devolverlo.
        ...
```

El método `manejar_alerta` es **el único obligatorio**. La
factoría se encarga del servidor HTTP, de servir la Agent Card,
de validar la `AlertaEmergencia` entrante con Pydantic y de
empaquetar el `InformeResolucion` como cuerpo JSON-RPC.

Para enriquecer la Agent Card con habilidades específicas del
rol, sobrescribir `construir_agent_card`:

```python
from contrato.agent_card import AgentCard, Habilidad

def construir_agent_card(self) -> AgentCard:
    card = super().construir_agent_card()
    card.skills.append(
        Habilidad(
            id="contract_net_cfp",
            name="Convocatoria de propuestas",
            description="Atiende CFP de subtareas de extinción.",
            tags=["bomberos", "contract_net"],
        ),
    )
    return card
```

Para implementar Contract Net (Hito 4), registrar handlers
adicionales:

```python
async def _handler_cfp(params):
    return {"propuestas": [...]}

self.registrar_handler("contract_net/cfp", _handler_cfp)
```

---

## 5. Conexión con el registro REST

La factoría **no** se inscribe automáticamente en el registro
REST: la inscripción depende de los privados, del catálogo de
habilidades reales del grupo y de la política de señal de vida
que el grupo elija (Hito 5). El alumno debe implementar esa
inscripción en su agente concreto, leyendo
`config.red.perfiles[<perfil_activo>].registro_central` y
emitiendo las peticiones REST correspondientes (consultar
`doc/registro_rest_para_clientes.md` de la rama
`desarrollo-nivel3`).

---

## 6. Ejecución conjunta

Con todo en su sitio:

```bash
# 1. Levantar la infraestructura local (perfil "local" de config.yaml).
git clone https://gitlab.com/ssmmaa/infraestructurassmmaa/ssmmaa-infraestructura.git
cd ssmmaa-infraestructura && make build && make up && make pull-modelo
cd -

# 2. Copiar agents.yaml.ejemplo a agents.yaml y ajustar.
cp config/agents.yaml.ejemplo config/agents.yaml

# 3. Arrancar el sistema multiagente.
python main.py

# 4. En otra terminal, ejecutar la serie de validación.
pytest tests/profesor/integracion/ -v
```

La primera vez todos los tests fallarán por
`httpx.ConnectError` o por `Task.failed`. Cada hito superado
elimina fallos. El objetivo es llegar al examen con la serie de validación
en verde.

---

## 7. Lo que no se debe modificar

- **`contrato/`**: cambiar un modelo Pydantic rompe el contrato
  externo. Lo que el grupo necesite ampliar debe ser un campo
  opcional adicional en su informe, pero los campos obligatorios
  no se pueden tocar.
- **`tests/profesor/`**: el Coordinador del profesor ejecuta
  estos mismos tests el día del examen. Modificarlos o
  comentarlos no aumenta la nota.
- **`factoria/agente_a2a.py`**: la firma del extremo HTTP y el
  esquema de la Agent Card forman parte del contrato. La
  factoría está diseñada para extenderse, no para modificarse.
- **La rama `desarrollo-nivel3` (en su conjunto)**: durante la
  preparación del examen no se fusiona ni se reescribe. Sigue
  siendo el espacio donde el grupo puede continuar el trabajo
  general del proyecto sin contaminarlo con código y tests
  específicos del examen. Los cambios viajan en una sola
  dirección: de `desarrollo-nivel3` a `examen-alumno`, y solo a
  nivel de archivo, mediante la incorporación selectiva del §3.

Cualquier extensión funcional se hace en clases concretas del
grupo (`agentes/*.py`) o registrando handlers personalizados a
través de `AgenteA2A.registrar_handler(...)`.
