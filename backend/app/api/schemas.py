from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CatalogoBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    descripcion: str | None = None
    activo: bool = True


class CatalogoCreate(CatalogoBase):
    pass


class CatalogoUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    descripcion: str | None = None
    activo: bool | None = None


class CatalogoResponse(SchemaBase, CatalogoBase):
    id: int
    creado_en: datetime
    actualizado_en: datetime


class CodigoCatalogoCreate(CatalogoBase):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)


class CodigoCatalogoUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    descripcion: str | None = None
    activo: bool | None = None


class CodigoCatalogoResponse(SchemaBase, CodigoCatalogoCreate):
    id: int
    creado_en: datetime
    actualizado_en: datetime


class ProcesoCreate(CodigoCatalogoCreate):
    area_id: int


class ProcesoUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    descripcion: str | None = None
    area_id: int | None = None
    activo: bool | None = None


class ProcesoResponse(SchemaBase, ProcesoCreate):
    id: int
    activo: bool
    creado_en: datetime
    actualizado_en: datetime


class MaquinaCreate(CodigoCatalogoCreate):
    pass


class MaquinaResponse(SchemaBase, MaquinaCreate):
    id: int
    creado_en: datetime
    actualizado_en: datetime


class PersonaBase(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    documento: str = Field(min_length=1, max_length=50)
    nombres: str = Field(min_length=1, max_length=120)
    apellidos: str = Field(min_length=1, max_length=120)
    correo: str | None = None
    activo: bool = True


class PersonaCreate(PersonaBase):
    pass


class PersonaUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    documento: str | None = Field(default=None, min_length=1, max_length=50)
    nombres: str | None = Field(default=None, min_length=1, max_length=120)
    apellidos: str | None = Field(default=None, min_length=1, max_length=120)
    correo: str | None = None
    activo: bool | None = None


class PersonaResponse(SchemaBase, PersonaBase):
    id: int
    usuario_id: int | None = None
    creado_en: datetime
    actualizado_en: datetime


class TrabajadorCreate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    documento: str = Field(min_length=1, max_length=50)
    nombres: str = Field(min_length=1, max_length=120)
    apellidos: str = Field(min_length=1, max_length=120)
    activo: bool = True


class TrabajadorUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    documento: str | None = Field(default=None, min_length=1, max_length=50)
    nombres: str | None = Field(default=None, min_length=1, max_length=120)
    apellidos: str | None = Field(default=None, min_length=1, max_length=120)
    activo: bool | None = None


class TrabajadorResponse(SchemaBase, TrabajadorCreate):
    id: int
    creado_en: datetime
    actualizado_en: datetime


class AsignacionLaboralCreate(BaseModel):
    cargo_id: int
    area_id: int
    turno_id: int
    fecha_inicio: date


class AsignacionLaboralResponse(SchemaBase, AsignacionLaboralCreate):
    id: int
    trabajador_id: int
    fecha_fin: date | None
    creado_en: datetime
    actualizado_en: datetime


class SupervisorAsignacionCreate(BaseModel):
    supervisor_id: int
    fecha_inicio: date


class TrabajadorPuestoCreate(BaseModel):
    puesto_id: int
    fecha_inicio: date


class TrabajadorRegistroCompleto(BaseModel):
    documento: str = Field(min_length=1, max_length=50)
    nombres: str = Field(min_length=1, max_length=120)
    apellidos: str = Field(min_length=1, max_length=120)
    cargo_id: int
    area_id: int
    turno_id: int
    supervisor_id: int
    puesto_ids: list[int] = Field(min_length=1)
    fecha_inicio: date


class TrabajadorRegistroUpdate(BaseModel):
    documento: str = Field(min_length=1, max_length=50)
    nombres: str = Field(min_length=1, max_length=120)
    apellidos: str = Field(min_length=1, max_length=120)
    cargo_id: int
    area_id: int
    turno_id: int
    supervisor_id: int
    puesto_ids: list[int] = Field(min_length=1)
    fecha_inicio: date


class ChecklistCompetenciaResponse(BaseModel):
    requisito_id: int
    competencia_id: int
    competencia: str
    nivel_minimo: int


class ChecklistActividadResponse(BaseModel):
    actividad_id: int
    actividad: str
    competencias: list[ChecklistCompetenciaResponse]


class HistorialResponse(SchemaBase):
    id: int
    fecha_inicio: date
    fecha_fin: date | None
    creado_en: datetime
    actualizado_en: datetime


class PuestoCreate(CodigoCatalogoCreate):
    cargo_id: int
    area_id: int
    proceso_id: int | None = None
    maquina_id: int | None = None
    tipo_puesto: str = Field(default="manual", pattern="^(operador|ayudante|manual)$")


class PuestoUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    descripcion: str | None = None
    cargo_id: int | None = None
    area_id: int | None = None
    proceso_id: int | None = None
    maquina_id: int | None = None
    tipo_puesto: str | None = Field(
        default=None, pattern="^(operador|ayudante|manual)$"
    )
    activo: bool | None = None


class PuestoResponse(SchemaBase, PuestoCreate):
    id: int
    activo: bool
    creado_en: datetime
    actualizado_en: datetime


class PuestoMaquinaCreate(BaseModel):
    maquina_id: int
    fecha_inicio: date


class MaquinaProcesoCreate(BaseModel):
    proceso_id: int
    fecha_inicio: date


class MaquinaProcesoResponse(SchemaBase, MaquinaProcesoCreate):
    id: int
    maquina_id: int
    fecha_fin: date | None
    creado_en: datetime
    actualizado_en: datetime


class PuestoActividadCreate(BaseModel):
    actividad_id: int


class RequisitoCreate(BaseModel):
    actividad_id: int
    competencia_id: int
    nivel_minimo: int = Field(ge=1, le=5)


class RequisitoResponse(SchemaBase):
    id: int
    puesto_actividad_id: int
    competencia_id: int
    nivel_minimo: int
    creado_en: datetime
    actualizado_en: datetime


class EvaluacionDetalleCreate(BaseModel):
    requisito_id: int
    nivel_obtenido: int = Field(ge=1, le=5)
    observaciones: str | None = None


class EvaluacionDetalleResponse(SchemaBase, EvaluacionDetalleCreate):
    id: int
    evaluacion_id: int
    nivel_minimo: int
    aprobado: bool
    creado_en: datetime
    actualizado_en: datetime


class EvaluacionCreate(BaseModel):
    trabajador_id: int
    puesto_id: int
    fecha: date
    observaciones: str | None = None
    detalles: list[EvaluacionDetalleCreate] = Field(min_length=1)


class EvaluacionUpdate(BaseModel):
    fecha: date | None = None
    observaciones: str | None = None
    detalles: list[EvaluacionDetalleCreate] | None = Field(default=None, min_length=1)


class EvaluacionResponse(SchemaBase):
    id: int
    trabajador_id: int
    evaluador_id: int | None
    supervisor_id: int | None
    usuario_ejecutor_id: int | None
    puesto_id: int
    fecha: date
    estado: str
    observaciones: str | None
    detalles: list[EvaluacionDetalleResponse]
    creado_en: datetime
    actualizado_en: datetime


class TrabajadorCapacitadoResponse(TrabajadorResponse):
    pass


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class VincularUsuarioRequest(BaseModel):
    usuario_id: int


class UsuarioCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    correo: str = Field(min_length=5, max_length=255)
    nombre_completo: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=128)
    activo: bool = True
    rol_ids: list[int] = []


class UsuarioUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=80)
    correo: str | None = Field(default=None, min_length=5, max_length=255)
    nombre_completo: str | None = Field(default=None, min_length=1, max_length=200)
    activo: bool | None = None
    rol_ids: list[int] | None = None


class UsuarioResponse(SchemaBase):
    id: int
    username: str
    correo: str
    nombre_completo: str
    activo: bool
    ultimo_acceso: datetime | None
    roles: list["RolResponse"]
    creado_en: datetime
    actualizado_en: datetime


class PermisoCreate(BaseModel):
    codigo: str = Field(min_length=3, max_length=120)
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str | None = None
    modulo: str = Field(min_length=1, max_length=80)
    accion: str = Field(min_length=1, max_length=80)
    activo: bool = True


class PermisoUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=3, max_length=120)
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    descripcion: str | None = None
    modulo: str | None = Field(default=None, min_length=1, max_length=80)
    accion: str | None = Field(default=None, min_length=1, max_length=80)
    activo: bool | None = None


class PermisoResponse(SchemaBase, PermisoCreate):
    id: int
    sistema: bool
    creado_en: datetime
    actualizado_en: datetime


class RolCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=80)
    descripcion: str | None = None
    activo: bool = True
    permiso_ids: list[int] = []


class RolUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=80)
    descripcion: str | None = None
    activo: bool | None = None
    permiso_ids: list[int] | None = None


class RolResponse(SchemaBase):
    id: int
    nombre: str
    descripcion: str | None
    sistema: bool
    activo: bool
    permisos: list[PermisoResponse]
    creado_en: datetime
    actualizado_en: datetime


class MeResponse(UsuarioResponse):
    permisos: list[str]
