import io

from minio import Minio
from minio.error import S3Error

from app.config.settings import get_minio_config


class MinioService:
    def __init__(self):
        cfg = get_minio_config()
        self.client = Minio(
            f"{cfg['host']}:{cfg['port']}",
            access_key=cfg["access_key"],
            secret_key=cfg["secret_key"],
            secure=False,
        )
        self.bucket = cfg["bucket"]
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload_image(self, image_data: bytes, object_name: str, content_type: str = "image/png") -> str:
        size = len(image_data)
        self.client.put_object(
            self.bucket,
            object_name,
            io.BytesIO(image_data),
            size,
            content_type=content_type,
        )
        return object_name

    def get_image(self, object_name: str) -> bytes | None:
        try:
            response = self.client.get_object(self.bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error:
            return None

    def delete_object(self, object_name: str):
        try:
            self.client.remove_object(self.bucket, object_name)
        except S3Error:
            pass
