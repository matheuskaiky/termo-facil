import logging
import os
import whisper
from app.services.ports import ASRModel, DiarizationModel

logger = logging.getLogger(__name__)

_model_cache: dict = {}

_SPEAKER_GAP_THRESHOLD = 1.0
_LOGPROB_THRESHOLD     = -1.0   # Whisper avg_logprob: below this → likely hallucination
_COMPRESSION_RATIO_MAX =  2.4   # above this → repetitive/hallucinated text


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

    def transcribe_separated(
        self, separated_paths: dict[str, str], language: str = "pt"
    ) -> list[dict]:
        """
        Transcribes each speaker's pre-separated clean audio file individually.
        Each file has the same duration as the original — silent where the other
        speaker was active — so Whisper timestamps align to the original recording.
        All segments are merged and sorted chronologically by start time.
        """
        all_segments: list[dict] = []
        for role, audio_path in separated_paths.items():
            if not os.path.isfile(audio_path):
                continue
            result = self.model.transcribe(
                audio_path,
                language=language,
                condition_on_previous_text=False,  # prevents cross-segment hallucination
                no_speech_threshold=0.6,           # suppress near-silent output
            )
            for seg in result["segments"]:
                avg_logprob       = seg.get("avg_logprob", 0.0)
                compression_ratio = seg.get("compression_ratio", 1.0)
                if avg_logprob < _LOGPROB_THRESHOLD or compression_ratio > _COMPRESSION_RATIO_MAX:
                    logger.debug(
                        "Segment discarded (hallucination filter): speaker=%s start=%.2fs "
                        "avg_logprob=%.3f compression_ratio=%.3f text=%r",
                        role, seg["start"], avg_logprob, compression_ratio, seg["text"][:40],
                    )
                    continue
                all_segments.append({
                    "start": round(float(seg["start"]), 2),
                    "end":   round(float(seg["end"]),   2),
                    "text":  seg["text"].strip(),
                    "speaker": role,
                })
        all_segments.sort(key=lambda s: s["start"])
        return all_segments


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

    def transcribe_separated(
        self, separated_paths: dict[str, str], language: str = "pt"
    ) -> list[dict]:
        if self._instance is None:
            self._instance = WhisperASRModel(
                model_size=os.getenv("WHISPER_MODEL_SIZE", "base"),
                diarizer=self._diarizer,
            )
        return self._instance.transcribe_separated(separated_paths, language)


def _build_asr_model() -> ASRModel:
    # Speaker separation (PixIT) is orchestrated at the task level via build_diarizer().
    # The ASR service itself uses the heuristic (diarizer=None) as its internal fallback.
    return _LazyWhisperASR(diarizer=None)


asr_model: ASRModel = _build_asr_model()
