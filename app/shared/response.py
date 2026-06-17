from typing import Any, Optional

from pydantic import BaseModel


class GenericResponse(BaseModel):
    status: str
    message: str
    data: Optional[Any] = None


def success_response(data: Any = None, message: str = "Operación exitosa") -> GenericResponse:
    return GenericResponse(status="SUCCESS", message=message, data=data)


def error_response(message: str = "Error", data: Any = None, exc: Optional[Exception] = None) -> GenericResponse:
    return GenericResponse(status="ERROR", message=message, data=data)
