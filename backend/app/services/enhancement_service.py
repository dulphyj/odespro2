import cv2
import numpy as np
import pytesseract
from PIL import Image
import io


class EnhancementService:
    def __init__(self, lang: str = "spa"):
        self.lang = lang

    def enhance(self, image_bytes: bytes, do_overlay: bool = False) -> tuple[bytes, str, str | None]:
        img_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        processed = self._deskew(img)
        processed = self._denoise(processed)
        processed = self._binarize(processed)
        processed = self._crop_borders(processed)

        ocr_text = self._ocr(processed)

        if do_overlay:
            processed = self._clean_to_text_page(processed, ocr_text)

        _, buffer = cv2.imencode(".png", processed)
        return buffer.tobytes(), ocr_text, None

    def _deskew(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.bitwise_not(gray)
        coords = cv2.findNonZero(gray)
        if coords is None:
            return img
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) < 0.5:
            return img
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(
            img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )

    def _denoise(self, img: np.ndarray) -> np.ndarray:
        return cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

    def _binarize(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

    def _crop_borders(self, img: np.ndarray, margin: int = 10) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        coords = cv2.findNonZero(thresh)
        if coords is None:
            return img
        x, y, w, h = cv2.boundingRect(coords)
        x = max(0, x - margin)
        y = max(0, y - margin)
        w = min(img.shape[1] - x, w + 2 * margin)
        h = min(img.shape[0] - y, h + 2 * margin)
        return img[y : y + h, x : x + w]

    def _ocr(self, img: np.ndarray) -> str:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        return pytesseract.image_to_string(pil_img, lang=self.lang)

    def _clean_to_text_page(self, img: np.ndarray, text: str) -> np.ndarray:
        h, w = img.shape[:2]
        white = np.full((h, w, 3), 255, dtype=np.uint8)
        return white
