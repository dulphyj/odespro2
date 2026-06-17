import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import DocumentoModelDB, PaginaModelDB
from app.schemas.document import DocumentoResponse
from app.shared.response import success_response, error_response
from app.services.storage_service import StorageService
from app.services.pdf_service import PdfService

router = APIRouter(prefix="/v1/documents", tags=["Documentos"])


def storage_service():
    return StorageService()


@router.get("/")
async def list_documents(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(DocumentoModelDB).order_by(DocumentoModelDB.fecha_creacion.desc())
        )
        docs = result.scalars().all()
        return success_response(data=[DocumentoResponse.model_validate(d) for d in docs])
    except Exception as e:
        return error_response(message=str(e), exc=e)


@router.get("/{doc_id}")
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(DocumentoModelDB).where(DocumentoModelDB.id == doc_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            return error_response(message="Documento no encontrado")
        pages_result = await db.execute(
            select(PaginaModelDB).where(
                PaginaModelDB.documento_id == doc_id
            ).order_by(PaginaModelDB.numero_pagina)
        )
        doc.paginas = pages_result.scalars().all()
        return success_response(data=DocumentoResponse.model_validate(doc))
    except Exception as e:
        return error_response(message=str(e), exc=e)


@router.post("/upload-image")
async def upload_image(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(storage_service),
):
    try:
        contents = await file.read()
        doc = DocumentoModelDB(
            titulo=title,
            tipo_documento="image",
            nombre_original=file.filename or "untitled",
            total_paginas=1,
        )
        db.add(doc)
        await db.flush()
        object_name = f"{doc.id}/page_001.png"
        storage.upload_image(contents, object_name)
        page = PaginaModelDB(
            documento_id=doc.id,
            numero_pagina=1,
            ruta_imagen_original=object_name,
        )
        db.add(page)
        await db.commit()
        await db.refresh(doc)
        pages_result = await db.execute(
            select(PaginaModelDB).where(
                PaginaModelDB.documento_id == doc.id
            ).order_by(PaginaModelDB.numero_pagina)
        )
        doc.paginas = pages_result.scalars().all()
        return success_response(data=DocumentoResponse.model_validate(doc), message="Imagen subida")
    except Exception as e:
        return error_response(message=str(e), exc=e)


@router.post("/upload-pdf")
async def upload_pdf(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(storage_service),
):
    try:
        contents = await file.read()
        images = PdfService.pdf_to_images(contents)
        doc = DocumentoModelDB(
            titulo=title,
            tipo_documento="pdf",
            nombre_original=file.filename or "untitled",
            total_paginas=len(images),
        )
        db.add(doc)
        await db.flush()
        for i, img_bytes in enumerate(images, start=1):
            object_name = f"{doc.id}/page_{i:03d}.png"
            storage.upload_image(img_bytes, object_name)
            page = PaginaModelDB(
                documento_id=doc.id,
                numero_pagina=i,
                ruta_imagen_original=object_name,
            )
            db.add(page)
        await db.commit()
        await db.refresh(doc)
        pages_result = await db.execute(
            select(PaginaModelDB).where(
                PaginaModelDB.documento_id == doc.id
            ).order_by(PaginaModelDB.numero_pagina)
        )
        doc.paginas = pages_result.scalars().all()
        return success_response(data=DocumentoResponse.model_validate(doc), message="PDF subido")
    except Exception as e:
        return error_response(message=str(e), exc=e)


@router.post("/{doc_id}/enhance-all")
async def enhance_all_pages(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(storage_service),
):
    try:
        from app.services.enhancement_service import EnhancementService

        result = await db.execute(
            select(PaginaModelDB).where(PaginaModelDB.documento_id == doc_id)
        )
        pages = result.scalars().all()
        if not pages:
            return error_response(message="No se encontraron páginas")

        svc = EnhancementService()
        for page in pages:
            orig_data = storage.get_image(page.ruta_imagen_original)
            if not orig_data:
                continue
            enhanced_bytes = svc.enhance(orig_data)
            enh_object_name = f"{doc_id}/enhanced/page_{page.numero_pagina:03d}.png"
            storage.upload_image(enhanced_bytes, enh_object_name)
            page.ruta_imagen_mejorada = enh_object_name
            page.estado = "completed"

        await db.commit()
        return success_response(message=f"Imágenes mejoradas: {len(pages)} páginas")
    except Exception as e:
        return error_response(message=str(e), exc=e)
