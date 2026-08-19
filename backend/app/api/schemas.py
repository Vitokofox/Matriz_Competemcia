from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class CompetenciaCreate(CodigoCatalogoCreate):
    dimension: str = Field(
        default="tecnica",
        pattern="^(tecnica|conductual|seguridad|calidad|coordinacion)$",
    )
    critica: bool = False
    nivel_sugerido: int = Field(default=3, ge=0, le=4)


class CompetenciaUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    descripcion: str | None = None
    dimension: str | None = Field(
        default=None,
        pattern="^(tecnica|conductual|seguridad|calidad|coordinacion)$",
    )
    critica: bool | None = None
    nivel_sugerido: int | None = Field(default=None, ge=0, le=4)
    activo: bool | None = None


class CodigoCatalogoUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    descripcion: str | None = None
    activo: bool | None = None


class CodigoCatalogoResponse(SchemaBase, CodigoCatalogoCreate):
    id: int
    creado_en: datetime
    actualizado_en: datetime


class CompetenciaResponse(SchemaBase, CompetenciaCreate):
    id: int
    activo: bool
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
    dimension: str
    critica: bool


class ChecklistCriterioResponse(BaseModel):
    puesto_criterio_id: int
    descripcion: str
    referencia: str | None
    critico: bool
    obligatorio: bool
    competencias: list[ChecklistCompetenciaResponse]
    indicadores: list[str]


class ChecklistActividadResponse(BaseModel):
    actividad_id: int
    actividad: str
    competencias: list[ChecklistCompetenciaResponse]
    criterios: list[ChecklistCriterioResponse]


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


class ActividadCriterioCreate(BaseModel):
    descripcion: str = Field(min_length=1)
    referencia: str | None = Field(default=None, max_length=100)
    orden: int = Field(default=0, ge=0)
    critico: bool = False
    activo: bool = True


class FichaCriterioCreate(ActividadCriterioCreate):
    competencia_ids: list[int] = []


class FichaCompetenciaPuestoCreate(BaseModel):
    competencia_id: int
    nivel_minimo: int = Field(ge=0, le=4)


class FichaPuestoCreate(BaseModel):
    puesto_id: int
    competencias: list[FichaCompetenciaPuestoCreate] = []


class FichaOperativaCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    descripcion: str | None = None
    punto_procedimiento: str | None = Field(default=None, max_length=100)
    referencia: str | None = Field(default=None, max_length=100)
    orden: int = Field(default=0, ge=0)
    area_ids: list[int] = []
    maquina_ids: list[int] = []
    criterios: list[FichaCriterioCreate] = []
    puestos: list[FichaPuestoCreate] = []


class FichaOperativaResponse(SchemaBase):
    actividad_id: int
    actividad: str
    criterios_creados: int
    areas_asociadas: int
    maquinas_asociadas: int
    puestos_asociados: int
    requisitos_creados: int


class PerfilRoleConfig(BaseModel):
    enabled: bool = True
    position_id: int | None = None
    general_level: int = Field(ge=0, le=4)
    safety_level: int = Field(ge=3, le=4)


class PerfilDestinationConfig(BaseModel):
    machine_id: int
    equipment_label: str | None = None
    roles: dict[str, PerfilRoleConfig]


class PerfilActivityConfig(BaseModel):
    included_roles: list[str]


class PerfilCriterionConfig(BaseModel):
    included_roles: list[str]
    required: bool = True
    critical: bool = False
    macro_keys: list[str]


class PerfilImportConfig(BaseModel):
    destinations: list[PerfilDestinationConfig] = Field(min_length=1)
    activities: dict[str, PerfilActivityConfig]
    criteria: dict[str, PerfilCriterionConfig]


class ActividadCriterioUpdate(BaseModel):
    descripcion: str | None = Field(default=None, min_length=1)
    referencia: str | None = Field(default=None, max_length=100)
    orden: int | None = Field(default=None, ge=0)
    critico: bool | None = None
    activo: bool | None = None


class ActividadCriterioResponse(SchemaBase, ActividadCriterioCreate):
    id: int
    actividad_id: int
    creado_en: datetime
    actualizado_en: datetime


class RequisitoCreate(BaseModel):
    actividad_id: int
    competencia_id: int
    nivel_minimo: int = Field(ge=0, le=4)


class RequisitoUpdate(BaseModel):
    nivel_minimo: int = Field(ge=0, le=4)


class RequisitoResponse(SchemaBase):
    id: int
    puesto_actividad_id: int
    competencia_id: int
    nivel_minimo: int
    creado_en: datetime
    actualizado_en: datetime


class EvaluacionCriterioCreate(BaseModel):
    puesto_criterio_id: int
    nivel_obtenido: int = Field(ge=0, le=4)
    observaciones: str | None = None
    evidencia: str | None = None

    @model_validator(mode="after")
    def require_evidence_for_gap(self):
        if self.nivel_obtenido < 3 and not (self.evidencia or self.observaciones):
            raise ValueError("Los niveles 0, 1 y 2 requieren evidencia u observación")
        return self


class EvaluacionCriterioResponse(SchemaBase, EvaluacionCriterioCreate):
    id: int
    evaluacion_id: int
    critico_incumplido: bool
    actividad_nombre: str
    criterio_descripcion: str
    referencia: str | None
    orden: int
    critico: bool
    creado_en: datetime
    actualizado_en: datetime


class EvaluacionDetalleCreate(BaseModel):
    requisito_id: int
    nivel_obtenido: int = Field(ge=0, le=4)
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
    criterios: list[EvaluacionCriterioCreate] = Field(min_length=1)
    proxima_fecha: date | None = None


class EvaluacionUpdate(BaseModel):
    fecha: date | None = None
    observaciones: str | None = None
    criterios: list[EvaluacionCriterioCreate] | None = None
    proxima_fecha: date | None = None


class EvaluacionResponse(SchemaBase):
    id: int
    trabajador_id: int
    evaluador_id: int | None
    supervisor_id: int | None
    usuario_ejecutor_id: int | None
    puesto_id: int
    matriz_version_id: int | None
    fecha: date
    estado: str
    observaciones: str | None
    proxima_fecha: date | None
    correccion_habilitada_hasta: datetime | None
    motivo_correccion: str | None
    motivo_anulacion: str | None
    anulada_en: datetime | None
    resultado: str | None
    vigente: bool
    detalles: list[EvaluacionDetalleResponse]
    criterios: list[EvaluacionCriterioResponse]
    creado_en: datetime
    actualizado_en: datetime


class PlanCapacitacionActividadCreate(BaseModel):
    actividad_id: int
    fecha_programada: date


class PlanCapacitacionActividadResponse(SchemaBase):
    id: int
    plan_id: int
    actividad_id: int
    fecha_programada: date
    fecha_reprogramacion_1: date | None
    fecha_reprogramacion_2: date | None
    fecha_cumplimiento: date | None
    estado: str
    observaciones: str | None
    creado_en: datetime
    actualizado_en: datetime


class PlanCapacitacionCreate(BaseModel):
    trabajador_id: int
    puesto_id: int
    tipo: str = Field(pattern="^(reevaluacion|nuevo_puesto|reemplazo|manual)$")
    motivo: str | None = None
    fecha_inicio: date
    actividades: list[PlanCapacitacionActividadCreate] = Field(min_length=1)


class PlanCapacitacionResponse(SchemaBase):
    id: int
    trabajador_id: int
    puesto_id: int
    evaluacion_id: int | None
    tipo: str
    estado: str
    motivo: str | None
    fecha_inicio: date
    fecha_fin: date | None
    actividades: list[PlanCapacitacionActividadResponse]
    creado_en: datetime
    actualizado_en: datetime


class PlanActividadDateUpdate(BaseModel):
    fecha: date


class CorrectionEnableRequest(BaseModel):
    motivo: str = Field(min_length=5, max_length=500)


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
