"""Hito 3 — *Resolución intra-grupo sin acceso al registro central* (escenario 8).

Un escenario de modalidad A (que se resuelve íntegramente con
agentes del propio grupo) no debe depender de la disponibilidad
del registro REST del aula. La prueba lo verifica desde el lado
del coordinador: aunque el grupo arranque apuntando a un registro
inexistente, los escenarios A deben seguir completándose.

La prueba **no apaga el registro real** —el coordinador no tiene
ese privilegio—; en su lugar exige que la configuración del grupo
(bloque ``red`` de ``config/config.yaml``) declare en ``REGISTRO_REST_URL`` un
servidor inexistente antes de ejecutar este test. El usuario tipo
del test es por tanto el propio grupo evaluado, que ejecuta la
prueba durante su desarrollo apuntando ``REGISTRO_REST_URL`` a un
host inexistente.

Para que la prueba sea reproducible sin requerir intervención
manual, comprueba **el comportamiento observable desde el
coordinador**: una alerta intra-grupo procesada con normalidad.
Esto es necesario pero no suficiente; la condición suficiente
(que el grupo realmente no haya consultado al registro) se
verifica en ``test_modalidad_a_sin_trafico.py``.

Prueba de **caja negra contra el sistema real** del grupo.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from contrato.alerta_emergencia import AlertaEmergencia
from contrato.tipos import EstadoTask, RolEspecialista
from cliente_pruebas.cliente import ClienteCoordinador


@pytest.mark.integration
@pytest.mark.hito_3
class TestModalidadASinRegistro:
    """Los escenarios intra-grupo no dependen del registro central."""

    @pytest.mark.asyncio
    async def test_escenario_intra_grupo_completa_aunque_no_haya_registro(
        self,
        cliente_coordinador: ClienteCoordinador,
        url_centralita: str,
        nuevo_identificador_emergencia: UUID,
        identificador_task_prefijado: str,
    ) -> None:
        """Una alerta resoluble intra-grupo termina `completed` con o sin registro.

        El grupo debe arrancar su sistema apuntando a un registro
        inexistente (por ejemplo, exportando
        ``REGISTRO_REST_URL=http://localhost:9999`` antes de
        arrancar) y, sin reiniciar entre el cambio y el test,
        ejecutar esta prueba. La alerta solo requiere especialistas
        del propio grupo, así que no hay justificación para que la
        Centralita consulte al registro y, por tanto, la resolución
        no debería verse afectada por la inaccesibilidad del
        directorio externo.
        """
        alerta = AlertaEmergencia(
            id_emergencia=nuevo_identificador_emergencia,
            texto=(
                "Pequeño incendio en contenedor de cartón sin víctimas, "
                "resoluble íntegramente con los recursos del propio grupo."
            ),
        )
        respuesta = await cliente_coordinador.enviar_alerta(
            url_centralita=url_centralita,
            alerta=alerta,
            identificador_task=identificador_task_prefijado,
        )

        assert respuesta.estado is EstadoTask.COMPLETED, (
            "La Task intra-grupo debería completar aunque el registro central "
            f"no esté disponible; estado obtenido: {respuesta.estado.value}, "
            f"mensaje: {respuesta.mensaje_error!r}."
        )
        assert respuesta.informe is not None
        # Al menos un especialista del grupo debe haber intervenido.
        assert len(respuesta.informe.informes_especialistas) >= 1, (
            "Un escenario intra-grupo debe contar con al menos una "
            "contribución de un especialista del propio grupo."
        )
        # Bomberos es el rol natural para este escenario; verificamos
        # su presencia para asegurar que la resolución es coherente.
        roles_intervinientes = {
            informe.rol for informe in respuesta.informe.informes_especialistas
        }
        assert RolEspecialista.BOMBEROS in roles_intervinientes
