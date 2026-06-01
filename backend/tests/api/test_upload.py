import io
import uuid

from tests.factories import create_delegacia, create_user, create_depoimento, create_midia

# Minimal valid WAV header (RIFF....WAVE) — passes the magic-bytes check.
WAV_HEADER = b"RIFF\x24\x08\x00\x00WAVEfmt "


def _login(client, matricula):
    resp = client.post("/api/v1/auth/login", json={"matricula": matricula, "senha": "senha_forte"})
    assert resp.status_code == 200, resp.json()
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_upload_audio_success(client, db_session, valid_token, test_user, mock_storage, mock_celery, mocker):
    dep = create_depoimento(db_session, test_user, test_user.delegacia)
    mocker.patch("app.api.endpoints.upload._resolve_modelo", return_value=uuid.uuid4())

    files = {"file": ("test.wav", io.BytesIO(WAV_HEADER + b"\x00" * 100), "audio/wav")}
    data = {"id_depoimento": str(dep.id_depoimento)}

    response = client.post("/api/v1/upload/audio", headers=valid_token, files=files, data=data)

    assert response.status_code == 202, response.json()
    body = response.json()
    assert "id_job" in body
    assert body["status"] == "Pendente"
    mock_celery.assert_called_once()


def test_upload_audio_unsupported_extension(client, db_session, valid_token, test_user):
    dep = create_depoimento(db_session, test_user, test_user.delegacia)
    files = {"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")}
    data = {"id_depoimento": str(dep.id_depoimento)}
    response = client.post("/api/v1/upload/audio", headers=valid_token, files=files, data=data)
    assert response.status_code == 400


def test_upload_audio_depoimento_not_found(client, valid_token, test_user, mocker):
    mocker.patch("app.api.endpoints.upload._resolve_modelo", return_value=uuid.uuid4())
    files = {"file": ("test.wav", io.BytesIO(WAV_HEADER + b"\x00" * 100), "audio/wav")}
    data = {"id_depoimento": str(uuid.uuid4())}
    response = client.post("/api/v1/upload/audio", headers=valid_token, files=files, data=data)
    assert response.status_code == 404


def test_upload_audio_rejects_invalid_magic_bytes(client, db_session, valid_token, test_user, mocker):
    dep = create_depoimento(db_session, test_user, test_user.delegacia)
    mocker.patch("app.api.endpoints.upload._resolve_modelo", return_value=uuid.uuid4())
    files = {"file": ("audio.wav", io.BytesIO(b"%PDF-1.4 not an audio file at all"), "audio/wav")}
    data = {"id_depoimento": str(dep.id_depoimento)}
    response = client.post("/api/v1/upload/audio", headers=valid_token, files=files, data=data)
    assert response.status_code == 415


def test_upload_requires_permission(client, db_session, mock_storage, mock_celery, mocker):
    """A user lacking UPLOAD_AUDIO gets 403."""
    deleg = create_delegacia(db_session)
    create_user(db_session, deleg, "Somente Leitura", ["VER_METRICAS"], "RO0001")
    mocker.patch("app.api.endpoints.upload._resolve_modelo", return_value=uuid.uuid4())
    headers = _login(client, "RO0001")
    files = {"file": ("test.wav", io.BytesIO(WAV_HEADER + b"\x00" * 100), "audio/wav")}
    data = {"id_depoimento": str(uuid.uuid4())}
    response = client.post("/api/v1/upload/audio", headers=headers, files=files, data=data)
    assert response.status_code == 403


def test_upload_speaker_sample_success(client, db_session, valid_token, test_user, mock_storage):
    dep = create_depoimento(db_session, test_user, test_user.delegacia)
    create_midia(db_session, dep)
    files = {"file": ("sample.wav", io.BytesIO(WAV_HEADER + b"\x00" * 100), "audio/wav")}
    data = {"id_depoimento": str(dep.id_depoimento), "role": "Depoente"}
    response = client.post("/api/v1/upload/speaker-sample", headers=valid_token, files=files, data=data)
    assert response.status_code == 200
    assert response.json()["role"] == "Depoente"


def test_upload_speaker_sample_invalid_role(client, db_session, valid_token, test_user, mock_storage):
    dep = create_depoimento(db_session, test_user, test_user.delegacia)
    create_midia(db_session, dep)
    files = {"file": ("sample.wav", io.BytesIO(WAV_HEADER + b"\x00" * 100), "audio/wav")}
    data = {"id_depoimento": str(dep.id_depoimento), "role": "Juiz"}
    response = client.post("/api/v1/upload/speaker-sample", headers=valid_token, files=files, data=data)
    assert response.status_code == 422


def test_upload_speaker_sample_requires_main_audio_first(client, db_session, valid_token, test_user, mock_storage):
    dep = create_depoimento(db_session, test_user, test_user.delegacia)  # no midia
    files = {"file": ("sample.wav", io.BytesIO(WAV_HEADER + b"\x00" * 100), "audio/wav")}
    data = {"id_depoimento": str(dep.id_depoimento), "role": "Depoente"}
    response = client.post("/api/v1/upload/speaker-sample", headers=valid_token, files=files, data=data)
    assert response.status_code == 400
