from psycopg2 import pool
from typing import Generator
from app.config import DB_CONFIG

_pool = None


def init_db_pool():
    global _pool
    _pool = pool.ThreadedConnectionPool(
        1, 20,
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        dbname=DB_CONFIG['dbname'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )


def get_db_connection():
    global _pool
    if _pool is None:
        init_db_pool()
    return _pool.getconn()


def release_db_connection(conn):
    if _pool:
        _pool.putconn(conn)


def get_db() -> Generator:
    conn = get_db_connection()
    try:
        yield conn
    finally:
        release_db_connection(conn)
