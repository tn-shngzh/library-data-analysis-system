import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from app.database import run_sync_db
from app.config import education_levels
from app.cache import cache
from app.auth import get_current_user

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
            year_month = int(today.strftime('%Y%m'))
            month_start = int(f"{year_month}01")
            month_end = int(f"{year_month}31")

            cur.execute("""
                SELECT COUNT(DISTINCT borrower_id), COUNT(*)
                FROM circulations
                WHERE borrow_date BETWEEN %s AND %s
            """, (month_start, month_end))
            month_row = cur.fetchone()

            if month_row and month_row[0]:
                month_active = month_row[0] or 0
                month_borrowers = month_row[1] or 0
            else:
                month_active = 0
                month_borrowers = 0

            try:
                cur.execute("""
                    SELECT AVG(borrow_count) FROM (
                        SELECT borrower_id, COUNT(*) as borrow_count
                        FROM circulations
                        WHERE status = 'borrowed'
                        GROUP BY borrower_id
                    ) t
                """)
                avg_borrows = cur.fetchone()[0]
            except Exception:
                conn.rollback()
                logger.warning("获取平均借阅数失败，使用默认值0")
                avg_borrows = 0

            return {
                "total_readers": total_readers,
                "month_active": month_active,
                "month_new": month_borrowers,
                "avg_borrows": round(avg_borrows, 1) if avg_borrows else 0
            }

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取读者统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取读者统计失败: {e}")


@router.get("/types")
async def get_reader_types(start_date: str = None, end_date: str = None):
    cache_key = f"readers:types:{start_date}:{end_date}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            if start_date and end_date:
                start_int = int(start_date.replace('-', ''))
                end_int = int(end_date.replace('-', ''))
                cur.execute("""
                    SELECT b.degree, COUNT(DISTINCT c.borrower_id) as count
                    FROM circulations c
                    JOIN borrowers b ON c.borrower_id = b.id
                    WHERE c.borrow_date BETWEEN %s AND %s
                    GROUP BY b.degree
                    ORDER BY count DESC
                """, (start_int, end_int))
                rows = cur.fetchall()
                total = sum(r[1] for r in rows) if rows else 1
                result = []
                for i, (name, cnt) in enumerate(rows):
                    pct = round(cnt / total * 100, 1) if total else 0
                    if i == len(rows) - 1:
                        pct = round(100.0 - sum(round(rr[1] / total * 100, 1) for rr in rows[:-1]), 1) if len(rows) > 1 else 100.0
                    result.append({"name": name, "value": cnt, "percent": pct})
                return result
            else:
                cur.execute("""
                    SELECT degree, COUNT(*) as count
                    FROM borrowers
                    GROUP BY degree
                    ORDER BY count DESC
                """)
                rows = cur.fetchall()
                total = sum(r[1] for r in rows) if rows else 1
                result = []
                for i, (name, cnt) in enumerate(rows):
                    pct = round(cnt / total * 100, 1) if total else 0
                    if i == len(rows) - 1:
                        pct = round(100.0 - sum(round(rr[1] / total * 100, 1) for rr in rows[:-1]), 1) if len(rows) > 1 else 100.0
                    result.append({"name": name, "value": cnt, "percent": pct})
                return result

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取读者类型统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取读者类型统计失败: {e}")


@router.get("/monthly-trend")
async def get_monthly_trend(year: Optional[int] = None, start_date: str = None, end_date: str = None):
    cache_key = f"readers:monthly-trend:{year}:{start_date}:{end_date}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT month, active_readers, cko_count
                FROM monthly_history_cache
                ORDER BY month DESC
                LIMIT 24
            """)
            rows = cur.fetchall()
            return [{"label": str(r[0]), "value": r[1], "count": r[2]} for r in reversed(rows)]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 600)
        return result
    except Exception as e:
        logger.error("获取读者月度趋势失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取读者月度趋势失败: {e}")


@router.get("/top")
async def get_top_readers(start_date: str = None, end_date: str = None):
    cache_key = f"readers:top:{start_date}:{end_date}"
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
                    WHERE c.status = 'borrowed' AND c.borrow_date BETWEEN %s AND %s
                    GROUP BY c.borrower_id, b.degree
                    ORDER BY borrow_count DESC
                    LIMIT 15
                """, (start_int, end_int))
            else:
                cur.execute("""
                    SELECT c.borrower_id, b.degree, COUNT(*) as borrow_count
                    FROM circulations c
                    JOIN borrowers b ON c.borrower_id = b.id
                    WHERE c.status = 'borrowed'
                    GROUP BY c.borrower_id, b.degree
                    ORDER BY borrow_count DESC
                    LIMIT 15
                """)
            rows = cur.fetchall()
            return [
                {
                    "rank": i + 1,
                    "id": r[0],
                    "borrowed": r[2],
                    "type": education_levels.get(r[1], r[1])
                }
                for i, r in enumerate(rows)
            ]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取热门读者失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取热门读者失败: {e}")


@router.get("/degree-stats")
async def get_degree_stats(current_user=Depends(get_current_user)):
    cache_key = "readers:degree-stats"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT b.degree, COUNT(*) as count
                    FROM borrowers b
                    GROUP BY b.degree
                    ORDER BY count DESC
                """)
                rows = cur.fetchall()
                result = []
                for degree, count in rows:
                    result.append({
                        "degree": degree,
                        "degree_name": education_levels.get(degree, degree),
                        "count": count
                    })
                return result

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取读者学历统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取读者学历统计失败: {e}")


@router.get("/degree-hour-heatmap")
async def get_degree_hour_heatmap(current_user=Depends(get_current_user)):
    cache_key = "readers:degree-hour-heatmap"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            with conn.cursor() as cur:
                # 尝试使用预聚合的缓存表
                try:
                    cur.execute("""
                        SELECT degree, hour, cnt
                        FROM degree_hour_cache
                        ORDER BY degree, hour
                    """)
                    rows = cur.fetchall()
                    if rows:
                        degree_hours = {}
                        all_hours = set()
                        for degree, hour, cnt in rows:
                            if degree and degree.lower() == 'unknown':
                                continue
                            if degree not in degree_hours:
                                degree_hours[degree] = {}
                            degree_hours[degree][hour] = cnt
                            all_hours.add(hour)

                        degrees = sorted(degree_hours.keys())
                        hours = sorted(h for h in all_hours if 6 <= h <= 22)

                        if not degrees or not hours:
                            return {
                                "degrees": [],
                                "hours": [f"{h:02d}:00" for h in hours],
                                "data": [],
                                "max": 0
                            }

                        heatmap_data = []
                        max_val = 0
                        for i, degree in enumerate(degrees):
                            for j, hour in enumerate(hours):
                                count = degree_hours[degree].get(hour, 0)
                                heatmap_data.append([j, i, count])
                                if count > max_val:
                                    max_val = count

                        return {
                            "degrees": [education_levels.get(d, d) for d in degrees],
                            "hours": [f"{h:02d}:00" for h in hours],
                            "data": heatmap_data,
                            "max": max_val
                        }
                except Exception:
                    conn.rollback()
                    logger.warning("degree_hour_cache查询失败，使用回退查询")

                # 回退：使用 borrowers 表的小表 JOIN，限制只取最近1年数据
                one_year_ago = int((datetime.now().replace(year=datetime.now().year - 1)).strftime('%Y%m%d'))
                cur.execute("""
                    SELECT b.degree, LEFT(c.borrow_time::TEXT, 2)::INT as hour, COUNT(*) as cnt
                    FROM circulations c
                    JOIN borrowers b ON c.borrower_id = b.id
                    WHERE c.status = 'borrowed' AND c.borrow_time IS NOT NULL
                      AND LEFT(c.borrow_time::TEXT, 2)::INT BETWEEN 0 AND 23
                      AND c.borrow_date >= %s
                    GROUP BY b.degree, hour
                """, (one_year_ago,))
                rows = cur.fetchall()

                degree_hours = {}
                all_hours = set()
                for degree, hour, cnt in rows:
                    if degree and degree.lower() == 'unknown':
                        continue
                    if degree not in degree_hours:
                        degree_hours[degree] = {}
                    degree_hours[degree][hour] = cnt
                    all_hours.add(hour)

                degrees = sorted(degree_hours.keys())
                hours = sorted(h for h in all_hours if 6 <= h <= 22)

                if not degrees or not hours:
                    return {
                        "degrees": [],
                        "hours": [f"{h:02d}:00" for h in hours],
                        "data": [],
                        "max": 0
                    }

                heatmap_data = []
                max_val = 0
                for i, degree in enumerate(degrees):
                    for j, hour in enumerate(hours):
                        count = degree_hours[degree].get(hour, 0)
                        heatmap_data.append([j, i, count])
                        if count > max_val:
                            max_val = count

                return {
                    "degrees": [education_levels.get(d, d) for d in degrees],
                    "hours": [f"{h:02d}:00" for h in hours],
                    "data": heatmap_data,
                    "max": max_val
                }

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取学历时段热力图失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取学历时段热力图失败: {e}")


@router.get("/frequency-distribution")
async def get_frequency_distribution(current_user=Depends(get_current_user)):
    cache_key = "readers:frequency-distribution"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            with conn.cursor() as cur:
                three_years_ago = int((datetime.now().replace(year=datetime.now().year - 3)).strftime('%Y%m%d'))
                cur.execute("""
                    SELECT COUNT(DISTINCT borrower_id) as total FROM circulations
                    WHERE status = 'borrowed' AND borrow_date >= %s
                """, (three_years_ago,))
                total_readers = cur.fetchone()[0] or 0

                if total_readers == 0:
                    return {"groups": [], "details": {"total_readers": 0, "avg_borrows": 0}}

                cur.execute("""
                    SELECT COUNT(*) / COUNT(DISTINCT borrower_id) FROM circulations
                    WHERE status = 'borrowed' AND borrow_date >= %s
                """, (three_years_ago,))
                avg_borrows = round(cur.fetchone()[0] or 0, 1)

                cur.execute("""
                    SELECT borrow_count, COUNT(*) as reader_cnt
                    FROM (
                        SELECT borrower_id, COUNT(*) as borrow_count
                        FROM circulations WHERE status = 'borrowed' AND borrow_date >= %s
                        GROUP BY borrower_id
                    ) t
                    GROUP BY borrow_count
                    ORDER BY borrow_count DESC
                """, (three_years_ago,))
                rows = cur.fetchall()

                if not rows:
                    return {"groups": [], "details": {"total_readers": total_readers, "avg_borrows": avg_borrows}}

                cumsum = 0
                high_threshold = None
                low_threshold = None
                for borrow_count, reader_cnt in rows:
                    cumsum += reader_cnt
                    if high_threshold is None and cumsum >= total_readers * 0.2:
                        high_threshold = borrow_count
                    if low_threshold is None and cumsum >= total_readers * 0.7:
                        low_threshold = borrow_count

                if high_threshold is None:
                    high_threshold = rows[0][0] if rows else 1
                if low_threshold is None:
                    low_threshold = rows[-1][0] if rows else 1

                high_count = sum(cnt for bc, cnt in rows if bc >= high_threshold)
                low_count = sum(cnt for bc, cnt in rows if bc <= low_threshold)
                mid_count = total_readers - high_count - low_count

                return {
                    "groups": [
                        {"name": "高频读者", "count": high_count, "percent": round(high_count / total_readers * 100, 1), "threshold": f">={high_threshold}"},
                        {"name": "中频读者", "count": mid_count, "percent": round(mid_count / total_readers * 100, 1), "threshold": f"{low_threshold}~{high_threshold-1}"},
                        {"name": "低频读者", "count": low_count, "percent": round(low_count / total_readers * 100, 1), "threshold": f"<={low_threshold}"}
                    ],
                    "details": {
                        "total_readers": total_readers,
                        "high_threshold": high_threshold,
                        "low_threshold": low_threshold,
                        "avg_borrows": avg_borrows
                    }
                }

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取借阅频次分布失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取借阅频次分布失败: {e}")
