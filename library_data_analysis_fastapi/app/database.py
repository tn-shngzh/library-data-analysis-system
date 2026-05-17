import asyncio
from concurrent.futures import ThreadPoolExecutor
import psycopg
import psycopg_pool
from typing import Generator, Callable, Any
import logging
from app.config import DB_CONFIG

_pool = None
_logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=50)


def get_connection_string():
    return (
        f"host={DB_CONFIG['host']} "
        f"port={DB_CONFIG['port']} "
        f"dbname={DB_CONFIG['dbname']} "
        f"user={DB_CONFIG['user']} "
        f"password={DB_CONFIG['password']}"
    )


def init_db_pool():
    global _pool
    conn_string = get_connection_string()
    _pool = psycopg_pool.ConnectionPool(
        conninfo=conn_string,
        min_size=10,
        max_size=50,
        timeout=10
    )
    ensure_indexes()


def ensure_indexes():
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_circ_borrow_date ON circulations(borrow_date)",
        "CREATE INDEX IF NOT EXISTS idx_circ_borrow_date_status ON circulations(borrow_date, status)",
        "CREATE INDEX IF NOT EXISTS idx_circ_borrower_id ON circulations(borrower_id)",
        "CREATE INDEX IF NOT EXISTS idx_circ_bib_id ON circulations(bib_id)",
        "CREATE INDEX IF NOT EXISTS idx_circ_status ON circulations(status)",
        "CREATE INDEX IF NOT EXISTS idx_borrowers_degree ON borrowers(degree)",
        "CREATE INDEX IF NOT EXISTS idx_book_cat_bib_id ON book_categories(bib_id)",
    ]
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            for sql in indexes:
                try:
                    cur.execute(sql)
                except Exception as e:
                    _logger.warning("Create index failed: %s, Error: %s", sql, e)
        conn.commit()
    except Exception as e:
        _logger.warning("ensure_indexes failed: %s", e)
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
    finally:
        if conn:
            release_db_connection(conn)


def get_db_connection():
    global _pool
    if _pool is None:
        init_db_pool()
    if _pool is None:
        raise Exception("Database connection pool initialization failed")
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


async def run_sync(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    loop = asyncio.get_running_loop()
    if kwargs:
        from functools import partial
        return await loop.run_in_executor(_executor, partial(func, *args, **kwargs))
    return await loop.run_in_executor(_executor, func, *args)


async def run_sync_db(query_func: Callable[..., Any]) -> Any:
    def _with_connection():
        conn = get_db_connection()
        try:
            conn.rollback()
            return query_func(conn)
        except Exception:
            try:
                conn.rollback()
            except Exception as rollback_err:
                _logger.warning("Rollback failed: %s", rollback_err)
            raise
        finally:
            release_db_connection(conn)

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, _with_connection)