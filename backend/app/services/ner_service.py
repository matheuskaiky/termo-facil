import os
import re
from typing import Protocol
from transformers import pipeline as hf_pipeline

# ~350 words * 1.3 tokens/word ≈ 455 tokens — safely under the 512 BERT limit.
# Splitting at sentence boundaries avoids cutting entities in half.
_MAX_WORDS_PER_CHUNK = 350


def _build_chunks(text: str) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks: list[str] = []
    current: list[str] = []
    count = 0
    for sentence in sentences:
        words = sentence.split()
        if count + len(words) > _MAX_WORDS_PER_CHUNK and current:
            chunks.append(" ".join(current))
            current = words
            count = len(words)
        else:
            current.extend(words)
            count += len(words)
    if current:
        chunks.append(" ".join(current))
    return chunks


class NERModel(Protocol):
    def extract_entities(self, text: str) -> dict:
        ...


class LeNERModel:
    _LABEL_MAP = {
        "PESSOA":         "PESSOAS",
        "LOCAL":          "LOCAIS",
        "ORGANIZACAO":    "ORGANIZACOES",
        "TEMPO":          "TEMPO",
        "LEGISLACAO":     "LEGISLACAO",
        "JURISPRUDENCIA": "JURISPRUDENCIA",
    }

    def __init__(self, model_name: str):
        self._pipeline = hf_pipeline(
            "ner",
            model=model_name,
            aggregation_strategy="simple",
        )

    def extract_entities(self, text: str) -> dict:
        result: dict = {v: [] for v in self._LABEL_MAP.values()}
        for chunk in _build_chunks(text):
            for entity in self._pipeline(chunk):
                key = self._LABEL_MAP.get(entity["entity_group"])
                if key and entity["word"] not in result[key]:
                    result[key].append(entity["word"])
        return result


ner_model: NERModel = LeNERModel(
    model_name=os.getenv("NER_MODEL_NAME", "alfaneo/lener_br"),
)
