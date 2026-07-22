from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin


class SecuenciaCodigo(TimestampMixin, Base):
    __tablename__ = "secuencias_codigos"

    id: Mapped[int] = mapped_column(primary_key=True)
    entidad: Mapped[str] = mapped_column(String(50), unique=True)
    prefijo: Mapped[str] = mapped_column(String(10), unique=True)
    siguiente_numero: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    longitud: Mapped[int] = mapped_column(Integer, default=4, server_default="4")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
