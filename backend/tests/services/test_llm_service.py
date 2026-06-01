"""Unit tests for llm_service — prompt construction + Ollama/vLLM adapters (HTTP mocked)."""
import pytest

from app.services import llm_service
from app.services.llm_service import _build_prompt, OllamaLLM, VLLMModel

pytestmark = pytest.mark.unit


def test_prompt_contains_legal_system_instructions():
    prompt = _build_prompt("transcrição qualquer", None)
    assert "Termos de Depoimento" in prompt
    assert "[(Trecho Ininteligível)]" in prompt          # RN-01 instruction
    assert "EXCLUSIVAMENTE as entidades" in prompt        # NER anchoring instruction


def test_prompt_injects_ner_entities_block():
    entities = {"PESSOAS": ["João da Silva"], "LOCAIS": ["Teresina"]}
    prompt = _build_prompt("texto", entities)
    assert "Entidades Factuais Identificadas" in prompt
    assert "João da Silva" in prompt
    assert "Teresina" in prompt


def test_llm_options_are_deterministic():
    # RN-01 (LGPD): temperature must be 0.0; top_p tightened to 0.1
    assert llm_service._LLM_OPTIONS == {"temperature": 0.0, "top_p": 0.1}


def test_ollama_synthesize_posts_expected_payload(mocker):
    captured = {}

    class _Resp:
        def raise_for_status(self): pass
        def json(self): return {"response": "Resumo determinístico."}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        return _Resp()

    mocker.patch.object(llm_service.httpx, "post", side_effect=fake_post)

    out = OllamaLLM("http://localhost:11434", "llama3").synthesize(
        "transcrição", entities={"PESSOAS": ["Maria"]}
    )
    assert out == "Resumo determinístico."
    assert captured["url"].endswith("/api/generate")
    assert captured["json"]["model"] == "llama3"
    assert captured["json"]["options"] == {"temperature": 0.0, "top_p": 0.1}
    assert captured["json"]["stream"] is False
    assert "Maria" in captured["json"]["prompt"]


def test_vllm_synthesize_uses_openai_completions(mocker):
    captured = {}

    class _Resp:
        def raise_for_status(self): pass
        def json(self): return {"choices": [{"text": "Saída vLLM."}]}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        return _Resp()

    mocker.patch.object(llm_service.httpx, "post", side_effect=fake_post)

    out = VLLMModel("http://hpc:8000", "llama3").synthesize("t", entities=None)
    assert out == "Saída vLLM."
    assert captured["url"].endswith("/v1/completions")
    assert captured["json"]["temperature"] == 0.0
    assert captured["json"]["top_p"] == 0.1
