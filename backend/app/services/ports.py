from typing import Protocol


class ASRModel(Protocol):
    def transcribe(self, audio_path: str, language: str) -> list[dict]:
        """Returns a list of {start, end, text, speaker} segment dicts."""
        ...

    def transcribe_separated(
        self, separated_paths: dict[str, str], language: str
    ) -> list[dict]:
        """
        Transcribes each speaker's pre-separated clean audio file individually.
        separated_paths: {role_label: absolute_path_to_clean_wav}
        Segments from all speakers are merged and sorted by start time.
        Caller must not delete the files before this method returns.
        """
        ...


class DiarizationModel(Protocol):
    def diarize(self, audio_path: str) -> list[tuple[float, float, str]]:
        """Returns list of (start, end, speaker_label) speaker turns from audio."""
        ...


class SeparationDiarizationModel(Protocol):
    def diarize_and_separate(self, audio_path: str) -> dict[str, str]:
        """
        Runs joint speaker diarization + speech separation (e.g. PixIT).
        Returns {role_label: absolute_path_to_clean_wav_at_16kHz}.
        Separated files have the same duration as the input — silence where the
        other speaker was active — so Whisper timestamps align to the original.
        Caller is responsible for deleting the returned temp files after use.
        """
        ...


class NERModel(Protocol):
    def extract_entities(self, text: str) -> dict:
        ...


class LLMModel(Protocol):
    def synthesize(self, text: str, entities: dict | None = None) -> str:
        ...


class SpeakerRoleModel(Protocol):
    def resolve(
        self,
        segments: list[dict],
        audio_path: str | None = None,
        known_samples: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """
        Returns {current_label: target_role} remapping.
        e.g. {"Inquiridor": "Depoente", "Depoente": "Inquiridor"} when roles are inverted.
        known_samples: {role: local_audio_path_for_embedding_comparison}
        Empty dict means no remapping needed.
        """
        ...
