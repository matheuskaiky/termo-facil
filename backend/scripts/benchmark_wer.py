"""
Benchmark ASR (Whisper) — Fase 20, Issue #28

Runs REAL Whisper inference over audio files and reports measurable performance:
  - latency (s) and RTF (real-time factor = processing_time / audio_duration)
  - WER/CER, computed ONLY for files that ship a ground-truth reference

Dataset layout (optional ground truth):
  backend/benchmarks/data/<name>.wav          audio to transcribe
  backend/benchmarks/data/<name>.ref.txt      (optional) reference transcript

If no labeled audio is present, the script still transcribes the bundled sample
(tests/micro-machines.wav) to measure real latency/RTF and emit the hypothesis,
and reports WER as N/A. Producing a true WER number for PT-BR police testimony
requires a labeled audio corpus — that is the pending input for full US-02 validation.

Usage:
  cd backend
  python scripts/benchmark_wer.py [--model base] [--language pt]
"""

import argparse
import json
import os
import sys
import time
import wave

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_HERE = os.path.dirname(__file__)
_BACKEND = os.path.abspath(os.path.join(_HERE, ".."))
DATA_DIR = os.path.join(_BACKEND, "benchmarks", "data")
RESULTS_DIR = os.path.join(_BACKEND, "benchmarks", "results")
FALLBACK_AUDIO = os.path.join(_BACKEND, "tests", "micro-machines.wav")


def _wav_duration(path: str) -> float:
    try:
        with wave.open(path, "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return 0.0


def _load_audio_16k_mono(path: str):
    """
    Loads a WAV as float32 mono @16kHz WITHOUT ffmpeg (Whisper's load_audio shells
    out to ffmpeg, which may be absent). Reads PCM with `wave`, downmixes to mono
    and linearly resamples to 16kHz — enough to feed whisper.transcribe(ndarray).
    """
    import numpy as np
    with wave.open(path, "rb") as w:
        n_ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    dtype = {1: np.int8, 2: np.int16, 4: np.int32}[width]
    data = np.frombuffer(raw, dtype=dtype).astype(np.float32)
    if width == 2:
        data /= 32768.0
    elif width == 4:
        data /= 2147483648.0
    if n_ch > 1:
        data = data.reshape(-1, n_ch).mean(axis=1)
    if rate != 16000 and len(data):
        tgt_len = int(round(len(data) * 16000 / rate))
        data = np.interp(np.linspace(0, len(data), tgt_len, endpoint=False),
                         np.arange(len(data)), data).astype(np.float32)
    return np.ascontiguousarray(data, dtype=np.float32)


def _collect_dataset() -> list[dict]:
    items: list[dict] = []
    if os.path.isdir(DATA_DIR):
        for fn in sorted(os.listdir(DATA_DIR)):
            if fn.lower().endswith(".wav"):
                base = os.path.splitext(fn)[0]
                ref_path = os.path.join(DATA_DIR, base + ".ref.txt")
                ref = None
                if os.path.isfile(ref_path):
                    with open(ref_path, encoding="utf-8") as fh:
                        ref = fh.read().strip()
                items.append({"id": base, "audio": os.path.join(DATA_DIR, fn), "reference": ref})
    if not items and os.path.isfile(FALLBACK_AUDIO):
        items.append({"id": "micro-machines (sample, unlabeled)", "audio": FALLBACK_AUDIO, "reference": None})
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=os.getenv("WHISPER_MODEL_SIZE", "base"))
    parser.add_argument("--language", default="pt")
    args = parser.parse_args()

    try:
        import jiwer
    except ImportError:
        print("ERRO: jiwer não instalado. pip install jiwer")
        sys.exit(1)
    from app.services.asr_service import WhisperASRModel

    print("=" * 70)
    print(f"ASR Benchmark — Whisper '{args.model}' (Issue #28)")
    print("=" * 70)

    dataset = _collect_dataset()
    if not dataset:
        print("Nenhum áudio encontrado (benchmarks/data/*.wav nem amostra). Abortando.")
        sys.exit(1)

    print(f"Carregando Whisper '{args.model}'... (pode baixar pesos no primeiro uso)")
    model = WhisperASRModel(model_size=args.model)

    rows = []
    for item in dataset:
        audio = item["audio"]
        dur = _wav_duration(audio)
        lang = "en" if "micro-machines" in item["id"] else args.language
        audio_array = _load_audio_16k_mono(audio)  # ffmpeg-free decode
        t0 = time.perf_counter()
        # Call the underlying Whisper model directly with the preloaded ndarray
        # so we don't depend on ffmpeg for file decoding.
        result = model.model.transcribe(audio_array, language=lang)
        elapsed = time.perf_counter() - t0
        hypothesis = " ".join(s["text"] for s in result["segments"]).strip()

        row = {
            "id": item["id"],
            "audio_duration_s": round(dur, 2),
            "latency_s": round(elapsed, 2),
            "rtf": round(elapsed / dur, 3) if dur else None,
            "hypothesis_preview": hypothesis[:160],
            "wer": None,
            "cer": None,
        }
        if item["reference"]:
            row["wer"] = round(jiwer.wer(item["reference"], hypothesis), 4)
            row["cer"] = round(jiwer.cer(item["reference"], hypothesis), 4)
        rows.append(row)
        wer_str = f"{row['wer']:.1%}" if row["wer"] is not None else "N/A (sem referência)"
        print(f"  ✓ {item['id']}: dur={row['audio_duration_s']}s "
              f"latency={row['latency_s']}s RTF={row['rtf']} WER={wer_str}")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out = {"model": args.model, "results": rows}
    with open(os.path.join(RESULTS_DIR, "wer.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"\nResultados salvos em benchmarks/results/wer.json")


if __name__ == "__main__":
    main()
