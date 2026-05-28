import json
import os
import httpx
from app.services.ports import LLMModel

# RN-01 (LGPD): temperature=0.0 is a legal requirement — deterministic output only.
_SYSTEM_PROMPT = (
    "Você é um escrivão policial brasileiro especializado em redigir Termos de Depoimento. "
    "Converta a transcrição literal abaixo para o formato formal de inquérito policial, "
    "na terceira pessoa, sem alterar os fatos. Seja preciso, conciso e jurídico. "
    "Use EXCLUSIVAMENTE as entidades factuais fornecidas. "
    "Se algum trecho do áudio for ininteligível, escreva [(Trecho Ininteligível)] — jamais tente adivinhar."
)

_LLM_OPTIONS = {"temperature": 0.0, "top_p": 0.1}


def _build_prompt(text: str, entities: dict | None) -> str:
    entities_block = ""
    if entities:
        entities_block = (
            f"\n\nEntidades Factuais Identificadas (use APENAS estes dados):\n"
            f"{json.dumps(entities, ensure_ascii=False, indent=2)}"
        )
    return f"{_SYSTEM_PROMPT}{entities_block}\n\nTranscrição:\n{text}"


class OllamaLLM:
    """
    Ollama inference server — recommended for local/single-GPU dev environments.
    Model pulled with: ollama pull <LLM_MODEL_NAME>
    Server started with: ollama serve
    """

    def __init__(self, base_url: str, model_name: str):
        self._base_url = base_url
        self._model_name = model_name

    def synthesize(self, text: str, entities: dict | None = None) -> str:
        payload = {
            "model": self._model_name,
            "prompt": _build_prompt(text, entities),
            "stream": False,
            "options": _LLM_OPTIONS,
        }
        response = httpx.post(f"{self._base_url}/api/generate", json=payload, timeout=120.0)
        response.raise_for_status()
        return response.json()["response"]


class VLLMModel:
    """
    vLLM inference server via OpenAI-compatible /v1/completions API.
    Preferred for HPC/production — PagedAttention dramatically reduces VRAM fragmentation,
    enabling multiple concurrent requests on a single A100.
    Set LLM_BASE_URL to the vLLM server (e.g. http://hpc-node:8000).
    Compatible with any model served by vLLM: Llama 3, Mistral, Qwen2, Phi-3, Gemma 2, etc.
    """

    def __init__(self, base_url: str, model_name: str):
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name

    def synthesize(self, text: str, entities: dict | None = None) -> str:
        payload = {
            "model": self._model_name,
            "prompt": _build_prompt(text, entities),
            "max_tokens": 2048,
            "temperature": _LLM_OPTIONS["temperature"],
            "top_p": _LLM_OPTIONS["top_p"],
            "stream": False,
        }
        response = httpx.post(
            f"{self._base_url}/v1/completions",
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["text"]


def _build_llm_model() -> LLMModel:
    provider = os.getenv("LLM_PROVIDER", "ollama")
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    model_name = os.getenv("LLM_MODEL_NAME", "llama3")
    if provider == "vllm":
        return VLLMModel(base_url=base_url, model_name=model_name)
    return OllamaLLM(base_url=base_url, model_name=model_name)


llm_model: LLMModel = _build_llm_model()
