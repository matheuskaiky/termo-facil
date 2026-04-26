import sys
import os
from datetime import date
import uuid
import json

# Adiciona a raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal
from app.models import (
    Delegacia, Usuario, Depoente, Inquerito, Depoimento, Modelo,
    CargoUsuario, TipoDepoente, TipoModelo
)

def seed():
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
            
        # Usuario
        usuario = db.query(Usuario).first()
        if not usuario:
            usuario = Usuario(
                id_delegacia=delegacia.id_delegacia,
                matricula="123456",
                nome="João Silva",
                cargo=CargoUsuario.ESCRIVAO
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
