"""
End-to-end pipeline integration: runs the actual process_audio_task against the
test DB. Real AI models are used when available; otherwise deterministic mocks
keep the suite green everywhere (see tests/pipeline_helpers.py).
"""
import pytest

from app.models import JobProcessamentoIA, TermosFinais, StatusJob
from tests.conftest import TestingSessionLocal
from tests.factories import create_delegacia, create_user, create_depoimento, create_midia, create_job
from tests.pipeline_helpers import run_process_audio

pytestmark = pytest.mark.integration


def _pending_job(db):
    deleg = create_delegacia(db)
    user = create_user(db, deleg, "Escrivão", ["EDITAR_TERMO"])
    dep = create_depoimento(db, user, deleg)
    create_midia(db, dep)
    job = create_job(db, dep, status=StatusJob.PENDENTE)
    return dep, job


def test_pipeline_creates_termos_finais(db_session, mocker):
    dep, job = _pending_job(db_session)

    result = run_process_audio(job.id_job, TestingSessionLocal, mocker)
    assert result["ok"] is True

    db_session.expire_all()
    termo = db_session.query(TermosFinais).filter_by(id_depoimento=dep.id_depoimento).first()
    assert termo is not None
    assert termo.txt_literal_asr            # transcript present
    assert termo.txt_original_ia            # LLM summary present
    assert termo.dicionario_ner is not None
    assert isinstance(termo.segmentos_asr, list) and len(termo.segmentos_asr) > 0

    refreshed_job = db_session.query(JobProcessamentoIA).filter_by(id_job=job.id_job).first()
    assert refreshed_job.status == StatusJob.CONCLUIDO


def test_pipeline_persists_error_on_failure(db_session, mocker):
    """Issue #53: a failure must set job status ERRO and store the message in parametros_ia."""
    import app.tasks.process_audio as task_mod

    dep, job = _pending_job(db_session)

    class _BoomASR:
        def transcribe(self, *a, **k):
            raise RuntimeError("falha simulada no ASR")
        def transcribe_separated(self, *a, **k):
            raise RuntimeError("falha simulada no ASR")

    mocker.patch.object(task_mod, "SessionLocal", TestingSessionLocal)
    mocker.patch.object(task_mod, "asr_model", _BoomASR())
    mocker.patch.object(task_mod, "build_diarizer", lambda: None)

    import contextlib

    @contextlib.contextmanager
    def fake_download(_p):
        yield "/tmp/whatever.wav"

    mocker.patch("app.services.storage_service.audio_storage.download_as_local_file", fake_download)

    ok = task_mod.process_audio_task(job.id_job)
    assert ok is False

    db_session.expire_all()
    refreshed = db_session.query(JobProcessamentoIA).filter_by(id_job=job.id_job).first()
    assert refreshed.status == StatusJob.ERRO
    assert "erro" in (refreshed.parametros_ia or {})
    assert "falha simulada" in refreshed.parametros_ia["erro"]


def test_pipeline_missing_media_sets_error(db_session, mocker):
    deleg = create_delegacia(db_session)
    user = create_user(db_session, deleg, "Escrivão", ["EDITAR_TERMO"])
    dep = create_depoimento(db_session, user, deleg)  # no midia
    job = create_job(db_session, dep, status=StatusJob.PENDENTE)

    import app.tasks.process_audio as task_mod
    mocker.patch.object(task_mod, "SessionLocal", TestingSessionLocal)

    ok = task_mod.process_audio_task(job.id_job)
    assert ok is False

    db_session.expire_all()
    refreshed = db_session.query(JobProcessamentoIA).filter_by(id_job=job.id_job).first()
    assert refreshed.status == StatusJob.ERRO
