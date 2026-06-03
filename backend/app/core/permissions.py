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
