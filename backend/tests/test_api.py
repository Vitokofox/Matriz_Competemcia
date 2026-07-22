from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.security import hash_password
from app.db.session import Base, get_db
from app.main import app
from app.models import Permiso, Rol, Usuario


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        permission = Permiso(
            codigo="usuarios.ver",
            nombre="Ver usuarios",
            modulo="usuarios",
            accion="ver",
        )
        role = Rol(nombre="Administrador", sistema=True, permisos=[permission])
        session.add(
            Usuario(
                username="admin",
                correo="admin@test.local",
                nombre_completo="Admin Test",
                password_hash=hash_password("Secret123!"),
                roles=[role],
            )
        )
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def test_crud_area(client: TestClient) -> None:
    created = client.post(
        "/api/areas",
        json={"nombre": "Producción", "descripcion": "Área operativa"},
    )
    assert created.status_code == 201
    area_id = created.json()["id"]

    listed = client.get("/api/areas", params={"buscar": "produ"})
    assert listed.status_code == 200
    assert listed.json()[0]["nombre"] == "Producción"

    updated = client.patch(f"/api/areas/{area_id}", json={"activo": False})
    assert updated.status_code == 200
    assert updated.json()["activo"] is False

    deleted = client.delete(f"/api/areas/{area_id}")
    assert deleted.status_code == 204


def test_crud_trabajador_y_asignacion_laboral(client: TestClient) -> None:
    area = client.post("/api/areas", json={"nombre": "Producción"}).json()
    cargo = client.post("/api/cargos", json={"nombre": "Operador"}).json()
    turno = client.post("/api/turnos", json={"nombre": "Turno 1"}).json()
    worker = client.post(
        "/api/trabajadores",
        json={
            "codigo": "T-001",
            "documento": "1001",
            "nombres": "Ana",
            "apellidos": "Pérez",
        },
    ).json()

    assignment = client.post(
        f"/api/trabajadores/{worker['id']}/asignacion-laboral",
        json={
            "cargo_id": cargo["id"],
            "area_id": area["id"],
            "turno_id": turno["id"],
            "fecha_inicio": "2026-01-01",
        },
    )
    assert assignment.status_code == 201
    assert assignment.json()["trabajador_id"] == worker["id"]


def test_puesto_requiere_cargo_y_area(client: TestClient) -> None:
    response = client.post(
        "/api/puestos",
        json={
            "codigo": "PX-OP",
            "nombre": "Operador Máquina X",
            "cargo_id": 999,
            "area_id": 999,
        },
    )
    assert response.status_code == 404


def test_login_carga_permisos_del_usuario(client: TestClient) -> None:
    login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Secret123!"},
    )
    assert login.status_code == 200

    me = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["permisos"] == ["usuarios.ver"]


def test_codigo_de_trabajador_se_genera_automaticamente(client: TestClient) -> None:
    response = client.post(
        "/api/trabajadores",
        json={
            "documento": "1002",
            "nombres": "Luis",
            "apellidos": "Gómez",
        },
    )
    assert response.status_code == 201
    assert response.json()["codigo"] == "TRB-0001"


def test_registro_completo_asigna_supervisor_y_puestos(client: TestClient) -> None:
    area = client.post("/api/areas", json={"nombre": "Producción"}).json()
    cargo = client.post("/api/cargos", json={"nombre": "Operador"}).json()
    shift = client.post("/api/turnos", json={"nombre": "Turno 1"}).json()
    supervisor = client.post(
        "/api/supervisores",
        json={"documento": "SUP-1", "nombres": "Ana", "apellidos": "Supervisora"},
    ).json()
    position = client.post(
        "/api/puestos",
        json={
            "nombre": "Operador Línea 1",
            "cargo_id": cargo["id"],
            "area_id": area["id"],
        },
    ).json()

    response = client.post(
        "/api/trabajadores/registro-completo",
        json={
            "documento": "17041213",
            "nombres": "Guillermo",
            "apellidos": "Flores Aguilera",
            "cargo_id": cargo["id"],
            "area_id": area["id"],
            "turno_id": shift["id"],
            "supervisor_id": supervisor["id"],
            "puesto_ids": [position["id"]],
            "fecha_inicio": "2026-07-22",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["codigo"] == "TRB-0001"

    detail = client.get(f"/api/trabajadores/{response.json()['id']}/detalle")
    assert detail.status_code == 200
    assert detail.json()["supervisor"]["supervisor_id"] == supervisor["id"]
    assert [item["id"] for item in detail.json()["puestos"]] == [position["id"]]

    filtered = client.get(
        f"/api/trabajadores?area_id={area['id']}&supervisor_id={supervisor['id']}&puesto_id={position['id']}"
    )
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
