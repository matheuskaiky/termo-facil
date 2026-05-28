from typing import Protocol


class ASRModel(Protocol):
    def transcribe(self, audio_path: str, language: str) -> list[dict]:
        """Returns a list of {start, end, text, speaker} segment dicts."""
        ...


class NERModel(Protocol):
    def extract_entities(self, text: str) -> dict:
        ...


class LLMModel(Protocol):
    def synthesize(self, text: str, entities: dict | None = None) -> str:
        ...
