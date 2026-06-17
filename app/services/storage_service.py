import os

from app.config.settings import STORAGE_DIR


class StorageService:
    def __init__(self):
        os.makedirs(STORAGE_DIR, exist_ok=True)

    def _path(self, object_name: str) -> str:
        full = os.path.join(STORAGE_DIR, object_name)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        return full

    def upload_image(self, image_data: bytes, object_name: str, content_type: str = "image/png") -> str:
        path = self._path(object_name)
        with open(path, "wb") as f:
            f.write(image_data)
        return object_name

    def get_image(self, object_name: str) -> bytes | None:
        path = self._path(object_name)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return f.read()

    def delete_object(self, object_name: str):
        path = self._path(object_name)
        if os.path.exists(path):
            os.remove(path)
