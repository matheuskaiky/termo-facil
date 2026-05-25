import io
import math
import wave
import uuid
import pytest
from datetime import date
from app.models import Depoimento, MidiaBruta, Depoente, Inquerito


def _gerar_wav_seno(freq=440, duracao_s=1.0, sample_rate=16000, amplitude=0.4):
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


class TestGetAudioUrl:
	"""Tests for the /api/v1/audio/{id_depoimento} endpoint."""

	def test_get_audio_url_success(self, client, valid_token, db_session, test_user, mock_storage):
		"""Should return presigned URL for valid audio."""
		id_depoimento = uuid.uuid4()

		depoente = Depoente(
			id_depoente=uuid.uuid4(),
			cpf="12345678901234",
			nome_depoente="João da Silva"
		)
		db_session.add(depoente)

		inquerito = Inquerito(
			id_inquerito=uuid.uuid4(),
			id_delegacia=test_user.id_delegacia,
			num_procedimento="2024-00001",
			data_instauracao=date.today()
		)
		db_session.add(inquerito)
		db_session.flush()

		depoimento = Depoimento(
			id_depoimento=id_depoimento,
			id_inquerito=inquerito.id_inquerito,
			id_usuario=test_user.id_usuario,
			id_depoente=depoente.id_depoente,
			tipo_depoente="Vítima"
		)
		db_session.add(depoimento)

		midia = MidiaBruta(
			id_depoimento=id_depoimento,
			storage_path="s3://bucket/audio.wav",
			hash_sha256="abc123def456",
			codec_info="audio/wav"
		)
		db_session.add(midia)
		db_session.commit()

		response = client.get(
			f"/api/v1/audio/{id_depoimento}",
			headers=valid_token
		)

		assert response.status_code == 200
		data = response.json()
		assert "audio_url" in data
		assert data["audio_url"] == "http://localhost:9000/audio.wav"

	def test_get_audio_url_invalid_uuid(self, client, valid_token):
		"""Should return 422 for invalid UUID format."""
		response = client.get(
			"/api/v1/audio/not-a-uuid",
			headers=valid_token
		)

		assert response.status_code == 422
		data = response.json()
		assert "ID de depoimento inválido" in data["detail"]

	def test_get_audio_url_not_found(self, client, valid_token):
		"""Should return 404 when audio doesn't exist."""
		fake_uuid = uuid.uuid4()

		response = client.get(
			f"/api/v1/audio/{fake_uuid}",
			headers=valid_token
		)

		assert response.status_code == 404
		data = response.json()
		assert "Mídia de áudio não encontrada" in data["detail"]

	def test_get_audio_url_storage_error(self, client, valid_token, db_session, test_user, mocker):
		"""Should return 500 when storage service fails."""
		id_depoimento = uuid.uuid4()

		depoente = Depoente(
			id_depoente=uuid.uuid4(),
			cpf="12345678901234",
			nome_depoente="João da Silva"
		)
		db_session.add(depoente)

		inquerito = Inquerito(
			id_inquerito=uuid.uuid4(),
			id_delegacia=test_user.id_delegacia,
			num_procedimento="2024-00001",
			data_instauracao=date.today()
		)
		db_session.add(inquerito)
		db_session.flush()

		depoimento = Depoimento(
			id_depoimento=id_depoimento,
			id_inquerito=inquerito.id_inquerito,
			id_usuario=test_user.id_usuario,
			id_depoente=depoente.id_depoente,
			tipo_depoente="Vítima"
		)
		db_session.add(depoimento)

		midia = MidiaBruta(
			id_depoimento=id_depoimento,
			storage_path="s3://bucket/audio.wav",
			hash_sha256="abc123def456",
			codec_info="audio/wav"
		)
		db_session.add(midia)
		db_session.commit()

		mocker.patch(
			"app.services.storage_service.audio_storage.generate_presigned_url",
			side_effect=Exception("Connection refused")
		)

		response = client.get(
			f"/api/v1/audio/{id_depoimento}",
			headers=valid_token
		)

		assert response.status_code == 500
		data = response.json()
		assert "Erro ao gerar URL de acesso ao áudio" in data["detail"]

	def test_get_audio_url_requires_authentication(self, client):
		"""Should return 401 when not authenticated."""
		fake_uuid = uuid.uuid4()

		response = client.get(f"/api/v1/audio/{fake_uuid}")

		assert response.status_code == 401
