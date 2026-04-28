import boto3
from botocore.client import Config
from app.core.config import settings

class MinioService:
    def __init__(self):
        # MinIO API is 100% compatible with AWS S3
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1' # Fictional region required by boto3
        )
        self.bucket_name = "audio-uploads"
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except Exception:
            # Bucket does not exist, so we create it
            self.s3_client.create_bucket(Bucket=self.bucket_name)

    def upload_file(self, file_content: bytes, file_name: str) -> str:
        """
        Uploads the file and returns its storage URI.
        """
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=file_name,
            Body=file_content
        )
        # The storage_path to be saved in the database
        return f"s3://{self.bucket_name}/{file_name}"

minio_service = MinioService()
