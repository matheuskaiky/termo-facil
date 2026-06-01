"""Unit tests for the diarizer factory + label map (no model loading)."""
import pytest

from app.services import diarization_service as diar
from app.services.diarization_service import (
    build_diarizer, _LazyPyAnnoteSeparationDiarizer, _PYANNOTE_LABEL_MAP,
)

pytestmark = pytest.mark.unit


def test_build_diarizer_heuristic_returns_none(monkeypatch):
    monkeypatch.setenv("DIARIZATION_PROVIDER", "heuristic")
    assert build_diarizer() is None


def test_build_diarizer_default_is_heuristic(monkeypatch):
    monkeypatch.delenv("DIARIZATION_PROVIDER", raising=False)
    assert build_diarizer() is None


def test_build_diarizer_pyannote_returns_separation_diarizer(monkeypatch):
    monkeypatch.setenv("DIARIZATION_PROVIDER", "pyannote")
    d = build_diarizer()
    assert isinstance(d, _LazyPyAnnoteSeparationDiarizer)


def test_pixit_diarizer_requires_token(monkeypatch):
    monkeypatch.delenv("PYANNOTE_HF_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="PYANNOTE_HF_TOKEN"):
        _LazyPyAnnoteSeparationDiarizer().diarize_and_separate("/tmp/audio.wav")


def test_label_map_maps_first_two_speakers():
    assert _PYANNOTE_LABEL_MAP["SPEAKER_00"] == "Inquiridor"
    assert _PYANNOTE_LABEL_MAP["SPEAKER_01"] == "Depoente"
