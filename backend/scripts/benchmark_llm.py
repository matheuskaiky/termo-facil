"""
Benchmark Comparativo de LLMs para Síntese Jurídica — Fase 20, Issue #30

Avalia qualidade e desempenho de diferentes LLMs para síntese de depoimentos.
Critérios: fidelidade factual, latência, tamanho da resposta.

Uso:
  cd backend
  python scripts/benchmark_llm.py --models llama3,mistral
"""

import sys
import os
import time
import argparse
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.llm_service import OllamaLLM


# Fixture: transcrição + NER para teste
TEST_CASE = {
    "transcript": (
        "Inquiridor: O senhor estava presente no local dos fatos? "
        "Depoente: Sim, estava sim. Vi quando o sujeito chegou correndo pela rua. "
        "Inquiridor: Pode descrever a aparência dele? "
        "Depoente: Era um rapaz de uns vinte e cinco anos, moreno, cabelos curtos, "
        "usando uma jaqueta preta."
    ),
    "ner_entities": {
        "PESSOAS": ["Inquiridor", "Depoente", "sujeito", "rapaz"],
        "LOCAIS": ["rua"],
        "DATAS": [],
        "LEGISLACAO": []
    }
}


def benchmark_llm(model_name: str, base_url: str = "http://localhost:11434"):
    """Avalia um modelo LLM específico."""
    print(f"\n📊 Testando LLM: {model_name}")

    try:
        llm = OllamaLLM(model_name=model_name, base_url=base_url)
    except Exception as e:
        print(f"  ❌ Erro ao conectar: {e}")
        return None

    try:
        start = time.perf_counter()
        synthesis = llm.synthesize(
            TEST_CASE["transcript"],
            entities=TEST_CASE["ner_entities"],
        )
        elapsed = time.perf_counter() - start

        # Conta entidades que aparecem na síntese
        all_entities = []
        for entity_list in TEST_CASE["ner_entities"].values():
            all_entities.extend(entity_list)

        found_entities = sum(1 for entity in all_entities if entity.lower() in synthesis.lower())
        total_entities = len(all_entities)
        factual_fidelity = found_entities / total_entities if total_entities > 0 else 0

        result = {
            "model": model_name,
            "latency_sec": elapsed,
            "response_length": len(synthesis),
            "entities_found": found_entities,
            "total_entities": total_entities,
            "factual_fidelity": factual_fidelity,
            "sample_output": synthesis[:200] + "..." if len(synthesis) > 200 else synthesis
        }

        print(f"  ✓ Latência: {elapsed:.2f}s")
        print(f"  ✓ Tamanho resposta: {len(synthesis)} chars")
        print(f"  ✓ Fidelidade factual: {factual_fidelity:.1%} ({found_entities}/{total_entities})")

        return result

    except Exception as e:
        print(f"  ❌ Erro ao executar síntese: {e}")
        return None


def main():
    """Executa benchmark comparativo de LLMs."""
    parser = argparse.ArgumentParser(description="Benchmark de LLMs para síntese jurídica")
    parser.add_argument(
        "--models",
        default="llama3",
        help="Lista de modelos separados por vírgula (ex: llama3,mistral,phi3)"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:11434",
        help="URL da API Ollama"
    )

    args = parser.parse_args()
    model_list = [m.strip() for m in args.models.split(",")]

    print("=" * 70)
    print("LLM Benchmark — Síntese Jurídica (Issue #30)")
    print("=" * 70)
    print(f"Base URL: {args.url}")
    print(f"Modelos: {', '.join(model_list)}")

    results = []
    for model_name in model_list:
        result = benchmark_llm(model_name, args.url)
        if result:
            results.append(result)

    # Persist results (or a 'skipped' marker) for documentation/CI traceability.
    results_dir = os.path.join(os.path.dirname(__file__), "..", "benchmarks", "results")
    os.makedirs(results_dir, exist_ok=True)
    with open(os.path.join(results_dir, "llm.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {"status": "ok" if results else "skipped — Ollama unavailable", "results": results},
            fh, ensure_ascii=False, indent=2,
        )

    if results:
        print("\n" + "=" * 70)
        print("RESULTADOS COMPARATIVOS")
        print("=" * 70)
        print(f"\n| Modelo      | Latência (s) | Tamanho (chars) | Fidelidade | ")
        print("|-------------|--------------|-----------------|-----------|")

        for r in results:
            print(
                f"| {r['model']:11} | {r['latency_sec']:12.3f} | {r['response_length']:15} | {r['factual_fidelity']:8.1%} |"
            )

        print("\n" + "=" * 70)
        print("AMOSTRAS DE SAÍDA")
        print("=" * 70)

        for r in results:
            print(f"\n{r['model']}:")
            print(f"  {r['sample_output']}")

        print("\n✅ Benchmark concluído.")
        print("💡 Recomendação: Adicione estes resultados a NOTAS_PIBITI.md")
        print("   com análise de trade-offs entre latência e fidelidade.")

    else:
        print("\n❌ Nenhum resultado foi gerado.")
        print("💡 Dica: Certifique-se de que Ollama está rodando:")
        print("   ollama serve")
        print("   ollama pull llama3")


if __name__ == "__main__":
    main()
