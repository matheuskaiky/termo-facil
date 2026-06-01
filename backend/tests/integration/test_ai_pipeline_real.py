"""
Real-model integration tests (the priority path).

These run the *actual* Whisper / LeNER-Br / Ollama adapters. Each test skips
gracefully when its model is unavailable, so the default suite stays green while
still exercising real inference whenever the artefacts/servers are present.

Force with TEST_AI_MODE=real; force-skip with TEST_AI_MODE=mock.
"""
import os

import pytest

from tests import ai_availability as avail
from tests.conftest import TestingSessionLocal
from tests.factories import create_delegacia, create_user, create_depoimento, create_midia, create_job
from tests.pipeline_helpers import run_process_audio, TEST_WAV
from app.models import TermosFinais, JobProcessamentoIA, StatusJob

pytestmark = [pytest.mark.requires_models, pytest.mark.slow]


@pytest.mark.skipif(not avail.whisper_available(), reason="Whisper model not available")
def test_real_whisper_transcribes_sample_audio():
    from app.services.asr_service import WhisperASRModel
    model = WhisperASRModel(model_size=os.getenv("WHISPER_MODEL_SIZE", "base"))
    segments = model.transcribe(TEST_WAV, language="en")
    assert isinstance(segments, list) and len(segments) > 0
    assert all({"start", "end", "text", "speaker"} <= set(s) for s in segments)
    assert any(s["text"].strip() for s in segments)


@pytest.mark.skipif(not avail.lener_available(), reason="LeNER-Br model not available")
def test_real_lener_extracts_person_entity():
    from app.services.ner_service import LeNERModel
    model = LeNERModel(model_name=os.getenv("NER_MODEL_NAME", "pierreguillou/ner-bert-large-cased-pt-lenerbr"))
    texto = (
        "O depoente João da Silva declarou que, conforme o artigo 157 do Código Penal, "
        "o fato ocorreu na cidade de Teresina."
    )
    entidades = model.extract_entities(texto)
    assert set(entidades.keys()) >= {"PESSOAS", "LOCAIS", "LEGISLACAO"}
    todas = sum((v for v in entidades.values()), [])
    assert any("João" in e or "Silva" in e for e in todas)


@pytest.mark.skipif(not avail.ollama_available(), reason="Ollama server not reachable")
def test_real_ollama_synthesizes_with_ner_anchoring():
    from app.services.llm_service import OllamaLLM
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    model_name = os.getenv("LLM_MODEL_NAME", "llama3")
    llm = OllamaLLM(base_url, model_name)
    out = llm.synthesize(
        "Eu sou João e estava na avenida central.",
        entities={"PESSOAS": ["João"], "LOCAIS": ["avenida central"]},
    )
    assert isinstance(out, str) and len(out.strip()) > 0


@pytest.mark.skipif(not avail.whisper_available(), reason="Whisper model not available")
def test_real_pipeline_end_to_end(db_session, mocker):
    """Runs process_audio_task with real models where available (ASR at minimum)."""
    deleg = create_delegacia(db_session)
    user = create_user(db_session, deleg, "Escrivão", ["EDITAR_TERMO"])
    dep = create_depoimento(db_session, user, deleg)
    create_midia(db_session, dep)
    job = create_job(db_session, dep, status=StatusJob.PENDENTE)

    result = run_process_audio(job.id_job, TestingSessionLocal, mocker, audio_path=TEST_WAV)
    assert result["asr"] == "real"  # priority path actually exercised
    assert result["ok"] is True

    db_session.expire_all()
    termo = db_session.query(TermosFinais).filter_by(id_depoimento=dep.id_depoimento).first()
    assert termo is not None and termo.txt_literal_asr
    refreshed = db_session.query(JobProcessamentoIA).filter_by(id_job=job.id_job).first()
    assert refreshed.status == StatusJob.CONCLUIDO
