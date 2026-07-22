from io import BytesIO

import pytest
from openpyxl import Workbook, load_workbook
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.session import Base
from app.models import Area
from app.services.importaciones import create_template, execute_import, validate_import


def workbook_bytes(rows: list[list[object]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "areas"
    sheet.append(["__ejemplo__", "nombre", "descripcion", "activo"])
    for row in rows:
        sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


@pytest.fixture
def db() -> Session:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_template_has_instructions_and_examples() -> None:
    workbook = load_workbook(BytesIO(create_template()), read_only=True)
    assert workbook.sheetnames[0] == "LEAME"
    assert "areas" in workbook.sheetnames
    assert list(workbook["areas"].values)[1][0] == "SI"


def test_import_updates_informed_fields_and_can_skip(db) -> None:
    first = workbook_bytes([[None, "Producción", "Inicial", True]])
    assert validate_import(first, db)["valido"]
    execute_import(first, db, skip_existing=False)
    second = workbook_bytes([[None, "Producción", "Actualizada", None]])
    execute_import(second, db, skip_existing=False)
    area = db.query(Area).one()
    assert (area.nombre, area.descripcion, area.activo) == (
        "Producción",
        "Actualizada",
        True,
    )
    execute_import(
        workbook_bytes([[None, "Producción", "No cambia", True]]),
        db,
        skip_existing=True,
    )
    assert (
        db.execute(text("SELECT descripcion FROM areas")).scalar_one()
        == "Actualizada"
    )
