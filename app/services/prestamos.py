"""Reglas de negocio de préstamos y devoluciones."""
from datetime import date, timedelta
from typing import Optional

from sqlmodel import Session, select

from app.exceptions import Conflicto, Invalido, Prohibido
from app.models import Libro, Prestamo, PrestamoCreate, Socio
from app.services.catalogo import obtener

PLAZO_DIAS = 14
MAX_PRESTAMOS_ACTIVOS = 3
MULTA_POR_DIA = 100


def contar_activos(session: Session, socio_id: int) -> int:
    activos = session.exec(
        select(Prestamo).where(
            Prestamo.socio_id == socio_id, Prestamo.fecha_devolucion == None  # noqa: E711
        )
    ).all()
    return len(activos)


def registrar_prestamo(session: Session, data: PrestamoCreate) -> Prestamo:
    socio = obtener(session, Socio, data.socio_id)   # 404
    libro = obtener(session, Libro, data.libro_id)   # 404

    if not socio.activo:                                              # regla 3
        raise Prohibido("El socio está inactivo y no puede pedir préstamos")
    if contar_activos(session, socio.id) >= MAX_PRESTAMOS_ACTIVOS:    # regla 1
        raise Conflicto(f"El socio ya tiene {MAX_PRESTAMOS_ACTIVOS} préstamos activos")
    if libro.stock <= 0:                                              # regla 2
        raise Conflicto("No hay stock disponible de este libro")

    fecha = data.fecha_prestamo or date.today()
    prestamo = Prestamo(
        socio_id=socio.id,
        libro_id=libro.id,
        fecha_prestamo=fecha,
        fecha_vencimiento=fecha + timedelta(days=PLAZO_DIAS),         # regla 4
    )
    libro.stock -= 1                                                  # regla 2
    session.add(prestamo)
    session.add(libro)
    session.commit()  # una sola transacción: préstamo + descuento de stock
    session.refresh(prestamo)
    return prestamo


def calcular_multa(fecha_vencimiento: date, fecha_devolucion: date) -> int:
    dias_atraso = max(0, (fecha_devolucion - fecha_vencimiento).days)
    return MULTA_POR_DIA * dias_atraso


def registrar_devolucion(
    session: Session, prestamo_id: int, fecha_devolucion: Optional[date] = None
) -> Prestamo:
    prestamo = obtener(session, Prestamo, prestamo_id)                # 404
    if prestamo.fecha_devolucion is not None:                         # regla 6
        raise Conflicto("El préstamo ya fue devuelto")

    fecha = fecha_devolucion or date.today()
    if fecha < prestamo.fecha_prestamo:
        raise Invalido("La fecha de devolución no puede ser anterior al préstamo")

    prestamo.fecha_devolucion = fecha
    prestamo.multa = calcular_multa(prestamo.fecha_vencimiento, fecha)  # regla 5
    libro = obtener(session, Libro, prestamo.libro_id)
    libro.stock += 1                                                  # regla 5
    session.add(prestamo)
    session.add(libro)
    session.commit()
    session.refresh(prestamo)
    return prestamo


def listar_prestamos(
    session: Session, activos: bool = False
) -> list[Prestamo]:
    consulta = select(Prestamo)
    if activos:
        consulta = consulta.where(Prestamo.fecha_devolucion == None)  # noqa: E711
    return list(session.exec(consulta).all())


def listar_prestamos_socio(
    session: Session, socio_id: int, activos: bool = False
) -> list[Prestamo]:
    obtener(session, Socio, socio_id)  # 404 si el socio no existe
    consulta = select(Prestamo).where(Prestamo.socio_id == socio_id)
    if activos:
        consulta = consulta.where(Prestamo.fecha_devolucion == None)  # noqa: E711
    return list(session.exec(consulta).all())
