"""
ORM factory helpers for tests.

Build the Delegacia → Inquerito → Depoente → Depoimento → MidiaBruta → Job →
TermosFinais chain with sensible defaults, so individual tests only specify what
they actually care about. All helpers commit and refresh.
"""

from __future__ import annotations
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.core.security import hash_senha
from app.models import (
    Cargo, Permissao, Delegacia, Usuario, Inquerito, Depoente, Depoimento,
    MidiaBruta, Modelo, JobProcessamentoIA, TermosFinais,
    TipoDepoente, TipoModelo, StatusJob,
)

DEFAULT_PASSWORD = "senha_forte"


def get_or_create_cargo(db: Session, nome_cargo: str, permissoes: list[str]) -> Cargo:
    cargo = db.query(Cargo).filter(Cargo.nome_cargo == nome_cargo).first()
    if cargo:
        return cargo
    perm_objs = []
    for nome in permissoes:
        p = db.query(Permissao).filter(Permissao.nome_permissao == nome).first()
        if not p:
            p = Permissao(id_permissao=uuid.uuid4(), nome_permissao=nome, descricao_permissao=nome)
            db.add(p)
        perm_objs.append(p)
    cargo = Cargo(id_cargo=uuid.uuid4(), nome_cargo=nome_cargo, permissoes=perm_objs)
    db.add(cargo)
    db.commit()
    db.refresh(cargo)
    return cargo


def create_delegacia(db: Session, nome: str = "Delegacia X", cod: str | None = None) -> Delegacia:
    d = Delegacia(id_delegacia=uuid.uuid4(), nome_unidade=nome, cod_sinesp=cod or f"C{uuid.uuid4().hex[:8]}")
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def create_user(
    db: Session,
    delegacia: Delegacia,
    nome_cargo: str = "Escrivão",
    permissoes: list[str] | None = None,
    matricula: str | None = None,
) -> Usuario:
    cargo = get_or_create_cargo(db, nome_cargo, permissoes or ["EDITAR_TERMO"])
    user = Usuario(
        id_usuario=uuid.uuid4(),
        id_delegacia=delegacia.id_delegacia,
        id_cargo=cargo.id_cargo,
        matricula=matricula or f"M{uuid.uuid4().hex[:6]}",
        nome=f"Usuario {nome_cargo}",
        senha_hash=hash_senha(DEFAULT_PASSWORD),
        must_change_password=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_models(db: Session) -> tuple[Modelo, Modelo]:
    asr = Modelo(id_modelo=uuid.uuid4(), nome_modelo="Whisper Test", desenvolvedora="OpenAI", tipo_modelo=TipoModelo.ASR)
    llm = Modelo(id_modelo=uuid.uuid4(), nome_modelo="Llama3 Test", desenvolvedora="Meta", tipo_modelo=TipoModelo.LLM)
    db.add_all([asr, llm])
    db.commit()
    return asr, llm


def create_depoimento(
    db: Session,
    user: Usuario,
    delegacia: Delegacia,
    tipo: TipoDepoente = TipoDepoente.TESTEMUNHA,
) -> Depoimento:
    inquerito = Inquerito(
        id_inquerito=uuid.uuid4(),
        id_delegacia=delegacia.id_delegacia,
        num_procedimento=f"IP-{uuid.uuid4().hex[:10]}",
        data_instauracao=date.today(),
    )
    depoente = Depoente(
        id_depoente=uuid.uuid4(),
        cpf=f"{uuid.uuid4().int % 99999999999:011d}",
        nome_depoente="Depoente Teste",
    )
    db.add_all([inquerito, depoente])
    db.flush()
    dep = Depoimento(
        id_depoimento=uuid.uuid4(),
        id_inquerito=inquerito.id_inquerito,
        id_usuario=user.id_usuario,
        id_depoente=depoente.id_depoente,
        tipo_depoente=tipo,
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


def create_midia(db: Session, dep: Depoimento, codec_info: dict | None = None) -> MidiaBruta:
    midia = MidiaBruta(
        id_depoimento=dep.id_depoimento,
        hash_sha256="0" * 64,
        storage_path=f"{dep.id_depoimento}/audio.wav",
        codec_info=codec_info or {"filename": "audio.wav"},
    )
    db.add(midia)
    db.commit()
    return midia


def create_job(db: Session, dep: Depoimento, status: StatusJob = StatusJob.CONCLUIDO) -> JobProcessamentoIA:
    asr, llm = create_models(db)
    job = JobProcessamentoIA(
        id_job=uuid.uuid4(),
        id_depoimento=dep.id_depoimento,
        id_modelo_asr=asr.id_modelo,
        id_modelo_llm=llm.id_modelo,
        status=status,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def create_termos(
    db: Session,
    dep: Depoimento,
    job: JobProcessamentoIA,
    *,
    txt_original_ia: str = "Resumo gerado pela IA.",
    txt_editado_humano: str | None = "Resumo revisado pelo escrivão.",
    txt_literal_asr: str = "Transcrição literal do áudio.",
    dicionario_ner: dict | None = None,
    segmentos_asr: list[dict] | None = None,
) -> TermosFinais:
    termos = TermosFinais(
        id_depoimento=dep.id_depoimento,
        id_job=job.id_job,
        txt_original_ia=txt_original_ia,
        txt_editado_humano=txt_editado_humano,
        txt_literal_asr=txt_literal_asr,
        dicionario_ner=dicionario_ner if dicionario_ner is not None else {"PESSOAS": ["João da Silva"]},
        segmentos_asr=segmentos_asr if segmentos_asr is not None else [
            {"start": 0.0, "end": 3.0, "text": "Pergunta.", "speaker": "Inquiridor"},
            {"start": 3.0, "end": 6.0, "text": "Resposta.", "speaker": "Depoente"},
        ],
    )
    db.add(termos)
    db.commit()
    db.refresh(termos)
    return termos


def full_chain(db: Session, nome_cargo: str = "Escrivão", permissoes: list[str] | None = None):
    """Builds the complete chain and returns a dict of all created objects."""
    delegacia = create_delegacia(db)
    user = create_user(db, delegacia, nome_cargo, permissoes)
    dep = create_depoimento(db, user, delegacia)
    midia = create_midia(db, dep)
    job = create_job(db, dep)
    termos = create_termos(db, dep, job)
    return {
        "delegacia": delegacia, "user": user, "depoimento": dep,
        "midia": midia, "job": job, "termos": termos,
    }
