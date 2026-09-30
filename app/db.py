"""Read-only MySQL connection (soukchay_sysdata) with UTF-8 support."""
import pymysql
from pymysql.cursors import DictCursor

from .config import settings


def get_conn():
    """Open a new connection. Caller must close() it."""
    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset=settings.DB_CHARSET,
        cursorclass=DictCursor,
        autocommit=False,
    )


def query(sql, params=None):
    """Run a SELECT, return list of dict rows. Always read-only."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SET NAMES utf8mb4")
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()


def query_one(sql, params=None):
    rows = query(sql, params)
    return rows[0] if rows else None