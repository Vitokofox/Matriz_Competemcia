from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.catalogos import Puesto, PuestoActividadCompetencia
    from app.models.personas import Evaluador, Supervisor, Trabajador
    from app.models.seguridad import Usuario


class Evaluacion(TimestampMixin, Base):
    __tablename__ = "evaluaciones"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('borrador', 'completada', 'anulada')",
            name="estado_valido",
        ),
        CheckConstraint(
            "(supervisor_id IS NOT NULL) != (evaluador_id IS NOT NULL)",
            name="ejecutor_autorizado",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trabajador_id: Mapped[int] = mapped_column(
        ForeignKey("trabajadores.id", ondelete="RESTRICT")
    )
    evaluador_id: Mapped[int | None] = mapped_column(
        ForeignKey("evaluadores.id", ondelete="RESTRICT")
    )
    supervisor_id: Mapped[int | None] = mapped_column(
        ForeignKey("supervisores.id", ondelete="RESTRICT")
    )
    usuario_ejecutor_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT")
    )
    puesto_id: Mapped[int] = mapped_column(
        ForeignKey("puestos.id", ondelete="RESTRICT")
    )
    fecha: Mapped[date] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(
        String(20), default="borrador", server_default="borrador"
    )
    observaciones: Mapped[str | None] = mapped_column(Text)

    trabajador: Mapped[Trabajador] = relationship()
    evaluador: Mapped[Evaluador] = relationship()
    supervisor: Mapped[Supervisor] = relationship()
    usuario_ejecutor: Mapped[Usuario] = relationship()
    puesto: Mapped[Puesto] = relationship()
    detalles: Mapped[list[EvaluacionDetalle]] = relationship(
        back_populates="evaluacion",
        cascade="all, delete-orphan",
    )


class EvaluacionDetalle(TimestampMixin, Base):
    __tablename__ = "evaluacion_detalles"
    __table_args__ = (
        CheckConstraint("nivel_obtenido BETWEEN 1 AND 5", name="nivel_obtenido_1_5"),
        CheckConstraint("nivel_minimo BETWEEN 1 AND 5", name="nivel_minimo_1_5"),
        UniqueConstraint("evaluacion_id", "requisito_id", name="evaluacion_requisito"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluacion_id: Mapped[int] = mapped_column(
        ForeignKey("evaluaciones.id", ondelete="CASCADE")
    )
    requisito_id: Mapped[int] = mapped_column(
        ForeignKey("puesto_actividad_competencias.id", ondelete="RESTRICT")
    )
    nivel_obtenido: Mapped[int] = mapped_column(Integer)
    nivel_minimo: Mapped[int] = mapped_column(Integer)
    observaciones: Mapped[str | None] = mapped_column(Text)

    evaluacion: Mapped[Evaluacion] = relationship(back_populates="detalles")
    requisito: Mapped[PuestoActividadCompetencia] = relationship()

    @hybrid_property
    def aprobado(self) -> bool:
        return self.nivel_obtenido >= self.nivel_minimo

    @aprobado.inplace.expression
    @classmethod
    def _aprobado_expression(cls):
        return cls.nivel_obtenido >= cls.nivel_minimo
