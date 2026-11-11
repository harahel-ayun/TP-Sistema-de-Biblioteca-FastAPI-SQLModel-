"""Errores de dominio. Los servicios los lanzan y main.py los traduce a HTTP."""


class ErrorDominio(Exception):
    status_code = 400

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class NoEncontrado(ErrorDominio):
    status_code = 404


class Conflicto(ErrorDominio):
    status_code = 409


class Prohibido(ErrorDominio):
    status_code = 403


class Invalido(ErrorDominio):
    status_code = 422
