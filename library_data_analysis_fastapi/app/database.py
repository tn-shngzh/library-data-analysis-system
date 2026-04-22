import psycopg2
from app.config import DB_CONFIG


def get_db_connection():
    conn_str = (
        f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} "
        f"dbname={DB_CONFIG['dbname']} user={DB_CONFIG['user']} "
        f"password={DB_CONFIG['password']}"
    )
    return psycopg2.connect(conn_str)
