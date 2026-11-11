# Sistema de Biblioteca (FastAPI + SQLModel)

API REST para gestionar el catálogo de una biblioteca (autores, libros, socios) y sus préstamos.

## Cómo correrlo

```bash
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Documentación interactiva: http://127.0.0.1:8000/docs
- Base de datos: SQLite en `biblioteca.db` (se crea sola al iniciar). Se puede cambiar con la variable de entorno `DATABASE_URL`.

## Cómo testearlo

```bash
pytest
```

Usa una base SQLite **en memoria** (aislada por test) y muestra la cobertura (`pytest-cov`, configurado en `pytest.ini`).

## Estructura

```
app/
├── main.py            # App FastAPI, routers y manejo de errores de dominio
├── database.py        # Engine y sesión
├── exceptions.py      # NoEncontrado(404), Conflicto(409), Prohibido(403), Invalido(422)
├── models/
│   ├── tablas.py      # Autor, Libro, LibroAutor, Socio, Prestamo (table=True)
│   └── schemas.py     # Esquemas de entrada/salida
├── routers/           # Capa HTTP (finos, sin reglas de negocio)
└── services/
    ├── catalogo.py    # CRUD, unicidad de ISBN/email, asociación libro-autor
    └── prestamos.py   # Reglas de negocio de préstamos y devoluciones
tests/                 # pytest: caso feliz y de error por cada regla
```

Los servicios lanzan excepciones de dominio y `main.py` las traduce a códigos HTTP; así las reglas no dependen de FastAPI.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST/GET/GET/PUT/DELETE | `/autores`, `/libros`, `/socios` (+ `/{id}`) | CRUD |
| POST | `/libros/{id}/autores/{autor_id}` | Asocia un autor a un libro (idempotente) |
| DELETE | `/libros/{id}/autores/{autor_id}` | Quita la asociación |
| GET | `/libros?disponibles=true` | Libros con stock > 0 |
| POST | `/prestamos` | Registra un préstamo |
| GET | `/prestamos` | Lista préstamos (solo activos si `activos=true`) |
| GET | `/prestamos/{id}` | Consulta un préstamo |
| POST | `/prestamos/{id}/devolucion` | Registra la devolución |
| GET | `/socios/{id}/prestamos?activos=true` | Préstamos del socio (solo activos si `activos=true`) |

`POST /prestamos` acepta un `fecha_prestamo` opcional y `POST /prestamos/{id}/devolucion` un `fecha_devolucion` opcional (ambos por defecto "hoy"). Sirven para cargar datos históricos y para testear multas sin depender del reloj.

## Reglas de negocio → dónde se cumplen y se testean

| # | Regla | Código | Implementación | Test |
|---|---|---|---|---|
| 1 | Máx. 3 préstamos activos | 409 | `services/prestamos.py` | `test_cuarto_prestamo_activo_409` |
| 2 | Sin stock no se presta; se descuenta 1 | 409 | `services/prestamos.py` | `test_sin_stock_409`, `test_prestamo_feliz_...` |
| 3 | Socio inactivo no pide préstamos | 403 | `services/prestamos.py` | `test_socio_inactivo_403` |
| 4 | Vencimiento = préstamo + 14 días | n/a | `services/prestamos.py` | `test_prestamo_feliz_...`, `test_vencimiento_...` |
| 5 | Devolución repone stock y calcula multa ($100/día de atraso) | n/a | `services/prestamos.py` | `test_devolucion_a_tiempo_...`, `test_devolucion_con_atraso_...` |
| 6 | No se devuelve dos veces | 409 | `services/prestamos.py` | `test_devolver_dos_veces_409_...` |
| 7 | Recurso inexistente | 404 | `services/catalogo.py::obtener` | tests `*_inexistente_404` |
| 8 | ISBN o email duplicado | 409 | `services/catalogo.py` | `test_isbn_duplicado_409`, `test_email_duplicado_409` |

## Decisiones de diseño

- Orden de validación al prestar: 404 (socio/libro) → 403 (inactivo) → 409 (límite) → 409 (stock).
- Eliminar un libro o socio con préstamos registrados devuelve 409 para no dejar préstamos huérfanos.
- Stock negativo se rechaza con 422 (validación de esquema).
- Una devolución con fecha anterior al préstamo devuelve 422.
- No se implementó la etapa opcional de roles (`bibliotecario` / `socio`).
