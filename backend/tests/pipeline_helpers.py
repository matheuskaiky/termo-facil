"""
Helpers to run the real Celery pipeline task (process_audio_task) synchronously
against the in-memory test DB, choosing real or mock AI adapters per availability.

Real models are the priority: when a model is available it is used; otherwise the
deterministic mock from tests/mocks.py is injected. ASR/NER/LLM are selected
independently so a partially-available environment (e.g. Whisper cached but no
Ollama) still exercises as much real code as possible.
"""

from __future__ import annotations
import contextlib
import os

from tests import ai_availability as avail
from tests.mocks import MockASRModel, MockNERModel, MockLLM

TEST_WAV = os.path.join(os.path.dirname(__file__), "micro-machines.wav")


def select_asr():
    if avail.whisper_available():
        from app.services.asr_service import asr_model
        return asr_model, "real"
    return MockASRModel(), "mock"


def select_ner():
    if avail.lener_available():
        from app.services.ner_service import ner_model
        return ner_model, "real"
    return MockNERModel(), "mock"


def select_llm():
    if avail.ollama_available():
        from app.services.llm_service import llm_model
        return llm_model, "real"
    return MockLLM(), "mock"


def run_process_audio(job_id, db_session_factory, mocker, audio_path: str = TEST_WAV):
    """
    Patches the task's module-level dependencies and runs it in-process.
    Returns a dict describing which adapters (real/mock) were used.
    """
    import app.tasks.process_audio as task_mod

    asr, asr_kind = select_asr()
    ner, ner_kind = select_ner()
    llm, llm_kind = select_llm()

    mocker.patch.object(task_mod, "SessionLocal", db_session_factory)
    mocker.patch.object(task_mod, "asr_model", asr)
    mocker.patch.object(task_mod, "ner_model", ner)
    mocker.patch.object(task_mod, "llm_model", llm)
    # Force the heuristic (non-PixIT) flow — separation is covered separately.
    mocker.patch.object(task_mod, "build_diarizer", lambda: None)

    @contextlib.contextmanager
    def fake_download(_storage_path):
        yield audio_path

    mocker.patch("app.services.storage_service.audio_storage.download_as_local_file", fake_download)

    # Pass the UUID object: the SQLite test engine keeps the postgres UUID bind
    # processor (only the DDL is remapped to VARCHAR), so it requires uuid.UUID.
    # In production the DB driver coerces the str Celery would send.
    ok = task_mod.process_audio_task(job_id)
    return {"ok": ok, "asr": asr_kind, "ner": ner_kind, "llm": llm_kind}
