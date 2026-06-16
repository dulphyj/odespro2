import io

from minio import Minio
from minio.error import S3Error

from app.config import get_settings

settings = get_settings()


class MinioService:
    def __init__(self):
        self.client = Minio(
            f"{settings.minio_host}:{settings.minio_port}",
            access_key=settings.minio_root_user,
            secret_key=settings.minio_root_password,
            secure=False,
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(settings.minio_bucket):
            self.client.make_bucket(settings.minio_bucket)

    def upload_image(self, image_data: bytes, object_name: str, content_type: str = "image/png") -> str:
        size = len(image_data)
        self.client.put_object(
            settings.minio_bucket,
            object_name,
            io.BytesIO(image_data),
            size,
            content_type=content_type,
        )
        return object_name

    def get_image(self, object_name: str) -> bytes | None:
        try:
            response = self.client.get_object(settings.minio_bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error:
            return None

    def delete_object(self, object_name: str):
        try:
            self.client.remove_object(settings.minio_bucket, object_name)
        except S3Error:
            pass
