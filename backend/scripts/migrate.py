"""
Schema migration script — run after any model change that adds columns to existing tables.
Safe to run multiple times (uses ADD COLUMN IF NOT EXISTS).

Usage:
    cd backend
    python scripts/migrate.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.db import engine

# Each entry: (table, column, DDL fragment)
MIGRATIONS = [
    (
        "job_processamento_ia",
        "data_criacao",
        "ALTER TABLE job_processamento_ia "
        "ADD COLUMN IF NOT EXISTS data_criacao TIMESTAMP WITHOUT TIME ZONE "
        "NOT NULL DEFAULT NOW()",
    ),
    (
        "job_processamento_ia",
        "data_criacao (ensure default)",
        # The column may pre-exist without a default (ADD COLUMN IF NOT EXISTS
        # skipped it), so the model's server_default never lands at the DB and
        # INSERTs hit a NOT NULL violation. Idempotent: setting it again is a no-op.
        "ALTER TABLE job_processamento_ia ALTER COLUMN data_criacao SET DEFAULT NOW()",
    ),
    (
        "usuario",
        "senha_hash",
        "ALTER TABLE usuario "
        "ADD COLUMN IF NOT EXISTS senha_hash VARCHAR(255)",
    ),
    (
        "usuario",
        "must_change_password",
        "ALTER TABLE usuario "
        "ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN NOT NULL DEFAULT FALSE",
    ),
    (
        "termos_finais",
        "segmentos_asr",
        "ALTER TABLE termos_finais "
        "ADD COLUMN IF NOT EXISTS segmentos_asr JSONB",
    ),
    (
        "termos_finais",
        "data_exportacao_pdf",
        "ALTER TABLE termos_finais "
        "ADD COLUMN IF NOT EXISTS data_exportacao_pdf TIMESTAMP WITHOUT TIME ZONE",
    ),
    (
        "termos_finais",
        "storage_path_pdf",
        "ALTER TABLE termos_finais "
        "ADD COLUMN IF NOT EXISTS storage_path_pdf VARCHAR(512)",
    ),
    (
        "midia_bruta",
        "storage_path (drop not null)",
        # RN-04: the LGPD expurgo nulls storage_path after deleting the audio.
        # DROP NOT NULL is idempotent in PostgreSQL.
        "ALTER TABLE midia_bruta ALTER COLUMN storage_path DROP NOT NULL",
    ),
    (
        "status_job_enum",
        "Transcrevendo",
        "ALTER TYPE status_job_enum ADD VALUE IF NOT EXISTS 'Transcrevendo'",
    ),
    (
        "status_job_enum",
        "Extraindo Dados",
        "ALTER TYPE status_job_enum ADD VALUE IF NOT EXISTS 'Extraindo Dados'",
    ),
    (
        "status_job_enum",
        "Gerando Resumo",
        "ALTER TYPE status_job_enum ADD VALUE IF NOT EXISTS 'Gerando Resumo'",
    ),
    # ── Delegacia: remove cod_sinesp, add structured address + IBGE ──────────
    (
        "delegacia",
        "drop cod_sinesp",
        "ALTER TABLE delegacia DROP COLUMN IF EXISTS cod_sinesp",
    ),
    ("delegacia", "tipo", "ALTER TABLE delegacia ADD COLUMN IF NOT EXISTS tipo VARCHAR(100)"),
    ("delegacia", "sigla", "ALTER TABLE delegacia ADD COLUMN IF NOT EXISTS sigla VARCHAR(30)"),
    ("delegacia", "cep", "ALTER TABLE delegacia ADD COLUMN IF NOT EXISTS cep VARCHAR(9)"),
    ("delegacia", "logradouro", "ALTER TABLE delegacia ADD COLUMN IF NOT EXISTS logradouro VARCHAR(255)"),
    ("delegacia", "numero", "ALTER TABLE delegacia ADD COLUMN IF NOT EXISTS numero VARCHAR(20)"),
    ("delegacia", "complemento", "ALTER TABLE delegacia ADD COLUMN IF NOT EXISTS complemento VARCHAR(255)"),
    ("delegacia", "bairro", "ALTER TABLE delegacia ADD COLUMN IF NOT EXISTS bairro VARCHAR(255)"),
    ("delegacia", "municipio", "ALTER TABLE delegacia ADD COLUMN IF NOT EXISTS municipio VARCHAR(255)"),
    ("delegacia", "uf", "ALTER TABLE delegacia ADD COLUMN IF NOT EXISTS uf VARCHAR(2)"),
    ("delegacia", "cod_ibge", "ALTER TABLE delegacia ADD COLUMN IF NOT EXISTS cod_ibge VARCHAR(7)"),
    ("delegacia", "telefone", "ALTER TABLE delegacia ADD COLUMN IF NOT EXISTS telefone VARCHAR(40)"),
    ("delegacia", "email", "ALTER TABLE delegacia ADD COLUMN IF NOT EXISTS email VARCHAR(255)"),
    (
        "delegacia",
        "ativo",
        "ALTER TABLE delegacia ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT TRUE",
    ),
    # ── Usuario: active/inactive status ──────────────────────────────────────
    (
        "usuario",
        "ativo",
        "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT TRUE",
    ),
    # ── Depoimento: soft-delete (descarte) ───────────────────────────────────
    (
        "depoimento",
        "descartado",
        "ALTER TABLE depoimento ADD COLUMN IF NOT EXISTS descartado BOOLEAN NOT NULL DEFAULT FALSE",
    ),
    ("depoimento", "data_descarte", "ALTER TABLE depoimento ADD COLUMN IF NOT EXISTS data_descarte TIMESTAMP WITHOUT TIME ZONE"),
    (
        "depoimento",
        "id_usuario_descarte",
        "ALTER TABLE depoimento ADD COLUMN IF NOT EXISTS id_usuario_descarte UUID REFERENCES usuario(id_usuario)",
    ),
    # ── Depoente: optional structured address + IBGE ─────────────────────────
    ("depoente", "cep", "ALTER TABLE depoente ADD COLUMN IF NOT EXISTS cep VARCHAR(9)"),
    ("depoente", "logradouro", "ALTER TABLE depoente ADD COLUMN IF NOT EXISTS logradouro VARCHAR(255)"),
    ("depoente", "numero", "ALTER TABLE depoente ADD COLUMN IF NOT EXISTS numero VARCHAR(20)"),
    ("depoente", "complemento", "ALTER TABLE depoente ADD COLUMN IF NOT EXISTS complemento VARCHAR(255)"),
    ("depoente", "bairro", "ALTER TABLE depoente ADD COLUMN IF NOT EXISTS bairro VARCHAR(255)"),
    ("depoente", "municipio", "ALTER TABLE depoente ADD COLUMN IF NOT EXISTS municipio VARCHAR(255)"),
    ("depoente", "uf", "ALTER TABLE depoente ADD COLUMN IF NOT EXISTS uf VARCHAR(2)"),
    ("depoente", "cod_ibge", "ALTER TABLE depoente ADD COLUMN IF NOT EXISTS cod_ibge VARCHAR(7)"),
    # ── New permission: VER_TODOS_TERMOS ─────────────────────────────────────
    (
        "permissao",
        "VER_TODOS_TERMOS",
        "INSERT INTO permissao (id_permissao, nome_permissao, descricao_permissao) "
        "SELECT gen_random_uuid(), 'VER_TODOS_TERMOS', "
        "'Visualizar termos/processos de todos os usuários' "
        "WHERE NOT EXISTS (SELECT 1 FROM permissao WHERE nome_permissao = 'VER_TODOS_TERMOS')",
    ),
    (
        "cargo_permissao",
        "grant VER_TODOS_TERMOS to Admin/Gestor",
        "INSERT INTO cargo_permissao (id_cargo, id_permissao) "
        "SELECT c.id_cargo, p.id_permissao FROM cargo c, permissao p "
        "WHERE p.nome_permissao = 'VER_TODOS_TERMOS' "
        "AND c.nome_cargo IN ('Admin', 'Gestor Estratégico') "
        "AND NOT EXISTS (SELECT 1 FROM cargo_permissao cp "
        "WHERE cp.id_cargo = c.id_cargo AND cp.id_permissao = p.id_permissao)",
    ),
    # ── Permission: CRIAR_TERMO (required to create a processo) ───────────────
    (
        "permissao",
        "CRIAR_TERMO",
        "INSERT INTO permissao (id_permissao, nome_permissao, descricao_permissao) "
        "SELECT gen_random_uuid(), 'CRIAR_TERMO', "
        "'Criar novo processo/termo de depoimento' "
        "WHERE NOT EXISTS (SELECT 1 FROM permissao WHERE nome_permissao = 'CRIAR_TERMO')",
    ),
    (
        "cargo_permissao",
        "grant CRIAR_TERMO to Admin/Escrivão",
        "INSERT INTO cargo_permissao (id_cargo, id_permissao) "
        "SELECT c.id_cargo, p.id_permissao FROM cargo c, permissao p "
        "WHERE p.nome_permissao = 'CRIAR_TERMO' "
        "AND c.nome_cargo IN ('Admin', 'Escrivão') "
        "AND NOT EXISTS (SELECT 1 FROM cargo_permissao cp "
        "WHERE cp.id_cargo = c.id_cargo AND cp.id_permissao = p.id_permissao)",
    ),
]


def run():
    with engine.connect() as conn:
        for table, column, ddl in MIGRATIONS:
            conn.execute(text(ddl))
            print(f"  OK  {table}.{column}")
        conn.commit()
    print("Migrações aplicadas com sucesso.")


if __name__ == "__main__":
    run()
