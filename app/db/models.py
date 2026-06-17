from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class DocumentoModelDB(Base):
    __tablename__ = "documento"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    titulo = Column(String(255), nullable=False)
    tipo_documento = Column(String(10), nullable=False)
    nombre_original = Column(String(255), nullable=False)
    total_paginas = Column(Integer, default=0, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    paginas = relationship("PaginaModelDB", back_populates="documento", cascade="all, delete-orphan")


class PaginaModelDB(Base):
    __tablename__ = "pagina"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    documento_id = Column(String(36), ForeignKey("documento.id"), nullable=False)
    numero_pagina = Column(Integer, nullable=False)
    ruta_imagen_original = Column(Text, nullable=False)
    ruta_imagen_mejorada = Column(Text, nullable=True)
    estado = Column(String(20), default="pending", nullable=False)

    documento = relationship("DocumentoModelDB", back_populates="paginas")
