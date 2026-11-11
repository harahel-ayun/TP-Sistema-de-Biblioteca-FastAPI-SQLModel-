from typing import Optional

from fastapi import APIRouter, status

from app.models import DevolucionCreate, Prestamo, PrestamoCreate, PrestamoRead
from app.routers.deps import SessionDep
from app.services import catalogo, prestamos

router = APIRouter(prefix="/prestamos", tags=["Préstamos"])


@router.post("", response_model=PrestamoRead, status_code=status.HTTP_201_CREATED)
def crear(data: PrestamoCreate, session: SessionDep):
    return prestamos.registrar_prestamo(session, data)


@router.get("", response_model=list[PrestamoRead])
def listar(session: SessionDep, activos: bool = False):
    return prestamos.listar_prestamos(session, activos)


@router.get("/{prestamo_id}", response_model=PrestamoRead)
def obtener(prestamo_id: int, session: SessionDep):
    return catalogo.obtener(session, Prestamo, prestamo_id)


@router.post("/{prestamo_id}/devolucion", response_model=PrestamoRead)
def devolver(
    prestamo_id: int, session: SessionDep, data: Optional[DevolucionCreate] = None
):
    fecha = data.fecha_devolucion if data else None
    return prestamos.registrar_devolucion(session, prestamo_id, fecha)
