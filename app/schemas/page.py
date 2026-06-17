from typing import Optional

from pydantic import BaseModel


class PaginaResponse(BaseModel):
    id: str
    documento_id: str
    numero_pagina: int
    ruta_imagen_original: str
    ruta_imagen_mejorada: Optional[str] = None
    estado: str

    class Config:
        from_attributes = True


class PaginaStatusResponse(BaseModel):
    id: str
    estado: str
    ruta_imagen_mejorada: Optional[str] = None
