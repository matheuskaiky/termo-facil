"""
PARTE 2 — módulo Dev/Debug: catálogo de modelos, criação de teste/processamento,
paridade de carga de dados com produção, detalhe na shape de /termos e export CSV.
Todos os endpoints exigem ACESSAR_DEV_DEBUG.
"""
import contextlib
import uuid

import pytest

from app.models import ProcessamentoTeste, StatusJob, TesteIA
from tests import factories
from tests.factories import DEFAULT_PASSWORD
from tests.conftest import TestingSessionLocal
from tests.mocks import MockASRModel, MockNERModel, MockLLM

pytestmark = pytest.mark.integration

WAV = b"RIFF\x24\x08\x00\x00WAVEfmt "


def _no_debug_token(client, db_session):
    deleg = factories.create_delegacia(db_session)
    factories.create_user(db_session, deleg, "SemDebug", ["EDITAR_TERMO"], matricula="NODBG1")
    r = client.post("/api/v1/auth/login", json={"matricula": "NODBG1", "senha": DEFAULT_PASSWORD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_models_available_exige_permissao(client, db_session, valid_token, test_user):
    # test_user tem ACESSAR_DEV_DEBUG (conftest) → 200
    r = client.get("/api/v1/models/available", headers=valid_token)
    assert r.status_code == 200
    body = r.json()
    assert "catalogo" in body and "health" in body
    assert {"asr", "ner", "llm", "diarizacao"} <= set(body["catalogo"].keys())
    # opção "Não testar" presente no ASR
    assert any(o["id"] == "skip" for o in body["catalogo"]["asr"])

    # usuário sem a permissão → 403
    r2 = client.get("/api/v1/models/available", headers=_no_debug_token(client, db_session))
    assert r2.status_code == 403


def test_criar_teste_listar_e_processar(client, db_session, valid_token, test_user, mock_storage, mock_celery):
    # cria teste com áudio
    r = client.post(
        "/api/v1/debug/testes",
        headers=valid_token,
        files={"file": ("a.wav", WAV, "audio/wav")},
        data={"nome": "Teste comparativo"},
    )
    assert r.status_code == 201, r.json()
    teste_id = r.json()["id_teste"]

    assert any(t["id_teste"] == teste_id for t in client.get("/api/v1/debug/testes", headers=valid_token).json())

    # cria processamento (dispara a task)
    r = client.post(
        f"/api/v1/debug/testes/{teste_id}/processamentos",
        headers=valid_token,
        json={"asr_model": "whisper-base", "ner_model": "lener-br", "llm_model": "llama3", "diarizacao": "heuristic"},
    )
    assert r.status_code == 202, r.json()
    mock_celery.assert_called()
    assert r.json()["asr_model"] == "whisper-base"

    det = client.get(f"/api/v1/debug/testes/{teste_id}", headers=valid_token).json()
    assert det["n_processamentos"] == 1


def test_processamento_sem_asr_e_422(client, db_session, valid_token, test_user, mock_storage):
    r = client.post(
        "/api/v1/debug/testes",
        headers=valid_token,
        files={"file": ("a.wav", WAV, "audio/wav")},
        data={"nome": "T"},
    )
    teste_id = r.json()["id_teste"]
    r = client.post(
        f"/api/v1/debug/testes/{teste_id}/processamentos",
        headers=valid_token,
        json={"asr_model": "skip"},
    )
    assert r.status_code == 422


def test_detalhe_processamento_tem_shape_de_termos(client, db_session, valid_token, test_user):
    teste = TesteIA(nome="X", storage_path_audio="p", audio_filename="a.wav")
    db_session.add(teste)
    db_session.commit()
    proc = ProcessamentoTeste(
        id_teste=teste.id_teste, asr_model="whisper-base", ner_model="lener-br",
        llm_model="llama3", diarizacao="heuristic", status=StatusJob.CONCLUIDO,
        txt_literal_asr="oi", segmentos_asr=[{"start": 0, "end": 1, "text": "oi", "speaker": "Depoente"}],
        ner_entidades=[{"tipo": "PESSOAS", "texto": "X", "score": 90.0}],
        confianca_asr=88.0, confianca_ner=90.0, tempo_total_ms=1200.0,
    )
    db_session.add(proc)
    db_session.commit()

    body = client.get(f"/api/v1/debug/processamentos/{proc.id_processamento}", headers=valid_token).json()
    # mesma shape consumida pela auditoria
    for k in ("txt_literal_asr", "txt_original_ia", "txt_editado_humano", "dicionario_ner",
              "segmentos_asr", "ner_entidades", "confianca_asr", "confianca_ner",
              "tempo_total_ms", "nome_depoente", "num_procedimento", "assinado"):
        assert k in body
    assert body["assinado"] is True  # read-only


def test_export_csv(client, db_session, valid_token, test_user):
    teste = TesteIA(nome="CSV", storage_path_audio="p", audio_filename="a.wav")
    db_session.add(teste)
    db_session.commit()
    db_session.add(ProcessamentoTeste(
        id_teste=teste.id_teste, asr_model="whisper-base", status=StatusJob.CONCLUIDO,
        txt_literal_asr="abc", tempo_total_ms=10.0,
    ))
    db_session.commit()
    r = client.get(f"/api/v1/debug/testes/{teste.id_teste}/export.csv", headers=valid_token)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "tempo_total_ms" in r.text and "asr_model" in r.text


def test_run_debug_processing_salva_mesma_carga(db_session, mocker):
    """A task de debug grava a MESMA carga que produção (transcrição/NER/segmentos/tempos)."""
    import app.tasks.debug_processing as mod

    teste = TesteIA(nome="Run", storage_path_audio="path/a.wav", audio_filename="a.wav")
    db_session.add(teste)
    db_session.commit()
    proc = ProcessamentoTeste(
        id_teste=teste.id_teste, asr_model="whisper-base", ner_model="lener-br",
        llm_model="llama3", diarizacao="heuristic", status=StatusJob.PENDENTE,
    )
    db_session.add(proc)
    db_session.commit()
    # Passa o UUID (não str): o engine SQLite de teste mantém o bind processor de
    # UUID do Postgres; em produção o driver coage a str que o Celery envia.
    pid = proc.id_processamento

    mocker.patch.object(mod, "SessionLocal", TestingSessionLocal)
    mocker.patch.object(mod, "build_asr", lambda size: MockASRModel())
    mocker.patch.object(mod, "build_ner", lambda name: MockNERModel())
    mocker.patch.object(mod, "build_llm", lambda name: MockLLM())
    mocker.patch.object(mod, "build_diarizer_for", lambda prov: None)

    @contextlib.contextmanager
    def fake_download(_p):
        yield "/tmp/whatever.wav"

    mocker.patch("app.services.storage_service.audio_storage.download_as_local_file", fake_download)

    ok = mod.run_debug_processing(pid)
    assert ok is True

    db_session.expire_all()
    refreshed = db_session.query(ProcessamentoTeste).filter_by(id_processamento=proc.id_processamento).first()
    assert refreshed.status == StatusJob.CONCLUIDO
    assert refreshed.txt_literal_asr and refreshed.txt_original_ia
    assert isinstance(refreshed.segmentos_asr, list) and len(refreshed.segmentos_asr) > 0
    assert isinstance(refreshed.ner_entidades, list) and len(refreshed.ner_entidades) > 0
    assert refreshed.tempo_total_ms is not None


def test_run_debug_skip_ner_e_llm(db_session, mocker):
    """Skip pula NER/LLM: sem termo nem entidades, mas com transcrição."""
    import app.tasks.debug_processing as mod

    teste = TesteIA(nome="Skip", storage_path_audio="path/a.wav", audio_filename="a.wav")
    db_session.add(teste)
    db_session.commit()
    proc = ProcessamentoTeste(
        id_teste=teste.id_teste, asr_model="whisper-base", ner_model="skip",
        llm_model="skip", diarizacao="heuristic", status=StatusJob.PENDENTE,
    )
    db_session.add(proc)
    db_session.commit()

    mocker.patch.object(mod, "SessionLocal", TestingSessionLocal)
    mocker.patch.object(mod, "build_asr", lambda size: MockASRModel())
    mocker.patch.object(mod, "build_diarizer_for", lambda prov: None)

    @contextlib.contextmanager
    def fake_download(_p):
        yield "/tmp/whatever.wav"

    mocker.patch("app.services.storage_service.audio_storage.download_as_local_file", fake_download)

    assert mod.run_debug_processing(proc.id_processamento) is True
    db_session.expire_all()
    refreshed = db_session.query(ProcessamentoTeste).filter_by(id_processamento=proc.id_processamento).first()
    assert refreshed.status == StatusJob.CONCLUIDO
    assert refreshed.txt_literal_asr
    assert refreshed.txt_original_ia is None
    assert (refreshed.ner_entidades or []) == []
    assert refreshed.tempo_ner_ms is None and refreshed.tempo_llm_ms is None
