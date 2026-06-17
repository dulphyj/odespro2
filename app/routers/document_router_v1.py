from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import DocumentoModelDB, PaginaModelDB
from app.schemas.document import DocumentoResponse
from app.shared.response import success_response, error_response
from app.services.storage_service import StorageService
from app.services.pdf_service import PdfService

router = APIRouter(prefix="/v1/documents", tags=["Documentos"])


@router.get("/")
def list_documents(db: Session = Depends(get_db)):
    try:
        docs = db.execute(
            select(DocumentoModelDB).order_by(DocumentoModelDB.fecha_creacion.desc())
        ).scalars().all()
        return success_response(data=[DocumentoResponse.model_validate(d) for d in docs])
    except Exception as e:
        return error_response(message=str(e), exc=e)


@router.get("/{doc_id}")
def get_document(doc_id: str, db: Session = Depends(get_db)):
    try:
        doc = db.execute(
            select(DocumentoModelDB).where(DocumentoModelDB.id == doc_id)
        ).scalar_one_or_none()
        if not doc:
            return error_response(message="Documento no encontrado")
        pages = db.execute(
            select(PaginaModelDB).where(
                PaginaModelDB.documento_id == doc_id
            ).order_by(PaginaModelDB.numero_pagina)
        ).scalars().all()
        doc.paginas = pages
        return success_response(data=DocumentoResponse.model_validate(doc))
    except Exception as e:
        return error_response(message=str(e), exc=e)


@router.post("/upload-image")
def upload_image(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        storage = StorageService()
        contents = file.file.read()
        doc = DocumentoModelDB(
            titulo=title,
            tipo_documento="image",
            nombre_original=file.filename or "untitled",
            total_paginas=1,
        )
        db.add(doc)
        db.flush()
        object_name = f"{doc.id}/page_001.png"
        page = PaginaModelDB(
            documento_id=doc.id,
            numero_pagina=1,
            ruta_imagen_original=object_name,
        )
        db.add(page)
        db.commit()
        storage.upload_image(contents, object_name)
        db.refresh(doc)
        pages = db.execute(
            select(PaginaModelDB).where(
                PaginaModelDB.documento_id == doc.id
            ).order_by(PaginaModelDB.numero_pagina)
        ).scalars().all()
        doc.paginas = pages
        return success_response(data=DocumentoResponse.model_validate(doc), message="Imagen subida")
    except Exception as e:
        return error_response(message=str(e), exc=e)


@router.post("/upload-pdf")
def upload_pdf(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        storage = StorageService()
        contents = file.file.read()
        images = PdfService.pdf_to_images(contents)
        doc = DocumentoModelDB(
            titulo=title,
            tipo_documento="pdf",
            nombre_original=file.filename or "untitled",
            total_paginas=len(images),
        )
        db.add(doc)
        db.flush()
        object_names = []
        for i in range(len(images)):
            object_name = f"{doc.id}/page_{i+1:03d}.png"
            page = PaginaModelDB(
                documento_id=doc.id,
                numero_pagina=i+1,
                ruta_imagen_original=object_name,
            )
            db.add(page)
            object_names.append(object_name)
        db.commit()
        for i, img_bytes in enumerate(images):
            storage.upload_image(img_bytes, object_names[i])
        db.refresh(doc)
        pages = db.execute(
            select(PaginaModelDB).where(
                PaginaModelDB.documento_id == doc.id
            ).order_by(PaginaModelDB.numero_pagina)
        ).scalars().all()
        doc.paginas = pages
        return success_response(data=DocumentoResponse.model_validate(doc), message="PDF subido")
    except Exception as e:
        return error_response(message=str(e), exc=e)


@router.post("/{doc_id}/enhance-all")
def enhance_all_pages(doc_id: str, db: Session = Depends(get_db)):
    try:
        from app.services.enhancement_service import EnhancementService

        storage = StorageService()
        enhancer = EnhancementService()

        pages = db.execute(
            select(PaginaModelDB).where(PaginaModelDB.documento_id == doc_id)
        ).scalars().all()
        if not pages:
            return error_response(message="No se encontraron páginas")

        for p in pages:
            orig_data = storage.get_image(p.ruta_imagen_original)
            if not orig_data:
                continue
            enhanced_bytes = enhancer.enhance(orig_data)
            enh_name = f"{doc_id}/enhanced/page_{p.numero_pagina:03d}.png"
            storage.upload_image(enhanced_bytes, enh_name)
            p.ruta_imagen_mejorada = enh_name
            p.estado = "completed"

        db.commit()
        return success_response(message=f"Imágenes mejoradas: {len(pages)} páginas")
    except Exception as e:
        return error_response(message=str(e), exc=e)
