import os
import tempfile
from typing import Protocol, Generator
from contextlib import contextmanager

from app.services.minio_service import minio_service


class FileStorage(Protocol):
    def upload_file(self, file_content: bytes, file_name: str) -> str:
        ...

    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> str:
        ...

    def delete_file(self, object_key: str) -> None:
        ...

    @contextmanager
    def download_as_local_file(self, object_key: str) -> Generator[str, None, None]:
        ...


class MinioStorage:
    def __init__(self, client, bucket: str):
        self._client = client
        self._bucket = bucket

    def upload_file(self, file_content: bytes, file_name: str) -> str:
        self._client.upload_file(file_content, file_name, self._bucket)
        return file_name

    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> str:
        return self._client.generate_presigned_url(self._bucket, object_key, expiration)

    def delete_file(self, object_key: str) -> None:
        self._client.s3_client.delete_object(Bucket=self._bucket, Key=object_key)

    @contextmanager
    def download_as_local_file(self, object_key: str) -> Generator[str, None, None]:
        _, ext = os.path.splitext(object_key)
        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        try:
            self._client.s3_client.download_file(self._bucket, object_key, tmp.name)
            tmp.close()
            yield tmp.name
        finally:
            os.unlink(tmp.name)


audio_storage = MinioStorage(minio_service, bucket="audio-uploads")
pdf_storage   = MinioStorage(minio_service, bucket="termos-finais")
