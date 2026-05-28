import os
from app.services.ports import DiarizationModel

# PyAnnote labels speakers as SPEAKER_00, SPEAKER_01, ...
# Map first two to the legal interview roles used throughout the system.
_PYANNOTE_LABEL_MAP: dict[str, str] = {
    "SPEAKER_00": "Inquiridor",
    "SPEAKER_01": "Depoente",
}


class PyAnnoteDiarizer:
    """
    Real speaker diarization via pyannote/speaker-diarization-3.1.
    Requires:
      1. pip install pyannote.audio
      2. HuggingFace account — accept terms for pyannote/speaker-diarization-3.1
         and pyannote/segmentation-3.0 at huggingface.co/pyannote
      3. PYANNOTE_HF_TOKEN=hf_xxx in .env
    Recommended for GPU deployments (NCAD/HPC Mandu).
    """

    def __init__(self, hf_token: str):
        self._hf_token = hf_token
        self._pipeline = None

    def _ensure_loaded(self) -> None:
        if self._pipeline is None:
            from pyannote.audio import Pipeline  # noqa: PLC0415 — lazy GPU import
            self._pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self._hf_token,
            )

    def diarize(self, audio_path: str) -> list[tuple[float, float, str]]:
        self._ensure_loaded()
        annotation = self._pipeline(audio_path)
        turns: list[tuple[float, float, str]] = []
        for segment, _, speaker in annotation.itertracks(yield_label=True):
            label = _PYANNOTE_LABEL_MAP.get(speaker, speaker)
            turns.append((segment.start, segment.end, label))
        return turns


class _LazyPyannoteDiarizer:
    """Defers PyAnnote model loading until the first diarize() call."""
    _instance: PyAnnoteDiarizer | None = None

    def diarize(self, audio_path: str) -> list[tuple[float, float, str]]:
        if self._instance is None:
            token = os.getenv("PYANNOTE_HF_TOKEN")
            if not token:
                raise RuntimeError(
                    "PYANNOTE_HF_TOKEN must be set when DIARIZATION_PROVIDER=pyannote. "
                    "Accept model terms at huggingface.co/pyannote/speaker-diarization-3.1 first."
                )
            self._instance = PyAnnoteDiarizer(hf_token=token)
        return self._instance.diarize(audio_path)


def build_diarizer() -> DiarizationModel | None:
    """
    Factory: returns the configured DiarizationModel, or None to use the gap-based heuristic.
    Controlled by DIARIZATION_PROVIDER env var: 'heuristic' (default) | 'pyannote'
    """
    provider = os.getenv("DIARIZATION_PROVIDER", "heuristic")
    if provider == "pyannote":
        return _LazyPyannoteDiarizer()
    return None
