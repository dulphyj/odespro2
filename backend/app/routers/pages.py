import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Page
from app.schemas import PageResponse, PageStatus
from app.services import MinioService

router = APIRouter(prefix="/api/v1/pages", tags=["pages"])


def minio_service():
    return MinioService()


@router.get("/{page_id}", response_model=PageResponse)
async def get_page(page_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(404, "Page not found")
    return page


@router.get("/{page_id}/status", response_model=PageStatus)
async def get_page_status(page_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(404, "Page not found")
    return PageStatus(
        id=page.id,
        status=page.status,
        enh_image_path=page.enh_image_path,
    )


@router.get("/{page_id}/image")
async def get_page_image(
    page_id: uuid.UUID,
    type: str = "original",
    db: AsyncSession = Depends(get_db),
    minio_svc: MinioService = Depends(minio_service),
):
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(404, "Page not found")

    object_name = page.enh_image_path if type == "enhanced" and page.enh_image_path else page.orig_image_path
    if not object_name:
        raise HTTPException(404, "Image not found")

    data = minio_svc.get_image(object_name)
    if not data:
        raise HTTPException(404, "Image not found in storage")

    return Response(content=data, media_type="image/png")


@router.post("/{page_id}/enhance", response_model=PageStatus)
async def enhance_page(
    page_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    from app.tasks.enhance_task import enqueue_enhance_page

    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(404, "Page not found")

    page.status = "processing"
    await db.commit()
    await enqueue_enhance_page(str(page.id))
    return PageStatus(id=page.id, status="processing", enh_image_path=None)
