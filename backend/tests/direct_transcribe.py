import os
import whisper

_model_cache: dict = {}

class WhisperASRModel:
    def __init__(self, model_size: str):
        if model_size not in _model_cache:
            _model_cache[model_size] = whisper.load_model(model_size)
        self.model = _model_cache[model_size]

    def transcribe(self, audio_path: str, language: str) -> list[dict]:
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        result = self.model.transcribe(audio_path, language=language)
        return result

def test_direct_transcribe():
    model = WhisperASRModel(model_size="base")
    result = model.transcribe(audio_path="./micro-machines.wav", language="en")
    print(result["text"])

test_direct_transcribe()