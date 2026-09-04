# Carpeta `tests/` — Pruebas del proyecto

Esta carpeta reúne las pruebas pytest que el grupo ejecuta para
verificar el sistema antes de la sesión del examen. Conviven dos
familias de tests **con orígenes y propósitos distintos**:

| Carpeta | Origen | Qué verifica | ¿Modificable por el grupo? |
|---------|--------|--------------|---------------------------|
| `tests/profesor/` | Aportado por el profesor | El **contrato externo**: la Centralita y los especialistas responden con la estructura, los estados y la semántica acordadas en `contrato/`. Es la misma serie de validación que el Coordinador del profesor ejecutará tras el examen. | **No.** Cualquier modificación rompe la equivalencia con la evaluación oficial. |
| `tests/unidad/`, `tests/integracion/` | Escrita por el grupo | El **código interno del grupo**: funciones puras de dominio, validadores, agregación del informe, lógica de selección Contract Net, combinaciones de componentes propios. | **Sí.** El grupo elige nombres, estructura y aserciones. |

La lista mínima exigible de escenarios que el grupo debe cubrir
con `tests/unidad/` y `tests/integracion/` está en
[`doc/ESCENARIOS_TESTS_OBLIGATORIOS.md`](../doc/ESCENARIOS_TESTS_OBLIGATORIOS.md).

---

## 1. Detalle de `tests/profesor/`

Subcarpetas y conteos:

| Subcarpeta | Tests | Naturaleza |
|------------|------:|------------|
| `tests/profesor/modelos/` | 62 | Unitarios de los modelos Pydantic del contrato (Agent Card, AlertaEmergencia, InformeActuacion, InformeResolucion, Traza...). |
| `tests/profesor/cliente_pruebas/` | 7 | Unitarios del cliente A2A con `httpx.MockTransport`. |
| `tests/profesor/integracion/` | 49 | Caja negra contra el sistema real del grupo. Fallan con `ConnectError` si el sistema no está arrancado: es el comportamiento esperado. |

Los marcadores `hito_1` … `hito_6` permiten filtrar por hito al
ejecutar `pytest -m`. Los unitarios no dependen del sistema y
**deben pasar siempre**; los de integración requieren tener
`python main.py` corriendo y el bloque `evaluacion:` de
`config/config.yaml` ajustado.

---

## 2. Detalle de los tests del propio grupo

El grupo es libre de elegir la estructura de carpetas. Una
distribución razonable y reconocible por el `conftest.py` raíz:

```
tests/
├── unidad/             # Tests U1.x ... U6.x de ESCENARIOS_TESTS_OBLIGATORIOS.md
└── integracion/        # Tests I1.x ... I6.x de ESCENARIOS_TESTS_OBLIGATORIOS.md
```

Convenciones (consistentes con las del profesor):

- Nombres en español: `test_descripcion_de_lo_que_verifica`.
- Pruebas asíncronas marcadas con `@pytest.mark.asyncio`.
- Cada `conftest.py` agrupa los accesorios (*fixtures*) comunes
  a su directorio.
- Mocks puros para los unitarios (sin red, sin LLM, sin agentes
  arrancados); combinaciones de componentes propios para los
  de integración.

---

## 3. Ejecución

Con el entorno virtual del proyecto activo (ver §3.1 del
`README.md` raíz si aún no se ha creado):

```bash
# Toda la suite (del profesor + del grupo).
pytest

# Solo lo del profesor (sin tocar lo del grupo).
pytest tests/profesor/

# Solo unitarios del profesor (no requieren sistema arrancado).
pytest tests/profesor/modelos/ tests/profesor/cliente_pruebas/

# Solo integración del profesor (requiere `python main.py` en
# otra terminal y el bloque `evaluacion:` ya descomentado).
pytest tests/profesor/integracion/

# Solo lo del grupo.
pytest tests/unidad/ tests/integracion/

# Filtrar por hito.
pytest -m hito_3

# Filtrar por nombre.
pytest -k clasificacion
```

---

## 4. Tabla resumen al final de la sesión

Al cierre de cada ejecución, el `conftest.py` raíz imprime una
tabla con una fila por **bloque** (cada fichero de test es un
bloque) y cuatro columnas: Correctos, Incidencia, Omitidos y
Total. Una última fila agrega los totales y un veredicto resume
el estado (`OK` o `REVISAR`).

Cuando hay incidencias, debajo de la tabla aparece un bloque
**«Detalle de incidencias y cómo corregirlas»** con el motivo
abreviado y una lista de pasos accionables para cada test
fallido. Las pruebas omitidas se agrupan por motivo en
**«Detalle de pruebas omitidas y cómo activarlas»**, con
indicaciones específicas (bloque `evaluacion:` por completar,
rol no declarado por el grupo, registro REST no accesible,
etc.).

Este formato sustituye los tracebacks largos de `httpx` y
`aiohttp`, suprimidos por la opción `addopts = --tb=no` de
`pytest.ini`. Cuando se necesite el detalle técnico de un fallo
concreto, basta con relanzarlo con traza completa:

```bash
pytest --tb=long <ruta>::<Clase>::<test>
```

---

## 5. Política

- `tests/profesor/`: **no modificar.** Si una prueba no pasa,
  ajustar la implementación del agente, nunca el test.
  Modificar, comentar o eliminar tests de esta carpeta se
  considera una alteración indebida del contrato y se penaliza
  en la evaluación.
- `tests/unidad/` y `tests/integracion/`: el grupo es
  responsable. La lista de escenarios mínimos exigibles está en
  [`doc/ESCENARIOS_TESTS_OBLIGATORIOS.md`](../doc/ESCENARIOS_TESTS_OBLIGATORIOS.md);
  saltar un escenario obligatorio del hito al que se aspira
  reduce la nota del bloque de calidad de código y
  documentación.
