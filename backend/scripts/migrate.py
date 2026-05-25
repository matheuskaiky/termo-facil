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
