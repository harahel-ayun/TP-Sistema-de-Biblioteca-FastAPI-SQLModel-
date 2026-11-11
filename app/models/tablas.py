"""Modelos de tablas (SQLModel, table=True)."""
from datetime import date
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class LibroAutor(SQLModel, table=True):
    """Tabla intermedia Libro N-N Autor."""

    libro_id: int = Field(foreign_key="libro.id", primary_key=True)
    autor_id: int = Field(foreign_key="autor.id", primary_key=True)


class Autor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    nacionalidad: Optional[str] = None

    libros: list["Libro"] = Relationship(back_populates="autores", link_model=LibroAutor)


class Libro(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str
    isbn: str = Field(unique=True, index=True)
    stock: int = Field(default=0, ge=0)
    anio: Optional[int] = None

    autores: list[Autor] = Relationship(back_populates="libros", link_model=LibroAutor)


class Socio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str = Field(unique=True, index=True)
    activo: bool = True


class Prestamo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    socio_id: int = Field(foreign_key="socio.id", index=True)
    libro_id: int = Field(foreign_key="libro.id", index=True)
    fecha_prestamo: date
    fecha_vencimiento: date
    fecha_devolucion: Optional[date] = None
    multa: int = 0
