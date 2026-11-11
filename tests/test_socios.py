from tests.conftest import crear_libro, crear_socio, prestar


def test_crud_socio(client):
    socio = crear_socio(client)
    assert socio["activo"] is True
    assert client.get(f"/socios/{socio['id']}").json()["email"] == "ana@mail.com"
    assert len(client.get("/socios").json()) == 1

    r = client.put(f"/socios/{socio['id']}", json={"activo": False})
    assert r.status_code == 200 and r.json()["activo"] is False

    assert client.delete(f"/socios/{socio['id']}").status_code == 204
    assert client.get(f"/socios/{socio['id']}").status_code == 404


def test_socio_inexistente_404(client):
    assert client.get("/socios/999").status_code == 404
    assert client.put("/socios/999", json={"nombre": "X"}).status_code == 404
    assert client.delete("/socios/999").status_code == 404
    assert client.get("/socios/999/prestamos").status_code == 404


# Regla 8
def test_email_duplicado_409(client):
    crear_socio(client, email="a@a.com")
    r = client.post("/socios", json={"nombre": "Otro", "email": "a@a.com"})
    assert r.status_code == 409


def test_actualizar_email_a_uno_existente_409(client):
    crear_socio(client, email="a@a.com")
    otro = crear_socio(client, email="b@b.com")
    assert client.put(f"/socios/{otro['id']}", json={"email": "a@a.com"}).status_code == 409


def test_actualizar_email_propio_ok(client):
    socio = crear_socio(client, email="a@a.com")
    r = client.put(f"/socios/{socio['id']}", json={"email": "a@a.com", "nombre": "Nuevo"})
    assert r.status_code == 200


def test_email_invalido_422(client):
    r = client.post("/socios", json={"nombre": "X", "email": "no-es-email"})
    assert r.status_code == 422


def test_no_se_elimina_socio_con_prestamos_409(client):
    libro, socio = crear_libro(client), crear_socio(client)
    prestar(client, socio["id"], libro["id"])
    assert client.delete(f"/socios/{socio['id']}").status_code == 409
