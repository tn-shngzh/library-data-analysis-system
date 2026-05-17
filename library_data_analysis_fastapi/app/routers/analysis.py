import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timedelta
from typing import Optional
from app.database import run_sync_db
from app.cache import cache
from app.config import education_levels
from app.auth import get_current_user

router = APIRouter(prefix="/api/analysis", tags=["数据分析"])
logger = logging.getLogger(__name__)


@router.get("/correlation")
async def get_correlation(year: Optional[int] = None, current_user=Depends(get_current_user)):
    cache_key = f"analysis:correlation:{year}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            nonlocal year
            with conn.cursor() as cur:
                today = datetime.now().date()
                if year is None:
                    cur.execute("SELECT MAX(borrow_date) FROM circulations WHERE status = 'borrowed'")
                    row = cur.fetchone()
                    year = (row[0] // 10000) if row and row[0] else today.year

                if year != today.year:
                    start = int(f"{year}0101")
                    end = int(f"{year}1231")
                else:
                    start = int(f"{today.year}0101")
                    end = int(today.strftime('%Y%m%d'))

                cur.execute("""
                    SELECT b.degree,
                           COUNT(*) as total,
                           COUNT(CASE WHEN c.status = 'borrowed' THEN 1 END) as borrowed,
                           COUNT(CASE WHEN c.status = 'returned' THEN 1 END) as returned,
                           COUNT(DISTINCT c.borrower_id) as reader_count
                    FROM circulations c
                    JOIN borrowers b ON c.borrower_id = b.id
                    WHERE c.borrow_date BETWEEN %s AND %s
                    GROUP BY b.degree
                    ORDER BY total DESC
                """, (start, end))
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()

                reader_type_borrow = []
                for row in rows:
                    d = dict(zip(columns, row))
                    d['degree_name'] = education_levels.get(d['degree'], d['degree'])
                    d['avg_per_reader'] = round(d['total'] / d['reader_count'], 1) if d['reader_count'] > 0 else 0
                    reader_type_borrow.append(d)

                cur.execute("""
                    SELECT status, COUNT(*) as count
                    FROM circulations
                    WHERE borrow_date BETWEEN %s AND %s
                    GROUP BY status
                    ORDER BY count DESC
                """, (start, end))
                status_rows = cur.fetchall()
                total_status = sum(r[1] for r in status_rows) or 1
                status_names = {'borrowed': '借出', 'returned': '归还'}
                action_distribution = [
                    {"action": r[0], "name": status_names.get(r[0], r[0]), "count": r[1], "percent": round(r[1] / total_status * 100, 1)}
                    for r in status_rows
                ]

                return {"reader_type_borrow": reader_type_borrow, "action_distribution": action_distribution}

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 120)
        return result
    except Exception as e:
        logger.error("获取关联分析失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取关联分析失败: {e}")


@router.get("/period-comparison")
async def get_period_comparison(
    period1_start: Optional[int] = None,
    period1_end: Optional[int] = None,
    period2_start: Optional[int] = None,
    period2_end: Optional[int] = None,
    current_user=Depends(get_current_user)
):
    today = datetime.now().date()
    if period1_start is None:
        period1_start = int(today.replace(day=1).strftime('%Y%m%d'))
    if period1_end is None:
        period1_end = int(today.strftime('%Y%m%d'))
    if period2_start is None:
        last_month = today.replace(day=1) - timedelta(days=1)
        period2_start = int(last_month.replace(day=1).strftime('%Y%m%d'))
    if period2_end is None:
        last_month = today.replace(day=1) - timedelta(days=1)
        period2_end = int(last_month.strftime('%Y%m%d'))

    cache_key = f"analysis:period:{period1_start}:{period1_end}:{period2_start}:{period2_end}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            with conn.cursor() as cur:
                def get_period_stats(s, e):
                    cur.execute("""
                        SELECT COUNT(*) as total,
                               COUNT(CASE WHEN status = 'borrowed' THEN 1 END) as borrowed,
                               COUNT(CASE WHEN status = 'returned' THEN 1 END) as returned,
                               COUNT(DISTINCT borrower_id) as active_readers
                        FROM circulations
                        WHERE borrow_date BETWEEN %s AND %s
                    """, (s, e))
                    cols = [desc[0] for desc in cur.description]
                    return dict(zip(cols, cur.fetchone()))

                p1 = get_period_stats(period1_start, period1_end)
                p2 = get_period_stats(period2_start, period2_end)

                def calc_change(key):
                    v1 = p1.get(key, 0) or 0
                    v2 = p2.get(key, 0) or 0
                    if v2 == 0:
                        return None
                    return round((v1 - v2) / v2 * 100, 1)

                changes = {k: calc_change(k) for k in ['total', 'borrowed', 'returned', 'active_readers']}
                return {"period1": p1, "period2": p2, "changes": changes}

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 120)
        return result
    except Exception as e:
        logger.error("获取时段对比失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取时段对比失败: {e}")


@router.get("/category-heatmap")
async def get_category_heatmap(year: Optional[int] = None, months: int = 12, current_user=Depends(get_current_user)):
    cache_key = f"analysis:heatmap:{year}:{months}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            nonlocal year
            with conn.cursor() as cur:
                today = datetime.now().date()
                if year is None:
                    cur.execute("SELECT MAX(borrow_date) FROM circulations WHERE status = 'borrowed'")
                    row = cur.fetchone()
                    year = (row[0] // 10000) if row and row[0] else today.year

                start_date = int(f"{year}0101")
                end_date = int(f"{year}1231") if year != today.year else int(today.strftime('%Y%m%d'))

                cur.execute("""
                    SELECT bc.category,
                           MOD(c.borrow_date, 10000) / 100 as month,
                           COUNT(*) as count
                    FROM circulations c
                    JOIN book_categories bc ON c.bib_id = bc.bib_id
                    WHERE c.borrow_date BETWEEN %s AND %s
                    GROUP BY bc.category, month
                    ORDER BY bc.category, month
                """, (start_date, end_date))
                rows = cur.fetchall()

                categories_set = set()
                month_set = set()
                data_map = {}
                for row in rows:
                    cat, month, count = row
                    categories_set.add(cat)
                    month_set.add(int(month))
                    data_map[(cat, int(month))] = count

                categories = sorted(categories_set)
                months_list = sorted(month_set)
                month_names = [f"{m}月" for m in months_list]

                values = []
                for cat in categories:
                    row_vals = []
                    for m in months_list:
                        row_vals.append(data_map.get((cat, m), 0))
                    values.append(row_vals)

                return {"categories": categories, "months": month_names, "values": values}

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取分类热力图失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取分类热力图失败: {e}")


@router.get("/degree-monthly-trend")
async def get_degree_monthly_trend(year: Optional[int] = None, current_user=Depends(get_current_user)):
    cache_key = f"analysis:degree_trend:{year}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            nonlocal year
            with conn.cursor() as cur:
                today = datetime.now().date()
                if year is None:
                    cur.execute("SELECT MAX(borrow_date) FROM circulations WHERE status = 'borrowed'")
                    row = cur.fetchone()
                    year = (row[0] // 10000) if row and row[0] else today.year

                if year != today.year:
                    start = int(f"{year}0101")
                    end = int(f"{year}1231")
                else:
                    start = int(f"{today.year}0101")
                    end = int(today.strftime('%Y%m%d'))

                cur.execute("""
                    SELECT b.degree,
                           MOD(c.borrow_date, 10000) / 100 as month,
                           COUNT(*) as count
                    FROM circulations c
                    JOIN borrowers b ON c.borrower_id = b.id
                    WHERE c.borrow_date BETWEEN %s AND %s
                    GROUP BY b.degree, month
                    ORDER BY b.degree, month
                """, (start, end))
                rows = cur.fetchall()

                degrees_order = list(education_levels.keys())
                month_set = set()
                data_map = {}
                for row in rows:
                    deg, month, count = row
                    month_set.add(int(month))
                    data_map[(deg, int(month))] = count

                months_list = sorted(month_set)
                month_names = [f"{m}月" for m in months_list]

                series = []
                for deg in degrees_order:
                    if deg not in set(r[0] for r in rows):
                        continue
                    deg_data = []
                    for m in months_list:
                        deg_data.append(data_map.get((deg, m), 0))
                    deg_name = education_levels.get(deg, deg)
                    series.append({
                        "name": deg_name,
                        "data": deg_data
                    })

                return {"months": month_names, "series": series}

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取学历月度趋势失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取学历月度趋势失败: {e}")


@router.get("/daily-trend")
async def get_daily_trend(
    start_date: Optional[int] = None,
    end_date: Optional[int] = None,
    current_user=Depends(get_current_user)
):
    today = datetime.now().date()
    if start_date is None:
        start_date = int(today.replace(day=1).strftime('%Y%m%d'))
    if end_date is None:
        end_date = int(today.strftime('%Y%m%d'))

    cache_key = f"analysis:daily:{start_date}:{end_date}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT borrow_date,
                           COUNT(*) as total,
                           COUNT(CASE WHEN status = 'borrowed' THEN 1 END) as borrowed,
                           COUNT(CASE WHEN status = 'returned' THEN 1 END) as returned
                    FROM circulations
                    WHERE borrow_date BETWEEN %s AND %s
                    GROUP BY borrow_date
                    ORDER BY borrow_date
                """, (start_date, end_date))
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()

                dates = []
                total_series = []
                borrowed_series = []
                returned_series = []

                for row in rows:
                    d = dict(zip(columns, row))
                    date_str = str(d['borrow_date'])
                    dates.append(f"{date_str[4:6]}/{date_str[6:8]}")
                    total_series.append(d['total'])
                    borrowed_series.append(d['borrowed'])
                    returned_series.append(d['returned'])

                return {
                    "dates": dates,
                    "total": total_series,
                    "borrowed": borrowed_series,
                    "returned": returned_series
                }

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 600)
        return result
    except Exception as e:
        logger.error("获取每日趋势失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取每日趋势失败: {e}")


@router.get("/category-period-comparison")
async def get_category_period_comparison(
    period1_start: Optional[int] = None,
    period1_end: Optional[int] = None,
    period2_start: Optional[int] = None,
    period2_end: Optional[int] = None,
    current_user=Depends(get_current_user)
):
    today = datetime.now().date()
    if period1_start is None:
        period1_start = int(today.replace(day=1).strftime('%Y%m%d'))
    if period1_end is None:
        period1_end = int(today.strftime('%Y%m%d'))
    if period2_start is None:
        last_month = today.replace(day=1) - timedelta(days=1)
        period2_start = int(last_month.replace(day=1).strftime('%Y%m%d'))
    if period2_end is None:
        last_month = today.replace(day=1) - timedelta(days=1)
        period2_end = int(last_month.strftime('%Y%m%d'))

    cache_key = f"analysis:cat_period:{period1_start}:{period1_end}:{period2_start}:{period2_end}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            with conn.cursor() as cur:
                def get_cat_stats(s, e):
                    cur.execute("""
                        SELECT bc.category, COUNT(*) as count
                        FROM circulations c
                        JOIN book_categories bc ON c.bib_id = bc.bib_id
                        WHERE c.borrow_date BETWEEN %s AND %s
                        GROUP BY bc.category
                        ORDER BY count DESC
                    """, (s, e))
                    return {row[0]: row[1] for row in cur.fetchall()}

                p1 = get_cat_stats(period1_start, period1_end)
                p2 = get_cat_stats(period2_start, period2_end)

                all_cats = set(list(p1.keys()) + list(p2.keys()))
                comparison = []
                for cat in all_cats:
                    v1 = p1.get(cat, 0)
                    v2 = p2.get(cat, 0)
                    if v2 > 0:
                        change = round((v1 - v2) / v2 * 100, 1)
                    elif v1 > 0:
                        change = 100.0
                    else:
                        change = 0.0
                    comparison.append({
                        "category": cat,
                        "period1_count": v1,
                        "period2_count": v2,
                        "change": change
                    })

                comparison.sort(key=lambda x: x['change'], reverse=True)

                return {
                    "period1_start": period1_start,
                    "period1_end": period1_end,
                    "period2_start": period2_start,
                    "period2_end": period2_end,
                    "comparison": comparison
                }

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 600)
        return result
    except Exception as e:
        logger.error("获取分类时段对比失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取分类时段对比失败: {e}")
