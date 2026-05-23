from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import List, Any
from app.db import get_db
from app.models import Depoimento, Inquerito, Depoente, Usuario, JobProcessamentoIA, StatusJob, TipoDepoente
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/")
def listar_processos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
) -> Any:
    """
    Lista os depoimentos (processos).
    Filtra por id_usuario se o cargo for 'Escrivão'.
    Retorna todos da delegacia se for 'Delegado' ou 'Admin'.
    """
    cargo_nome = current_user.cargo.nome_cargo if current_user.cargo else ""
    
    query = db.query(Depoimento).options(
        joinedload(Depoimento.inquerito),
        joinedload(Depoimento.depoente),
        joinedload(Depoimento.usuario),
        joinedload(Depoimento.jobs)
    )

    if cargo_nome == "Escrivão":
        query = query.filter(Depoimento.id_usuario == current_user.id_usuario)
    elif cargo_nome in ["Delegado", "Admin"]:
        # Se quiser filtrar apenas da delegacia do usuário:
        query = query.join(Usuario).filter(Usuario.id_delegacia == current_user.id_delegacia)

    depoimentos = query.order_by(Depoimento.data_hora_reg.desc()).all()

    resultados = []
    for d in depoimentos:
        ultimo_job = max(d.jobs, key=lambda j: j.data_criacao) if d.jobs else None
        job_status = ultimo_job.status if ultimo_job else "Sem Upload"
        resultados.append({
            "id_depoimento": str(d.id_depoimento),
            "num_procedimento": d.inquerito.num_procedimento if d.inquerito else "N/A",
            "nome_depoente": d.depoente.nome_depoente if d.depoente else "N/A",
            "tipo_depoente": d.tipo_depoente,
            "data_hora_reg": d.data_hora_reg.isoformat() if d.data_hora_reg else None,
            "escrivao": d.usuario.nome if d.usuario else "N/A",
            "status_job": job_status
        })

    return resultados

@router.post("/novo")
def criar_processo_mock(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
) -> Any:
    """
    Cria um Depoimento mock para testar a tela de Auditoria/Upload (MVP).
    Utiliza um Inquerito e Depoente existentes para simplificar.
    """
    inquerito = db.query(Inquerito).first()
    depoente = db.query(Depoente).first()
    
    if not inquerito or not depoente:
        raise HTTPException(status_code=500, detail="Execute o seed_db.py primeiro.")
        
    novo_depoimento = Depoimento(
        id_inquerito=inquerito.id_inquerito,
        id_usuario=current_user.id_usuario,
        id_depoente=depoente.id_depoente,
        tipo_depoente=TipoDepoente.TESTEMUNHA
    )
    
    db.add(novo_depoimento)
    db.commit()
    db.refresh(novo_depoimento)
    
    return {"id_depoimento": str(novo_depoimento.id_depoimento)}
