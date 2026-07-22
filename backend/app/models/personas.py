from __future__ import annotations

from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin


class Trabajador(TimestampMixin, Base):
    __tablename__ = "trabajadores"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    documento: Mapped[str] = mapped_column(String(50), unique=True)
    nombres: Mapped[str] = mapped_column(String(120))
    apellidos: Mapped[str] = mapped_column(String(120))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    asignaciones_laborales: Mapped[list[AsignacionLaboral]] = relationship(
        back_populates="trabajador"
    )
    supervisores: Mapped[list[TrabajadorSupervisor]] = relationship(
        back_populates="trabajador"
    )
    puestos: Mapped[list[TrabajadorPuesto]] = relationship(back_populates="trabajador")


class Supervisor(TimestampMixin, Base):
    __tablename__ = "supervisores"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    documento: Mapped[str] = mapped_column(String(50), unique=True)
    nombres: Mapped[str] = mapped_column(String(120))
    apellidos: Mapped[str] = mapped_column(String(120))
    correo: Mapped[str | None] = mapped_column(String(255), unique=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), unique=True
    )

    trabajadores: Mapped[list[TrabajadorSupervisor]] = relationship(
        back_populates="supervisor"
    )


class Evaluador(TimestampMixin, Base):
    __tablename__ = "evaluadores"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    documento: Mapped[str] = mapped_column(String(50), unique=True)
    nombres: Mapped[str] = mapped_column(String(120))
    apellidos: Mapped[str] = mapped_column(String(120))
    correo: Mapped[str | None] = mapped_column(String(255), unique=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), unique=True
    )


class AsignacionLaboral(TimestampMixin, Base):
    __tablename__ = "asignaciones_laborales"
    __table_args__ = (
        CheckConstraint(
            "fecha_fin IS NULL OR fecha_fin >= fecha_inicio",
            name="fechas_validas",
        ),
        Index(
            "uq_asignacion_laboral_activa",
            "trabajador_id",
            unique=True,
            sqlite_where=text("fecha_fin IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trabajador_id: Mapped[int] = mapped_column(
        ForeignKey("trabajadores.id", ondelete="RESTRICT")
    )
    cargo_id: Mapped[int] = mapped_column(ForeignKey("cargos.id", ondelete="RESTRICT"))
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id", ondelete="RESTRICT"))
    turno_id: Mapped[int] = mapped_column(ForeignKey("turnos.id", ondelete="RESTRICT"))
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date)

    trabajador: Mapped[Trabajador] = relationship(
        back_populates="asignaciones_laborales"
    )


class TrabajadorSupervisor(TimestampMixin, Base):
    __tablename__ = "trabajador_supervisores"
    __table_args__ = (
        CheckConstraint(
            "fecha_fin IS NULL OR fecha_fin >= fecha_inicio",
            name="fechas_validas",
        ),
        Index(
            "uq_trabajador_supervisor_activo",
            "trabajador_id",
            unique=True,
            sqlite_where=text("fecha_fin IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trabajador_id: Mapped[int] = mapped_column(
        ForeignKey("trabajadores.id", ondelete="RESTRICT")
    )
    supervisor_id: Mapped[int] = mapped_column(
        ForeignKey("supervisores.id", ondelete="RESTRICT")
    )
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date)

    trabajador: Mapped[Trabajador] = relationship(back_populates="supervisores")
    supervisor: Mapped[Supervisor] = relationship(back_populates="trabajadores")


class TrabajadorPuesto(TimestampMixin, Base):
    __tablename__ = "trabajador_puestos"
    __table_args__ = (
        CheckConstraint(
            "fecha_fin IS NULL OR fecha_fin >= fecha_inicio",
            name="fechas_validas",
        ),
        Index(
            "uq_trabajador_puesto_activo",
            "trabajador_id",
            "puesto_id",
            unique=True,
            sqlite_where=text("fecha_fin IS NULL"),
        ),
        UniqueConstraint(
            "trabajador_id",
            "puesto_id",
            "fecha_inicio",
            name="trabajador_puesto_fecha",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trabajador_id: Mapped[int] = mapped_column(
        ForeignKey("trabajadores.id", ondelete="RESTRICT")
    )
    puesto_id: Mapped[int] = mapped_column(
        ForeignKey("puestos.id", ondelete="RESTRICT")
    )
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date)

    trabajador: Mapped[Trabajador] = relationship(back_populates="puestos")
