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
