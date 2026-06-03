import os
import re
from transformers import pipeline as hf_pipeline
from app.services.ports import NERModel

# ~200 words * 2.5 tokens/word ≈ 500 tokens — safely under the 512 BERT limit for dense legal text.
# Splitting at sentence boundaries avoids cutting entities in half.
_MAX_WORDS_PER_CHUNK = 200


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


def _remove_subsumed(entities: list[str]) -> list[str]:
    # Keep the longest form when one entity is contained in another.
    # e.g. "Itaú" ⊂ "Banco Itaú" → keep only "Banco Itaú".
    by_length = sorted(entities, key=len, reverse=True)
    result = []
    for ent in by_length:
        if not any(ent in longer for longer in result):
            result.append(ent)
    return result


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
        # "first" merges ## subword tokens into full words before entity grouping,
        # preventing the ## artifacts that "simple" produces when the model assigns
        # B- labels to subword continuation tokens.
        self._pipeline = hf_pipeline(
            "ner",
            model=model_name,
            aggregation_strategy="first",
        )

    def extract_entities(self, text: str) -> dict:
        return self.extract_entities_scored(text)[0]

    def extract_entities_scored(self, text: str) -> tuple[dict, list[dict]]:
        """Returns (dict {TIPO:[palavras]}, [{tipo, texto, score(%)}]).
        The score is the highest confidence the model assigned to each surviving word."""
        raw: dict = {v: [] for v in self._LABEL_MAP.values()}
        best_score: dict = {}  # word -> (tipo, score 0..1)
        for chunk in _build_chunks(text):
            for entity in self._pipeline(chunk):
                key = self._LABEL_MAP.get(entity["entity_group"])
                if not key:
                    continue
                word = entity["word"]
                if word not in raw[key]:
                    raw[key].append(word)
                score = float(entity.get("score", 0.0))
                if word not in best_score or score > best_score[word][1]:
                    best_score[word] = (key, score)
        dic = {k: _remove_subsumed(v) for k, v in raw.items()}
        surviving = {w for words in dic.values() for w in words}
        entidades = [
            {"tipo": tipo, "texto": word, "score": round(score * 100, 1)}
            for word, (tipo, score) in best_score.items()
            if word in surviving
        ]
        return dic, entidades


class _LazyLeNER:
    """Defers LeNER-Br BERT loading until the first extract_entities() call (B-6).
    BERT weights (~1.3 GB) must not be loaded by the FastAPI web workers."""
    _instance: LeNERModel | None = None

    def _ensure(self) -> LeNERModel:
        if self._instance is None:
            self._instance = LeNERModel(
                model_name=os.getenv("NER_MODEL_NAME", "pierreguillou/ner-bert-large-cased-pt-lenerbr"),
            )
        return self._instance

    def extract_entities(self, text: str) -> dict:
        return self._ensure().extract_entities(text)

    def extract_entities_scored(self, text: str) -> tuple[dict, list[dict]]:
        return self._ensure().extract_entities_scored(text)


ner_model: NERModel = _LazyLeNER()
