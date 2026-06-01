"""
Unit tests for asr_service logic that does NOT require loading Whisper weights:
- the gap-based speaker heuristic
- the diarization-overlap merge
- the Whisper hallucination filter in transcribe_separated
"""
import pytest

from app.services import asr_service
from app.services.asr_service import (
    WhisperASRModel, _assign_speakers_heuristic, _merge_with_diarization,
)

pytestmark = pytest.mark.unit


def test_heuristic_alternates_speakers_on_long_gap():
    segments = [
        {"start": 0.0, "end": 2.0, "text": "Pergunta um."},
        {"start": 2.2, "end": 4.0, "text": "continuação"},      # small gap → same speaker
        {"start": 6.0, "end": 8.0, "text": "Resposta."},        # >1s gap → switch
    ]
    out = _assign_speakers_heuristic(segments)
    assert out[0]["speaker"] == "Inquiridor"
    assert out[1]["speaker"] == "Inquiridor"
    assert out[2]["speaker"] == "Depoente"


def test_merge_with_diarization_assigns_by_overlap():
    segments = [{"start": 0.0, "end": 5.0, "text": "fala"}]
    turns = [(0.0, 1.0, "SPEAKER_00"), (1.0, 5.0, "SPEAKER_01")]
    out = _merge_with_diarization(segments, turns)
    assert out[0]["speaker"] == "SPEAKER_01"  # covers most of the segment


def _whisper_with_fake_model(fake_result):
    """Builds a WhisperASRModel bypassing __init__ (no weight loading)."""
    model = object.__new__(WhisperASRModel)
    model.model = type("M", (), {"transcribe": lambda self, *a, **k: fake_result})()
    model._diarizer = None
    return model


def test_transcribe_separated_filters_hallucinations(tmp_path):
    """Segments with avg_logprob < -1.0 or compression_ratio > 2.4 are dropped."""
    audio = tmp_path / "spk.wav"
    audio.write_bytes(b"RIFF0000WAVE")

    fake_result = {"segments": [
        {"start": 0.0, "end": 2.0, "text": "Fala válida.", "avg_logprob": -0.3, "compression_ratio": 1.5},
        {"start": 2.0, "end": 4.0, "text": "ruído", "avg_logprob": -2.0, "compression_ratio": 1.2},   # low confidence
        {"start": 4.0, "end": 6.0, "text": "lalalala", "avg_logprob": -0.2, "compression_ratio": 3.0}, # repetitive
    ]}
    model = _whisper_with_fake_model(fake_result)
    out = model.transcribe_separated({"Depoente": str(audio)})
    assert len(out) == 1
    assert out[0]["text"] == "Fala válida."
    assert out[0]["speaker"] == "Depoente"


def test_transcribe_separated_skips_missing_files():
    model = _whisper_with_fake_model({"segments": []})
    out = model.transcribe_separated({"Depoente": "/path/does/not/exist.wav"})
    assert out == []
