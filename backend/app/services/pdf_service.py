import io
import tempfile
from pathlib import Path

import fitz


class PdfService:
    @staticmethod
    def pdf_to_images(pdf_data: bytes, dpi: int = 300) -> list[bytes]:
        images: list[bytes] = []
        pdf_stream = io.BytesIO(pdf_data)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("png")
            images.append(img_bytes)

        doc.close()
        return images

    @staticmethod
    def page_count(pdf_data: bytes) -> int:
        pdf_stream = io.BytesIO(pdf_data)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        count = len(doc)
        doc.close()
        return count
