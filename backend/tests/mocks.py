"""
Deterministic mock adapters for the AI ports defined in app/services/ports.py.

They implement the exact Protocol signatures (ASRModel, NERModel, LLMModel,
SeparationDiarizationModel, SpeakerRoleModel) so the hexagonal pipeline can run
end-to-end without GPUs, model downloads, or a running Ollama server.

The canned data mirrors a short PT-BR police testimony so that NER/LLM assertions
have realistic entities to anchor on.
"""

from __future__ import annotations
import copy

# A two-speaker interview fragment with entities the mock NER will "find".
DEFAULT_SEGMENTS: list[dict] = [
    {"start": 0.0, "end": 3.0, "text": "O senhor poderia declarar seu nome completo?", "speaker": "Inquiridor"},
    {"start": 3.2, "end": 8.0, "text": "Eu sou João da Silva e estava na Avenida Frei Serafim no dia 10 de janeiro de 2024.", "speaker": "Depoente"},
    {"start": 8.5, "end": 11.0, "text": "O que o senhor viu naquele momento?", "speaker": "Inquiridor"},
    {"start": 11.2, "end": 16.0, "text": "Eu vi dois homens fugindo em direção ao Bairro Centro por volta das vinte horas.", "speaker": "Depoente"},
]

DEFAULT_ENTITIES: dict = {
    "PESSOAS": ["João da Silva"],
    "LOCAIS": ["Avenida Frei Serafim", "Bairro Centro"],
    "TEMPO": ["10 de janeiro de 2024", "vinte horas"],
    "LEGISLACAO": [],
    "ORGANIZACOES": [],
    "JURISPRUDENCIA": [],
}


class MockASRModel:
    """Implements ports.ASRModel — returns canned segments, no audio decoding."""

    def __init__(self, segments: list[dict] | None = None):
        self._segments = segments if segments is not None else DEFAULT_SEGMENTS

    def transcribe(self, audio_path: str, language: str = "pt") -> list[dict]:
        return copy.deepcopy(self._segments)

    def transcribe_separated(self, separated_paths: dict[str, str], language: str = "pt") -> list[dict]:
        return copy.deepcopy(self._segments)


class MockNERModel:
    """Implements ports.NERModel — returns a fixed entity dictionary."""

    def __init__(self, entities: dict | None = None):
        self._entities = entities if entities is not None else DEFAULT_ENTITIES

    def extract_entities(self, text: str) -> dict:
        return copy.deepcopy(self._entities)

    def extract_entities_scored(self, text: str) -> tuple[dict, list[dict]]:
        dic = copy.deepcopy(self._entities)
        entidades = [
            {"tipo": tipo, "texto": w, "score": 99.0}
            for tipo, words in dic.items() for w in words
        ]
        return dic, entidades


class MockLLM:
    """
    Implements ports.LLMModel — deterministic synthesis that echoes the anchored
    NER entities, so 'factual fidelity' assertions (entities present in output) hold.
    """

    def synthesize(self, text: str, entities: dict | None = None) -> str:
        nomes = ", ".join((entities or {}).get("PESSOAS", [])) or "o depoente"
        locais = ", ".join((entities or {}).get("LOCAIS", []))
        partes = [f"O depoente {nomes} prestou declarações."]
        if locais:
            partes.append(f"Os fatos ocorreram em: {locais}.")
        partes.append("Trecho não compreendido: [(Trecho Ininteligível)].")
        return " ".join(partes)


class MockSeparationDiarizer:
    """Implements ports.SeparationDiarizationModel — returns no separated tracks."""

    def diarize_and_separate(self, audio_path: str) -> dict[str, str]:
        return {}
