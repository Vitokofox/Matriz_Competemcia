from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin

usuario_roles = Table(
    "usuario_roles",
    Base.metadata,
    Column(
        "usuario_id", ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("rol_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

rol_permisos = Table(
    "rol_permisos",
    Base.metadata,
    Column("rol_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permiso_id", ForeignKey("permisos.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Usuario(TimestampMixin, Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    correo: Mapped[str] = mapped_column(String(255), unique=True)
    nombre_completo: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    ultimo_acceso: Mapped[datetime | None]

    roles: Mapped[list[Rol]] = relationship(
        secondary=usuario_roles, back_populates="usuarios"
    )


class Rol(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    sistema: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    usuarios: Mapped[list[Usuario]] = relationship(
        secondary=usuario_roles, back_populates="roles"
    )
    permisos: Mapped[list[Permiso]] = relationship(
        secondary=rol_permisos, back_populates="roles"
    )


class Permiso(TimestampMixin, Base):
    __tablename__ = "permisos"
    __table_args__ = (UniqueConstraint("codigo", name="permiso_codigo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(120))
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str | None] = mapped_column(Text)
    modulo: Mapped[str] = mapped_column(String(80))
    accion: Mapped[str] = mapped_column(String(80))
    sistema: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    roles: Mapped[list[Rol]] = relationship(
        secondary=rol_permisos, back_populates="permisos"
    )
