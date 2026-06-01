"""Tests for the LGPD safety-net expurgo task (RN-04)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.tasks import expurgo as expurgo_mod
from app.models import MidiaBruta, TermosFinais
from tests.conftest import TestingSessionLocal
from tests.factories import create_delegacia, create_user, create_depoimento, create_job, create_termos

pytestmark = pytest.mark.integration


def test_expurgo_removes_audio_and_clears_ner_after_24h(db_session, mocker):
    deleg = create_delegacia(db_session)
    user = create_user(db_session, deleg, "Escrivão", ["EDITAR_TERMO"])
    dep = create_depoimento(db_session, user, deleg)

    midia = MidiaBruta(
        id_depoimento=dep.id_depoimento,
        hash_sha256="0" * 64,
        storage_path=f"{dep.id_depoimento}/audio.wav",
        codec_info={"speaker_samples": {"Depoente": "key/sample.wav"}},
    )
    db_session.add(midia)
    job = create_job(db_session, dep)
    termos = create_termos(db_session, dep, job)
    termos.data_exportacao_pdf = datetime.now(timezone.utc) - timedelta(hours=25)
    db_session.commit()

    audio_del = mocker.patch("app.tasks.expurgo.audio_storage.delete_file")
    sample_del = mocker.patch("app.tasks.expurgo.speaker_samples_storage.delete_file")
    mocker.patch.object(expurgo_mod, "SessionLocal", TestingSessionLocal)

    expurgo_mod.expurgo_dados_expirados()

    audio_del.assert_called_once()
    sample_del.assert_called_once_with("key/sample.wav")

    db_session.expire_all()
    m = db_session.query(MidiaBruta).filter_by(id_depoimento=dep.id_depoimento).first()
    t = db_session.query(TermosFinais).filter_by(id_depoimento=dep.id_depoimento).first()
    assert m.storage_path is None
    assert t.dicionario_ner is None
    assert t.segmentos_asr is None


def test_expurgo_skips_recent_records(db_session, mocker):
    deleg = create_delegacia(db_session)
    user = create_user(db_session, deleg, "Escrivão", ["EDITAR_TERMO"])
    dep = create_depoimento(db_session, user, deleg)
    midia = MidiaBruta(
        id_depoimento=dep.id_depoimento, hash_sha256="0" * 64,
        storage_path=f"{dep.id_depoimento}/audio.wav", codec_info={},
    )
    db_session.add(midia)
    job = create_job(db_session, dep)
    termos = create_termos(db_session, dep, job)
    termos.data_exportacao_pdf = datetime.now(timezone.utc) - timedelta(hours=1)  # recent
    db_session.commit()

    audio_del = mocker.patch("app.tasks.expurgo.audio_storage.delete_file")
    mocker.patch.object(expurgo_mod, "SessionLocal", TestingSessionLocal)

    expurgo_mod.expurgo_dados_expirados()

    audio_del.assert_not_called()
    db_session.expire_all()
    m = db_session.query(MidiaBruta).filter_by(id_depoimento=dep.id_depoimento).first()
    assert m.storage_path is not None
