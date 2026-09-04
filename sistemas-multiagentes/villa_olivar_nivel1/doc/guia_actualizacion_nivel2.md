# Guia de actualizacion al Nivel 2 y entrega en PLATEA

**Asignatura:** Sistemas Multiagente — Grado en Ingenieria Informatica
**Universidad de Jaen — Departamento de Informatica**
**Curso:** 2025-2026

---

## 1. Antes de empezar

Antes de actualizar vuestro proyecto, aseguraos de que cumplís estos
requisitos:

- Tenéis el **Nivel 1 completado**: los cinco agentes SPADE funcionan, la
  lógica de dominio está separada en `logica/`, las pruebas pasan y la
  rama `desarrollo-nivel1` está cerrada y fusionada en `main`.
- Habéis completado los **Guiones 4, 5 y 6** de prácticas (MCP, ADK y
  SPADE-LLM respectivamente).
- Tenéis **Docker** instalado y funcionando en vuestro equipo:
  - **Windows / macOS:** [Docker Desktop](https://www.docker.com/products/docker-desktop/)
    (en Windows requiere WSL2).
  - **Linux:** [Docker Engine](https://docs.docker.com/engine/install/) con
    el complemento (*plugin*) Compose.
- Tenéis **Git** configurado y acceso de escritura al repositorio del grupo.

---

## 2. Obtener la rama de desarrollo del Nivel 2

El profesor ha publicado la rama `desarrollo-nivel2` en el repositorio base.
Esta rama contiene los ficheros nuevos y las modificaciones necesarias para
el Nivel 2. Seguid estos pasos **un solo miembro del grupo** (el que vaya a
integrar):

```bash
# 1. Situarse en la rama main y asegurarse de estar al día
git checkout main
git pull origin main

# 2. Obtener la rama desarrollo-nivel2 del repositorio del profesor
#    (si el remote del profesor se llama "upstream")
git fetch upstream desarrollo-nivel2

# 3. Crear la rama local a partir de la del profesor
git checkout -b desarrollo-nivel2 upstream/desarrollo-nivel2

# 4. Subir la rama al repositorio del grupo
git push -u origin desarrollo-nivel2
```

> **Nota:** si vuestro repositorio ya tiene configurado el *remote* del
> profesor como `upstream`, el paso 2 funcionará directamente. Si no, añadidlo
> primero:
> ```bash
> git remote add upstream <URL_DEL_REPOSITORIO_DEL_PROFESOR>
> ```

### 2.1. Si el grupo trabaja con un *fork*

Si en lugar de un *remote* aparte estáis trabajando con un *fork* del
repositorio del profesor, sincronizad primero vuestro *fork* desde la
interfaz de GitHub (*Sync fork*) y luego:

```bash
git checkout main
git pull origin main
git checkout -b desarrollo-nivel2 origin/desarrollo-nivel2
```

---

## 3. Crear las ramas personales

Cada miembro del grupo crea su rama personal a partir de `desarrollo-nivel2`,
igual que en el Nivel 1:

```bash
git checkout desarrollo-nivel2
git checkout -b nombre-apellido
git push -u origin nombre-apellido
```

---

## 4. Instalar las dependencias del Nivel 2

El Nivel 2 incorpora nuevas dependencias (SPADE-LLM, Google ADK,
Pydantic, etc.). Se recomienda crear un **entorno virtual nuevo** para evitar
conflictos con el del Nivel 1:

```bash
# 1. Crear un entorno virtual específico para el Nivel 2
python -m venv venv-nivel2

# 2. Activar el entorno virtual
source venv-nivel2/bin/activate        # Linux / macOS
# venv-nivel2\Scripts\activate         # Windows (cmd)
# venv-nivel2\Scripts\Activate.ps1     # Windows (PowerShell)

# 3. Instalar todas las dependencias
pip install -r requirements.txt

# 4. Verificar que todo está instalado correctamente
python -c "from spade_llm import LLMAgent, LLMProvider; print('SPADE-LLM OK')"
python -c "from google.adk.tools import FunctionTool; print('ADK OK')"
python -c "from ontologia.modelos_compartidos import DatosEmergencia; print('Ontologia OK')"
```

Si las tres verificaciones imprimen `OK`, el entorno está listo.

---

## 5. Poner en marcha los servicios Docker (Prosody + Ollama)

El servidor XMPP de la asignatura (`sinbad2.ujaen.es`) es **accesible desde
cualquier punto en Internet**, por lo que se puede usar tanto en el laboratorio
como desde casa. No obstante, el proyecto incluye un **respaldo local** en
forma de contenedor Docker (Prosody) para situaciones sin conectividad o para
pruebas aisladas. El servidor LLM (`sinbad2ia.ujaen.es`) **solo es accesible
desde la red del laboratorio**; para trabajar fuera del laboratorio es
**obligatorio** usar el contenedor Docker de Ollama. El fichero
`docker-compose.yml` levanta dos servicios:

- **Prosody** — Servidor XMPP con registro automático de cuentas y soporte
  MUC (`conference.localhost`). Sustituye a `spade run`.
- **Ollama** — Servidor LLM local.

```bash
# 1. Arrancar ambos contenedores (desde la raíz del proyecto)
docker compose up -d

# 2. Comprobar que Prosody (XMPP) responde
nc -zv localhost 5222
# Salida esperada: Connection to localhost port 5222 [...] succeeded!

# 3. Comprobar que Ollama (LLM) responde
curl http://localhost:11434
# Salida esperada: Ollama is running

# 4. Descargar el modelo recomendado para desarrollo
docker compose exec ollama ollama pull llama3.2:3b

# 5. Verificar que el modelo está disponible
docker compose exec ollama ollama list
```

El perfil de conexión se controla en `config.yaml`. Para desarrollo local:

```yaml
perfil_xmpp_activo: "local"    # Prosody en Docker (localhost:5222)
perfil_llm_activo: "local"     # Ollama en Docker (localhost:11434)
```

### 5.1. Elección del modelo

| Modelo | Descarga | RAM necesaria | Equipo mínimo |
|---|---|---|---|
| `llama3.2:3b` | ~2,0 GB | ~5 GB | 8 GB RAM, 4 núcleos (*cores*) |
| `gemma3:4b`   | ~3,3 GB | ~6 GB | 8 GB RAM, 4 núcleos (*cores*) |
| `llama3:8b`   | ~4,7 GB | ~10 GB | 16 GB RAM, 8 núcleos (*cores*) |

Para la mayoría de los portátiles, `llama3.2:3b` es la opción más adecuada.

### 5.2. Verificar la conexión desde Python

```python
import asyncio
from spade_llm import LLMProvider, ContextManager
from spade_llm.context._types import UserMessage

async def verificar():
    proveedor = LLMProvider.create_ollama(model="llama3.2:3b")
    contexto = ContextManager(system_prompt="Responde en espanol, brevemente.")
    mensaje = UserMessage(role="user", content="Hola, responde con una frase corta.")
    contexto.add_message_dict(mensaje, conversation_id="verificacion")
    contexto.set_current_conversation("verificacion")
    respuesta = await proveedor.get_response(contexto)
    print(respuesta)

asyncio.run(verificar())
```

Si obtenéis una respuesta coherente, la cadena completa
Python → LLMProvider → Ollama → modelo funciona correctamente.

> **Capas de compatibilidad (`utils.py`):** el módulo `utils.py` aplica
> automáticamente dos adaptaciones al importarse: (1) habilita SASL
> PLAIN/SCRAM-SHA-1 sobre conexiones XMPP sin TLS (necesario para Prosody
> en Docker sin STARTTLS), y (2) inyecta el método `llm_chat()` en
> `LLMAgent` si la versión de SPADE-LLM no lo proporciona. Sin el primer
> parche, los agentes fallan con `No appropriate login method`. Ambas
> adaptaciones se desactivan solas si versiones futuras las hacen
> innecesarias. Patrón idéntico al del Guión 7 (`configuracion.py`).

---

## 6. Revisar los ficheros nuevos del Nivel 2

La rama `desarrollo-nivel2` incluye los siguientes ficheros **nuevos** que
no existían en el Nivel 1. Es importante revisarlos antes de empezar a
programar:

| Fichero | Descripción |
|---|---|
| `config.yaml` | Extendido con la sección `perfiles_llm` (local y servidor). |
| `docker-compose.yml` | Contenedores Docker para Prosody (XMPP) y Ollama (LLM). |
| `requirements.txt` | Dependencias de Python para el Nivel 2 (preserva las del Nivel 1). |
| `ontologia/modelos_compartidos.py` | Modelos Pydantic compartidos. **Solo lectura** — no modificar. |
| `ontologia/esquema_emergencias.json` | Esquema JSON de la mensajería **interna** del grupo (preservado del Nivel 1). |
| `ontologia/esquema_supervisor.json` | Esquema JSON de los mensajes que viajan entre el **supervisor del profesor** y los agentes del grupo. |
| `docs/contrato_supervisor.md` *(rama `desarrollo-nivel2` y rama `agente-profesor-emergencias`)* | **Contrato observable** del supervisor: performativas FIPA-ACL, plazos, cabeceras y batería de tests obligatoria. |
| `herramientas/__init__.py` | Paquete donde implementar las `FunctionTool` de ADK. |
| `prompts/` | Directorio donde crear los ficheros de *prompt* de cada agente. |
| `xmpp/prosody.cfg.lua` | Configuración del servidor XMPP local con MUC y registro automático. |

### 6.1. Protocolos del supervisor del profesor

El supervisor del profesor es el agente externo que evalúa el sistema
del grupo en el Hito 4. Habla **FIPA-ACL estándar** y se reduce a
**dos protocolos**, que el grupo debe atender obligatoriamente:

1. **Inyección de incidentes** (`fipa-request`) — El supervisor envía
   un `request` con `DatosEmergencia` a la **Centralita** del grupo.
   La Centralita responde con `agree` (≤ 5 s) y, tras la actuación
   interna, envía un `inform` con `InformeResolucion` (≤ 180 s).

2. **Consulta de estado** (`fipa-query`) — El supervisor envía un
   `query-ref` con `ConsultaEstado` a **cualquier agente** del grupo
   (Centralita, Bomberos, Sanitario, Policía, Municipal). El agente
   responde con un `inform` que lleva un `EstadoAgente` (≤ 2 s).

Las cabeceras FIPA-ACL exactas (`performative`, `conversation_id`,
`in_reply_to`, `protocol`, `ontology`, `language`), los modelos
Pydantic implicados, los plazos, los ejemplos de mensajes y los
tests automáticos que el grupo debe escribir están detallados en
`docs/contrato_supervisor.md`, disponible en la rama `desarrollo-nivel2`
y en la rama del profesor (`agente-profesor-emergencias`).

> **Importante:** los modelos Pydantic ya están en
> `ontologia/modelos_compartidos.py`. La equivalencia en JSON-Schema
> está en `ontologia/esquema_supervisor.json`. El grupo no debe
> redefinir estos modelos: debe importarlos y usarlos tal cual.

---

## 7. Resumen de lo que hay que implementar

El grupo debe implementar los siguientes elementos (consultar el README.md
para los detalles completos y los hitos de evaluación):

1. **Clase base `agentes/base_agente_llm.py`** — Hereda de `LLMAgent`,
   centraliza la configuración LLM, la carga de *prompts* y la respuesta
   a las consultas de estado del supervisor (protocolo `fipa-query`
   descrito en `docs/contrato_supervisor.md` de la rama `desarrollo-nivel2`).

2. **Migrar los agentes** de `Agent` a la clase base: cambiar la herencia,
   añadir la configuración LLM y sustituir la lógica `if/elif` por
   `llm_chat()`.

3. **Prompts de sistema** (`prompts/{rol}.txt`) — Un fichero por agente con
   el rol, competencias, formato de salida JSON, coordinación y un ejemplo.

4. **Herramientas ADK** (`herramientas/{rol}.py`) — Envolver las funciones
   de `logica/` como `FunctionTool` de Google ADK.

5. **Pruebas automatizadas** (`tests/`) — Ampliar la batería de pruebas
   según los hitos.

6. **Documento de verificación** (`doc/guia_verificacion_nivel2.md`) —
   Instrucciones para que el profesor reproduzca la ejecución.

> **Importante:** los módulos de `logica/` **no se modifican**. Son funciones
> puras de Python que se reutilizan tal cual del Nivel 1.

---

## 8. Entrega en PLATEA

### 8.1. Preparar el repositorio para la entrega

Antes de subir nada a PLATEA, el repositorio debe estar completo y
etiquetado. Seguid estos pasos:

```bash
# 1. Asegurarse de que todas las ramas personales están fusionadas
#    en desarrollo-nivel2
git checkout desarrollo-nivel2
git pull origin desarrollo-nivel2

# 2. Ejecutar las pruebas y guardar el resultado
pytest tests/ -v > resultado_tests_nivel2.txt 2>&1
git add resultado_tests_nivel2.txt
git commit -m "Añadir resultado de las pruebas del Nivel 2"

# 3. Fusionar en main y etiquetar la entrega
git checkout main
git pull origin main
git merge desarrollo-nivel2
git tag -a entrega-nivel2 -m "Entrega Nivel 2 — Villa Olivar"
git push origin main --tags
```

### 8.2. Contenido obligatorio del repositorio

Verificad que el repositorio contiene **todos** estos elementos antes de
entregar:

- [ ] `logica/` — Módulos de lógica pura (preservados del Nivel 1).
- [ ] `agentes/` — Agentes SPADE-LLM (incluye `base_agente_llm.py`).
- [ ] `herramientas/` — Módulos con las `FunctionTool` de ADK.
- [ ] `prompts/` — Ficheros de *prompt* de sistema de cada agente.
- [ ] `descubrimiento/` — Sistema de descubrimiento (preservado/adaptado).
- [ ] `tests/` — Pruebas automatizadas (ampliadas para el Nivel 2).
- [ ] `ontologia/modelos_compartidos.py` — Modelos Pydantic (sin modificar).
- [ ] `ontologia/esquema_emergencias.json` — Esquema JSON de la ontología.
- [ ] `config.yaml` — Configuración con perfiles XMPP y LLM.
- [ ] `docker-compose.yml` — Contenedores Docker para Prosody y Ollama.
- [ ] `main.py` — Lanzador del sistema.
- [ ] `utils.py` — Funciones factoría.
- [ ] `requirements.txt` — Dependencias.
- [ ] `resultado_tests_nivel2.txt` — Salida de las pruebas.
- [ ] `doc/guia_verificacion_nivel2.md` — Documento de verificación.

### 8.3. Qué subir a PLATEA

La entrega en PLATEA consiste en un **único fichero PDF** que contenga:

1. **Nombres completos y correos** de todos los miembros del grupo.
2. **Denominación del grupo** (el sufijo usado en los JIDs de los agentes,
   por ejemplo: `fenix`, `olivar42`).
3. **Enlace al repositorio** del grupo en GitHub (debe ser accesible para
   el profesor).
4. **Hito máximo al que aspira el grupo** (del 1 al 6, correspondiente a
   las notas del 5 al 10).

**Solo un miembro del grupo realiza la entrega en PLATEA.** No es necesario
subir el código fuente a PLATEA; el profesor lo revisará directamente en el
repositorio a través del enlace proporcionado.

### 8.4. Memoria técnica

Adicionalmente al PDF de entrega, el grupo debe preparar una **memoria
técnica breve** (máximo 5 páginas) que incluya:

- Un **diagrama de la arquitectura** del sistema mostrando las tres capas
  (dominio, LLM y SPADE) y la relación entre los cinco agentes.
- La **estrategia de *prompting*** elegida para cada agente: qué información
  se incluye en cada *prompt*, cómo se fuerza la salida JSON, si se usan
  ejemplos de aprendizaje con pocos ejemplos (*few-shot*).
- Una **reflexión comparativa** entre los enfoques ADK y SPADE-LLM aplicados
  al escenario de Villa Olivar: ventajas, limitaciones y lecciones aprendidas.

---

## 9. Recordatorio: flujo de trabajo diario

El ciclo de trabajo es el mismo que en el Nivel 1:

```
1. Actualizar    →  git checkout mi-rama && git pull origin desarrollo-nivel2
2. Desarrollar   →  Editar, probar, hacer commits descriptivos en español
3. Integrar      →  git checkout desarrollo-nivel2 && git merge mi-rama && git push
```

Cada miembro trabaja en su rama personal. La integración en
`desarrollo-nivel2` se hace mediante fusión (*merge*). No fusionéis
`desarrollo-nivel2` en `main` hasta que la entrega esté lista.

---

*Sistemas Multiagente — Grado en Ingenieria Informatica — Universidad de
Jaen — Curso 2025-2026*
