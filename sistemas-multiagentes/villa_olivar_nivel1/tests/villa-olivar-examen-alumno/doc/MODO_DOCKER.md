# Modo Docker — Ejecutar en casa antes del examen

El perfil `local` de `config/config.yaml` está pensado para que
el alumno pueda ensayar el examen completo en su propio equipo,
sin necesidad de conectarse al aula. Se apoya en la pila Docker
de la asignatura, mantenida en un repositorio aparte.

---

## 1. Qué se levanta en Docker

La pila local de la asignatura proporciona los servicios externos
que el sistema del grupo necesita:

| Servicio | Puerto local | Para qué sirve en el Nivel 3 |
|----------|-------------:|------------------------------|
| **Registro REST** | `8020` | Directorio del aula: alta de agentes públicos, señal de vida, `GET /agentes` para el descubrimiento (Hito 5). |
| **Ollama** | `11434` | LLM local que los agentes invocan a través de SPADE-LLM/ADK. |
| **Prosody (XMPP)** | `5222` | No es necesario para el Nivel 3 puro; se mantiene encendido para compatibilidad con el Nivel 1 y 2. |

Los agentes del grupo y el Coordinador del profesor se conectan
por TCP a estos puertos.

---

## 2. Cómo se levanta

La infraestructura **no vive en este repositorio**. Toda la
configuración (Docker Compose, configuración de Prosody, scripts
auxiliares) reside en el repositorio
[`ssmmaa-infraestructura`](https://gitlab.com/ssmmaa/infraestructurassmmaa/ssmmaa-infraestructura),
fuente única de verdad para todos los proyectos de la asignatura.

Para levantarla la primera vez:

```bash
git clone https://gitlab.com/ssmmaa/infraestructurassmmaa/ssmmaa-infraestructura.git
cd ssmmaa-infraestructura
make build
make up
make pull-modelo    # descarga el modelo Ollama si no está en caché
```

A partir de ahí basta con `make up` para arrancarla y `make down`
para detenerla. Detalles completos (variables, puertos, modos de
arranque) en el README del repositorio
`ssmmaa-infraestructura`.

---

## 3. Comprobación rápida

Tras `make up`, en otra terminal:

```bash
# Registro REST: debería devolver un JSON (lista vacía al principio).
curl http://localhost:8020/agentes

# Ollama: debería responder con el listado de modelos disponibles.
curl http://localhost:11434/api/tags
```

Si alguno falla, el contenedor correspondiente no está activo o
ha tardado más de lo esperado en inicializarse. Esperar 30
segundos y reintentar; si persiste, consultar los logs:

```bash
docker compose logs -f registro
docker compose logs -f ollama
```

---

## 4. Arrancar el sistema del grupo en este modo

Con la pila Docker levantada y el perfil `local` activo en
`config/config.yaml`:

```bash
# En la raíz de esta rama:
python main.py
```

El lanzador instancia cada agente declarado en
`config/agents.yaml`, los arranca en los puertos del rango 81xx
(Centralita en `8110`, especialistas en `8120` a `8150`) y queda
a la espera de peticiones JSON-RPC.

Para verificar que un agente publica su Agent Card:

```bash
curl http://localhost:8110/.well-known/agent.json
```

---

## 5. Ejecutar la serie de validación en este modo

Con el sistema arrancado:

```bash
pytest tests/profesor/integracion/ -v
```

Las pruebas leen el bloque `evaluacion:` de `config/config.yaml`
para conocer las URL del grupo. Ese bloque viene **comentado**
con los valores típicos del modo local; el alumno solo tiene
que descomentarlo (y ajustar las URL si los puertos difieren).

---

## 6. Limitaciones del modo Docker

- El LLM local (`ollama/llama3.2:3b` por defecto) es más rápido
  pero menos preciso que el modelo del servidor de la
  asignatura. Algunas clasificaciones marginales pueden
  variar; los textos de las pruebas están escritos para
  minimizar ese riesgo.
- La pila Docker no incluye los sistemas de **otros grupos**.
  Las pruebas del Hito 5 que dependen de cooperación entre
  grupos se omiten o se prueban contra los **dobles A2A**
  simulados que la factoría arranca en proceso (ver
  `tests/profesor/integracion/conftest.py`).
- El registro REST local arranca vacío en cada `make up`. No es
  necesario sembrar nada: los agentes se inscriben al arrancar.

---

## 7. Atajos útiles

```bash
# Detener todo
cd ssmmaa-infraestructura && make down

# Limpiar volúmenes (resetea el estado de Prosody y borra el
# modelo Ollama descargado; no necesario en el flujo normal).
make clean

# Volver a empezar
make build && make up && make pull-modelo
```
