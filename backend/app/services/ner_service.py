import os
from typing import Protocol
from transformers import pipeline as hf_pipeline


class NERModel(Protocol):
    def extract_entities(self, text: str) -> dict:
        ...


class LeNERModel:
    # Maps LeNER-Br entity groups to the dicionario_ner schema
    _LABEL_MAP = {
        "PESSOA":        "PESSOAS",
        "LOCAL":         "LOCAIS",
        "ORGANIZACAO":   "ORGANIZACOES",
        "TEMPO":         "TEMPO",
        "LEGISLACAO":    "LEGISLACAO",
        "JURISPRUDENCIA": "JURISPRUDENCIA",
    }

    def __init__(self, model_name: str):
        # truncation=True silently truncates at 512 tokens (BERT limit).
        # For depositions longer than ~400 words, entities near the end may be missed.
        self._pipeline = hf_pipeline(
            "ner",
            model=model_name,
            aggregation_strategy="simple",
            truncation=True,
        )

    def extract_entities(self, text: str) -> dict:
        result: dict = {v: [] for v in self._LABEL_MAP.values()}
        for entity in self._pipeline(text):
            key = self._LABEL_MAP.get(entity["entity_group"])
            if key and entity["word"] not in result[key]:
                result[key].append(entity["word"])
        return result


ner_model: NERModel = LeNERModel(
    model_name=os.getenv("NER_MODEL_NAME", "alfaneo/lener_br"),
)
