import os
import psycopg
from contextlib import contextmanager

DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/postgres"
)

def get_conn():
    # Autocommit off; we manage transactions explicitly.
    return psycopg.connect(DSN)

@contextmanager
def tx():
    with get_conn() as conn:
        with conn.cursor() as cur:
            try:
                yield cur
                conn.commit()
            except:
                conn.rollback()
                raise