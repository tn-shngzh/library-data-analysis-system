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
                    cur.execute("SELECT MAX(action_date) FROM circulations")
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
                           COUNT(CASE WHEN c.action = 'CKO' THEN 1 END) as cko,
                           COUNT(CASE WHEN c.action = 'CKI' THEN 1 END) as cki,
                           COUNT(CASE WHEN c.action = 'REH' THEN 1 END) as reh,
                           COUNT(CASE WHEN c.action = 'REI' THEN 1 END) as rei,
                           COUNT(DISTINCT c.borrower_id) as reader_count
                    FROM circulations c
                    JOIN borrowers b ON c.borrower_id = b.borrower_id
                    WHERE c.action_date BETWEEN %s AND %s
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
                    SELECT action, COUNT(*) as count
                    FROM circulations
                    WHERE action_date BETWEEN %s AND %s
                    GROUP BY action
                    ORDER BY count DESC
                """, (start, end))
                action_rows = cur.fetchall()
                total_actions = sum(r[1] for r in action_rows) or 1
                action_names = {'CKO': '借出', 'CKI': '归还', 'REH': '馆内续借', 'REI': '线上续借'}
                action_distribution = [
                    {"action": r[0], "name": action_names.get(r[0], r[0]), "count": r[1], "percent": round(r[1] / total_actions * 100, 1)}
                    for r in action_rows
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
                               COUNT(CASE WHEN action = 'CKO' THEN 1 END) as cko,
                               COUNT(CASE WHEN action = 'CKI' THEN 1 END) as cki,
                               COUNT(CASE WHEN action = 'REH' THEN 1 END) as reh,
                               COUNT(CASE WHEN action = 'REI' THEN 1 END) as rei,
                               COUNT(DISTINCT borrower_id) as active_readers
                        FROM circulations
                        WHERE action_date BETWEEN %s AND %s
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

                changes = {k: calc_change(k) for k in ['total', 'cko', 'cki', 'reh', 'rei', 'active_readers']}
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
                    cur.execute("SELECT MAX(action_date) FROM circulations")
                    row = cur.fetchone()
                    year = (row[0] // 10000) if row and row[0] else today.year

                start_date = int(f"{year}0101")
                end_date = int(f"{year}1231") if year != today.year else int(today.strftime('%Y%m%d'))

                cur.execute("""
                    SELECT bc.category,
                           EXTRACT(MONTH FROM TO_DATE(c.action_date::TEXT, 'YYYYMMDD')) as month,
                           COUNT(*) as count
                    FROM circulations c
                    JOIN book_categories bc ON c.bib_id = bc.bib_id
                    WHERE c.action_date BETWEEN %s AND %s
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
        cache.cache_set(cache_key, result, 300)
        return result
    except Exception as e:
        logger.error("获取分类热力图失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取分类热力图失败: {e}")
