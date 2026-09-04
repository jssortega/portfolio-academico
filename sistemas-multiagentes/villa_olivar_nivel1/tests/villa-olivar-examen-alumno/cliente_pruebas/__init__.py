"""Cliente A2A usado por la batería de pruebas del profesor.

Este paquete contiene el cliente A2A asíncrono que la batería de
pruebas de `tests/profesor/` invoca para enviar Tasks reales a la
Centralita del grupo, leer Agent Cards y consultar el estado de
las Tasks.

En la rama del alumno (`examen-alumno`) el paquete está incluido
**solo para que los tests funcionen**: ni la factoría ni los
agentes que el grupo escribe lo importan. Es la misma clase con
la que el Coordinador del profesor evaluará a los grupos el día
del examen; mantenerla aquí garantiza que las verificaciones
previas del alumno y la evaluación oficial del profesor usen
literalmente el mismo cliente.

Las pruebas unitarias del cliente viven en
`tests/profesor/cliente_pruebas/` y se ejecutan con mocks puros
(`httpx.MockTransport`), sin conectar contra ningún sistema real.
"""

from cliente_pruebas.cliente import ClienteCoordinador, RespuestaTask

__all__ = ["ClienteCoordinador", "RespuestaTask"]
