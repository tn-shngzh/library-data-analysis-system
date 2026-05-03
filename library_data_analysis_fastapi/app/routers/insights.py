import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timedelta
from typing import Optional
from app.database import run_sync_db
from app.cache import cache
from app.auth import get_current_user

router = APIRouter(prefix="/api/insights", tags=["智能洞察"])
logger = logging.getLogger(__name__)


@router.get("/auto")
async def get_auto_insights(limit: int = Query(5, ge=1, le=20), current_user=Depends(get_current_user)):
    cache_key = f"insights:auto:{limit}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            insights = []
            today = datetime.now().date()
            today_int = int(today.strftime('%Y%m%d'))
            this_month_start = int(today.replace(day=1).strftime('%Y%m%d'))

            last_month_end = today.replace(day=1) - timedelta(days=1)
            last_month_start = int(last_month_end.replace(day=1).strftime('%Y%m%d'))
            last_month_end_int = int(last_month_end.strftime('%Y%m%d'))
            same_day_last_month = int((today - timedelta(days=30)).strftime('%Y%m%d'))

            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM circulations WHERE action_date BETWEEN %s AND %s", (this_month_start, today_int))
                this_month_count = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM circulations WHERE action_date BETWEEN %s AND %s", (last_month_start, same_day_last_month))
                last_month_count = cur.fetchone()[0]

                if last_month_count > 0:
                    change = round((this_month_count - last_month_count) / last_month_count * 100, 1)
                    if abs(change) >= 5:
                        insights.append({
                            "id": "borrow_trend",
                            "type": "trend",
                            "title": "借阅量趋势" if change > 0 else "借阅量下降趋势",
                            "description": f"本月借阅量{this_month_count}次，较上月同期{last_month_count}次{'增长' if change > 0 else '下降'}{abs(change)}%",
                            "severity": "success" if change > 0 else "warning",
                            "metric": "borrow_change",
                            "value": change
                        })

                cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE action_date BETWEEN %s AND %s", (this_month_start, today_int))
                this_month_active = cur.fetchone()[0]

                cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE action_date BETWEEN %s AND %s", (last_month_start, same_day_last_month))
                last_month_active = cur.fetchone()[0]

                if last_month_active > 0:
                    reader_change = round((this_month_active - last_month_active) / last_month_active * 100, 1)
                    if abs(reader_change) >= 5:
                        insights.append({
                            "id": "active_reader_trend",
                            "type": "trend",
                            "title": "活跃读者趋势" if reader_change > 0 else "活跃读者下降",
                            "description": f"本月活跃读者{this_month_active}人，较上月同期{last_month_active}人{'增长' if reader_change > 0 else '减少'}{abs(reader_change)}%",
                            "severity": "success" if reader_change > 0 else "warning",
                            "metric": "reader_change",
                            "value": reader_change
                        })

                cur.execute("""
                    SELECT bc.category, COUNT(*) as cnt
                    FROM circulations c
                    JOIN book_categories bc ON c.bib_id = bc.bib_id
                    WHERE c.action_date BETWEEN %s AND %s
                    GROUP BY bc.category
                    ORDER BY cnt DESC LIMIT 1
                """, (this_month_start, today_int))
                pop_row = cur.fetchone()
                if pop_row:
                    insights.append({
                        "id": "popular_category",
                        "type": "info",
                        "title": "热门分类",
                        "description": f"本月最受欢迎的分类是「{pop_row[0]}」，共借阅{pop_row[1]}次",
                        "severity": "info",
                        "metric": "popular_category_count",
                        "value": pop_row[1]
                    })

                cur.execute("SELECT COUNT(*) FROM circulations WHERE action_date = %s", (today_int,))
                today_count = cur.fetchone()[0]

                days_this_month = today.day
                avg_daily = round(this_month_count / days_this_month) if days_this_month > 0 else 0

                if avg_daily > 0 and today_count < avg_daily * 0.5:
                    insights.append({
                        "id": "low_activity",
                        "type": "anomaly",
                        "title": "今日活跃度异常偏低",
                        "description": f"今日借阅{today_count}次，仅为本月日均{avg_daily}次的{round(today_count/avg_daily*100)}%",
                        "severity": "warning",
                        "metric": "today_vs_avg",
                        "value": today_count
                    })
                elif avg_daily > 0 and today_count > avg_daily * 1.5:
                    insights.append({
                        "id": "high_activity",
                        "type": "anomaly",
                        "title": "今日活跃度异常偏高",
                        "description": f"今日借阅{today_count}次，为本月日均{avg_daily}次的{round(today_count/avg_daily*100)}%",
                        "severity": "success",
                        "metric": "today_vs_avg",
                        "value": today_count
                    })

                cur.execute("""
                    SELECT
                        COUNT(CASE WHEN action = 'CKO' THEN 1 END) as cko,
                        COUNT(CASE WHEN action = 'CKI' THEN 1 END) as cki
                    FROM circulations
                    WHERE action_date BETWEEN %s AND %s
                """, (this_month_start, today_int))
                ret_row = cur.fetchone()
                if ret_row and ret_row[0] > 0:
                    return_rate = round(ret_row[1] / ret_row[0] * 100, 1)
                    if return_rate < 80:
                        insights.append({
                            "id": "low_return_rate",
                            "type": "recommendation",
                            "title": "归还率偏低",
                            "description": f"本月归还率为{return_rate}%，建议发送催还通知",
                            "severity": "warning",
                            "metric": "return_rate",
                            "value": return_rate
                        })

                cur.execute("""
                    SELECT bc.category, COUNT(*) as cnt
                    FROM circulations c
                    JOIN book_categories bc ON c.bib_id = bc.bib_id
                    WHERE c.action_date BETWEEN %s AND %s
                    GROUP BY bc.category
                    ORDER BY cnt ASC LIMIT 1
                """, (this_month_start, today_int))
                low_row = cur.fetchone()
                if low_row and pop_row:
                    insights.append({
                        "id": "low_category",
                        "type": "recommendation",
                        "title": "冷门分类提醒",
                        "description": f"分类「{low_row[0]}」本月仅借阅{low_row[1]}次，建议考虑调整馆藏或推广",
                        "severity": "info",
                        "metric": "low_category_count",
                        "value": low_row[1]
                    })

            return {"insights": insights[:limit]}

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 60)
        return result
    except Exception as e:
        logger.error("获取智能洞察失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取智能洞察失败: {e}")
