from app.models.catalogos import (
    Actividad,
    Area,
    Cargo,
    Competencia,
    Maquina,
    MaquinaProceso,
    Proceso,
    Puesto,
    PuestoActividad,
    PuestoActividadCompetencia,
    PuestoMaquina,
    Turno,
)
from app.models.evaluaciones import Evaluacion, EvaluacionDetalle
from app.models.personas import (
    AsignacionLaboral,
    Evaluador,
    Supervisor,
    Trabajador,
    TrabajadorPuesto,
    TrabajadorSupervisor,
)
from app.models.secuencias import SecuenciaCodigo
from app.models.seguridad import Permiso, Rol, Usuario

__all__ = [
    "Actividad",
    "Area",
    "AsignacionLaboral",
    "Cargo",
    "Competencia",
    "Evaluacion",
    "EvaluacionDetalle",
    "Evaluador",
    "Permiso",
    "Rol",
    "SecuenciaCodigo",
    "Maquina",
    "MaquinaProceso",
    "Proceso",
    "Puesto",
    "PuestoActividad",
    "PuestoActividadCompetencia",
    "PuestoMaquina",
    "Supervisor",
    "Trabajador",
    "TrabajadorPuesto",
    "TrabajadorSupervisor",
    "Turno",
    "Usuario",
]
