"""
Real-AI availability detection for the test suite.

The user requirement is: **real models are the priority**, with a mock fallback used
only when a model is genuinely unavailable. `TEST_AI_MODE` controls the policy:

    auto  (default) — use the real model when detected as available, else mock
    real            — force real models (tests skip/fail if a model is missing)
    mock            — force mocks (fast, deterministic, CI-friendly)

Availability is probed conservatively so the default suite stays green offline:
a model counts as "available" only when its weights are already cached locally
(ASR/NER) or its server answers (Ollama). This way real execution is preferred
whenever the artefacts exist, without ever requiring a network download mid-test.
"""

import os
import glob
import shutil
import httpx


def mode() -> str:
    return os.getenv("TEST_AI_MODE", "auto").lower()


def _force_real() -> bool:
    return mode() == "real"


def _force_mock() -> bool:
    return mode() == "mock"


# ── ASR (Whisper) ────────────────────────────────────────────────────────────
def whisper_model_cached(size: str | None = None) -> bool:
    size = size or os.getenv("WHISPER_MODEL_SIZE", "base")
    cache = os.path.expanduser("~/.cache/whisper")
    return os.path.isfile(os.path.join(cache, f"{size}.pt"))


def whisper_available() -> bool:
    if _force_mock():
        return False
    try:
        import whisper  # noqa: F401
    except Exception:
        return False
    # asr_service.transcribe() decodes audio via ffmpeg (whisper.load_audio).
    # Without ffmpeg the service path cannot run, so treat it as unavailable.
    if shutil.which("ffmpeg") is None:
        return False
    return True if _force_real() else whisper_model_cached()


# ── NER (LeNER-Br via HuggingFace) ───────────────────────────────────────────
def lener_cached() -> bool:
    hub = os.path.expanduser("~/.cache/huggingface/hub")
    return bool(glob.glob(os.path.join(hub, "*lener*")) or glob.glob(os.path.join(hub, "*ner-bert*")))


def lener_available() -> bool:
    if _force_mock():
        return False
    try:
        import transformers  # noqa: F401
        import torch  # noqa: F401
    except Exception:
        return False
    return True if _force_real() else lener_cached()


# ── LLM (Ollama / vLLM) ──────────────────────────────────────────────────────
def ollama_available() -> bool:
    if _force_mock():
        return False
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    try:
        resp = httpx.get(f"{base_url}/api/tags", timeout=2.0)
        return resp.status_code == 200
    except Exception:
        return False


# ── Diarization / embeddings (PyAnnote) ──────────────────────────────────────
def pyannote_available() -> bool:
    if _force_mock():
        return False
    try:
        import pyannote.audio  # noqa: F401
    except Exception:
        return False
    return True
