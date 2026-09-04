# Pruebas previas al examen

Esta rama incluye los **mismos tests** que el Coordinador del
profesor ejecutará el día del examen. El grupo puede (y debe)
ejecutarlos sobre su propio sistema durante el desarrollo para
verificar que cumple el contrato externo antes de la sesión real.

Esta guía cubre **solo la ejecución de la serie de validación del profesor**.
Los tests que el grupo debe escribir sobre su propio código
(unitarios y de integración internos) se enumeran en
[`ESCENARIOS_TESTS_OBLIGATORIOS.md`](ESCENARIOS_TESTS_OBLIGATORIOS.md);
no son opcionales y aquí no se describen.

---

## 1. Catálogo de pruebas

| Carpeta | Naturaleza | Número | Requisitos para pasar |
|---------|-----------|--------|-----------------------|
| `tests/profesor/modelos/` | Unitarias del contrato | 62 | Ninguno: validan los modelos Pydantic. **Deben pasar siempre**. |
| `tests/profesor/cliente_pruebas/` | Unitarias del cliente | 7 | Ninguno: usan `httpx.MockTransport`. **Deben pasar siempre**. |
| `tests/profesor/integracion/` | Caja negra contra el sistema real | 49 | El sistema del grupo arrancado y accesible en las URL declaradas en el bloque `evaluacion:` de `config/config.yaml`. |

Los marcadores `hito_1`...`hito_6` permiten filtrar por hito al
ejecutar `pytest -m`.

---

## 2. Verificación rápida (sin sistema arrancado)

Las pruebas unitarias del contrato y del cliente no requieren
ningún agente arrancado y son una buena verificación inicial:

```bash
pytest tests/profesor/modelos/ tests/profesor/cliente_pruebas/ -v
```

Si fallan, hay un problema con la instalación: confirmar que
el entorno virtual del proyecto está activo y que se han
instalado las dependencias de `requirements.txt`.

---

## 3. Ejecución completa (con el sistema arrancado)

### 3.1. Antes de arrancar

1. Con el **entorno virtual activo** del proyecto (el mismo
   que se viene usando desde el Nivel 2; ver §3.1 del
   `README.md` si aún no se ha creado), instalar las
   dependencias:

   ```bash
   pip install -r requirements.txt
   ```

2. Levantar la infraestructura Docker local (registro REST,
   servidor Ollama, etc.). Consultar
   [`doc/MODO_DOCKER.md`](MODO_DOCKER.md).

3. Copiar `config/agents.yaml.ejemplo` a `config/agents.yaml` y
   ajustarlo si es necesario.

4. En `config/config.yaml`, descomentar el bloque `evaluacion:`
   y verificar que las URL coinciden con `config/agents.yaml`
   (puertos del rango 81xx por defecto).

5. Arrancar el sistema multiagente:

   ```bash
   python main.py
   ```

### 3.2. Lanzar la serie de validación

En otra terminal del mismo equipo:

```bash
pytest tests/profesor/integracion/ -v
```

La primera vez muchos tests fallarán: cada hito superado elimina
fallos. La meta es llegar al día del examen con la mayor parte
del catálogo en verde.

### 3.3. Filtrar por hito

Para concentrarse en un hito durante el desarrollo:

```bash
pytest tests/profesor/integracion/ -m hito_1 -v   # solo Hito 1
pytest tests/profesor/integracion/ -m hito_3 -v   # solo Hito 3
```

### 3.4. Filtrar por nombre

```bash
pytest tests/profesor/integracion/ -k "clasificacion" -v
```

---

## 4. Interpretación de los fallos

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `httpx.ConnectError: All connection attempts failed` | El agente no está arrancado en la URL declarada. | Comprobar `python main.py` y la coincidencia entre `config/agents.yaml` y el bloque `evaluacion:` de `config/config.yaml`. |
| `pytest.skip: variable X no definida` | La prueba depende de un dato declarativo (privado, especialista público concreto). | Rellenar la URL correspondiente en el bloque `evaluacion:` de `config/config.yaml`. |
| `Task no completó: estado=failed, mensaje=...` | El agente devuelve `failed`; suele ser un error de validación Pydantic. | Comprobar que el grupo respeta los campos obligatorios del modelo. |
| `Clasificación incorrecta: esperado=incendio, obtenido=otro` | El LLM no acertó la clasificación. | Mejorar el prompt o la `FunctionTool` de clasificación. |
| `La traza no contiene `recibir_propuesta`` | El grupo no implementa Contract Net o no lo refleja en la traza. | Implementar Hito 4 y registrar los eventos en `traza_participacion`. |

---

## 5. Cobertura por hito

El número y tipo de pruebas no es uniforme entre hitos. El
detalle escenario a escenario se mantiene en la rama del
profesor (`coordinador-profesor`), pero el resumen es:

| Hito | Tests de integración | Foco principal |
|------|---------------------:|----------------|
| 1 | 7 | Centralita responde, clasifica, persiste, no se degrada. |
| 2 | 5 | Envío a especialistas; DataPart malformado. |
| 3 | 4 | Cinco roles coordinados; privados aislados; sin registro. |
| 4 | 10 | Contract Net (propuestas, asignación, perdedor, reintento), `input-required`, ciclo de vida, fallo localizado. |
| 5 | 5 | Descubrimiento por rol; cooperación con grupo simulado; sin tráfico al registro en modalidad A. |
| 6 | 2 | SSE (`tasks/sendSubscribe`); resistencia a peticiones malformadas. |

Los hitos superiores presuponen los anteriores: no tiene sentido
intentar Hito 5 si el Hito 1 todavía falla.

---

## 6. Garantía de equivalencia con el día del examen

Las pruebas de esta rama y las que el Coordinador del profesor
ejecutará el día del examen son **literalmente las mismas**.
Cualquier divergencia entre el resultado en el equipo del
alumno y el resultado en el aula tendrá únicamente dos causas
posibles:

1. **Configuración**: las URL del bloque `evaluacion:` de
   `config/config.yaml` no coinciden con las URL en las que los
   agentes están escuchando en el aula. Revisar también
   `a2a.host_por_defecto` y `red.perfiles.<perfil>.direccion_publicada`
   en el mismo fichero.
2. **Diferencia de comportamiento del LLM** entre el perfil
   `local` (Ollama) y el perfil `servidor` (modelo de
   producción). Algunas clasificaciones marginales pueden
   variar; los tests están escritos con textos suficientemente
   inequívocos para minimizar este riesgo.

Si algún test pasa en local pero falla en el aula, es un fallo
del grupo, no del banco de pruebas.
