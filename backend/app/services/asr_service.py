import os
import whisper
from app.services.ports import ASRModel, DiarizationModel

_model_cache: dict = {}

_SPEAKER_GAP_THRESHOLD = 1.0


def _assign_speakers_heuristic(segments: list[dict]) -> list[dict]:
    """
    Gap-based fallback: alternates Inquiridor/Depoente labels whenever a pause
    longer than _SPEAKER_GAP_THRESHOLD seconds separates consecutive segments.
    No audio analysis required — operates on Whisper's timestamp output only.
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


def _merge_with_diarization(
    segments: list[dict],
    turns: list[tuple[float, float, str]],
) -> list[dict]:
    """
    Aligns diarizer speaker turns to Whisper segments by maximum time overlap.
    For each segment the speaker whose turn covers the most of its duration wins.
    """
    result = []
    for seg in segments:
        seg_start, seg_end = float(seg["start"]), float(seg["end"])
        best_speaker: str | None = None
        best_overlap = 0.0
        for t_start, t_end, speaker in turns:
            overlap = min(t_end, seg_end) - max(t_start, seg_start)
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = speaker
        result.append({
            "start": round(seg_start, 2),
            "end":   round(seg_end, 2),
            "text":  seg["text"].strip(),
            "speaker": best_speaker or "Desconhecido",
        })
    return result


class WhisperASRModel:
    """
    Whisper transcription with optional injected DiarizationModel.
    When diarizer is None, falls back to the gap-based heuristic.
    """

    def __init__(self, model_size: str, diarizer: DiarizationModel | None = None):
        if model_size not in _model_cache:
            _model_cache[model_size] = whisper.load_model(model_size)
        self.model = _model_cache[model_size]
        self._diarizer = diarizer

    def transcribe(self, audio_path: str, language: str) -> list[dict]:
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        result = self.model.transcribe(audio_path, language=language)
        if self._diarizer:
            turns = self._diarizer.diarize(audio_path)
            return _merge_with_diarization(result["segments"], turns)
        return _assign_speakers_heuristic(result["segments"])


class _LazyWhisperASR:
    """Defers Whisper weight loading until the first transcribe() call."""

    def __init__(self, diarizer: DiarizationModel | None = None):
        self._diarizer = diarizer
        self._instance: WhisperASRModel | None = None

    def transcribe(self, audio_path: str, language: str) -> list[dict]:
        if self._instance is None:
            self._instance = WhisperASRModel(
                model_size=os.getenv("WHISPER_MODEL_SIZE", "base"),
                diarizer=self._diarizer,
            )
        return self._instance.transcribe(audio_path, language)


def _build_asr_model() -> ASRModel:
    from app.services.diarization_service import build_diarizer  # late import avoids circular
    diarizer = build_diarizer()
    return _LazyWhisperASR(diarizer=diarizer)


asr_model: ASRModel = _build_asr_model()
