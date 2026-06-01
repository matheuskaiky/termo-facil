"""
Benchmark NER (LeNER-Br) — Fase 20, Issue #29

Runs the REAL LeNER-Br model over annotated sentences and computes token-level
F1 / Precision / Recall with seqeval against a BIO-tagged ground truth.

The dataset is small (illustrative); for the full US-03 acceptance (F1 ≥ 0.85)
a larger annotated legal corpus is needed. The number produced here is real.

Usage:
  cd backend
  python scripts/benchmark_ner.py [--model <hf_model>]
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS_DIR = os.path.join(_BACKEND, "benchmarks", "results")

# Maps the model's output dict keys → the tag types used in the ground truth.
TYPE_MAP = {"PESSOAS": "PESSOA", "LOCAIS": "LOCAL", "LEGISLACAO": "LEGISLACAO", "TEMPO": "DATA"}

TEST_DATASET = [
    {
        "text": "João da Silva foi acusado de roubo em São Paulo.",
        "entities": ["B-PESSOA", "I-PESSOA", "I-PESSOA", "O", "O", "O", "O", "O", "B-LOCAL", "I-LOCAL"],
    },
    {
        # tokens: A | Lei | 8.072/1990 | trata | de | crimes | hediondos | no | Brasil.
        "text": "A Lei 8.072/1990 trata de crimes hediondos no Brasil.",
        "entities": ["O", "B-LEGISLACAO", "I-LEGISLACAO", "O", "O", "O", "O", "O", "B-LOCAL"],
    },
    {
        # tokens: Maria | foi | ouvida | em | 15 | de | maio | de | 2024.
        "text": "Maria foi ouvida em 15 de maio de 2024.",
        "entities": ["B-PESSOA", "O", "O", "O", "B-DATA", "I-DATA", "I-DATA", "I-DATA", "I-DATA"],
    },
]


def _norm(token: str) -> str:
    return re.sub(r"[^\wÀ-ÿ]", "", token).lower()


def _align_to_bio(text: str, result: dict) -> list[str]:
    tokens = text.split()
    norm = [_norm(t) for t in tokens]
    bio = ["O"] * len(tokens)
    for type_key, entities in result.items():
        tag = TYPE_MAP.get(type_key)
        if not tag:
            continue
        for ent in entities:
            ent_words = [_norm(w) for w in ent.split() if _norm(w)]
            if not ent_words:
                continue
            for i in range(len(norm) - len(ent_words) + 1):
                if norm[i:i + len(ent_words)] == ent_words:
                    bio[i] = f"B-{tag}"
                    for j in range(1, len(ent_words)):
                        bio[i + j] = f"I-{tag}"
                    break
    return bio


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=os.getenv("NER_MODEL_NAME", "pierreguillou/ner-bert-large-cased-pt-lenerbr"))
    args = parser.parse_args()

    try:
        from seqeval.metrics import classification_report, f1_score, precision_score, recall_score
    except ImportError:
        print("ERRO: seqeval não instalado. pip install seqeval")
        sys.exit(1)
    from app.services.ner_service import LeNERModel

    print("=" * 70)
    print(f"NER Benchmark — LeNER-Br ({args.model}) (Issue #29)")
    print("=" * 70)
    print("Carregando modelo... (pode baixar ~1.3GB no primeiro uso)")
    model = LeNERModel(model_name=args.model)

    y_true, y_pred = [], []
    for test in TEST_DATASET:
        result = model.extract_entities(test["text"])
        predicted = _align_to_bio(test["text"], result)
        y_true.append(test["entities"])
        y_pred.append(predicted)
        print(f"  ✓ {test['text'][:48]}...")
        print(f"      esperado:  {test['entities']}")
        print(f"      previsto:  {predicted}")

    f1 = float(f1_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred))
    recall = float(recall_score(y_true, y_pred))

    print("\n| Métrica    | Score   |")
    print("|------------|---------|")
    print(f"| F1-Score   | {f1:6.1%} |")
    print(f"| Precision  | {precision:6.1%} |")
    print(f"| Recall     | {recall:6.1%} |")
    print("\n" + classification_report(y_true, y_pred))

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "ner.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "model": args.model, "f1": f1, "precision": precision, "recall": recall,
            "num_samples": len(TEST_DATASET),
        }, fh, ensure_ascii=False, indent=2)
    print("\nResultados salvos em benchmarks/results/ner.json")


if __name__ == "__main__":
    main()
