import logging
import os
from app.services.ports import DiarizationModel, SeparationDiarizationModel

logger = logging.getLogger(__name__)

# PyAnnote labels speakers as SPEAKER_00, SPEAKER_01, ...
# Map first two to the legal interview roles used throughout the system.
_PYANNOTE_LABEL_MAP: dict[str, str] = {
    "SPEAKER_00": "Inquiridor",
    "SPEAKER_01": "Depoente",
}


# ── Alignment-based diarizer (used inside asr_service for the heuristic flow) ──

class PyAnnoteDiarizer:
    """
    Speaker diarization via pyannote/speaker-diarization-3.1.
    Returns speaker turns for time-based alignment with Whisper segments.
    Requires PYANNOTE_HF_TOKEN + accepted model terms.
    """

    def __init__(self, hf_token: str):
        self._hf_token = hf_token
        self._pipeline = None

    def _ensure_loaded(self) -> None:
        if self._pipeline is None:
            from pyannote.audio import Pipeline  # noqa: PLC0415
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
    """Defers PyAnnote loading until the first diarize() call."""
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


# ── Separation-based diarizer (PixIT — used directly by the Celery task) ──

class PyAnnoteSeparationDiarizer:
    """
    Joint speaker diarization + speech separation via pyannote/speech-separation-ami-1.0 (PixIT).

    Requires:
      1. pip install pyannote.audio[separation]==3.3.2
      2. PYANNOTE_HF_TOKEN set in .env
      3. Accept user terms at huggingface.co/pyannote/speech-separation-ami-1.0
         and huggingface.co/pyannote/separation-ami-1.0

    Output files are full-duration WAVs at 16kHz — silence where the other speaker is active.
    This preserves original timestamps for downstream Whisper transcription.
    GPU strongly recommended: pipeline is automatically sent to CUDA if available.
    """

    def __init__(self, hf_token: str):
        self._hf_token = hf_token
        self._pipeline = None

    def _ensure_loaded(self) -> None:
        if self._pipeline is None:
            import torch
            from pyannote.audio import Pipeline  # noqa: PLC0415
            self._pipeline = Pipeline.from_pretrained(
                "pyannote/speech-separation-ami-1.0",
                use_auth_token=self._hf_token,
            )
            cuda_available = torch.cuda.is_available()
            device = torch.device("cuda" if cuda_available else "cpu")
            logger.info("PixIT pipeline loading on device=%s (CUDA available: %s)", device, cuda_available)
            self._pipeline.to(device)
            logger.info("PixIT pipeline ready.")

    def diarize_and_separate(self, audio_path: str) -> dict[str, str]:
        """
        Returns {role_label: temp_wav_path}.
        pyannote resamples input to 16kHz automatically; sources are always at 16kHz.
        Caller must delete the returned files after use.
        """
        import tempfile
        import numpy as np
        import scipy.io.wavfile  # noqa: PLC0415

        self._ensure_loaded()
        diarization, sources = self._pipeline(audio_path)

        result: dict[str, str] = {}
        for s, speaker in enumerate(diarization.labels()):
            # Keep raw PyAnnote labels (SPEAKER_00, SPEAKER_01, ...).
            # Role assignment (Inquiridor / Depoente) is the SpeakerRoleResolver's job.
            audio_data = sources.data[:, s]
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            # Clip to [-1, 1] — scipy float32 WAV requirement
            audio_data = np.clip(audio_data, -1.0, 1.0)
            tmp = tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False, prefix=f"sep_{speaker}_"
            )
            tmp.close()
            scipy.io.wavfile.write(tmp.name, 16000, audio_data)
            result[speaker] = tmp.name

        return result


class _LazyPyAnnoteSeparationDiarizer:
    """Defers PixIT pipeline loading until the first diarize_and_separate() call."""
    _instance: PyAnnoteSeparationDiarizer | None = None

    def diarize_and_separate(self, audio_path: str) -> dict[str, str]:
        if self._instance is None:
            token = os.getenv("PYANNOTE_HF_TOKEN")
            if not token:
                raise RuntimeError(
                    "PYANNOTE_HF_TOKEN must be set when DIARIZATION_PROVIDER=pyannote. "
                    "Accept model terms at hf.co/pyannote/speech-separation-ami-1.0 first."
                )
            self._instance = PyAnnoteSeparationDiarizer(hf_token=token)
        return self._instance.diarize_and_separate(audio_path)


def build_diarizer_for(provider: str) -> SeparationDiarizationModel | None:
    """Explicit factory (used by the Dev/Debug module): 'pyannote' → PixIT,
    anything else → None (gap-based heuristic)."""
    if provider == "pyannote":
        return _LazyPyAnnoteSeparationDiarizer()
    return None


def build_diarizer() -> SeparationDiarizationModel | None:
    """
    Factory: returns a SeparationDiarizationModel (PixIT) when DIARIZATION_PROVIDER=pyannote,
    or None to fall back to the gap-based heuristic inside asr_service.
    """
    return build_diarizer_for(os.getenv("DIARIZATION_PROVIDER", "heuristic"))
