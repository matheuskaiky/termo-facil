class Permission:
    UPLOAD_AUDIO = "UPLOAD_AUDIO"
    EDITAR_TERMO = "EDITAR_TERMO"
    GERAR_PDF = "GERAR_PDF"
    GERENCIAR_USUARIOS = "GERENCIAR_USUARIOS"
    VER_METRICAS = "VER_METRICAS"
    CRIAR_TERMO = "CRIAR_TERMO"
    REDEFINIR_SENHA = "REDEFINIR_SENHA"
    # Lets a user see every user's termos/processos, bypassing the per-author scope.
    VER_TODOS_TERMOS = "VER_TODOS_TERMOS"
    # Access to the Dev/Debug benchmarking module (model comparison runs).
    ACESSAR_DEV_DEBUG = "ACESSAR_DEV_DEBUG"


# The Admin role is immutable and omnipotent: it ALWAYS resolves to every
# permission in the system (regardless of what is stored in cargo_permissao),
# and the Admin cargo itself may never be altered — not even by an Admin.
ADMIN_CARGO = "Admin"


def is_admin(user) -> bool:
    """True when the user's cargo is the immutable Admin role."""
    return bool(getattr(user, "cargo", None)) and user.cargo.nome_cargo == ADMIN_CARGO


def resolve_permissoes(user, db) -> list[str]:
    """
    Single source of truth for a user's effective permissions.
    Admin is omnipotent → returns the full catalogue of permission names.
    Everyone else gets exactly the permissions attached to their cargo.
    """
    from app.models import Permissao  # local import avoids import cycles
    if is_admin(user):
        return [p.nome_permissao for p in db.query(Permissao).all()]
    return [p.nome_permissao for p in user.cargo.permissoes] if user.cargo else []
