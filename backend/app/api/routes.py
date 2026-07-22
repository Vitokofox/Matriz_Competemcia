from datetime import UTC, timedelta

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas import (
    AsignacionLaboralCreate,
    AsignacionLaboralResponse,
    CatalogoCreate,
    CatalogoResponse,
    CatalogoUpdate,
    ChangePasswordRequest,
    CodigoCatalogoCreate,
    CodigoCatalogoResponse,
    CodigoCatalogoUpdate,
    EvaluacionCreate,
    EvaluacionResponse,
    EvaluacionUpdate,
    HistorialResponse,
    LoginRequest,
    MaquinaCreate,
    MaquinaProcesoCreate,
    MaquinaProcesoResponse,
    MaquinaResponse,
    MeResponse,
    PermisoCreate,
    PermisoResponse,
    PermisoUpdate,
    PersonaCreate,
    PersonaResponse,
    PersonaUpdate,
    ProcesoCreate,
    ProcesoResponse,
    ProcesoUpdate,
    PuestoActividadCreate,
    PuestoCreate,
    PuestoMaquinaCreate,
    PuestoResponse,
    PuestoUpdate,
    RequisitoCreate,
    RequisitoResponse,
    ResetPasswordRequest,
    RolCreate,
    RolResponse,
    RolUpdate,
    SupervisorAsignacionCreate,
    TokenResponse,
    TrabajadorCreate,
    TrabajadorPuestoCreate,
    TrabajadorRegistroCompleto,
    TrabajadorRegistroUpdate,
    TrabajadorResponse,
    TrabajadorUpdate,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
    VincularUsuarioRequest,
)
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    permissions_for,
    require_any_permission,
    verify_password,
)
from app.db.session import get_db
from app.models import (
    Actividad,
    Area,
    AsignacionLaboral,
    Cargo,
    Competencia,
    Evaluacion,
    EvaluacionDetalle,
    Evaluador,
    Maquina,
    MaquinaProceso,
    Permiso,
    Proceso,
    Puesto,
    PuestoActividad,
    PuestoActividadCompetencia,
    PuestoMaquina,
    Rol,
    Supervisor,
    Trabajador,
    TrabajadorPuesto,
    TrabajadorSupervisor,
    Turno,
    Usuario,
)
from app.services.capacitacion import obtener_trabajadores_capacitados
from app.services.codigos import generar_codigo
from app.services.importaciones import create_template, execute_import, validate_import

router = APIRouter()


@router.get("/importaciones/plantilla", tags=["importaciones"])
def download_import_template(
    user: Usuario = Depends(require_any_permission("catalogos.gestionar")),
):
    del user
    return StreamingResponse(
        iter([create_template()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="plantilla_carga_masiva.xlsx"'
        },
    )


@router.post("/importaciones/validar", tags=["importaciones"])
async def validate_import_file(
    archivo: UploadFile = File(...),
    user: Usuario = Depends(require_any_permission("catalogos.gestionar")),
    db: Session = Depends(get_db),
):
    del user
    if not archivo.filename or not archivo.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=422, detail="Debe cargar un archivo .xlsx")
    return validate_import(await archivo.read(), db)


@router.post("/importaciones/ejecutar", tags=["importaciones"])
async def execute_import_file(
    archivo: UploadFile = File(...),
    omitir_existentes: bool = Query(default=False),
    user: Usuario = Depends(require_any_permission("catalogos.gestionar")),
    db: Session = Depends(get_db),
):
    del user
    if not archivo.filename or not archivo.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=422, detail="Debe cargar un archivo .xlsx")
    try:
        result = execute_import(await archivo.read(), db, omitir_existentes)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=422, detail=f"No se pudo ejecutar la importación: {exc}"
        ) from exc
    if not result["valido"]:
        raise HTTPException(status_code=422, detail=result)
    return result


CODE_ENTITIES = {
    "trabajadores": "trabajador",
    "supervisores": "supervisor",
    "evaluadores": "evaluador",
    "competencias": "competencia",
    "maquinas": "maquina",
    "puestos": "puesto",
    "procesos": "proceso",
}


def get_or_404(db: Session, model, item_id: int):
    item = db.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    return item


def commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La operación viola una restricción o un valor único",
        ) from exc


def model_values(model, values: dict) -> dict:
    fields = set(model.__mapper__.attrs.keys())
    return {key: value for key, value in values.items() if key in fields}


def register_catalog_routes(
    model,
    prefix: str,
    create_schema,
    update_schema,
    response_schema,
    has_code: bool = False,
) -> None:
    @router.get(prefix, response_model=list[response_schema], tags=[prefix[1:]])
    def list_items(
        db: Session = Depends(get_db),
        activo: bool | None = None,
        buscar: str | None = Query(default=None, min_length=1),
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=100),
    ):
        query = db.query(model)
        if activo is not None:
            query = query.filter(model.activo == activo)
        if buscar:
            pattern = f"%{buscar}%"
            fields = [model.nombre]
            if has_code:
                fields.append(model.codigo)
            query = query.filter(or_(*[field.ilike(pattern) for field in fields]))
        return query.order_by(model.nombre).offset(skip).limit(limit).all()

    @router.get(
        f"{prefix}/{{item_id}}", response_model=response_schema, tags=[prefix[1:]]
    )
    def get_item(item_id: int, db: Session = Depends(get_db)):
        return get_or_404(db, model, item_id)

    @router.post(
        prefix,
        response_model=response_schema,
        status_code=status.HTTP_201_CREATED,
        tags=[prefix[1:]],
    )
    def create_item(payload: create_schema, db: Session = Depends(get_db)):
        values = model_values(model, payload.model_dump())
        entity = CODE_ENTITIES.get(prefix.strip("/"))
        if entity and not values.get("codigo"):
            values["codigo"] = generar_codigo(db, entity)
        item = model(**values)
        db.add(item)
        commit_or_conflict(db)
        db.refresh(item)
        return item

    @router.patch(
        f"{prefix}/{{item_id}}", response_model=response_schema, tags=[prefix[1:]]
    )
    def update_item(
        item_id: int, payload: update_schema, db: Session = Depends(get_db)
    ):
        item = get_or_404(db, model, item_id)
        for key, value in model_values(
            model, payload.model_dump(exclude_unset=True)
        ).items():
            setattr(item, key, value)
        commit_or_conflict(db)
        db.refresh(item)
        return item

    @router.delete(
        f"{prefix}/{{item_id}}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=[prefix[1:]],
    )
    def delete_item(item_id: int, db: Session = Depends(get_db)):
        item = get_or_404(db, model, item_id)
        item.activo = False
        commit_or_conflict(db)

    @router.post(
        f"{prefix}/{{item_id}}/activar",
        response_model=response_schema,
        tags=[prefix[1:]],
    )
    def activate_item(item_id: int, db: Session = Depends(get_db)):
        item = get_or_404(db, model, item_id)
        item.activo = True
        commit_or_conflict(db)
        db.refresh(item)
        return item


register_catalog_routes(
    Area, "/areas", CatalogoCreate, CatalogoUpdate, CatalogoResponse
)
register_catalog_routes(
    Cargo, "/cargos", CatalogoCreate, CatalogoUpdate, CatalogoResponse
)
register_catalog_routes(
    Turno, "/turnos", CatalogoCreate, CatalogoUpdate, CatalogoResponse
)
register_catalog_routes(
    Actividad, "/actividades", CatalogoCreate, CatalogoUpdate, CatalogoResponse
)
register_catalog_routes(
    Competencia,
    "/competencias",
    CodigoCatalogoCreate,
    CodigoCatalogoUpdate,
    CodigoCatalogoResponse,
    has_code=True,
)
register_catalog_routes(
    Maquina,
    "/maquinas",
    MaquinaCreate,
    CodigoCatalogoUpdate,
    MaquinaResponse,
    has_code=True,
)


def register_persona_routes(model, prefix: str):
    @router.get(prefix, response_model=list[PersonaResponse], tags=[prefix[1:]])
    def list_personas(db: Session = Depends(get_db), activo: bool | None = None):
        query = db.query(model)
        if activo is not None:
            query = query.filter(model.activo == activo)
        return query.order_by(model.apellidos, model.nombres).all()

    @router.get(
        f"{prefix}/{{item_id}}", response_model=PersonaResponse, tags=[prefix[1:]]
    )
    def get_persona(item_id: int, db: Session = Depends(get_db)):
        return get_or_404(db, model, item_id)

    @router.post(
        prefix, response_model=PersonaResponse, status_code=201, tags=[prefix[1:]]
    )
    def create_persona(payload: PersonaCreate, db: Session = Depends(get_db)):
        values = payload.model_dump()
        entity = CODE_ENTITIES[prefix.strip("/")]
        if not values.get("codigo"):
            values["codigo"] = generar_codigo(db, entity)
        item = model(**values)
        db.add(item)
        commit_or_conflict(db)
        db.refresh(item)
        return item

    @router.patch(
        f"{prefix}/{{item_id}}", response_model=PersonaResponse, tags=[prefix[1:]]
    )
    def update_persona(
        item_id: int, payload: PersonaUpdate, db: Session = Depends(get_db)
    ):
        item = get_or_404(db, model, item_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        commit_or_conflict(db)
        db.refresh(item)
        return item

    @router.delete(f"{prefix}/{{item_id}}", status_code=204, tags=[prefix[1:]])
    def delete_persona(item_id: int, db: Session = Depends(get_db)):
        item = get_or_404(db, model, item_id)
        item.activo = False
        commit_or_conflict(db)

    @router.post(
        f"{prefix}/{{item_id}}/activar",
        response_model=PersonaResponse,
        tags=[prefix[1:]],
    )
    def activate_persona(item_id: int, db: Session = Depends(get_db)):
        item = get_or_404(db, model, item_id)
        item.activo = True
        commit_or_conflict(db)
        db.refresh(item)
        return item


register_persona_routes(Supervisor, "/supervisores")
register_persona_routes(Evaluador, "/evaluadores")


@router.get("/procesos", response_model=list[ProcesoResponse], tags=["procesos"])
def list_procesos(
    db: Session = Depends(get_db),
    area_id: int | None = None,
    activo: bool | None = None,
):
    query = db.query(Proceso)
    if area_id is not None:
        query = query.filter(Proceso.area_id == area_id)
    if activo is not None:
        query = query.filter(Proceso.activo == activo)
    return query.order_by(Proceso.nombre).all()


@router.get("/procesos/{item_id}", response_model=ProcesoResponse, tags=["procesos"])
def get_proceso(item_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Proceso, item_id)


@router.post(
    "/procesos", response_model=ProcesoResponse, status_code=201, tags=["procesos"]
)
def create_proceso(payload: ProcesoCreate, db: Session = Depends(get_db)):
    get_or_404(db, Area, payload.area_id)
    values = payload.model_dump()
    values["codigo"] = values.get("codigo") or generar_codigo(db, "proceso")
    item = Proceso(**values)
    db.add(item)
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.patch("/procesos/{item_id}", response_model=ProcesoResponse, tags=["procesos"])
def update_proceso(item_id: int, payload: ProcesoUpdate, db: Session = Depends(get_db)):
    item = get_or_404(db, Proceso, item_id)
    values = payload.model_dump(exclude_unset=True)
    if "area_id" in values:
        get_or_404(db, Area, values["area_id"])
    for key, value in values.items():
        setattr(item, key, value)
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.delete("/procesos/{item_id}", status_code=204, tags=["procesos"])
def delete_proceso(item_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Proceso, item_id)
    item.activo = False
    commit_or_conflict(db)


@router.post(
    "/procesos/{item_id}/activar", response_model=ProcesoResponse, tags=["procesos"]
)
def activate_proceso(item_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Proceso, item_id)
    item.activo = True
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.post(
    "/maquinas/{item_id}/proceso",
    response_model=MaquinaProcesoResponse,
    status_code=201,
    tags=["procesos"],
)
def assign_machine_process(
    item_id: int, payload: MaquinaProcesoCreate, db: Session = Depends(get_db)
):
    get_or_404(db, Maquina, item_id)
    get_or_404(db, Proceso, payload.proceso_id)
    active = (
        db.query(MaquinaProceso).filter_by(maquina_id=item_id, fecha_fin=None).first()
    )
    if active:
        active.fecha_fin = payload.fecha_inicio - timedelta(days=1)
    relation = MaquinaProceso(maquina_id=item_id, **payload.model_dump())
    db.add(relation)
    commit_or_conflict(db)
    db.refresh(relation)
    return relation


@router.get("/puestos", response_model=list[PuestoResponse], tags=["puestos"])
def list_puestos(db: Session = Depends(get_db), activo: bool | None = None):
    query = db.query(Puesto)
    if activo is not None:
        query = query.filter(Puesto.activo == activo)
    return query.order_by(Puesto.nombre).all()


@router.get("/puestos/{item_id}", response_model=PuestoResponse, tags=["puestos"])
def get_puesto(item_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Puesto, item_id)


@router.post(
    "/puestos", response_model=PuestoResponse, status_code=201, tags=["puestos"]
)
def create_puesto(payload: PuestoCreate, db: Session = Depends(get_db)):
    get_or_404(db, Cargo, payload.cargo_id)
    get_or_404(db, Area, payload.area_id)
    if payload.proceso_id is not None:
        proceso = get_or_404(db, Proceso, payload.proceso_id)
        if proceso.area_id != payload.area_id:
            raise HTTPException(
                status_code=422, detail="El proceso no pertenece al área seleccionada"
            )
    if payload.maquina_id is not None:
        get_or_404(db, Maquina, payload.maquina_id)
    values = payload.model_dump()
    values["codigo"] = values.get("codigo") or generar_codigo(db, "puesto")
    item = Puesto(**values)
    db.add(item)
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.patch("/puestos/{item_id}", response_model=PuestoResponse, tags=["puestos"])
def update_puesto(item_id: int, payload: PuestoUpdate, db: Session = Depends(get_db)):
    item = get_or_404(db, Puesto, item_id)
    values = payload.model_dump(exclude_unset=True)
    if "cargo_id" in values:
        get_or_404(db, Cargo, values["cargo_id"])
    if "area_id" in values:
        get_or_404(db, Area, values["area_id"])
    if "proceso_id" in values and values["proceso_id"] is not None:
        get_or_404(db, Proceso, values["proceso_id"])
    if "maquina_id" in values and values["maquina_id"] is not None:
        get_or_404(db, Maquina, values["maquina_id"])
    for key, value in values.items():
        setattr(item, key, value)
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.delete("/puestos/{item_id}", status_code=204, tags=["puestos"])
def delete_puesto(item_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Puesto, item_id)
    item.activo = False
    commit_or_conflict(db)


@router.post(
    "/puestos/{item_id}/activar", response_model=PuestoResponse, tags=["puestos"]
)
def activate_puesto(item_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Puesto, item_id)
    item.activo = True
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.post(
    "/trabajadores",
    response_model=TrabajadorResponse,
    status_code=201,
    tags=["trabajadores"],
)
def create_trabajador(payload: TrabajadorCreate, db: Session = Depends(get_db)):
    values = payload.model_dump()
    values["codigo"] = values.get("codigo") or generar_codigo(db, "trabajador")
    item = Trabajador(**values)
    db.add(item)
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.post(
    "/trabajadores/registro-completo",
    response_model=TrabajadorResponse,
    status_code=201,
    tags=["trabajadores"],
)
def create_complete_worker(
    payload: TrabajadorRegistroCompleto, db: Session = Depends(get_db)
):
    for model, value in (
        (Cargo, payload.cargo_id),
        (Area, payload.area_id),
        (Turno, payload.turno_id),
        (Supervisor, payload.supervisor_id),
    ):
        get_or_404(db, model, value)
    positions = (
        db.query(Puesto)
        .filter(Puesto.id.in_(payload.puesto_ids), Puesto.activo.is_(True))
        .all()
    )
    if len(positions) != len(set(payload.puesto_ids)):
        raise HTTPException(
            status_code=422, detail="Uno o más puestos no existen o están inactivos"
        )
    worker = Trabajador(
        codigo=generar_codigo(db, "trabajador"),
        documento=payload.documento,
        nombres=payload.nombres,
        apellidos=payload.apellidos,
    )
    db.add(worker)
    db.flush()
    db.add(
        AsignacionLaboral(
            trabajador_id=worker.id,
            cargo_id=payload.cargo_id,
            area_id=payload.area_id,
            turno_id=payload.turno_id,
            fecha_inicio=payload.fecha_inicio,
        )
    )
    db.add(
        TrabajadorSupervisor(
            trabajador_id=worker.id,
            supervisor_id=payload.supervisor_id,
            fecha_inicio=payload.fecha_inicio,
        )
    )
    db.add_all(
        [
            TrabajadorPuesto(
                trabajador_id=worker.id,
                puesto_id=position.id,
                fecha_inicio=payload.fecha_inicio,
            )
            for position in positions
        ]
    )
    commit_or_conflict(db)
    db.refresh(worker)
    return worker


@router.patch(
    "/trabajadores/{item_id}/registro",
    response_model=TrabajadorResponse,
    tags=["trabajadores"],
)
def update_complete_worker(
    item_id: int, payload: TrabajadorRegistroUpdate, db: Session = Depends(get_db)
):
    worker = get_or_404(db, Trabajador, item_id)
    for model, value in (
        (Cargo, payload.cargo_id),
        (Area, payload.area_id),
        (Turno, payload.turno_id),
        (Supervisor, payload.supervisor_id),
    ):
        get_or_404(db, model, value)
    positions = (
        db.query(Puesto)
        .filter(Puesto.id.in_(payload.puesto_ids), Puesto.activo.is_(True))
        .all()
    )
    if len(positions) != len(set(payload.puesto_ids)):
        raise HTTPException(
            status_code=422, detail="Uno o más puestos no existen o están inactivos"
        )

    worker.documento = payload.documento
    worker.nombres = payload.nombres
    worker.apellidos = payload.apellidos
    current_labor = (
        db.query(AsignacionLaboral)
        .filter_by(trabajador_id=item_id, fecha_fin=None)
        .first()
    )
    labor_values = (payload.cargo_id, payload.area_id, payload.turno_id)
    if (
        current_labor is None
        or (current_labor.cargo_id, current_labor.area_id, current_labor.turno_id)
        != labor_values
    ):
        if current_labor:
            current_labor.fecha_fin = payload.fecha_inicio - timedelta(days=1)
        db.add(
            AsignacionLaboral(
                trabajador_id=item_id,
                cargo_id=payload.cargo_id,
                area_id=payload.area_id,
                turno_id=payload.turno_id,
                fecha_inicio=payload.fecha_inicio,
            )
        )

    current_supervisor = (
        db.query(TrabajadorSupervisor)
        .filter_by(trabajador_id=item_id, fecha_fin=None)
        .first()
    )
    if (
        current_supervisor is None
        or current_supervisor.supervisor_id != payload.supervisor_id
    ):
        if current_supervisor:
            current_supervisor.fecha_fin = payload.fecha_inicio - timedelta(days=1)
        db.add(
            TrabajadorSupervisor(
                trabajador_id=item_id,
                supervisor_id=payload.supervisor_id,
                fecha_inicio=payload.fecha_inicio,
            )
        )

    requested_positions = set(payload.puesto_ids)
    current_positions = (
        db.query(TrabajadorPuesto)
        .filter_by(trabajador_id=item_id, fecha_fin=None)
        .all()
    )
    current_ids = {assignment.puesto_id for assignment in current_positions}
    for assignment in current_positions:
        if assignment.puesto_id not in requested_positions:
            assignment.fecha_fin = payload.fecha_inicio - timedelta(days=1)
    for position in positions:
        if position.id not in current_ids:
            db.add(
                TrabajadorPuesto(
                    trabajador_id=item_id,
                    puesto_id=position.id,
                    fecha_inicio=payload.fecha_inicio,
                )
            )
    commit_or_conflict(db)
    db.refresh(worker)
    return worker


@router.get(
    "/trabajadores", response_model=list[TrabajadorResponse], tags=["trabajadores"]
)
def list_trabajadores(
    db: Session = Depends(get_db),
    activo: bool | None = None,
    buscar: str | None = None,
    area_id: int | None = None,
    supervisor_id: int | None = None,
    puesto_id: int | None = None,
):
    query = db.query(Trabajador)
    if activo is not None:
        query = query.filter(Trabajador.activo == activo)
    if buscar:
        pattern = f"%{buscar}%"
        query = query.filter(
            or_(
                Trabajador.codigo.ilike(pattern),
                Trabajador.documento.ilike(pattern),
                Trabajador.nombres.ilike(pattern),
                Trabajador.apellidos.ilike(pattern),
            )
        )
    if area_id is not None:
        query = query.join(AsignacionLaboral).filter(
            AsignacionLaboral.area_id == area_id,
            AsignacionLaboral.fecha_fin.is_(None),
        )
    if supervisor_id is not None:
        query = query.join(TrabajadorSupervisor).filter(
            TrabajadorSupervisor.supervisor_id == supervisor_id,
            TrabajadorSupervisor.fecha_fin.is_(None),
        )
    if puesto_id is not None:
        query = query.join(TrabajadorPuesto).filter(
            TrabajadorPuesto.puesto_id == puesto_id,
            TrabajadorPuesto.fecha_fin.is_(None),
        )
    return query.distinct().order_by(Trabajador.apellidos, Trabajador.nombres).all()


@router.get(
    "/trabajadores/{item_id}", response_model=TrabajadorResponse, tags=["trabajadores"]
)
def get_trabajador(item_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Trabajador, item_id)


@router.get("/trabajadores/{item_id}/detalle", tags=["trabajadores"])
def worker_detail(item_id: int, db: Session = Depends(get_db)):
    worker = get_or_404(db, Trabajador, item_id)
    labor = (
        db.query(AsignacionLaboral)
        .filter_by(trabajador_id=item_id, fecha_fin=None)
        .first()
    )
    supervisor = (
        db.query(TrabajadorSupervisor)
        .filter_by(trabajador_id=item_id, fecha_fin=None)
        .first()
    )
    positions = (
        db.query(Puesto)
        .join(TrabajadorPuesto, TrabajadorPuesto.puesto_id == Puesto.id)
        .filter(
            TrabajadorPuesto.trabajador_id == item_id,
            TrabajadorPuesto.fecha_fin.is_(None),
        )
        .all()
    )
    return {
        "trabajador": worker,
        "asignacion_laboral": labor,
        "supervisor": supervisor,
        "puestos": positions,
    }


@router.patch(
    "/trabajadores/{item_id}", response_model=TrabajadorResponse, tags=["trabajadores"]
)
def update_trabajador(
    item_id: int, payload: TrabajadorUpdate, db: Session = Depends(get_db)
):
    item = get_or_404(db, Trabajador, item_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.delete("/trabajadores/{item_id}", status_code=204, tags=["trabajadores"])
def delete_trabajador(item_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Trabajador, item_id)
    item.activo = False
    commit_or_conflict(db)


@router.post(
    "/trabajadores/{item_id}/activar",
    response_model=TrabajadorResponse,
    tags=["trabajadores"],
)
def activate_trabajador(item_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Trabajador, item_id)
    item.activo = True
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.post(
    "/trabajadores/{item_id}/asignacion-laboral",
    response_model=AsignacionLaboralResponse,
    status_code=201,
    tags=["historial"],
)
def assign_labor(
    item_id: int, payload: AsignacionLaboralCreate, db: Session = Depends(get_db)
):
    trabajador = get_or_404(db, Trabajador, item_id)
    for model, value in (
        (Cargo, payload.cargo_id),
        (Area, payload.area_id),
        (Turno, payload.turno_id),
    ):
        get_or_404(db, model, value)
    active = (
        db.query(AsignacionLaboral)
        .filter_by(trabajador_id=item_id, fecha_fin=None)
        .first()
    )
    if active:
        active.fecha_fin = payload.fecha_inicio - timedelta(days=1)
    assignment = AsignacionLaboral(trabajador_id=trabajador.id, **payload.model_dump())
    db.add(assignment)
    commit_or_conflict(db)
    db.refresh(assignment)
    return assignment


@router.post(
    "/trabajadores/{item_id}/supervisor",
    response_model=HistorialResponse,
    status_code=201,
    tags=["historial"],
)
def assign_supervisor(
    item_id: int, payload: SupervisorAsignacionCreate, db: Session = Depends(get_db)
):
    get_or_404(db, Trabajador, item_id)
    get_or_404(db, Supervisor, payload.supervisor_id)
    active = (
        db.query(TrabajadorSupervisor)
        .filter_by(trabajador_id=item_id, fecha_fin=None)
        .first()
    )
    if active:
        active.fecha_fin = payload.fecha_inicio - timedelta(days=1)
    relation = TrabajadorSupervisor(trabajador_id=item_id, **payload.model_dump())
    db.add(relation)
    commit_or_conflict(db)
    db.refresh(relation)
    return relation


@router.post(
    "/trabajadores/{item_id}/puestos",
    response_model=HistorialResponse,
    status_code=201,
    tags=["historial"],
)
def assign_position(
    item_id: int, payload: TrabajadorPuestoCreate, db: Session = Depends(get_db)
):
    get_or_404(db, Trabajador, item_id)
    get_or_404(db, Puesto, payload.puesto_id)
    relation = TrabajadorPuesto(trabajador_id=item_id, **payload.model_dump())
    db.add(relation)
    commit_or_conflict(db)
    db.refresh(relation)
    return relation


@router.get("/trabajadores/{item_id}/historial", tags=["historial"])
def worker_history(item_id: int, db: Session = Depends(get_db)):
    get_or_404(db, Trabajador, item_id)
    return {
        "asignaciones_laborales": db.query(AsignacionLaboral)
        .filter_by(trabajador_id=item_id)
        .all(),
        "supervisores": db.query(TrabajadorSupervisor)
        .filter_by(trabajador_id=item_id)
        .all(),
        "puestos": db.query(TrabajadorPuesto).filter_by(trabajador_id=item_id).all(),
    }


@router.post("/puestos/{item_id}/maquinas", status_code=201, tags=["puestos"])
def assign_machine(
    item_id: int, payload: PuestoMaquinaCreate, db: Session = Depends(get_db)
):
    get_or_404(db, Puesto, item_id)
    get_or_404(db, Maquina, payload.maquina_id)
    relation = PuestoMaquina(puesto_id=item_id, **payload.model_dump())
    db.add(relation)
    commit_or_conflict(db)
    db.refresh(relation)
    return relation


@router.post("/puestos/{item_id}/actividades", status_code=201, tags=["puestos"])
def assign_activity(
    item_id: int, payload: PuestoActividadCreate, db: Session = Depends(get_db)
):
    get_or_404(db, Puesto, item_id)
    get_or_404(db, Actividad, payload.actividad_id)
    relation = PuestoActividad(puesto_id=item_id, **payload.model_dump())
    db.add(relation)
    commit_or_conflict(db)
    db.refresh(relation)
    return relation


@router.post(
    "/puestos/{item_id}/requisitos",
    response_model=RequisitoResponse,
    status_code=201,
    tags=["puestos"],
)
def add_requirement(
    item_id: int, payload: RequisitoCreate, db: Session = Depends(get_db)
):
    puesto_activity = (
        db.query(PuestoActividad)
        .filter_by(puesto_id=item_id, actividad_id=payload.actividad_id)
        .first()
    )
    if not puesto_activity:
        raise HTTPException(
            status_code=404, detail="La actividad no está asignada al puesto"
        )
    get_or_404(db, Competencia, payload.competencia_id)
    requirement = PuestoActividadCompetencia(
        puesto_actividad_id=puesto_activity.id,
        competencia_id=payload.competencia_id,
        nivel_minimo=payload.nivel_minimo,
    )
    db.add(requirement)
    commit_or_conflict(db)
    db.refresh(requirement)
    return requirement


@router.get(
    "/puestos/{item_id}/requisitos",
    response_model=list[RequisitoResponse],
    tags=["puestos"],
)
def list_requirements(item_id: int, db: Session = Depends(get_db)):
    get_or_404(db, Puesto, item_id)
    return (
        db.query(PuestoActividadCompetencia)
        .join(PuestoActividad)
        .filter(PuestoActividad.puesto_id == item_id)
        .all()
    )


@router.get("/puestos/{item_id}/checklist", tags=["evaluaciones"])
def position_checklist(item_id: int, db: Session = Depends(get_db)):
    get_or_404(db, Puesto, item_id)
    activities = (
        db.query(PuestoActividad, Actividad)
        .join(Actividad, Actividad.id == PuestoActividad.actividad_id)
        .filter(PuestoActividad.puesto_id == item_id)
        .order_by(Actividad.nombre)
        .all()
    )
    result = []
    for assignment, activity in activities:
        requirements = (
            db.query(PuestoActividadCompetencia, Competencia)
            .join(
                Competencia, Competencia.id == PuestoActividadCompetencia.competencia_id
            )
            .filter(PuestoActividadCompetencia.puesto_actividad_id == assignment.id)
            .order_by(Competencia.nombre)
            .all()
        )
        result.append(
            {
                "actividad_id": activity.id,
                "actividad": activity.nombre,
                "competencias": [
                    {
                        "requisito_id": requirement.id,
                        "competencia_id": competency.id,
                        "competencia": competency.nombre,
                        "nivel_minimo": requirement.nivel_minimo,
                    }
                    for requirement, competency in requirements
                ],
            }
        )
    return {"puesto_id": item_id, "actividades": result}


def load_evaluation_details(db: Session, evaluation: Evaluacion, details) -> None:
    requirements = {
        item.id: item
        for item in db.query(PuestoActividadCompetencia)
        .join(PuestoActividad)
        .filter(PuestoActividad.puesto_id == evaluation.puesto_id)
        .all()
    }
    if {item.requisito_id for item in details} - requirements.keys():
        raise HTTPException(
            status_code=422, detail="Hay requisitos que no pertenecen al puesto"
        )
    if len({item.requisito_id for item in details}) != len(details):
        raise HTTPException(status_code=422, detail="No se puede repetir un requisito")
    evaluation.detalles = [
        EvaluacionDetalle(
            requisito_id=item.requisito_id,
            nivel_obtenido=item.nivel_obtenido,
            nivel_minimo=requirements[item.requisito_id].nivel_minimo,
            observaciones=item.observaciones,
        )
        for item in details
    ]


@router.post(
    "/evaluaciones",
    response_model=EvaluacionResponse,
    status_code=201,
    tags=["evaluaciones"],
)
def create_evaluation(
    payload: EvaluacionCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("evaluaciones.crear")),
):
    get_or_404(db, Trabajador, payload.trabajador_id)
    evaluator = db.query(Evaluador).filter_by(usuario_id=user.id, activo=True).first()
    supervisor = db.query(Supervisor).filter_by(usuario_id=user.id, activo=True).first()
    if bool(evaluator) == bool(supervisor):
        raise HTTPException(
            status_code=403,
            detail="El usuario debe estar vinculado a un supervisor o evaluador activo",
        )
    get_or_404(db, Puesto, payload.puesto_id)
    evaluation = Evaluacion(
        trabajador_id=payload.trabajador_id,
        puesto_id=payload.puesto_id,
        fecha=payload.fecha,
        observaciones=payload.observaciones,
        evaluador_id=evaluator.id if evaluator else None,
        supervisor_id=supervisor.id if supervisor else None,
        usuario_ejecutor_id=user.id,
    )
    load_evaluation_details(db, evaluation, payload.detalles)
    db.add(evaluation)
    commit_or_conflict(db)
    db.refresh(evaluation)
    return evaluation


@router.get(
    "/evaluaciones", response_model=list[EvaluacionResponse], tags=["evaluaciones"]
)
def list_evaluations(db: Session = Depends(get_db), trabajador_id: int | None = None):
    query = db.query(Evaluacion)
    if trabajador_id is not None:
        query = query.filter(Evaluacion.trabajador_id == trabajador_id)
    return query.order_by(Evaluacion.fecha.desc(), Evaluacion.id.desc()).all()


@router.get(
    "/evaluaciones/{item_id}", response_model=EvaluacionResponse, tags=["evaluaciones"]
)
def get_evaluation(item_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Evaluacion, item_id)


@router.patch(
    "/evaluaciones/{item_id}", response_model=EvaluacionResponse, tags=["evaluaciones"]
)
def update_evaluation(
    item_id: int, payload: EvaluacionUpdate, db: Session = Depends(get_db)
):
    evaluation = get_or_404(db, Evaluacion, item_id)
    if evaluation.estado != "borrador":
        raise HTTPException(
            status_code=409, detail="Solo se pueden editar evaluaciones borrador"
        )
    values = payload.model_dump(exclude_unset=True)
    details = values.pop("detalles", None)
    for key, value in values.items():
        setattr(evaluation, key, value)
    if details is not None:
        load_evaluation_details(db, evaluation, details)
    commit_or_conflict(db)
    db.refresh(evaluation)
    return evaluation


@router.post(
    "/evaluaciones/{item_id}/completar",
    response_model=EvaluacionResponse,
    tags=["evaluaciones"],
)
def complete_evaluation(item_id: int, db: Session = Depends(get_db)):
    evaluation = get_or_404(db, Evaluacion, item_id)
    if evaluation.estado != "borrador":
        raise HTTPException(status_code=409, detail="La evaluación no está en borrador")
    requirements = {
        item.id: item
        for item in db.query(PuestoActividadCompetencia)
        .join(PuestoActividad)
        .filter(PuestoActividad.puesto_id == evaluation.puesto_id)
        .all()
    }
    if set(requirements) != {detail.requisito_id for detail in evaluation.detalles}:
        raise HTTPException(
            status_code=422, detail="La evaluación debe cubrir todos los requisitos"
        )
    evaluation.estado = "completada"
    commit_or_conflict(db)
    db.refresh(evaluation)
    return evaluation


@router.post(
    "/evaluaciones/{item_id}/anular",
    response_model=EvaluacionResponse,
    tags=["evaluaciones"],
)
def cancel_evaluation(item_id: int, db: Session = Depends(get_db)):
    evaluation = get_or_404(db, Evaluacion, item_id)
    evaluation.estado = "anulada"
    commit_or_conflict(db)
    db.refresh(evaluation)
    return evaluation


@router.get("/puestos/{item_id}/trabajadores-capacitados", tags=["capacitacion"])
def qualified_workers(item_id: int, db: Session = Depends(get_db)):
    get_or_404(db, Puesto, item_id)
    return obtener_trabajadores_capacitados(db, item_id)


@router.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter_by(username=payload.username).first()
    if (
        user is None
        or not user.activo
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(status_code=401, detail="Usuario o contraseña inválidos")
    from datetime import datetime

    user.ultimo_acceso = datetime.now(UTC)
    db.commit()
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/auth/me", response_model=MeResponse, tags=["auth"])
def current_user(user: Usuario = Depends(get_current_user)):
    data = user.__dict__.copy()
    data["roles"] = user.roles
    data["permisos"] = sorted(permissions_for(user))
    return data


@router.post("/auth/change-password", status_code=204, tags=["auth"])
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="La contraseña actual no es válida")
    user.password_hash = hash_password(payload.new_password)
    db.commit()


@router.get("/usuarios", response_model=list[UsuarioResponse], tags=["seguridad"])
def list_users(
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("usuarios.ver", "usuarios.crear")),
):
    del user
    return db.query(Usuario).order_by(Usuario.nombre_completo).all()


@router.post(
    "/usuarios", response_model=UsuarioResponse, status_code=201, tags=["seguridad"]
)
def create_user(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("usuarios.crear")),
):
    del user
    roles = db.query(Rol).filter(Rol.id.in_(payload.rol_ids)).all()
    if len(roles) != len(set(payload.rol_ids)):
        raise HTTPException(status_code=422, detail="Uno o más roles no existen")
    item = Usuario(
        username=payload.username,
        correo=payload.correo,
        nombre_completo=payload.nombre_completo,
        password_hash=hash_password(payload.password),
        activo=payload.activo,
        roles=roles,
    )
    db.add(item)
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.post("/supervisores/{item_id}/usuario", tags=["seguridad"])
def link_supervisor_user(
    item_id: int,
    payload: VincularUsuarioRequest,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("usuarios.editar")),
):
    del user
    supervisor = get_or_404(db, Supervisor, item_id)
    account = get_or_404(db, Usuario, payload.usuario_id)
    if (
        db.query(Supervisor).filter_by(usuario_id=account.id).first()
        or db.query(Evaluador).filter_by(usuario_id=account.id).first()
    ):
        raise HTTPException(status_code=409, detail="El usuario ya está vinculado")
    supervisor.usuario_id = account.id
    commit_or_conflict(db)
    return {"supervisor_id": supervisor.id, "usuario_id": account.id}


@router.post("/evaluadores/{item_id}/usuario", tags=["seguridad"])
def link_evaluator_user(
    item_id: int,
    payload: VincularUsuarioRequest,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("usuarios.editar")),
):
    del user
    evaluator = get_or_404(db, Evaluador, item_id)
    account = get_or_404(db, Usuario, payload.usuario_id)
    if (
        db.query(Evaluador).filter_by(usuario_id=account.id).first()
        or db.query(Supervisor).filter_by(usuario_id=account.id).first()
    ):
        raise HTTPException(status_code=409, detail="El usuario ya está vinculado")
    evaluator.usuario_id = account.id
    commit_or_conflict(db)
    return {"evaluador_id": evaluator.id, "usuario_id": account.id}


@router.get("/usuarios/{item_id}", response_model=UsuarioResponse, tags=["seguridad"])
def get_user(
    item_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("usuarios.ver", "usuarios.crear")),
):
    del user
    return get_or_404(db, Usuario, item_id)


@router.patch("/usuarios/{item_id}", response_model=UsuarioResponse, tags=["seguridad"])
def update_user(
    item_id: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("usuarios.editar")),
):
    del user
    item = get_or_404(db, Usuario, item_id)
    values = payload.model_dump(exclude_unset=True)
    role_ids = values.pop("rol_ids", None)
    if role_ids is not None:
        roles = db.query(Rol).filter(Rol.id.in_(role_ids)).all()
        if len(roles) != len(set(role_ids)):
            raise HTTPException(status_code=422, detail="Uno o más roles no existen")
        item.roles = roles
    for key, value in values.items():
        setattr(item, key, value)
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.delete("/usuarios/{item_id}", status_code=204, tags=["seguridad"])
def disable_user(
    item_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("usuarios.desactivar")),
):
    if item_id == user.id:
        raise HTTPException(
            status_code=409, detail="No puede desactivar su propio usuario"
        )
    item = get_or_404(db, Usuario, item_id)
    admin_role = db.query(Rol).filter_by(nombre="Administrador", activo=True).first()
    active_admins = (
        db.query(Usuario)
        .join(Usuario.roles)
        .filter(Rol.id == admin_role.id, Usuario.activo.is_(True))
        .count()
        if admin_role
        else 0
    )
    if admin_role and admin_role in item.roles and active_admins <= 1:
        raise HTTPException(
            status_code=409,
            detail="No puede desactivar el último administrador activo",
        )
    item.activo = False
    commit_or_conflict(db)


@router.post(
    "/usuarios/{item_id}/activar", response_model=UsuarioResponse, tags=["seguridad"]
)
def activate_user(
    item_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("usuarios.editar")),
):
    del user
    item = get_or_404(db, Usuario, item_id)
    item.activo = True
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.post("/usuarios/{item_id}/reset-password", status_code=204, tags=["seguridad"])
def reset_user_password(
    item_id: int,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("usuarios.editar")),
):
    del user
    item = get_or_404(db, Usuario, item_id)
    item.password_hash = hash_password(payload.new_password)
    commit_or_conflict(db)


@router.get("/roles", response_model=list[RolResponse], tags=["seguridad"])
def list_roles(
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("roles.ver", "roles.gestionar")),
):
    del user
    return db.query(Rol).order_by(Rol.nombre).all()


@router.get("/roles/{item_id}", response_model=RolResponse, tags=["seguridad"])
def get_role(
    item_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("roles.ver", "roles.gestionar")),
):
    del user
    return get_or_404(db, Rol, item_id)


@router.post("/roles", response_model=RolResponse, status_code=201, tags=["seguridad"])
def create_role(
    payload: RolCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("roles.gestionar")),
):
    del user
    permissions = db.query(Permiso).filter(Permiso.id.in_(payload.permiso_ids)).all()
    if len(permissions) != len(set(payload.permiso_ids)):
        raise HTTPException(status_code=422, detail="Uno o más permisos no existen")
    item = Rol(
        nombre=payload.nombre,
        descripcion=payload.descripcion,
        activo=payload.activo,
        permisos=permissions,
    )
    db.add(item)
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.patch("/roles/{item_id}", response_model=RolResponse, tags=["seguridad"])
def update_role(
    item_id: int,
    payload: RolUpdate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("roles.gestionar")),
):
    del user
    item = get_or_404(db, Rol, item_id)
    values = payload.model_dump(exclude_unset=True)
    permission_ids = values.pop("permiso_ids", None)
    if permission_ids is not None:
        permissions = db.query(Permiso).filter(Permiso.id.in_(permission_ids)).all()
        if len(permissions) != len(set(permission_ids)):
            raise HTTPException(status_code=422, detail="Uno o más permisos no existen")
        item.permisos = permissions
    for key, value in values.items():
        setattr(item, key, value)
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.delete("/roles/{item_id}", status_code=204, tags=["seguridad"])
def disable_role(
    item_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("roles.gestionar")),
):
    del user
    item = get_or_404(db, Rol, item_id)
    if item.sistema:
        raise HTTPException(
            status_code=409, detail="Los roles del sistema no se pueden eliminar"
        )
    item.activo = False
    commit_or_conflict(db)


@router.post("/roles/{item_id}/activar", response_model=RolResponse, tags=["seguridad"])
def activate_role(
    item_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("roles.gestionar")),
):
    del user
    item = get_or_404(db, Rol, item_id)
    item.activo = True
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.get("/permisos", response_model=list[PermisoResponse], tags=["seguridad"])
def list_permissions(
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("permisos.gestionar", "roles.ver")),
):
    del user
    return db.query(Permiso).order_by(Permiso.modulo, Permiso.accion).all()


@router.post(
    "/permisos", response_model=PermisoResponse, status_code=201, tags=["seguridad"]
)
def create_permission(
    payload: PermisoCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("permisos.gestionar")),
):
    del user
    item = Permiso(**payload.model_dump())
    db.add(item)
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.patch("/permisos/{item_id}", response_model=PermisoResponse, tags=["seguridad"])
def update_permission(
    item_id: int,
    payload: PermisoUpdate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_any_permission("permisos.gestionar")),
):
    del user
    item = get_or_404(db, Permiso, item_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    commit_or_conflict(db)
    db.refresh(item)
    return item


@router.get("/health", tags=["health"])
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
