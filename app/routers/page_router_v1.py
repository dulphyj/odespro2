from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import PaginaModelDB
from app.schemas.page import PaginaResponse, PaginaStatusResponse
from app.shared.response import success_response, error_response
from app.services.storage_service import StorageService
from app.services.enhancement_service import EnhancementService

router = APIRouter(prefix="/v1/pages", tags=["Páginas"])


@router.get("/{page_id}")
def get_page(page_id: str, db: Session = Depends(get_db)):
    try:
        page = db.execute(select(PaginaModelDB).where(PaginaModelDB.id == page_id)).scalar_one_or_none()
        if not page:
            return error_response(message="Página no encontrada")
        return success_response(data=PaginaResponse.model_validate(page))
    except Exception as e:
        return error_response(message=str(e), exc=e)


@router.get("/{page_id}/status")
def get_page_status(page_id: str, db: Session = Depends(get_db)):
    try:
        page = db.execute(select(PaginaModelDB).where(PaginaModelDB.id == page_id)).scalar_one_or_none()
        if not page:
            return error_response(message="Página no encontrada")
        return success_response(data=PaginaStatusResponse(
            id=page.id,
            estado=page.estado,
            ruta_imagen_mejorada=page.ruta_imagen_mejorada,
        ))
    except Exception as e:
        return error_response(message=str(e), exc=e)


@router.get("/{page_id}/image")
def get_page_image(
    page_id: str,
    type: str = "original",
    db: Session = Depends(get_db),
):
    try:
        storage = StorageService()
        page = db.execute(select(PaginaModelDB).where(PaginaModelDB.id == page_id)).scalar_one_or_none()
        if not page:
            return error_response(message="Página no encontrada")
        object_name = page.ruta_imagen_mejorada if type == "enhanced" and page.ruta_imagen_mejorada else page.ruta_imagen_original
        if not object_name:
            return error_response(message="Imagen no encontrada")
        data = storage.get_image(object_name)
        if not data:
            return error_response(message="Imagen no encontrada")
        return Response(content=data, media_type="image/png")
    except Exception as e:
        return error_response(message=str(e), exc=e)


@router.post("/{page_id}/enhance")
def enhance_page(page_id: str, db: Session = Depends(get_db)):
    try:
        storage = StorageService()
        enhancer = EnhancementService()

        page = db.execute(select(PaginaModelDB).where(PaginaModelDB.id == page_id)).scalar_one_or_none()
        if not page:
            return error_response(message="Página no encontrada")

        orig_data = storage.get_image(page.ruta_imagen_original)
        if not orig_data:
            return error_response(message="Imagen original no encontrada")

        enhanced_bytes = enhancer.enhance(orig_data)
        enh_name = f"{page.documento_id}/enhanced/page_{page.numero_pagina:03d}.png"
        storage.upload_image(enhanced_bytes, enh_name)
        page.ruta_imagen_mejorada = enh_name
        page.estado = "completed"
        db.commit()

        return success_response(data=PaginaStatusResponse(
            id=page.id, estado="completed", ruta_imagen_mejorada=enh_name,
        ), message="Imagen mejorada")
    except Exception as e:
        return error_response(message=str(e), exc=e)
