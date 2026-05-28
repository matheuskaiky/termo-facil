import enum
from sqlalchemy import Boolean, Column, String, Integer, DateTime, ForeignKey, Text, LargeBinary, JSON, Date, Table, Enum as SQLAlchemyEnum, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA
from sqlalchemy.orm import relationship
import uuid
from app.db import Base

cargo_permissao = Table(
    'cargo_permissao', Base.metadata,
    Column('id_cargo', UUID(as_uuid=True), ForeignKey('cargo.id_cargo'), primary_key=True),
    Column('id_permissao', UUID(as_uuid=True), ForeignKey('permissao.id_permissao'), primary_key=True)
)

# --- ENUMS ---
class TipoDepoente(str, enum.Enum):
    TESTEMUNHA = 'Testemunha'
    VITIMA = 'Vítima'
    SUSPEITO = 'Suspeito'
    INFORMANTE = 'Informante'

class StatusJob(str, enum.Enum):
    PENDENTE = 'Pendente'
    PROCESSANDO = 'Processando'          # mantido para registros legados
    TRANSCREVENDO = 'Transcrevendo'
    EXTRAINDO_DADOS = 'Extraindo Dados'
    GERANDO_RESUMO = 'Gerando Resumo'
    CONCLUIDO = 'Concluído'
    ERRO = 'Erro'

class TipoModelo(str, enum.Enum):
    ASR = 'ASR'
    LLM = 'LLM'
    OCR = 'OCR'

# --- MODELS ---
class Delegacia(Base):
    """ Model representing a Police Station (Delegacia) """
    __tablename__ = 'delegacia'
    id_delegacia = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_unidade = Column(String(255), nullable=False)
    cod_sinesp = Column(String(100), unique=True, nullable=False)

    usuarios = relationship("Usuario", back_populates="delegacia")
    inqueritos = relationship("Inquerito", back_populates="delegacia")

class Depoente(Base):
    """ Model representing the Testifier/Suspect (Depoente) """
    __tablename__ = 'depoente'
    id_depoente = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cpf = Column(String(14), unique=True, nullable=False)
    nome_depoente = Column(String(255), nullable=False)

    depoimentos = relationship("Depoimento", back_populates="depoente")

class Modelo(Base):
    """ Model representing an AI Engine version (ASR, LLM, etc.) """
    __tablename__ = 'modelo'
    id_modelo = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_modelo = Column(String(255), nullable=False)
    desenvolvedora = Column(String(255), nullable=False)
    tipo_modelo = Column(SQLAlchemyEnum(TipoModelo, name='tipo_modelo_enum', values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    parametros = Column(Text, nullable=True)

class Usuario(Base):
    """ Model representing the Police Officer / Clerk (Escrivão/Delegado) """
    __tablename__ = 'usuario'
    id_usuario = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_delegacia = Column(UUID(as_uuid=True), ForeignKey('delegacia.id_delegacia'), nullable=False)
    id_cargo = Column(UUID(as_uuid=True), ForeignKey('cargo.id_cargo'), nullable=False)
    matricula = Column(String(50), unique=True, nullable=False)
    nome = Column(String(255), nullable=False)
    senha_hash = Column(String(255), nullable=True)
    must_change_password = Column(Boolean, default=False, nullable=False)

    cargo = relationship("Cargo", back_populates="usuarios")
    delegacia = relationship("Delegacia", back_populates="usuarios")
    depoimentos = relationship("Depoimento", back_populates="usuario")

class Inquerito(Base):
    """ Model representing the Police Investigation (Inquérito Policial) """
    __tablename__ = 'inquerito'
    id_inquerito = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_delegacia = Column(UUID(as_uuid=True), ForeignKey('delegacia.id_delegacia'), nullable=False)
    num_procedimento = Column(String(100), unique=True, nullable=False)
    data_instauracao = Column(Date, nullable=False)

    delegacia = relationship("Delegacia", back_populates="inqueritos")
    depoimentos = relationship("Depoimento", back_populates="inquerito")

class Depoimento(Base):
    """ Model representing the formal testimony event (Termo de Depoimento) """
    __tablename__ = 'depoimento'
    id_depoimento = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_inquerito = Column(UUID(as_uuid=True), ForeignKey('inquerito.id_inquerito'), nullable=False)
    id_usuario = Column(UUID(as_uuid=True), ForeignKey('usuario.id_usuario'), nullable=False)
    id_depoente = Column(UUID(as_uuid=True), ForeignKey('depoente.id_depoente'), nullable=False)
    tipo_depoente = Column(SQLAlchemyEnum(TipoDepoente, name='tipo_depoente_enum', values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    data_hora_reg = Column(DateTime, server_default=func.now())

    inquerito = relationship("Inquerito", back_populates="depoimentos")
    usuario = relationship("Usuario", back_populates="depoimentos")
    depoente = relationship("Depoente", back_populates="depoimentos")
    
    midia_bruta = relationship("MidiaBruta", back_populates="depoimento", uselist=False)
    jobs = relationship("JobProcessamentoIA", back_populates="depoimento")
    termos_finais = relationship("TermosFinais", back_populates="depoimento", uselist=False)

class MidiaBruta(Base):
    """ Model representing the raw audio/video blob metadata and storage path """
    __tablename__ = 'midia_bruta'
    id_depoimento = Column(UUID(as_uuid=True), ForeignKey('depoimento.id_depoimento'), primary_key=True)
    hash_sha256 = Column(String(64), nullable=False)
    storage_path = Column(String(512), nullable=False)
    codec_info = Column(JSONB, nullable=True)

    depoimento = relationship("Depoimento", back_populates="midia_bruta")

class JobProcessamentoIA(Base):
    """ Model tracking the AI background processing queue status for a Testimony """
    __tablename__ = 'job_processamento_ia'
    id_job = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_depoimento = Column(UUID(as_uuid=True), ForeignKey('depoimento.id_depoimento'), nullable=False)
    id_modelo_asr = Column(UUID(as_uuid=True), ForeignKey('modelo.id_modelo'), nullable=False)
    id_modelo_llm = Column(UUID(as_uuid=True), ForeignKey('modelo.id_modelo'), nullable=False)
    status = Column(SQLAlchemyEnum(StatusJob, name='status_job_enum', values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=StatusJob.PENDENTE)
    gpu_hw_id = Column(String(100), nullable=True)
    parametros_ia = Column(JSONB, nullable=True)
    data_criacao = Column(DateTime, server_default=func.now(), nullable=False)

    depoimento = relationship("Depoimento", back_populates="jobs")
    modelo_asr = relationship("Modelo", foreign_keys=[id_modelo_asr])
    modelo_llm = relationship("Modelo", foreign_keys=[id_modelo_llm])
    
    termos_finais = relationship("TermosFinais", back_populates="job", uselist=False)

class TermosFinais(Base):
    """ Model representing the resulting transcriptions and the final PDF document """
    __tablename__ = 'termos_finais'
    id_depoimento = Column(UUID(as_uuid=True), ForeignKey('depoimento.id_depoimento'), primary_key=True)
    id_job = Column(UUID(as_uuid=True), ForeignKey('job_processamento_ia.id_job'), nullable=False)
    txt_original_ia = Column(Text, nullable=True)
    txt_editado_humano = Column(Text, nullable=True)
    txt_literal_asr = Column(Text, nullable=True)
    dicionario_ner = Column(JSONB, nullable=True)
    segmentos_asr = Column(JSONB, nullable=True)
    assinatura_digital = Column(BYTEA, nullable=True)
    hash_pdf = Column(String(64), nullable=True)
    storage_path_pdf = Column(String(512), nullable=True)
    data_exportacao_pdf = Column(DateTime, nullable=True)

    depoimento = relationship("Depoimento", back_populates="termos_finais")
    job = relationship("JobProcessamentoIA", back_populates="termos_finais")

class AuditLog(Base):
    """LGPD Art. 37 — records who accessed which personal data resource and when."""
    __tablename__ = 'audit_log'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_usuario = Column(UUID(as_uuid=True), ForeignKey('usuario.id_usuario'), nullable=True)
    endpoint = Column(String(100), nullable=False)
    id_recurso = Column(String(100), nullable=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)


class Cargo(Base):
    """ Model representing the function of an user """
    __tablename__ = 'cargo'
    id_cargo = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_cargo = Column(String(50), nullable=False, unique=True)

    permissoes = relationship("Permissao", secondary=cargo_permissao, back_populates="cargos")
    usuarios = relationship("Usuario", back_populates="cargo")

class Permissao(Base):
    """ Model representing the permissions of access on the system """
    __tablename__ = 'permissao'
    id_permissao = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_permissao = Column(String(50), nullable=False, unique=True)
    descricao_permissao = Column(Text, nullable=False)

    cargos = relationship("Cargo", secondary=cargo_permissao, back_populates="permissoes")


Index('ix_depoimento_id_usuario', Depoimento.id_usuario)
Index('ix_depoimento_id_inquerito', Depoimento.id_inquerito)
Index('ix_job_id_depoimento', JobProcessamentoIA.id_depoimento)
Index('ix_termos_id_job', TermosFinais.id_job)
Index('ix_termos_data_exportacao', TermosFinais.data_exportacao_pdf)