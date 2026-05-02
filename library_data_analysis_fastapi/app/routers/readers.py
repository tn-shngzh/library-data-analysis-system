import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.database import run_sync_db
from app.config import education_levels
from app.cache import cache

router = APIRouter(prefix="/api/readers", tags=["读者分析"])
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_reader_stats():
    cache_key = "readers:stats"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM borrowers")
            total_readers = cur.fetchone()[0]

            today = datetime.now().date()
            this_month_start = int(today.replace(day=1).strftime('%Y%m%d'))
            this_month_end = int(today.strftime('%Y%m%d'))

            cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE action_date BETWEEN %s AND %s", (this_month_start, this_month_end))
            month_active = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE action_date BETWEEN %s AND %s AND action = 'CKO'", (this_month_start, this_month_end))
            month_borrowers = cur.fetchone()[0]

            try:
                cur.execute("SELECT AVG(borrow_count) FROM mv_reader_stats")
                avg_borrows = cur.fetchone()[0]
            except Exception:
                conn.rollback()
                cur.execute("SELECT COUNT(*)::float / NULLIF(COUNT(DISTINCT borrower_id), 0) FROM circulations")
                avg_borrows = cur.fetchone()[0]

            return {
                "total_readers": total_readers,
                "month_active": month_active,
                "month_new": month_borrowers,
                "avg_borrows": round(avg_borrows, 1) if avg_borrows else 0
            }

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 60)
        return result
    except Exception as e:
        logger.error("获取读者统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取读者统计失败: {e}")


@router.get("/types")
async def get_reader_types():
    cache_key = "readers:types"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    SELECT el.name, COUNT(b.id) as count
                    FROM borrowers b
                    JOIN education_levels el ON b.degree = el.code
                    GROUP BY el.name
                    ORDER BY count DESC
                """)
                rows = cur.fetchall()
            except Exception:
                conn.rollback()
                cur.execute("""
                    SELECT b.degree, COUNT(b.id) as count
                    FROM borrowers b
                    GROUP BY b.degree
                    ORDER BY count DESC
                """)
                raw_rows = cur.fetchall()
                rows = [(education_levels.get(r[0], r[0]), r[1]) for r in raw_rows]
            total = sum(r[1] for r in rows)
            result = []
            for i, r in enumerate(rows):
                pct = round(r[1] / total * 100, 1) if total else 0
                if i == len(rows) - 1:
                    pct = round(100.0 - sum(round(rr[1] / total * 100, 1) for rr in rows[:-1]), 1)
                result.append({"name": r[0], "count": r[1], "percent": pct})
            return result

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 300)
        return result
    except Exception as e:
        logger.error("获取读者类型统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取读者类型统计失败: {e}")


@router.get("/monthly-trend")
async def get_monthly_trend(year: Optional[int] = None):
    cached = cache.cache_get("readers:monthly-trend")
    if cached is not None:
        return cached

    def format_month(m):
        return f"{m // 100}年{m % 100}月"

    def _query(conn):
        with conn.cursor() as cur:
            try:
                if year is not None:
                    cur.execute("""
                        SELECT
                            ma.month,
                            ma.active_count,
                            COALESCE(bc.borrow_count, 0) as borrow_count
                        FROM mv_monthly_active ma
                        LEFT JOIN (
                            SELECT
                                (action_date / 100) as month,
                                COUNT(*) as borrow_count
                            FROM circulations
                            WHERE action = 'CKO'
                            GROUP BY (action_date / 100)
                        ) bc ON ma.month = bc.month
                        WHERE (ma.month / 100) = %s
                        ORDER BY ma.month
                    """, (year,))
                else:
                    cur.execute("""
                        SELECT
                            ma.month,
                            ma.active_count,
                            COALESCE(bc.borrow_count, 0) as borrow_count
                        FROM mv_monthly_active ma
                        LEFT JOIN (
                            SELECT
                                (action_date / 100) as month,
                                COUNT(*) as borrow_count
                            FROM circulations
                            WHERE action = 'CKO'
                            GROUP BY (action_date / 100)
                        ) bc ON ma.month = bc.month
                        ORDER BY ma.month
                    """)
                rows = cur.fetchall()
                return [
                    {"month": format_month(r[0]), "activeCount": r[1], "borrowCount": r[2]}
                    for r in rows
                ]
            except Exception:
                conn.rollback()
                if year is not None:
                    cur.execute("""
                        SELECT
                            (action_date / 100) as month,
                            COUNT(DISTINCT borrower_id) as active_count,
                            COUNT(*) FILTER (WHERE action = 'CKO') as borrow_count
                        FROM circulations
                        WHERE (action_date / 10000) = %s
                        GROUP BY (action_date / 100)
                        ORDER BY month
                    """, (year,))
                else:
                    cur.execute("""
                        SELECT
                            (action_date / 100) as month,
                            COUNT(DISTINCT borrower_id) as active_count,
                            COUNT(*) FILTER (WHERE action = 'CKO') as borrow_count
                        FROM circulations
                        GROUP BY (action_date / 100)
                        ORDER BY month
                    """)
                rows = cur.fetchall()
                return [
                    {"month": format_month(r[0]), "activeCount": r[1], "borrowCount": r[2]}
                    for r in rows
                ]

    try:
        result = await run_sync_db(_query)
        cache.cache_set("readers:monthly-trend", result, 300)
        return result
    except Exception as e:
        logger.error("获取读者月度趋势失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取读者月度趋势失败: {e}")


@router.get("/top")
async def get_top_readers():
    cached = cache.cache_get("readers:top")
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    SELECT rs.borrower_id, rs.borrow_count, b.degree
                    FROM mv_reader_stats rs
                    JOIN borrowers b ON rs.borrower_id = b.id
                    ORDER BY rs.borrow_count DESC
                    LIMIT 10
                """)
                rows = cur.fetchall()
            except Exception:
                conn.rollback()
                cur.execute("""
                    SELECT c.borrower_id, COUNT(*) as borrow_count, b.degree
                    FROM circulations c
                    JOIN borrowers b ON c.borrower_id = b.id
                    WHERE c.action = 'CKO'
                    GROUP BY c.borrower_id, b.degree
                    ORDER BY borrow_count DESC
                    LIMIT 10
                """)
                rows = cur.fetchall()
            return rows

    try:
        rows = await run_sync_db(_query)
        result = [
            {
                "rank": i + 1,
                "id": r[0],
                "borrowed": r[1],
                "type": education_levels.get(r[2], r[2])
            }
            for i, r in enumerate(rows)
        ]
        cache.cache_set("readers:top", result, 300)
        return result
    except Exception as e:
        logger.error("获取热门读者失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取热门读者失败: {e}")
