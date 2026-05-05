import sys
import os
from datetime import date
import uuid
import json

# Adiciona a raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal, engine, Base
from app.models import (
    Delegacia, Usuario, Depoente, Inquerito, Depoimento, Modelo,
    TipoDepoente, TipoModelo, Cargo, Permissao
)

def seed():
    # Garante que as novas tabelas (Cargo, Permissao) existam no banco!
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Verifica se já existe um modelo ASR
        modelo_asr = db.query(Modelo).filter(Modelo.tipo_modelo == TipoModelo.ASR).first()
        if not modelo_asr:
            modelo_asr = Modelo(
                nome_modelo="Whisper Turbo (Mock)",
                desenvolvedora="OpenAI",
                tipo_modelo=TipoModelo.ASR
            )
            db.add(modelo_asr)

        # Verifica se já existe um modelo LLM
        modelo_llm = db.query(Modelo).filter(Modelo.tipo_modelo == TipoModelo.LLM).first()
        if not modelo_llm:
            modelo_llm = Modelo(
                nome_modelo="vLLM Llama 3 (Mock)",
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
        permissoes_chaves = ['UPLOAD_AUDIO', 'EDITAR_TERMO', 'GERAR_PDF', 'GERENCIAR_USUARIOS']
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
        
        db.flush()

        # Usuario
        usuario = db.query(Usuario).first()
        if not usuario:
            usuario = Usuario(
                id_delegacia=delegacia.id_delegacia,
                id_cargo=cargo_escrivao.id_cargo,
                matricula="123456",
                nome="João Silva"
            )
            db.add(usuario)

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

        # Depoimento
        depoimento = db.query(Depoimento).first()
        if not depoimento:
            depoimento = Depoimento(
                id_inquerito=inquerito.id_inquerito,
                id_usuario=usuario.id_usuario,
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
        print("Use estes IDs para testar o upload!")
        
        # Salva num arquivo json na raiz do frontend para podermos usar os IDs automaticamente no Mock
        mock_data = {
            "id_depoimento": str(depoimento.id_depoimento),
            "id_modelo_asr": str(modelo_asr.id_modelo),
            "id_modelo_llm": str(modelo_llm.id_modelo)
        }
        
        frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/src/mock_ids.json"))
        with open(frontend_path, "w") as f:
            json.dump(mock_data, f)
            
        print(f"IDs salvos em: {frontend_path}")

    except Exception as e:
        print(f"Erro ao rodar seed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
