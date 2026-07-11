from __future__ import annotations

import io
from PIL import Image, ImageDraw, ImageFont


class MockScanner:

    @staticmethod
    def is_available() -> bool:
        return True

    @staticmethod
    def list_scanners() -> list[dict]:
        return [{"index": 0, "name": "Escáner de prueba (Mock)"}]

    @staticmethod
    def scan(scanner_index: int = 0, show_ui: bool = True, dpi: int = 200, pages: int = 1) -> list[bytes]:
        results = []
        for i in range(pages if pages > 0 else 1):
            img = Image.new("RGB", (2480, 3508), "white")
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except Exception:
                font = ImageFont.load_default()
            draw.text((200, 200), f"Documento de prueba - Pagina {i + 1}", fill="black", font=font)
            draw.text((200, 400), "Escaneo simulado para demostracion", fill="gray", font=font)
            draw.text((200, 600), f"DPI: {dpi} | Pagina: {i + 1} de {pages}", fill="gray", font=font)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            results.append(buf.getvalue())
        return results
