# Verificación exhaustiva de los servicios XMPP y LLM

> **Antes de empezar a programar agentes, ejecuta el guion (*script*) de verificación.**
> La inmensa mayoría de los problemas que los alumnos informan al inicio
> del Nivel 2 (autenticación rechazada, agentes que se cierran sin error,
> herramientas ADK que se cuelgan al primer mensaje) son fallos de
> conexión, no fallos del código. El guion
> [`verificar_conexion.py`](../verificar_conexion.py) los detecta en
> menos de un minuto y dice exactamente cuál es el problema.

Esta guía documenta el funcionamiento del guion
`verificar_conexion.py` que se incluye en la raíz del proyecto. Su
propósito es comprobar, en un único ejecutable, que los dos servicios
de infraestructura del Nivel 2 funcionan correctamente:

1. El **servidor XMPP** (Prosody en local, o `sinbad2.ujaen.es` en el
   laboratorio) acepta el registro y la autenticación de agentes
   SPADE, y permite la creación y uso de salas MUC para coordinación.
2. El **servidor LLM** (Ollama en local, Ollama en `sinbad2ia.ujaen.es`
   o Google AI Studio mediante clave de API — *API key*) está
   accesible, tiene los modelos esperados disponibles y responde a un
   mensaje de prueba.

---

## 1. Cuándo ejecutar el guion

| Situación | Ejecutar |
|---|---|
| Primera vez que arrancas el proyecto en un equipo nuevo. | `python verificar_conexion.py` |
| Cambiaste `perfil_xmpp_activo` o `perfil_llm_activo` en `config.yaml`. | `python verificar_conexion.py` |
| Acabas de exportar tu clave de API de Gemini o cambiaste de proyecto Google Cloud. | `python verificar_conexion.py llm gemini` |
| Sospechas que el problema está en XMPP (agentes que no se autentican). | `python verificar_conexion.py xmpp` |
| Sospechas que el problema está en el LLM (respuestas vacías, tiempos de espera agotados — *timeouts*). | `python verificar_conexion.py llm` |
| Cambiaste de red (laboratorio → casa o viceversa) y quieres revalidar todo. | `python verificar_conexion.py` |

> **Si el guion pasa, el sistema multiagente puede arrancar.**
> Si el guion falla, **no avances** en el desarrollo: el problema no
> está en tu código, está en la infraestructura. Resuelve primero el
> error que el guion informa.

---

## 2. Uso

```bash
# 1. Asegúrate de estar en el entorno virtual del proyecto
source venv-nivel2/bin/activate

# 2. (Si vas a probar el perfil "local") arranca los contenedores
docker compose up -d

# 3. Ejecuta la verificación con los perfiles activos en config.yaml
python verificar_conexion.py
```

Argumentos opcionales:

| Comando | Qué hace |
|---|---|
| `python verificar_conexion.py` | Verifica XMPP **y** LLM con los perfiles activos en `config.yaml`. |
| `python verificar_conexion.py xmpp` | Solo XMPP (perfil activo). |
| `python verificar_conexion.py xmpp servidor` | Solo XMPP, forzando el perfil `servidor`. |
| `python verificar_conexion.py llm` | Solo LLM (perfil activo). |
| `python verificar_conexion.py llm gemini` | Solo LLM, forzando el perfil `gemini`. |

El guion termina con código de salida `0` si todas las
verificaciones pasan, y `1` si alguna falla.

---

## 3. Qué comprueba el guion

### 3.1. Verificación XMPP (4 pasos)

1. **Alcanzabilidad TCP**: abre un *socket* al puerto declarado en
   `config.yaml` para el perfil activo (`localhost:5222` o
   `sinbad2.ujaen.es:8022`). Si el puerto no responde, el resto de
   pasos no tendrían sentido.
2. **Registro y autenticación**: arranca dos agentes SPADE temporales
   (`verif_alfa` y `verif_beta`) con `auto_register=True`. Si las
   cuentas no existen, Prosody las crea mediante registro en banda
   (*in-band registration*). Si ya existen con la misma contraseña,
   se reutilizan. Esto valida tres cosas a la vez: que el parche
   SASL sin TLS de `utils.py` está activo, que el servidor permite
   el registro, y que la autenticación PLAIN/SCRAM funciona contra
   el servidor.
3. **Creación de sala MUC**: el primer agente entra (`join_muc`) en
   `verif_sala@conference.<dominio>`. Si la sala no existe, Prosody
   la crea al instante porque `muc_room_locking = false` y
   `restrict_room_creation = false`.
4. **Co-ocupación de la sala**: el segundo agente se une a la misma
   sala. Si ambos consiguen estar dentro, la coordinación por MUC
   está garantizada — que es exactamente lo que necesitan los cinco
   agentes del proyecto para descubrirse entre sí.

> **Nota técnica sobre el descubrimiento de salas (`disco#items`).**
> El protocolo MUC publica una sala en el listado del componente
> (`conference.<dominio>`) **solo cuando su configuración ha sido
> finalizada** por el dueño. SPADE no envía el formulario de
> configuración al crear la sala, así que las salas recién creadas
> **no aparecen** en `disco#items` aunque estén operativas. Por eso
> el guion verifica la coordinación entrando con el segundo agente
> a la misma sala (que es lo que harán los agentes del proyecto), no
> consultando el listado del componente. Si tu código de
> descubrimiento depende de `disco#items`, considera cambiar a un
> mecanismo basado en presencia dentro de salas conocidas por
> convención (`bomberos@conference.<dominio>`, etc.).

### 3.2. Verificación LLM (2 pasos)

1. **Listado de modelos disponibles**: consulta al proveedor activo
   qué modelos puede usar el proyecto:
   - **Ollama**: `GET {url_base}/api/tags` devuelve los modelos
     descargados localmente. Si el modelo declarado en el perfil no
     está en el listado, el guion lo señala con un AVISO y muestra
     el comando para descargarlo (`docker compose exec ollama ollama
     pull <modelo>`).
   - **Gemini**: `GET v1beta/models?key=...` devuelve todos los
     modelos publicados por Google que admiten `generateContent`.
     Cada modelo se etiqueta como `[gratis]` o `[pago]` según los
     prefijos del nivel gratuito de Google AI Studio, y se muestra
     su cuota publicada (RPM y RPD). Los gratuitos aparecen
     primero — son los únicos que importan para la asignatura.
2. **Mensaje de prueba**: envía la consulta declarada en
   `verificacion.mensaje_prueba` (en `config.yaml`) al modelo activo
   y muestra la respuesta. Si esto pasa, la pila completa
   (`config.yaml` → `utils.py` → cliente HTTP → proveedor → modelo)
   funciona.

---

## 4. Configuración por perfil

Los tres perfiles LLM se configuran de manera distinta. La tabla
siguiente resume qué necesitas tener en cada caso antes de ejecutar
el guion.

| Perfil | Requisito | Ventajas | Limitaciones |
|---|---|---|---|
| `local` | Docker arrancado y modelo descargado: `docker compose up -d` y `docker compose exec ollama ollama pull llama3.2:3b`. | Sin cuota, sin red. | Lentitud y consumo de RAM en equipos modestos. |
| `servidor` | Estar dentro de la red del laboratorio. | Modelo grande (`llama3:8b`, `qwen3:32b`) sin coste local. | Solo accesible desde el laboratorio. |
| `gemini` | Clave de API gratuita exportada en `GOOGLE_API_KEY`. Ver sección 5. | Modelos potentes (`gemini-2.5-flash`) en la nube, sin instalar nada. | Cuota diaria por modelo (ver tabla en sección 5.3). Requiere conexión a Internet. |

Para cambiar de perfil, edita una sola línea de `config.yaml`:

```yaml
perfil_llm_activo: "gemini"   # "local" | "servidor" | "gemini"
```

Para XMPP, lo mismo:

```yaml
perfil_xmpp_activo: "local"   # "local" | "servidor"
```

---

## 5. Configurar el perfil Gemini (Google AI Studio)

Gemini es la alternativa recomendada para alumnos cuyo equipo no
puede ejecutar modelos locales con fluidez (≤ 8 GB RAM, sin GPU) y
que están fuera de la red del laboratorio. Google AI Studio ofrece
un nivel gratuito generoso para uso académico.

### 5.1. Crear la clave de API

1. Entra en [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
   con tu cuenta de Google.
2. Crea una clave de API (*API key*) nueva. Google la asocia a un
   proyecto de Google Cloud (lo crea automáticamente la primera vez).
3. **Acepta los términos del nivel gratuito**: entra en
   [aistudio.google.com](https://aistudio.google.com/) y abre cualquier
   modelo en el entorno de pruebas (*playground*). Hasta que aceptes
   los términos, todas las llamadas devuelven `403 PERMISSION_DENIED`
   aunque la clave esté creada.

### 5.2. Exportar la clave de API

```bash
export GOOGLE_API_KEY="tu-api-key"
```

Para que la variable persista entre sesiones, añádela a tu
`~/.bashrc` o `~/.zshrc`. **Nunca** la guardes en `config.yaml` ni la
publiques en el repositorio. El campo `api_key_env` del perfil
`gemini` indica el nombre de la variable de entorno que el guion
consultará (por defecto, `GOOGLE_API_KEY`).

### 5.3. Cuotas del nivel gratuito (estado 2026-04)

Solo los modelos marcados como `[gratis]` por el guion son útiles
sin facturación activa. Los `[pago]` requieren habilitar facturación
en Google Cloud. Las columnas RPM (peticiones por minuto — *requests
per minute*) y RPD (peticiones por día — *requests per day*) se
aplican por clave de API:

| Modelo | RPM gratis | RPD gratis |
|---|---:|---:|
| `gemini-2.0-flash-lite` | 30 | 200 |
| `gemini-2.0-flash` | 15 | 200 |
| `gemini-2.5-flash-lite` | 15 | 1000 |
| `gemini-2.5-flash` | 10 | 250 |
| `gemini-2.5-pro` | 5 | 100 |
| `gemini-3-flash-preview` | 5 | 20 |
| `gemma-3` | 30 | 14400 |
| `gemma-3n` | 30 | 14400 |

> **Recomendación para Villa Olivar**: usa `gemini-2.5-flash` (perfil
> por defecto) o `gemini-2.5-flash-lite` si necesitas más cuota
> diaria. La Centralita coordina con cuatro especialistas, así que
> 250 RPD pueden agotarse rápido si cada turno hace varias rondas.
> Para experimentación inicial, `gemini-2.5-flash-lite` (1000 RPD) es
> más cómodo.

Fuente oficial:
[ai.google.dev/gemini-api/docs/rate-limits](https://ai.google.dev/gemini-api/docs/rate-limits).
Google ajusta los límites sin previo aviso; el guion muestra los
valores publicados en su tabla estática junto a cada modelo.

### 5.4. Cambiar el modelo Gemini activo

El perfil `gemini` declara un único modelo en `config.yaml`:

```yaml
perfiles_llm:
  gemini:
    proveedor: "gemini"
    modelo: "gemini-2.5-flash"   # cambia aquí para usar otro modelo
    api_key_env: "GOOGLE_API_KEY"
```

ADK soporta Gemini de forma nativa, así que el modelo va **sin
prefijo** (`gemini-2.5-flash`, no `gemini/gemini-2.5-flash`). Para
una verificación con LiteLLM, el guion añade el prefijo
internamente.

---

## 6. Errores típicos y su diagnóstico

### 6.1. XMPP

| Error que informa el guion | Causa habitual | Solución |
|---|---|---|
| `Puerto 5222 en localhost no accesible` | El contenedor Prosody no está arrancado. | `docker compose up -d`. |
| `Puerto 8022 en sinbad2.ujaen.es no accesible` | Estás fuera de la red del laboratorio. | Cambia a perfil `local` o conéctate a la VPN del laboratorio. |
| `No appropriate login method` (en los registros — *logs* — internos) | El parche SASL sin TLS no se aplicó. | Asegúrate de importar `utils` antes de instanciar cualquier `Agent`. El guion lo hace correctamente; revisa tu propio código. |
| `not-authorized` | La cuenta existe en el servidor con OTRA contraseña. | Cambia el sufijo de tu grupo en `agents.yaml` para evitar colisiones, o pide al profesor que borre la cuenta. |
| Las salas MUC no aparecen al hacer `disco#items`. | Comportamiento esperado de Prosody. | Usa nombres de sala convencionales (`bomberos@conference.<dominio>`) y haz que cada agente entre en la suya por presencia, en lugar de descubrir salas por listado. |

### 6.2. LLM Ollama

| Error | Causa habitual | Solución |
|---|---|---|
| `Connection refused` en `localhost:11434` | El contenedor Ollama no está arrancado. | `docker compose up -d`. |
| `AVISO: el modelo 'llama3.2:3b' NO está descargado` | El volumen Docker está vacío o se usó `docker compose down -v`. | `docker compose exec ollama ollama pull llama3.2:3b`. |
| `Server disconnected without sending a response` | Carga del modelo en la primera petición (arranque en frío — *cold start*). | Vuelve a ejecutar el guion: la segunda llamada irá rápida porque el modelo ya está en memoria. |
| `timed out` en la generación | Modelo demasiado grande para el equipo. | Cambia a `llama3.2:3b` (perfil local) o `gemini-2.5-flash` (perfil gemini). |

### 6.3. LLM Gemini

| Error | Causa habitual | Solución |
|---|---|---|
| `La variable de entorno GOOGLE_API_KEY no está definida` | No has exportado la clave de API en esta sesión. | `export GOOGLE_API_KEY="..."`. Para hacerlo permanente, añádelo a `~/.bashrc`/`~/.zshrc`. |
| `403 PERMISSION_DENIED` | API "Generative Language" no habilitada, o términos del nivel gratuito sin aceptar. | Sigue los pasos 1-3 de la sección 5.1. |
| `429` con `limit: 0` | El modelo elegido no está incluido en el nivel gratuito. | Cambia a un modelo `[gratis]` (sección 5.3) o activa facturación. |
| `429` con `limit: N` (N > 0) | Cuota del minuto/día agotada. | Espera el `retryDelay` indicado o cambia a otro modelo con cuota disponible. |
| `404 NOT_FOUND` | El identificador del modelo es incorrecto o se ha retirado. | Mira el listado del guion y elige uno de los devueltos. |

---

## 7. Para profundizar en Gemini

La documentación detallada de la configuración Gemini, niveles de
servicio (Free / Tier 1), errores típicos y rutas de integración con
ADK (vía LiteLLM o nativa) se encuentra en el Guión 6 de la
asignatura:

- [`docs/gemini.md`](https://github.com/grupos-sma/guion6/blob/main/docs/gemini.md)
  del proyecto `guion6` — guía completa con tabla oficial de cuotas,
  flujo de sondeo activo, distinción entre 429 transitorio y 429
  con cuota cero, y referencias a la consola de uso de Google.

Si tu clave de API se comporta de forma rara (todo devuelve 403,
modelos que aparecen y desaparecen, cuotas distintas a las
publicadas), empieza por esa guía antes que por buscar en foros como
*Stack Overflow*.

---

*Sistemas Multiagente — Grado en Ingeniería Informática — Universidad de Jaén — Curso 2025-2026*
