from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.session import Base
from app.models import (
    Actividad,
    Area,
    Cargo,
    Competencia,
    Evaluacion,
    EvaluacionDetalle,
    Evaluador,
    Puesto,
    PuestoActividad,
    PuestoActividadCompetencia,
    Supervisor,
    Trabajador,
    TrabajadorSupervisor,
)
from app.services.capacitacion import obtener_trabajadores_capacitados


@pytest.fixture
def db() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)


def test_esquema_contiene_todas_las_tablas() -> None:
    assert len(Base.metadata.tables) == 26
    assert {
        "trabajadores",
        "supervisores",
        "evaluadores",
        "puestos",
        "maquinas",
        "actividades",
        "competencias",
        "evaluaciones",
        "evaluacion_detalles",
    }.issubset(Base.metadata.tables)


def test_un_trabajador_solo_tiene_un_supervisor_activo(db: Session) -> None:
    trabajador = Trabajador(
        codigo="T-001",
        documento="1001",
        nombres="Ana",
        apellidos="Perez",
    )
    supervisor_a = Supervisor(
        codigo="S-001",
        documento="2001",
        nombres="Luis",
        apellidos="Diaz",
    )
    supervisor_b = Supervisor(
        codigo="S-002",
        documento="2002",
        nombres="Maria",
        apellidos="Leon",
    )
    db.add_all([trabajador, supervisor_a, supervisor_b])
    db.flush()
    db.add(
        TrabajadorSupervisor(
            trabajador_id=trabajador.id,
            supervisor_id=supervisor_a.id,
            fecha_inicio=date(2026, 1, 1),
        )
    )
    db.commit()

    db.add(
        TrabajadorSupervisor(
            trabajador_id=trabajador.id,
            supervisor_id=supervisor_b.id,
            fecha_inicio=date(2026, 2, 1),
        )
    )

    with pytest.raises(IntegrityError):
        db.commit()


def test_nivel_aprobado_se_calcula_con_la_nota_minima() -> None:
    assert EvaluacionDetalle(nivel_obtenido=3, nivel_minimo=3).aprobado
    assert not EvaluacionDetalle(nivel_obtenido=2, nivel_minimo=3).aprobado


def test_consulta_diferencia_expertis_por_puesto(db: Session) -> None:
    area = Area(nombre="Produccion")
    cargo_operador = Cargo(nombre="Operador")
    cargo_ayudante = Cargo(nombre="Ayudante")
    actividad = Actividad(nombre="Cargar material")
    competencia = Competencia(codigo="SEG-01", nombre="Operacion segura")
    evaluador = Evaluador(
        codigo="E-001",
        documento="3001",
        nombres="Eva",
        apellidos="Lopez",
    )
    trabajador = Trabajador(
        codigo="T-001",
        documento="1001",
        nombres="Carlos",
        apellidos="Rojas",
    )
    puesto_operador = Puesto(
        codigo="PX-OP",
        nombre="Operador Maquina X",
        cargo=cargo_operador,
        area=area,
    )
    puesto_ayudante = Puesto(
        codigo="PX-AY",
        nombre="Ayudante Maquina X",
        cargo=cargo_ayudante,
        area=area,
    )
    operador_actividad = PuestoActividad(
        puesto=puesto_operador,
        actividad=actividad,
    )
    ayudante_actividad = PuestoActividad(
        puesto=puesto_ayudante,
        actividad=actividad,
    )
    requisito_operador = PuestoActividadCompetencia(
        puesto_actividad=operador_actividad,
        competencia=competencia,
        nivel_minimo=4,
    )
    requisito_ayudante = PuestoActividadCompetencia(
        puesto_actividad=ayudante_actividad,
        competencia=competencia,
        nivel_minimo=3,
    )
    db.add_all(
        [
            evaluador,
            trabajador,
            requisito_operador,
            requisito_ayudante,
        ]
    )
    db.flush()
    db.add_all(
        [
            Evaluacion(
                trabajador_id=trabajador.id,
                evaluador_id=evaluador.id,
                puesto_id=puesto_operador.id,
                fecha=date(2026, 7, 1),
                estado="completada",
                detalles=[
                    EvaluacionDetalle(
                        requisito_id=requisito_operador.id,
                        nivel_obtenido=3,
                        nivel_minimo=4,
                    )
                ],
            ),
            Evaluacion(
                trabajador_id=trabajador.id,
                evaluador_id=evaluador.id,
                puesto_id=puesto_ayudante.id,
                fecha=date(2026, 7, 1),
                estado="completada",
                detalles=[
                    EvaluacionDetalle(
                        requisito_id=requisito_ayudante.id,
                        nivel_obtenido=3,
                        nivel_minimo=3,
                    )
                ],
            ),
        ]
    )
    db.commit()

    assert obtener_trabajadores_capacitados(db, puesto_operador.id) == []
    assert obtener_trabajadores_capacitados(db, puesto_ayudante.id) == [trabajador]
