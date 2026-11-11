from tests.conftest import crear_autor


def test_crud_autor(client):
    autor = crear_autor(client)
    assert client.get(f"/autores/{autor['id']}").json()["nombre"] == autor["nombre"]
    assert len(client.get("/autores").json()) == 1

    r = client.put(f"/autores/{autor['id']}", json={"nacionalidad": "Argentina"})
    assert r.status_code == 200
    assert r.json()["nacionalidad"] == "Argentina"
    assert r.json()["nombre"] == autor["nombre"]  # no se pisa lo que no se envió

    assert client.delete(f"/autores/{autor['id']}").status_code == 204
    assert client.get(f"/autores/{autor['id']}").status_code == 404


def test_autor_inexistente_404(client):
    assert client.get("/autores/999").status_code == 404
    assert client.put("/autores/999", json={"nombre": "X"}).status_code == 404
    assert client.delete("/autores/999").status_code == 404


def test_autor_nombre_vacio_422(client):
    assert client.post("/autores", json={"nombre": ""}).status_code == 422
