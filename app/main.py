from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import init_db
from app.exceptions import ErrorDominio
from app.routers import autores, libros, prestamos, socios


@asynccontextmanager
async def lifespan(_: FastAPI):  # pragma: no cover
    init_db()
    yield


app = FastAPI(title="Sistema de Biblioteca", version="1.0.0", lifespan=lifespan)


@app.exception_handler(ErrorDominio)
async def manejar_error_dominio(_: Request, exc: ErrorDominio):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(autores.router)
app.include_router(libros.router)
app.include_router(socios.router)
app.include_router(prestamos.router)
