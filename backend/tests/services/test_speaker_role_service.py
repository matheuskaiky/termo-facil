"""Unit tests for the text-based speaker role resolver (no GPU / no audio)."""
import pytest

from app.services.speaker_role_service import (
    TextBasedRoleResolver, AudioBasedRoleResolver, SpeakerRoleResolver,
)

pytestmark = pytest.mark.unit


def test_text_resolver_detects_inverted_roles():
    """Labels are swapped vs. content: the 'Depoente' asks questions, the
    'Inquiridor' gives first-person answers → resolver proposes a remap."""
    segments = [
        {"speaker": "Depoente", "text": "O senhor poderia dizer onde estava?"},
        {"speaker": "Depoente", "text": "E quando isso aconteceu? Quem mais viu?"},
        {"speaker": "Inquiridor", "text": "Eu estava em casa, vi tudo e depois fui embora correndo com medo."},
        {"speaker": "Inquiridor", "text": "Eu morava lá perto e conheço o bairro muito bem."},
    ]
    mapping = TextBasedRoleResolver().resolve(segments).mapping
    assert mapping.get("Depoente") == "Inquiridor"
    assert mapping.get("Inquiridor") == "Depoente"


def test_text_resolver_correct_labels_no_remap():
    segments = [
        {"speaker": "Inquiridor", "text": "Onde a senhora estava? Pode descrever?"},
        {"speaker": "Depoente", "text": "Eu estava na avenida, vi o carro e fui embora."},
    ]
    mapping = TextBasedRoleResolver().resolve(segments).mapping
    assert mapping == {}


def test_text_resolver_single_speaker_no_mapping():
    segments = [{"speaker": "Inquiridor", "text": "Apenas uma fala."}]
    result = TextBasedRoleResolver().resolve(segments)
    assert result.mapping == {}
    assert result.confidence == 0.0


def test_orchestrator_falls_back_to_text_without_samples():
    segments = [
        {"speaker": "A", "text": "Quem estava com o senhor? Onde foi?"},
        {"speaker": "B", "text": "Eu estava sozinho, fui e voltei rapidamente."},
    ]
    resolver = SpeakerRoleResolver(
        text_resolver=TextBasedRoleResolver(),
        audio_resolver=AudioBasedRoleResolver(),
    )
    mapping = resolver.resolve(segments)  # no audio_path/known_samples
    assert mapping.get("A") == "Inquiridor"
    assert mapping.get("B") == "Depoente"
