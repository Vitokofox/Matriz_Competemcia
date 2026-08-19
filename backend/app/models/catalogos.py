from __future__ import annotations

from datetime import date, datetime

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
    source_key: Mapped[str | None] = mapped_column(String(120), unique=True)
    nombre: Mapped[str] = mapped_column(String(150), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    punto_procedimiento: Mapped[str | None] = mapped_column(String(100))
    referencia: Mapped[str | None] = mapped_column(String(100))
    orden: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    asignaciones_puesto: Mapped[list[PuestoActividad]] = relationship(
        back_populates="actividad"
    )
    criterios: Mapped[list[ActividadCriterio]] = relationship(
        back_populates="actividad", cascade="all, delete-orphan"
    )
    areas: Mapped[list[ActividadArea]] = relationship(
        back_populates="actividad", cascade="all, delete-orphan"
    )
    maquinas: Mapped[list[ActividadMaquina]] = relationship(
        back_populates="actividad", cascade="all, delete-orphan"
    )


class ActividadArea(TimestampMixin, Base):
    __tablename__ = "actividad_areas"
    __table_args__ = (UniqueConstraint("actividad_id", "area_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    actividad_id: Mapped[int] = mapped_column(
        ForeignKey("actividades.id", ondelete="CASCADE")
    )
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id", ondelete="RESTRICT"))

    actividad: Mapped[Actividad] = relationship(back_populates="areas")
    area: Mapped[Area] = relationship()


class ActividadMaquina(TimestampMixin, Base):
    __tablename__ = "actividad_maquinas"
    __table_args__ = (UniqueConstraint("actividad_id", "maquina_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    actividad_id: Mapped[int] = mapped_column(
        ForeignKey("actividades.id", ondelete="CASCADE")
    )
    maquina_id: Mapped[int] = mapped_column(
        ForeignKey("maquinas.id", ondelete="RESTRICT")
    )

    actividad: Mapped[Actividad] = relationship(back_populates="maquinas")
    maquina: Mapped[Maquina] = relationship()


class Competencia(TimestampMixin, Base):
    __tablename__ = "competencias"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    nombre: Mapped[str] = mapped_column(String(150), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    dimension: Mapped[str] = mapped_column(
        String(30), default="tecnica", server_default="tecnica"
    )
    critica: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    nivel_sugerido: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    __table_args__ = (
        CheckConstraint(
            "dimension IN ('tecnica', 'conductual', 'seguridad', "
            "'calidad', 'coordinacion')",
            name="dimension_competencia_valida",
        ),
        CheckConstraint("nivel_sugerido BETWEEN 0 AND 4", name="nivel_sugerido_0_4"),
    )
    requisitos: Mapped[list[PuestoActividadCompetencia]] = relationship(
        back_populates="competencia"
    )


class ActividadCriterio(TimestampMixin, Base):
    __tablename__ = "actividad_criterios"
    __table_args__ = (
        CheckConstraint("orden >= 0", name="ck_actividad_criterios_orden_no_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_key: Mapped[str | None] = mapped_column(String(120), unique=True)
    actividad_id: Mapped[int] = mapped_column(
        ForeignKey("actividades.id", ondelete="CASCADE")
    )
    descripcion: Mapped[str] = mapped_column(Text)
    referencia: Mapped[str | None] = mapped_column(String(100))
    orden: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    critico: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    actividad: Mapped[Actividad] = relationship(back_populates="criterios")
    competencias: Mapped[list[ActividadCriterioCompetencia]] = relationship(
        back_populates="criterio", cascade="all, delete-orphan"
    )


class ActividadCriterioCompetencia(TimestampMixin, Base):
    __tablename__ = "actividad_criterio_competencias"
    __table_args__ = (UniqueConstraint("criterio_id", "competencia_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    criterio_id: Mapped[int] = mapped_column(
        ForeignKey("actividad_criterios.id", ondelete="CASCADE")
    )
    competencia_id: Mapped[int] = mapped_column(
        ForeignKey("competencias.id", ondelete="RESTRICT")
    )

    criterio: Mapped[ActividadCriterio] = relationship(back_populates="competencias")
    competencia: Mapped[Competencia] = relationship()


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
    versiones_matriz: Mapped[list[MatrizPuestoVersion]] = relationship(
        back_populates="puesto", cascade="all, delete-orphan"
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


class ImportacionMatriz(TimestampMixin, Base):
    __tablename__ = "importaciones_matriz"
    __table_args__ = (
        UniqueConstraint(
            "maquina_id",
            "normalized_hash",
            "importer_version",
            name="importacion_maquina_contenido_reglas",
        ),
        CheckConstraint(
            "estado IN ('validada', 'publicada', 'fallida')",
            name="estado_importacion_matriz_valido",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    maquina_id: Mapped[int] = mapped_column(
        ForeignKey("maquinas.id", ondelete="RESTRICT")
    )
    raw_source_hash: Mapped[str] = mapped_column(String(64))
    normalized_hash: Mapped[str] = mapped_column(String(64))
    importer_version: Mapped[str] = mapped_column(String(20))
    fuente: Mapped[str] = mapped_column(String(255))
    estado: Mapped[str] = mapped_column(String(20), default="validada")
    creado_por_usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    maquina: Mapped[Maquina] = relationship()
    versiones: Mapped[list[MatrizPuestoVersion]] = relationship(
        back_populates="importacion"
    )


class BorradorImportacionMatriz(TimestampMixin, Base):
    __tablename__ = "borradores_importacion_matriz"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('analizado', 'configurado', 'validado', "
            "'publicado', 'fallido')",
            name="estado_borrador_importacion_valido",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(36), unique=True)
    archivo_nombre: Mapped[str] = mapped_column(String(255))
    procedure_code: Mapped[str] = mapped_column(String(100))
    raw_source_hash: Mapped[str] = mapped_column(String(64))
    normalized_hash: Mapped[str] = mapped_column(String(64))
    datos_normalizados: Mapped[str] = mapped_column(Text)
    configuracion: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20), default="analizado")
    errores: Mapped[str | None] = mapped_column(Text)
    creado_por_usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )


class MatrizPuestoVersion(TimestampMixin, Base):
    __tablename__ = "matriz_puesto_versiones"
    __table_args__ = (
        UniqueConstraint("puesto_id", "version", name="matriz_puesto_version"),
        UniqueConstraint(
            "puesto_id",
            "source_hash",
            "importer_version",
            name="matriz_puesto_fuente_reglas",
        ),
        CheckConstraint(
            "estado IN ('borrador', 'publicada', 'retirada')",
            name="estado_matriz_valido",
        ),
        Index(
            "uq_matriz_puesto_publicada",
            "puesto_id",
            unique=True,
            sqlite_where=text("estado = 'publicada'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    puesto_id: Mapped[int] = mapped_column(ForeignKey("puestos.id", ondelete="CASCADE"))
    importacion_id: Mapped[int | None] = mapped_column(
        ForeignKey("importaciones_matriz.id", ondelete="SET NULL")
    )
    version: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20), default="borrador")
    source_hash: Mapped[str] = mapped_column(String(64))
    importer_version: Mapped[str] = mapped_column(
        String(20), default="1", server_default="1"
    )
    fuente: Mapped[str | None] = mapped_column(String(255))
    publicada_en: Mapped[datetime | None]

    puesto: Mapped[Puesto] = relationship(back_populates="versiones_matriz")
    importacion: Mapped[ImportacionMatriz | None] = relationship(
        back_populates="versiones"
    )
    actividades: Mapped[list[PuestoActividad]] = relationship(
        back_populates="matriz_version", cascade="all, delete-orphan"
    )


class PuestoActividad(TimestampMixin, Base):
    __tablename__ = "puesto_actividades"
    __table_args__ = (
        UniqueConstraint(
            "puesto_id",
            "actividad_id",
            "matriz_version_id",
            name="puesto_actividad_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    puesto_id: Mapped[int] = mapped_column(ForeignKey("puestos.id", ondelete="CASCADE"))
    actividad_id: Mapped[int] = mapped_column(
        ForeignKey("actividades.id", ondelete="RESTRICT")
    )
    matriz_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("matriz_puesto_versiones.id", ondelete="CASCADE")
    )

    puesto: Mapped[Puesto] = relationship(back_populates="actividades")
    actividad: Mapped[Actividad] = relationship(back_populates="asignaciones_puesto")
    matriz_version: Mapped[MatrizPuestoVersion | None] = relationship(
        back_populates="actividades"
    )
    requisitos: Mapped[list[PuestoActividadCompetencia]] = relationship(
        back_populates="puesto_actividad",
        cascade="all, delete-orphan",
    )
    criterios_evaluables: Mapped[list[PuestoActividadCriterio]] = relationship(
        back_populates="puesto_actividad", cascade="all, delete-orphan"
    )


class PuestoActividadCompetencia(TimestampMixin, Base):
    __tablename__ = "puesto_actividad_competencias"
    __table_args__ = (
        CheckConstraint("nivel_minimo BETWEEN 0 AND 4", name="nivel_minimo_0_4"),
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
    competencia: Mapped[Competencia] = relationship(back_populates="requisitos")
    criterios: Mapped[list[PuestoActividadCriterioRequisito]] = relationship(
        back_populates="requisito", cascade="all, delete-orphan"
    )


class PuestoActividadCriterio(TimestampMixin, Base):
    __tablename__ = "puesto_actividad_criterios"
    __table_args__ = (
        UniqueConstraint("puesto_actividad_id", "source_key"),
        UniqueConstraint("puesto_actividad_id", "criterio_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    puesto_actividad_id: Mapped[int] = mapped_column(
        ForeignKey("puesto_actividades.id", ondelete="CASCADE")
    )
    criterio_id: Mapped[int] = mapped_column(
        ForeignKey("actividad_criterios.id", ondelete="RESTRICT")
    )
    source_key: Mapped[str] = mapped_column(String(120))
    orden: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    obligatorio: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    critico: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    puesto_actividad: Mapped[PuestoActividad] = relationship(
        back_populates="criterios_evaluables"
    )
    criterio: Mapped[ActividadCriterio] = relationship()
    requisitos: Mapped[list[PuestoActividadCriterioRequisito]] = relationship(
        back_populates="puesto_criterio", cascade="all, delete-orphan"
    )
    indicadores: Mapped[list[CriterioIndicador]] = relationship(
        back_populates="puesto_criterio", cascade="all, delete-orphan"
    )


class PuestoActividadCriterioRequisito(TimestampMixin, Base):
    __tablename__ = "puesto_actividad_criterio_requisitos"
    __table_args__ = (UniqueConstraint("puesto_criterio_id", "requisito_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    puesto_criterio_id: Mapped[int] = mapped_column(
        ForeignKey("puesto_actividad_criterios.id", ondelete="CASCADE")
    )
    requisito_id: Mapped[int] = mapped_column(
        ForeignKey("puesto_actividad_competencias.id", ondelete="CASCADE")
    )

    puesto_criterio: Mapped[PuestoActividadCriterio] = relationship(
        back_populates="requisitos"
    )
    requisito: Mapped[PuestoActividadCompetencia] = relationship(
        back_populates="criterios"
    )


class CriterioIndicador(TimestampMixin, Base):
    __tablename__ = "criterio_indicadores"
    __table_args__ = (UniqueConstraint("puesto_criterio_id", "categoria", "texto"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    puesto_criterio_id: Mapped[int] = mapped_column(
        ForeignKey("puesto_actividad_criterios.id", ondelete="CASCADE")
    )
    categoria: Mapped[str] = mapped_column(String(30))
    texto: Mapped[str] = mapped_column(Text)

    puesto_criterio: Mapped[PuestoActividadCriterio] = relationship(
        back_populates="indicadores"
    )
