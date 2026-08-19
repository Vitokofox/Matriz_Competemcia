from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import (
    Evaluacion,
    Trabajador,
)


def consulta_trabajadores_capacitados(puesto_id: int) -> Select[tuple[Trabajador]]:
    return (
        select(Trabajador)
        .join(Evaluacion, Evaluacion.trabajador_id == Trabajador.id)
        .where(
            Trabajador.activo.is_(True),
            Evaluacion.puesto_id == puesto_id,
            Evaluacion.estado == "completada",
            Evaluacion.vigente.is_(True),
            Evaluacion.resultado == "aprobada",
        )
        .distinct()
        .order_by(Trabajador.apellidos, Trabajador.nombres)
    )


def obtener_trabajadores_capacitados(db: Session, puesto_id: int) -> list[Trabajador]:
    return list(db.scalars(consulta_trabajadores_capacitados(puesto_id)).unique())
