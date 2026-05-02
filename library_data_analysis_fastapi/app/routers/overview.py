import logging
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Optional
from app.database import run_sync_db
from app.cache import cache
from app.config import education_levels

router = APIRouter(prefix="/api/overview", tags=["数据总览"])
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_overview_stats(year: Optional[int] = None):
    cache_key = f"overview:stats:{year}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        nonlocal year
        with conn.cursor() as cur:
            today = datetime.now().date()
            today_int = int(today.strftime('%Y%m%d'))
            yesterday_int = int((today - timedelta(days=1)).strftime('%Y%m%d'))
            three_months_ago = int((today.replace(day=1) - timedelta(days=90)).strftime('%Y%m%d'))

            if year is None:
                cur.execute("SELECT MAX(action_date) FROM circulations")
                max_date_row = cur.fetchone()
                if max_date_row and max_date_row[0]:
                    data_year = max_date_row[0] // 10000
                else:
                    data_year = today.year
                year = data_year

            if year != today.year:
                year_start = int(f"{year}0101")
                year_end = int(f"{year}1231")
                last_year_start = int(f"{year-1}0101")
                last_year_end = int(f"{year-1}1231")
            else:
                year_start = int(f"{today.year}0101")
                year_end = int(today.strftime('%Y%m%d'))
                last_year_start = int(f"{today.year-1}0101")
                last_year_end = int(f"{today.year-1}{today.strftime('%m%d')}")

            def yoy_pct(current, previous):
                if previous == 0:
                    return None
                return round((current - previous) / previous * 100, 1)

            def dod_pct(current, previous):
                if previous == 0:
                    return None
                return round((current - previous) / previous * 100, 1)

            cur.execute("""
                WITH year_stats AS (
                    SELECT
                        COUNT(*) as total_borrows,
                        COUNT(CASE WHEN action = 'CKO' THEN 1 END) as cko_count,
                        COUNT(CASE WHEN action = 'CKI' THEN 1 END) as cki_count,
                        COUNT(CASE WHEN action = 'REH' THEN 1 END) as reh_count,
                        COUNT(CASE WHEN action = 'REI' THEN 1 END) as rei_count,
                        COUNT(DISTINCT borrower_id) as active_readers
                    FROM circulations
                    WHERE action_date BETWEEN %s AND %s
                ),
                recent_active AS (
                    SELECT COUNT(DISTINCT borrower_id) as active_readers_3m
                    FROM circulations
                    WHERE action_date BETWEEN %s AND %s
                ),
                today_stats AS (
                    SELECT
                        COUNT(DISTINCT borrower_id) as today_visits,
                        COUNT(CASE WHEN action = 'CKO' THEN 1 END) as today_borrows,
                        COUNT(CASE WHEN action = 'CKI' THEN 1 END) as today_returns
                    FROM circulations
                    WHERE action_date = %s
                ),
                yesterday_stats AS (
                    SELECT
                        COUNT(DISTINCT borrower_id) as yesterday_visits,
                        COUNT(CASE WHEN action = 'CKO' THEN 1 END) as yesterday_borrows,
                        COUNT(CASE WHEN action = 'CKI' THEN 1 END) as yesterday_returns
                    FROM circulations
                    WHERE action_date = %s
                ),
                last_year_stats AS (
                    SELECT
                        COUNT(DISTINCT borrower_id) as ly_total_readers,
                        COUNT(*) as ly_total_borrows,
                        COUNT(CASE WHEN action = 'CKO' THEN 1 END) as ly_cko_count,
                        COUNT(CASE WHEN action = 'CKI' THEN 1 END) as ly_cki_count,
                        COUNT(CASE WHEN action = 'REH' THEN 1 END) as ly_reh_count,
                        COUNT(CASE WHEN action = 'REI' THEN 1 END) as ly_rei_count
                    FROM circulations
                    WHERE action_date BETWEEN %s AND %s
                ),
                ref_stats AS (
                    SELECT
                        (SELECT COUNT(*) FROM borrowers) as total_readers,
                        (SELECT COUNT(DISTINCT bib_id) FROM book_categories) as total_books,
                        (SELECT COUNT(DISTINCT category) FROM book_categories) as total_categories
                )
                SELECT
                    COALESCE(NULLIF(ys.active_readers, 0), ra.active_readers_3m),
                    ys.total_borrows, ys.cko_count, ys.cki_count, ys.reh_count, ys.rei_count,
                    ts.today_visits, ts.today_borrows, ts.today_returns,
                    yss.yesterday_visits, yss.yesterday_borrows, yss.yesterday_returns,
                    lys.ly_total_readers, lys.ly_total_borrows, lys.ly_cko_count, lys.ly_cki_count,
                    lys.ly_reh_count, lys.ly_rei_count,
                    rs.total_readers, rs.total_books, rs.total_categories
                FROM year_stats ys, recent_active ra, today_stats ts, yesterday_stats yss, last_year_stats lys, ref_stats rs
            """, (
                year_start, year_end,
                three_months_ago, year_end,
                today_int,
                yesterday_int,
                last_year_start, last_year_end,
            ))
            row = cur.fetchone()

            active_readers = row[0] or 0
            total_borrows = row[1] or 0
            cko_count = row[2] or 0
            cki_count = row[3] or 0
            reh_count = row[4] or 0
            rei_count = row[5] or 0
            today_visits = row[6] or 0
            today_borrows = row[7] or 0
            today_returns = row[8] or 0
            yesterday_visits = row[9] or 0
            yesterday_borrows = row[10] or 0
            yesterday_returns = row[11] or 0
            ly_total_readers = row[12] or 0
            ly_total_borrows = row[13] or 0
            ly_cko_count = row[14] or 0
            ly_cki_count = row[15] or 0
            ly_reh_count = row[16] or 0
            ly_rei_count = row[17] or 0
            total_readers = row[18] or 0
            total_books = row[19] or 0
            total_categories = row[20] or 0

            result = {
                "total_readers": total_readers,
                "total_borrows": total_borrows,
                "active_readers": active_readers,
                "total_books": total_books,
                "cko_count": cko_count,
                "cki_count": cki_count,
                "reh_count": reh_count,
                "rei_count": rei_count,
                "today_visits": today_visits,
                "total_categories": total_categories,
                "today_borrows": today_borrows,
                "today_returns": today_returns,
                "yoy_changes": {
                    "total_borrows": yoy_pct(total_borrows, ly_total_borrows),
                    "active_readers": yoy_pct(active_readers, ly_total_readers),
                    "cko_count": yoy_pct(cko_count, ly_cko_count),
                    "cki_count": yoy_pct(cki_count, ly_cki_count),
                    "total_readers": yoy_pct(total_readers, ly_total_readers),
                    "total_books": None,
                    "reh_count": yoy_pct(reh_count, ly_reh_count),
                    "rei_count": yoy_pct(rei_count, ly_rei_count)
                },
                "dod_changes": {
                    "visits": dod_pct(today_visits, yesterday_visits),
                    "borrows": dod_pct(today_borrows, yesterday_borrows),
                    "returns": dod_pct(today_returns, yesterday_returns)
                }
            }

            cache.cache_set(cache_key, result, 60)
            return result

    try:
        result = await run_sync_db(_query)
        return result
    except Exception as e:
        logger.error("获取数据总览统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取数据总览统计失败: {e}")


@router.get("/historical-stats")
async def get_historical_stats():
    cache_key = "overview:historical-stats"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("""
                WITH base_stats AS (
                    SELECT
                        MIN(action_date) AS min_date,
                        MAX(action_date) AS max_date,
                        COUNT(*) AS total_circ,
                        COUNT(DISTINCT (action_date / 10000 * 10000 + action_date % 10000 / 100)) AS month_count,
                        COUNT(DISTINCT action_date) AS day_count,
                        COUNT(CASE WHEN action = 'REH' THEN 1 END) AS reh_count,
                        COUNT(CASE WHEN action = 'CKO' THEN 1 END) AS cko_count,
                        COUNT(DISTINCT borrower_id) AS total_active_readers
                    FROM circulations
                ),
                yearly_trend AS (
                    SELECT (action_date / 10000) AS year, COUNT(*) AS cnt
                    FROM circulations
                    GROUP BY year
                    ORDER BY year DESC
                    LIMIT 5
                ),
                peak_month AS (
                    SELECT (action_date % 10000 / 100) AS month, COUNT(*) AS cnt
                    FROM circulations
                    GROUP BY month
                    ORDER BY cnt DESC
                    LIMIT 1
                ),
                peak_ym AS (
                    SELECT (action_date / 10000) AS year, (action_date % 10000 / 100) AS month, COUNT(*) AS cnt
                    FROM circulations
                    GROUP BY year, month
                    ORDER BY cnt DESC
                    LIMIT 1
                ),
                returning_readers AS (
                    SELECT COUNT(DISTINCT borrower_id) AS returning_count
                    FROM circulations
                    WHERE action_date BETWEEN (SELECT MIN(action_date) FROM circulations) AND (SELECT MAX(action_date) - 10000 FROM circulations)
                )
                SELECT
                    bs.min_date,
                    bs.max_date,
                    bs.total_circ,
                    bs.month_count,
                    bs.day_count,
                    bs.reh_count,
                    bs.cko_count,
                    bs.total_active_readers,
                    (SELECT array_agg(ARRAY[yr.year, yr.cnt] ORDER BY yr.year DESC) FROM yearly_trend yr) AS yearly_trend,
                    (SELECT pm.month FROM peak_month pm) AS peak_month,
                    (SELECT pm.cnt FROM peak_month pm) AS peak_month_count,
                    (SELECT pym.year FROM peak_ym pym) AS peak_ym_year,
                    (SELECT pym.month FROM peak_ym pym) AS peak_ym_month,
                    (SELECT pym.cnt FROM peak_ym pym) AS peak_ym_count,
                    (SELECT rr.returning_count FROM returning_readers rr) AS returning_count
                FROM base_stats bs
            """)
            row = cur.fetchone()

            min_date = row[0] if row[0] else 0
            max_date = row[1] if row[1] else 0
            data_start_year = min_date // 10000 if min_date else 0
            data_end_year = max_date // 10000 if max_date else 0
            data_years = data_end_year - data_start_year + 1 if data_start_year > 0 else 0
            total_circ = row[2] or 0
            month_count = row[3] or 1
            day_count = row[4] or 1
            reh_count = row[5] or 0
            cko_count_total = row[6] or 1
            total_active_readers = row[7] or 1
            yearly_trend = [{"year": r[0], "count": r[1]} for r in (row[8] or [])]
            peak_month = row[9] if row[9] else 0
            peak_month_count = row[10] if row[10] else 0
            peak_ym_year = row[11]
            peak_ym_month = row[12]
            peak_ym_count = row[13] if row[13] else 0
            returning_readers = row[14] or 0

            avg_monthly = round(total_circ / month_count) if month_count > 0 else 0
            avg_daily = round(total_circ / day_count) if day_count > 0 else 0
            reader_retention_rate = round(returning_readers / total_active_readers * 100, 1) if total_active_readers > 0 else 0
            renew_rate = round(reh_count / (cko_count_total + reh_count) * 100, 1) if (cko_count_total + reh_count) > 0 else 0
            peak_year_month = f"{peak_ym_year}-{peak_ym_month:02d}" if peak_ym_year is not None else "-"

            cur.execute("""
                SELECT
                    COUNT(DISTINCT CASE WHEN c.action = 'CKO' THEN bc.bib_id END) AS borrowed_distinct,
                    COUNT(DISTINCT bc.bib_id) AS total_distinct_books,
                    COUNT(DISTINCT CASE WHEN c.id IS NULL THEN bc.bib_id END) AS never_borrowed
                FROM book_categories bc
                LEFT JOIN circulations c ON c.bib_id = bc.bib_id AND c.action = 'CKO'
            """)
            book_row = cur.fetchone()
            borrowed_distinct = book_row[0] or 0
            total_distinct_books = book_row[1] or 1
            never_borrowed = book_row[2] or 0
            book_turnover_rate = round(borrowed_distinct / total_distinct_books * 100, 1) if total_distinct_books > 0 else 0

            result = {
                "data_years": data_years,
                "data_start_year": data_start_year,
                "data_end_year": data_end_year,
                "yearly_trend": yearly_trend,
                "avg_monthly_circulations": avg_monthly,
                "avg_daily_circulations": avg_daily,
                "peak_month": peak_month,
                "peak_month_count": peak_month_count,
                "peak_year_month": peak_year_month,
                "peak_ym_count": peak_ym_count,
                "book_turnover_rate": book_turnover_rate,
                "reader_retention_rate": reader_retention_rate,
                "renew_rate": renew_rate,
                "never_borrowed_books": never_borrowed,
                "borrowed_distinct_books": borrowed_distinct,
                "total_distinct_books": total_distinct_books
            }

            cache.cache_set(cache_key, result, 120)
            return result

    try:
        result = await run_sync_db(_query)
        return result
    except Exception as e:
        logger.error("获取历史统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取历史统计失败: {e}")


@router.get("/reader-types")
async def get_reader_types():
    cache_key = "overview:reader-types"
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


@router.get("/book-categories")
async def get_book_categories():
    cached = cache.cache_get("overview:book-categories")
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT bc.category, COUNT(*) as total_items
                FROM book_categories bc
                GROUP BY bc.category
                ORDER BY total_items DESC
            """)
            rows = cur.fetchall()
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
        cache.cache_set("overview:book-categories", result, 300)
        return result
    except Exception as e:
        logger.error("获取图书分类统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取图书分类统计失败: {e}")


@router.get("/recent-books")
async def get_recent_books():
    cache_key = "overview:recent-books"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.action_date, c.action, b.degree,
                       c.bib_id, bc.name, bc.category
                FROM circulations c
                JOIN borrowers b ON c.borrower_id = b.id
                LEFT JOIN book_categories bc ON c.bib_id = bc.bib_id
                WHERE c.action = 'CKO'
                ORDER BY c.action_date DESC, c.action_time DESC
                LIMIT 5
            """)
            rows = cur.fetchall()
            return [
                {
                    "date": str(r[0]),
                    "action": r[1],
                    "degree": r[2],
                    "bib_id": r[3],
                    "title": r[4] if r[4] else '未知',
                    "category": r[5] if r[5] else '未知'
                }
                for r in rows
            ]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 60)
        return result
    except Exception as e:
        logger.error("获取最近借阅失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取最近借阅失败: {e}")


@router.get("/weekly-trend")
async def get_weekly_trend(weeks: int = 12):
    cache_key = "overview:weekly-trend"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            today = datetime.now().date()
            start_date = today - timedelta(weeks=weeks)
            start_int = int(start_date.strftime('%Y%m%d'))
            end_int = int(today.strftime('%Y%m%d'))

            cur.execute("""
                SELECT
                    (action_date / 100) * 100 + ((action_date % 100 - 1) / 7 * 7 + 1) as week_start,
                    COUNT(DISTINCT borrower_id) as active_readers,
                    COUNT(*) as borrow_count
                FROM circulations
                WHERE action = 'CKO' AND action_date BETWEEN %s AND %s
                GROUP BY week_start
                ORDER BY week_start
            """, (start_int, end_int))
            rows = cur.fetchall()

            result = []
            for r in rows:
                week_start = r[0]
                try:
                    year = week_start // 10000
                    month_day = week_start % 10000
                    month = month_day // 100
                    day = month_day % 100
                    from datetime import date as dt
                    d = dt(year, month, day)
                    week_num = d.isocalendar()[1]
                    result.append({
                        "week": f"W{week_num:02d}",
                        "value": r[1] or 0,
                        "borrows": r[2] or 0
                    })
                except (ValueError, OverflowError):
                    result.append({
                        "week": f"W{len(result)+1:02d}",
                        "value": r[1] or 0,
                        "borrows": r[2] or 0
                    })
            return result

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 300)
        return result
    except Exception as e:
        logger.error("获取周趋势失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取周趋势失败: {e}")


@router.get("/top-books")
async def get_top_books(limit: int = 10):
    cache_key = f"overview:top-books:{limit}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT bc.bib_id, bc.name, bc.category, COUNT(c.id) as borrow_count
                FROM book_categories bc
                LEFT JOIN circulations c ON c.bib_id = bc.bib_id AND c.action = 'CKO'
                GROUP BY bc.bib_id, bc.name, bc.category
                ORDER BY borrow_count DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            result = []
            for i, r in enumerate(rows):
                result.append({
                    "bib_id": r[0],
                    "name": r[1],
                    "category": r[2],
                    "borrow_count": r[3] or 0,
                    "rank": i + 1
                })
            return result

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 300)
        return result
    except Exception as e:
        logger.error("获取热门图书失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取热门图书失败: {e}")
