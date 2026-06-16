import uuid

from pydantic import BaseModel, ConfigDict


class PageResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    page_number: int
    status: str
    orig_image_path: str | None = None
    enh_image_path: str | None = None
    ocr_text: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PageStatus(BaseModel):
    id: uuid.UUID
    status: str
    enh_image_path: str | None = None
