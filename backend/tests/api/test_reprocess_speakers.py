"""Reprocessar (só em Erro) e identificação manual de falantes."""
import pytest
from app.models import StatusJob
from tests import factories

pytestmark = pytest.mark.integration


def test_reprocessar_apenas_em_erro(client, valid_token, test_user, db_session, mock_celery):
    chain = factories.full_chain(db_session)  # job Concluído
    jid = str(chain["job"].id_job)

    # Concluído → 409
    assert client.post(f"/api/v1/jobs/{jid}/reprocessar", headers=valid_token).status_code == 409

    # Erro → 200, volta para Pendente e dispara a task
    chain["job"].status = StatusJob.ERRO
    chain["job"].parametros_ia = {"erro": "x"}
    db_session.commit()
    r = client.post(f"/api/v1/jobs/{jid}/reprocessar", headers=valid_token)
    assert r.status_code == 200
    assert r.json()["status"] == "Pendente"
    mock_celery.assert_called()


def test_set_speakers_reescreve_rotulos(client, valid_token, test_user, db_session):
    chain = factories.full_chain(db_session)
    did = str(chain["depoimento"].id_depoimento)
    label = chain["termos"].segmentos_asr[0]["speaker"]

    r = client.post(f"/api/v1/termos/{did}/speakers",
                    json={"mapping": {label: {"role": "Depoente", "nome": "João da Silva"}}},
                    headers=valid_token)
    assert r.status_code == 200
    body = r.json()
    assert any(s["speaker"] == "Depoente" and s.get("speaker_nome") == "João da Silva"
               for s in body["segmentos_asr"])
    # o detalhe agora expõe o nome do depoente p/ o título
    assert "nome_depoente" in body


def test_detalhe_inclui_confianca_e_nome(client, valid_token, test_user, db_session):
    chain = factories.full_chain(db_session)
    did = str(chain["depoimento"].id_depoimento)
    r = client.get(f"/api/v1/termos/{did}", headers=valid_token)
    assert r.status_code == 200
    body = r.json()
    assert "confianca_asr" in body and "confianca_ner" in body
    assert "nome_depoente" in body and "assinado" in body
    # Tempos de execução expostos no detalhe (podem ser null em termos antigos).
    assert "tempo_total_ms" in body and "tempo_asr_ms" in body
    assert "tempo_ner_ms" in body and "tempo_llm_ms" in body
