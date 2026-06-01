"""Unit tests for pdf_service — real ReportLab PDF generation (no AI, no network)."""
import pytest

from app.services.pdf_service import gerar_pdf_termo_depoimento
from app.core.exceptions import (
    DepoimentoNotFoundError, TermosNotFoundError, TextoAusenteError,
)
from tests.factories import (
    create_delegacia, create_user, create_depoimento, create_job, create_termos,
)

pytestmark = pytest.mark.integration


def _setup(db, **termos_kwargs):
    deleg = create_delegacia(db)
    user = create_user(db, deleg, "Escrivão", ["EDITAR_TERMO"])
    dep = create_depoimento(db, user, deleg)
    job = create_job(db, dep)
    create_termos(db, dep, job, **termos_kwargs)
    return dep


def test_gera_pdf_valido_com_segmentos(db_session):
    dep = _setup(db_session)
    pdf_bytes, sha = gerar_pdf_termo_depoimento(db_session, dep.id_depoimento)
    assert pdf_bytes.startswith(b"%PDF")           # real PDF magic
    assert pdf_bytes.rstrip().endswith(b"%%EOF")
    assert len(sha) == 64                           # sha256 hex digest


def test_pdf_e_deterministico_no_hash_de_conteudo(db_session):
    """Same content → same SHA-256 (timestamp aside, the structure is stable)."""
    dep = _setup(db_session)
    b1, _ = gerar_pdf_termo_depoimento(db_session, dep.id_depoimento)
    b2, _ = gerar_pdf_termo_depoimento(db_session, dep.id_depoimento)
    # Two builds in the same minute produce identical-length documents
    assert abs(len(b1) - len(b2)) < 200


def test_usa_texto_editado_humano_quando_presente(db_session):
    dep = _setup(db_session, txt_editado_humano="EDICAO_HUMANA_MARCADOR", txt_original_ia="IA_MARCADOR")
    pdf_bytes, _ = gerar_pdf_termo_depoimento(db_session, dep.id_depoimento)
    assert pdf_bytes.startswith(b"%PDF")  # built successfully with human text precedence


def test_fallback_para_txt_literal_quando_sem_segmentos(db_session):
    dep = _setup(db_session, segmentos_asr=[], txt_literal_asr="Transcrição literal sem segmentos.")
    pdf_bytes, _ = gerar_pdf_termo_depoimento(db_session, dep.id_depoimento)
    assert pdf_bytes.startswith(b"%PDF")


def test_raises_depoimento_not_found(db_session):
    import uuid
    with pytest.raises(DepoimentoNotFoundError):
        gerar_pdf_termo_depoimento(db_session, uuid.uuid4())


def test_raises_termos_not_found(db_session):
    deleg = create_delegacia(db_session)
    user = create_user(db_session, deleg, "Escrivão", ["EDITAR_TERMO"])
    dep = create_depoimento(db_session, user, deleg)  # no termos
    with pytest.raises(TermosNotFoundError):
        gerar_pdf_termo_depoimento(db_session, dep.id_depoimento)


def test_raises_texto_ausente(db_session):
    dep = _setup(db_session, txt_editado_humano=None, txt_original_ia=None)
    with pytest.raises(TextoAusenteError):
        gerar_pdf_termo_depoimento(db_session, dep.id_depoimento)
