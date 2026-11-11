from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.main import app


@pytest.fixture(name="client")
def client_fixture():
    """Cliente de pruebas con una base SQLite en memoria, aislada por test."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()


# ----- helpers para armar datos de prueba -----
def crear_autor(client, nombre="Gabriel García Márquez", nacionalidad="Colombiana"):
    r = client.post("/autores", json={"nombre": nombre, "nacionalidad": nacionalidad})
    assert r.status_code == 201, r.text
    return r.json()


def crear_libro(client, isbn="978-0-00-000001-0", stock=1, titulo="Cien años de soledad", anio=1967):
    r = client.post(
        "/libros", json={"titulo": titulo, "isbn": isbn, "stock": stock, "anio": anio}
    )
    assert r.status_code == 201, r.text
    return r.json()


def crear_socio(client, email="ana@mail.com", nombre="Ana", activo=True):
    r = client.post("/socios", json={"nombre": nombre, "email": email, "activo": activo})
    assert r.status_code == 201, r.text
    return r.json()


def prestar(client, socio_id, libro_id, fecha_prestamo=None):
    body = {"socio_id": socio_id, "libro_id": libro_id}
    if fecha_prestamo:
        body["fecha_prestamo"] = fecha_prestamo.isoformat()
    return client.post("/prestamos", json=body)


@pytest.fixture
def hoy():
    return date.today()


@pytest.fixture
def hace():
    return lambda dias: date.today() - timedelta(days=dias)
