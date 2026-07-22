from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import (
    Evaluacion,
    EvaluacionDetalle,
    PuestoActividad,
    PuestoActividadCompetencia,
    Trabajador,
)


def consulta_trabajadores_capacitados(puesto_id: int) -> Select[tuple[Trabajador]]:
    requisitos = (
        select(PuestoActividadCompetencia.id)
        .join(PuestoActividad)
        .where(PuestoActividad.puesto_id == puesto_id)
    )
    total_requisitos = (
        select(func.count())
        .select_from(PuestoActividadCompetencia)
        .join(PuestoActividad)
        .where(PuestoActividad.puesto_id == puesto_id)
        .scalar_subquery()
    )
    requisitos_aprobados = (
        select(func.count(func.distinct(EvaluacionDetalle.requisito_id)))
        .join(
            PuestoActividadCompetencia,
            PuestoActividadCompetencia.id == EvaluacionDetalle.requisito_id,
        )
        .where(
            EvaluacionDetalle.evaluacion_id == Evaluacion.id,
            EvaluacionDetalle.requisito_id.in_(requisitos),
            EvaluacionDetalle.nivel_obtenido >= PuestoActividadCompetencia.nivel_minimo,
        )
        .correlate(Evaluacion)
        .scalar_subquery()
    )

    return (
        select(Trabajador)
        .join(Evaluacion, Evaluacion.trabajador_id == Trabajador.id)
        .where(
            Trabajador.activo.is_(True),
            Evaluacion.puesto_id == puesto_id,
            Evaluacion.estado == "completada",
            total_requisitos > 0,
            requisitos_aprobados == total_requisitos,
        )
        .distinct()
        .order_by(Trabajador.apellidos, Trabajador.nombres)
    )


def obtener_trabajadores_capacitados(db: Session, puesto_id: int) -> list[Trabajador]:
    return list(db.scalars(consulta_trabajadores_capacitados(puesto_id)).unique())
