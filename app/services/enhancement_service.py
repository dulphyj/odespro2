import io

import numpy as np
from PIL import Image, ImageFilter


class EnhancementService:
    def enhance(self, image_bytes: bytes) -> bytes:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = self._deskew(img)
        img = self._denoise(img)
        img = self._binarize(img)
        img = self._crop_borders(img)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def _deskew(self, img: Image.Image) -> Image.Image:
        try:
            import math
            gray = img.convert("L")
            arr = np.array(gray)
            arr = 255 - arr
            coords = np.column_stack(np.where(arr > 0))
            if coords.shape[0] < 100:
                return img
            y, x = coords[:, 0], coords[:, 1]
            if len(x) < 2:
                return img
            A = np.vstack([x, np.ones(len(x))]).T
            m, _ = np.linalg.lstsq(A, y, rcond=None)[0]
            angle = math.degrees(math.atan(m))
            if abs(angle) < 0.5:
                return img
            return img.rotate(angle, expand=True, fillcolor=(255, 255, 255))
        except Exception:
            return img

    def _denoise(self, img: Image.Image) -> Image.Image:
        return img.filter(ImageFilter.MedianFilter(size=3))

    def _binarize(self, img: Image.Image) -> Image.Image:
        gray = img.convert("L")
        arr = np.array(gray)
        thresh = 128
        binary = np.where(arr > thresh, 255, 0).astype(np.uint8)
        return Image.fromarray(binary).convert("RGB")

    def _crop_borders(self, img: Image.Image, margin: int = 10) -> Image.Image:
        arr = np.array(img.convert("L"))
        mask = arr < 240
        coords = np.column_stack(np.where(mask))
        if coords.shape[0] == 0:
            return img
        y0, x0 = coords.min(axis=0)
        y1, x1 = coords.max(axis=0) + 1
        x0 = max(0, x0 - margin)
        y0 = max(0, y0 - margin)
        x1 = min(img.width, x1 + margin)
        y1 = min(img.height, y1 + margin)
        return img.crop((x0, y0, x1, y1))
