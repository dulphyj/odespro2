import io

from PIL import Image, ImageEnhance


class ImageEditService:

    @staticmethod
    def scale(img: Image.Image, factor: float) -> Image.Image:
        if factor <= 0:
            return img
        new_size = (max(1, int(img.width * factor)), max(1, int(img.height * factor)))
        return img.resize(new_size, Image.LANCZOS)

    @staticmethod
    def rotate(img: Image.Image, angle: float) -> Image.Image:
        return img.rotate(angle, expand=True, fillcolor=(255, 255, 255))

    @staticmethod
    def brightness(img: Image.Image, factor: float) -> Image.Image:
        return ImageEnhance.Brightness(img).enhance(factor)

    @staticmethod
    def contrast(img: Image.Image, factor: float) -> Image.Image:
        return ImageEnhance.Contrast(img).enhance(factor)

    @staticmethod
    def apply_all(img: Image.Image, *, scale: float = None, rotate: float = None, brightness: float = None, contrast: float = None) -> bytes:
        if scale:
            img = ImageEditService.scale(img, scale)
        if rotate:
            img = ImageEditService.rotate(img, rotate)
        if brightness:
            img = ImageEditService.brightness(img, brightness)
        if contrast:
            img = ImageEditService.contrast(img, contrast)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
