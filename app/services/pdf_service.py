import fitz


class PdfService:
    @staticmethod
    def pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> list[bytes]:
        images = []
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=dpi)
            img_bytes = pix.tobytes("png")
            images.append(img_bytes)
        doc.close()
        return images
