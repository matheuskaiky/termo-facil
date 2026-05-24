import pytest
import io
import uuid


def test_upload_audio(client, valid_token, mock_storage, mock_celery, mocker):
    fake_uuid = uuid.uuid4()
    mocker.patch("app.api.endpoints.upload._resolve_modelo", return_value=fake_uuid)

    file_content = b"fake wav audio data"
    files = {"file": ("test.wav", io.BytesIO(file_content), "audio/wav")}
    data = {"id_depoimento": str(uuid.uuid4())}

    response = client.post(
        "/api/v1/upload/audio",
        headers=valid_token,
        files=files,
        data=data,
    )

    assert response.status_code == 202
    resp_data = response.json()
    assert "id_job" in resp_data
    assert "id_depoimento" in resp_data
    assert resp_data["status"] == "Pendente"

    mock_celery.assert_called_once()
