import logging
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from app.database import run_sync_db
from app.config import education_levels
from app.cache import cache

router = APIRouter(prefix="/api/borrows", tags=["借阅分析"])
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_borrow_stats():
    cache_key = "borrows:stats"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT SUM(cko_count) as total_borrows, SUM(cki_count) as total_returns
                FROM monthly_history_cache
            """)
            row = cur.fetchone()
            total_borrows = row[0] or 0
            total_returns = row[1] or 0

            cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE status = 'borrowed'")
            active_borrowers = cur.fetchone()[0] or 0

            cur.execute("SELECT COUNT(DISTINCT bib_id) FROM circulations WHERE status = 'borrowed'")
            borrowed_books = cur.fetchone()[0] or 0

            cur.execute("SELECT COUNT(*) FROM borrowers")
            total_readers = cur.fetchone()[0] or 0

            cur.execute("SELECT COUNT(DISTINCT bib_id) FROM book_categories")
            total_books = cur.fetchone()[0] or 0

            cur.execute("SELECT COUNT(DISTINCT category) FROM book_categories")
            category_count = cur.fetchone()[0] or 0

            result = {
                "total_actions": total_borrows,
                "total_borrows": total_borrows,
                "total_returns": total_returns,
                "total_renewals": 0,
                "active_borrowers": active_borrowers,
                "borrowed_books": borrowed_books,
                "total_books": total_books,
                "total_readers": total_readers,
                "today_visits": active_borrowers,
                "today_borrows": 0,
                "today_returns": 0,
                "category_count": category_count,
                "cko_count": total_borrows,
                "cki_count": total_returns,
                "reh_count": 0,
                "rei_count": 0
            }
            return result

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取借阅统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取借阅统计失败: {e}")


@router.get("/action-stats")
async def get_action_stats(start_date: str = None, end_date: str = None):
    cache_key = f"borrows:action-stats:{start_date}:{end_date}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            if start_date and end_date:
                start_int = int(start_date.replace('-', ''))
                end_int = int(end_date.replace('-', ''))
                cur.execute("""
                    SELECT
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'borrowed') as borrowed,
                        COUNT(*) FILTER (WHERE status = 'returned') as returned,
                        COUNT(*) FILTER (WHERE renew_count > 0) as renewals
                    FROM circulations
                    WHERE borrow_date BETWEEN %s AND %s
                """, (start_int, end_int))
                row = cur.fetchone()
            else:
                one_year_ago = int((datetime.now() - timedelta(days=365)).strftime('%Y%m%d'))
                today_int = int(datetime.now().strftime('%Y%m%d'))
                cur.execute("""
                    SELECT
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'borrowed') as borrowed,
                        COUNT(*) FILTER (WHERE status = 'returned') as returned,
                        COUNT(*) FILTER (WHERE renew_count > 0) as renewals
                    FROM circulations
                    WHERE borrow_date BETWEEN %s AND %s
                """, (one_year_ago, today_int))
                row = cur.fetchone()

            total = row[0] if row else 1
            borrowed = row[1] if row[1] else 0
            returned = row[2] if row[2] else 0
            renewals = row[3] if row[3] else 0

            status_names = {
                'borrowed': '借出',
                'returned': '已还',
                'library_renewal': '馆内续借',
                'online_renewal': '网上续借'
            }
            status_colors = {
                'borrowed': '#d97706',
                'returned': '#10b981',
                'library_renewal': '#3b82f6',
                'online_renewal': '#8b5cf6'
            }

            result = [
                {'action': 'borrowed', 'name': status_names['borrowed'],
                 'count': borrowed, 'percent': round(borrowed / total * 100, 1) if total > 0 else 0, 'color': status_colors['borrowed']},
                {'action': 'returned', 'name': status_names['returned'],
                 'count': returned, 'percent': round(returned / total * 100, 1) if total > 0 else 0, 'color': status_colors['returned']},
                {'action': 'library_renewal', 'name': status_names['library_renewal'],
                 'count': renewals, 'percent': round(renewals / total * 100, 1) if total > 0 else 0, 'color': status_colors['library_renewal']},
                {'action': 'online_renewal', 'name': status_names['online_renewal'],
                 'count': 0, 'percent': 0, 'color': status_colors['online_renewal']},
            ]
            return result

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取操作统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取操作统计失败: {e}")


@router.get("/degree-stats")
async def get_degree_stats(start_date: str = None, end_date: str = None):
    cache_key = f"borrows:degree-stats:{start_date}:{end_date}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            if start_date and end_date:
                start_int = int(start_date.replace('-', ''))
                end_int = int(end_date.replace('-', ''))
                cur.execute("""
                    SELECT b.degree, COUNT(*) as count
                    FROM circulations c
                    JOIN borrowers b ON c.borrower_id = b.id
                    WHERE c.borrow_date BETWEEN %s AND %s
                    AND c.status = 'borrowed'
                    GROUP BY b.degree
                    ORDER BY count DESC
                """, (start_int, end_int))
            else:
                # 直接查询 circulations JOIN borrowers 按学历分组
                cur.execute("""
                    SELECT b.degree, COUNT(*) as count
                    FROM circulations c
                    JOIN borrowers b ON c.borrower_id = b.id
                    WHERE c.status = 'borrowed'
                    GROUP BY b.degree
                    ORDER BY count DESC
                """)
            raw_rows = cur.fetchall()
            total = sum(r[1] for r in raw_rows) if raw_rows else 0
            result = []
            for i, row in enumerate(raw_rows):
                code = row[0]
                cnt = row[1]
                pct = round(cnt / total * 100, 1) if total > 0 else 0
                if i == len(raw_rows) - 1 and total > 0:
                    pct = round(100.0 - sum(round(r[1] / total * 100, 1) for r in raw_rows[:-1]), 1)
                result.append({
                    "code": code,
                    "name": education_levels.get(code, code),
                    "count": cnt,
                    "percent": pct
                })
            return result

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取学历统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取学历统计失败: {e}")


@router.get("/daily-trend")
async def get_daily_trend(start_date: str = None, end_date: str = None):
    cache_key = f"borrows:daily-trend:{start_date}:{end_date}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    one_year_ago_int = int((datetime.now() - timedelta(days=365)).strftime('%Y%m%d'))

    def _query(conn):
        with conn.cursor() as cur:
            if start_date and end_date:
                start_int = int(start_date.replace('-', ''))
                end_int = int(end_date.replace('-', ''))
                cur.execute("""
                    SELECT borrow_date, COUNT(*) as count
                    FROM circulations
                    WHERE borrow_date BETWEEN %s AND %s
                    GROUP BY borrow_date
                    ORDER BY borrow_date
                """, (start_int, end_int))
            else:
                # 限制只获取最近一年的数据，避免全表扫描
                cur.execute("""
                    SELECT borrow_date, COUNT(*) as count
                    FROM circulations
                    WHERE borrow_date >= %s
                    GROUP BY borrow_date
                    ORDER BY borrow_date
                """, (one_year_ago_int,))
            rows = cur.fetchall()
            return [{"date": str(r[0]), "count": r[1]} for r in rows]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取日趋势失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取日趋势失败: {e}")


@router.get("/top-borrowers")
async def get_top_borrowers(start_date: str = None, end_date: str = None):
    cache_key = f"borrows:top-borrowers:{start_date}:{end_date}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            if start_date and end_date:
                start_int = int(start_date.replace('-', ''))
                end_int = int(end_date.replace('-', ''))
                cur.execute("""
                    SELECT c.borrower_id, b.degree, COUNT(*) as borrow_count
                    FROM circulations c
                    JOIN borrowers b ON c.borrower_id = b.id
                    WHERE c.borrow_date BETWEEN %s AND %s
                    AND c.status = 'borrowed'
                    GROUP BY c.borrower_id, b.degree
                    ORDER BY borrow_count DESC
                    LIMIT 15
                """, (start_int, end_int))
            else:
                three_years_ago = int((datetime.now().replace(year=datetime.now().year - 3)).strftime('%Y%m%d'))
                cur.execute("""
                    SELECT c.borrower_id, b.degree, COUNT(*) as borrow_count
                    FROM circulations c
                    JOIN borrowers b ON c.borrower_id = b.id
                    WHERE c.status = 'borrowed' AND c.borrow_date >= %s
                    GROUP BY c.borrower_id, b.degree
                    ORDER BY borrow_count DESC
                    LIMIT 15
                """, (three_years_ago,))
            rows = cur.fetchall()
            return [
                {
                    "rank": i + 1,
                    "id": r[0],
                    "type": education_levels.get(r[1], r[1]),
                    "borrowed": r[2]
                }
                for i, r in enumerate(rows)
            ]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取热门借阅者失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取热门借阅者失败: {e}")


@router.get("/top-books")
async def get_top_borrowed_books(start_date: str = None, end_date: str = None):
    cache_key = f"borrows:top-books:{start_date}:{end_date}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            if start_date and end_date:
                start_int = int(start_date.replace('-', ''))
                end_int = int(end_date.replace('-', ''))
                cur.execute("""
                    SELECT c.bib_id, bc.category, COUNT(*) as borrow_count, bc.name
                    FROM circulations c
                    LEFT JOIN book_categories bc ON c.bib_id = bc.bib_id
                    WHERE c.borrow_date BETWEEN %s AND %s
                    AND c.status = 'borrowed'
                    GROUP BY c.bib_id, bc.category, bc.name
                    ORDER BY borrow_count DESC
                    LIMIT 15
                """, (start_int, end_int))
            else:
                three_years_ago = int((datetime.now().replace(year=datetime.now().year - 3)).strftime('%Y%m%d'))
                cur.execute("""
                    SELECT c.bib_id, bc.category, COUNT(*) as borrow_count, bc.name
                    FROM circulations c
                    LEFT JOIN book_categories bc ON c.bib_id = bc.bib_id
                    WHERE c.status = 'borrowed' AND c.borrow_date >= %s
                    GROUP BY c.bib_id, bc.category, bc.name
                    ORDER BY borrow_count DESC
                    LIMIT 15
                """, (three_years_ago,))
            rows = cur.fetchall()
            return [
                {
                    "rank": i + 1,
                    "bib_id": r[0],
                    "category": r[1] if r[1] else '未知',
                    "borrow_count": r[2],
                    "name": r[3] if r[3] else f'《{r[0]}》'
                }
                for i, r in enumerate(rows)
            ]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取热门借阅图书失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取热门借阅图书失败: {e}")


@router.get("/recent")
async def get_recent_borrows():
    cache_key = "borrows:recent"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            three_years_ago = int((datetime.now().replace(year=datetime.now().year - 3)).strftime('%Y%m%d'))
            cur.execute("""
                SELECT c.borrow_date, c.borrower_id, c.bib_id, c.status,
                       b.degree, bc.category, bc.name
                FROM circulations c
                LEFT JOIN borrowers b ON c.borrower_id = b.id
                LEFT JOIN book_categories bc ON c.bib_id = bc.bib_id
                WHERE c.borrow_date >= %s
                ORDER BY c.borrow_date DESC, c.borrower_id DESC
                LIMIT 20
            """, (three_years_ago,))
            rows = cur.fetchall()
            return [
                {
                    "date": str(r[0]),
                    "time": '',
                    "borrower_id": r[1],
                    "bib_id": r[2],
                    "action": r[3],
                    "degree": education_levels.get(r[4], r[4]) if r[4] else '未知',
                    "category": r[5] if r[5] else '未知',
                    "title": r[6] if r[6] else '未知'
                }
                for r in rows
            ]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取最近借阅记录失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取最近借阅记录失败: {e}")


@router.get("/monthly-trend")
async def get_monthly_trend():
    cache_key = "borrows:monthly-trend"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT month, cko_count
                FROM monthly_history_cache
                ORDER BY month DESC
                LIMIT 24
            """)
            rows = cur.fetchall()
            return [{"month": str(r[0]), "count": r[1]} for r in reversed(rows)]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 600)
        return result
    except Exception as e:
        logger.error("获取月度趋势失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取月度趋势失败: {e}")


@router.get("/monthly-returns")
async def get_monthly_returns():
    cache_key = "borrows:monthly-returns"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT month, cki_count
                FROM monthly_history_cache
                ORDER BY month DESC
                LIMIT 24
            """)
            rows = cur.fetchall()
            return [{"month": str(r[0]), "count": r[1]} for r in reversed(rows)]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 600)
        return result
    except Exception as e:
        logger.error("获取月度归还失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取月度归还失败: {e}")
