from __future__ import annotations

from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin


class Area(TimestampMixin, Base):
    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")


class Cargo(TimestampMixin, Base):
    __tablename__ = "cargos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")


class Turno(TimestampMixin, Base):
    __tablename__ = "turnos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")


class Proceso(TimestampMixin, Base):
    __tablename__ = "procesos"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    nombre: Mapped[str] = mapped_column(String(150), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id", ondelete="RESTRICT"))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    area: Mapped[Area] = relationship()
    maquinas: Mapped[list[MaquinaProceso]] = relationship(back_populates="proceso")
    puestos: Mapped[list[Puesto]] = relationship(back_populates="proceso")


class Maquina(TimestampMixin, Base):
    __tablename__ = "maquinas"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    asignaciones_puesto: Mapped[list[PuestoMaquina]] = relationship(
        back_populates="maquina"
    )
    procesos: Mapped[list[MaquinaProceso]] = relationship(back_populates="maquina")


class MaquinaProceso(TimestampMixin, Base):
    __tablename__ = "maquina_procesos"
    __table_args__ = (
        CheckConstraint(
            "fecha_fin IS NULL OR fecha_fin >= fecha_inicio", name="fechas_validas"
        ),
        Index(
            "uq_maquina_proceso_activo",
            "maquina_id",
            unique=True,
            sqlite_where=text("fecha_fin IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    maquina_id: Mapped[int] = mapped_column(
        ForeignKey("maquinas.id", ondelete="RESTRICT")
    )
    proceso_id: Mapped[int] = mapped_column(
        ForeignKey("procesos.id", ondelete="RESTRICT")
    )
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date)

    maquina: Mapped[Maquina] = relationship(back_populates="procesos")
    proceso: Mapped[Proceso] = relationship(back_populates="maquinas")


class Actividad(TimestampMixin, Base):
    __tablename__ = "actividades"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    asignaciones_puesto: Mapped[list[PuestoActividad]] = relationship(
        back_populates="actividad"
    )


class Competencia(TimestampMixin, Base):
    __tablename__ = "competencias"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    nombre: Mapped[str] = mapped_column(String(150), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")


class Puesto(TimestampMixin, Base):
    __tablename__ = "puestos"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    nombre: Mapped[str] = mapped_column(String(150), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    cargo_id: Mapped[int] = mapped_column(ForeignKey("cargos.id", ondelete="RESTRICT"))
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id", ondelete="RESTRICT"))
    proceso_id: Mapped[int | None] = mapped_column(
        ForeignKey("procesos.id", ondelete="RESTRICT")
    )
    maquina_id: Mapped[int | None] = mapped_column(
        ForeignKey("maquinas.id", ondelete="RESTRICT")
    )
    tipo_puesto: Mapped[str] = mapped_column(
        String(20), default="manual", server_default="manual"
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    __table_args__ = (
        CheckConstraint(
            "tipo_puesto IN ('operador', 'ayudante', 'manual')",
            name="tipo_puesto_valido",
        ),
    )

    cargo: Mapped[Cargo] = relationship()
    area: Mapped[Area] = relationship()
    proceso: Mapped[Proceso] = relationship(back_populates="puestos")
    maquina: Mapped[Maquina | None] = relationship()
    asignaciones_maquina: Mapped[list[PuestoMaquina]] = relationship(
        back_populates="puesto"
    )
    actividades: Mapped[list[PuestoActividad]] = relationship(
        back_populates="puesto",
        cascade="all, delete-orphan",
    )


class PuestoMaquina(TimestampMixin, Base):
    __tablename__ = "puesto_maquinas"
    __table_args__ = (
        CheckConstraint(
            "fecha_fin IS NULL OR fecha_fin >= fecha_inicio",
            name="fechas_validas",
        ),
        Index(
            "uq_puesto_maquina_activa",
            "puesto_id",
            unique=True,
            sqlite_where=text("fecha_fin IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    puesto_id: Mapped[int] = mapped_column(
        ForeignKey("puestos.id", ondelete="RESTRICT")
    )
    maquina_id: Mapped[int] = mapped_column(
        ForeignKey("maquinas.id", ondelete="RESTRICT")
    )
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date)

    puesto: Mapped[Puesto] = relationship(back_populates="asignaciones_maquina")
    maquina: Mapped[Maquina] = relationship(back_populates="asignaciones_puesto")


class PuestoActividad(TimestampMixin, Base):
    __tablename__ = "puesto_actividades"
    __table_args__ = (
        UniqueConstraint("puesto_id", "actividad_id", name="puesto_actividad"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    puesto_id: Mapped[int] = mapped_column(ForeignKey("puestos.id", ondelete="CASCADE"))
    actividad_id: Mapped[int] = mapped_column(
        ForeignKey("actividades.id", ondelete="RESTRICT")
    )

    puesto: Mapped[Puesto] = relationship(back_populates="actividades")
    actividad: Mapped[Actividad] = relationship(back_populates="asignaciones_puesto")
    requisitos: Mapped[list[PuestoActividadCompetencia]] = relationship(
        back_populates="puesto_actividad",
        cascade="all, delete-orphan",
    )


class PuestoActividadCompetencia(TimestampMixin, Base):
    __tablename__ = "puesto_actividad_competencias"
    __table_args__ = (
        CheckConstraint("nivel_minimo BETWEEN 1 AND 5", name="nivel_minimo_1_5"),
        UniqueConstraint(
            "puesto_actividad_id",
            "competencia_id",
            name="puesto_actividad_competencia",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    puesto_actividad_id: Mapped[int] = mapped_column(
        ForeignKey("puesto_actividades.id", ondelete="CASCADE")
    )
    competencia_id: Mapped[int] = mapped_column(
        ForeignKey("competencias.id", ondelete="RESTRICT")
    )
    nivel_minimo: Mapped[int] = mapped_column(Integer)

    puesto_actividad: Mapped[PuestoActividad] = relationship(
        back_populates="requisitos"
    )
    competencia: Mapped[Competencia] = relationship()
