import os
import whisper
from typing import Protocol

_model_cache: dict = {}

# Gap (seconds) between Whisper segments that suggests a speaker change.
# This is a simple heuristic — replace with PyAnnote for real diarisation.
_SPEAKER_GAP_THRESHOLD = 1.0


def _assign_speakers(segments: list[dict]) -> list[dict]:
    """
    Alternates between two speaker labels whenever a pause longer than
    _SPEAKER_GAP_THRESHOLD seconds is detected between consecutive segments.
    Labels: 'Inquiridor' / 'Depoente' to match the legal interview context.
    """
    labels = ["Inquiridor", "Depoente"]
    current = 0
    prev_end = 0.0
    result = []
    for seg in segments:
        if seg["start"] - prev_end > _SPEAKER_GAP_THRESHOLD:
            current = 1 - current
        result.append({
            "start": round(seg["start"], 2),
            "end":   round(seg["end"],   2),
            "text":  seg["text"].strip(),
            "speaker": labels[current],
        })
        prev_end = seg["end"]
    return result


class ASRModel(Protocol):
    def transcribe(self, audio_path: str, language: str) -> list[dict]:
        """Returns a list of {start, end, text, speaker} segment dicts."""
        ...


class WhisperASRModel:
    def __init__(self, model_size: str):
        if model_size not in _model_cache:
            _model_cache[model_size] = whisper.load_model(model_size)
        self.model = _model_cache[model_size]

    def transcribe(self, audio_path: str, language: str) -> list[dict]:
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        result = self.model.transcribe(audio_path, language=language)
        return _assign_speakers(result["segments"])


asr_model: ASRModel = WhisperASRModel(model_size=os.getenv("WHISPER_MODEL_SIZE", "base"))
