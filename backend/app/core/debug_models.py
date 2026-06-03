"""
Catálogo de modelos do módulo Dev/Debug — INTENCIONALMENTE separado do config de
produção (`config.py`/serviços) para não confundir "modelos disponíveis para teste"
com "modelos em uso na produção".

Define:
- quais modelos podem ser comparados em cada etapa (ASR/NER/LLM/diarização);
- a opção "Não testar" (SKIP) por etapa;
- um health-check que valida a existência/funcionamento de cada modelo;
- a pasta local de pesos (`models_debug/`, cujo conteúdo é gitignorado).

Nenhuma função aqui levanta exceção: o health-check degrada com elegância
(modelo "indisponível" + motivo), nunca derruba o endpoint.
"""
from __future__ import annotations

import os

import httpx

# Pasta para pesos locais de teste (o conteúdo é ignorado pelo git; ver .gitignore).
MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models_debug"
)

# Valor sentinela para "Não testar" (pula a etapa).
SKIP = "skip"
SKIP_OPTION = {"id": SKIP, "label": "Não testar", "tipo": None, "recurso": None}

ASR_MODELS = [
    {"id": "whisper-tiny", "label": "Whisper tiny", "tipo": "asr", "recurso": "tiny"},
    {"id": "whisper-base", "label": "Whisper base", "tipo": "asr", "recurso": "base"},
    {"id": "whisper-small", "label": "Whisper small", "tipo": "asr", "recurso": "small"},
    {"id": "whisper-medium", "label": "Whisper medium", "tipo": "asr", "recurso": "medium"},
    {"id": "whisper-large-v3", "label": "Whisper large-v3", "tipo": "asr", "recurso": "large-v3"},
]

NER_MODELS = [
    {
        "id": "lener-br",
        "label": "LeNER-Br",
        "tipo": "ner",
        "recurso": os.getenv("NER_MODEL_NAME", "pierreguillou/ner-bert-large-cased-pt-lenerbr"),
    },
]

DIARIZACAO = [
    {"id": "heuristic", "label": "Heurística (gap)", "tipo": "diarizacao", "recurso": "heuristic"},
    {"id": "pyannote", "label": "PixIT (separação)", "tipo": "diarizacao", "recurso": "pyannote"},
]


def llm_models() -> list[dict]:
    """Descobre dinamicamente os modelos puxados no Ollama (`/api/tags`).
    Cai para o modelo configurado quando o servidor não responde."""
    base = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    try:
        r = httpx.get(f"{base}/api/tags", timeout=3.0)
        r.raise_for_status()
        models = r.json().get("models", [])
        if models:
            return [
                {"id": m["name"], "label": m["name"], "tipo": "llm", "recurso": m["name"]}
                for m in models
            ]
    except Exception:
        pass
    name = os.getenv("LLM_MODEL_NAME", "llama3")
    return [{"id": name, "label": name, "tipo": "llm", "recurso": name}]


# ── Resolução id → recurso (consumida pelas factories de serviço) ───────────────
def resolve_asr(model_id: str) -> str | None:
    return next((m["recurso"] for m in ASR_MODELS if m["id"] == model_id), None)


def resolve_ner(model_id: str) -> str | None:
    return next((m["recurso"] for m in NER_MODELS if m["id"] == model_id), None)


def resolve_llm(model_id: str) -> str | None:
    # LLM é dinâmico: o próprio id já é o nome do modelo no Ollama.
    if model_id in (None, SKIP):
        return None
    return model_id


def resolve_diarizacao(model_id: str) -> str:
    return model_id if model_id in ("heuristic", "pyannote") else "heuristic"


# ── Health-check (nunca levanta) ────────────────────────────────────────────────
def _check_whisper(size: str) -> dict:
    try:
        import whisper  # type: ignore
        if size in whisper.available_models():
            return {"available": True, "motivo": "disponível"}
        return {"available": False, "motivo": f"tamanho '{size}' desconhecido"}
    except Exception as exc:  # whisper não instalado
        return {"available": False, "motivo": f"whisper indisponível: {exc}"}


def _check_ner(_recurso: str) -> dict:
    try:
        import transformers  # noqa: F401
        import torch  # noqa: F401
        return {"available": True, "motivo": "transformers/torch disponíveis"}
    except Exception as exc:
        return {"available": False, "motivo": f"transformers/torch ausentes: {exc}"}


def _check_llm() -> dict:
    base = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    try:
        r = httpx.get(f"{base}/api/tags", timeout=3.0)
        r.raise_for_status()
        return {"available": True, "motivo": "ollama respondeu"}
    except Exception as exc:
        return {"available": False, "motivo": f"ollama indisponível: {exc}"}


def _check_diarizacao(recurso: str) -> dict:
    if recurso == "heuristic":
        return {"available": True, "motivo": "sem dependências"}
    if os.getenv("PYANNOTE_HF_TOKEN"):
        return {"available": True, "motivo": "token presente"}
    return {"available": False, "motivo": "defina PYANNOTE_HF_TOKEN e aceite os termos em hf.co"}


def health_check() -> dict:
    """Valida cada modelo do catálogo e devolve disponibilidade + motivo."""
    llm_status = _check_llm()
    return {
        "asr": [{**m, **_check_whisper(m["recurso"])} for m in ASR_MODELS],
        "ner": [{**m, **_check_ner(m["recurso"])} for m in NER_MODELS],
        "llm": [{**m, **llm_status} for m in llm_models()],
        "diarizacao": [{**m, **_check_diarizacao(m["recurso"])} for m in DIARIZACAO],
    }


def catalogo() -> dict:
    """Catálogo bruto (sem health-check) + opção SKIP por etapa — para popular os comboboxes."""
    return {
        "asr": ASR_MODELS + [SKIP_OPTION],
        "ner": NER_MODELS + [SKIP_OPTION],
        "llm": llm_models() + [SKIP_OPTION],
        "diarizacao": DIARIZACAO,
    }
