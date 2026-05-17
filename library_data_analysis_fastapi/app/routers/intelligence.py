import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.database import run_sync_db
from app.cache import cache
from app.auth import get_current_user

router = APIRouter(prefix="/api/intelligence", tags=["智能分析"])
logger = logging.getLogger(__name__)

CATEGORY_COLORS = {
    "文学": "#E74C3C",
    "艺术": "#9B59B6",
    "历史": "#3498DB",
    "科技": "#1ABC9C",
    "教育": "#F39C12",
    "哲学": "#2C3E50",
    "社会科学": "#27AE60",
    "医学": "#E67E22",
    "工业技术": "#34495E",
    "自然科学": "#16A085",
}


def get_category_color(category: str) -> str:
    if not category:
        return "#95A5A6"
    for key, color in CATEGORY_COLORS.items():
        if key in category:
            return color
    return "#95A5A6"


def compute_date_cutoff(years_back: int) -> int:
    """根据最大借出日期减去N年，返回 YYYYMMDD 格式的整数"""
    with run_sync_db.__self__.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(borrow_date) FROM circulations WHERE status = 'borrowed'")
            row = cur.fetchone()
            max_date = row[0] if row and row[0] else 0
            if max_date == 0:
                return 20220101
            year = max_date // 10000
            month_day = max_date % 10000
            return (year - years_back) * 10000 + month_day


@router.get("/correlation")
async def get_correlation(
    year_range: str = Query("all", pattern="^(1|2|all)$"),
    min_support: float = Query(0.05, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=1000),
    current_user=Depends(get_current_user)
):
    cache_key = f"intelligence:correlation:{year_range}:{min_support}:{limit}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            with conn.cursor() as cur:
                if year_range == "all":
                    years_back = 10
                else:
                    years_back = int(year_range)

                cur.execute("SELECT MAX(borrow_date) FROM circulations WHERE status = 'borrowed'")
                row = cur.fetchone()
                max_date = row[0] if row and row[0] else 0
                if max_date == 0:
                    cutoff_date = 20220101
                else:
                    year = max_date // 10000
                    month_day = max_date % 10000
                    cutoff_date = (year - years_back) * 10000 + month_day

                reader_books_sql = """
                    WITH frequent_borrowers AS (
                        SELECT borrower_id
                        FROM circulations
                        WHERE status = 'borrowed' AND borrow_date >= %s
                        GROUP BY borrower_id
                        HAVING COUNT(DISTINCT bib_id) >= 5
                    ),
                    reader_books AS (
                        SELECT c.borrower_id, c.bib_id
                        FROM circulations c
                        JOIN frequent_borrowers fb ON c.borrower_id = fb.borrower_id
                        WHERE c.status = 'borrowed' AND c.borrow_date >= %s
                    ),
                    book_pairs AS (
                        SELECT rb1.bib_id as book1, rb2.bib_id as book2, COUNT(*) as co_count
                        FROM reader_books rb1
                        JOIN reader_books rb2 ON rb1.borrower_id = rb2.borrower_id 
                            AND rb1.bib_id < rb2.bib_id
                        GROUP BY rb1.bib_id, rb2.bib_id
                        HAVING COUNT(*) >= 5
                    ),
                    book_stats AS (
                        SELECT bib_id, COUNT(DISTINCT borrower_id) as reader_count
                        FROM reader_books
                        GROUP BY bib_id
                    )
                    SELECT 
                        bp.book1, COALESCE(bc1.name, CONCAT('图书', bp.book1)) as name1, bc1.category,
                        bp.book2, COALESCE(bc2.name, CONCAT('图书', bp.book2)) as name2, bc2.category,
                        bp.co_count, bs1.reader_count, bs2.reader_count,
                        CAST(bp.co_count AS FLOAT) / LEAST(bs1.reader_count, bs2.reader_count) as confidence
                    FROM book_pairs bp
                    LEFT JOIN book_categories bc1 ON bp.book1 = bc1.bib_id
                    LEFT JOIN book_categories bc2 ON bp.book2 = bc2.bib_id
                    JOIN book_stats bs1 ON bp.book1 = bs1.bib_id
                    JOIN book_stats bs2 ON bp.book2 = bs2.bib_id
                    WHERE CAST(bp.co_count AS FLOAT) / LEAST(bs1.reader_count, bs2.reader_count) >= %s
                    ORDER BY bp.co_count DESC
                    LIMIT %s
                """

                cur.execute(reader_books_sql, (cutoff_date, cutoff_date, min_support, limit))
                rows = cur.fetchall()

                nodes_map = {}
                links = []

                for row in rows:
                    book1_id, name1, category1, book2_id, name2, category2, co_count, readers1, readers2, confidence = row

                    if book1_id not in nodes_map:
                        nodes_map[book1_id] = {
                            "id": str(book1_id),
                            "name": name1,
                            "category": category1 or "未分类",
                            "readers": readers1,
                            "color": get_category_color(category1)
                        }

                    if book2_id not in nodes_map:
                        nodes_map[book2_id] = {
                            "id": str(book2_id),
                            "name": name2,
                            "category": category2 or "未分类",
                            "readers": readers2,
                            "color": get_category_color(category2)
                        }

                    links.append({
                        "source": str(book1_id),
                        "target": str(book2_id),
                        "value": co_count,
                        "confidence": round(confidence, 3)
                    })

                nodes = list(nodes_map.values())

                return {
                    "nodes": nodes,
                    "links": links,
                    "total_pairs": len(links)
                }

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取关联分析失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取关联分析失败: {e}")


@router.get("/collection-optimization")
async def get_collection_optimization(
    never_borrowed: bool = Query(True),
    low_freq_threshold: int = Query(5, ge=1, le=100),
    idle_months: int = Query(4, ge=1, le=24),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user=Depends(get_current_user)
):
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 50

    offset = (page - 1) * page_size

    try:
        def _query(conn):
            with conn.cursor() as cur:
                cur.execute("SELECT MAX(borrow_date) FROM circulations WHERE status = 'borrowed'")
                row = cur.fetchone()
                max_date = row[0] if row and row[0] else 20260101

                max_year = max_date // 10000
                max_month = (max_date % 10000) // 100
                idle_cutoff_year = max_year
                idle_cutoff_month = max_month - idle_months
                if idle_cutoff_month <= 0:
                    idle_cutoff_year -= 1
                    idle_cutoff_month += 12
                idle_cutoff_date = idle_cutoff_year * 10000 + idle_cutoff_month * 100 + 1

                cat_filter = " AND bc.category = %(category)s" if category else ""
                cat_param = {"category": category} if category else {}

                if never_borrowed:
                    count_sql = f"""
                        SELECT COUNT(*)
                        FROM book_categories bc
                        WHERE NOT EXISTS (
                            SELECT 1 FROM circulations c 
                            WHERE c.bib_id = bc.bib_id AND c.status = 'borrowed'
                        )
                        {cat_filter}
                    """
                    cur.execute(count_sql, cat_param)
                    total = cur.fetchone()[0]

                    data_sql = f"""
                        SELECT 
                            bc.bib_id,
                            COALESCE(bc.name, CONCAT('图书', bc.bib_id)) as name,
                            bc.category,
                            0 as borrow_count,
                            NULL as last_borrow_date,
                            'never_borrowed' as issue_type,
                            '从未被借阅' as issue_type_name
                        FROM book_categories bc
                        WHERE NOT EXISTS (
                            SELECT 1 FROM circulations c 
                            WHERE c.bib_id = bc.bib_id AND c.status = 'borrowed'
                        )
                        {cat_filter}
                        ORDER BY bc.bib_id ASC
                        LIMIT %(page_size)s OFFSET %(offset)s
                    """
                    cur.execute(data_sql, {**cat_param, "page_size": page_size, "offset": offset})
                    rows = cur.fetchall()
                else:
                    count_sql = f"""
                        SELECT COUNT(*) FROM (
                            SELECT bc.bib_id,
                                   COUNT(c.id) as borrow_count,
                                   MAX(c.borrow_date) as last_borrow_date
                            FROM book_categories bc
                            JOIN circulations c ON bc.bib_id = c.bib_id AND c.status = 'borrowed'
                            GROUP BY bc.bib_id
                            HAVING COUNT(c.id) < %(threshold)s OR MAX(c.borrow_date) <= %(idle_cutoff)s
                            {cat_filter.replace('bc.category', 'bc.category')}
                        ) sub
                    """
                    count_params = {**cat_param, "threshold": low_freq_threshold, "idle_cutoff": idle_cutoff_date}
                    cur.execute(count_sql, count_params)
                    total = cur.fetchone()[0]

                    data_sql = f"""
                        SELECT 
                            bc.bib_id,
                            COALESCE(bc.name, CONCAT('图书', bc.bib_id)) as name,
                            bc.category,
                            COUNT(c.id) as borrow_count,
                            MAX(c.borrow_date) as last_borrow_date,
                            CASE 
                                WHEN MAX(c.borrow_date) <= %(idle_cutoff)s THEN 'idle'
                                ELSE 'low_frequency'
                            END as issue_type,
                            CASE 
                                WHEN MAX(c.borrow_date) <= %(idle_cutoff)s THEN '长期闲置'
                                ELSE '低频借阅'
                            END as issue_type_name
                        FROM book_categories bc
                        JOIN circulations c ON bc.bib_id = c.bib_id AND c.status = 'borrowed'
                        GROUP BY bc.bib_id, bc.name, bc.category
                        HAVING COUNT(c.id) < %(threshold)s OR MAX(c.borrow_date) <= %(idle_cutoff)s
                        {cat_filter}
                        ORDER BY 
                            CASE WHEN MAX(c.borrow_date) <= %(idle_cutoff)s THEN 1 ELSE 2 END,
                            COUNT(c.id) ASC
                        LIMIT %(page_size)s OFFSET %(offset)s
                    """
                    data_params = {**cat_param, "threshold": low_freq_threshold, "idle_cutoff": idle_cutoff_date,
                                   "page_size": page_size, "offset": offset}
                    cur.execute(data_sql, data_params)
                    rows = cur.fetchall()

                result_list = []
                for row in rows:
                    bib_id, name, cat, borrow_count, last_date, issue_type, issue_type_name = row
                    result_list.append({
                        "bib_id": str(bib_id),
                        "name": name,
                        "category": cat or "未分类",
                        "borrow_count": borrow_count,
                        "last_borrow_date": str(last_date) if last_date else None,
                        "issue_type": issue_type,
                        "issue_type_name": issue_type_name
                    })

                total_pages = (total + page_size - 1) // page_size if total > 0 else 0

                return {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                    "list": result_list
                }

        result = await run_sync_db(_query)
        return result
    except Exception as e:
        logger.error("获取馆藏优化建议失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取馆藏优化建议失败: {e}")
