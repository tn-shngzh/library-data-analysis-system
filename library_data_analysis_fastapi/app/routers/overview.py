import logging
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Optional
from app.database import run_sync_db
from app.cache import cache

router = APIRouter(prefix="/api/overview", tags=["数据总览"])
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_overview_stats():
    cache_key = "overview:stats"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(borrow_date) FROM circulations")
            max_date = cur.fetchone()[0]
            if max_date is None:
                max_date = int(datetime.now().strftime('%Y%m%d'))
            today_int = max_date
            yesterday_int = max_date - 1

            latest_data_year = today_int // 10000
            year_start = f"{latest_data_year}0101"

            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'borrowed') as cko_count,
                    COUNT(*) FILTER (WHERE status = 'returned') as cki_count,
                    COUNT(DISTINCT borrower_id) as active_readers,
                    COUNT(DISTINCT bib_id) as borrowed_books
                FROM circulations
                WHERE borrow_date >= %s
            """, (int(f"{latest_data_year}0101"),))
            row = cur.fetchone()
            total_circ = row[0] or 0
            cko_count = row[1] or 0
            cki_count = row[2] or 0
            active_readers = row[3] or 0
            total_books = row[4] or 0

            cur.execute("SELECT COUNT(*) FROM borrowers")
            total_readers = cur.fetchone()[0] or 0

            cur.execute("SELECT COUNT(DISTINCT category) FROM book_categories")
            total_categories = cur.fetchone()[0] or 0

            # 去年数据（同比用，基于 monthly_history_cache）
            last_year = latest_data_year - 1
            cur.execute("""
                SELECT COALESCE(SUM(cko_count), 0) + COALESCE(SUM(cki_count), 0)
                FROM monthly_history_cache
                WHERE month BETWEEN %s AND %s
            """, (f"{last_year}01", f"{last_year}12"))
            last_year_total = cur.fetchone()[0] or 0

            cur.execute("""
                SELECT COALESCE(SUM(cko_count), 0) + COALESCE(SUM(cki_count), 0)
                FROM monthly_history_cache
                WHERE month BETWEEN %s AND %s
            """, (f"{latest_data_year}01", f"{latest_data_year}12"))
            this_year_cache_total = cur.fetchone()[0] or 0

            # 最新日数据
            cur.execute("SELECT COUNT(*) FROM circulations WHERE borrow_date = %s", (today_int,))
            today_borrows = cur.fetchone()[0] or 0

            cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE borrow_date = %s", (today_int,))
            today_visitors = cur.fetchone()[0] or 0

            cur.execute("SELECT COUNT(*) FROM circulations WHERE return_date = %s", (today_int,))
            today_returns = cur.fetchone()[0] or 0

            # 前一日数据
            cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE borrow_date = %s", (yesterday_int,))
            yesterday_visitors = cur.fetchone()[0] or 0

            cur.execute("SELECT COUNT(*) FROM circulations WHERE borrow_date = %s", (yesterday_int,))
            yesterday_borrows = cur.fetchone()[0] or 0

            cur.execute("SELECT COUNT(*) FROM circulations WHERE return_date = %s", (yesterday_int,))
            yesterday_returns = cur.fetchone()[0] or 0

            def pct(current, previous):
                if previous == 0: return None
                return round((current - previous) / previous * 100, 1)

            return {
                "total_readers": total_readers,
                "total_borrows": total_circ,
                "active_readers": active_readers,
                "total_books": total_books,
                "cko_count": cko_count,
                "cki_count": cki_count,
                "reh_count": 0,
                "rei_count": 0,
                "today_visits": today_visitors,
                "total_categories": total_categories,
                "today_borrows": today_borrows,
                "today_returns": today_returns,
                "yoy_changes": {
                    "total_borrows": pct(this_year_cache_total, last_year_total),
                    "active_readers": None,
                    "cko_count": None, "cki_count": None,
                    "total_readers": None, "total_books": None,
                    "reh_count": None, "rei_count": None
                },
                "dod_changes": {
                    "visits": pct(today_visitors, yesterday_visitors),
                    "borrows": pct(today_borrows, yesterday_borrows),
                    "returns": pct(today_returns, yesterday_returns)
                }
            }

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
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
                SELECT MIN(month) as min_month, MAX(month) as max_month,
                       SUM(cko_count + cki_count) as total_circ,
                       ROUND(AVG(active_readers)) as avg_readers
                FROM monthly_history_cache
            """)
            row = cur.fetchone()
            min_month = row[0] or 0
            max_month = row[1] or 0
            total_circ = row[2] or 0
            total_active_readers = row[3] or 0

            cur.execute("SELECT COUNT(DISTINCT bib_id) FROM book_categories")
            total_distinct_books = cur.fetchone()[0] or 0

            cur.execute("SELECT COUNT(*) FROM borrowers")
            total_readers = cur.fetchone()[0] or 0

            borrowed_distinct = total_distinct_books

            cur.execute("""
                SELECT COUNT(DISTINCT bc.bib_id)
                FROM book_categories bc
                WHERE NOT EXISTS (
                    SELECT 1 FROM circulations c WHERE c.bib_id = bc.bib_id
                )
            """)
            never_borrowed = cur.fetchone()[0] or 0

            data_start_year = min_month // 100 if min_month else 0
            data_end_year = max_month // 100 if max_month else 0
            data_years = data_end_year - data_start_year + 1 if data_start_year > 0 else 0

            book_turnover_rate = round((total_distinct_books - never_borrowed) / total_distinct_books * 100, 1) if total_distinct_books > 0 else 0
            reader_retention_rate = round(total_active_readers / total_readers * 100, 1) if total_readers > 0 else 0

            if min_month and max_month and min_month > 0:
                months_span = (data_end_year - data_start_year) * 12 + 1
                avg_monthly_circ = round(total_circ / max(months_span, 1), 1)
                days_span = months_span * 30
                avg_daily_circ = round(total_circ / max(days_span, 1), 1)
            else:
                avg_daily_circ = 0
                avg_monthly_circ = 0

            cur.execute("""
                SELECT month, cko_count + cki_count as cnt
                FROM monthly_history_cache
                ORDER BY cnt DESC
                LIMIT 1
            """)
            peak_row = cur.fetchone()
            peak_ym = peak_row[0] if peak_row else 0
            peak_ym_count = peak_row[1] if peak_row else 0

            cur.execute("""
                SELECT mod(month, 100) as m, SUM(cko_count + cki_count) as total
                FROM monthly_history_cache
                GROUP BY mod(month, 100)
                ORDER BY total DESC
                LIMIT 1
            """)
            pm_row = cur.fetchone()
            peak_month = pm_row[0] if pm_row else 0
            peak_month_count = pm_row[1] if pm_row else 0

            cur.execute("""
                SELECT (month / 100) as year,
                       SUM(cko_count) as cko_count,
                       SUM(cki_count) as cki_count,
                       ROUND(AVG(active_readers)) as active_readers,
                       SUM(cko_count + cki_count) as total
                FROM monthly_history_cache
                GROUP BY (month / 100)
                ORDER BY year
            """)
            yearly_trend = []
            for yr in cur.fetchall():
                yearly_trend.append({
                    "year": yr[0],
                    "cko_count": yr[1],
                    "cki_count": yr[2],
                    "active_readers": yr[3],
                    "total": yr[4]
                })

            cur.execute("""
                SELECT ROUND(AVG(rei_count::numeric / NULLIF(cko_count + rei_count, 0)) * 100, 1)
                FROM monthly_history_cache
            """)
            renew_rate = cur.fetchone()[0] or 0

            return {
                "data_years": data_years,
                "data_start_year": data_start_year,
                "data_end_year": data_end_year,
                "total_circulations": total_circ,
                "total_active_readers": total_active_readers,
                "yearly_trend": yearly_trend,
                "avg_monthly_circulations": avg_monthly_circ,
                "avg_daily_circulations": avg_daily_circ,
                "peak_month": peak_month,
                "peak_month_count": peak_month_count,
                "peak_year_month": str(peak_ym) if peak_ym > 0 else "-",
                "peak_ym_count": peak_ym_count,
                "book_turnover_rate": book_turnover_rate,
                "reader_retention_rate": reader_retention_rate,
                "renew_rate": renew_rate,
                "never_borrowed_books": never_borrowed,
                "borrowed_distinct_books": borrowed_distinct,
                "total_distinct_books": total_distinct_books
            }

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取历史统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取历史统计失败: {e}")


@router.get("/historical-detail")
async def get_historical_detail():
    cache_key = "overview:historical-detail"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT month, cko_count, cki_count, active_readers,
                       cko_count + cki_count as total
                FROM monthly_history_cache
                ORDER BY month
            """)
            rows = cur.fetchall()
            return [
                {
                    "month": r[0],
                    "cko_count": r[1],
                    "cki_count": r[2],
                    "active_readers": r[3],
                    "total": r[4]
                }
                for r in rows
            ]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取历史明细失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取历史明细失败: {e}")


@router.get("/recent-books")
async def get_recent_books():
    cache_key = "overview:recent-books"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.borrow_date, c.borrower_id, b.degree, c.bib_id, bc.name, bc.category
                FROM circulations c
                JOIN borrowers b ON c.borrower_id = b.id
                LEFT JOIN book_categories bc ON c.bib_id = bc.bib_id
                ORDER BY c.borrow_date DESC, c.borrow_time DESC
                LIMIT 5
            """)
            rows = cur.fetchall()
            return [
                {
                    "date": str(r[0]),
                    "action": "borrowed",
                    "degree": r[2] or '',
                    "bib_id": r[3],
                    "title": r[4] or '未知',
                    "category": r[5] or '未知'
                }
                for r in rows
            ]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取最近借阅失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取最近借阅失败: {e}")


@router.get("/top-books")
async def get_top_books(limit: int = 10):
    cache_key = f"overview:top-books:{limit}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.bib_id, bc.name, bc.category, COUNT(*) as borrow_count
                FROM circulations c
                LEFT JOIN book_categories bc ON c.bib_id = bc.bib_id
                WHERE c.status = 'borrowed'
                GROUP BY c.bib_id, bc.name, bc.category
                ORDER BY borrow_count DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            return [
                {
                    "bib_id": r[0], "name": r[1] or '未知', "category": r[2] or '未知',
                    "borrow_count": r[3], "rank": i + 1
                }
                for i, r in enumerate(rows)
            ]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取热门图书失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取热门图书失败: {e}")


@router.get("/book-categories")
async def get_book_categories():
    cache_key = "overview:book-categories"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT category, COUNT(*) as cnt
                FROM book_categories
                GROUP BY category
                ORDER BY cnt DESC
            """)
            rows = cur.fetchall()
            total = sum(r[1] for r in rows) if rows else 1
            return [
                {
                    "category": r[0] or '未知',
                    "book_count": 0,
                    "borrow_count": r[1],
                    "percent": round(r[1] / total * 100, 1) if total else 0
                }
                for r in rows
            ]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取图书分类失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取图书分类失败: {e}")


@router.get("/monthly-borrows")
async def get_monthly_borrows(year: Optional[int] = None):
    cache_key = f"overview:monthly-borrows:{year}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        if year:
            current_year = year
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT MAX(borrow_date) FROM circulations")
                max_d = cur.fetchone()[0]
                current_year = (max_d // 10000) if max_d else datetime.now().year
        with conn.cursor() as cur:
            start = f"{current_year}0101"
            end = f"{current_year}1231"
            cur.execute("""
                SELECT (borrow_date / 100) as month, COUNT(*) as count
                FROM circulations
                WHERE borrow_date BETWEEN %s AND %s
                GROUP BY month
                ORDER BY month
            """, (start, end))
            rows = cur.fetchall()
            return [{"month": str(r[0]), "count": r[1]} for r in rows]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取月度借阅失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取月度借阅失败: {e}")


@router.get("/trend-7d")
async def get_trend_7d():
    cache_key = "overview:trend-7d"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(borrow_date) FROM circulations")
            max_date = cur.fetchone()[0]
            if max_date is None:
                return []
            max_str = str(max_date)
            max_dt = datetime(int(max_str[:4]), int(max_str[4:6]), int(max_str[6:8]))
            seven_days_ago = int((max_dt - timedelta(days=7)).strftime('%Y%m%d'))
            today_int = max_date

            cur.execute("""
                SELECT borrow_date, COUNT(*) as borrows, COUNT(DISTINCT borrower_id) as borrowers
                FROM circulations
                WHERE borrow_date BETWEEN %s AND %s
                GROUP BY borrow_date
                ORDER BY borrow_date
            """, (seven_days_ago, today_int))
            borrow_rows = cur.fetchall()
            borrow_map = {str(r[0]): r[1] for r in borrow_rows}
            borrowers_map = {str(r[0]): r[2] for r in borrow_rows}

            cur.execute("""
                SELECT return_date, COUNT(*) as returns
                FROM circulations
                WHERE return_date IS NOT NULL AND return_date BETWEEN %s AND %s
                GROUP BY return_date
                ORDER BY return_date
            """, (seven_days_ago, today_int))
            return_rows = cur.fetchall()
            return_map = {str(r[0]): r[1] for r in return_rows}

            all_dates = sorted(set(list(borrow_map.keys()) + list(return_map.keys())))
            if not all_dates:
                cur.execute("""
                    SELECT month, cko_count, cki_count
                    FROM monthly_history_cache
                    ORDER BY month DESC
                    LIMIT 6
                """)
                month_rows = cur.fetchall()
                if not month_rows:
                    return []
                return [{"date": str(r[0]), "borrows": r[1], "returns": r[2], "total": r[1] + r[2], "borrowers": 0} for r in reversed(month_rows)]

            return [{"date": d, "borrows": borrow_map.get(d, 0), "returns": return_map.get(d, 0), "total": borrow_map.get(d, 0) + return_map.get(d, 0), "borrowers": borrowers_map.get(d, 0)} for d in all_dates]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 600)
        return result
    except Exception as e:
        logger.error("获取7日趋势失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取7日趋势失败: {e}")


@router.get("/collection-health")
async def get_collection_health():
    cache_key = "overview:collection-health"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(DISTINCT bib_id) FROM book_categories")
            total_books = cur.fetchone()[0] or 0

            cur.execute("""
                SELECT COUNT(DISTINCT bib_id) FROM circulations
                WHERE status = 'borrowed'
            """)
            borrowed_books = cur.fetchone()[0] or 0

            cur.execute("""
                SELECT COUNT(DISTINCT bc.bib_id)
                FROM book_categories bc
                WHERE NOT EXISTS (
                    SELECT 1 FROM circulations c WHERE c.bib_id = bc.bib_id
                )
            """)
            zero_borrow = cur.fetchone()[0] or 0

            utilization = round(borrowed_books / total_books * 100, 1) if total_books > 0 else 0

            return {
                "total_books": total_books,
                "borrowed_books": borrowed_books,
                "zero_borrow": zero_borrow,
                "utilization": utilization
            }

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取馆藏健康度失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取馆藏健康度失败: {e}")


@router.get("/reader-activity-heatmap")
async def get_reader_activity_heatmap():
    cache_key = "overview:reader-activity-heatmap"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(borrow_date) FROM circulations")
            max_date = cur.fetchone()[0]
            if max_date is None:
                return {"days": [], "hours": [], "data": [], "max": 0}

            max_str = str(max_date)
            max_dt = datetime(int(max_str[:4]), int(max_str[4:6]), int(max_str[6:8]))
            seven_days_ago = int((max_dt - timedelta(days=6)).strftime('%Y%m%d'))

            cur.execute("""
                SELECT
                    EXTRACT(DOW FROM TO_DATE(borrow_date::TEXT, 'YYYYMMDD')) as dow,
                    FLOOR(borrow_time::INT / 10000)::INT - 6 as hour_idx,
                    COUNT(DISTINCT borrower_id) as cnt
                FROM circulations
                WHERE borrow_time IS NOT NULL
                    AND borrow_time::INT BETWEEN 0 AND 235959
                    AND FLOOR(borrow_time::INT / 10000)::INT BETWEEN 6 AND 22
                    AND borrow_date >= %s
                GROUP BY dow, hour_idx
                ORDER BY dow, hour_idx
            """, (seven_days_ago,))
            rows = cur.fetchall()

            day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            hour_labels = [str(h) for h in range(6, 23)]

            cell_map = {}
            max_val = 0
            for dow, hour_idx, cnt in rows:
                adjusted_dow = (int(dow) - 1) % 7
                h = int(hour_idx)
                if 0 <= h <= 16:
                    cell_map[(adjusted_dow, h)] = cnt
                    if cnt > max_val:
                        max_val = cnt

            heatmap_data = []
            for i in range(7):
                for j in range(17):
                    val = cell_map.get((i, j), 0)
                    heatmap_data.append([j, i, val])

            return {
                "days": day_names,
                "hours": hour_labels,
                "data": heatmap_data,
                "max": max_val
            }

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取读者活跃度热力图失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取读者活跃度热力图失败: {e}")
