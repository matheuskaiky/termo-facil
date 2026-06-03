from sqlalchemy.orm import Query
from app.models import Depoimento, Inquerito, Usuario
from app.core.permissions import Permission


def user_has_permission(user: Usuario, permission: str) -> bool:
    """True if the user's cargo grants the given permission."""
    if not user.cargo:
        return False
    return any(p.nome_permissao == permission for p in user.cargo.permissoes)


def apply_depoimento_scope(query: Query, user: Usuario) -> Query:
    """
    Applies row-level authorization scoping to any query that includes Depoimento.
    - VER_TODOS_TERMOS: sees everything, regardless of cargo (no filter)
    - Escrivão: sees only their own depoimentos (by id_usuario)
    - Delegado: sees all depoimentos from their delegacia (via Inquerito.id_delegacia)
    - Admin / Gestor Estratégico: no filter applied
    """
    if user_has_permission(user, Permission.VER_TODOS_TERMOS):
        return query
    cargo_nome = user.cargo.nome_cargo if user.cargo else ""
    if cargo_nome == "Escrivão":
        return query.filter(Depoimento.id_usuario == user.id_usuario)
    if cargo_nome == "Delegado":
        return (
            query
            .join(Inquerito, Depoimento.id_inquerito == Inquerito.id_inquerito)
            .filter(Inquerito.id_delegacia == user.id_delegacia)
        )
    return query
