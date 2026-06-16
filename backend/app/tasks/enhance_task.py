import uuid

from arq.connections import create_pool, RedisSettings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import async_session
from app.models import Page
from app.services import MinioService, EnhancementService

settings = get_settings()


async def enqueue_enhance_page(page_id: str):
    pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    try:
        await pool.enqueue_job("process_enhance_page", page_id)
    finally:
        await pool.close()


async def process_enhance_page(ctx: dict, page_id: str):
    minio_svc = MinioService()
    enhancer = EnhancementService(lang=settings.tesseract_lang)

    async with async_session() as db:
        result = await db.execute(
            select(Page).where(Page.id == uuid.UUID(page_id))
        )
        page = result.scalar_one_or_none()
        if not page:
            return

        try:
            image_data = minio_svc.get_image(page.orig_image_path)
            if not image_data:
                page.status = "failed"
                await db.commit()
                return

            enhanced_bytes, ocr_text, _ = enhancer.enhance(image_data, do_overlay=False)

            enh_object_name = f"{page.document_id}/enh_page_{page.page_number:03d}.png"
            minio_svc.upload_image(enhanced_bytes, enh_object_name)
            page.enh_image_path = enh_object_name
            page.ocr_text = ocr_text
            page.status = "completed"
        except Exception:
            page.status = "failed"

        await db.commit()
