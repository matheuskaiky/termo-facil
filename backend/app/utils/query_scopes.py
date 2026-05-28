from sqlalchemy.orm import Query
from app.models import Depoimento, Inquerito, Usuario


def apply_depoimento_scope(query: Query, user: Usuario) -> Query:
    """
    Applies row-level authorization scoping to any query that includes Depoimento.
    - Escrivão: sees only their own depoimentos (by id_usuario)
    - Delegado: sees all depoimentos from their delegacia (via Inquerito.id_delegacia)
    - Admin / Gestor Estratégico: no filter applied
    """
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
