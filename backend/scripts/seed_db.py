import sys
import os
from datetime import date
import uuid

# Adiciona a raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal, engine, Base
from app.models import (
    Delegacia, Usuario, Depoente, Inquerito, Depoimento, Modelo,
    TipoDepoente, TipoModelo, Cargo, Permissao
)
from app.core.security import hash_senha
from scripts.migrate import run as run_migrations

_DEFAULT_PASSWORD = "senha123"

def seed():
    # Garante que as novas tabelas existam e aplica migrações de colunas
    Base.metadata.create_all(bind=engine)
    run_migrations()

    db = SessionLocal()
    try:
        # Verifica se já existe um modelo ASR
        modelo_asr = db.query(Modelo).filter(Modelo.tipo_modelo == TipoModelo.ASR).first()
        if not modelo_asr:
            modelo_asr = Modelo(
                nome_modelo="Whisper base",
                desenvolvedora="OpenAI",
                tipo_modelo=TipoModelo.ASR
            )
            db.add(modelo_asr)

        # Verifica se já existe um modelo LLM
        modelo_llm = db.query(Modelo).filter(Modelo.tipo_modelo == TipoModelo.LLM).first()
        if not modelo_llm:
            modelo_llm = Modelo(
                nome_modelo="Ollama llama3",
                desenvolvedora="Meta",
                tipo_modelo=TipoModelo.LLM
            )
            db.add(modelo_llm)

        # Delegacia
        delegacia = db.query(Delegacia).first()
        if not delegacia:
            delegacia = Delegacia(
                nome_unidade="12ª Delegacia de Polícia",
                cod_sinesp="12DP-PI"
            )
            db.add(delegacia)
            db.flush() # Para gerar o ID
            
        # Permissões
        permissoes_chaves = ['UPLOAD_AUDIO', 'EDITAR_TERMO', 'GERAR_PDF', 'GERENCIAR_USUARIOS', 'REDEFINIR_SENHA', 'VER_METRICAS']
        permissoes_obj = {}
        for p in permissoes_chaves:
            perm = db.query(Permissao).filter(Permissao.nome_permissao == p).first()
            if not perm:
                perm = Permissao(nome_permissao=p, descricao_permissao=f"Permite {p}")
                db.add(perm)
                db.flush() # Flush to get ID if needed inside the loop, though we get the object reference
            else:
                permissoes_obj[p] = perm
                
        # If we added new ones, we need them in the dictionary
        for p in permissoes_chaves:
            if p not in permissoes_obj:
                permissoes_obj[p] = db.query(Permissao).filter(Permissao.nome_permissao == p).first()

        # Cargos
        cargo_admin = db.query(Cargo).filter(Cargo.nome_cargo == 'Admin').first()
        if not cargo_admin:
            cargo_admin = Cargo(nome_cargo='Admin')
            cargo_admin.permissoes = list(permissoes_obj.values())
            db.add(cargo_admin)
            
        cargo_escrivao = db.query(Cargo).filter(Cargo.nome_cargo == 'Escrivão').first()
        if not cargo_escrivao:
            cargo_escrivao = Cargo(nome_cargo='Escrivão')
            cargo_escrivao.permissoes = [permissoes_obj['UPLOAD_AUDIO'], permissoes_obj['EDITAR_TERMO'], permissoes_obj['GERAR_PDF']]
            db.add(cargo_escrivao)

        cargo_delegado = db.query(Cargo).filter(Cargo.nome_cargo == 'Delegado').first()
        if not cargo_delegado:
            cargo_delegado = Cargo(nome_cargo='Delegado')
            cargo_delegado.permissoes = [permissoes_obj['EDITAR_TERMO'], permissoes_obj['GERAR_PDF']]
            db.add(cargo_delegado)

        cargo_gestor = db.query(Cargo).filter(Cargo.nome_cargo == 'Gestor Estratégico').first()
        if not cargo_gestor:
            cargo_gestor = Cargo(nome_cargo='Gestor Estratégico')
            cargo_gestor.permissoes = [permissoes_obj['VER_METRICAS']]
            db.add(cargo_gestor)

        db.flush()

        # Usuarios — upsert: cria se não existe, seta senha_hash se estiver NULL
        usuario_escrivao = db.query(Usuario).filter(Usuario.matricula == "123456").first()
        if not usuario_escrivao:
            usuario_escrivao = Usuario(
                id_delegacia=delegacia.id_delegacia,
                id_cargo=cargo_escrivao.id_cargo,
                matricula="123456",
                nome="João Silva (Escrivão)",
                senha_hash=hash_senha(_DEFAULT_PASSWORD),
            )
            db.add(usuario_escrivao)
        elif not usuario_escrivao.senha_hash:
            usuario_escrivao.senha_hash = hash_senha(_DEFAULT_PASSWORD)

        usuario_delegado = db.query(Usuario).filter(Usuario.matricula == "789012").first()
        if not usuario_delegado:
            usuario_delegado = Usuario(
                id_delegacia=delegacia.id_delegacia,
                id_cargo=cargo_delegado.id_cargo,
                matricula="789012",
                nome="Maria Souza (Delegado)",
                senha_hash=hash_senha(_DEFAULT_PASSWORD),
            )
            db.add(usuario_delegado)
        elif not usuario_delegado.senha_hash:
            usuario_delegado.senha_hash = hash_senha(_DEFAULT_PASSWORD)

        usuario_admin = db.query(Usuario).filter(Usuario.matricula == "111111").first()
        if not usuario_admin:
            usuario_admin = Usuario(
                id_delegacia=delegacia.id_delegacia,
                id_cargo=cargo_admin.id_cargo,
                matricula="111111",
                nome="Carlos Admin (Admin)",
                senha_hash=hash_senha(_DEFAULT_PASSWORD),
            )
            db.add(usuario_admin)
        elif not usuario_admin.senha_hash:
            usuario_admin.senha_hash = hash_senha(_DEFAULT_PASSWORD)

        usuario_gestor = db.query(Usuario).filter(Usuario.matricula == "999999").first()
        if not usuario_gestor:
            usuario_gestor = Usuario(
                id_delegacia=delegacia.id_delegacia,
                id_cargo=cargo_gestor.id_cargo,
                matricula="999999",
                nome="Ana Gestora (Gestor Estratégico)",
                senha_hash=hash_senha(_DEFAULT_PASSWORD),
            )
            db.add(usuario_gestor)
        elif not usuario_gestor.senha_hash:
            usuario_gestor.senha_hash = hash_senha(_DEFAULT_PASSWORD)

        # Inquerito
        inquerito = db.query(Inquerito).first()
        if not inquerito:
            inquerito = Inquerito(
                id_delegacia=delegacia.id_delegacia,
                num_procedimento="IP-2026/001",
                data_instauracao=date.today()
            )
            db.add(inquerito)
            
        # Depoente
        depoente = db.query(Depoente).first()
        if not depoente:
            depoente = Depoente(
                cpf="00011122233",
                nome_depoente="José Maria da Silva"
            )
            db.add(depoente)
            db.flush()

        db.commit()  # Persiste cargos, usuários, inquerito e depoente

        # Depoimento
        depoimento = db.query(Depoimento).first()
        if not depoimento:
            depoimento = Depoimento(
                id_inquerito=inquerito.id_inquerito,
                id_usuario=usuario_escrivao.id_usuario,
                id_depoente=depoente.id_depoente,
                tipo_depoente=TipoDepoente.SUSPEITO
            )
            db.add(depoimento)
            db.commit()

        # Agora recupera os IDs finais
        db.refresh(depoimento)
        db.refresh(modelo_asr)
        db.refresh(modelo_llm)

        print("=== Banco de dados populado com sucesso! ===")
        print(f"ID Depoimento: {depoimento.id_depoimento}")
        print(f"ID Modelo ASR: {modelo_asr.id_modelo}")
        print(f"ID Modelo LLM: {modelo_llm.id_modelo}")
        print("Modelos IA:")
        print(f"  ASR: {modelo_asr.nome_modelo}")
        print(f"  LLM: {modelo_llm.nome_modelo}")

    except Exception as e:
        print(f"Erro ao rodar seed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
