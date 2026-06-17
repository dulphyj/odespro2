import io
import re

import numpy as np
from PIL import Image


class OcrService:
    _reader = None

    @classmethod
    def _get_reader(cls):
        if cls._reader is None:
            import easyocr
            cls._reader = easyocr.Reader(["es", "en"], gpu=False)
        return cls._reader

    @classmethod
    def _clean(cls, text: str) -> str:
        return re.sub(r"[^\w\sáéíóúñüÁÉÍÓÚÑÜ.,;:!¿?¡()\-]", " ", text).strip()

    @classmethod
    def extract_text(cls, image_bytes: bytes) -> str:
        reader = cls._get_reader()
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        arr = np.array(img)
        result = reader.readtext(arr, paragraph=True)
        return "\n\n".join([cls._clean(r[1]) for r in result])
