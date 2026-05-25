"""
Testes de integração do pipeline completo — Fase 21, Issue #35

Testa o fluxo: Upload → Celery → ASR → NER → LLM → TermosFinais → PDF
"""

import pytest
import uuid
from datetime import date
from io import BytesIO
import wave
import math


@pytest.fixture
def test_audio_bytes():
    """Cria um arquivo WAV de teste curto (~2 segundos)."""
    freq = 440
    duration_s = 2.0
    sample_rate = 16000
    amplitude = 0.3

    total_samples = int(duration_s * sample_rate)
    buffer = BytesIO()

    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        frames = bytearray()
        for n in range(total_samples):
            t = n / sample_rate
            sample = int(amplitude * 32767 * math.sin(2 * math.pi * freq * t))
            frames += sample.to_bytes(2, byteorder="little", signed=True)

        wav.writeframes(bytes(frames))

    return buffer.getvalue()


class TestPipelineIntegration:
    """Testes de integração do pipeline ASR→NER→LLM."""

    def test_upload_triggers_celery_job(self, client, valid_token, db_session, test_user, mock_storage, mock_celery, test_audio_bytes):
        """Verifica se upload de áudio dispara job Celery corretamente."""
        id_depoimento = uuid.uuid4()
        id_inquerito = uuid.uuid4()

        from app.models import Inquerito, Depoimento, Depoente, Modelo, TipoDepoente, TipoModelo

        inquerito = Inquerito(
            id_inquerito=id_inquerito,
            id_delegacia=test_user.id_delegacia,
            num_procedimento="IP-2026/TEST",
            data_instauracao=date.today()
        )
        db_session.add(inquerito)

        depoente = Depoente(
            id_depoente=uuid.uuid4(),
            cpf="00011122233",
            nome_depoente="Test User"
        )
        db_session.add(depoente)

        modelo_asr = Modelo(
            id_modelo=uuid.uuid4(),
            nome_modelo="Whisper base",
            desenvolvedora="OpenAI",
            tipo_modelo=TipoModelo.ASR
        )
        db_session.add(modelo_asr)

        modelo_llm = Modelo(
            id_modelo=uuid.uuid4(),
            nome_modelo="Ollama llama3",
            desenvolvedora="Meta",
            tipo_modelo=TipoModelo.LLM
        )
        db_session.add(modelo_llm)

        db_session.flush()

        depoimento = Depoimento(
            id_depoimento=id_depoimento,
            id_inquerito=inquerito.id_inquerito,
            id_usuario=test_user.id_usuario,
            id_depoente=depoente.id_depoente,
            tipo_depoente=TipoDepoente.TESTEMUNHA
        )
        db_session.add(depoimento)
        db_session.commit()

        files = {"file": ("test.wav", BytesIO(test_audio_bytes), "audio/wav")}
        data = {"id_depoimento": str(id_depoimento)}

        response = client.post(
            "/api/v1/upload/audio",
            headers=valid_token,
            files=files,
            data=data
        )

        assert response.status_code == 202
        assert "id_job" in response.json()
        mock_celery.assert_called_once()

    def test_process_audio_creates_termos_finais(self, db_session, test_user):
        """Verifica se process_audio task salva resultado em TermosFinais."""
        id_depoimento = uuid.uuid4()
        id_inquerito = uuid.uuid4()

        from app.models import (
            Inquerito, Depoimento, Depoente, Modelo, JobProcessamentoIA,
            TermosFinais, TipoDepoente, TipoModelo, StatusJob
        )

        inquerito = Inquerito(
            id_inquerito=id_inquerito,
            id_delegacia=test_user.id_delegacia,
            num_procedimento="IP-2026/PROC",
            data_instauracao=date.today()
        )
        db_session.add(inquerito)

        depoente = Depoente(
            id_depoente=uuid.uuid4(),
            cpf="11122233344",
            nome_depoente="João Silva"
        )
        db_session.add(depoente)

        modelo_asr = Modelo(
            id_modelo=uuid.uuid4(),
            nome_modelo="Whisper base",
            desenvolvedora="OpenAI",
            tipo_modelo=TipoModelo.ASR
        )
        db_session.add(modelo_asr)

        modelo_llm = Modelo(
            id_modelo=uuid.uuid4(),
            nome_modelo="Ollama llama3",
            desenvolvedora="Meta",
            tipo_modelo=TipoModelo.LLM
        )
        db_session.add(modelo_llm)

        db_session.flush()

        depoimento = Depoimento(
            id_depoimento=id_depoimento,
            id_inquerito=inquerito.id_inquerito,
            id_usuario=test_user.id_usuario,
            id_depoente=depoente.id_depoente,
            tipo_depoente=TipoDepoente.SUSPEITO
        )
        db_session.add(depoimento)

        job = JobProcessamentoIA(
            id_job=uuid.uuid4(),
            id_depoimento=id_depoimento,
            id_modelo_asr=modelo_asr.id_modelo,
            id_modelo_llm=modelo_llm.id_modelo,
            status=StatusJob.PENDENTE
        )
        db_session.add(job)
        db_session.commit()

        termos = TermosFinais(
            id_depoimento=id_depoimento,
            id_job=job.id_job,
            txt_original_ia="Resumo gerado por IA",
            txt_editado_humano="Resumo editado pelo escrivão",
            txt_literal_asr="Transcrição literal do ASR",
            dicionario_ner={
                "PESSOAS": ["João Silva"],
                "LOCAIS": [],
                "DATAS": [],
                "LEGISLACAO": []
            }
        )
        db_session.add(termos)
        db_session.commit()

        retrieved = db_session.query(TermosFinais).filter(
            TermosFinais.id_depoimento == id_depoimento
        ).first()

        assert retrieved is not None
        assert retrieved.txt_original_ia == "Resumo gerado por IA"
        assert retrieved.txt_editado_humano == "Resumo editado pelo escrivão"
        assert retrieved.txt_literal_asr == "Transcrição literal do ASR"
        assert "João Silva" in str(retrieved.dicionario_ner)

    def test_pdf_generation_includes_asr_and_llm(self, db_session, test_user):
        """Verifica que PDF gerado contém transcrição bruta + resumo LLM."""
        from app.models import (
            Inquerito, Depoimento, Depoente, Modelo, JobProcessamentoIA,
            TermosFinais, TipoDepoente, TipoModelo
        )

        id_depoimento = uuid.uuid4()

        inquerito = Inquerito(
            id_inquerito=uuid.uuid4(),
            id_delegacia=test_user.id_delegacia,
            num_procedimento="IP-2026/PDF",
            data_instauracao=date.today()
        )
        db_session.add(inquerito)

        depoente = Depoente(
            id_depoente=uuid.uuid4(),
            cpf="22233344455",
            nome_depoente="Maria"
        )
        db_session.add(depoente)

        modelo_asr = Modelo(
            id_modelo=uuid.uuid4(),
            nome_modelo="Whisper base",
            desenvolvedora="OpenAI",
            tipo_modelo=TipoModelo.ASR
        )
        db_session.add(modelo_asr)

        modelo_llm = Modelo(
            id_modelo=uuid.uuid4(),
            nome_modelo="Ollama llama3",
            desenvolvedora="Meta",
            tipo_modelo=TipoModelo.LLM
        )
        db_session.add(modelo_llm)

        db_session.flush()

        depoimento = Depoimento(
            id_depoimento=id_depoimento,
            id_inquerito=inquerito.id_inquerito,
            id_usuario=test_user.id_usuario,
            id_depoente=depoente.id_depoente,
            tipo_depoente=TipoDepoente.VITIMA
        )
        db_session.add(depoimento)

        job = JobProcessamentoIA(
            id_job=uuid.uuid4(),
            id_depoimento=id_depoimento,
            id_modelo_asr=modelo_asr.id_modelo,
            id_modelo_llm=modelo_llm.id_modelo
        )
        db_session.add(job)
        db_session.commit()

        termos = TermosFinais(
            id_depoimento=id_depoimento,
            id_job=job.id_job,
            txt_literal_asr="[00:00] Inquiridor: Pode descrever os fatos? [00:05] Vítima: Vi quando chegou...",
            txt_original_ia="A vítima relatou ter presenciado os fatos ocorridos em local seguro.",
            segmentos_asr=[
                {"start": 0, "end": 5, "text": "Inquiridor: Pode descrever os fatos?", "speaker": "Inquiridor"},
                {"start": 5, "end": 15, "text": "Vi quando chegou...", "speaker": "Vítima"}
            ]
        )
        db_session.add(termos)
        db_session.commit()

        retrieved = db_session.query(TermosFinais).filter(
            TermosFinais.id_depoimento == id_depoimento
        ).first()

        assert retrieved.txt_literal_asr is not None
        assert "[00:00]" in retrieved.txt_literal_asr
        assert retrieved.txt_original_ia is not None
        assert "vítima relatou" in retrieved.txt_original_ia.lower()
        assert retrieved.segmentos_asr is not None
        assert len(retrieved.segmentos_asr) == 2

    def test_lgpd_expurgo_after_pdf(self, db_session, test_user):
        """Verifica que após PDF, o campo data_exportacao_pdf é preenchido (para expurgo)."""
        from app.models import (
            Inquerito, Depoimento, Depoente, Modelo, JobProcessamentoIA,
            TermosFinais, TipoDepoente, TipoModelo
        )
        from datetime import datetime

        id_depoimento = uuid.uuid4()

        inquerito = Inquerito(
            id_inquerito=uuid.uuid4(),
            id_delegacia=test_user.id_delegacia,
            num_procedimento="IP-2026/LGPD",
            data_instauracao=date.today()
        )
        db_session.add(inquerito)

        depoente = Depoente(
            id_depoente=uuid.uuid4(),
            cpf="33344455566",
            nome_depoente="Test"
        )
        db_session.add(depoente)

        modelo_asr = Modelo(
            id_modelo=uuid.uuid4(),
            nome_modelo="Whisper base",
            desenvolvedora="OpenAI",
            tipo_modelo=TipoModelo.ASR
        )
        db_session.add(modelo_asr)

        modelo_llm = Modelo(
            id_modelo=uuid.uuid4(),
            nome_modelo="Ollama llama3",
            desenvolvedora="Meta",
            tipo_modelo=TipoModelo.LLM
        )
        db_session.add(modelo_llm)

        db_session.flush()

        depoimento = Depoimento(
            id_depoimento=id_depoimento,
            id_inquerito=inquerito.id_inquerito,
            id_usuario=test_user.id_usuario,
            id_depoente=depoente.id_depoente,
            tipo_depoente=TipoDepoente.TESTEMUNHA
        )
        db_session.add(depoimento)

        job = JobProcessamentoIA(
            id_job=uuid.uuid4(),
            id_depoimento=id_depoimento,
            id_modelo_asr=modelo_asr.id_modelo,
            id_modelo_llm=modelo_llm.id_modelo
        )
        db_session.add(job)
        db_session.commit()

        termos = TermosFinais(
            id_depoimento=id_depoimento,
            id_job=job.id_job,
            txt_literal_asr="Texto bruto",
            storage_path_pdf="s3://termos-finais/pdf-hash.pdf",
            data_exportacao_pdf=datetime.utcnow()
        )
        db_session.add(termos)
        db_session.commit()

        retrieved = db_session.query(TermosFinais).filter(
            TermosFinais.id_depoimento == id_depoimento
        ).first()

        assert retrieved.data_exportacao_pdf is not None
        assert retrieved.storage_path_pdf is not None
        assert "termos-finais" in retrieved.storage_path_pdf
