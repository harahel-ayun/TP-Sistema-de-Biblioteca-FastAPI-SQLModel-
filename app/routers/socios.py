from fastapi import APIRouter, Response, status

from app.models import PrestamoRead, Socio, SocioCreate, SocioRead, SocioUpdate
from app.routers.deps import SessionDep
from app.services import catalogo, prestamos

router = APIRouter(prefix="/socios", tags=["Socios"])


@router.post("", response_model=SocioRead, status_code=status.HTTP_201_CREATED)
def crear(data: SocioCreate, session: SessionDep):
    return catalogo.crear_socio(session, data)


@router.get("", response_model=list[SocioRead])
def listar(session: SessionDep):
    return catalogo.listar_socios(session)


@router.get("/{socio_id}", response_model=SocioRead)
def obtener(socio_id: int, session: SessionDep):
    return catalogo.obtener(session, Socio, socio_id)


@router.put("/{socio_id}", response_model=SocioRead)
def actualizar(socio_id: int, data: SocioUpdate, session: SessionDep):
    return catalogo.actualizar_socio(session, socio_id, data)


@router.delete("/{socio_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(socio_id: int, session: SessionDep):
    catalogo.eliminar_socio(session, socio_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{socio_id}/prestamos", response_model=list[PrestamoRead])
def prestamos_del_socio(socio_id: int, session: SessionDep, activos: bool = False):
    return prestamos.listar_prestamos_socio(session, socio_id, activos)
