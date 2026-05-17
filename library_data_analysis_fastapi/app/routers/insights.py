import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timedelta
from typing import Optional
from app.database import run_sync_db
from app.cache import cache
from app.auth import get_current_user

router = APIRouter(prefix="/api/insights", tags=["智能洞察"])
logger = logging.getLogger(__name__)


def _parse_time_to_hour(time_str):
    """将时间字符串转换为小时（0-23）"""
    if not time_str or len(time_str) < 2:
        return None
    try:
        hour = int(time_str[:2])
        if 0 <= hour <= 23:
            return hour
        # 处理一些异常格式（如'92100'表示9点）
        if len(time_str) >= 5:
            hour = int(time_str[0:1])
            if 0 <= hour <= 9:
                return hour
    except (ValueError, IndexError):
        pass
    return None


@router.get("/auto")
async def get_auto_insights(limit: int = Query(6, ge=1, le=20), current_user=Depends(get_current_user)):
    cache_key = f"insights:auto:{limit}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            insights = []
            with conn.cursor() as cur:
                # 使用数据库中的最新日期作为"今天"
                cur.execute("SELECT MAX(borrow_date) FROM circulations WHERE status = 'borrowed'")
                row = cur.fetchone()
                max_date = row[0] if row and row[0] else 0

                if max_date == 0:
                    return {"insights": []}

                # 将最大日期解析为datetime
                max_year = max_date // 10000
                max_month = (max_date % 10000) // 100
                max_day = max_date % 100
                try:
                    today = datetime(max_year, max_month, max_day).date()
                except ValueError:
                    today = datetime.now().date()

                today_int = max_date
                this_month_start = int(today.replace(day=1).strftime('%Y%m%d'))
                last_month_end = today.replace(day=1) - timedelta(days=1)
                last_month_start = int(last_month_end.replace(day=1).strftime('%Y%m%d'))
                same_day_last_month = int((today - timedelta(days=30)).strftime('%Y%m%d'))
                # ========== 1. 分类洞察 ==========
                # 获取本月各分类借阅量
                cur.execute("""
                    SELECT bc.category, COUNT(*) as cnt
                    FROM circulations c
                    JOIN book_categories bc ON c.bib_id = bc.bib_id
                    WHERE c.borrow_date BETWEEN %s AND %s AND c.status = 'borrowed'
                    GROUP BY bc.category
                    ORDER BY cnt DESC
                """, (this_month_start, today_int))
                this_month_categories = {row[0]: row[1] for row in cur.fetchall()}

                # 获取上月同期各分类借阅量
                cur.execute("""
                    SELECT bc.category, COUNT(*) as cnt
                    FROM circulations c
                    JOIN book_categories bc ON c.bib_id = bc.bib_id
                    WHERE c.borrow_date BETWEEN %s AND %s AND c.status = 'borrowed'
                    GROUP BY bc.category
                """, (last_month_start, same_day_last_month))
                last_month_categories = {row[0]: row[1] for row in cur.fetchall()}

                # 找出增长最快的分类
                category_growth = []
                for cat, this_count in this_month_categories.items():
                    last_count = last_month_categories.get(cat, 0)
                    if last_count > 10:  # 需要有一定基数
                        growth = (this_count - last_count) / last_count * 100
                        category_growth.append((cat, growth, this_count, last_count))

                category_growth.sort(key=lambda x: x[1], reverse=True)

                # 生成分类洞察 - 增长最快
                if category_growth and category_growth[0][1] > 15:
                    cat, growth, this_cnt, last_cnt = category_growth[0]
                    insights.append({
                        "id": f"category_growth_{cat}",
                        "type": "category",
                        "icon": "💡",
                        "title": f"{cat}类借阅增长显著",
                        "main": f"{cat}类借阅量本月达{this_cnt}次",
                        "reason": f"较上月同期增长{round(growth, 1)}%，从{last_cnt}次增至{this_cnt}次",
                        "trend": "up",
                        "severity": "success",
                        "metric": "category_growth",
                        "value": round(growth, 1)
                    })

                # 找出下降最快的分类（预警）
                category_growth_asc = sorted(category_growth, key=lambda x: x[1])
                if category_growth_asc and category_growth_asc[0][1] < -20:
                    cat, growth, this_cnt, last_cnt = category_growth_asc[0]
                    insights.append({
                        "id": f"category_decline_{cat}",
                        "type": "category",
                        "icon": "📉",
                        "title": f"{cat}类借阅量下降",
                        "main": f"{cat}类借阅量降至{this_cnt}次",
                        "reason": f"较上月同期下降{abs(round(growth, 1))}%，从{last_cnt}次降至{this_cnt}次",
                        "trend": "down",
                        "severity": "warning",
                        "metric": "category_decline",
                        "value": round(growth, 1)
                    })

                # ========== 2. 时段洞察 ==========
                # 获取本月各时段借阅分布
                cur.execute("""
                    SELECT c.borrow_time, COUNT(*) as cnt
                    FROM circulations c
                    WHERE c.borrow_date BETWEEN %s AND %s AND c.status = 'borrowed'
                        AND c.borrow_time IS NOT NULL
                    GROUP BY c.borrow_time
                """, (this_month_start, today_int))
                time_rows = cur.fetchall()

                hour_distribution = {}
                for time_str, cnt in time_rows:
                    hour = _parse_time_to_hour(time_str)
                    if hour is not None:
                        hour_distribution[hour] = hour_distribution.get(hour, 0) + cnt

                if hour_distribution:
                    # 找出高峰时段
                    peak_hour = max(hour_distribution, key=hour_distribution.get)
                    peak_count = hour_distribution[peak_hour]
                    total_hours = sum(hour_distribution.values())

                    # 夜间时段 (22:00-01:00) 分析
                    night_hours = [22, 23, 0, 1]
                    night_count = sum(hour_distribution.get(h, 0) for h in night_hours)
                    night_pct = night_count / total_hours * 100 if total_hours > 0 else 0

                    # 如果夜间借阅占比超过5%，生成洞察
                    if night_pct > 5:
                        insights.append({
                            "id": "night_peak",
                            "type": "time",
                            "icon": "🌙",
                            "title": "夜间借阅活跃",
                            "main": f"夜间(22:00~01:00)借阅占{round(night_pct, 1)}%",
                            "reason": f"夜间时段共借阅{night_count}次，显示读者有深夜阅读/借阅习惯",
                            "trend": "up",
                            "severity": "info",
                            "metric": "night_ratio",
                            "value": round(night_pct, 1)
                        })

                    # 高峰时段洞察
                    peak_pct = peak_count / total_hours * 100 if total_hours > 0 else 0
                    if peak_pct > 15:
                        next_hour = (peak_hour + 1) % 24
                        hour_label = f"{peak_hour:02d}:00~{next_hour:02d}:00"
                        insights.append({
                            "id": f"peak_hour_{peak_hour}",
                            "type": "time",
                            "icon": "⏰",
                            "title": f"{hour_label}为借阅高峰",
                            "main": f"该时段借阅量占全天的{round(peak_pct, 1)}%",
                            "reason": f"共{peak_count}次借阅，是全天最活跃的时段",
                            "trend": "up",
                            "severity": "info",
                            "metric": "peak_hour_ratio",
                            "value": round(peak_pct, 1)
                        })

                # ========== 3. 闲置预警 ==========
                # 获取总图书数和半年未借图书数
                six_months_ago = today - timedelta(days=180)
                six_months_ago_int = int(six_months_ago.strftime('%Y%m%d'))

                cur.execute("SELECT COUNT(*) FROM book_categories")
                total_books = cur.fetchone()[0]

                # 半年内有借阅记录的图书
                cur.execute("""
                    SELECT COUNT(DISTINCT bib_id)
                    FROM circulations
                    WHERE borrow_date > %s AND status = 'borrowed'
                """, (six_months_ago_int,))
                recent_borrowed = cur.fetchone()[0]

                idle_books = total_books - recent_borrowed
                idle_pct = idle_books / total_books * 100 if total_books > 0 else 0

                if idle_pct > 5:
                    insights.append({
                        "id": "idle_books_warning",
                        "type": "warning",
                        "icon": "📚",
                        "title": "闲置图书预警",
                        "main": f"{round(idle_pct, 1)}%图书半年未被借阅",
                        "reason": f"共{idle_books}册图书超过6个月无借阅记录，建议进行馆藏优化",
                        "trend": "down",
                        "severity": "warning",
                        "metric": "idle_book_ratio",
                        "value": round(idle_pct, 1)
                    })

                # ========== 4. 热门分类洞察 ==========
                if this_month_categories:
                    top_cat = max(this_month_categories, key=this_month_categories.get)
                    top_count = this_month_categories[top_cat]
                    total_cat = sum(this_month_categories.values())
                    top_pct = top_count / total_cat * 100 if total_cat > 0 else 0

                    if top_pct > 20:
                        insights.append({
                            "id": f"popular_{top_cat}",
                            "type": "category",
                            "icon": "🔥",
                            "title": f"{top_cat}类最受欢迎",
                            "main": f"占本月借阅量的{round(top_pct, 1)}%",
                            "reason": f"共借阅{top_count}次，是最热门的分类",
                            "trend": "up",
                            "severity": "success",
                            "metric": "popular_category_pct",
                            "value": round(top_pct, 1)
                        })

                # ========== 5. 借阅量趋势洞察 ==========
                cur.execute("""
                    SELECT COUNT(*) FROM circulations
                    WHERE borrow_date BETWEEN %s AND %s AND status = 'borrowed'
                """, (this_month_start, today_int))
                this_month_count = cur.fetchone()[0]

                cur.execute("""
                    SELECT COUNT(*) FROM circulations
                    WHERE borrow_date BETWEEN %s AND %s AND status = 'borrowed'
                """, (last_month_start, same_day_last_month))
                last_month_count = cur.fetchone()[0]

                if last_month_count > 100:
                    change = (this_month_count - last_month_count) / last_month_count * 100
                    if abs(change) >= 10:
                        insights.append({
                            "id": "borrow_trend",
                            "type": "trend",
                            "icon": "📊",
                            "title": "借阅量" + ("增长" if change > 0 else "下降"),
                            "main": f"本月借阅{this_month_count}次",
                            "reason": f"较上月同期{last_month_count}次{'增长' if change > 0 else '下降'}{abs(round(change, 1))}%",
                            "trend": "up" if change > 0 else "down",
                            "severity": "success" if change > 0 else "warning",
                            "metric": "borrow_change",
                            "value": round(change, 1)
                        })

                # ========== 6. 周末vs工作日洞察 ==========
                cur.execute("""
                    SELECT 
                        CASE WHEN MOD(borrow_date, 7) IN (0, 6) 
                            THEN 'weekend' ELSE 'weekday' END as day_type,
                        COUNT(*) as cnt
                    FROM circulations
                    WHERE borrow_date BETWEEN %s AND %s AND status = 'borrowed'
                    GROUP BY day_type
                """, (this_month_start, today_int))
                day_type_rows = {row[0]: row[1] for row in cur.fetchall()}

                weekday_count = day_type_rows.get('weekday', 0)
                weekend_count = day_type_rows.get('weekend', 0)
                if weekday_count > 0 and weekend_count > 0:
                    weekend_ratio = weekend_count / (weekend_count + weekday_count) * 100
                    if weekend_ratio > 40:
                        insights.append({
                            "id": "weekend_high",
                            "type": "time",
                            "icon": "🎯",
                            "title": "周末借阅活跃",
                            "main": f"周末借阅占{round(weekend_ratio, 1)}%",
                            "reason": f"周末共借阅{weekend_count}次，工作日{weekday_count}次，周末偏好明显",
                            "trend": "up",
                            "severity": "info",
                            "metric": "weekend_ratio",
                            "value": round(weekend_ratio, 1)
                        })

            # 按优先级排序：warning > success > info
            severity_order = {"warning": 0, "success": 1, "info": 2}
            insights.sort(key=lambda x: severity_order.get(x["severity"], 3))

            return {"insights": insights[:limit]}

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)  # 5分钟缓存
        return result
    except Exception as e:
        logger.error("获取智能洞察失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取智能洞察失败: {e}")
