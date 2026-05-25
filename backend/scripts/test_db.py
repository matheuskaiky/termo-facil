import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID, BYTEA

@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(UUID, 'sqlite')
def compile_uuid_sqlite(type_, compiler, **kw):
    return "VARCHAR(36)"

@compiles(BYTEA, 'sqlite')
def compile_bytea_sqlite(type_, compiler, **kw):
    return "BLOB"

from sqlalchemy import create_engine
from app.models import Base

engine = create_engine('sqlite:///:memory:')

try:
    Base.metadata.create_all(bind=engine)
    print("Success")
except Exception as e:
    print(f"Error: {e}")
