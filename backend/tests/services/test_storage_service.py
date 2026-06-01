"""Unit tests for the MinioStorage adapter (boto3 client mocked)."""
from unittest.mock import MagicMock

import pytest

from app.services.storage_service import MinioStorage

pytestmark = pytest.mark.unit


def test_upload_file_delegates_and_returns_key():
    client = MagicMock()
    storage = MinioStorage(client, bucket="audio-uploads")
    key = storage.upload_file(b"data", "file.wav")
    assert key == "file.wav"
    client.upload_file.assert_called_once_with(b"data", "file.wav", "audio-uploads")


def test_generate_presigned_url_delegates():
    client = MagicMock()
    client.generate_presigned_url.return_value = "http://minio/presigned"
    storage = MinioStorage(client, bucket="termos-finais")
    url = storage.generate_presigned_url("obj", expiration=120)
    assert url == "http://minio/presigned"
    client.generate_presigned_url.assert_called_once_with("termos-finais", "obj", 120)


def test_delete_file_calls_s3_delete_object():
    client = MagicMock()
    storage = MinioStorage(client, bucket="audio-uploads")
    storage.delete_file("some/key.wav")
    client.s3_client.delete_object.assert_called_once_with(Bucket="audio-uploads", Key="some/key.wav")
