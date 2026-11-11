from tests.conftest import crear_autor, crear_libro, crear_socio, prestar


def test_crud_libro(client):
    libro = crear_libro(client)
    assert client.get(f"/libros/{libro['id']}").json()["isbn"] == libro["isbn"]
    assert len(client.get("/libros").json()) == 1

    r = client.put(f"/libros/{libro['id']}", json={"stock": 5})
    assert r.status_code == 200 and r.json()["stock"] == 5

    assert client.delete(f"/libros/{libro['id']}").status_code == 204
    assert client.get(f"/libros/{libro['id']}").status_code == 404


def test_libro_inexistente_404(client):
    assert client.get("/libros/999").status_code == 404
    assert client.put("/libros/999", json={"stock": 1}).status_code == 404
    assert client.delete("/libros/999").status_code == 404


# Regla 8
def test_isbn_duplicado_409(client):
    crear_libro(client, isbn="111")
    r = client.post("/libros", json={"titulo": "Otro", "isbn": "111", "stock": 1})
    assert r.status_code == 409


def test_actualizar_isbn_a_uno_existente_409(client):
    crear_libro(client, isbn="111")
    otro = crear_libro(client, isbn="222")
    assert client.put(f"/libros/{otro['id']}", json={"isbn": "111"}).status_code == 409


def test_actualizar_isbn_propio_ok(client):
    libro = crear_libro(client, isbn="111")
    r = client.put(f"/libros/{libro['id']}", json={"isbn": "111", "titulo": "Nuevo"})
    assert r.status_code == 200


def test_stock_negativo_422(client):
    r = client.post("/libros", json={"titulo": "X", "isbn": "1", "stock": -1})
    assert r.status_code == 422
    libro = crear_libro(client, isbn="2")
    assert client.put(f"/libros/{libro['id']}", json={"stock": -5}).status_code == 422


def test_filtro_disponibles(client):
    crear_libro(client, isbn="1", stock=2)
    crear_libro(client, isbn="2", stock=0)
    todos = client.get("/libros").json()
    disponibles = client.get("/libros?disponibles=true").json()
    assert len(todos) == 2
    assert [l["isbn"] for l in disponibles] == ["1"]


def test_asociar_autor_y_respuesta_con_autores(client):
    libro, autor = crear_libro(client), crear_autor(client)
    r = client.post(f"/libros/{libro['id']}/autores/{autor['id']}")
    assert r.status_code == 200
    assert [a["id"] for a in r.json()["autores"]] == [autor["id"]]
    # el GET también incluye los autores
    assert client.get(f"/libros/{libro['id']}").json()["autores"][0]["nombre"] == autor["nombre"]
    # el listado también
    assert client.get("/libros").json()[0]["autores"][0]["id"] == autor["id"]


def test_asociar_autor_es_idempotente(client):
    libro, autor = crear_libro(client), crear_autor(client)
    client.post(f"/libros/{libro['id']}/autores/{autor['id']}")
    r = client.post(f"/libros/{libro['id']}/autores/{autor['id']}")
    assert r.status_code == 200 and len(r.json()["autores"]) == 1


def test_libro_con_varios_autores(client):
    libro = crear_libro(client)
    a1, a2 = crear_autor(client, "Autor Uno"), crear_autor(client, "Autor Dos")
    client.post(f"/libros/{libro['id']}/autores/{a1['id']}")
    r = client.post(f"/libros/{libro['id']}/autores/{a2['id']}")
    assert len(r.json()["autores"]) == 2


def test_un_autor_en_varios_libros(client):
    autor = crear_autor(client)
    l1, l2 = crear_libro(client, isbn="1"), crear_libro(client, isbn="2")
    client.post(f"/libros/{l1['id']}/autores/{autor['id']}")
    client.post(f"/libros/{l2['id']}/autores/{autor['id']}")
    assert all(len(l["autores"]) == 1 for l in client.get("/libros").json())


def test_asociar_con_ids_inexistentes_404(client):
    libro, autor = crear_libro(client), crear_autor(client)
    assert client.post(f"/libros/999/autores/{autor['id']}").status_code == 404
    assert client.post(f"/libros/{libro['id']}/autores/999").status_code == 404


def test_desasociar_autor(client):
    libro, autor = crear_libro(client), crear_autor(client)
    client.post(f"/libros/{libro['id']}/autores/{autor['id']}")
    r = client.delete(f"/libros/{libro['id']}/autores/{autor['id']}")
    assert r.status_code == 200 and r.json()["autores"] == []
    # desasociar algo no asociado no rompe
    assert client.delete(f"/libros/{libro['id']}/autores/{autor['id']}").status_code == 200


def test_eliminar_autor_asociado_limpia_relacion(client):
    libro, autor = crear_libro(client), crear_autor(client)
    client.post(f"/libros/{libro['id']}/autores/{autor['id']}")
    assert client.delete(f"/autores/{autor['id']}").status_code == 204
    assert client.get(f"/libros/{libro['id']}").json()["autores"] == []


def test_no_se_elimina_libro_con_prestamos_409(client):
    libro, socio = crear_libro(client), crear_socio(client)
    assert prestar(client, socio["id"], libro["id"]).status_code == 201
    assert client.delete(f"/libros/{libro['id']}").status_code == 409
