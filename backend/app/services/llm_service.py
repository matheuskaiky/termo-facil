import os
import httpx
from typing import Protocol

_SYSTEM_PROMPT = (
    "Você é um escrivão policial brasileiro especializado em redigir Termos de Depoimento. "
    "Converta a transcrição literal abaixo para o formato formal de inquérito policial, "
    "na terceira pessoa, sem alterar os fatos. Seja preciso, conciso e jurídico."
)


class LLMModel(Protocol):
    def synthesize(self, text: str) -> str:
        ...


class OllamaLLM:
    def __init__(self, base_url: str, model_name: str):
        self._base_url = base_url
        self._model_name = model_name

    def synthesize(self, text: str) -> str:
        payload = {
            "model": self._model_name,
            "prompt": f"{_SYSTEM_PROMPT}\n\nTranscrição: {text}",
            "stream": False,
            "options": {"temperature": 0.0},
        }
        response = httpx.post(
            f"{self._base_url}/api/generate",
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["response"]


llm_model: LLMModel = OllamaLLM(
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434"),
    model_name=os.getenv("LLM_MODEL_NAME", "llama3"),
)
