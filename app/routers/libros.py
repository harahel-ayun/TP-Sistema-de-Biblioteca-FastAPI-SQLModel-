from fastapi import APIRouter, Response, status

from app.models import Libro, LibroCreate, LibroRead, LibroUpdate
from app.routers.deps import SessionDep
from app.services import catalogo

router = APIRouter(prefix="/libros", tags=["Libros"])


@router.post("", response_model=LibroRead, status_code=status.HTTP_201_CREATED)
def crear(data: LibroCreate, session: SessionDep):
    return catalogo.crear_libro(session, data)


@router.get("", response_model=list[LibroRead])
def listar(session: SessionDep, disponibles: bool = False):
    return catalogo.listar_libros(session, disponibles)


@router.get("/{libro_id}", response_model=LibroRead)
def obtener(libro_id: int, session: SessionDep):
    return catalogo.obtener(session, Libro, libro_id)


@router.put("/{libro_id}", response_model=LibroRead)
def actualizar(libro_id: int, data: LibroUpdate, session: SessionDep):
    return catalogo.actualizar_libro(session, libro_id, data)


@router.delete("/{libro_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(libro_id: int, session: SessionDep):
    catalogo.eliminar_libro(session, libro_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{libro_id}/autores/{autor_id}", response_model=LibroRead)
def asociar_autor(libro_id: int, autor_id: int, session: SessionDep):
    return catalogo.asociar_autor(session, libro_id, autor_id)


@router.delete("/{libro_id}/autores/{autor_id}", response_model=LibroRead)
def desasociar_autor(libro_id: int, autor_id: int, session: SessionDep):
    return catalogo.desasociar_autor(session, libro_id, autor_id)
