"""
IDOR and ownership enforcement tests.
Verifies that Escrivão A cannot access resources belonging to Escrivão B.
"""
import pytest
import uuid
import io
from app.models import (
    Usuario, Cargo, Permissao, Delegacia, Depoimento, Inquerito,
    Depoente, TermosFinais, JobProcessamentoIA, Modelo, TipoDepoente, TipoModelo, StatusJob,
)
from app.core.security import hash_senha
from datetime import date


def _get_or_create_cargo(db, nome_cargo, permissoes_nomes):
    """Reuses an existing cargo by name (unique constraint) or creates a new one."""
    cargo = db.query(Cargo).filter(Cargo.nome_cargo == nome_cargo).first()
    if cargo:
        return cargo
    perm_objs = []
    for nome in permissoes_nomes:
        p = db.query(Permissao).filter(Permissao.nome_permissao == nome).first()
        if not p:
            p = Permissao(id_permissao=uuid.uuid4(), nome_permissao=nome, descricao_permissao=nome)
            db.add(p)
        perm_objs.append(p)
    cargo = Cargo(id_cargo=uuid.uuid4(), nome_cargo=nome_cargo)
    cargo.permissoes = perm_objs
    db.add(cargo)
    db.commit()
    db.refresh(cargo)
    return cargo


def _create_user_in_delegacia(db, delegacia, nome_cargo, permissoes_nomes, matricula):
    cargo = _get_or_create_cargo(db, nome_cargo, permissoes_nomes)
    user = Usuario(
        id_usuario=uuid.uuid4(),
        id_delegacia=delegacia.id_delegacia,
        id_cargo=cargo.id_cargo,
        matricula=matricula,
        nome=f"Usuario {matricula}",
        senha_hash=hash_senha("senha_forte"),
        must_change_password=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_depoimento_for_user(db, user, delegacia):
    inquerito = Inquerito(
        id_inquerito=uuid.uuid4(),
        id_delegacia=delegacia.id_delegacia,
        num_procedimento=f"IP-{uuid.uuid4()}",
        data_instauracao=date.today(),
    )
    db.add(inquerito)

    depoente = Depoente(
        id_depoente=uuid.uuid4(),
        cpf=f"{uuid.uuid4().int % 99999999999:011d}",
        nome_depoente="Depoente Teste",
    )
    db.add(depoente)

    dep = Depoimento(
        id_depoimento=uuid.uuid4(),
        id_inquerito=inquerito.id_inquerito,
        id_usuario=user.id_usuario,
        id_depoente=depoente.id_depoente,
        tipo_depoente=TipoDepoente.TESTEMUNHA,
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


def _login(client, matricula):
    resp = client.post("/api/v1/auth/login", json={"matricula": matricula, "senha": "senha_forte"})
    assert resp.status_code == 200, f"Login failed for {matricula}: {resp.json()}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _create_termos(db, dep):
    modelo = Modelo(
        id_modelo=uuid.uuid4(),
        nome_modelo="Whisper Test",
        desenvolvedora="OpenAI",
        tipo_modelo=TipoModelo.ASR,
    )
    db.add(modelo)
    modelo_llm = Modelo(
        id_modelo=uuid.uuid4(),
        nome_modelo="Llama3 Test",
        desenvolvedora="Meta",
        tipo_modelo=TipoModelo.LLM,
    )
    db.add(modelo_llm)

    job = JobProcessamentoIA(
        id_job=uuid.uuid4(),
        id_depoimento=dep.id_depoimento,
        id_modelo_asr=modelo.id_modelo,
        id_modelo_llm=modelo_llm.id_modelo,
        status=StatusJob.CONCLUIDO,
    )
    db.add(job)

    termos = TermosFinais(
        id_depoimento=dep.id_depoimento,
        id_job=job.id_job,
        txt_original_ia="Texto da IA",
        txt_editado_humano="Texto editado",
        txt_literal_asr="Texto literal",
    )
    db.add(termos)
    db.commit()
    db.refresh(job)
    return job, termos


# ──────────────────────────────────────────────────────────────────────────────
# GET /termos/{id} — Escrivão A não acessa termo de Escrivão B
# ──────────────────────────────────────────────────────────────────────────────

def test_escrivao_cannot_access_outro_escrivao_termo(client, db_session):
    del1 = Delegacia(id_delegacia=uuid.uuid4(), nome_unidade="Del A", cod_sinesp="AA001")
    db_session.add(del1)
    db_session.commit()

    user_a = _create_user_in_delegacia(db_session, del1, "Escrivão", ["EDITAR_TERMO"], "A00001")
    user_b = _create_user_in_delegacia(db_session, del1, "Escrivão", ["EDITAR_TERMO"], "B00001")

    dep_b = _create_depoimento_for_user(db_session, user_b, del1)
    _create_termos(db_session, dep_b)

    headers_a = _login(client, "A00001")
    response = client.get(f"/api/v1/termos/{dep_b.id_depoimento}", headers=headers_a)
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.json()}"


def test_escrivao_accesses_own_termo(client, db_session):
    del1 = Delegacia(id_delegacia=uuid.uuid4(), nome_unidade="Del AA", cod_sinesp="AA002")
    db_session.add(del1)
    db_session.commit()

    user_a = _create_user_in_delegacia(db_session, del1, "Escrivão", ["EDITAR_TERMO"], "C00001")
    dep_a = _create_depoimento_for_user(db_session, user_a, del1)
    _create_termos(db_session, dep_a)

    headers_a = _login(client, "C00001")
    response = client.get(f"/api/v1/termos/{dep_a.id_depoimento}", headers=headers_a)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"


# ──────────────────────────────────────────────────────────────────────────────
# GET /termos/{id} — unauthenticated request
# ──────────────────────────────────────────────────────────────────────────────

def test_termos_requires_auth(client, db_session):
    response = client.get(f"/api/v1/termos/{uuid.uuid4()}")
    assert response.status_code == 401


# ──────────────────────────────────────────────────────────────────────────────
# Upload — magic bytes validation
# ──────────────────────────────────────────────────────────────────────────────

def test_upload_rejects_non_audio_magic_bytes(client, db_session, mocker):
    del1 = Delegacia(id_delegacia=uuid.uuid4(), nome_unidade="Del Magic", cod_sinesp="MG001")
    db_session.add(del1)
    db_session.commit()

    user = _create_user_in_delegacia(db_session, del1, "Escrivão", ["UPLOAD_AUDIO"], "MG00001")
    dep = _create_depoimento_for_user(db_session, user, del1)
    headers = _login(client, "MG00001")

    mocker.patch("app.api.endpoints.upload._resolve_modelo", return_value=uuid.uuid4())

    # Send a fake PDF (starts with %PDF) renamed to .wav — should be rejected
    fake_pdf_bytes = b"%PDF-1.4 fake pdf content that is definitely not audio"
    files = {"file": ("audio.wav", io.BytesIO(fake_pdf_bytes), "audio/wav")}
    data = {"id_depoimento": str(dep.id_depoimento)}

    response = client.post("/api/v1/upload/audio", headers=headers, files=files, data=data)
    assert response.status_code == 415, f"Expected 415, got {response.status_code}: {response.json()}"


def test_upload_accepts_valid_wav_magic_bytes(client, db_session, mock_storage, mock_celery, mocker):
    del1 = Delegacia(id_delegacia=uuid.uuid4(), nome_unidade="Del Wav", cod_sinesp="WV001")
    db_session.add(del1)
    db_session.commit()

    user = _create_user_in_delegacia(db_session, del1, "Escrivão", ["UPLOAD_AUDIO"], "WV00001")
    dep = _create_depoimento_for_user(db_session, user, del1)
    headers = _login(client, "WV00001")

    mocker.patch("app.api.endpoints.upload._resolve_modelo", return_value=uuid.uuid4())

    # Valid WAV header: RIFF....WAVE
    wav_header = b"RIFF\x24\x08\x00\x00WAVEfmt "
    files = {"file": ("audio.wav", io.BytesIO(wav_header + b"\x00" * 100), "audio/wav")}
    data = {"id_depoimento": str(dep.id_depoimento)}

    response = client.post("/api/v1/upload/audio", headers=headers, files=files, data=data)
    assert response.status_code == 202, f"Expected 202, got {response.status_code}: {response.json()}"


# ──────────────────────────────────────────────────────────────────────────────
# GET /{job_id}/pdf — requires authentication
# ──────────────────────────────────────────────────────────────────────────────

def test_pdf_download_requires_auth(client):
    response = client.get(f"/api/v1/pdf/{uuid.uuid4()}/pdf")
    assert response.status_code == 401
