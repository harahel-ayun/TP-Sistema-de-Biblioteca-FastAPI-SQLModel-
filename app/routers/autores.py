from fastapi import APIRouter, Response, status

from app.models import Autor, AutorCreate, AutorRead, AutorUpdate
from app.routers.deps import SessionDep
from app.services import catalogo

router = APIRouter(prefix="/autores", tags=["Autores"])


@router.post("", response_model=AutorRead, status_code=status.HTTP_201_CREATED)
def crear(data: AutorCreate, session: SessionDep):
    return catalogo.crear_autor(session, data)


@router.get("", response_model=list[AutorRead])
def listar(session: SessionDep):
    return catalogo.listar_autores(session)


@router.get("/{autor_id}", response_model=AutorRead)
def obtener(autor_id: int, session: SessionDep):
    return catalogo.obtener(session, Autor, autor_id)


@router.put("/{autor_id}", response_model=AutorRead)
def actualizar(autor_id: int, data: AutorUpdate, session: SessionDep):
    return catalogo.actualizar_autor(session, autor_id, data)


@router.delete("/{autor_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(autor_id: int, session: SessionDep):
    catalogo.eliminar_autor(session, autor_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
