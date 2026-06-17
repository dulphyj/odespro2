from typing import Optional
from datetime import datetime

from pydantic import BaseModel


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
    paginas: list[dict] = []

    class Config:
        from_attributes = True
