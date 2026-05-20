from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Usuario
import uuid

def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: str = Header(None, alias="X-User-Id")
) -> Usuario:
    """
    Dependency to retrieve the currently logged in / simulated user.
    Reads from the 'X-User-Id' header. If absent, falls back to the first user in the database.
    """
    if x_user_id:
        try:
            user_uuid = uuid.UUID(x_user_id)
            user = db.query(Usuario).filter(Usuario.id_usuario == user_uuid).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuário não encontrado no sistema."
                )
            return user
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de ID de usuário inválido."
            )
    else:
        # Fallback for dev / mock environment
        user = db.query(Usuario).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nenhum usuário cadastrado no banco de dados. Por favor, execute o seed."
            )
        return user

class RequirePermission:
    """
    Dependency to require a specific permission for an API endpoint.
    Example: Depends(RequirePermission('GERAR_PDF'))
    """
    def __init__(self, permission_name: str):
        self.permission_name = permission_name

    def __call__(
        self,
        current_user: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> Usuario:
        if not current_user.cargo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="O usuário não possui nenhum cargo atribuído."
            )
        
        # Check permissions associated with the user's role (cargo)
        permissions = [p.nome_permissao for p in current_user.cargo.permissoes]
        if self.permission_name not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado: Permissão '{self.permission_name}' é necessária."
            )
        
        return current_user
