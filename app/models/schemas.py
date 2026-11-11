"""Esquemas de entrada/salida de la API (validación con Pydantic)."""
from datetime import date
from typing import Annotated, Optional

from pydantic import StringConstraints
from sqlmodel import Field, SQLModel

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
Email = Annotated[str, StringConstraints(pattern=EMAIL_REGEX)]


# ---- Autor ----
class AutorCreate(SQLModel):
    nombre: str = Field(min_length=1)
    nacionalidad: Optional[str] = None


class AutorUpdate(SQLModel):
    nombre: Optional[str] = Field(default=None, min_length=1)
    nacionalidad: Optional[str] = None


class AutorRead(SQLModel):
    id: int
    nombre: str
    nacionalidad: Optional[str] = None


# ---- Libro ----
class LibroCreate(SQLModel):
    titulo: str = Field(min_length=1)
    isbn: str = Field(min_length=1)
    stock: int = Field(default=0, ge=0)
    anio: Optional[int] = None


class LibroUpdate(SQLModel):
    titulo: Optional[str] = Field(default=None, min_length=1)
    isbn: Optional[str] = Field(default=None, min_length=1)
    stock: Optional[int] = Field(default=None, ge=0)
    anio: Optional[int] = None


class LibroRead(SQLModel):
    id: int
    titulo: str
    isbn: str
    stock: int
    anio: Optional[int] = None
    autores: list[AutorRead] = []


# ---- Socio ----
class SocioCreate(SQLModel):
    nombre: str = Field(min_length=1, schema_extra={"examples": ["Juan Pérez"]})
    email: Email = Field(schema_extra={"examples": ["nombre@email.com"]})
    activo: bool = True
class SocioUpdate(SQLModel):
    nombre: Optional[str] = Field(default=None, min_length=1)
    email: Optional[Email] = None
    activo: Optional[bool] = None


class SocioRead(SQLModel):
    id: int
    nombre: str
    email: str
    activo: bool


# ---- Préstamo ----
class PrestamoCreate(SQLModel):
    socio_id: int
    libro_id: int
    # Opcional: por defecto es hoy. Permite cargar préstamos históricos y testear multas.
    fecha_prestamo: Optional[date] = None


class DevolucionCreate(SQLModel):
    # Opcional: por defecto es hoy.
    fecha_devolucion: Optional[date] = None


class PrestamoRead(SQLModel):
    id: int
    socio_id: int
    libro_id: int
    fecha_prestamo: date
    fecha_vencimiento: date
    fecha_devolucion: Optional[date] = None
    multa: int
