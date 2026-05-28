import os
import whisper
from app.services.ports import ASRModel

_model_cache: dict = {}

# Gap (seconds) between Whisper segments that suggests a speaker change.
# Used only by the heuristic fallback; replaced by PyAnnote when DIARIZATION_PROVIDER=pyannote.
_SPEAKER_GAP_THRESHOLD = 1.0

# PyAnnote labels speakers as SPEAKER_00, SPEAKER_01, ... Map first two to legal interview roles.
_PYANNOTE_LABEL_MAP: dict[str, str] = {
    "SPEAKER_00": "Inquiridor",
    "SPEAKER_01": "Depoente",
}


def _assign_speakers_heuristic(segments: list[dict]) -> list[dict]:
    """
    Alternates between two speaker labels whenever a pause longer than
    _SPEAKER_GAP_THRESHOLD seconds is detected. Fallback when PyAnnote is unavailable.
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


def _merge_whisper_with_pyannote(segments: list[dict], diarization) -> list[dict]:
    """
    Aligns PyAnnote speaker turns to Whisper segments by maximum overlap.
    For each Whisper segment, the speaker whose turn covers the most time wins.
    """
    result = []
    for seg in segments:
        seg_start, seg_end = float(seg["start"]), float(seg["end"])
        best_speaker: str | None = None
        best_overlap = 0.0
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            overlap = min(turn.end, seg_end) - max(turn.start, seg_start)
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = speaker
        label = _PYANNOTE_LABEL_MAP.get(best_speaker, best_speaker or "Desconhecido")
        result.append({
            "start": round(seg_start, 2),
            "end":   round(seg_end, 2),
            "text":  seg["text"].strip(),
            "speaker": label,
        })
    return result


class WhisperASRModel:
    def __init__(self, model_size: str):
        if model_size not in _model_cache:
            _model_cache[model_size] = whisper.load_model(model_size)
        self.model = _model_cache[model_size]

    def transcribe(self, audio_path: str, language: str) -> list[dict]:
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        result = self.model.transcribe(audio_path, language=language)
        return _assign_speakers_heuristic(result["segments"])


class WhisperWithPyannoteDiarizer:
    """
    Whisper transcription + PyAnnote speaker-diarization-3.1 for real multi-speaker separation.
    Requires PYANNOTE_HF_TOKEN (accept pyannote/speaker-diarization-3.1 terms at hf.co first).
    Recommended for HPC/GPU deployments; falls back to heuristic on import failure.
    """

    def __init__(self, model_size: str, hf_token: str):
        self._model_size = model_size
        self._hf_token = hf_token
        self._whisper: whisper.Whisper | None = None
        self._pipeline = None

    def _ensure_loaded(self) -> None:
        if self._whisper is None:
            if self._model_size not in _model_cache:
                _model_cache[self._model_size] = whisper.load_model(self._model_size)
            self._whisper = _model_cache[self._model_size]
        if self._pipeline is None:
            from pyannote.audio import Pipeline  # noqa: PLC0415 — lazy import
            self._pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self._hf_token,
            )

    def transcribe(self, audio_path: str, language: str) -> list[dict]:
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        self._ensure_loaded()
        result = self._whisper.transcribe(audio_path, language=language)
        diarization = self._pipeline(audio_path)
        return _merge_whisper_with_pyannote(result["segments"], diarization)


class _LazyWhisperASR:
    """Defers Whisper weight loading until the first transcribe() call."""
    _instance: WhisperASRModel | None = None

    def transcribe(self, audio_path: str, language: str) -> list[dict]:
        if self._instance is None:
            self._instance = WhisperASRModel(model_size=os.getenv("WHISPER_MODEL_SIZE", "base"))
        return self._instance.transcribe(audio_path, language)


class _LazyPyannoteASR:
    """Defers Whisper + PyAnnote loading until the first transcribe() call."""
    _instance: WhisperWithPyannoteDiarizer | None = None

    def transcribe(self, audio_path: str, language: str) -> list[dict]:
        if self._instance is None:
            token = os.getenv("PYANNOTE_HF_TOKEN")
            if not token:
                raise RuntimeError(
                    "PYANNOTE_HF_TOKEN must be set when DIARIZATION_PROVIDER=pyannote. "
                    "Accept pyannote/speaker-diarization-3.1 terms at huggingface.co first."
                )
            self._instance = WhisperWithPyannoteDiarizer(
                model_size=os.getenv("WHISPER_MODEL_SIZE", "base"),
                hf_token=token,
            )
        return self._instance.transcribe(audio_path, language)


def _build_asr_model() -> ASRModel:
    provider = os.getenv("DIARIZATION_PROVIDER", "heuristic")
    if provider == "pyannote":
        return _LazyPyannoteASR()
    return _LazyWhisperASR()


asr_model: ASRModel = _build_asr_model()
