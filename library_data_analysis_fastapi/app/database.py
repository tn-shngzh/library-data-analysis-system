import asyncio
from concurrent.futures import ThreadPoolExecutor
from psycopg2 import pool
from typing import Generator, Callable, Any
import logging
from app.config import DB_CONFIG

_pool = None
_logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=50)


def init_db_pool():
    global _pool
    _pool = pool.ThreadedConnectionPool(
        10, 50,
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        dbname=DB_CONFIG['dbname'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    ensure_indexes()


def ensure_indexes():
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_circ_action_date_action ON circulations(action_date, action)",
        "CREATE INDEX IF NOT EXISTS idx_circ_borrower_action ON circulations(borrower_id, action)",
        "CREATE INDEX IF NOT EXISTS idx_circ_borrower_bib_action ON circulations(borrower_id, bib_id, action)",
        "CREATE INDEX IF NOT EXISTS idx_circ_bib_action ON circulations(bib_id, action)",
        "CREATE INDEX IF NOT EXISTS idx_book_categories_category ON book_categories(category)",
        "CREATE INDEX IF NOT EXISTS idx_book_categories_bib ON book_categories(bib_id)",
    ]
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            for sql in indexes:
                try:
                    cur.execute(sql)
                except Exception as e:
                    _logger.warning("创建索引失败: %s, 错误: %s", sql, e)
        conn.commit()
    except Exception as e:
        _logger.warning("ensure_indexes 执行失败: %s", e)
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
        raise Exception("数据库连接池初始化失败")
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
    """Run a synchronous function in the thread pool executor."""
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
                _logger.warning("回滚失败: %s", rollback_err)
            raise
        finally:
            release_db_connection(conn)
    
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, _with_connection)
