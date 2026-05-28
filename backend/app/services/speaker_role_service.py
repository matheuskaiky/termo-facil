"""
Speaker role identification: determines which diarized speaker is Inquiridor vs Depoente.

Two independent resolution strategies (SRP):
- TextBasedRoleResolver  — scores transcript content patterns, no GPU needed
- AudioBasedRoleResolver — matches voice embeddings against known samples (pyannote/embedding)

SpeakerRoleResolver orchestrates: tries audio when samples are available,
falls back to text-based (DIP — both resolvers are injected, not created internally).
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_AUDIO_CONFIDENCE_THRESHOLD = 0.75

# Portuguese interrogative / questioning patterns (Inquiridor markers)
_INTERROGATIVE_RE = re.compile(
    r"\b(quem|onde|quando|como|por\s+que|por\s+quê|qual|quais|quanto|"
    r"quantos|poderia|pode|confirma|declara|descreva|explique|relate)\b",
    re.IGNORECASE,
)

# First-person singular patterns (Depoente markers)
_FIRST_PERSON_RE = re.compile(
    r"\b(eu\b|estava|fui|fiz|saí|cheguei|vi|ouvi|meu|minha|"
    r"meus|minhas|sim\b|não\b|trabalhava|morava|conheço|conhecia)\b",
    re.IGNORECASE,
)


@dataclass
class _ResolutionResult:
    mapping: dict[str, str]
    confidence: float
    method: str


class TextBasedRoleResolver:
    """
    Infers Inquiridor / Depoente from transcript content.
    Scoring: question ratio + interrogative keywords → Inquiridor score.
             first-person pronouns + longer answers → Depoente score.
    """

    def resolve(self, segments: list[dict]) -> _ResolutionResult:
        stats: dict[str, dict] = defaultdict(
            lambda: {"questions": 0.0, "first_person": 0, "total": 0, "chars": 0}
        )

        for seg in segments:
            label = seg.get("speaker", "")
            text = seg.get("text", "")
            if not label or not text:
                continue
            s = stats[label]
            s["total"] += 1
            s["chars"] += len(text)
            if text.strip().endswith("?"):
                s["questions"] += 1.0
            if _INTERROGATIVE_RE.search(text):
                s["questions"] += 0.5
            if _FIRST_PERSON_RE.search(text):
                s["first_person"] += 1

        if len(stats) < 2:
            return _ResolutionResult(mapping={}, confidence=0.0, method="text")

        # Keep only the two most active speakers for the binary assignment
        top_two = sorted(stats, key=lambda l: stats[l]["total"], reverse=True)[:2]
        stats = {k: stats[k] for k in top_two}

        def interrogator_score(s: dict) -> float:
            total = max(s["total"], 1)
            avg_len = s["chars"] / total
            return (s["questions"] / total) * 0.7 + (1.0 / max(avg_len, 1)) * 30.0

        scored = {label: interrogator_score(s) for label, s in stats.items()}
        sorted_labels = sorted(scored, key=scored.get, reverse=True)
        inq_label, dep_label = sorted_labels[0], sorted_labels[1]

        top_score = scored[inq_label]
        second_score = scored[dep_label]
        confidence = min((top_score - second_score) / max(top_score, 0.01), 1.0)

        mapping: dict[str, str] = {}
        if inq_label != "Inquiridor":
            mapping[inq_label] = "Inquiridor"
        if dep_label != "Depoente":
            mapping[dep_label] = "Depoente"

        return _ResolutionResult(mapping=mapping, confidence=confidence, method="text")


class AudioBasedRoleResolver:
    """
    Matches known voice samples against diarized speakers via cosine similarity
    on pyannote/embedding speaker embeddings. No HF token required for this model.
    Falls back gracefully if pyannote is unavailable.
    """

    _inference = None

    def _get_inference(self):
        if self._inference is None:
            from pyannote.audio import Inference  # noqa: PLC0415
            token = None
            try:
                self._inference = Inference("pyannote/embedding", window="whole")
            except Exception:
                import os
                token = os.getenv("PYANNOTE_HF_TOKEN")
                self._inference = Inference(
                    "pyannote/embedding", window="whole", use_auth_token=token
                )
        return self._inference

    def resolve(
        self,
        segments: list[dict],
        audio_path: str,
        known_samples: dict[str, str],
    ) -> _ResolutionResult:
        try:
            return self._resolve(segments, audio_path, known_samples)
        except Exception as exc:
            logger.warning("AudioBasedRoleResolver failed, falling back: %s", exc)
            return _ResolutionResult(mapping={}, confidence=0.0, method="audio")

    def _resolve(
        self,
        segments: list[dict],
        audio_path: str,
        known_samples: dict[str, str],
    ) -> _ResolutionResult:
        import numpy as np
        from pyannote.core import Segment  # noqa: PLC0415

        inference = self._get_inference()

        # Average embedding per speaker from their turns in the full audio
        speaker_embs: dict[str, list] = defaultdict(list)
        for seg in segments:
            label = seg.get("speaker")
            duration = seg.get("end", 0) - seg.get("start", 0)
            if not label or duration < 0.5:
                continue
            try:
                emb = inference.crop(audio_path, Segment(seg["start"], seg["end"]))
                speaker_embs[label].append(emb)
            except Exception:
                continue

        if not speaker_embs:
            return _ResolutionResult(mapping={}, confidence=0.0, method="audio")

        avg_embs = {
            label: np.mean(embs, axis=0) for label, embs in speaker_embs.items()
        }

        def cosine_sim(a: "np.ndarray", b: "np.ndarray") -> float:
            denom = np.linalg.norm(a) * np.linalg.norm(b)
            return float(np.dot(a, b) / (denom + 1e-8))

        mapping: dict[str, str] = {}
        best_confidence = 0.0

        for role, sample_path in known_samples.items():
            try:
                sample_emb = inference(sample_path)
            except Exception as exc:
                logger.warning("Could not embed sample for role=%s: %s", role, exc)
                continue

            sims = {lbl: cosine_sim(sample_emb, avg) for lbl, avg in avg_embs.items()}
            best_match = max(sims, key=sims.get)
            best_confidence = max(best_confidence, sims[best_match])

            if best_match != role:
                mapping[best_match] = role

        return _ResolutionResult(mapping=mapping, confidence=best_confidence, method="audio")


class SpeakerRoleResolver:
    """
    Orchestrates role resolution:
    1. Audio-based (if known_samples provided and confidence ≥ threshold)
    2. Text-based fallback
    Resolvers are injected (DIP) — no internal construction.
    """

    def __init__(
        self,
        text_resolver: TextBasedRoleResolver,
        audio_resolver: AudioBasedRoleResolver,
    ):
        self._text = text_resolver
        self._audio = audio_resolver

    def resolve(
        self,
        segments: list[dict],
        audio_path: str | None = None,
        known_samples: dict[str, str] | None = None,
    ) -> dict[str, str]:
        if audio_path and known_samples:
            result = self._audio.resolve(segments, audio_path, known_samples)
            if result.confidence >= _AUDIO_CONFIDENCE_THRESHOLD:
                logger.info(
                    "SpeakerRoleResolver: audio-based (confidence=%.2f) mapping=%s",
                    result.confidence,
                    result.mapping,
                )
                return result.mapping

        result = self._text.resolve(segments)
        logger.info(
            "SpeakerRoleResolver: text-based (confidence=%.2f) mapping=%s",
            result.confidence,
            result.mapping,
        )
        return result.mapping


# Module-level singleton — resolvers are stateless except for lazy-loaded models
role_resolver = SpeakerRoleResolver(
    text_resolver=TextBasedRoleResolver(),
    audio_resolver=AudioBasedRoleResolver(),
)
