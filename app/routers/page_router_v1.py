import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import PaginaModelDB
from app.schemas.page import PaginaResponse, PaginaStatusResponse
from app.shared.response import success_response, error_response
from app.services.minio_service import MinioService
from app.services.enhancement_service import EnhancementService

router = APIRouter(prefix="/v1/pages", tags=["Páginas"])


def minio_service():
    return MinioService()


@router.get("/{page_id}")
async def get_page(page_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(PaginaModelDB).where(PaginaModelDB.id == page_id))
        page = result.scalar_one_or_none()
        if not page:
            return error_response(message="Página no encontrada")
        return success_response(data=PaginaResponse.model_validate(page))
    except Exception as e:
        return error_response(message=str(e), exc=e)


@router.get("/{page_id}/status")
async def get_page_status(page_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(PaginaModelDB).where(PaginaModelDB.id == page_id))
        page = result.scalar_one_or_none()
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
async def get_page_image(
    page_id: str,
    type: str = "original",
    db: AsyncSession = Depends(get_db),
    minio_svc: MinioService = Depends(minio_service),
):
    try:
        result = await db.execute(select(PaginaModelDB).where(PaginaModelDB.id == page_id))
        page = result.scalar_one_or_none()
        if not page:
            return error_response(message="Página no encontrada")
        object_name = page.ruta_imagen_mejorada if type == "enhanced" and page.ruta_imagen_mejorada else page.ruta_imagen_original
        if not object_name:
            return error_response(message="Imagen no encontrada")
        data = minio_svc.get_image(object_name)
        if not data:
            return error_response(message="Imagen no encontrada en almacenamiento")
        return Response(content=data, media_type="image/png")
    except Exception as e:
        return error_response(message=str(e), exc=e)


@router.post("/{page_id}/enhance")
async def enhance_page(
    page_id: str,
    db: AsyncSession = Depends(get_db),
    minio_svc: MinioService = Depends(minio_service),
):
    try:
        result = await db.execute(select(PaginaModelDB).where(PaginaModelDB.id == page_id))
        page = result.scalar_one_or_none()
        if not page:
            return error_response(message="Página no encontrada")
        orig_data = minio_svc.get_image(page.ruta_imagen_original)
        if not orig_data:
            return error_response(message="Imagen original no encontrada")
        svc = EnhancementService()
        enhanced_bytes = svc.enhance(orig_data)
        enh_object_name = f"{page.documento_id}/enhanced/page_{page.numero_pagina:03d}.png"
        minio_svc.upload_image(enhanced_bytes, enh_object_name)
        page.ruta_imagen_mejorada = enh_object_name
        page.estado = "completed"
        await db.commit()
        return success_response(data=PaginaStatusResponse(
            id=page.id,
            estado="completed",
            ruta_imagen_mejorada=enh_object_name,
        ), message="Imagen mejorada")
    except Exception as e:
        return error_response(message=str(e), exc=e)
