from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.models import Usuario
from app.schemas.admin import UsuarioSchema
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/me", response_model=UsuarioSchema)
def get_me(current_user: Usuario = Depends(get_current_user)):
    """
    Get the currently active simulated user.
    """
    return current_user

@router.get("/users", response_model=List[UsuarioSchema])
def list_sim_users(db: Session = Depends(get_db)):
    """
    List all users in the system (no protection, used for user switching in frontend).
    """
    return db.query(Usuario).all()
