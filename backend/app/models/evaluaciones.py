from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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
    from app.models.catalogos import (
        MatrizPuestoVersion,
        Puesto,
        PuestoActividadCompetencia,
        PuestoActividadCriterio,
    )
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
    matriz_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("matriz_puesto_versiones.id", ondelete="RESTRICT")
    )
    fecha: Mapped[date] = mapped_column(Date)
    proxima_fecha: Mapped[date | None] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(
        String(20), default="borrador", server_default="borrador"
    )
    observaciones: Mapped[str | None] = mapped_column(Text)
    correccion_habilitada_hasta: Mapped[datetime | None]
    correccion_habilitada_por_id: Mapped[int | None] = mapped_column(Integer)
    motivo_correccion: Mapped[str | None] = mapped_column(Text)
    motivo_anulacion: Mapped[str | None] = mapped_column(Text)
    anulada_en: Mapped[datetime | None]
    anulada_por_usuario_id: Mapped[int | None] = mapped_column(Integer)
    resultado: Mapped[str | None] = mapped_column(String(20))
    vigente: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")

    trabajador: Mapped[Trabajador] = relationship()
    evaluador: Mapped[Evaluador] = relationship()
    supervisor: Mapped[Supervisor] = relationship()
    usuario_ejecutor: Mapped[Usuario] = relationship(foreign_keys=[usuario_ejecutor_id])
    puesto: Mapped[Puesto] = relationship()
    matriz_version: Mapped[MatrizPuestoVersion | None] = relationship()
    detalles: Mapped[list[EvaluacionDetalle]] = relationship(
        back_populates="evaluacion",
        cascade="all, delete-orphan",
    )
    criterios: Mapped[list[EvaluacionCriterio]] = relationship(
        back_populates="evaluacion", cascade="all, delete-orphan"
    )
    versiones: Mapped[list[EvaluacionVersion]] = relationship(
        back_populates="evaluacion", cascade="all, delete-orphan"
    )


class EvaluacionDetalle(TimestampMixin, Base):
    __tablename__ = "evaluacion_detalles"
    __table_args__ = (
        CheckConstraint("nivel_obtenido BETWEEN 0 AND 4", name="nivel_obtenido_0_4"),
        CheckConstraint("nivel_minimo BETWEEN 0 AND 4", name="nivel_minimo_0_4"),
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


class EvaluacionCriterio(TimestampMixin, Base):
    __tablename__ = "evaluacion_criterios"
    __table_args__ = (
        CheckConstraint("nivel_obtenido BETWEEN 0 AND 4", name="nivel_criterio_0_4"),
        UniqueConstraint(
            "evaluacion_id", "puesto_criterio_id", name="evaluacion_puesto_criterio"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluacion_id: Mapped[int] = mapped_column(
        ForeignKey("evaluaciones.id", ondelete="CASCADE")
    )
    puesto_criterio_id: Mapped[int] = mapped_column(
        ForeignKey("puesto_actividad_criterios.id", ondelete="RESTRICT")
    )
    nivel_obtenido: Mapped[int] = mapped_column(Integer)
    observaciones: Mapped[str | None] = mapped_column(Text)
    evidencia: Mapped[str | None] = mapped_column(Text)
    actividad_nombre: Mapped[str] = mapped_column(String(150))
    criterio_descripcion: Mapped[str] = mapped_column(Text)
    referencia: Mapped[str | None] = mapped_column(String(100))
    orden: Mapped[int] = mapped_column(Integer)
    critico: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    critico_incumplido: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0"
    )

    evaluacion: Mapped[Evaluacion] = relationship(back_populates="criterios")
    puesto_criterio: Mapped[PuestoActividadCriterio] = relationship()


class EvaluacionVersion(TimestampMixin, Base):
    __tablename__ = "evaluacion_versiones"

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluacion_id: Mapped[int] = mapped_column(
        ForeignKey("evaluaciones.id", ondelete="CASCADE")
    )
    version: Mapped[int] = mapped_column(Integer)
    datos: Mapped[str] = mapped_column(Text)
    motivo: Mapped[str] = mapped_column(Text)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    evaluacion: Mapped[Evaluacion] = relationship(back_populates="versiones")
