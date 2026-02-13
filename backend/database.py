import os
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
_db_pool = None


def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    return psycopg2.connect(DATABASE_URL)


def init_db_pool(minconn=1, maxconn=10):
    global _db_pool
    if _db_pool is None:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is not set")
        _db_pool = ThreadedConnectionPool(minconn=minconn, maxconn=maxconn, dsn=DATABASE_URL)
    return _db_pool


def close_db_pool():
    global _db_pool
    if _db_pool is not None:
        _db_pool.closeall()
        _db_pool = None


@contextmanager
def _managed_connection():
    using_pool = _db_pool is not None
    conn = _db_pool.getconn() if using_pool else get_db_connection()
    try:
        yield conn
    finally:
        if using_pool:
            _db_pool.putconn(conn)
        else:
            conn.close()


def execute_query(query, params=None, fetch=False):
    with _managed_connection() as conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                result = None
                if fetch == "one":
                    result = cur.fetchone()
                elif fetch:
                    result = cur.fetchall()
                conn.commit()
                return result
        except Exception:
            conn.rollback()
            raise
