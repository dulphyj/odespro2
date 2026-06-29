from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import DocumentoModelDB, PaginaModelDB
from app.schemas.document import DocumentoResponse
from app.shared.response import success_response, error_response
from app.services.storage_service import StorageService
from desktop.scanner_backend import ScannerBackend

router = APIRouter(prefix="/v1/scanner", tags=["Escáner"])


@router.get("/list")
def list_scanners():
    try:
        if not ScannerBackend.is_available():
            return error_response(message="No hay escáner disponible (WIA/TWAIN)")
        scanners = ScannerBackend.list_scanners()
        return success_response(data={"scanners": scanners})
    except Exception as e:
        return error_response(message=str(e), exc=e)


@router.post("/scan")
def scan_document(
    scanner_index: int = Query(0, description="Índice del escáner"),
    pages: int = Query(0, description="0=auto (alimentador ADF), N=número exacto de páginas"),
    dpi: int = Query(200, description="Resolución DPI"),
):
    try:
        if not ScannerBackend.is_available():
            return error_response(message="No hay escáner disponible (WIA/TWAIN)")
        images = ScannerBackend.scan(scanner_index=scanner_index, show_ui=pages > 0, dpi=dpi, pages=pages)
        if len(images) == 1:
            return Response(content=images[0], media_type="image/png")
        from fastapi.responses import JSONResponse
        return JSONResponse({"pages": len(images), "detail": "Múltiples páginas escaneadas, usa scan-and-upload para guardar"})
    except Exception as e:
        return error_response(message=str(e), exc=e)


@router.post("/scan-and-upload")
def scan_and_upload(
    title: str = Query("Escaneo", description="Título del documento"),
    scanner_index: int = Query(0, description="Índice del escáner"),
    pages: int = Query(0, description="0=auto (alimentador ADF), N=número exacto de páginas"),
    dpi: int = Query(200, description="Resolución DPI"),
    db: Session = Depends(get_db),
):
    try:
        if not ScannerBackend.is_available():
            return error_response(message="No hay escáner disponible (WIA/TWAIN)")

        storage = StorageService()
        images = ScannerBackend.scan(scanner_index=scanner_index, show_ui=pages > 0, dpi=dpi, pages=pages)

        doc = DocumentoModelDB(
            titulo=title,
            tipo_documento="scan",
            nombre_original=f"{title}.png",
            total_paginas=len(images),
        )
        db.add(doc)
        db.flush()

        object_names = []
        for i, img_bytes in enumerate(images):
            object_name = f"{doc.id}/page_{i+1:03d}.png"
            page = PaginaModelDB(
                documento_id=doc.id,
                numero_pagina=i + 1,
                ruta_imagen_original=object_name,
            )
            db.add(page)
            object_names.append(object_name)

        db.commit()

        for i, img_bytes in enumerate(images):
            storage.upload_image(img_bytes, object_names[i])

        db.refresh(doc)
        from sqlalchemy import select
        pages = db.execute(
            select(PaginaModelDB).where(PaginaModelDB.documento_id == doc.id)
            .order_by(PaginaModelDB.numero_pagina)
        ).scalars().all()
        doc.paginas = pages

        return success_response(data=DocumentoResponse.model_validate(doc), message="Documento escaneado")
    except Exception as e:
        return error_response(message=str(e), exc=e)
