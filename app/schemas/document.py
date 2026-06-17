from typing import List
from datetime import datetime

from pydantic import BaseModel

from app.schemas.page import PaginaResponse


class DocumentoRequest(BaseModel):
    titulo: str
    tipo_documento: str = "image"
    nombre_original: str = ""


class DocumentoResponse(BaseModel):
    id: str
    titulo: str
    tipo_documento: str
    nombre_original: str
    total_paginas: int
    fecha_creacion: datetime
    paginas: List[PaginaResponse] = []

    class Config:
        from_attributes = True
