import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    title: str
    total_pages: int = 1


class PageItem(BaseModel):
    id: uuid.UUID
    page_number: int
    status: str
    enh_image_path: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    doc_type: str
    original_filename: str
    total_pages: int
    created_at: datetime
    pages: list[PageItem] = []

    model_config = ConfigDict(from_attributes=True)


class DocumentList(BaseModel):
    id: uuid.UUID
    title: str
    doc_type: str
    original_filename: str
    total_pages: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
