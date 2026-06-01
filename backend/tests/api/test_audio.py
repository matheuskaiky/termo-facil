import io
import math
import wave
import uuid
from datetime import date

from app.models import Depoimento, MidiaBruta, Depoente, Inquerito


def _gerar_wav_seno(freq=440, duracao_s=1.0, sample_rate=16000, amplitude=0.4) -> bytes:
    total_samples = int(duracao_s * sample_rate)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)  # 16-bit PCM
        wav.setframerate(sample_rate)
        frames = bytearray()
        for n in range(total_samples):
            t = n / sample_rate
            sample = int(amplitude * 32767 * math.sin(2 * math.pi * freq * t))
            frames += sample.to_bytes(2, byteorder="little", signed=True)
        wav.writeframes(bytes(frames))
    return buffer.getvalue()


def test_wav_gerado_tem_header_riff_wave():
    audio = _gerar_wav_seno()
    assert audio[:4] == b"RIFF"
    assert audio[8:12] == b"WAVE"


def test_wav_gerado_tem_parametros_esperados():
    audio = _gerar_wav_seno(freq=220, duracao_s=0.5, sample_rate=8000)
    with wave.open(io.BytesIO(audio), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == 8000
        assert wav.getnframes() == 4000


def _seed_depoimento_com_midia(db_session, test_user) -> uuid.UUID:
    id_depoimento = uuid.uuid4()
    depoente = Depoente(id_depoente=uuid.uuid4(), cpf="12345678901234", nome_depoente="João da Silva")
    inquerito = Inquerito(
        id_inquerito=uuid.uuid4(),
        id_delegacia=test_user.id_delegacia,
        num_procedimento=f"2024-{uuid.uuid4().hex[:5]}",
        data_instauracao=date.today(),
    )
    db_session.add_all([depoente, inquerito])
    db_session.flush()
    db_session.add(Depoimento(
        id_depoimento=id_depoimento,
        id_inquerito=inquerito.id_inquerito,
        id_usuario=test_user.id_usuario,
        id_depoente=depoente.id_depoente,
        tipo_depoente="Vítima",
    ))
    db_session.add(MidiaBruta(
        id_depoimento=id_depoimento,
        storage_path="s3://bucket/audio.wav",
        hash_sha256="abc123def456",
        codec_info={"content_type": "audio/wav"},
    ))
    db_session.commit()
    return id_depoimento


class TestGetAudioUrl:
    """Tests for the /api/v1/audio/{id_depoimento} endpoint."""

    def test_get_audio_url_success(self, client, valid_token, db_session, test_user, mock_storage):
        id_depoimento = _seed_depoimento_com_midia(db_session, test_user)
        response = client.get(f"/api/v1/audio/{id_depoimento}", headers=valid_token)
        assert response.status_code == 200
        assert response.json()["audio_url"] == "http://localhost:9000/audio.wav"

    def test_get_audio_url_invalid_uuid(self, client, valid_token):
        response = client.get("/api/v1/audio/not-a-uuid", headers=valid_token)
        assert response.status_code == 422
        assert "ID de depoimento inválido" in response.json()["detail"]

    def test_get_audio_url_not_found(self, client, valid_token):
        response = client.get(f"/api/v1/audio/{uuid.uuid4()}", headers=valid_token)
        assert response.status_code == 404
        assert "Mídia de áudio não encontrada" in response.json()["detail"]

    def test_get_audio_url_storage_error(self, client, valid_token, db_session, test_user, mocker):
        id_depoimento = _seed_depoimento_com_midia(db_session, test_user)
        mocker.patch(
            "app.services.storage_service.audio_storage.generate_presigned_url",
            side_effect=Exception("Connection refused"),
        )
        response = client.get(f"/api/v1/audio/{id_depoimento}", headers=valid_token)
        assert response.status_code == 500
        assert "Erro ao gerar URL de acesso ao áudio" in response.json()["detail"]

    def test_get_audio_url_requires_authentication(self, client):
        response = client.get(f"/api/v1/audio/{uuid.uuid4()}")
        assert response.status_code == 401
