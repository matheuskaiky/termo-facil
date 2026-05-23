import os
import whisper
from typing import Protocol

_model_cache: dict = {}


class ASRModel(Protocol):
    def transcribe(self, audio_path: str, language: str) -> str:
        ...


class WhisperASRModel:
    def __init__(self, model_size: str):
        if model_size not in _model_cache:
            _model_cache[model_size] = whisper.load_model(model_size)
        self.model = _model_cache[model_size]

    def transcribe(self, audio_path: str, language: str) -> str:
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        result = self.model.transcribe(audio_path, language=language)
        return result["text"]


asr_model: ASRModel = WhisperASRModel(model_size=os.getenv("WHISPER_MODEL_SIZE", "base"))


# ====================================================
#                       Testes
# ====================================================

def main():
    audio_path = "../sample_audio/micro-machines.wav"
    texto = asr_model.transcribe(audio_path, language="pt")
    print(texto)

if __name__ == "__main__":
    main()
