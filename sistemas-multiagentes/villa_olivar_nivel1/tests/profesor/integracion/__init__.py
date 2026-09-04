"""Pruebas de integración (caja negra) contra el sistema real del grupo.

Este paquete agrupa las pruebas descritas en
el plan de pruebas de la rama del profesor → directorio
``tests/profesor/integracion/``. Tratan el sistema del grupo
evaluado como una **caja negra** accesible únicamente a través
del cliente A2A ``cliente_pruebas.cliente.ClienteCoordinador``.

Las pruebas envían peticiones HTTP **reales** contra la
Centralita y los especialistas públicos del grupo (sin dobles ni
mocks). Por tanto, fallan con error de conexión mientras el grupo
no haya arrancado su sistema en la URL que la variable de entorno
``CENTRALITA_URL`` indica (predeterminado: ``http://localhost:8110``).

Las pruebas están etiquetadas con ``@pytest.mark.integration``
para que cualquier ejecución sin sistema arrancado pueda
filtrarlas con ``pytest -m "not integration"``.
"""
