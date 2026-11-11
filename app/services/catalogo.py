"""Lógica del catálogo: autores, libros y socios."""
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.exceptions import Conflicto, NoEncontrado
from app.models import (
    Autor, AutorCreate, AutorUpdate,
    Libro, LibroCreate, LibroUpdate,
    Prestamo, Socio, SocioCreate, SocioUpdate,
)


def obtener(session: Session, modelo, id_: int):
    """Devuelve el registro o lanza 404 (regla 7)."""
    obj = session.get(modelo, id_)
    if obj is None:
        raise NoEncontrado(f"{modelo.__name__} {id_} no existe")
    return obj


def _guardar(session: Session, obj, mensaje_conflicto: str):
    session.add(obj)
    try:
        session.commit()
    except IntegrityError:  # pragma: no cover
        session.rollback()
        raise Conflicto(mensaje_conflicto)
    session.refresh(obj)
    return obj


# ------------------------------ Autores ------------------------------
def crear_autor(session: Session, data: AutorCreate) -> Autor:
    return _guardar(session, Autor.model_validate(data), "Autor duplicado")


def listar_autores(session: Session) -> list[Autor]:
    return list(session.exec(select(Autor)).all())


def actualizar_autor(session: Session, autor_id: int, data: AutorUpdate) -> Autor:
    autor = obtener(session, Autor, autor_id)
    autor.sqlmodel_update(data.model_dump(exclude_unset=True))
    return _guardar(session, autor, "Autor duplicado")


def eliminar_autor(session: Session, autor_id: int) -> None:
    autor = obtener(session, Autor, autor_id)
    session.delete(autor)  # SQLAlchemy borra también las filas de LibroAutor
    session.commit()


# ------------------------------- Libros -------------------------------
def _isbn_en_uso(session: Session, isbn: str, excepto_id: Optional[int] = None) -> bool:
    existente = session.exec(select(Libro).where(Libro.isbn == isbn)).first()
    return existente is not None and existente.id != excepto_id


def crear_libro(session: Session, data: LibroCreate) -> Libro:
    if _isbn_en_uso(session, data.isbn):
        raise Conflicto(f"Ya existe un libro con ISBN {data.isbn}")  # regla 8
    return _guardar(session, Libro.model_validate(data), "ISBN duplicado")


def listar_libros(session: Session, disponibles: bool = False) -> list[Libro]:
    consulta = select(Libro)
    if disponibles:
        consulta = consulta.where(Libro.stock > 0)
    return list(session.exec(consulta).all())


def actualizar_libro(session: Session, libro_id: int, data: LibroUpdate) -> Libro:
    libro = obtener(session, Libro, libro_id)
    cambios = data.model_dump(exclude_unset=True)
    if "isbn" in cambios and _isbn_en_uso(session, cambios["isbn"], excepto_id=libro.id):
        raise Conflicto(f"Ya existe un libro con ISBN {cambios['isbn']}")
    libro.sqlmodel_update(cambios)
    return _guardar(session, libro, "ISBN duplicado")


def eliminar_libro(session: Session, libro_id: int) -> None:
    libro = obtener(session, Libro, libro_id)
    if session.exec(select(Prestamo).where(Prestamo.libro_id == libro_id)).first():
        raise Conflicto("No se puede eliminar un libro con préstamos registrados")
    session.delete(libro)
    session.commit()


def asociar_autor(session: Session, libro_id: int, autor_id: int) -> Libro:
    """Asocia un autor a un libro (idempotente)."""
    libro = obtener(session, Libro, libro_id)
    autor = obtener(session, Autor, autor_id)
    if autor not in libro.autores:
        libro.autores.append(autor)
        session.add(libro)
        session.commit()
        session.refresh(libro)
    return libro


def desasociar_autor(session: Session, libro_id: int, autor_id: int) -> Libro:
    libro = obtener(session, Libro, libro_id)
    autor = obtener(session, Autor, autor_id)
    if autor in libro.autores:
        libro.autores.remove(autor)
        session.add(libro)
        session.commit()
        session.refresh(libro)
    return libro


# -------------------------------- Socios --------------------------------
def _email_en_uso(session: Session, email: str, excepto_id: Optional[int] = None) -> bool:
    existente = session.exec(select(Socio).where(Socio.email == email)).first()
    return existente is not None and existente.id != excepto_id


def crear_socio(session: Session, data: SocioCreate) -> Socio:
    if _email_en_uso(session, data.email):
        raise Conflicto(f"Ya existe un socio con email {data.email}")  # regla 8
    return _guardar(session, Socio.model_validate(data), "Email duplicado")


def listar_socios(session: Session) -> list[Socio]:
    return list(session.exec(select(Socio)).all())


def actualizar_socio(session: Session, socio_id: int, data: SocioUpdate) -> Socio:
    socio = obtener(session, Socio, socio_id)
    cambios = data.model_dump(exclude_unset=True)
    if "email" in cambios and _email_en_uso(session, cambios["email"], excepto_id=socio.id):
        raise Conflicto(f"Ya existe un socio con email {cambios['email']}")
    socio.sqlmodel_update(cambios)
    return _guardar(session, socio, "Email duplicado")


def eliminar_socio(session: Session, socio_id: int) -> None:
    socio = obtener(session, Socio, socio_id)
    if session.exec(select(Prestamo).where(Prestamo.socio_id == socio_id)).first():
        raise Conflicto("No se puede eliminar un socio con préstamos registrados")
    session.delete(socio)
    session.commit()
