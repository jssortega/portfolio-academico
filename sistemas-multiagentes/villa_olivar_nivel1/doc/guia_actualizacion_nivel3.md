# Guía de actualización al Nivel 3

## Del Nivel 2 (SPADE-LLM + ADK) al Nivel 3 (ADK + A2A)

Esta guía describe **qué cambia** al pasar del Nivel 2 al Nivel 3 y
**qué pasos** debe dar el grupo. El Nivel 3 sustituye la comunicación
XMPP/FIPA-ACL por el protocolo **A2A sobre HTTP**. La capa de
razonamiento (ADK) y la capa de dominio (`logica/`) se conservan
intactas.

> El detalle de cómo se escribe cada agente sobre la clase base está en
> [`guia_base_agente_a2a.md`](guia_base_agente_a2a.md). Esta guía se
> centra en la **migración**; aquella, en la **construcción** de los
> agentes.

---

## 1. Antes de empezar

### 1.1. Requisitos previos

Verifica que tienes completado:

- [ ] Nivel 2 entregado y etiquetado (`entrega-nivel2`).
- [ ] Los cinco agentes SPADE-LLM funcionan con `FunctionTool` ADK.
- [ ] Los prompts de `prompts/` están afinados y producen salidas JSON interpretables.
- [ ] Guiones 8 y 9 completados (agente eco A2A + agente inteligente A2A).
- [ ] Temas 8, 9 y 10 de clases expositivas completados.
- [ ] Docker instalado y funcionando.
- [ ] Python 3.12+ disponible.

### 1.2. Software necesario

| Software | Versión mínima | Comando de verificación |
|----------|---------------|------------------------|
| Python | 3.12 | `python --version` |
| Docker | 24.0 | `docker --version` |
| Docker Compose | 2.20 | `docker compose version` |
| Git | 2.40 | `git --version` |
| pip | 23.0 | `pip --version` |

---

## 2. Obtener la rama de desarrollo

### 2.1. Actualizar el repositorio

```bash
git checkout main
git pull origin main
```

### 2.2. Obtener la rama desarrollo-nivel3

```bash
# Si la rama viene del repositorio upstream (profesor)
git fetch upstream desarrollo-nivel3
git checkout -b desarrollo-nivel3 upstream/desarrollo-nivel3
git push -u origin desarrollo-nivel3

# Si la rama ya existe en local
git checkout desarrollo-nivel3
git pull origin desarrollo-nivel3
```

### 2.3. Crear ramas personales

```bash
git checkout desarrollo-nivel3
git checkout -b nombre-apellido
git push -u origin nombre-apellido
```

---

## 3. Instalar dependencias

### 3.1. Crear un entorno virtual nuevo

Se recomienda un entorno virtual específico para el Nivel 3: las
dependencias cambian (se elimina SPADE-LLM):

```bash
python -m venv venv-nivel3
source venv-nivel3/bin/activate        # Linux/macOS
# venv-nivel3\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 3.2. Cambios en las dependencias

El transporte A2A del Nivel 3 **no usa `a2a-sdk`**. El servidor HTTP y
el despacho de los métodos JSON-RPC se construyen con **`aiohttp`** (ya
presente desde el Nivel 2). El motivo está en
[`guia_base_agente_a2a.md`](guia_base_agente_a2a.md) §4: el supervisor
del Nivel 3 emplea el método `tasks/send`, que la clase
`A2AStarletteApplication` de `a2a-sdk` no reconoce.

```txt
# Preservadas del Nivel 2
google-adk                    # Framework de agentes LLM
ollama                        # Cliente Ollama
httpx                         # Cliente HTTP asíncrono
aiohttp                       # Servidor HTTP del transporte A2A
litellm                       # Abstracción multi-LLM
pydantic>=2.0                 # Modelos de datos
pyyaml                        # Configuración YAML
jsonschema                    # Validación JSON Schema

# Nuevas en el Nivel 3
google-generativeai           # Cliente de la API de Gemini

# Eliminadas en el Nivel 3
# spade>=4.1.2                # Ya no se usa SPADE
# spade-llm                   # Ya no se usa SPADE-LLM

# Pruebas
pytest
pytest-asyncio
pytest-timeout
```

### 3.3. Verificar las instalaciones

```bash
# Verificar el servidor HTTP del transporte A2A
python -c "from aiohttp import web; print('aiohttp OK')"

# Verificar ADK
python -c "from google.adk.agents import LlmAgent; print('ADK OK')"

# Verificar el paquete del contrato externo (modelos Pydantic del Nivel 3)
python -c "from contrato.alerta_emergencia import AlertaEmergencia; print('Contrato OK')"

# Verificar LiteLLM
python -c "import litellm; print('LiteLLM OK')"
```

---

## 4. Configurar la infraestructura

### 4.1. Docker: solo Ollama

En el Nivel 3, el servidor XMPP (Prosody) ya **no es necesario**. La
comunicación entre agentes se realiza vía HTTP/A2A. Solo se necesita
Ollama (si se elige un perfil de LLM local):

```bash
docker compose up -d ollama
curl http://localhost:11434          # Salida esperada: Ollama is running
docker exec ollama-ssmmaa ollama pull llama3.2:3b
```

### 4.2. Configuración: `config.yaml` y `agents.yaml`

El Nivel 3 separa la configuración en dos ficheros, **ya provistos en
la raíz**:

- **`config.yaml`** — conexiones: perfil de red y registro REST
  (`red`), parámetros del transporte HTTP (`a2a`), perfiles de modelo
  de lenguaje (`llm`) y comportamiento del lanzador (`lanzamiento`).
- **`agents.yaml`** — definición de los cinco agentes: rol,
  visibilidad, puerto, módulo y clase.

El grupo **personaliza**, no reescribe, estos ficheros:

- En `config.yaml`: el `host_por_defecto` de la sección `a2a` (la IP
  del PC del aula) y los perfiles activos de `red` y `llm`.
- En `agents.yaml`: la visibilidad de cada especialista (dos públicos,
  dos privados) y, en el bloque `parametros.privados` de la Centralita,
  las URL locales de los privados.

El formato exacto de `agents.yaml` está documentado en
[`AGENTES_A2A.md`](AGENTES_A2A.md) §7.

---

## 5. Migración de los agentes

### 5.1. Resumen de cambios por fichero

| Fichero | Acción | Detalle |
|---------|--------|---------|
| `logica/*.py` | **Sin cambios** | Las funciones puras se preservan intactas |
| `herramientas/*.py` | **Sin cambios** | Las `FunctionTool` se reutilizan directamente |
| `prompts/*.txt` | **Sin cambios** | Se trasladan como `instruction` del `LlmAgent` |
| `contrato/` | **Integrar** | Paquete Pydantic con los modelos vinculantes del Nivel 3 (`AlertaEmergencia`, `InformeResolucion`, `EventoTraza`, `ConsultaEstado`, `EstadoAgente`, `AgentCard`). Se serializa como `DataPart` en los Tasks A2A. |
| `config.yaml`, `agents.yaml` | **Personalizar** | Provistos; solo se ajustan los valores del grupo |
| `agentes/base_agente_a2a.py` | **No tocar** | Clase base provista: transporte HTTP y despacho A2A |
| `main.py` | **No tocar** | Lanzador provisto: lee `config.yaml` y `agents.yaml` |
| `agentes/agente_*.py` | **Escribir** | Los cinco agentes, como subclases de `BaseAgenteA2A` |
| `descubrimiento/` | **Reescribir** | De DF/MUC a registro REST + Agent Cards |
| `tests/` | **Ampliar** | Nuevas pruebas A2A |

El trabajo de programación del grupo se concentra en **las cinco
subclases de agente**, el **cliente del registro** y las **pruebas**.
La infraestructura A2A (servidor, despacho, ciclo de vida) la aporta la
clase base.

### 5.2. La clase base ya está escrita

`agentes/base_agente_a2a.py` contiene `BaseAgenteA2A`, que monta el
servidor `aiohttp`, publica la tarjeta de agente, despacha los métodos
JSON-RPC (`tasks/send`, `tasks/get`, `tasks/sendSubscribe`), valida la
`AlertaEmergencia` contra el contrato y traduce las excepciones a Tasks
`failed`. El grupo **no la modifica**: hereda de ella.

Esto sustituye a la composición `A2AStarletteApplication` +
`AgentExecutor` que se estudió en el Guión 9: aquel montaje, basado en
`a2a-sdk`, solo habla el método `message/send` y no serviría para el
`tasks/send` del Nivel 3 (ver [`guia_base_agente_a2a.md`](guia_base_agente_a2a.md) §4 y §5).

### 5.3. Migrar cada agente

Cada agente pasa de ser un agente SPADE-LLM a una **subclase de
`BaseAgenteA2A`** que construye su `LlmAgent` e implementa
`manejar_alerta`.

**Antes (Nivel 2):**

```python
from agentes.base_agente_llm import AgenteVillaOlivarLLM

class AgenteBomberos(AgenteVillaOlivarLLM):
    async def setup(self):
        await super().setup()
        # Registrar herramientas y behaviours
```

**Después (Nivel 3):**

```python
from agentes.base_agente_a2a import BaseAgenteA2A, EspecificacionAgente
from contrato.alerta_emergencia import AlertaEmergencia
from contrato.informe_resolucion import InformeResolucion

from google.adk.agents import LlmAgent
from herramientas.herramientas_bomberos import herramientas_bomberos


class AgenteBomberos(BaseAgenteA2A):

    def __init__(self, especificacion: EspecificacionAgente) -> None:
        super().__init__(especificacion)
        self._llm = LlmAgent(
            name="bomberos_villa_olivar",
            instruction=self._leer_prompt("bomberos"),
            tools=herramientas_bomberos(),
            model=self._configurar_modelo(),
        )

    async def manejar_alerta(
        self,
        alerta: AlertaEmergencia,
    ) -> InformeResolucion:
        # Reutiliza la invocación al Runner de ADK del Nivel 2.
        ...
```

El paso a paso de la construcción de cada subclase (especialistas y
Centralita), el razonamiento de ADK y el registro de manejadores de
Contract Net están en [`guia_base_agente_a2a.md`](guia_base_agente_a2a.md)
§6, §7 y §8.

### 5.4. La tarjeta de agente se compone por código

En el Nivel 3 **no hay ficheros JSON de tarjetas de agente**. Cada
subclase obtiene una tarjeta válida por defecto de la base; si quiere
declarar habilidades propias, sobrescribe `construir_agent_card` y
compone el `AgentCard` en código a partir de la especificación.

### 5.5. Actualizar el descubrimiento

El cliente del registro REST (`descubrimiento/`) sustituye al
Directory Facilitator de XMPP. Da de alta al agente público al
arrancar, mantiene la señal de vida (*heartbeat*), descubre agentes de
otros grupos y se da de baja al apagarse. Su uso desde el ciclo de
vida del agente está en
[`guia_base_agente_a2a.md`](guia_base_agente_a2a.md) §9.

### 5.6. Ampliar las pruebas

Crear los nuevos ficheros de test:

- `tests/test_agent_cards.py` — Validación de la tarjeta que compone `construir_agent_card`.
- `tests/test_agente_a2a.py` — Pruebas de agentes A2A individuales.
- `tests/test_integracion_a2a.py` — Pruebas de integración.
- `tests/test_negociacion_a2a.py` — Pruebas de Contract Net sobre A2A.
- `tests/test_interoperabilidad.py` — Pruebas entre grupos.

---

## 6. Verificación rápida

### 6.1. Arrancar el sistema

```bash
# 1. Arrancar Ollama (si el perfil LLM activo es local)
docker compose up -d ollama

# 2. Arrancar los cinco agentes
python main.py
```

### 6.2. Verificar un agente

```bash
# Tarjeta de agente de la Centralita
curl http://localhost:8110/.well-known/agent.json

# Enviar un Task de prueba con tasks/send
curl -X POST http://localhost:8110/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tasks/send",
    "params": {
      "id": "test-001",
      "message": {
        "role": "user",
        "parts": [
          {
            "type": "data",
            "data": {
              "id_emergencia": "e-001",
              "descripcion": "Incendio en la calle Olivos 12"
            }
          }
        ]
      }
    }
  }'
```

Una respuesta con `result.status.state` igual a `completed` indica que
el agente acepta y procesa la tarea. El catálogo de causas por las que
un agente «no acepta tareas» está en
[`resolucion_a2a_porque_no_acepta_tareas.md`](resolucion_a2a_porque_no_acepta_tareas.md)
de la rama `examen-alumno`.

### 6.3. Verificar la batería de pruebas

```bash
pytest tests/test_integracion_a2a.py -v --timeout=120
```

---

## 7. Elección del modelo LLM

Los modelos disponibles son los mismos del Nivel 2:

| Modelo | Descarga | RAM | Equipo mínimo | Calidad |
|--------|----------|-----|---------------|---------|
| `llama3.2:3b` | ~2.0 GB | ~5 GB | 8 GB RAM, 4 cores | Básica |
| `gemma3:4b` | ~3.3 GB | ~6 GB | 8 GB RAM, 4 cores | Buena |
| `llama3:8b` | ~4.7 GB | ~10 GB | 16 GB RAM, 8 cores | Alta |

El perfil por defecto de la prueba evaluativa es **Gemini**, para que
todos los grupos consuman el mismo modelo. El perfil activo se elige en
`config.yaml`, sección `llm`.

> **Nota:** cada agente ejecuta su propio `LlmAgent`, pero todos
> comparten la misma instancia de Ollama (en los perfiles locales). El
> rendimiento depende de cuántos agentes procesen peticiones a la vez.

---

## 8. Resolución de problemas

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: contrato` | Integrar el paquete `contrato/` en la rama. |
| `ModuleNotFoundError` (aiohttp, pydantic) | `pip install -r requirements.txt`. |
| `Address already in use` en un puerto | Otro proceso ocupa el puerto. Verificar con `lsof -i :8110` y detenerlo. |
| El agente responde `-32601` a un `tasks/send` | Se está delegando el enrutado en `a2a-sdk`. El despacho de `tasks/send` lo hace `BaseAgenteA2A`; ver `guia_base_agente_a2a.md` §4. |
| Tarjeta de agente no accesible | Verificar que `main.py` está en ejecución y el puerto es correcto. |
| Task devuelve `failed` | Revisar el registro de trazas. Probablemente el LLM no está disponible. |
| Timeout al contactar otro agente | Verificar que el agente destino está activo. Aumentar el timeout en `httpx`. |
| `Connection refused` a Ollama | `docker compose up -d ollama` y verificar con `curl http://localhost:11434`. |

---

## 9. Entrega

### 9.1. Documento de verificación

El grupo debe incluir `doc/guia_verificacion_nivel3.md` con:

**Sección A — Pruebas automatizadas:**
1. Cómo arrancar Ollama y descargar el modelo.
2. Comando exacto para ejecutar las pruebas.
3. Salida esperada según el hito al que aspira el grupo.

**Sección B — Ejecución de prueba del sistema:**
1. Cómo arrancar los cinco agentes A2A (`python main.py`).
2. Cómo verificar que las tarjetas de agente son accesibles.
3. Cómo enviar un escenario de emergencia con `curl`.
4. Traza de ejemplo de la salida esperada.

### 9.2. Procedimiento de entrega

```bash
# 1. Generar el resultado de las pruebas
pytest tests/ -v > resultado_tests_nivel3.txt 2>&1
git add resultado_tests_nivel3.txt
git commit -m "Añadir el resultado de las pruebas del Nivel 3"

# 2. Etiquetar la entrega
git checkout main
git merge desarrollo-nivel3
git tag -a entrega-nivel3 -m "Entrega Nivel 3 — Villa Olivar"
git push origin main --tags
```

### 9.3. Contenido obligatorio

- Todos los ficheros fuente de `logica/`, `agentes/`, `herramientas/`, `prompts/`, `descubrimiento/` y `tests/`.
- El paquete `contrato/` con los modelos Pydantic vinculantes del Nivel 3.
- Los ficheros `config.yaml`, `agents.yaml`, `main.py`, `requirements.txt` y `docker-compose.yml`.
- El fichero `resultado_tests_nivel3.txt`.
- El documento de verificación (`doc/guia_verificacion_nivel3.md`).
- La documentación del proyecto en `doc/`.

---

*Guía de actualización al Nivel 3 — Proyecto Villa Olivar — Sistemas Multiagente — Universidad de Jaén*
