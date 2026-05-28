import boto3
from botocore.client import Config
from app.core.config import settings

class MinioService:
    def __init__(self):
        # MinIO API is 100% compatible with AWS S3
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f"{'https' if settings.MINIO_SECURE else 'http'}://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1' # Fictional region required by boto3
        )
        self.bucket_name = "audio-uploads"
        self._buckets_checked = False

    def _ensure_buckets(self):
        if self._buckets_checked:
            return
        self._ensure_bucket_exists(self.bucket_name)
        self._ensure_bucket_exists("termos-finais")
        self._ensure_bucket_exists("speaker-samples")
        self._buckets_checked = True

    def _ensure_bucket_exists(self, bucket_name: str):
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except Exception:
            # Bucket does not exist, so we create it
            self.s3_client.create_bucket(Bucket=bucket_name)

    def upload_file(self, file_content: bytes, file_name: str, bucket_name: str = "audio-uploads") -> str:
        """
        Uploads the file and returns its storage URI.
        """
        self._ensure_buckets()
        self.s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=file_content
        )
        return file_name
        
    def generate_presigned_url(self, bucket_name: str, object_name: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL to share an S3 object
        """
        self._ensure_buckets()
        response = self.s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
        return response

minio_service = MinioService()
