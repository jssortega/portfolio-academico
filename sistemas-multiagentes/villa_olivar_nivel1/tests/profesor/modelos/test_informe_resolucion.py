"""Pruebas unitarias del modelo `InformeResolucion`.

El `InformeResolucion` es el principal artefacto observable del
contrato externo. Estas pruebas verifican su esquema; la validación
de coherencia con la alerta original o con los especialistas
intervinientes corresponde a las pruebas de integración.

Cubren los escenarios 6 del Hito 3 y el escenario 5 del Hito 4
descritos en `doc/HITOS_EVALUACION.md`. Incluyen las pruebas de los
campos `id_emergencia` y `traza_participacion`, que son obligatorios
desde la versión del contrato armonizada con el supervisor del
profesor.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from contrato.informe_actuacion import InformeActuacion
from contrato.informe_resolucion import InformeResolucion
from contrato.tipos import EstadoFinal, Prioridad, RolEspecialista, TipoEmergencia
from contrato.traza import EventoTraza, RolAgente, VisibilidadAgente


ID_EMERGENCIA_FIJO = UUID("2efae4fb-ef5e-5920-989d-957b9a511bff")


def _evento_minimo(
    instante: datetime,
    *,
    rol: RolAgente = RolAgente.CENTRALITA,
    visibilidad: VisibilidadAgente = VisibilidadAgente.PUBLICO,
    accion: str = "recibir_alerta",
    detalle: str = "AlertaEmergencia recibida vía A2A",
    agente_id: str = "centralita_fenix",
) -> EventoTraza:
    """Auxiliar: construye un `EventoTraza` válido con los valores por defecto."""
    return EventoTraza(
        instante=instante,
        agente_id=agente_id,
        rol=rol,
        visibilidad=visibilidad,
        accion=accion,
        detalle=detalle,
    )


@pytest.mark.hito_3
class TestInformeResolucion:
    """Pruebas del modelo `InformeResolucion`."""

    def test_admite_un_informe_minimo_con_traza_de_un_solo_evento(self) -> None:
        """Un informe con clasificación, estado final y un evento de traza es válido."""
        informe = InformeResolucion(
            id_emergencia=ID_EMERGENCIA_FIJO,
            tipo_emergencia=TipoEmergencia.OTRO,
            prioridad=Prioridad.BAJA,
            estado_final=EstadoFinal.NO_RESUELTA,
            traza_participacion=[_evento_minimo(datetime.now(timezone.utc))],
        )
        assert informe.tipo_emergencia is TipoEmergencia.OTRO
        assert informe.informes_especialistas == []
        assert len(informe.traza_participacion) == 1

    def test_admite_un_informe_con_los_cuatro_especialistas_intervinientes(self) -> None:
        """Un escenario integral con los cuatro roles produce un informe coherente."""
        intervinientes = [
            InformeActuacion(rol=RolEspecialista.BOMBEROS, completado=True),
            InformeActuacion(rol=RolEspecialista.SANITARIO, completado=True),
            InformeActuacion(rol=RolEspecialista.POLICIA, completado=True),
            InformeActuacion(rol=RolEspecialista.MUNICIPAL, completado=True),
        ]
        ahora = datetime.now(timezone.utc)
        informe = InformeResolucion(
            id_emergencia=uuid4(),
            tipo_emergencia=TipoEmergencia.ACCIDENTE_TRAFICO,
            prioridad=Prioridad.ALTA,
            informes_especialistas=intervinientes,
            estado_final=EstadoFinal.RESUELTA,
            traza_participacion=[
                _evento_minimo(ahora),
                _evento_minimo(
                    ahora + timedelta(seconds=2),
                    rol=RolAgente.BOMBEROS,
                    accion="evaluar_situacion",
                    detalle="Confirma incendio activo",
                    agente_id="bomberos_fenix",
                ),
            ],
        )
        roles_presentes = {parte.rol for parte in informe.informes_especialistas}
        assert roles_presentes == set(RolEspecialista)

    def test_rechaza_un_estado_final_inventado(self) -> None:
        """Un valor de `estado_final` fuera del enumerado debe rechazarse."""
        with pytest.raises(ValidationError):
            InformeResolucion.model_validate(
                {
                    "id_emergencia": str(ID_EMERGENCIA_FIJO),
                    "tipo_emergencia": "incendio",
                    "prioridad": "media",
                    "estado_final": "resuelto_a_medias",
                    "traza_participacion": [
                        _evento_minimo(datetime.now(timezone.utc)).model_dump(mode="json"),
                    ],
                },
            )

    def test_rechaza_un_informe_sin_id_de_emergencia(self) -> None:
        """`id_emergencia` es obligatorio: el correlador con la alerta no puede faltar."""
        with pytest.raises(ValidationError):
            InformeResolucion.model_validate(
                {
                    "tipo_emergencia": "incendio",
                    "prioridad": "media",
                    "estado_final": "resuelta",
                    "traza_participacion": [
                        _evento_minimo(datetime.now(timezone.utc)).model_dump(mode="json"),
                    ],
                },
            )

    def test_rechaza_un_informe_sin_traza_de_participacion(self) -> None:
        """`traza_participacion` es obligatoria: sin ella no hay evidencia para validar el hito."""
        with pytest.raises(ValidationError):
            InformeResolucion.model_validate(
                {
                    "id_emergencia": str(ID_EMERGENCIA_FIJO),
                    "tipo_emergencia": "incendio",
                    "prioridad": "media",
                    "estado_final": "resuelta",
                },
            )

    def test_rechaza_un_informe_con_traza_de_participacion_vacia(self) -> None:
        """Una traza con cero eventos no satisface la cobertura mínima."""
        with pytest.raises(ValidationError):
            InformeResolucion(
                id_emergencia=ID_EMERGENCIA_FIJO,
                tipo_emergencia=TipoEmergencia.INCENDIO,
                prioridad=Prioridad.ALTA,
                estado_final=EstadoFinal.RESUELTA,
                traza_participacion=[],
            )

    def test_admite_estado_parcial_con_un_subconjunto_de_especialistas(self) -> None:
        """Un escenario donde solo algunos especialistas intervienen es admisible."""
        intervinientes = [
            InformeActuacion(rol=RolEspecialista.SANITARIO, completado=True),
            InformeActuacion(rol=RolEspecialista.POLICIA, completado=False),
        ]
        informe = InformeResolucion(
            id_emergencia=ID_EMERGENCIA_FIJO,
            tipo_emergencia=TipoEmergencia.OTRO,
            prioridad=Prioridad.MEDIA,
            informes_especialistas=intervinientes,
            estado_final=EstadoFinal.PARCIAL,
            traza_participacion=[_evento_minimo(datetime.now(timezone.utc))],
        )
        assert informe.estado_final is EstadoFinal.PARCIAL
        roles = [interviniente.rol for interviniente in informe.informes_especialistas]
        assert RolEspecialista.BOMBEROS not in roles

    def test_se_serializa_y_se_recompone_sin_perdida(self) -> None:
        """La conversión a JSON y la validación inversa son idempotentes."""
        ahora = datetime.now(timezone.utc)
        original = InformeResolucion(
            id_emergencia=ID_EMERGENCIA_FIJO,
            tipo_emergencia=TipoEmergencia.INUNDACION,
            prioridad=Prioridad.CRITICA,
            informes_especialistas=[
                InformeActuacion(
                    rol=RolEspecialista.MUNICIPAL,
                    completado=True,
                    acciones_realizadas=["corte de suministro eléctrico"],
                ),
            ],
            estado_final=EstadoFinal.RESUELTA,
            resumen="Inundación resuelta tras 90 minutos.",
            traza_participacion=[
                _evento_minimo(ahora),
                _evento_minimo(
                    ahora + timedelta(seconds=30),
                    rol=RolAgente.MUNICIPAL,
                    visibilidad=VisibilidadAgente.PRIVADO,
                    accion="cortar_suministro",
                    detalle="Suministro eléctrico cortado en la calle Mayor",
                    agente_id="municipal_fenix",
                ),
            ],
        )
        cuerpo_json = original.model_dump(mode="json")
        recompuesto = InformeResolucion.model_validate(cuerpo_json)
        assert recompuesto == original
