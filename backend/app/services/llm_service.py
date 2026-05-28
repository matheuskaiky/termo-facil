import json
import os
import httpx
from app.services.ports import LLMModel

_SYSTEM_PROMPT = (
    "Você é um escrivão policial brasileiro especializado em redigir Termos de Depoimento. "
    "Converta a transcrição literal abaixo para o formato formal de inquérito policial, "
    "na terceira pessoa, sem alterar os fatos. Seja preciso, conciso e jurídico. "
    "Use EXCLUSIVAMENTE as entidades factuais fornecidas. "
    "Se algum trecho do áudio for ininteligível, escreva [(Trecho Ininteligível)] — jamais tente adivinhar."
)


class OllamaLLM:
    def __init__(self, base_url: str, model_name: str):
        self._base_url = base_url
        self._model_name = model_name

    def synthesize(self, text: str, entities: dict | None = None) -> str:
        entities_block = ""
        if entities:
            entities_block = f"\n\nEntidades Factuais Identificadas (use APENAS estes dados):\n{json.dumps(entities, ensure_ascii=False, indent=2)}"
        payload = {
            "model": self._model_name,
            "prompt": f"{_SYSTEM_PROMPT}{entities_block}\n\nTranscrição:\n{text}",
            "stream": False,
            "options": {"temperature": 0.0, "top_p": 0.1},
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
