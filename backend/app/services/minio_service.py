import boto3
from botocore.client import Config
from app.core.config import settings

class MinioService:
    def __init__(self):
        # A API do MinIO é 100% compatível com a do S3 da AWS
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1' # Região fictícia requerida pelo boto3
        )
        self.bucket_name = "audio-uploads"
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except Exception:
            # O bucket não existe, então criamos
            self.s3_client.create_bucket(Bucket=self.bucket_name)

    def upload_file(self, file_content: bytes, file_name: str) -> str:
        """
        Faz o upload do arquivo e retorna a URI do storage.
        """
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=file_name,
            Body=file_content
        )
        # O storage_path para ser salvo no banco
        return f"s3://{self.bucket_name}/{file_name}"

minio_service = MinioService()
