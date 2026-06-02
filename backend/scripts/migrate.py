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
