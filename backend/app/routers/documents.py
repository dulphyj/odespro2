import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Document, Page
from app.schemas import DocumentResponse, DocumentList, PageResponse
from app.services import MinioService, PdfService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def minio_service():
    return MinioService()


@router.get("", response_model=list[DocumentList])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).order_by(Document.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).where(Document.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    pages_result = await db.execute(
        select(Page).where(Page.document_id == doc_id).order_by(Page.page_number)
    )
    doc.pages = pages_result.scalars().all()
    return doc


@router.post("/upload-image", response_model=DocumentResponse)
async def upload_image(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    minio_svc: MinioService = Depends(minio_service),
):
    contents = await file.read()
    doc = Document(
        title=title,
        doc_type="image",
        original_filename=file.filename or "untitled",
        total_pages=1,
    )
    db.add(doc)
    await db.flush()

    object_name = f"{doc.id}/page_001.png"
    minio_svc.upload_image(contents, object_name)
    page = Page(
        document_id=doc.id,
        page_number=1,
        orig_image_path=object_name,
    )
    db.add(page)
    await db.commit()
    await db.refresh(doc)

    pages_result = await db.execute(
        select(Page).where(Page.document_id == doc.id).order_by(Page.page_number)
    )
    doc.pages = pages_result.scalars().all()
    return doc


@router.post("/upload-pdf", response_model=DocumentResponse)
async def upload_pdf(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    minio_svc: MinioService = Depends(minio_service),
):
    contents = await file.read()

    images = PdfService.pdf_to_images(contents)
    doc = Document(
        title=title,
        doc_type="pdf",
        original_filename=file.filename or "untitled",
        total_pages=len(images),
    )
    db.add(doc)
    await db.flush()

    pages = []
    for i, img_bytes in enumerate(images, start=1):
        object_name = f"{doc.id}/page_{i:03d}.png"
        minio_svc.upload_image(img_bytes, object_name)

        page = Page(
            document_id=doc.id,
            page_number=i,
            orig_image_path=object_name,
        )
        db.add(page)
        pages.append(page)

    await db.commit()
    await db.refresh(doc)
    doc.pages = pages
    return doc


@router.post("/{doc_id}/enhance-all")
async def enhance_all_pages(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    from app.tasks.enhance_task import enqueue_enhance_page

    result = await db.execute(
        select(Page).where(Page.document_id == doc_id, Page.status == "pending")
    )
    pages = result.scalars().all()
    if not pages:
        raise HTTPException(400, "No pending pages to enhance")

    for page in pages:
        page.status = "processing"
        await enqueue_enhance_page(str(page.id))

    await db.commit()
    return {"message": f"Enqueued {len(pages)} pages for enhancement"}
