# Pruebas del profesor

Este directorio contiene las pruebas pytest que el grupo recibe
en esta rama (`examen-alumno`) y que el Coordinador del profesor
ejecutará tras el examen para fijar la nota automática del
proyecto.

Las pruebas verifican el cumplimiento del contrato externo de la
Centralita y de los especialistas (formato del `DataPart`,
estructura del `InformeResolucion`, ciclo de vida de Tasks A2A,
comportamiento ante peticiones malformadas, etc.) y forman parte
del **25 % de la serie de validación automática** descrita en
los hitos de evaluación del Nivel 3.

Vista general del proyecto, política de modificación y formato
de la salida en [`../README.md`](../README.md).

## Convenciones

- Nombres de pruebas en español:
  `test_descripcion_de_lo_que_verifica`.
- Pruebas asíncronas marcadas con `@pytest.mark.asyncio`.
- `conftest.py` agrupa los accesorios (*fixtures*) comunes a
  este directorio.

## Ejecución

Con el entorno virtual del proyecto activo y las dependencias
instaladas (ver §3.1 del `README.md` raíz):

```bash
pytest tests/profesor/ -v
```

## Política

Los grupos **no deben modificar** el contenido de estas pruebas:
si una prueba no pasa, debe ajustarse la implementación del
agente, no el test. Cualquier cambio en este directorio se
considera una modificación indebida del contrato y se penaliza
en la evaluación.
