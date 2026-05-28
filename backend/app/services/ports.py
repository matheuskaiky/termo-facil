from typing import Protocol


class ASRModel(Protocol):
    def transcribe(self, audio_path: str, language: str) -> list[dict]:
        """Returns a list of {start, end, text, speaker} segment dicts."""
        ...


class DiarizationModel(Protocol):
    def diarize(self, audio_path: str) -> list[tuple[float, float, str]]:
        """Returns list of (start, end, speaker_label) speaker turns from audio."""
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
