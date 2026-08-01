from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.catalogos import Actividad, Puesto
    from app.models.evaluaciones import Evaluacion
    from app.models.personas import Trabajador
    from app.models.seguridad import Usuario


class PlanCapacitacion(TimestampMixin, Base):
    __tablename__ = "planes_capacitacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    trabajador_id: Mapped[int] = mapped_column(
        ForeignKey("trabajadores.id", ondelete="RESTRICT")
    )
    puesto_id: Mapped[int] = mapped_column(
        ForeignKey("puestos.id", ondelete="RESTRICT")
    )
    evaluacion_id: Mapped[int | None] = mapped_column(
        ForeignKey("evaluaciones.id", ondelete="SET NULL")
    )
    tipo: Mapped[str] = mapped_column(String(30))
    estado: Mapped[str] = mapped_column(
        String(20), default="pendiente", server_default="pendiente"
    )
    motivo: Mapped[str | None] = mapped_column(Text)
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date)
    creado_por_usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    trabajador: Mapped[Trabajador] = relationship()
    puesto: Mapped[Puesto] = relationship()
    evaluacion: Mapped[Evaluacion | None] = relationship()
    creado_por: Mapped[Usuario | None] = relationship()
    actividades: Mapped[list[PlanCapacitacionActividad]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanCapacitacionActividad.fecha_programada",
    )


class PlanCapacitacionActividad(TimestampMixin, Base):
    __tablename__ = "planes_capacitacion_actividades"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("planes_capacitacion.id", ondelete="CASCADE")
    )
    actividad_id: Mapped[int] = mapped_column(
        ForeignKey("actividades.id", ondelete="RESTRICT")
    )
    fecha_programada: Mapped[date] = mapped_column(Date)
    fecha_reprogramacion_1: Mapped[date | None] = mapped_column(Date)
    fecha_reprogramacion_2: Mapped[date | None] = mapped_column(Date)
    fecha_cumplimiento: Mapped[date | None] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(
        String(20), default="pendiente", server_default="pendiente"
    )
    observaciones: Mapped[str | None] = mapped_column(Text)
    completada_por_usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    plan: Mapped[PlanCapacitacion] = relationship(back_populates="actividades")
    actividad: Mapped[Actividad] = relationship()
    completada_por: Mapped[Usuario | None] = relationship(
        foreign_keys=[completada_por_usuario_id]
    )

    @property
    def fecha_vigente(self) -> date:
        return (
            self.fecha_reprogramacion_2
            or self.fecha_reprogramacion_1
            or self.fecha_programada
        )

    @property
    def reprogramaciones(self) -> int:
        return int(self.fecha_reprogramacion_1 is not None) + int(
            self.fecha_reprogramacion_2 is not None
        )
