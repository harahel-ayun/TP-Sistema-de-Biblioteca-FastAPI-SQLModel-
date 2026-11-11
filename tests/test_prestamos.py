from datetime import timedelta

from tests.conftest import crear_libro, crear_socio, prestar


def stock(client, libro_id):
    return client.get(f"/libros/{libro_id}").json()["stock"]


# ---------------- Regla 4 + 2 (caso feliz de préstamo) ----------------
def test_prestamo_feliz_descuenta_stock_y_fija_vencimiento(client, hoy):
    libro, socio = crear_libro(client, stock=2), crear_socio(client)
    r = prestar(client, socio["id"], libro["id"])
    assert r.status_code == 201
    p = r.json()
    assert p["fecha_prestamo"] == hoy.isoformat()
    assert p["fecha_vencimiento"] == (hoy + timedelta(days=14)).isoformat()  # regla 4
    assert p["fecha_devolucion"] is None and p["multa"] == 0
    assert stock(client, libro["id"]) == 1                                    # regla 2


def test_vencimiento_es_prestamo_mas_14_dias_con_fecha_explicita(client, hace):
    libro, socio = crear_libro(client), crear_socio(client)
    p = prestar(client, socio["id"], libro["id"], hace(30)).json()
    assert p["fecha_vencimiento"] == (hace(30) + timedelta(days=14)).isoformat()


def test_obtener_prestamo(client):
    libro, socio = crear_libro(client), crear_socio(client)
    p = prestar(client, socio["id"], libro["id"]).json()
    assert client.get(f"/prestamos/{p['id']}").json()["id"] == p["id"]
    assert client.get("/prestamos/999").status_code == 404


# ---------------- Regla 1: máximo 3 activos ----------------
def test_cuarto_prestamo_activo_409(client):
    socio = crear_socio(client)
    libros = [crear_libro(client, isbn=str(i), stock=1) for i in range(4)]
    for l in libros[:3]:
        assert prestar(client, socio["id"], l["id"]).status_code == 201
    assert prestar(client, socio["id"], libros[3]["id"]).status_code == 409
    assert stock(client, libros[3]["id"]) == 1  # no se descontó nada


def test_devolver_libera_cupo_de_prestamos(client):
    socio = crear_socio(client)
    libros = [crear_libro(client, isbn=str(i)) for i in range(4)]
    prestamos = [prestar(client, socio["id"], l["id"]).json() for l in libros[:3]]
    client.post(f"/prestamos/{prestamos[0]['id']}/devolucion")
    assert prestar(client, socio["id"], libros[3]["id"]).status_code == 201


def test_limite_es_por_socio(client):
    s1, s2 = crear_socio(client, email="a@a.com"), crear_socio(client, email="b@b.com")
    libros = [crear_libro(client, isbn=str(i)) for i in range(4)]
    for l in libros[:3]:
        prestar(client, s1["id"], l["id"])
    assert prestar(client, s2["id"], libros[3]["id"]).status_code == 201


# ---------------- Regla 2: sin stock ----------------
def test_sin_stock_409(client):
    libro = crear_libro(client, stock=1)
    s1, s2 = crear_socio(client, email="a@a.com"), crear_socio(client, email="b@b.com")
    assert prestar(client, s1["id"], libro["id"]).status_code == 201
    assert stock(client, libro["id"]) == 0
    assert prestar(client, s2["id"], libro["id"]).status_code == 409


# ---------------- Regla 3: socio inactivo ----------------
def test_socio_inactivo_403(client):
    libro, socio = crear_libro(client), crear_socio(client, activo=False)
    assert prestar(client, socio["id"], libro["id"]).status_code == 403
    assert stock(client, libro["id"]) == 1


# ---------------- Regla 7: inexistentes ----------------
def test_prestamo_con_socio_o_libro_inexistente_404(client):
    libro, socio = crear_libro(client), crear_socio(client)
    assert prestar(client, 999, libro["id"]).status_code == 404
    assert prestar(client, socio["id"], 999).status_code == 404


# ---------------- Regla 5: devolución ----------------
def test_devolucion_a_tiempo_repone_stock_y_multa_cero(client, hoy):
    libro, socio = crear_libro(client, stock=1), crear_socio(client)
    p = prestar(client, socio["id"], libro["id"]).json()
    r = client.post(f"/prestamos/{p['id']}/devolucion")
    assert r.status_code == 200
    assert r.json()["multa"] == 0
    assert r.json()["fecha_devolucion"] == hoy.isoformat()
    assert stock(client, libro["id"]) == 1


def test_devolucion_el_dia_del_vencimiento_sin_multa(client, hace):
    libro, socio = crear_libro(client), crear_socio(client)
    p = prestar(client, socio["id"], libro["id"], hace(14)).json()  # vence hoy
    assert client.post(f"/prestamos/{p['id']}/devolucion").json()["multa"] == 0


def test_devolucion_con_atraso_calcula_multa(client, hace):
    libro, socio = crear_libro(client), crear_socio(client)
    p = prestar(client, socio["id"], libro["id"], hace(20)).json()  # vencía hace 6 días
    r = client.post(f"/prestamos/{p['id']}/devolucion")
    assert r.status_code == 200
    assert r.json()["multa"] == 600
    assert stock(client, libro["id"]) == 1


def test_devolucion_con_fecha_explicita(client, hace):
    libro, socio = crear_libro(client), crear_socio(client)
    p = prestar(client, socio["id"], libro["id"], hace(30)).json()
    venc = hace(30) + timedelta(days=14)
    dev = venc + timedelta(days=3)
    r = client.post(
        f"/prestamos/{p['id']}/devolucion", json={"fecha_devolucion": dev.isoformat()}
    )
    assert r.json()["multa"] == 300


def test_devolucion_anterior_al_prestamo_422(client, hoy):
    libro, socio = crear_libro(client), crear_socio(client)
    p = prestar(client, socio["id"], libro["id"]).json()
    ayer = (hoy - timedelta(days=1)).isoformat()
    r = client.post(f"/prestamos/{p['id']}/devolucion", json={"fecha_devolucion": ayer})
    assert r.status_code == 422


# ---------------- Regla 6: doble devolución ----------------
def test_devolver_dos_veces_409_y_no_repone_stock_doble(client):
    libro, socio = crear_libro(client, stock=1), crear_socio(client)
    p = prestar(client, socio["id"], libro["id"]).json()
    assert client.post(f"/prestamos/{p['id']}/devolucion").status_code == 200
    assert client.post(f"/prestamos/{p['id']}/devolucion").status_code == 409
    assert stock(client, libro["id"]) == 1


def test_devolver_prestamo_inexistente_404(client):
    assert client.post("/prestamos/999/devolucion").status_code == 404


# ---------------- Listado de préstamos del socio ----------------
def test_prestamos_del_socio_activos(client):
    socio = crear_socio(client)
    l1, l2 = crear_libro(client, isbn="1"), crear_libro(client, isbn="2")
    p1 = prestar(client, socio["id"], l1["id"]).json()
    prestar(client, socio["id"], l2["id"])
    client.post(f"/prestamos/{p1['id']}/devolucion")

    todos = client.get(f"/socios/{socio['id']}/prestamos").json()
    activos = client.get(f"/socios/{socio['id']}/prestamos?activos=true").json()
    assert len(todos) == 2
    assert len(activos) == 1 and activos[0]["libro_id"] == l2["id"]


def test_prestamos_del_socio_no_incluye_los_de_otros(client):
    s1, s2 = crear_socio(client, email="a@a.com"), crear_socio(client, email="b@b.com")
    libro = crear_libro(client, stock=2)
    prestar(client, s1["id"], libro["id"])
    assert client.get(f"/socios/{s2['id']}/prestamos").json() == []


# ---------------- Listado general de préstamos ----------------
def test_listar_prestamos_vacio(client):
    assert client.get("/prestamos").json() == []


def test_listar_prestamos_todos_y_activos(client):
    s1, s2 = crear_socio(client, email="a@a.com"), crear_socio(client, email="b@b.com")
    l1, l2 = crear_libro(client, isbn="1"), crear_libro(client, isbn="2")
    p1 = prestar(client, s1["id"], l1["id"]).json()
    p2 = prestar(client, s2["id"], l2["id"]).json()
    client.post(f"/prestamos/{p1['id']}/devolucion")

    todos = client.get("/prestamos").json()
    assert len(todos) == 2

    activos = client.get("/prestamos?activos=true").json()
    assert len(activos) == 1
    assert activos[0]["id"] == p2["id"]
